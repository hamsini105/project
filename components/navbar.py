"""Top navigation component."""

import streamlit as st


def render_navbar() -> None:
    """Render the dashboard top navigation shell."""
    st.markdown(
        """
        <nav class="top-nav fade-in-up">
            <div class="brand-group">
                <span class="brand-badge">RP</span>
                <div>
                    <p class="brand-title">Resume Parser System</p>
                    <p class="brand-subtitle">Recruiter intelligence workspace</p>
                </div>
            </div>
            <div class="nav-actions">
                <button class="nav-button">Invite Team</button>
                <button class="nav-button nav-button-primary">Upload Resumes</button>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
