"""
Insurance AI Pipeline — Executive Dashboard
=============================================
A professional demo UI for the end-to-end insurance document
processing pipeline.  Run with:

    streamlit run ui/app.py

Navigate using the sidebar to explore each pipeline stage,
query documents, and review evaluation results.
"""

import streamlit as st
import sys
import os

# Ensure project root is on the path so stage imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.components.theme import inject_css
from ui.components.runtime import is_demo_mode

# ─── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance AI Pipeline",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide default Streamlit multipage nav and deploy button
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

inject_css()
demo_mode = is_demo_mode()


# ─── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:1.2rem; font-weight:700; color:#F8FAFC; margin-top:4px;">
            Insurance AI Pipeline
        </div>
    </div>
    <hr style="border-color:#334155; margin:16px 0;">
    """, unsafe_allow_html=True)

    if demo_mode:
        st.markdown(
            "<div style='color:#F59E0B; font-size:0.8rem; font-weight:600; text-align:center; margin-bottom:10px;'>DEMO MODE (Read-only)</div>",
            unsafe_allow_html=True,
        )

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Pipeline Runner",
            "Document Explorer",
            "Query Interface",
            "Evaluation",
        ],
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style="position:fixed; bottom:16px; left:16px; right:16px; max-width:250px;">
        <div style="font-size:0.7rem; color:#475569; text-align:center;">
            Built by <b style="color:#94A3B8;">Waqas</b> — AI & Data Engineering
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Page router ─────────────────────────────────────────────
if page == "Overview":
    from ui.pages.overview import render
    render()
elif page == "Pipeline Runner":
    from ui.pages.pipeline_runner import render
    render()
elif page == "Document Explorer":
    from ui.pages.document_explorer import render
    render()
elif page == "Query Interface":
    from ui.pages.query_interface import render
    render()
elif page == "Evaluation":
    from ui.pages.evaluation import render
    render()
