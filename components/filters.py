"""
Filter panel component for the Candidates page.

Renders a structured set of Streamlit controls and returns a typed
FilterState dataclass so the calling page can apply filters without
coupling to widget key names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import streamlit as st

from components.status_badge import all_status_values
from utils.data_service import CandidateService

_service = CandidateService()

# Session-state key prefix for all filter widgets
_KEY_PREFIX = "filter_"


@dataclass
class FilterState:
    """Immutable snapshot of the current filter panel state."""

    query:     str       = ""
    statuses:  List[str] = field(default_factory=list)
    roles:     List[str] = field(default_factory=list)
    min_score: float     = 0.0
    max_score: float     = 100.0
    min_exp:   float     = 0.0
    max_exp:   float     = 20.0
    education: List[str] = field(default_factory=list)


def render_filter_panel() -> FilterState:
    """
    Render the filter sidebar panel and return the current FilterState.

    All widget keys are namespaced with ``_KEY_PREFIX`` to avoid collisions
    with other pages that also use st.session_state.

    Returns:
        FilterState reflecting current widget values.
    """
    st.markdown(
        '<div class="filter-panel-title">🔎 Search & Filters</div>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search candidates",
        key=f"{_KEY_PREFIX}query",
        placeholder="Name, email, role or location…",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
        'margin:0.75rem 0 0.3rem;">PIPELINE STATUS</p>',
        unsafe_allow_html=True,
    )
    statuses: List[str] = st.multiselect(
        "Status",
        options=all_status_values(),
        key=f"{_KEY_PREFIX}statuses",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
        'margin:0.75rem 0 0.3rem;">ROLE</p>',
        unsafe_allow_html=True,
    )
    all_roles = sorted(_service.get_all()["role"].unique().tolist())
    roles: List[str] = st.multiselect(
        "Role",
        options=all_roles,
        key=f"{_KEY_PREFIX}roles",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
        'margin:0.75rem 0 0.3rem;">ATS SCORE</p>',
        unsafe_allow_html=True,
    )
    score_range = st.slider(
        "ATS Score Range",
        min_value=0,
        max_value=100,
        value=(0, 100),
        key=f"{_KEY_PREFIX}score_range",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
        'margin:0.75rem 0 0.3rem;">EXPERIENCE (YEARS)</p>',
        unsafe_allow_html=True,
    )
    exp_range = st.slider(
        "Experience",
        min_value=0.0,
        max_value=20.0,
        value=(0.0, 20.0),
        step=0.5,
        key=f"{_KEY_PREFIX}exp_range",
        label_visibility="collapsed",
    )

    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.78rem;font-weight:600;'
        'margin:0.75rem 0 0.3rem;">EDUCATION</p>',
        unsafe_allow_html=True,
    )
    education: List[str] = st.multiselect(
        "Education",
        options=["Bachelor", "Master", "PhD"],
        key=f"{_KEY_PREFIX}education",
        label_visibility="collapsed",
    )

    if st.button("Clear all filters", use_container_width=True):
        _reset_filters()
        st.rerun()

    return FilterState(
        query=query,
        statuses=statuses,
        roles=roles,
        min_score=float(score_range[0]),
        max_score=float(score_range[1]),
        min_exp=float(exp_range[0]),
        max_exp=float(exp_range[1]),
        education=education,
    )


def _reset_filters() -> None:
    """Clear all filter keys from session state."""
    for key in list(st.session_state.keys()):
        if key.startswith(_KEY_PREFIX):
            del st.session_state[key]
