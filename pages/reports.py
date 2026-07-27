"""
Reports page.

Provides report generation options (CSV and PDF) for the full
candidate pool with configurable scope and status filters.
"""

from __future__ import annotations

import logging

import streamlit as st

from components.export import render_csv_export, render_pdf_export
from components.status_badge import all_status_values
from utils.data_service import CandidateService
from utils.formatters import format_number

logger = logging.getLogger(__name__)
_service = CandidateService()


def render_reports() -> None:
    """Render the Reports tab with export configuration and download buttons."""
    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Report Generation</h3>
                <p>Export candidate data in CSV or PDF format</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_scope, col_status = st.columns(2, gap="medium")

    with col_scope:
        st.markdown(
            '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
            'margin:0 0 0.3rem;">SCOPE</p>',
            unsafe_allow_html=True,
        )
        scope = st.selectbox(
            "Scope",
            options=["All candidates", "Active pipeline only", "Hired only", "Rejected only"],
            label_visibility="collapsed",
            key="report_scope",
        )

    with col_status:
        st.markdown(
            '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
            'margin:0 0 0.3rem;">FILTER BY STATUS</p>',
            unsafe_allow_html=True,
        )
        status_filter = st.multiselect(
            "Status filter",
            options=all_status_values(),
            label_visibility="collapsed",
            key="report_status_filter",
        )

    st.markdown("</section>", unsafe_allow_html=True)

    # ── Build filtered DataFrame ──────────────────────────────────────────────
    df = _service.get_all()

    if scope == "Active pipeline only":
        active = ["Screening", "Phone Screen", "Technical Round", "Final Round"]
        df = df[df["status"].isin(active)]
    elif scope == "Hired only":
        df = df[df["status"] == "Hired"]
    elif scope == "Rejected only":
        df = df[df["status"] == "Rejected"]

    if status_filter:
        df = df[df["status"].isin(status_filter)]

    # ── Summary stats ─────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <section class="panel-card fade-in-up" style="margin-top:0.5rem;">
            <div class="panel-card-header">
                <h3>Report Preview</h3>
                <p>{format_number(len(df))} candidates match the selected scope</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        avg_score = df["ats_score"].mean()
        hired     = int((df["status"] == "Hired").sum())
        rejected  = int((df["status"] == "Rejected").sum())

        stat_cols = st.columns(4)
        _stat_box(stat_cols[0], "Candidates", format_number(len(df)))
        _stat_box(stat_cols[1], "Avg ATS Score", f"{avg_score:.1f}")
        _stat_box(stat_cols[2], "Hired",    format_number(hired))
        _stat_box(stat_cols[3], "Rejected", format_number(rejected))
    else:
        st.info("No candidates match the selected filters.")

    st.markdown("</section>", unsafe_allow_html=True)

    # ── Download buttons ──────────────────────────────────────────────────────
    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        dl_csv, dl_pdf = st.columns(2, gap="medium")

        scope_slug = scope.lower().replace(" ", "_")

        with dl_csv:
            render_csv_export(
                df,
                filename=f"candidates_{scope_slug}.csv",
                label="⬇ Download CSV Report",
            )
        with dl_pdf:
            render_pdf_export(
                df,
                filename=f"candidates_{scope_slug}.pdf",
                title=f"Candidate Report — {scope}",
                label="⬇ Download PDF Report",
            )


def _stat_box(col, label: str, value: str) -> None:
    with col:
        st.markdown(
            f"""
            <div style="background:var(--bg-muted);border:1px solid var(--border-soft);
                        border-radius:var(--radius-sm);padding:0.7rem;text-align:center;">
                <p style="color:var(--text-muted);font-size:0.73rem;font-weight:600;margin:0;">{label}</p>
                <p style="color:var(--text-primary);font-size:1.1rem;font-weight:700;margin:0.15rem 0 0;">{value}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
