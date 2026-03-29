"""
Custom theme and CSS for the Insurance AI Pipeline dashboard.
Professional dark theme designed for executive demos.
"""

# ─── Brand colours ──────────────────────────────────────────
PRIMARY = "#6366F1"       # Indigo-500  – primary accent
PRIMARY_LIGHT = "#818CF8" # Indigo-400
SECONDARY = "#06B6D4"     # Cyan-500    – secondary accent
SUCCESS = "#10B981"       # Emerald-500
WARNING = "#F59E0B"       # Amber-500
DANGER = "#EF4444"        # Red-500
BG_DARK = "#0F172A"       # Slate-900
BG_CARD = "#1E293B"       # Slate-800
BG_CARD_HOVER = "#334155" # Slate-700
TEXT_PRIMARY = "#F8FAFC"   # Slate-50
TEXT_SECONDARY = "#94A3B8" # Slate-400
BORDER = "#334155"         # Slate-700

CUSTOM_CSS = """
<style>
/* ─── Global ─────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
}

/* ─── Hide default Streamlit chrome ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ─── Sidebar ────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border-right: 1px solid #334155;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F8FAFC;
}

/* ─── KPI Metric Cards ───────────── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px -5px rgba(99,102,241,0.25);
    border-color: #6366F1;
}
div[data-testid="stMetric"] label {
    color: #94A3B8 !important;
    font-weight: 500;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-weight: 700;
    font-size: 2rem;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-weight: 500;
}

/* ─── Cards / Containers ─────────── */
div[data-testid="stExpander"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    color: #F8FAFC;
    font-weight: 600;
}

/* ─── Tabs ────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #94A3B8;
    font-weight: 500;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366F1, #818CF8) !important;
    color: #F8FAFC !important;
    border-color: #6366F1 !important;
}

/* ─── Buttons ─────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #818CF8);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    transition: all 0.2s;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(99,102,241,0.5);
}

/* ─── Dataframes / Tables ─────────── */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}

/* ─── Text input / selectbox ──────── */
.stTextInput input, .stSelectbox select {
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}

/* ─── Custom hero section ─────────── */
.hero-container {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 50%, #1E1B4B 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 40px;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 0.5rem;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #94A3B8;
    margin-bottom: 0;
    line-height: 1.5;
}
.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6366F1, #818CF8);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 16px;
}

/* ─── Pipeline stage cards ────────── */
.stage-card {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s;
    height: 100%;
}
.stage-card:hover {
    border-color: #6366F1;
    box-shadow: 0 8px 25px -5px rgba(99,102,241,0.2);
}
.stage-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #6366F1, #818CF8);
    border-radius: 10px;
    color: white;
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 12px;
}
.stage-title {
    color: #F8FAFC;
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 6px;
}
.stage-desc {
    color: #94A3B8;
    font-size: 0.85rem;
    line-height: 1.4;
}

/* ─── Status badges ───────────────── */
.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.status-success { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.status-warning { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.status-error   { background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.3);  }
.status-info    { background: rgba(6,182,212,0.15);   color: #06B6D4; border: 1px solid rgba(6,182,212,0.3);  }

/* ─── Score/gauge display ─────────── */
.score-display {
    text-align: center;
    padding: 20px;
}
.score-value {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
}
.score-label {
    color: #94A3B8;
    font-size: 0.85rem;
    margin-top: 4px;
}

/* ─── Architecture diagram ────────── */
.arch-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 20px 0;
}
.arch-node {
    background: linear-gradient(135deg, #1E293B, #334155);
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 12px 18px;
    color: #F8FAFC;
    font-size: 0.85rem;
    font-weight: 500;
    text-align: center;
    min-width: 100px;
}
.arch-arrow {
    color: #6366F1;
    font-size: 1.4rem;
    font-weight: 700;
}

/* ─── Scrollbar ───────────────────── */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

/* ─── Animated gradient border ────── */
.gradient-border {
    position: relative;
    border-radius: 12px;
    padding: 1px;
    background: linear-gradient(135deg, #6366F1, #06B6D4, #6366F1);
    background-size: 200% 200%;
    animation: gradient-shift 3s ease infinite;
}
.gradient-border-inner {
    background: #0F172A;
    border-radius: 11px;
    padding: 24px;
}
@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
</style>
"""


def inject_css():
    """Call this at the top of every page to inject the custom CSS."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
