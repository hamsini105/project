"""Left sidebar navigation and workspace context component."""

from __future__ import annotations

import streamlit as st


_NAV_ITEMS = [
    ("📊", "Overview"),
    ("👥", "Candidates"),
    ("📈", "Analytics"),
    ("📄", "Reports"),
]


def render_sidebar() -> None:
    """
    Render the workspace context panel and tab-sync navigation hints.

    Navigation is driven by ``st.tabs()`` in app.py — the sidebar shows
    context info and a visual role label rather than functional links.
    """
    st.markdown(
        """
        <aside class="sidebar-panel fade-in-up">
            <div class="sidebar-section">
                <p class="sidebar-label">Workspace</p>
                <h2 class="sidebar-title">Hiring Operations</h2>
                <p class="sidebar-caption">Q3 Candidate Pipeline</p>
            </div>
            <div class="sidebar-section">
                <p class="sidebar-label">Navigation</p>
                <p class="sidebar-caption" style="font-size:0.76rem;">
                    Use the tabs above to switch between views.
                </p>
            </div>
        </aside>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📋 Quick Stats", expanded=True):
        try:
            from utils.data_service import CandidateService
            kpi = CandidateService().get_kpi_summary()
            st.markdown(
                f"""
                <div style="display:grid;gap:0.45rem;">
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;">
                        <span style="color:var(--text-muted);">Total Candidates</span>
                        <span style="font-weight:700;color:var(--text-primary);">{kpi['total_candidates']:,}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;">
                        <span style="color:var(--text-muted);">Avg ATS Score</span>
                        <span style="font-weight:700;color:var(--brand-500);">{kpi['avg_ats_score']}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;">
                        <span style="color:var(--text-muted);">Hired This Month</span>
                        <span style="font-weight:700;color:#16a34a;">{kpi['hired_this_month']}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;">
                        <span style="color:var(--text-muted);">Active Roles</span>
                        <span style="font-weight:700;color:var(--text-primary);">{kpi['active_roles']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            st.caption("Stats unavailable")

