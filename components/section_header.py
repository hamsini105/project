"""Section header component."""

import streamlit as st


def render_section_header(title: str, description: str) -> None:
    """Render a semantic section header used across dashboard blocks."""
    st.markdown(
        f"""
        <header class="section-header fade-in-up">
            <h2>{title}</h2>
            <p>{description}</p>
        </header>
        """,
        unsafe_allow_html=True,
    )
