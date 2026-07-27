"""
Candidate table component.

Renders a searchable, paginated, interactive candidate table backed by
a filtered DataFrame.  All interactive elements (search, page nav) use
session_state keys namespaced to avoid conflicts.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import streamlit as st

from components.status_badge import status_badge_html
from utils.formatters import format_date, format_experience, initials

logger = logging.getLogger(__name__)

_PAGE_SIZE = 20
_PAGE_KEY  = "candidates_page"


def render_candidate_table(
    df: pd.DataFrame,
    *,
    show_export_hint: bool = True,
) -> Optional[str]:
    """
    Render a paginated candidate table.

    Args:
        df:               Filtered DataFrame to display.
        show_export_hint: Whether to show the row-count / export hint below.

    Returns:
        The candidate ID if the user clicked "View" on a row, else None.
    """
    if df.empty:
        from components.empty_state import render_empty_state
        render_empty_state(
            icon="👥",
            title="No candidates match your filters",
            message="Try broadening your search or clearing the active filters.",
        )
        return None

    # ── Pagination ────────────────────────────────────────────────────────────
    total_rows = len(df)
    current_page = st.session_state.get(_PAGE_KEY, 0)
    max_page = max(0, (total_rows - 1) // _PAGE_SIZE)
    current_page = min(current_page, max_page)
    st.session_state[_PAGE_KEY] = current_page

    start = current_page * _PAGE_SIZE
    end   = start + _PAGE_SIZE
    page_df = df.iloc[start:end]

    # ── Table header row ──────────────────────────────────────────────────────
    header_cols = st.columns([0.4, 2.2, 2.0, 1.6, 1.1, 1.1, 1.1, 0.8])
    headers = ["", "Candidate", "Role", "Status", "ATS Score", "Experience", "Applied", ""]
    for col, hdr in zip(header_cols, headers):
        with col:
            st.markdown(
                f'<p style="color:var(--text-muted);font-size:0.75rem;'
                f'font-weight:600;margin:0;padding:0.3rem 0;">{hdr}</p>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr style="margin:0 0 0.3rem;border:none;border-top:1px solid var(--border-soft);">', unsafe_allow_html=True)

    # ── Table rows ────────────────────────────────────────────────────────────
    selected_id: Optional[str] = None

    for _, row in page_df.iterrows():
        cols = st.columns([0.4, 2.2, 2.0, 1.6, 1.1, 1.1, 1.1, 0.8])
        cid = str(row.get("id", ""))

        # Avatar
        with cols[0]:
            st.markdown(
                f'<div style="width:32px;height:32px;border-radius:50%;'
                f'background:linear-gradient(135deg,#2563eb,#7c3aed);'
                f'display:flex;align-items:center;justify-content:center;'
                f'color:#fff;font-size:0.68rem;font-weight:700;margin-top:0.15rem;">'
                f'{initials(str(row.get("name", "?")))}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Name + email
        with cols[1]:
            name  = str(row.get("name", ""))
            email = str(row.get("email", ""))
            st.markdown(
                f'<div style="padding-top:0.05rem;">'
                f'<p style="color:var(--text-primary);font-size:0.83rem;'
                f'font-weight:600;margin:0;">{name}</p>'
                f'<p style="color:var(--text-muted);font-size:0.72rem;margin:0;">{email}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Role
        with cols[2]:
            st.markdown(
                f'<p style="color:var(--text-secondary);font-size:0.8rem;'
                f'margin:0;padding-top:0.4rem;">{row.get("role", "")}</p>',
                unsafe_allow_html=True,
            )

        # Status badge
        with cols[3]:
            st.markdown(
                f'<div style="padding-top:0.3rem;">{status_badge_html(str(row.get("status", "")))}</div>',
                unsafe_allow_html=True,
            )

        # ATS score
        with cols[4]:
            score = float(row.get("ats_score", 0))
            color = "#16a34a" if score >= 80 else "#2563eb" if score >= 65 else "#d97706" if score >= 50 else "#dc2626"
            st.markdown(
                f'<p style="color:{color};font-size:0.85rem;font-weight:700;'
                f'margin:0;padding-top:0.35rem;">{score:.1f}</p>',
                unsafe_allow_html=True,
            )

        # Experience
        with cols[5]:
            exp = float(row.get("experience_years", 0))
            st.markdown(
                f'<p style="color:var(--text-secondary);font-size:0.8rem;'
                f'margin:0;padding-top:0.35rem;">{format_experience(exp)}</p>',
                unsafe_allow_html=True,
            )

        # Applied date
        with cols[6]:
            applied = row.get("applied_date")
            date_str = format_date(applied.date() if hasattr(applied, "date") else applied)
            st.markdown(
                f'<p style="color:var(--text-muted);font-size:0.78rem;'
                f'margin:0;padding-top:0.38rem;">{date_str}</p>',
                unsafe_allow_html=True,
            )

        # View button
        with cols[7]:
            if st.button("View", key=f"view_{cid}", use_container_width=True):
                selected_id = cid

        st.markdown(
            '<hr style="margin:0;border:none;border-top:1px solid var(--border-soft);">',
            unsafe_allow_html=True,
        )

    # ── Pagination controls ───────────────────────────────────────────────────
    if total_rows > _PAGE_SIZE:
        pag_left, pag_mid, pag_right = st.columns([1, 2, 1])
        with pag_left:
            if current_page > 0:
                if st.button("← Previous", use_container_width=True):
                    st.session_state[_PAGE_KEY] = current_page - 1
                    st.rerun()
        with pag_mid:
            page_start = start + 1
            page_end   = min(end, total_rows)
            st.markdown(
                f'<p class="page-info" style="text-align:center;margin-top:0.4rem;">'
                f'Showing {page_start}–{page_end} of {total_rows:,} candidates</p>',
                unsafe_allow_html=True,
            )
        with pag_right:
            if current_page < max_page:
                if st.button("Next →", use_container_width=True):
                    st.session_state[_PAGE_KEY] = current_page + 1
                    st.rerun()
    elif show_export_hint:
        st.markdown(
            f'<p style="color:var(--text-muted);font-size:0.76rem;margin-top:0.4rem;">'
            f'{total_rows:,} candidate{"s" if total_rows != 1 else ""} displayed</p>',
            unsafe_allow_html=True,
        )

    return selected_id
