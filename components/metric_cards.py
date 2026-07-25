"""Reusable metric cards for dashboard KPIs."""

from dataclasses import dataclass
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class MetricCardData:
    """DTO for consistent metric card rendering."""

    title: str
    value: str
    delta: str
    trend: str = "neutral"


def render_metric_cards(cards: Sequence[MetricCardData]) -> None:
    """Render responsive KPI cards from structured card data."""
    if not cards:
        return

    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        trend_class = f"trend-{card.trend.lower()}"
        with column:
            st.markdown(
                f"""
                <section class="metric-card fade-in-up">
                    <p class="metric-title">{card.title}</p>
                    <p class="metric-value">{card.value}</p>
                    <p class="metric-delta {trend_class}">{card.delta}</p>
                </section>
                """,
                unsafe_allow_html=True,
            )
