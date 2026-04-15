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
LOCAL_AGENT_URL = "http://127.0.0.1:8081"

# =========================
# GLOBALS
# =========================
tabs = {}
current_task = None

# =========================
# SAFE UI UPDATE
# =========================


def safe_ui(callback):
    root.after(0, callback)

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
    global current_task

    editor = get_editor()
    if not editor:
        return

    script = editor.get("1.0", tk.END).strip()

    append_log("\n📤 Sending task...\n")
    append_log(f"📝 Preview:\n{script[:120]}\n")

    def send():
        global current_task
        try:
            res = requests.post(
                f"{LOCAL_AGENT_URL}/run",
                json={
                    "script": script,
                    "language": language_var.get()
                }
            )
            data = res.json()
            current_task = data.get("task_id")

            safe_ui(lambda: append_log(f"✅ Task submitted → {current_task}\n"))

            # Start polling for results
            threading.Thread(target=poll_task_result, args=(
                current_task,), daemon=True).start()

        except Exception as e:
            safe_ui(lambda: append_log(f"❌ {e}\n"))

    threading.Thread(target=send, daemon=True).start()

# =========================
# TASK RESULT POLLING
# =========================


def poll_task_result(task_id):
    BACKEND_URL = "http://127.0.0.1:8000"
    while True:
        try:
            res = requests.get(f"{BACKEND_URL}/task/{task_id}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "completed":
                    safe_ui(lambda: show_task_result(data))
                    break
                elif data.get("status") == "failed":
                    safe_ui(lambda: append_log(f"❌ Task failed: {task_id}\n"))
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


# =========================
# CLOSE HANDLER (CLEAN)
# =========================


def on_close():
    append_log("🛑 Closing UI...\n")
    root.destroy()


# =========================
# UI
# =========================
root = tk.Tk()
root.title("⚡ Node IDE")
root.geometry("1200x750")
root.configure(bg="#1e1e1e")

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

root.mainloop()
