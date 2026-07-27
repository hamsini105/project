"""
Overview tab — main Recruiter Dashboard page.

Replaced placeholder charts with real Plotly visuals backed by CandidateService.
"""

from __future__ import annotations

import streamlit as st

from components.charts import (
    applications_trend,
    pipeline_funnel,
    skills_bar,
    status_donut,
)
from components.footer import render_footer
from components.metric_cards import MetricCardData, render_metric_cards
from components.navbar import render_navbar
from components.section_header import render_section_header
from components.sidebar import render_sidebar
from utils.data_service import CandidateService
from utils.formatters import format_number, format_percent
from utils.logger import get_logger

LOGGER = get_logger(__name__)
_service = CandidateService()
_CHART_CONFIG = {"displayModeBar": False, "responsive": True}


_ACTIVITY_ITEMS = [
    "Nina Patel moved 8 candidates into shortlist.",
    "Batch upload completed for Senior Python Engineer role.",
    "Recruiting Ops exported the Q3 candidate pipeline report.",
    "Team comment added on Data Platform Manager intake.",
    "ATS scoring complete for 27 new Machine Learning Engineer applications.",
    "Final Round interviews scheduled for 5 Frontend Engineer candidates.",
]


def _render_kpi_cards() -> None:
    kpi = _service.get_kpi_summary()
    render_metric_cards([
        MetricCardData(
            "Total Candidates",
            format_number(kpi["total_candidates"]),
            f"{kpi['active_roles']} active roles",
            "up",
        ),
        MetricCardData(
            "Avg ATS Score",
            str(kpi["avg_ats_score"]),
            "Across all pipeline stages",
            "neutral",
        ),
        MetricCardData(
            "Hired This Month",
            format_number(kpi["hired_this_month"]),
            f"Rejection rate: {format_percent(kpi['rejection_rate'])}",
            "up",
        ),
        MetricCardData(
            "Pending Screening",
            format_number(kpi["pending_review"]),
            "Awaiting first review",
            "neutral",
        ),
    ])


def _render_pipeline_funnel() -> None:
    stages_df = _service.get_pipeline_stages()
    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Hiring Funnel</h3>
                <p>Candidate volume through each pipeline stage</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not stages_df.empty:
        st.plotly_chart(pipeline_funnel(stages_df), use_container_width=True, config=_CHART_CONFIG)
    st.markdown("</section>", unsafe_allow_html=True)


def _render_status_donut() -> None:
    status_df = _service.get_status_distribution()
    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Status Distribution</h3>
                <p>Current snapshot of pipeline stage breakdown</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not status_df.empty:
        st.plotly_chart(status_donut(status_df), use_container_width=True, config=_CHART_CONFIG)
    st.markdown("</section>", unsafe_allow_html=True)


def _render_skills_and_trend() -> None:
    skills_left, trend_right = st.columns(2, gap="medium")
    with skills_left:
        skills_df = _service.get_skills_frequency(top_n=12)
        st.markdown(
            """
            <section class="panel-card fade-in-up">
                <div class="panel-card-header">
                    <h3>Top Skills in Pipeline</h3>
                    <p>Most-common skills across active candidates</p>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if not skills_df.empty:
            st.plotly_chart(
                skills_bar(skills_df.sort_values("count")),
                use_container_width=True, config=_CHART_CONFIG,
            )
        st.markdown("</section>", unsafe_allow_html=True)

    with trend_right:
        weekly_df = _service.get_applications_over_time()
        st.markdown(
            """
            <section class="panel-card fade-in-up">
                <div class="panel-card-header">
                    <h3>Application Volume</h3>
                    <p>Weekly intake over the last 6 months</p>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if not weekly_df.empty:
            st.plotly_chart(
                applications_trend(weekly_df),
                use_container_width=True, config=_CHART_CONFIG,
            )
        st.markdown("</section>", unsafe_allow_html=True)


def _render_activity_feed() -> None:
    items_html = "".join(f"<li>{item}</li>" for item in _ACTIVITY_ITEMS)
    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Recent Activity</h3>
                <p>Team operations over the last 24 hours</p>
            </div>
            <ul class="activity-feed">
                {items_html}
            </ul>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    """Render the full recruiter dashboard composed from reusable components."""
    LOGGER.info("Rendering dashboard UI")

    left, right = st.columns([1.1, 4], gap="large")

    with left:
        render_sidebar()

    with right:
        render_navbar()
        render_section_header(
            title="Hiring Command Center",
            description="Live pipeline metrics, candidate analytics, and team activity.",
        )
        _render_kpi_cards()

        chart_left, chart_right = st.columns(2, gap="medium")
        with chart_left:
            _render_pipeline_funnel()
        with chart_right:
            _render_status_donut()

        _render_skills_and_trend()
        _render_activity_feed()
        render_footer()
