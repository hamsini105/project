"""
Analytics page.

Six chart panels driven by live CandidateService aggregates.
Each chart is independently rendered into a panel-card container.
"""

from __future__ import annotations

import logging

import streamlit as st

from components.charts import (
    applications_trend,
    education_pie,
    experience_histogram,
    pipeline_funnel,
    score_by_role,
    score_histogram,
    skills_bar,
    status_donut,
)
from utils.data_service import CandidateService

logger = logging.getLogger(__name__)
_service = CandidateService()
_CHART_CONFIG = {"displayModeBar": False, "responsive": True}


def render_analytics() -> None:
    """Render the full Analytics tab with six Plotly chart panels."""
    logger.debug("Rendering analytics page")

    # ── Row 1: Pipeline funnel + Status donut ─────────────────────────────────
    r1_left, r1_right = st.columns(2, gap="medium")

    with r1_left:
        _chart_panel(
            title="Hiring Funnel",
            subtitle="Candidate throughput per pipeline stage",
            chart_fn=lambda: pipeline_funnel(_service.get_pipeline_stages()),
        )

    with r1_right:
        _chart_panel(
            title="Status Distribution",
            subtitle="Proportion of candidates per status",
            chart_fn=lambda: status_donut(_service.get_status_distribution()),
        )

    # ── Row 2: Score distribution + Score by role ─────────────────────────────
    r2_left, r2_right = st.columns(2, gap="medium")

    with r2_left:
        _chart_panel(
            title="ATS Score Distribution",
            subtitle="Score bands across the full candidate pool",
            chart_fn=lambda: score_histogram(_service.get_all()),
        )

    with r2_right:
        _chart_panel(
            title="Average Score by Role",
            subtitle="Comparative ATS performance across open positions",
            chart_fn=lambda: score_by_role(_service.get_score_by_role()),
        )

    # ── Row 3: Application trend + Experience distribution ────────────────────
    r3_left, r3_right = st.columns(2, gap="medium")

    with r3_left:
        _chart_panel(
            title="Application Volume",
            subtitle="Weekly inbound applications over the last 6 months",
            chart_fn=lambda: applications_trend(_service.get_applications_over_time()),
        )

    with r3_right:
        _chart_panel(
            title="Experience Distribution",
            subtitle="Years of experience across the candidate pool",
            chart_fn=lambda: experience_histogram(_service.get_all()),
        )

    # ── Row 4: Top skills + Education breakdown ───────────────────────────────
    r4_left, r4_right = st.columns(2, gap="medium")

    with r4_left:
        _chart_panel(
            title="Top Skills in Pipeline",
            subtitle="Most-frequent technical skills across all candidates",
            chart_fn=lambda: skills_bar(
                _service.get_skills_frequency(top_n=12).sort_values("count")
            ),
        )

    with r4_right:
        _chart_panel(
            title="Education Levels",
            subtitle="Highest qualification breakdown",
            chart_fn=lambda: education_pie(_service.get_education_distribution()),
        )


# ── Internal panel renderer ───────────────────────────────────────────────────

def _chart_panel(title: str, subtitle: str, chart_fn) -> None:
    """
    Render a titled panel-card with an embedded Plotly chart.

    ``chart_fn`` is called lazily so errors in one chart don't block others.
    """
    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>{title}</h3>
                <p>{subtitle}</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        fig = chart_fn()
        st.plotly_chart(fig, use_container_width=True, config=_CHART_CONFIG)
    except Exception as exc:
        logger.error("Chart render failed (%s): %s", title, exc)
        st.markdown(
            '<p style="color:var(--text-muted);font-size:0.8rem;padding:1rem 0;">Unable to render chart.</p>',
            unsafe_allow_html=True,
        )
    st.markdown("</section>", unsafe_allow_html=True)
