import streamlit as st
import plotly.graph_objects as go
import numpy as np


def render_main_chart():

    x = list(range(30))
    y = np.cumsum(np.random.randn(30)) + 5

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color='#00d4ff', width=3),
        fill='tozeroy'
    ))

    fig.update_layout(
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )

    st.plotly_chart(fig, use_container_width=True)
