from fastapi import FastAPI
from datetime import datetime
from uuid import uuid4
import requests
import uuid
import hashlib
import json
import os
import time
import psutil
import threading
import subprocess
import socket
import platform
import re

app = FastAPI()

# =========================
# CONFIG
# =========================
BACKEND_URL = "http://127.0.0.1:8000"
CONFIG_FILE = "node_config.json"

# =========================
# AGENT ID
# =========================


def generate_agent_id():
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()


def load_or_create_agent():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    config = {
        "agent_id": generate_agent_id(),
        "created_at": time.time(),
        "node_id": None
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

    return config


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(agent_config, f)


# =========================
# NETWORK (FIXED IP)
# =========================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


PORT = int(os.getenv("PORT", 8001))
IP_ADDRESS = f"{get_local_ip()}:{PORT}"

agent_config = load_or_create_agent()
AGENT_ID = agent_config["agent_id"]
NODE_ID = agent_config.get("node_id")


# =========================
# REGISTER NODE
# =========================
def register_node():
    global NODE_ID

    # ✅ reuse existing node_id
    if agent_config.get("node_id"):
        NODE_ID = agent_config["node_id"]
        print("Using existing node_id:", NODE_ID)
        return

    payload = {
        "agent_id": AGENT_ID,
        "ip_address": IP_ADDRESS,

        "cpu_cores": psutil.cpu_count(),
        "cpu_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 2.5,

        "total_memory": round(psutil.virtual_memory().total / (1024 ** 3), 2),

        "total_storage": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
        "free_storage": round(psutil.disk_usage('/').free / (1024 ** 3), 2),

        "os": platform.system(),
        "architecture": platform.machine()
    }

    try:
        res = requests.post(f"{BACKEND_URL}/register-node", json=payload)
        data = res.json()

        NODE_ID = data.get("node_id")

        # ✅ save node_id
        agent_config["node_id"] = NODE_ID
        save_config()

        print("Registered:", data)

    except Exception as e:
        print("Registration failed:", e)


# =========================
# TEMPERATURE
# =========================
def get_temperature():
    try:
        os_type = platform.system()

        if os_type == "Linux":
            temps = psutil.sensors_temperatures()
            if temps:
                for _, entries in temps.items():
                    for entry in entries:
                        return float(entry.current)

        cpu = psutil.cpu_percent()
        return round(40 + cpu * 0.4, 2)

    except:
        return 50.0


# =========================
# METRICS STREAMING
# =========================
def send_metrics():
    while True:
        if not NODE_ID:
            time.sleep(5)
            continue

        payload = {
            "node_id": NODE_ID,
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "temperature": get_temperature(),
            "node_timestamp": datetime.utcnow().isoformat()
        }

        try:
            requests.post(f"{BACKEND_URL}/metrics", json=payload)
        except Exception as e:
            print("Metrics failed:", e)

        time.sleep(5)


# =========================
# HEARTBEAT
# =========================
def heartbeat():
    while True:
        if NODE_ID:
            try:
                payload = {
                    "node_id": str(NODE_ID)   # ✅ ensure string
                }

                print("Sending heartbeat:", payload)  # 🔍 debug

                requests.post(
                    f"{BACKEND_URL}/heartbeat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )

            except Exception as e:
                print("Heartbeat failed:", e)

        time.sleep(10)


# =========================
# JAVA VALIDATION
# =========================
def validate_java_script(script: str):
    if not re.search(r'public\s+class\s+Main\b', script):
        return False, "Java must contain 'public class Main'"

    if "public static void main" not in script:
        return False, "Missing main() method"

    return True, None


# =========================
# EXECUTION
# =========================
@app.post("/node-execute")
def execute_script(payload: dict):
    script = payload.get("script")
    language = payload.get("language", "python")

    stats = {"cpu": [], "memory": []}
    stop_flag = {"stop": False}

    def monitor():
        while not stop_flag["stop"]:
            stats["cpu"].append(psutil.cpu_percent())
            stats["memory"].append(psutil.virtual_memory().percent)
            time.sleep(0.5)

    monitor_thread = None

    try:
        # Java validation
        if language == "java":
            valid, err = validate_java_script(script)
            if not valid:
                return {"status": "error", "error": err}

        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()

        start = time.time()

        if language == "python":
            result = subprocess.run(
                ["python", "-c", script],
                capture_output=True,
                text=True,
                timeout=10
            )

        elif language == "java":
            with open("Main.java", "w") as f:
                f.write(script)

            compile_proc = subprocess.run(
                ["javac", "Main.java"],
                capture_output=True,
                text=True
            )

            if compile_proc.returncode != 0:
                raise Exception(compile_proc.stderr)

            result = subprocess.run(
                ["java", "Main"],
                capture_output=True,
                text=True,
                timeout=10
            )

        else:
            raise Exception("Unsupported language")

        end = time.time()

    except Exception as e:
        return {"status": "error", "error": str(e)}

    finally:
        stop_flag["stop"] = True
        if monitor_thread:
            monitor_thread.join()

    # Cleanup Java
    if language == "java":
        for f in ["Main.java", "Main.class"]:
            if os.path.exists(f):
                os.remove(f)

    # Metrics
    cpu_avg = sum(stats["cpu"]) / len(stats["cpu"]) if stats["cpu"] else 0
    cpu_peak = max(stats["cpu"]) if stats["cpu"] else 0
    mem_avg = sum(stats["memory"]) / \
        len(stats["memory"]) if stats["memory"] else 0
    mem_peak = max(stats["memory"]) if stats["memory"] else 0

    execution_time = round(end - start, 4)
    script_id = hashlib.md5(script.encode()).hexdigest()

    try:
        requests.post(f"{BACKEND_URL}/execution-metrics", json={
            "node_id": NODE_ID,
            "script_id": script_id,
            "language": language,
            "execution_time": execution_time,
            "cpu_avg": cpu_avg,
            "cpu_peak": cpu_peak,
            "memory_avg": mem_avg,
            "memory_peak": mem_peak
        })
    except Exception as e:
        print("Execution metrics failed:", e)

    return {
        "status": "success",
        "output": result.stdout,
        "error": result.stderr,
        "execution_time": execution_time
    }


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup():
    print("Starting Node Agent...")
    print(f"Agent ID: {AGENT_ID}")
    print(f"IP: {IP_ADDRESS}")

    register_node()

    threading.Thread(target=send_metrics, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()
