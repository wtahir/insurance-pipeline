"""
Overview page — Executive summary with KPIs, pipeline architecture,
and high-level health indicators.
"""

import streamlit as st
import json
import os
from ui.components.theme import inject_css
from ui.components.widgets import (
    render_hero,
    render_pipeline_flow,
    render_tech_stack,
    render_kpi_row,
    render_stage_card,
    render_score_gauge,
    load_json,
    get_pdf_count,
    get_file_mod_time,
)


def render():
    inject_css()

    # ─── Hero ─────────────────────────────────────────────
    render_hero(
        title="Insurance Document Intelligence",
        subtitle="End-to-end AI pipeline that ingests, classifies, chunks, embeds, and queries "
                 "insurance claim documents — transforming unstructured PDFs into actionable insights.",
        badge="AI-Powered Pipeline",
    )

    # ─── Top-level KPIs ──────────────────────────────────
    ingestion = load_json("ingestion_summary.json")
    extraction = load_json("extraction_summary.json")
    chunking = load_json("chunking_summary.json")
    embedding = load_json("embedding_summary.json")
    evaluation = load_json("evaluation_summary.json")

    pdf_count = get_pdf_count()
    ingested = ingestion.get("successful", 0) if ingestion else 0
    extracted = extraction.get("successful", 0) if extraction else 0
    chunks = chunking.get("total_chunks_produced", 0) if chunking else 0
    vectors = embedding.get("total_vectors_in_collection", 0) if embedding else 0

    render_kpi_row([
        {"label": "Source PDFs", "value": pdf_count, "icon": "📂"},
        {"label": "Ingested", "value": ingested, "icon": "📥",
         "delta": f"{ingestion.get('failed', 0)} failed" if ingestion and ingestion.get("failed") else None},
        {"label": "Extracted", "value": extracted, "icon": "🤖",
         "delta": f"{extraction.get('failed', 0)} failed" if extraction and extraction.get("failed") else None},
        {"label": "Chunks Created", "value": chunks, "icon": "✂️"},
        {"label": "Vectors Stored", "value": vectors, "icon": "📐"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Pipeline Architecture ───────────────────────────
    st.markdown("### 🏗️ Pipeline Architecture")
    render_pipeline_flow()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Stage Details ───────────────────────────────────
    st.markdown("### 📋 Pipeline Stages")
    cols = st.columns(6)

    stages = [
        (1, "Ingestion", "PDF parsing with pdfplumber, text extraction, metadata capture", "📄"),
        (2, "Extraction", "GPT-4o classification & structured field extraction with Pydantic validation", "🤖"),
        (3, "Chunking", "Sentence-aware splitting with overlap, word-boundary respect", "✂️"),
        (4, "Embedding", "Multilingual sentence-transformers → ChromaDB vector store", "📐"),
        (5, "Retrieval", "Semantic search + GPT-4o RAG answer generation", "🔎"),
        (6, "Evaluation", "GPT-4o-as-judge scoring retrieval & answer quality", "📊"),
    ]

    for col, (num, title, desc, icon) in zip(cols, stages):
        with col:
            render_stage_card(num, title, desc, icon)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Two-column: Evaluation + Doc Types ──────────────
    left, right = st.columns(2)

    with left:
        st.markdown("### 📈 Evaluation Scores")
        if evaluation:
            score_cols = st.columns(2)
            with score_cols[0]:
                avg_ret = evaluation.get("avg_retrieval_score", 0)
                color = "#10B981" if avg_ret >= 4 else "#F59E0B" if avg_ret >= 3 else "#EF4444"
                render_score_gauge(avg_ret, 5, "Avg Retrieval Score", color)
            with score_cols[1]:
                avg_ans = evaluation.get("avg_answer_score", 0)
                color = "#10B981" if avg_ans >= 4 else "#F59E0B" if avg_ans >= 3 else "#EF4444"
                render_score_gauge(avg_ans, 5, "Avg Answer Score", color)

            # Failure breakdown
            failures = evaluation.get("failure_type_breakdown", {})
            if failures:
                st.markdown("**Failure Breakdown**")
                for ftype, count in failures.items():
                    icon = "✅" if ftype == "none" else "⚠️" if ftype in ("retrieval", "generation") else "❌"
                    st.markdown(f"{icon} **{ftype.title()}**: {count} queries")
        else:
            st.info("No evaluation data yet. Run Stage 6 to see scores.")

    with right:
        st.markdown("### 📑 Document Types Found")
        if extraction:
            doc_types = extraction.get("document_types_found", {})
            if doc_types:
                import plotly.express as px
                import pandas as pd

                df = pd.DataFrame([
                    {"Type": k.replace("_", " ").title(), "Count": v}
                    for k, v in doc_types.items()
                ])
                fig = px.pie(
                    df, names="Type", values="Count",
                    color_discrete_sequence=["#6366F1", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"],
                    hole=0.4,
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#F8FAFC",
                    legend=dict(font=dict(color="#94A3B8")),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300,
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No document types detected yet.")
        else:
            st.info("No extraction data yet. Run Stage 2 to see results.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Technology Stack ────────────────────────────────
    st.markdown("### 🛠️ Technology Stack")
    render_tech_stack()

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Last Run Times ──────────────────────────────────
    st.markdown("### 🕒 Stage Run History")
    run_cols = st.columns(6)
    stage_files = [
        ("Ingestion", "ingestion_summary.json"),
        ("Extraction", "extraction_summary.json"),
        ("Chunking", "chunking_summary.json"),
        ("Embedding", "embedding_summary.json"),
        ("Retrieval", "query_log.json"),
        ("Evaluation", "evaluation_summary.json"),
    ]
    for col, (name, fname) in zip(run_cols, stage_files):
        with col:
            mod_time = get_file_mod_time(fname)
            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #334155; border-radius:10px;
                        padding:14px; text-align:center;">
                <div style="color:#94A3B8; font-size:0.75rem; text-transform:uppercase;
                            letter-spacing:0.05em; margin-bottom:4px;">{name}</div>
                <div style="color:#F8FAFC; font-size:0.85rem; font-weight:500;">{mod_time}</div>
            </div>
            """, unsafe_allow_html=True)
