import streamlit as st


def apply_theme():
    st.markdown("""
    <style>

    html, body, .stApp {
        background: linear-gradient(135deg, #0f172a, #1e1b4b, #0f766e);
        color: white;
    }

    .glass-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 15px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        height: 220px;
    }

    .node-meta {
        font-size: 12px;
        opacity: 0.8;
        margin-top: 5px;
    }

    /* Summary cards */
    .summary-card {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }

    </style>
    """, unsafe_allow_html=True)
