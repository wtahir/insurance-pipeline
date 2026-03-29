"""
Document Explorer page — Browse, search, and inspect all ingested
and extracted insurance documents with rich metadata display.
"""

import streamlit as st
import pandas as pd
import json
import os

from ui.components.theme import inject_css
from ui.components.widgets import (
    render_hero,
    render_status_badge,
    render_kpi_row,
    load_json,
    get_pdf_count,
)


def render():
    inject_css()

    render_hero(
        title="Document Explorer",
        subtitle="Browse, search, and inspect all ingested and extracted insurance documents. "
                 "View extracted metadata, classification results, and original content.",
        badge="Data Explorer",
    )

    # ─── Load data ─────────────────────────────────────────
    extracted = load_json("extracted_data.json")
    ingested = load_json("ingested_data.json")

    if not extracted and not ingested:
        st.warning("⚠️ No data available. Run the pipeline first to ingest and extract documents.")
        return

    # Use extracted if available, else ingested
    docs = extracted if extracted else ingested
    data_source = "Extracted" if extracted else "Ingested"

    # ─── KPIs ─────────────────────────────────────────────
    total = len(docs)
    successful = sum(1 for d in docs if d.get("status") == "success")
    failed = sum(1 for d in docs if d.get("status") == "failed")
    skipped = sum(1 for d in docs if d.get("status") == "skipped")

    doc_types = {}
    languages = {}
    urgency_counts = {}
    for d in docs:
        if d.get("status") == "success":
            dt = d.get("document_type", "unknown")
            doc_types[dt] = doc_types.get(dt, 0) + 1
            lang = d.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            urg = d.get("urgency", "normal")
            urgency_counts[urg] = urgency_counts.get(urg, 0) + 1

    render_kpi_row([
        {"label": "Total Documents", "value": total, "icon": "📄"},
        {"label": "Successful", "value": successful, "icon": "✅"},
        {"label": "Failed", "value": failed, "icon": "❌"},
        {"label": "Document Types", "value": len(doc_types), "icon": "🏷️"},
        {"label": "Languages", "value": len(languages), "icon": "🌐"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Filters ──────────────────────────────────────────
    st.markdown("### 🔍 Search & Filter")
    filter_cols = st.columns([3, 2, 2, 2])

    with filter_cols[0]:
        search_query = st.text_input("🔎 Search by filename or content", placeholder="Type to search...")
    with filter_cols[1]:
        type_options = ["All"] + sorted(doc_types.keys())
        selected_type = st.selectbox("Document Type", type_options)
    with filter_cols[2]:
        status_options = ["All", "success", "failed", "skipped"]
        selected_status = st.selectbox("Status", status_options)
    with filter_cols[3]:
        urgency_options = ["All"] + sorted(urgency_counts.keys())
        selected_urgency = st.selectbox("Urgency", urgency_options)

    # Apply filters
    filtered = docs
    if search_query:
        q = search_query.lower()
        filtered = [d for d in filtered if
                    q in d.get("file_name", "").lower() or
                    q in d.get("summary_en", "").lower() or
                    q in d.get("claim_number", "").lower() or
                    q in d.get("original_content", d.get("content", "")).lower()]
    if selected_type != "All":
        filtered = [d for d in filtered if d.get("document_type") == selected_type]
    if selected_status != "All":
        filtered = [d for d in filtered if d.get("status") == selected_status]
    if selected_urgency != "All":
        filtered = [d for d in filtered if d.get("urgency") == selected_urgency]

    st.markdown(f"**Showing {len(filtered)} of {total} documents**")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Visualisations ──────────────────────────────────
    if doc_types and len(doc_types) > 0:
        viz_cols = st.columns(3)

        with viz_cols[0]:
            st.markdown("**📊 By Document Type**")
            import plotly.express as px
            df_types = pd.DataFrame([{"Type": k.replace("_", " ").title(), "Count": v} for k, v in doc_types.items()])
            fig = px.bar(df_types, x="Type", y="Count",
                         color_discrete_sequence=["#6366F1"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", height=250,
                margin=dict(l=20, r=20, t=10, b=40),
                xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"),
            )
            st.plotly_chart(fig, width='stretch')

        with viz_cols[1]:
            st.markdown("**🌐 By Language**")
            df_lang = pd.DataFrame([{"Language": k.upper(), "Count": v} for k, v in languages.items()])
            fig = px.pie(df_lang, names="Language", values="Count",
                         color_discrete_sequence=["#06B6D4", "#6366F1", "#10B981", "#F59E0B"],
                         hole=0.4)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", height=250,
                margin=dict(l=20, r=20, t=10, b=20),
            )
            st.plotly_chart(fig, width='stretch')

        with viz_cols[2]:
            st.markdown("**🚨 By Urgency**")
            df_urg = pd.DataFrame([{"Urgency": k.title(), "Count": v} for k, v in urgency_counts.items()])
            urg_colors = {"Low": "#10B981", "Normal": "#06B6D4", "High": "#EF4444"}
            fig = px.bar(df_urg, x="Urgency", y="Count",
                         color="Urgency",
                         color_discrete_map=urg_colors)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", height=250, showlegend=False,
                margin=dict(l=20, r=20, t=10, b=40),
                xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"),
            )
            st.plotly_chart(fig, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Document table ───────────────────────────────────
    st.markdown("### 📑 Document List")

    # Build summary table
    table_data = []
    for d in filtered:
        row = {
            "File": d.get("file_name", "—"),
            "Status": d.get("status", "—"),
            "Type": d.get("document_type", "—").replace("_", " ").title() if d.get("document_type") else "—",
            "Language": d.get("language", "—").upper() if d.get("language") else "—",
            "Claim #": d.get("claim_number", "—") or "—",
            "Date": d.get("date", "—") or "—",
            "Urgency": d.get("urgency", "—") or "—",
            "Confidence": f"{d.get('confidence', 0):.0%}" if d.get("confidence") else "—",
            "Summary": (d.get("summary_en", "") or "")[:100] + "..." if d.get("summary_en") else "—",
        }
        table_data.append(row)

    if table_data:
        df = pd.DataFrame(table_data)

        # Color-coded status
        def style_status(val):
            colors = {"success": "#10B981", "failed": "#EF4444", "skipped": "#F59E0B"}
            color = colors.get(val, "#94A3B8")
            return f"color: {color}; font-weight: 600"

        def style_urgency(val):
            colors = {"high": "#EF4444", "normal": "#06B6D4", "low": "#10B981"}
            color = colors.get(str(val).lower(), "#94A3B8")
            return f"color: {color}; font-weight: 600"

        styled = df.style.map(style_status, subset=["Status"])
        styled = styled.map(style_urgency, subset=["Urgency"])

        st.dataframe(
            styled,
            width='stretch',
            height=400,
            hide_index=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Document detail viewer ───────────────────────────
    st.markdown("### 🔬 Document Detail View")

    filenames = [d.get("file_name", "unknown") for d in filtered]
    if filenames:
        selected_file = st.selectbox("Select a document to inspect", filenames)
        selected_doc = next((d for d in filtered if d.get("file_name") == selected_file), None)

        if selected_doc:
            detail_tabs = st.tabs(["📋 Metadata", "📝 Summary", "📄 Original Content"])

            with detail_tabs[0]:
                meta_cols = st.columns(3)
                meta_fields = [
                    ("File Name", selected_doc.get("file_name")),
                    ("Status", selected_doc.get("status")),
                    ("Document Type", selected_doc.get("document_type", "").replace("_", " ").title()),
                    ("Language", selected_doc.get("language", "").upper()),
                    ("Claim Number", selected_doc.get("claim_number")),
                    ("Date", selected_doc.get("date")),
                    ("Sender", selected_doc.get("sender")),
                    ("Recipient", selected_doc.get("recipient")),
                    ("Subject", selected_doc.get("subject")),
                    ("Urgency", selected_doc.get("urgency")),
                    ("Confidence", f"{selected_doc.get('confidence', 0):.0%}" if selected_doc.get("confidence") else None),
                    ("Action Required", selected_doc.get("action_required")),
                    ("Total Pages", selected_doc.get("total_pages")),
                    ("Failed Pages", selected_doc.get("failed_pages")),
                    ("Attachments", ", ".join(selected_doc.get("attachments_mentioned", []))),
                ]

                for i, (label, value) in enumerate(meta_fields):
                    if value is not None and value != "" and value != []:
                        with meta_cols[i % 3]:
                            st.markdown(f"""
                            <div style="background:#1E293B; border:1px solid #334155; border-radius:8px;
                                        padding:12px; margin-bottom:8px;">
                                <div style="color:#94A3B8; font-size:0.75rem; text-transform:uppercase;
                                            letter-spacing:0.05em;">{label}</div>
                                <div style="color:#F8FAFC; font-size:0.95rem; font-weight:500;
                                            margin-top:4px;">{value}</div>
                            </div>
                            """, unsafe_allow_html=True)

            with detail_tabs[1]:
                summary = selected_doc.get("summary_en", "")
                if summary:
                    st.markdown(f"""
                    <div style="background:#1E293B; border:1px solid #334155; border-radius:12px;
                                padding:24px; line-height:1.6; color:#F8FAFC;">
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No summary available for this document.")

            with detail_tabs[2]:
                content = selected_doc.get("original_content", selected_doc.get("content", ""))
                if content:
                    st.code(content[:5000], language="text")
                    if len(content) > 5000:
                        st.caption(f"Showing first 5000 characters of {len(content)} total.")
                else:
                    st.info("No content available.")
    else:
        st.info("No documents match current filters.")
