import streamlit as st
import pandas as pd
import numpy as np

from api import (
    get_nodes,
    get_metrics,
    get_executions
)

st.set_page_config(layout="wide")

# =========================
# 🎨 MODERN UI STYLING
# =========================
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #0f1116;
    color: white;
}

/* Card */
.card {
    background-color: #151922;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #2a2f3a;
    transition: 0.2s;
}
.card:hover {
    border: 1px solid #4da3ff;
    transform: scale(1.02);
}

/* Status dots */
.green {color: #00ff9f;}
.yellow {color: #ffd166;}
.red {color: #ff4b4b;}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔁 SESSION STATE NAV
# =========================
if "view" not in st.session_state:
    st.session_state.view = "home"

if "selected_node" not in st.session_state:
    st.session_state.selected_node = None

# =========================
# 📡 SAFE FETCH
# =========================
def safe_fetch(func):
    try:
        return func()
    except:
        return []

nodes = safe_fetch(get_nodes)
metrics = safe_fetch(get_metrics)
executions = safe_fetch(get_executions)

df_nodes = pd.DataFrame(nodes) if nodes else pd.DataFrame()
df_metrics = pd.DataFrame(metrics) if metrics else pd.DataFrame()
df_exec = pd.DataFrame(executions) if executions else pd.DataFrame()

# =========================
# 🧩 HOME → NODE GRID
# =========================
def show_home():

    st.title("🧠 Node Dashboard")

    if df_nodes.empty:
        st.warning("No nodes connected")
        return

    cols = st.columns(3)

    for i, node in df_nodes.iterrows():

        with cols[i % 3]:

            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)

                node_id = node.get("agent_id", f"Node-{i}")
                status = str(node.get("status", "unknown")).lower()

                # Status color
                if status in ["active", "online"]:
                    color = "green"
                else:
                    color = "red"

                st.markdown(f"### {node_id}")
                st.markdown(f"Status: <span class='{color}'>● {status}</span>", unsafe_allow_html=True)

                # Dummy / fallback metrics
                cpu = np.random.randint(10, 90)
                mem = np.random.randint(20, 95)

                st.progress(cpu / 100)
                st.caption(f"CPU: {cpu}%")

                st.progress(mem / 100)
                st.caption(f"Memory: {mem}%")

                # Mini chart
                chart_data = pd.DataFrame({
                    "cpu": np.random.randint(20, 80, 20)
                })
                st.line_chart(chart_data)

                # Button → Deep Dive
                if st.button("View Details", key=f"btn_{i}"):
                    st.session_state.view = "detail"
                    st.session_state.selected_node = node_id

                st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 🔍 NODE DETAIL VIEW
# =========================
def show_detail():

    node_id = st.session_state.selected_node

    st.button("⬅ Back", on_click=lambda: st.session_state.update({"view": "home"}))

    st.title(f"🔍 Node Detail: {node_id}")

    # =========================
    # 📊 TOP METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    cpu = np.random.randint(20, 90)
    mem = np.random.randint(20, 90)
    energy = np.random.randint(50, 200)

    col1.metric("CPU Usage", f"{cpu}%")
    col2.metric("Memory Usage", f"{mem}%")
    col3.metric("Energy", f"{energy} W")

    # =========================
    # 📈 PERFORMANCE GRAPHS
    # =========================
    st.subheader("Performance")

    graph_data = pd.DataFrame({
        "cpu": np.random.randint(20, 90, 50),
        "memory": np.random.randint(30, 95, 50)
    })

    st.line_chart(graph_data)

    # =========================
    # ⚙️ DEVICE SPECS (VISUAL STYLE)
    # =========================
    st.subheader("Device Specifications")

    col1, col2, col3, col4 = st.columns(4)

    col1.info("🧠 CPU: Intel i7")
    col2.info("💾 RAM: 16 GB")
    col3.info("🎮 GPU: None")
    col4.info("🖥 OS: Linux")

    # =========================
    # 📋 TASKS
    # =========================
    st.subheader("Tasks")

    if not df_exec.empty:
        st.dataframe(df_exec, use_container_width=True)

    # =========================
    # 🧠 MODEL INPUT
    # =========================
    st.subheader("Model Input")

    sample_input = {
        "cpu": cpu,
        "memory": mem,
        "energy": energy
    }

    st.json(sample_input)


# =========================
# 🚦 ROUTER
# =========================
if st.session_state.view == "home":
    show_home()
else:
    show_detail()

# =========================
# ✨ FOOTER
# =========================
st.markdown("---")
st.caption("AI Energy-Aware Scheduler Dashboard")