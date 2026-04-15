import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
body {
    background-color: #0f172a;
    color: #e2e8f0;
}
.card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    padding: 15px;
    border-radius: 16px;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
}
.small {
    font-size: 12px;
    color: #94a3b8;
}
.alert {
    color: #f87171;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy-Aware Workload System")

# ---------------- Node Data ----------------
nodesData = [
    {"name": "Node 1", "cpu": 69, "color": "#22c55e"},
    {"name": "Node 2", "cpu": 83, "color": "#facc15"},
    {"name": "Node 3", "cpu": 95, "color": "#ef4444"},
    {"name": "Node 4", "cpu": 76, "color": "#fb923c"},
]

# Initialize session state
if "node_temps" not in st.session_state:
    st.session_state.node_temps = [
        list(np.random.uniform(60, 80, 10)) for _ in range(len(nodesData))
    ]

if "main_data" not in st.session_state:
    st.session_state.main_data = [2, 2.5, 2.7, 3, 3.8, 4.2, 4.5, 4.8, 5, 5.5]

# ---------------- Nodes Grid ----------------
cols = st.columns(4)

node_placeholders = []

for i, node in enumerate(nodesData):
    with cols[i]:
        placeholder = st.empty()
        node_placeholders.append((placeholder, node, i))

# ---------------- Stats ----------------
st.markdown("###")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="alert">⚠ Background Problems</div>
        <h2>2 Issues Detected</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div>Nodes Registered</div>
        <h2>8 Total Nodes</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div>Nodes Active</div>
        <h2>8 Total Nodes</h2>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Bottom Section ----------------
col_main, col_input = st.columns([2, 1])

main_chart_placeholder = col_main.empty()

with col_input:
    st.markdown("""
    <div class="card">
        <h3>Input Type</h3>
        <p><b>File:</b> data_sample.json</p>
        <p class="small">(batch, parameters...)</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- LIVE LOOP ----------------
while True:

    # ----- Update Node Charts -----
    for placeholder, node, i in node_placeholders:

        # update data
        data = st.session_state.node_temps[i]
        data.append(np.random.uniform(60, 80))
        data.pop(0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=data,
            mode='lines',
            line=dict(color=node["color"]),
        ))

        fig.update_layout(
            height=120,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        # progress circle HTML
        progress_html = f"""
        <div style="
            width:70px;height:70px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;
            background: conic-gradient({node['color']} 0% {node['cpu']}%, #1e293b {node['cpu']}%);
        ">
            {node['cpu']}%
        </div>
        """

        with placeholder.container():
            st.markdown(
                f"<div class='card'><h3>{node['name']}</h3>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)

            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown("""
                <p class="small">Temperature</p>
                <p>Power: 42.1W</p>
                <p>Voltage: 1.15V</p>
                """, unsafe_allow_html=True)

            with c2:
                st.markdown(progress_html, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ----- Update Main Chart -----
    st.session_state.main_data.append(np.random.uniform(4, 6))
    st.session_state.main_data.pop(0)

    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(
        y=st.session_state.main_data,
        mode='lines',
        fill='tozeroy'
    ))

    fig_main.update_layout(
        title="Nodes Performance",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    main_chart_placeholder.plotly_chart(fig_main, use_container_width=True)

    time.sleep(2)
