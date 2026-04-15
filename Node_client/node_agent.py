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
from datetime import datetime, UTC
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from uvicorn import run as uvicorn_run

# =========================
# BASE PATH
# =========================
BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, 'frozen', False) else __file__
)

CONFIG_FILE = os.path.join(BASE_DIR, "node_config.json")
LOG_FILE = os.path.join(BASE_DIR, "agent.log")

BACKEND_URL = "http://127.0.0.1:8000"

# =========================
# LOCAL API SERVER
# =========================
local_app = FastAPI(title="Node Agent Local API", version="1.0.0")


class RunScriptRequest(BaseModel):
    script: str
    language: str = "python"


# Store task results for UI polling
task_results = {}


@local_app.post("/run")
async def run_script(data: RunScriptRequest, background_tasks: BackgroundTasks = None):
    """Receive script from local UI and submit to backend queue"""
    try:
        script = data.script
        language = data.language

        # Generate task_id
        task_id = str(uuid.uuid4())

        # Send to backend
        res = requests.post(
            f"{BACKEND_URL}/execute",
            json={
                "script_content": script,
                "language": language,
                "task_id": task_id
            },
            timeout=10
        )

        if res.status_code == 200:
            log(f"✅ Task submitted: {task_id}")
            # Initialize task result
            task_results[task_id] = {"status": "submitted", "task_id": task_id}
            return {"task_id": task_id, "status": "submitted"}
        else:
            log(f"❌ Backend error: {res.status_code}")
            return {"error": "Backend submission failed"}

    except Exception as e:
        log(f"❌ Local run error: {e}")
        return {"error": str(e)}


@local_app.get("/task/{task_id}")
async def get_task_result(task_id: str):
    """Get task result for UI polling"""
    return task_results.get(task_id, {"status": "not_found"})


@local_app.get("/status")
async def get_status():
    """Get node status for UI"""
    return {
        "node_id": NODE_ID,
        "running": is_running(),
        "ws_connected": ws_connection is not None
    }

# =========================
# TASK RESULT POLLING
# =========================


def poll_task_results():
    while is_running():
        try:
            for task_id in list(task_results.keys()):
                if task_results[task_id]["status"] in ["submitted", "running"]:
                    # Poll backend for task status
                    res = requests.get(
                        f"{BACKEND_URL}/task/{task_id}", timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        task_results[task_id].update(data)
        except Exception as e:
            log(f"❌ Poll error: {e}")
        time.sleep(2)


# =========================
# CONTROL FLAGS
# =========================
shutdown_event = threading.Event()
ws_connection = None
event_loop = None  # 🔥 important for thread-safe async


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


def load_or_create_agent():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            if "agent_id" not in config:
                raise ValueError("Invalid config")

            if not config.get("node_id"):
                config["node_id"] = None

            log("📂 Loaded config")
            return config

        except Exception as e:
            log(f"⚠️ Config corrupted → recreating ({e})")

    config = {
        "agent_id": generate_agent_id(),
        "created_at": time.time(),
        "node_id": None
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    log("🆕 New config created")
    return config


def save_config():
    with open(CONFIG_FILE, "w") as f:
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
IP_ADDRESS = get_local_ip()

# =========================
# REGISTER NODE (FIXED)
# =========================


def register_node():
    global NODE_ID

    if NODE_ID:
        log(f"🔁 Using node_id: {NODE_ID}")
        return

    try:
        log("📡 Registering node...")

        payload = {
            "node_name": f"Node-{AGENT_ID[:6]}",
            "agent_id": AGENT_ID,
            "ip_address": f"{IP_ADDRESS}:8000",  # 🔥 REQUIRED FORMAT
            "cpu_cores": psutil.cpu_count(),
            "cpu_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 2.5,
            "total_memory": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "total_storage": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
            "free_storage": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
            "os": platform.system(),
            "architecture": platform.machine()
        }

        res = requests.post(f"{BACKEND_URL}/register-node",
                            json=payload, timeout=10)

        if res.status_code != 200:
            log(f"❌ Registration failed → {res.text}")
            return

        data = res.json()
        NODE_ID = data.get("node_id")

        if NODE_ID:
            agent_config["node_id"] = NODE_ID
            save_config()
            log(f"✅ Registered: {NODE_ID}")

    except Exception as e:
        log(f"❌ Registration error: {e}")

# =========================
# METRICS + HEARTBEAT
# =========================


def send_metrics():
    while is_running():
        if NODE_ID:
            try:
                requests.post(f"{BACKEND_URL}/metrics", json={
                    "node_id": NODE_ID,
                    "cpu": psutil.cpu_percent(),
                    "memory": psutil.virtual_memory().percent,
                    "temperature": round(40 + psutil.cpu_percent() * 0.4, 2),
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


def run_python(script, task_id):
    if shutil.which("docker"):
        return subprocess_run([
            "docker", "run", "--rm",
            "--cpus=1", "--memory=512m", "--network=none",
            "python:3.10",
            "python", "-u", "-c", script
        ], task_id)
    else:
        log("⚠️ Docker not found → running locally")
        return subprocess_run([sys.executable, "-u", "-c", script], task_id)


def run_java(script, task_id):
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

    ws_url = BACKEND_URL.replace("http", "ws") + "/ws"

    while is_running():
        try:
            log("🔌 Connecting WS...")

            async with websockets.connect(ws_url) as ws:
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
                await asyncio.sleep(3)

# =========================
# SHUTDOWN
# =========================


def shutdown():
    log("🛑 Shutting down agent...")
    shutdown_event.set()


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    try:
        log("🚀 Node Agent Starting...")

        register_node()

        # Start local API server in background thread
        def run_local_server():
            uvicorn_run(local_app, host="127.0.0.1",
                        port=8081, log_level="error")

        server_thread = threading.Thread(target=run_local_server, daemon=True)
        server_thread.start()
        log("🔧 Local API server started on http://127.0.0.1:8081")

        # Start metrics, heartbeat, and polling threads
        threading.Thread(target=send_metrics, daemon=True).start()
        threading.Thread(target=heartbeat, daemon=True).start()
        threading.Thread(target=poll_task_results, daemon=True).start()

        # Run WebSocket client (only for backend communication)
        asyncio.run(websocket_client())

    except KeyboardInterrupt:
        shutdown()
        log("👋 Agent stopped gracefully")
