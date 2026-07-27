"""
Empty-state and loading-state components.

Used when a table or chart has no data to display, giving users a
clear signal rather than a blank space.
"""

from __future__ import annotations

import streamlit as st


def render_empty_state(
    icon:    str = "🔍",
    title:   str = "No results found",
    message: str = "Try adjusting your search or filters.",
) -> None:
    """
    Render a centred empty-state card.

    Args:
        icon:    Emoji or unicode character to display prominently.
        title:   Short headline.
        message: Secondary explanatory text.
    """
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="empty-state">
                <div class="empty-state-icon">{icon}</div>
                <p class="empty-state-title">{title}</p>
                <p class="empty-state-body">{message}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_loading_state(message: str = "Loading data…") -> None:
    """Render a subtle loading placeholder row."""
    st.markdown(
        f"""
        <div class="panel-card" style="text-align:center;padding:2rem;">
            <p style="color:var(--text-muted);font-size:0.85rem;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
