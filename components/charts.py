"""
Reusable Plotly chart components for the Recruiter Dashboard.

Each function accepts a DataFrame or dict and returns a configured
``plotly.graph_objects.Figure``.  Callers render with ``st.plotly_chart()``.

Design notes:
- Brand palette and font are applied consistently across all charts.
- Margins and padding are sized for embedding inside panel-card containers.
- No chart hard-codes data — all inputs are parameters.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Brand palette ─────────────────────────────────────────────────────────────
_BRAND   = "#2563eb"
_SUCCESS = "#16a34a"
_AMBER   = "#d97706"
_DANGER  = "#dc2626"
_PURPLE  = "#7c3aed"
_CYAN    = "#0891b2"
_SLATE   = "#64748b"

_PALETTE = [_BRAND, _PURPLE, _SUCCESS, _AMBER, _CYAN, _DANGER, _SLATE,
            "#0f172a", "#84cc16", "#f97316"]

_FONT    = "Inter, -apple-system, sans-serif"
_BG      = "rgba(0,0,0,0)"  # transparent for panel embedding

_BASE_LAYOUT = dict(
    font_family=_FONT,
    font_color="#475569",
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    margin=dict(l=0, r=0, t=8, b=0),
    hoverlabel=dict(
        bgcolor="#ffffff",
        bordercolor="#e2e8f0",
        font_size=12,
        font_family=_FONT,
    ),
    showlegend=False,
)


# ── Pipeline funnel ───────────────────────────────────────────────────────────

def pipeline_funnel(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal funnel chart showing candidate counts per pipeline stage.

    Args:
        df: DataFrame with columns ``stage`` and ``count``.
    """
    fig = go.Figure(go.Funnel(
        y=df["stage"].tolist(),
        x=df["count"].tolist(),
        textinfo="value+percent initial",
        textfont_size=12,
        connector_line_color="#e2e8f0",
        marker=dict(
            color=[_BRAND, _PURPLE, _AMBER, _SUCCESS, _CYAN][: len(df)],
            line=dict(color=["#ffffff"] * len(df), width=1),
        ),
        opacity=0.88,
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=260,
        margin=dict(l=0, r=0, t=4, b=0),
    )
    return fig


# ── Status donut ──────────────────────────────────────────────────────────────

def status_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart of candidate pipeline-status distribution.

    Args:
        df: DataFrame with columns ``status`` and ``count``.
    """
    _STATUS_COLORS = {
        "Screening":       _SLATE,
        "Phone Screen":    _CYAN,
        "Technical Round": _PURPLE,
        "Final Round":     _AMBER,
        "Hired":           _SUCCESS,
        "Rejected":        _DANGER,
    }
    colors = [_STATUS_COLORS.get(s, _BRAND) for s in df["status"].tolist()]

    fig = go.Figure(go.Pie(
        labels=df["status"].tolist(),
        values=df["count"].tolist(),
        hole=0.62,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textinfo="none",
        hovertemplate="%{label}: <b>%{value}</b> (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.0,
            y=0.5,
            font_size=11,
            itemclick=False,
        ),
        height=220,
        margin=dict(l=0, r=80, t=4, b=0),
    )
    return fig


# ── Skills bar chart ──────────────────────────────────────────────────────────

def skills_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of the most-frequent skills in the pipeline.

    Args:
        df: DataFrame with columns ``skill`` and ``count``, sorted desc.
    """
    fig = go.Figure(go.Bar(
        x=df["count"].tolist(),
        y=df["skill"].tolist(),
        orientation="h",
        marker_color=_BRAND,
        marker_opacity=0.80,
        text=df["count"].tolist(),
        textposition="outside",
        textfont_size=11,
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=max(220, len(df) * 26),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, automargin=True, tickfont_size=11),
        bargap=0.35,
    )
    return fig


# ── ATS score distribution ────────────────────────────────────────────────────

def score_histogram(df: pd.DataFrame, score_col: str = "ats_score") -> go.Figure:
    """
    Histogram of ATS score distribution with band colour zones.

    Args:
        df:        Candidate DataFrame.
        score_col: Column to plot (default 'ats_score').
    """
    fig = go.Figure()

    # Coloured background bands
    for x0, x1, color, label in [
        (0,  50, "rgba(220,38,38,0.05)",   "Poor"),
        (50, 65, "rgba(234,179,8,0.07)",   "Fair"),
        (65, 80, "rgba(37,99,235,0.06)",   "Good"),
        (80, 100,"rgba(22,163,74,0.07)",   "Excellent"),
    ]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, line_width=0,
                      annotation_text=label, annotation_position="top left",
                      annotation_font_size=9, annotation_font_color="#94a3b8")

    fig.add_trace(go.Histogram(
        x=df[score_col].tolist(),
        nbinsx=20,
        marker_color=_BRAND,
        marker_opacity=0.75,
        hovertemplate="Score %{x}: <b>%{y}</b> candidates<extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=240,
        xaxis=dict(title="ATS Score", range=[0, 100], showgrid=False,
                   tickfont_size=11, title_font_size=12),
        yaxis=dict(title="Candidates", showgrid=True, gridcolor="#f1f5f9",
                   tickfont_size=11, title_font_size=12),
        bargap=0.05,
    )
    return fig


# ── Score by role ─────────────────────────────────────────────────────────────

def score_by_role(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart comparing average ATS scores across roles.

    Args:
        df: DataFrame with columns ``role`` and ``avg_score``.
    """
    sorted_df = df.sort_values("avg_score")
    fig = go.Figure(go.Bar(
        x=sorted_df["avg_score"].round(1).tolist(),
        y=sorted_df["role"].tolist(),
        orientation="h",
        marker_color=[
            _SUCCESS if s >= 70 else _AMBER if s >= 55 else _DANGER
            for s in sorted_df["avg_score"]
        ],
        marker_opacity=0.82,
        text=sorted_df["avg_score"].round(1).tolist(),
        textposition="outside",
        textfont_size=11,
        hovertemplate="%{y}: <b>%{x:.1f}</b><extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=260,
        xaxis=dict(title="Avg ATS Score", range=[0, 105], showgrid=False,
                   tickfont_size=11, title_font_size=12),
        yaxis=dict(showgrid=False, automargin=True, tickfont_size=11),
        bargap=0.30,
    )
    return fig


# ── Applications over time ────────────────────────────────────────────────────

def applications_trend(df: pd.DataFrame) -> go.Figure:
    """
    Filled area chart of weekly application volume.

    Args:
        df: DataFrame with columns ``week`` and ``applications``.
    """
    fig = go.Figure(go.Scatter(
        x=df["week"].tolist(),
        y=df["applications"].tolist(),
        mode="lines",
        line=dict(color=_BRAND, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.08)",
        hovertemplate="Week of %{x}: <b>%{y}</b><extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=220,
        xaxis=dict(showgrid=False, tickfont_size=10),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont_size=10),
    )
    return fig


# ── Education distribution ────────────────────────────────────────────────────

def education_pie(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart of candidate education level distribution.

    Args:
        df: DataFrame with columns ``education`` and ``count``.
    """
    _EDU_COLORS = {
        "Bachelor": _BRAND,
        "Master":   _PURPLE,
        "PhD":      _SUCCESS,
    }
    colors = [_EDU_COLORS.get(e, _SLATE) for e in df["education"].tolist()]

    fig = go.Figure(go.Pie(
        labels=df["education"].tolist(),
        values=df["count"].tolist(),
        hole=0.45,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textinfo="percent+label",
        textfont_size=11,
        hovertemplate="%{label}: <b>%{value}</b><extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        showlegend=False,
        height=220,
    )
    return fig


# ── Experience distribution ───────────────────────────────────────────────────

def experience_histogram(df: pd.DataFrame) -> go.Figure:
    """
    Histogram of candidate years of experience.

    Args:
        df: Candidate DataFrame with ``experience_years`` column.
    """
    fig = go.Figure(go.Histogram(
        x=df["experience_years"].tolist(),
        nbinsx=15,
        marker_color=_PURPLE,
        marker_opacity=0.78,
        hovertemplate="%{x:.1f} yrs: <b>%{y}</b> candidates<extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=220,
        xaxis=dict(title="Years of Experience", showgrid=False,
                   tickfont_size=11, title_font_size=12),
        yaxis=dict(title="Candidates", showgrid=True, gridcolor="#f1f5f9",
                   tickfont_size=11, title_font_size=12),
        bargap=0.08,
    )
    return fig
