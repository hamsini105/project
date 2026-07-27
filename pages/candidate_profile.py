"""
Candidate profile page.

Renders a rich detail view for a single candidate: contact info,
ATS score gauge, skills breakdown, experience timeline, education,
recruiter notes, and status management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import streamlit as st

from components.export import render_pdf_export
from components.status_badge import all_status_values, score_gauge_html, status_badge_html
from utils.data_service import CandidateService
from utils.formatters import format_date, format_experience, initials

logger = logging.getLogger(__name__)
_service = CandidateService()


def render_candidate_profile(candidate_id: str) -> None:
    """
    Render the full profile view for a candidate.

    Args:
        candidate_id: The candidate's ``id`` field from the DataFrame.
    """
    candidate = _service.get_by_id(candidate_id)
    if not candidate:
        st.error(f"Candidate '{candidate_id}' was not found.")
        return

    logger.debug("Rendering profile for candidate %s", candidate_id)

    _render_profile_header(candidate)

    left_col, right_col = st.columns([1, 1.6], gap="large")

    with left_col:
        _render_score_card(candidate)
        _render_contact_card(candidate)
        _render_skills_card(candidate)

    with right_col:
        _render_experience_card(candidate)
        _render_status_card(candidate)
        _render_notes_card(candidate)

    # Export
    import pandas as pd
    candidate_df = pd.DataFrame([candidate])
    render_pdf_export(
        candidate_df,
        filename=f"candidate_{candidate_id}.pdf",
        title=f"Candidate Report – {candidate.get('name', '')}",
        label="⬇ Export Profile PDF",
    )


# ── Header ─────────────────────────────────────────────────────────────────────

def _render_profile_header(candidate: Dict[str, Any]) -> None:
    name    = str(candidate.get("name", "Unknown"))
    role    = str(candidate.get("role", ""))
    status  = str(candidate.get("status", ""))
    location = str(candidate.get("location", ""))

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="profile-header">
                <div class="profile-avatar">{initials(name)}</div>
                <div class="profile-meta">
                    <h2>{name}</h2>
                    <p>{role}{"  ·  " + location if location else ""}</p>
                </div>
                <div style="margin-left:auto;">
                    {status_badge_html(status)}
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


# ── Score card ─────────────────────────────────────────────────────────────────

def _render_score_card(candidate: Dict[str, Any]) -> None:
    score = float(candidate.get("ats_score", 0))
    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>ATS Score</h3>
                <p>Automated Tracking System compatibility score</p>
            </div>
            {score_gauge_html(score)}
        </section>
        """,
        unsafe_allow_html=True,
    )


# ── Contact card ───────────────────────────────────────────────────────────────

def _render_contact_card(candidate: Dict[str, Any]) -> None:
    email    = candidate.get("email", "—")
    phone    = candidate.get("phone", "—")
    linkedin = candidate.get("linkedin", "")
    location = candidate.get("location", "—")
    applied  = candidate.get("applied_date")
    applied_str = format_date(applied.date() if hasattr(applied, "date") else applied)

    rows = [
        ("📧 Email",    email),
        ("📱 Phone",    phone),
        ("📍 Location", location),
        ("📅 Applied",  applied_str),
    ]
    if linkedin:
        rows.append(("🔗 LinkedIn", f'<a href="{linkedin}" target="_blank" style="color:var(--brand-500);">Profile</a>'))

    rows_html = "".join(
        f"""
        <div class="profile-detail-row">
            <span class="profile-detail-label">{label}</span>
            <span>{value}</span>
        </div>
        """
        for label, value in rows
    )

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Contact</h3>
            </div>
            {rows_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


# ── Skills card ────────────────────────────────────────────────────────────────

def _render_skills_card(candidate: Dict[str, Any]) -> None:
    skills: List[str] = candidate.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    badges = "".join(
        f'<span class="skill-badge" style="margin:0.15rem;">{s}</span>'
        for s in skills
    ) if skills else '<span style="color:var(--text-muted);font-size:0.8rem;">No skills listed</span>'

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Skills</h3>
                <p>{len(skills)} listed</p>
            </div>
            <div class="skill-badge-row" style="padding-top:0.5rem;">{badges}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


# ── Experience card ────────────────────────────────────────────────────────────

def _render_experience_card(candidate: Dict[str, Any]) -> None:
    years   = float(candidate.get("experience_years", 0))
    role    = str(candidate.get("role", ""))
    edu     = str(candidate.get("education", ""))

    st.markdown(
        f"""
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Background</h3>
                <p>Experience and qualifications summary</p>
            </div>
            <div class="profile-detail-row">
                <span class="profile-detail-label">🏢 Total Experience</span>
                <span>{format_experience(years)}</span>
            </div>
            <div class="profile-detail-row">
                <span class="profile-detail-label">💼 Applied Role</span>
                <span>{role}</span>
            </div>
            <div class="profile-detail-row">
                <span class="profile-detail-label">🎓 Education</span>
                <span>{edu + "'s Degree" if edu else "—"}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


# ── Status management ─────────────────────────────────────────────────────────

def _render_status_card(candidate: Dict[str, Any]) -> None:
    cid     = str(candidate.get("id", ""))
    current = str(candidate.get("status", ""))

    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Pipeline Status</h3>
                <p>Update candidate stage</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    all_statuses = all_status_values()
    current_index = all_statuses.index(current) if current in all_statuses else 0

    new_status = st.selectbox(
        "Pipeline Status",
        options=all_statuses,
        index=current_index,
        key=f"status_select_{cid}",
        label_visibility="collapsed",
    )

    if st.button("Update Status", key=f"update_status_{cid}", use_container_width=True):
        _service.update_status(cid, new_status)
        st.success(f"Status updated to **{new_status}**.")
        st.rerun()

    st.markdown("</section>", unsafe_allow_html=True)


# ── Recruiter notes ───────────────────────────────────────────────────────────

def _render_notes_card(candidate: Dict[str, Any]) -> None:
    cid   = str(candidate.get("id", ""))
    notes = str(candidate.get("notes", ""))

    st.markdown(
        """
        <section class="panel-card fade-in-up">
            <div class="panel-card-header">
                <h3>Recruiter Notes</h3>
                <p>Internal notes — not visible to the candidate</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    updated_notes = st.text_area(
        "Notes",
        value=notes,
        height=100,
        key=f"notes_{cid}",
        label_visibility="collapsed",
        placeholder="Add internal notes, interview feedback, or follow-up reminders…",
    )

    if st.button("Save Notes", key=f"save_notes_{cid}", use_container_width=True):
        _service.update_notes(cid, updated_notes)
        st.success("Notes saved.")

    st.markdown("</section>", unsafe_allow_html=True)
