"""
Candidates management page.

Provides a searchable, filterable candidate table with row-level
profile navigation.  Delegates data retrieval to CandidateService
and rendering to reusable components.
"""

from __future__ import annotations

import logging

import streamlit as st

from components.candidate_table import render_candidate_table
from components.export import render_export_row
from components.filters import render_filter_panel
from utils.data_service import CandidateService
from utils.formatters import format_number

logger = logging.getLogger(__name__)
_service = CandidateService()

_PROFILE_KEY = "view_candidate_id"
_PAGE_KEY    = "candidates_page"


def render_candidates() -> None:
    """
    Render the Candidates tab content.

    Internally routes between the list view and the profile view using
    ``st.session_state[_PROFILE_KEY]``.
    """
    candidate_id: str | None = st.session_state.get(_PROFILE_KEY)

    if candidate_id:
        _render_profile_shell(candidate_id)
    else:
        _render_list_view()


# ── List view ─────────────────────────────────────────────────────────────────

def _render_list_view() -> None:
    filter_col, table_col = st.columns([1, 3.2], gap="large")

    with filter_col:
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        filters = render_filter_panel()
        st.markdown("</div>", unsafe_allow_html=True)

    with table_col:
        df = _service.get_all()
        df = _service.search(filters.query, df)
        df = _service.apply_filters(
            df,
            statuses=filters.statuses or None,
            roles=filters.roles or None,
            min_score=filters.min_score,
            max_score=filters.max_score,
            min_exp=filters.min_exp,
            max_exp=filters.max_exp,
            education=filters.education or None,
        )

        # Table header
        st.markdown(
            f"""
            <div class="candidate-table-header">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <p style="color:var(--text-primary);font-size:0.95rem;
                              font-weight:700;margin:0;">Candidates</p>
                    <span class="candidate-count-badge">{format_number(len(df))}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Export row
        render_export_row(
            df,
            csv_filename="candidates_export.csv",
            pdf_filename="candidate_report.pdf",
            report_title="Candidate Pipeline Report",
        )

        st.markdown('<div style="margin-top:0.6rem;">', unsafe_allow_html=True)
        selected_id = render_candidate_table(df)
        st.markdown("</div>", unsafe_allow_html=True)

        if selected_id:
            st.session_state[_PROFILE_KEY] = selected_id
            st.session_state[_PAGE_KEY] = 0  # reset pagination on navigate
            st.rerun()


# ── Profile shell ─────────────────────────────────────────────────────────────

def _render_profile_shell(candidate_id: str) -> None:
    """
    Delegate to the candidate profile page while providing a back-nav button.
    """
    # Back button above the profile
    if st.button("← Back to Candidates", key="back_to_list"):
        del st.session_state[_PROFILE_KEY]
        st.rerun()

    # Import here to avoid circular loading order issues
    from pages.candidate_profile import render_candidate_profile
    render_candidate_profile(candidate_id)
