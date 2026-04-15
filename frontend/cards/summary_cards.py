import streamlit as st


def render_summary(nodes):

    total = len(nodes)
    active = sum(1 for n in nodes if n.get("status") == "ACTIVE")

    col1, col2, col3 = st.columns(3)

    col1.metric("⚠ Issues", "2 Detected")
    col2.metric("Total Nodes", total)
    col3.metric("Active Nodes", active)
