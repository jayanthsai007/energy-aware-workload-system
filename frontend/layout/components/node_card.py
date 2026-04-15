import streamlit as st
import plotly.graph_objects as go
import numpy as np


def render_node_card(title, cpu, color):

    with st.container():

        st.markdown("""
        <div class="glass-card">
        """, unsafe_allow_html=True)

        st.markdown(f"<b>{title}</b>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 2])

        # 📈 Chart
        with col1:
            x = list(range(20))
            y = np.random.randint(60, 90, size=20)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                mode='lines',
                line=dict(color=color, width=3),
                fill='tozeroy'
            ))

            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )

            st.plotly_chart(fig, use_container_width=True)

        # ⚡ Gauge
        with col2:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu,
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color}
                }
            ))

            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"}
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div class="node-meta">
        Temperature<br>
        Power: 42.1W<br>
        Voltage: 1.15V
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
