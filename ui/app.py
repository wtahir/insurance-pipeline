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
from ui.components.widgets import (
    render_hero,
    render_pipeline_flow,
    render_tech_stack,
    render_kpi_row,
    render_stage_card,
    load_json,
    get_pdf_count,
    get_file_mod_time,
)

# ─── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance AI Pipeline",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ─── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.5rem;">🏛️</div>
        <div style="font-size:1.2rem; font-weight:700; color:#F8FAFC; margin-top:4px;">
            Insurance AI
        </div>
        <div style="font-size:0.8rem; color:#94A3B8; margin-top:2px;">
            Intelligent Document Pipeline
        </div>
    </div>
    <hr style="border-color:#334155; margin:16px 0;">
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "📄 Pipeline Runner",
            "🔍 Document Explorer",
            "💬 Query Interface",
            "📊 Evaluation Dashboard",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#334155; margin:16px 0;'>", unsafe_allow_html=True)

    # Quick stats in sidebar
    pdf_count = get_pdf_count()
    st.caption(f"📂 {pdf_count} documents loaded")

    ingestion_summary = load_json("ingestion_summary.json")
    if ingestion_summary:
        st.caption(f"✅ {ingestion_summary.get('successful', 0)} ingested")
    st.caption(f"🕒 Last run: {get_file_mod_time('ingestion_summary.json')}")

    st.markdown("""
    <div style="position:fixed; bottom:16px; left:16px; right:16px; max-width:250px;">
        <div style="font-size:0.7rem; color:#475569; text-align:center;">
            Built with ❤️ by <b style="color:#94A3B8;">Waqas</b><br>
            AI & Data Engineering
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Page router ─────────────────────────────────────────────
if page == "🏠 Overview":
    from ui.pages.overview import render
    render()
elif page == "📄 Pipeline Runner":
    from ui.pages.pipeline_runner import render
    render()
elif page == "🔍 Document Explorer":
    from ui.pages.document_explorer import render
    render()
elif page == "💬 Query Interface":
    from ui.pages.query_interface import render
    render()
elif page == "📊 Evaluation Dashboard":
    from ui.pages.evaluation import render
    render()
