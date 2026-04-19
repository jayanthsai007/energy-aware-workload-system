import socket
import tkinter as tk
from tkinter import ttk, filedialog
import requests
import threading
import json
import os
import keyword
import sys
import time
import subprocess
from datetime import datetime, UTC

# =========================
# SINGLE INSTANCE LOCK
# =========================


def is_already_running():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 65432))
        return False
    except:
        return True


if is_already_running():
    sys.exit()

# =========================
# BASE PATH + LOGGING
# =========================
BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, 'frozen', False) else __file__
)

LOG_FILE = os.path.join(BASE_DIR, "ui.log")


def log(msg):
    timestamp = datetime.now(UTC).strftime("%H:%M:%S")
    print(f"[UI {timestamp}] {msg}")

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass


# =========================
# CONFIG
# =========================
LOCAL_AGENT_URL = "http://127.0.0.1:9000"
BACKEND_URL = "http://127.0.0.1:8000"

# =========================
# GLOBALS
# =========================
tabs = {}
current_task = None
metrics_labels = {}
agent_process = None
last_polled_status = None

# =========================
# METRICS UPDATER
# =========================


def update_metrics():
    try:
        # Get node config to know our node_id
        config_file = os.path.join(BASE_DIR, "node_config.json")
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                node_id = config.get("node_id")

                if node_id:
                    # Get latest metrics from backend
                    res = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
                    if res.status_code == 200:
                        metrics_list = res.json()
                        if metrics_list:
                            latest = metrics_list[0]  # Most recent
                            safe_ui(lambda: update_metrics_display(latest))
    except Exception:
        pass

    # Update every 5 seconds
    root.after(5000, update_metrics)


def update_metrics_display(metrics):
    if "cpu" in metrics_labels:
        metrics_labels["cpu"].config(text=f"{metrics.get('cpu', 0):.1f}%")
    if "memory" in metrics_labels:
        metrics_labels["memory"].config(
            text=f"{metrics.get('memory', 0):.1f}%")
    if "temperature" in metrics_labels:
        temp = metrics.get('temperature', 0)
        if temp > 0:
            metrics_labels["temperature"].config(text=f"{temp:.1f}°C")
        else:
            metrics_labels["temperature"].config(text="--°C")

    # Status is always online if we have metrics
    if "status" in metrics_labels:
        metrics_labels["status"].config(text="Online", fg="#00ff00")

# =========================
# LOG DISPLAY
# =========================


def append_log(msg):
    terminal.config(state="normal")
    terminal.insert(tk.END, msg)
    terminal.see(tk.END)
    terminal.config(state="disabled")

# =========================
# TAB MANAGEMENT
# =========================


def close_tab():
    tab_id = notebook.select()
    if not tab_id:
        return

    widget = notebook.nametowidget(tab_id)

    if widget in tabs:
        del tabs[widget]

    notebook.forget(tab_id)
    append_log("🗑️ Tab closed\n")


def on_tab_right_click(event):
    try:
        index = notebook.index(f"@{event.x},{event.y}")
        notebook.select(index)
        close_tab()
    except:
        pass


def close_all_tabs():
    for tab in notebook.tabs():
        notebook.forget(tab)
    tabs.clear()
    append_log("🧹 All tabs closed\n")

# =========================
# EDITOR
# =========================


def create_tab(title="Untitled", content=""):
    frame = tk.Frame(notebook, bg="#1e1e1e")

    text = tk.Text(
        frame,
        bg="#1e1e1e",
        fg="#d4d4d4",
        insertbackground="white",
        font=("Consolas", 12)
    )
    text.pack(fill="both", expand=True)
    text.insert("1.0", content)

    notebook.add(frame, text=title)
    notebook.select(frame)

    tabs[frame] = text
    text.bind("<KeyRelease>", lambda e: highlight(text))


def get_editor():
    tab = notebook.select()
    return tabs.get(notebook.nametowidget(tab))

# =========================
# FILE OPS
# =========================


def open_file():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    with open(file_path, "r") as f:
        create_tab(os.path.basename(file_path), f.read())

    append_log(f"📂 Opened {file_path}\n")


def save_file():
    editor = get_editor()
    if not editor:
        return

    file_path = filedialog.asksaveasfilename()
    if file_path:
        with open(file_path, "w") as f:
            f.write(editor.get("1.0", tk.END))
        append_log(f"💾 Saved {file_path}\n")

# =========================
# RUN SCRIPT
# =========================


def run_script():
    global current_task, last_polled_status

    editor = get_editor()
    if not editor:
        return

    script = editor.get("1.0", tk.END).strip()
    last_polled_status = None

    append_log("\n📤 Sending task...\n")
    append_log(f"📝 Preview:\n{script[:120]}\n")

    def send():
        global current_task
        try:
            # Check backend connectivity first
            try:
                backend_res = requests.get(
                    "http://127.0.0.1:8000/health", timeout=3)
                if backend_res.status_code != 200:
                    safe_ui(lambda: append_log(
                        f"❌ Backend server not responding (status: {backend_res.status_code})\n"))
                    return
            except requests.exceptions.RequestException as e:
                safe_ui(lambda: append_log(
                    f"❌ Cannot connect to backend server: {e}\n"))
                return

            append_log(f"🔗 Sending to {LOCAL_AGENT_URL}/run\n")

            res = requests.post(
                f"{LOCAL_AGENT_URL}/run",
                json={
                    "script": script,
                    "language": language_var.get()
                },
                timeout=10
            )

            append_log(f"📡 Response status: {res.status_code}\n")

            data = res.json()
            append_log(f"📄 Response data: {data}\n")

            current_task = data.get("task_id")

            if current_task:
                safe_ui(lambda: append_log(
                    f"✅ Task submitted → {current_task}\n"))
                # Start polling for results
                threading.Thread(target=poll_task_result, args=(
                    current_task,), daemon=True).start()
            else:
                error_msg = data.get("error", "Unknown error")
                safe_ui(lambda: append_log(
                    f"❌ Submission failed: {error_msg}\n"))

        except requests.exceptions.RequestException as e:
            safe_ui(lambda: append_log(f"❌ Network error: {e}\n"))
        except Exception as e:
            safe_ui(lambda: append_log(f"❌ Unexpected error: {e}\n"))

    threading.Thread(target=send, daemon=True).start()

# =========================
# TASK RESULT POLLING
# =========================


def poll_task_result(task_id):
    global last_polled_status

    while True:
        try:
            res = requests.get(f"{LOCAL_AGENT_URL}/task/{task_id}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                status = data.get("status")

                if status and status != last_polled_status:
                    last_polled_status = status
                    safe_ui(lambda s=status: append_log(f"⏳ Task status: {s}\n"))

                if status == "completed":
                    safe_ui(lambda: show_task_result(data))
                    break
                elif status == "failed":
                    safe_ui(lambda: show_task_result(data))
                    break
        except Exception:
            pass
        time.sleep(1)


def show_task_result(data):
    append_log("\n🎉 TASK COMPLETED\n")
    append_log(f"🆔 {data.get('task_id')}\n")
    append_log(f"⏱ {data.get('execution_time')} sec\n")

    append_log("\n📤 OUTPUT:\n")
    append_log(data.get("output", "") + "\n")

    if data.get("error"):
        append_log("\n❌ ERROR:\n")
        append_log(data.get("error") + "\n")

# =========================
# SYNTAX HIGHLIGHT
# =========================


def highlight(text):
    text.tag_remove("keyword", "1.0", tk.END)

    for kw in keyword.kwlist:
        start = "1.0"
        while True:
            start = text.search(rf"\b{kw}\b", start, regexp=True)
            if not start:
                break
            end = f"{start}+{len(kw)}c"
            text.tag_add("keyword", start, end)
            start = end

    text.tag_config("keyword", foreground="#569cd6")

# =========================
# WEBSOCKET LISTENER (STABLE)
# =========================
# CLOSE HANDLER (CLEAN)
# =========================


def on_close():
    append_log("🛑 Closing UI...\n")
    stop_agent()
    root.destroy()


# =========================
# AGENT MANAGEMENT
# =========================


def start_agent():
    global agent_process

    # Check if agent is already running
    try:
        res = requests.get(f"{LOCAL_AGENT_URL}/health", timeout=2)
        if res.status_code == 200:
            log("Agent already running")
            return
    except Exception:
        pass

    # Start agent process
    try:
        python_exe = sys.executable
        agent_script = os.path.join(BASE_DIR, "node_agent.py")

        log(f"Starting agent: {python_exe} {agent_script}")

        agent_process = subprocess.Popen(
            [python_exe, agent_script],
            cwd=BASE_DIR,
            stdout=None,
            stderr=None
        )

        log("Agent process started")

        # Wait a bit for agent to start
        time.sleep(5)

        # Verify the local API is available
        try:
            res = requests.get(f"{LOCAL_AGENT_URL}/health", timeout=5)
            if res.status_code == 200:
                log("Agent confirmed running")
            else:
                log(f"Agent health check failed: {res.status_code}")
        except Exception as e:
            log(f"Agent health check error: {e}")
            if agent_process and agent_process.poll() is None:
                try:
                    agent_process.kill()
                except Exception:
                    pass
            agent_process = None

    except Exception as e:
        log(f"Failed to start agent: {e}")
        agent_process = None


def stop_agent():
    global agent_process
    if agent_process and agent_process.poll() is None:
        log("Stopping agent process")
        try:
            agent_process.terminate()
            agent_process.wait(timeout=5)
        except Exception:
            try:
                agent_process.kill()
            except Exception:
                pass
    agent_process = None


# =========================
# UI
# =========================
root = tk.Tk()
root.title("⚡ Node IDE")
root.geometry("1200x750")
root.configure(bg="#1e1e1e")


def safe_ui(func):
    root.after(0, func)


root.protocol("WM_DELETE_WINDOW", on_close)

menu = tk.Frame(root, bg="#2d2d2d")
menu.pack(fill="x")

tk.Button(menu, text="Open", command=open_file).pack(side="left")
tk.Button(menu, text="Save", command=save_file).pack(side="left")
tk.Button(menu, text="Run", command=run_script).pack(side="left")
tk.Button(menu, text="Close All", command=close_all_tabs).pack(side="left")

language_var = tk.StringVar(value="python")
tk.OptionMenu(menu, language_var, "python", "java").pack(side="right")

main = tk.Frame(root)
main.pack(fill="both", expand=True)

# Metrics Panel
metrics_frame = tk.Frame(main, bg="#2d2d2d", height=100)
metrics_frame.pack(fill="x", side="bottom")
metrics_frame.pack_propagate(False)

tk.Label(metrics_frame, text="📊 Device Metrics", bg="#2d2d2d",
         fg="white", font=("Arial", 10, "bold")).pack(pady=5)

metrics_inner = tk.Frame(metrics_frame, bg="#2d2d2d")
metrics_inner.pack()

# CPU
tk.Label(metrics_inner, text="CPU:", bg="#2d2d2d",
         fg="white").grid(row=0, column=0, sticky="w")
cpu_label = tk.Label(metrics_inner, text="--%", bg="#2d2d2d", fg="#00ff00")
cpu_label.grid(row=0, column=1, sticky="w")
metrics_labels["cpu"] = cpu_label

# Memory
tk.Label(metrics_inner, text="Memory:", bg="#2d2d2d", fg="white").grid(
    row=0, column=2, sticky="w", padx=(20, 0))
mem_label = tk.Label(metrics_inner, text="--%", bg="#2d2d2d", fg="#00ff00")
mem_label.grid(row=0, column=3, sticky="w")
metrics_labels["memory"] = mem_label

# Temperature
tk.Label(metrics_inner, text="Temp:", bg="#2d2d2d", fg="white").grid(
    row=0, column=4, sticky="w", padx=(20, 0))
temp_label = tk.Label(metrics_inner, text="--°C", bg="#2d2d2d", fg="#00ff00")
temp_label.grid(row=0, column=5, sticky="w")
metrics_labels["temperature"] = temp_label

# Status
tk.Label(metrics_inner, text="Status:", bg="#2d2d2d", fg="white").grid(
    row=0, column=6, sticky="w", padx=(20, 0))
status_label = tk.Label(metrics_inner, text="Offline",
                        bg="#2d2d2d", fg="#ff6b6b")
status_label.grid(row=0, column=7, sticky="w")
metrics_labels["status"] = status_label

notebook = ttk.Notebook(main)
notebook.pack(fill="both", expand=True)

notebook.bind("<Button-3>", on_tab_right_click)

create_tab()

terminal = tk.Text(root, height=10, bg="black", fg="#00ff00", state="disabled")
terminal.pack(fill="x")

# =========================
# START
# =========================
log("UI started")

# Start agent
start_agent()

# Start metrics updater
update_metrics()

root.mainloop()
