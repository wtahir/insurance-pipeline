"""
Reusable UI components for the Insurance AI Pipeline dashboard.
"""

import streamlit as st
import json
import os
from datetime import datetime

# ─── Data loading helpers ─────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")


def load_json(filename: str):
    """Load a JSON file from the output directory. Returns None on failure."""
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_file_mod_time(filename: str) -> str:
    """Get the last modified time of an output file."""
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return "Never"
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts).strftime("%b %d, %Y %H:%M")


def get_pdf_count() -> int:
    """Count PDFs in the data/pdfs folder."""
    pdf_dir = os.path.join(BASE_DIR, "data", "pdfs")
    if not os.path.exists(pdf_dir):
        return 0
    return len([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")])


# ─── UI component helpers ──────────────────────────────────────

def render_hero(title: str, subtitle: str, badge: str = None):
    """Render a hero section at the top of a page."""
    badge_html = f'<div class="hero-badge">{badge}</div>' if badge else ""
    st.markdown(f"""
    <div class="hero-container">
        {badge_html}
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stage_card(number: int, title: str, description: str, icon: str = ""):
    """Render a single pipeline stage card."""
    st.markdown(f"""
    <div class="stage-card">
        <div class="stage-number">{number}</div>
        <div class="stage-title">{icon} {title}</div>
        <div class="stage-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Return HTML for a status badge."""
    css_class = {
        "success": "status-success",
        "failed": "status-error",
        "warning": "status-warning",
        "skipped": "status-warning",
        "info": "status-info",
        "running": "status-info",
    }.get(status.lower(), "status-info")
    return f'<span class="status-badge {css_class}">{status}</span>'


def render_score_gauge(value: float, max_val: float, label: str, color: str = "#6366F1"):
    """Render a large score display."""
    pct = (value / max_val * 100) if max_val > 0 else 0
    st.markdown(f"""
    <div class="score-display">
        <div class="score-value" style="color: {color};">{value:.1f}<span style="font-size:1.2rem;color:#94A3B8;">/{max_val:.0f}</span></div>
        <div class="score-label">{label}</div>
        <div style="margin-top:12px; background:#1E293B; border-radius:6px; height:8px; overflow:hidden;">
            <div style="width:{pct}%; height:100%; background:linear-gradient(90deg, {color}, {color}88); border-radius:6px; transition: width 1s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_flow():
    """Render the pipeline architecture flow diagram."""
    st.markdown("""
    <div class="arch-flow">
        <div class="arch-node">📄 PDF Upload</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">🔍 Ingestion</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">🤖 Extraction</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">✂️ Chunking</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">📐 Embedding</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">🔎 Retrieval</div>
        <div class="arch-arrow">→</div>
        <div class="arch-node">📊 Evaluation</div>
    </div>
    """, unsafe_allow_html=True)


def render_tech_stack():
    """Render the technology stack section."""
    st.markdown("""
    <div style="display:flex; flex-wrap:wrap; gap:10px; padding:12px 0;">
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🐍 Python</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🧠 GPT-4o (Azure)</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🗄️ ChromaDB</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🔗 LangChain</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🧮 Sentence Transformers</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            📊 Streamlit</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🐳 Docker</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            🥬 Celery + Redis</span>
        <span style="background:#1E293B; border:1px solid #334155; padding:6px 14px; border-radius:20px; font-size:0.8rem; color:#94A3B8;">
            📑 Pydantic</span>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_row(metrics: list[dict]):
    """
    Render a row of KPI metrics.
    Each dict: {"label": str, "value": str|int, "delta": str|None, "icon": str}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            col.metric(
                label=f"{m.get('icon', '')} {m['label']}",
                value=m["value"],
                delta=m.get("delta"),
            )
