"""
Formatting utilities for the Recruiter Dashboard.

Pure functions with no side effects — safe to use anywhere.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List

# ── Score formatting ──────────────────────────────────────────────────────────

def format_score(score: float) -> str:
    """Return a formatted score string, e.g. '82.4'."""
    return f"{score:.1f}"


def score_color(score: float) -> str:
    """Return a CSS hex color appropriate for the ATS score band."""
    if score >= 80:
        return "#16a34a"   # green — strong match
    if score >= 65:
        return "#2563eb"   # blue — good match
    if score >= 50:
        return "#d97706"   # amber — fair
    return "#dc2626"       # red — poor


def score_label(score: float) -> str:
    """Return a human-readable band label for an ATS score."""
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Poor"


# ── Date formatting ───────────────────────────────────────────────────────────

def relative_date(dt: date | datetime | None) -> str:
    """
    Return a relative date string, e.g. 'Today', '3 days ago', '2 months ago'.
    """
    if dt is None:
        return "—"

    if isinstance(dt, datetime):
        target = dt.date()
    else:
        target = dt

    today = date.today()
    delta = (today - target).days

    if delta == 0:
        return "Today"
    if delta == 1:
        return "Yesterday"
    if delta < 7:
        return f"{delta} days ago"
    if delta < 30:
        weeks = delta // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    if delta < 365:
        months = delta // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    years = delta // 365
    return f"{years} year{'s' if years > 1 else ''} ago"


def format_date(dt: date | datetime | None) -> str:
    """Return a formatted date string like 'Jan 15, 2025'."""
    if dt is None:
        return "—"
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt.strftime("%b %d, %Y")


# ── String formatting ─────────────────────────────────────────────────────────

def truncate(text: str, max_len: int = 35) -> str:
    """Truncate a string to max_len characters with an ellipsis."""
    if not text:
        return ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def format_experience(years: float) -> str:
    """Return a human-friendly experience string, e.g. '5.5 years'."""
    if years < 1:
        months = round(years * 12)
        return f"{months} month{'s' if months != 1 else ''}"
    return f"{years:.1f} yr{'s' if years != 1 else ''}"


def initials(name: str) -> str:
    """Return up to two initials from a full name."""
    parts = name.strip().split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


# ── Skills formatting ─────────────────────────────────────────────────────────

def skills_as_html_badges(skills: List[str], max_shown: int = 6) -> str:
    """
    Return an HTML string of skill badge pills.

    Args:
        skills:    List of skill names.
        max_shown: Maximum number of badges to render before showing a count.
    """
    if not skills:
        return '<span style="color:#94a3b8;font-size:0.78rem;">—</span>'

    shown = skills[:max_shown]
    remainder = len(skills) - len(shown)

    badges = "".join(
        f'<span class="skill-badge">{s}</span>' for s in shown
    )
    if remainder > 0:
        badges += f'<span class="skill-badge skill-badge-muted">+{remainder}</span>'
    return f'<div class="skill-badge-row">{badges}</div>'


# ── Number formatting ─────────────────────────────────────────────────────────

def format_number(n: int | float) -> str:
    """Return comma-formatted number string, e.g. 1,284."""
    return f"{int(n):,}"


def format_percent(value: float, decimals: int = 1) -> str:
    """Return a percentage string, e.g. '82.4%'."""
    return f"{value:.{decimals}f}%"
