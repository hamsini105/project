"""Recruiter-facing dashboard page."""

from typing import Final

import streamlit as st

from components.footer import render_footer
from components.metric_cards import MetricCardData, render_metric_cards
from components.navbar import render_navbar
from components.section_header import render_section_header
from components.sidebar import render_sidebar
from utils.logger import get_logger

LOGGER = get_logger(__name__)

RECENT_UPLOAD_ROWS: Final[list[tuple[str, str, str, str]]] = [
    ("Senior Python Engineer", "uploaded 18 min ago", "42 files", "In review"),
    ("Product Designer", "uploaded 1 hr ago", "27 files", "Queued"),
    ("Talent Operations Lead", "uploaded 3 hrs ago", "13 files", "Completed"),
    ("Data Platform Manager", "uploaded yesterday", "35 files", "In review"),
]

ACTIVITY_ITEMS: Final[list[str]] = [
    "Nina Patel moved 8 candidates into shortlist.",
    "Batch upload completed for Product Designer role.",
    "Recruiting Ops exported weekly candidate pipeline report.",
    "Team comment added on Data Platform Manager intake.",
]


def _render_recent_uploads() -> None:
    """Render a realistic recent uploads table with placeholder values."""
    rows_html = "".join(
        f"""
        <tr>
            <td>{role}</td>
            <td>{timestamp}</td>
            <td>{volume}</td>
            <td><span class='status-pill'>{status}</span></td>
        </tr>
        """
        for role, timestamp, volume, status in RECENT_UPLOAD_ROWS
    )

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Recent Uploads</h3>
                <p>Latest recruiter activity from resume intake queues</p>
            </div>
            <table class="uploads-table">
                <thead>
                    <tr>
                        <th>Role</th>
                        <th>Uploaded</th>
                        <th>Volume</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_activity_feed() -> None:
    """Render timeline-style activity feed placeholders."""
    items_html = "".join(f"<li>{item}</li>" for item in ACTIVITY_ITEMS)

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Activity</h3>
                <p>Team operations over the last 24 hours</p>
            </div>
            <ul class="activity-feed">
                {items_html}
            </ul>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_analytics_placeholders() -> None:
    """Render non-functional analytics placeholders for future integration."""
    st.markdown(
        """
        <section class="analytics-grid">
            <article class="panel-card fade-in-up">
                <div class="panel-card-header">
                    <h3>Upload Velocity</h3>
                    <p>Weekly resume intake trend</p>
                </div>
                <div class="chart-placeholder">
                    <span>Chart placeholder</span>
                </div>
            </article>
            <article class="panel-card fade-in-up">
                <div class="panel-card-header">
                    <h3>Team Throughput</h3>
                    <p>Candidate review completion rate</p>
                </div>
                <div class="chart-placeholder">
                    <span>Chart placeholder</span>
                </div>
            </article>
            <article class="panel-card fade-in-up">
                <div class="panel-card-header">
                    <h3>Pipeline Health</h3>
                    <p>Status distribution snapshot</p>
                </div>
                <div class="chart-placeholder">
                    <span>Chart placeholder</span>
                </div>
            </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_quick_actions() -> None:
    """Render quick action placeholders in a reusable card style."""
    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Quick Actions</h3>
                <p>Shortcuts for common recruiter workflows</p>
            </div>
            <div class="quick-actions-grid">
                <div class="quick-action-item">
                    <h4>Create Candidate Batch</h4>
                    <p>Prepare a new intake group for an open role.</p>
                </div>
                <div class="quick-action-item">
                    <h4>Assign Reviewer</h4>
                    <p>Allocate team ownership for incoming resumes.</p>
                </div>
                <div class="quick-action-item">
                    <h4>Schedule Weekly Sync</h4>
                    <p>Coordinate hiring standup with recruiting partners.</p>
                </div>
            </div>
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
            description="Track hiring pipeline activity with a polished frontend-ready interface.",
        )

        render_metric_cards(
            [
                MetricCardData("Resumes Ingested", "1,284", "+8.6% vs last week", "up"),
                MetricCardData("Open Roles", "24", "+2 this week", "up"),
                MetricCardData("Avg Review Time", "2.4 days", "-11% cycle time", "up"),
                MetricCardData("Pending Reviews", "317", "Stable this week", "neutral"),
            ]
        )

        content_left, content_right = st.columns([1.7, 1.3], gap="large")
        with content_left:
            _render_recent_uploads()
        with content_right:
            _render_activity_feed()

        _render_analytics_placeholders()
        _render_quick_actions()
        render_footer()
