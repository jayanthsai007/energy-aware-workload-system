import sys
import shutil
import tempfile
import websockets
import asyncio
import platform
import socket
import subprocess
import threading
import psutil
import time
import os
import json
import uuid
import requests
import re
from datetime import datetime, UTC
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# =========================
# SINGLE INSTANCE ENFORCEMENT
# =========================


def is_agent_already_running():
    """Check if another agent instance is running"""
    try:
        # Try to connect to our local API port
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 9000))
        s.close()
        return result == 0  # 0 means connection successful
    except:
        return False


if is_agent_already_running():
    print("[AGENT] Another instance is already running. Exiting.")
    sys.exit(1)
BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, 'frozen', False) else __file__
)
CODE_VERSION = str(int(os.path.getmtime(os.path.abspath(__file__))))

CONFIG_FILE = os.path.join(BASE_DIR, "node_config.json")
LOG_FILE = os.path.join(BASE_DIR, "agent.log")

DEFAULT_PUBLIC_BACKEND_URL = "https://your-app.onrender.com"
PYTHON_EXECUTOR_IMAGE = "energy-node-python:v2"
JAVA_EXECUTOR_IMAGE = "energy-node-java:latest"


def normalize_backend_url(url):
    return str(url or "").strip().rstrip("/")


def build_ws_url(backend_url):
    if backend_url.startswith("https://"):
        return "wss://" + backend_url[len("https://"):] + "/ws"
    if backend_url.startswith("http://"):
        return "ws://" + backend_url[len("http://"):] + "/ws"
    raise ValueError(f"Unsupported backend URL: {backend_url}")


def get_repo_root_candidates():
    candidates = []

    if os.getcwd():
        candidates.append(os.getcwd())

    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(script_dir)
    candidates.append(os.path.dirname(script_dir))

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(exe_dir)
        candidates.append(os.path.dirname(exe_dir))

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized not in seen:
            seen.add(normalized)
            unique_candidates.append(os.path.abspath(candidate))

    return unique_candidates


def find_executor_dir(executor_name):
    for base in get_repo_root_candidates():
        direct = os.path.join(base, "Node_client", "docker", executor_name)
        if os.path.isfile(os.path.join(direct, "Dockerfile")):
            return direct

        nested = os.path.join(base, "docker", executor_name)
        if os.path.isfile(os.path.join(nested, "Dockerfile")):
            return nested

    return None

# =========================
# LOCAL API SERVER
# =========================
local_app = FastAPI(title="Node Agent Local API", version="1.0.0")
local_server = None


class RunScriptRequest(BaseModel):
    script: str
    language: str = "python"


# Store task results for UI polling
task_results = {}


@local_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "node_id": NODE_ID, "code_version": CODE_VERSION}


@local_app.post("/run")
async def run_script(data: RunScriptRequest, background_tasks: BackgroundTasks = None):
    """Receive script from local UI and submit to backend queue"""
    try:
        script = data.script
        language = data.language

        log(f"📝 Received script: {len(script)} chars, language: {language}")

        # Generate task_id
        task_id = str(uuid.uuid4())
        log(f"🆔 Generated task_id: {task_id}")

        # Send to backend
        log(f"📡 Sending to backend: {BACKEND_URL}/execute")
        res = requests.post(
            f"{BACKEND_URL}/execute",
            json={
                "script_content": script,
                "language": language,
                "task_id": task_id
            },
            timeout=10
        )

        log(f"📡 Backend response: {res.status_code}")

        if res.status_code == 200:
            log(f"✅ Task submitted: {task_id}")
            # Initialize task result
            task_results[task_id] = {"status": "submitted", "task_id": task_id}
            return {"task_id": task_id, "status": "submitted"}
        else:
            error_msg = f"Backend error: {res.status_code} - {res.text}"
            log(f"❌ {error_msg}")
            return {"error": error_msg}

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {e}"
        log(f"❌ {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Local run error: {e}"
        log(f"❌ {error_msg}")
        return {"error": str(e)}


@local_app.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """Get task result (for UI polling)"""
    if task_id in task_results:
        return task_results[task_id]
    return {"error": "Task not found"}


@local_app.get("/status")
async def get_status():
    """Get node status for UI"""
    return {
        "node_id": NODE_ID,
        "running": is_running(),
        "ws_connected": ws_connection is not None
    }


@local_app.post("/shutdown")
async def shutdown_agent():
    """Allow the UI to stop the agent cleanly"""
    shutdown()
    return {"status": "shutting_down"}

# =========================
# TASK RESULT POLLING
# =========================


def poll_task_results():
    while is_running():
        try:
            for task_id in list(task_results.keys()):
                if task_results[task_id].get("status") not in ["completed", "failed"]:
                    # Poll backend for task status
                    res = requests.get(
                        f"{BACKEND_URL}/task/{task_id}", timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        task_results[task_id].update(data)
                        log(f"📊 Task {task_id}: {data.get('status')}")
        except Exception as e:
            log(f"❌ Poll error: {e}")
        time.sleep(2)


# =========================
# CONTROL FLAGS
# =========================
shutdown_event = threading.Event()
ws_connection = None
event_loop = None  # important for thread-safe async


def is_running():
    return not shutdown_event.is_set()

# =========================
# LOGGING
# =========================


def log(msg):
    timestamp = datetime.now(UTC).strftime("%H:%M:%S")
    print(f"[AGENT {timestamp}] {msg}")

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

# =========================
# CONFIG (ROBUST)
# =========================


def generate_agent_id():
    return str(uuid.uuid4())


def get_default_node_name():
    return f"Node-{platform.node()}"


def load_or_create_agent():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

            config.setdefault("backend_url", "")
            config["agent_id"] = str(config.get("agent_id") or generate_agent_id()).strip()
            config["created_at"] = config.get("created_at") or time.time()
            config["node_id"] = config.get("node_id") or None
            config["node_name"] = str(
                config.get("node_name") or get_default_node_name()
            ).strip()
            config["backend_url"] = normalize_backend_url(config.get("backend_url"))

            permissions = config.get("permissions")
            if not isinstance(permissions, dict):
                permissions = {}
            permissions.setdefault("metrics_access", True)
            permissions.setdefault("network_access", True)
            config["permissions"] = permissions

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            log("📂 Loaded config")
            return config

        except Exception as e:
            log(f"⚠️ Config corrupted -> recreating ({e})")

    # First-run setup
    log("🎉 First run detected! Setting up node...")

    # Default permissions (in production, prompt user)
    permissions = {
        "metrics_access": True,
        "network_access": True
    }

    # Default node name (in production, prompt user)
    node_name = get_default_node_name()

    config = {
        "backend_url": "",
        "agent_id": generate_agent_id(),
        "created_at": time.time(),
        "node_id": None,
        "node_name": node_name,
        "permissions": permissions
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    log(f"🆕 New config created for node: {node_name}")
    return config


def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(agent_config, f, indent=4)

# =========================
# NETWORK
# =========================


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


# =========================
# INIT
# =========================
agent_config = load_or_create_agent()
AGENT_ID = agent_config["agent_id"]
NODE_ID = agent_config.get("node_id") or None
BACKEND_URL = normalize_backend_url(agent_config.get("backend_url"))
WS_URL = ""
if BACKEND_URL:
    try:
        WS_URL = build_ws_url(BACKEND_URL)
    except ValueError:
        WS_URL = ""
IP_ADDRESS = get_local_ip()

# =========================
# REGISTER NODE (FIXED)
# =========================


def register_node():
    global NODE_ID

    if not BACKEND_URL:
        raise RuntimeError(
            "Missing backend_url in node_config.json. "
            f"Set it to a reachable backend URL such as {DEFAULT_PUBLIC_BACKEND_URL}."
        )
    if not WS_URL:
        raise RuntimeError(
            "Invalid backend_url in node_config.json. "
            "Use a full http:// or https:// URL."
        )

    if NODE_ID:
        log(f"🔁 Using node_id: {NODE_ID}")

    log("📡 Registering node...")

    payload = {
        "node_name": agent_config.get("node_name") or get_default_node_name(),
        "agent_id": AGENT_ID,
        "ip_address": f"{IP_ADDRESS}:8000",
        "cpu_cores": psutil.cpu_count(),
        "cpu_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 2.5,
        "total_memory": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "total_storage": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
        "free_storage": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
        "os": platform.system(),
        "architecture": platform.machine(),
        "metrics_access": bool(agent_config.get("permissions", {}).get("metrics_access", True)),
        "network_access": bool(agent_config.get("permissions", {}).get("network_access", True)),
    }

    res = requests.post(f"{BACKEND_URL}/register-node", json=payload, timeout=10)
    res.raise_for_status()

    data = res.json()
    NODE_ID = data.get("node_id")

    if NODE_ID:
        agent_config["node_id"] = NODE_ID
        agent_config["node_name"] = payload["node_name"]
        save_config()
        log(f"✅ Registered: {NODE_ID}")
        return True

    raise RuntimeError("Backend response did not include node_id")


def registration_retry_loop():
    while is_running() and not NODE_ID:
        try:
            register_node()
            if NODE_ID:
                return
        except Exception as e:
            log(f"❌ Registration error: {e}")

        if is_running() and not NODE_ID:
            log("🔁 Retrying registration in 5 seconds...")
            time.sleep(5)

# =========================
# METRICS + HEARTBEAT
# =========================


def send_metrics():
    while is_running():
        if NODE_ID:
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent

                # Get temperature - use real sensors if available, else simulate
                temperature = None
                sensor_fn = getattr(psutil, "sensors_temperatures", None)
                if callable(sensor_fn):
                    try:
                        sensors = sensor_fn()
                        if sensors:
                            for name, entries in sensors.items():
                                if entries:
                                    temperature = entries[0].current
                                    break
                    except Exception:
                        temperature = None

                if temperature is None:
                    temperature = 40 + cpu * 0.4

                log(f"📊 CPU: {cpu}%, MEM: {memory}%, TEMP: {round(temperature, 2)}°C")

                requests.post(f"{BACKEND_URL}/metrics", json={
                    "node_id": NODE_ID,
                    "cpu": cpu,
                    "memory": memory,
                    "temperature": round(temperature, 2),
                    "node_timestamp": datetime.now(UTC).isoformat()
                }, timeout=5)

                log("📊 Metrics sent")

            except Exception as e:
                log(f"❌ Metrics error: {e}")

        time.sleep(5)


def heartbeat():
    while is_running():
        if NODE_ID:
            try:
                requests.post(f"{BACKEND_URL}/heartbeat",
                              json={"node_id": NODE_ID},
                              timeout=5)

                log("💓 Heartbeat sent")

            except Exception as e:
                log(f"❌ Heartbeat error: {e}")

        time.sleep(10)

# =========================
# SAFE WS LOG (THREAD SAFE)
# =========================


def send_ws_log(msg):
    global ws_connection, event_loop

    if ws_connection and event_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                ws_connection.send(json.dumps({
                    "type": "execution_log",
                    "data": msg
                })),
                event_loop
            )
        except:
            pass

# =========================
# EXECUTION ENGINE
# =========================


def subprocess_run(cmd, task_id):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    output = []

    try:
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue

            output.append(line)

            log(f"⚡ [{task_id}] {line}")
            send_ws_log(f"[{task_id}] {line}")

        process.stdout.close()
        process.wait(timeout=20)

        stderr = process.stderr.read()

        return output, stderr

    except subprocess.TimeoutExpired:
        process.kill()
        return [], "Execution timed out"


def docker_image_exists(image_name):
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def ensure_docker_image(image_name, executor_name):
    if docker_image_exists(image_name):
        return True, None

    executor_dir = find_executor_dir(executor_name)
    if not executor_dir:
        return False, (
            f"Docker image '{image_name}' not found, and the '{executor_name}' "
            "executor Dockerfile could not be located."
        )

    dockerfile = os.path.join(executor_dir, "Dockerfile")
    log(f"🐳 Building missing Docker image '{image_name}' from {executor_dir}")

    try:
        build = subprocess.run(
            ["docker", "build", "-t", image_name, "-f", dockerfile, executor_dir],
            capture_output=True,
            text=True,
            timeout=600
        )
    except Exception as exc:
        return False, f"Failed to build Docker image '{image_name}': {exc}"

    if build.returncode != 0:
        error_text = (build.stderr or build.stdout or "").strip()
        return False, (
            f"Failed to build Docker image '{image_name}'. "
            f"{error_text or 'docker build exited with a non-zero status.'}"
        )

    log(f"✅ Built Docker image '{image_name}'")
    return True, None


def resolve_java_entrypoint(script):
    class_matches = list(re.finditer(r"(?:public\s+)?class\s+(\w+)\b", script))
    if not class_matches:
        return None, None

    public_class_match = re.search(r"public\s+class\s+(\w+)\b", script)
    public_class_name = public_class_match.group(1) if public_class_match else None

    main_match = re.search(r"public\s+static\s+void\s+main\s*\(", script)
    main_class_name = None
    if main_match:
        preceding_classes = [
            match.group(1)
            for match in class_matches
            if match.start() < main_match.start()
        ]
        if preceding_classes:
            main_class_name = preceding_classes[-1]

    source_class_name = public_class_name or main_class_name or class_matches[0].group(1)
    run_class_name = main_class_name or public_class_name or source_class_name

    return source_class_name, run_class_name


def run_python(script, task_id):
    if shutil.which("docker"):
        ok, err = ensure_docker_image(PYTHON_EXECUTOR_IMAGE, "python-executor")
        if not ok:
            return [], err
        return subprocess_run([
            "docker", "run", "--rm",
            "--cpus=1", "--memory=512m", "--network=none",
            PYTHON_EXECUTOR_IMAGE,
            "python", "-u", "-c", script
        ], task_id)
    else:
        log("⚠️ Docker not found -> running locally")
        return subprocess_run([sys.executable, "-u", "-c", script], task_id)


def run_java(script, task_id):
    if shutil.which("docker"):
        ok, err = ensure_docker_image(JAVA_EXECUTOR_IMAGE, "java-executor")
        if not ok:
            return [], err

        source_class_name, run_class_name = resolve_java_entrypoint(script)
        if not source_class_name or not run_class_name:
            return [], "Java execution requires a class definition and a main() entrypoint."

        with tempfile.TemporaryDirectory() as tmpdir:
            java_file = os.path.join(tmpdir, f"{source_class_name}.java")
            with open(java_file, "w") as f:
                f.write(script)
            return subprocess_run([
                "docker", "run", "--rm",
                "--cpus=1", "--memory=512m", "--network=none",
                "-v", f"{tmpdir}:/app",
                JAVA_EXECUTOR_IMAGE,
                "bash", "-c", f"cd /app && javac {source_class_name}.java && java {run_class_name}"
            ], task_id)
    else:
        return [], "Java requires Docker"


def execute_script(data):
    task_id = data.get("task_id")
    language = data.get("language")
    script = data.get("script")

    log(f"🚀 Task received: {task_id}")
    log(f"▶ Language: {language}")

    start = time.time()

    if language == "python":
        output, err = run_python(script, task_id)
    else:
        output, err = run_java(script, task_id)

    exec_time = round(time.time() - start, 3)
    log(f"✅ Task completed: {task_id} ({exec_time}s)")

    # Determine status based on error presence
    status = "success" if not err else "failed"

    return {
        "task_id": task_id,
        "status": status,
        "output": "\n".join(output),
        "error": err,
        "execution_time": exec_time,
        "language": language
    }

# =========================
# WEBSOCKET CLIENT (STABLE)
# =========================


async def websocket_client():
    global ws_connection, event_loop

    event_loop = asyncio.get_running_loop()

    while is_running():
        try:
            if not WS_URL:
                log("❌ Missing backend_url in node_config.json. WS retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue

            log("🔌 Connecting WS...")
            log(f"[AGENT] Backend URL: {BACKEND_URL}")
            log(f"[AGENT] WS URL: {WS_URL}")

            async with websockets.connect(WS_URL) as ws:
                ws_connection = ws
                log("✅ WS Connected")

                while not NODE_ID and is_running():
                    await asyncio.sleep(1)

                await ws.send(json.dumps({
                    "type": "register",
                    "node_id": NODE_ID
                }))

                log(f"🧠 Registered to WS: {NODE_ID}")

                while is_running():
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        if data.get("type") == "execute":
                            result = execute_script(data)

                            await ws.send(json.dumps({
                                "type": "execution_result",
                                "data": result
                            }))

                    except websockets.ConnectionClosed:
                        log("⚠️ WS disconnected")
                        break

        except Exception as e:
            if is_running():
                log(f"❌ WS error: {e}")
                log("WS failed, retrying in 5 seconds...")
                await asyncio.sleep(5)

# =========================
# SHUTDOWN
# =========================


def shutdown():
    global local_server, ws_connection
    log("🛑 Shutting down agent...")
    shutdown_event.set()
    if ws_connection and event_loop:
        try:
            close_future = asyncio.run_coroutine_threadsafe(ws_connection.close(), event_loop)
            close_future.result(timeout=5)
        except Exception:
            pass
    if local_server is not None:
        local_server.should_exit = True


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    try:
        log("🚀 Node Agent Starting...")
        log(f"[AGENT] Backend URL: {BACKEND_URL or '(not configured)'}")
        log(f"[AGENT] WS URL: {WS_URL or '(not configured)'}")

        # Start local API server in background thread
        def run_local_server():
            global local_server
            try:
                config = uvicorn.Config(
                    local_app,
                    host="127.0.0.1",
                    port=9000,
                    log_level="error",
                )
                local_server = uvicorn.Server(config)
                local_server.run()
            except Exception as e:
                log(f"❌ Local server error: {e}")

        server_thread = threading.Thread(target=run_local_server, daemon=True)
        server_thread.start()
        log("🔧 Local API server started on http://127.0.0.1:9000")

        threading.Thread(target=registration_retry_loop, daemon=True).start()

        # Start metrics, heartbeat, and polling threads
        threading.Thread(target=send_metrics, daemon=True).start()
        threading.Thread(target=heartbeat, daemon=True).start()
        threading.Thread(target=poll_task_results, daemon=True).start()

        # Run WebSocket client (only for backend communication)
        asyncio.run(websocket_client())

    except KeyboardInterrupt:
        shutdown()
        log("👋 Agent stopped gracefully")
