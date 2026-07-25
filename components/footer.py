"""Footer component for app shell."""

import streamlit as st


def render_footer() -> None:
    """Render a minimal footer aligned with SaaS dashboard aesthetics."""
    st.markdown(
        """
        <footer class="app-footer fade-in-up">
            <p>Resume Parser System Frontend Foundation</p>
            <p>Built for recruiter workflows with modular, production-ready UI architecture.</p>
        </footer>
        """,
        unsafe_allow_html=True,
    )
