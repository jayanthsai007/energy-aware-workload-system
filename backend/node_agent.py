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
import sys

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
except Exception:
    tk = None
    messagebox = None
    simpledialog = None

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
            config = json.load(f)
    else:
        config = {
            "agent_id": generate_agent_id(),
            "created_at": time.time(),
            "node_id": None
        }

    config.setdefault("agent_id", generate_agent_id())
    config.setdefault("created_at", time.time())
    config.setdefault("node_id", None)
    config.setdefault("node_name", "")
    config.setdefault("permissions", {})
    config["permissions"].setdefault("metrics_access", False)
    config["permissions"].setdefault("network_access", True)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

    return config


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(agent_config, f)


def get_default_device_name():
    computer_name = os.getenv(
        "COMPUTERNAME") or socket.gethostname() or "Device"
    return f"Node-{computer_name}"


def prompt_text(prompt_title, prompt_message, default_value):
    if tk and simpledialog:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        value = simpledialog.askstring(
            prompt_title, prompt_message, initialvalue=default_value, parent=root)
        root.destroy()
        if value and value.strip():
            return value.strip()

    if sys.stdin and sys.stdin.isatty():
        typed_value = input(f"{prompt_message} [{default_value}]: ").strip()
        return typed_value or default_value

    return default_value


def prompt_yes_no(prompt_title, prompt_message, default_value=False):
    if tk and messagebox:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        answer = messagebox.askyesno(prompt_title, prompt_message, parent=root)
        root.destroy()
        return answer

    if sys.stdin and sys.stdin.isatty():
        default_choice = "y" if default_value else "n"
        typed_value = input(
            f"{prompt_message} [y/n, default={default_choice}]: ").strip().lower()
        if not typed_value:
            return default_value
        return typed_value.startswith("y")

    return default_value


def ensure_security_setup():
    updated = False

    if not agent_config.get("node_name"):
        agent_config["node_name"] = prompt_text(
            "Device Name",
            "Enter a name for this device to show in the admin dashboard.",
            get_default_device_name(),
        )
        updated = True

    permissions = agent_config.setdefault("permissions", {})

    if "metrics_access" not in permissions or permissions.get("metrics_access") is None:
        permissions["metrics_access"] = prompt_yes_no(
            "Metrics Permission",
            "Allow this device to share CPU, memory, and temperature metrics with the admin dashboard?",
            default_value=False,
        )
        updated = True

    permissions.setdefault("network_access", True)

    if updated:
        save_config()


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
ensure_security_setup()
AGENT_ID = agent_config["agent_id"]
NODE_ID = agent_config.get("node_id")
NODE_NAME = agent_config.get("node_name") or get_default_device_name()
PERMISSIONS = agent_config.get("permissions", {})


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
        "node_name": NODE_NAME,
        "ip_address": IP_ADDRESS,

        "cpu_cores": psutil.cpu_count(),
        "cpu_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else 2.5,

        "total_memory": round(psutil.virtual_memory().total / (1024 ** 3), 2),

        "total_storage": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
        "free_storage": round(psutil.disk_usage('/').free / (1024 ** 3), 2),

        "os": platform.system(),
        "architecture": platform.machine(),
        "metrics_access": bool(PERMISSIONS.get("metrics_access", False)),
        "network_access": bool(PERMISSIONS.get("network_access", True))
    }

    try:
        res = requests.post(f"{BACKEND_URL}/register-node", json=payload)
        data = res.json()

        NODE_ID = data.get("node_id")
        agent_config["node_name"] = data.get("node_name", NODE_NAME)

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
        if not PERMISSIONS.get("metrics_access", False):
            time.sleep(5)
            continue

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
    print(f"Device Name: {NODE_NAME}")
    print(f"IP: {IP_ADDRESS}")
    print(f"Metrics Access: {PERMISSIONS.get('metrics_access', False)}")

    register_node()

    threading.Thread(target=send_metrics, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
