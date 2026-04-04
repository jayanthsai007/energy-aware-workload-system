import streamlit as st
import pandas as pd
import numpy as np
import time

from api import (
    get_nodes,
    get_metrics,
    get_executions
)

st.set_page_config(layout="wide")

# =========================
# 🎨 DARK THEME STYLING
# =========================
st.markdown("""
<style>
body {
    background-color: #0f1116;
}
[data-testid="stAppViewContainer"] {
    background-color: #0f1116;
    color: white;
}
.sidebar .sidebar-content {
    background-color: #0f1116;
}
.metric-box {
    border: 1px solid #2a2f3a;
    padding: 10px;
}
.status-green {color: #00ff9f;}
.status-yellow {color: #ffd166;}
.status-red {color: #ff4b4b;}
</style>
""", unsafe_allow_html=True)

# =========================
# 📌 SIDEBAR
# =========================
st.sidebar.title("⚙️ Scheduler")

menu = st.sidebar.radio(
    "Navigation",
    ["Overview", "Nodes", "Tasks", "Performance", "Model Insights"]
)

# =========================
# 🔄 AUTO REFRESH
# =========================
st.markdown("""
<script>
setTimeout(function(){
    window.location.reload();
}, 3000);
</script>
""", unsafe_allow_html=True)

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

df_metrics = pd.DataFrame(metrics) if metrics else pd.DataFrame()
df_nodes = pd.DataFrame(nodes) if nodes else pd.DataFrame()
df_exec = pd.DataFrame(executions) if executions else pd.DataFrame()

# =========================
# 📊 OVERVIEW
# =========================
if menu == "Overview":

    st.title("🧠 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    cpu = df_metrics["cpu"].mean() if not df_metrics.empty else 0
    mem = df_metrics["memory"].mean() if not df_metrics.empty else 0
    nodes_active = len(df_nodes)
    tasks_running = len(df_exec)

    col1.metric("CPU Load", f"{cpu:.2f}%")
    col2.metric("Memory", f"{mem:.2f}%")
    col3.metric("Active Nodes", nodes_active)
    col4.metric("Tasks", tasks_running)

# =========================
# 📈 PERFORMANCE TAB
# =========================
elif menu == "Performance":

    st.title("📈 Performance")

    if not df_metrics.empty:

        st.subheader("CPU Load")
        st.line_chart(df_metrics["cpu"])

        st.subheader("Memory Usage")
        st.area_chart(df_metrics["memory"])

# =========================
# 🖥️ NODES TAB
# =========================
elif menu == "Nodes":

    st.title("🖥️ Nodes")

    if not df_nodes.empty:

        def highlight_status(val):
            if str(val).lower() in ["active", "online"]:
                return "color: #00ff9f;"
            return "color: #ff4b4b;"

        if "status" in df_nodes.columns:
            st.dataframe(
                df_nodes.style.map(highlight_status, subset=["status"]),
                use_container_width=True
            )
        else:
            st.dataframe(df_nodes, use_container_width=True)

# =========================
# 📋 TASKS TAB (PROCESS TABLE)
# =========================
elif menu == "Tasks":

    st.title("📋 Active Tasks")

    if not df_exec.empty:

        df_exec_display = df_exec.copy()

        # Add dummy status if not present
        if "status" not in df_exec_display.columns:
            df_exec_display["status"] = "running"

        def color_status(val):
            if val == "running":
                return "color: #00ff9f;"
            elif val == "waiting":
                return "color: #ffd166;"
            else:
                return "color: #ff4b4b;"

        st.dataframe(
            df_exec_display.style.map(color_status, subset=["status"]),
            use_container_width=True
        )

# =========================
# 🤖 MODEL INSIGHTS
# =========================
elif menu == "Model Insights":

    st.title("🤖 Model Insights")

    if not df_exec.empty:

        st.subheader("Execution Time Trend")
        st.line_chart(df_exec["execution_time"])

        st.subheader("CPU vs Memory Usage")
        if "cpu_avg" in df_exec.columns and "memory_avg" in df_exec.columns:
            chart_data = df_exec[["cpu_avg", "memory_avg"]]
            st.line_chart(chart_data)

# =========================
# ✨ FOOTER
# =========================
st.markdown("---")
st.caption("AI Energy-Aware Scheduler Dashboard")
