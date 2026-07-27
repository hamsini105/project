"""
Status badge rendering utilities.

Each public function returns an HTML string — callers are responsible for
passing it to ``st.markdown(..., unsafe_allow_html=True)``.
"""

from __future__ import annotations

# Map canonical status values to their CSS modifier classes
_STATUS_CSS_MAP: dict[str, str] = {
    "Screening":       "status-screening",
    "Phone Screen":    "status-phone-screen",
    "Technical Round": "status-technical",
    "Final Round":     "status-final-round",
    "Hired":           "status-hired",
    "Rejected":        "status-rejected",
}


def status_badge_html(status: str) -> str:
    """
    Return an HTML badge for the given pipeline status.

    Falls back to the generic 'status-screening' style for unknown values.
    """
    css_class = _STATUS_CSS_MAP.get(status, "status-screening")
    return f'<span class="status-badge {css_class}">{status}</span>'


def score_pill_html(score: float) -> str:
    """Return an HTML pill coloured by ATS score band."""
    if score >= 80:
        css_class = "score-excellent"
        label = "Excellent"
    elif score >= 65:
        css_class = "score-good"
        label = "Good"
    elif score >= 50:
        css_class = "score-fair"
        label = "Fair"
    else:
        css_class = "score-poor"
        label = "Poor"

    return (
        f'<span class="score-pill {css_class}">'
        f'{score:.1f} <span style="font-weight:400;opacity:0.8">· {label}</span>'
        f'</span>'
    )


def score_gauge_html(score: float, label: str = "ATS Score") -> str:
    """Return a centred score gauge block for use in profile cards."""
    if score >= 80:
        color = "#16a34a"
    elif score >= 65:
        color = "#2563eb"
    elif score >= 50:
        color = "#d97706"
    else:
        color = "#dc2626"

    return f"""
    <div class="score-gauge-container">
        <div class="score-gauge-value" style="color:{color}">{score:.1f}</div>
        <div class="score-gauge-label" style="color:{color}">{label}</div>
    </div>
    """


def all_status_values() -> list[str]:
    """Return all known pipeline status values in funnel order."""
    return list(_STATUS_CSS_MAP.keys())
