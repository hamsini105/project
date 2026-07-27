"""Frontend entrypoint for the Resume Parser System dashboard."""

from pathlib import Path

import streamlit as st

from components.footer import render_footer
from components.navbar import render_navbar
from components.section_header import render_section_header
from components.sidebar import render_sidebar
from pages.analytics import render_analytics
from pages.candidates import render_candidates
from pages.dashboard import render_dashboard as render_overview_tab
from pages.reports import render_reports
from utils.logger import get_logger

LOGGER = get_logger(__name__)
CSS_FILES: tuple[str, ...] = (
    "theme.css", "layout.css", "cards.css", "responsive.css", "recruiter.css"
)


def configure_page() -> None:
    """Configure global Streamlit page metadata."""
    st.set_page_config(
        page_title="Resume Parser System",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def load_css(css_dir: Path) -> None:
    """Load external CSS files into the app in a deterministic order."""
    for css_name in CSS_FILES:
        css_path = css_dir / css_name
        if not css_path.exists():
            LOGGER.warning("CSS file not found: %s", css_path)
            continue
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def main() -> None:
    """Initialize the application shell and render the recruiter dashboard."""
    configure_page()
    load_css(Path(__file__).parent / "assets" / "css")

    try:
        left, right = st.columns([1.1, 4], gap="large")

        with left:
            render_sidebar()

        with right:
            render_navbar()
            render_section_header(
                title="Hiring Command Center",
                description="Live pipeline metrics, candidate management, and analytics.",
            )

            tab_overview, tab_candidates, tab_analytics, tab_reports = st.tabs([
                "📊  Overview",
                "👥  Candidates",
                "📈  Analytics",
                "📄  Reports",
            ])

            with tab_overview:
                _render_overview()

            with tab_candidates:
                render_candidates()

            with tab_analytics:
                render_analytics()

            with tab_reports:
                render_reports()

            render_footer()

    except Exception as exc:
        LOGGER.exception("Failed to render dashboard")
        st.error(f"Unable to render dashboard: {exc}")


def _render_overview() -> None:
    """Render the overview tab content (charts + KPIs)."""
    from components.charts import (
        applications_trend,
        pipeline_funnel,
        skills_bar,
        status_donut,
    )
    from components.metric_cards import MetricCardData, render_metric_cards
    from utils.data_service import CandidateService
    from utils.formatters import format_number, format_percent

    svc = CandidateService()
    kpi = svc.get_kpi_summary()
    cfg = {"displayModeBar": False, "responsive": True}

    render_metric_cards([
        MetricCardData("Total Candidates",  format_number(kpi["total_candidates"]),
                       f"{kpi['active_roles']} active roles", "up"),
        MetricCardData("Avg ATS Score",     str(kpi["avg_ats_score"]),
                       "Across all pipeline stages", "neutral"),
        MetricCardData("Hired This Month",  format_number(kpi["hired_this_month"]),
                       f"Rejection rate: {format_percent(kpi['rejection_rate'])}", "up"),
        MetricCardData("Pending Screening", format_number(kpi["pending_review"]),
                       "Awaiting first review", "neutral"),
    ])

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(_panel_header("Hiring Funnel", "Candidate throughput per stage"), unsafe_allow_html=True)
        st.plotly_chart(pipeline_funnel(svc.get_pipeline_stages()),
                        use_container_width=True, config=cfg)
        st.markdown("</section>", unsafe_allow_html=True)
    with c2:
        st.markdown(_panel_header("Status Distribution", "Current pipeline stage breakdown"), unsafe_allow_html=True)
        st.plotly_chart(status_donut(svc.get_status_distribution()),
                        use_container_width=True, config=cfg)
        st.markdown("</section>", unsafe_allow_html=True)

    c3, c4 = st.columns(2, gap="medium")
    with c3:
        st.markdown(_panel_header("Top Skills", "Most-common skills in the pipeline"), unsafe_allow_html=True)
        st.plotly_chart(skills_bar(svc.get_skills_frequency(12).sort_values("count")),
                        use_container_width=True, config=cfg)
        st.markdown("</section>", unsafe_allow_html=True)
    with c4:
        st.markdown(_panel_header("Application Volume", "Weekly intake trend"), unsafe_allow_html=True)
        st.plotly_chart(applications_trend(svc.get_applications_over_time()),
                        use_container_width=True, config=cfg)
        st.markdown("</section>", unsafe_allow_html=True)

    # Activity feed
    items_html = "".join(f"<li>{item}</li>" for item in [
        "Nina Patel moved 8 candidates into shortlist.",
        "Batch upload complete for Senior Python Engineer role.",
        "Ops exported Q3 candidate pipeline report.",
        "ATS scoring complete for 27 new ML Engineer applications.",
        "Final Round interviews scheduled for 5 Frontend Engineer candidates.",
    ])
    st.markdown(
        f'<section class="panel-card fade-in-up">'
        f'<div class="panel-card-header"><h3>Recent Activity</h3>'
        f'<p>Team operations over the last 24 hours</p></div>'
        f'<ul class="activity-feed">{items_html}</ul></section>',
        unsafe_allow_html=True,
    )


def _panel_header(title: str, subtitle: str) -> str:
    return (
        f'<section class="panel-card fade-in-up">'
        f'<div class="panel-card-header"><h3>{title}</h3><p>{subtitle}</p></div>'
    )


if __name__ == "__main__":
    main()

