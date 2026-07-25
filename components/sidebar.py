"""Left sidebar navigation component."""

import streamlit as st


def render_sidebar() -> None:
    """Render static navigation and team context in the sidebar."""
    st.markdown(
        """
        <aside class="sidebar-panel fade-in-up">
            <div class="sidebar-section">
                <p class="sidebar-label">Workspace</p>
                <h2 class="sidebar-title">Hiring Operations</h2>
                <p class="sidebar-caption">Q3 Candidate Pipeline</p>
            </div>
            <div class="sidebar-section">
                <p class="sidebar-label">Navigation</p>
                <ul class="sidebar-list">
                    <li class="sidebar-item sidebar-item-active">Dashboard</li>
                    <li class="sidebar-item">Candidate Queue</li>
                    <li class="sidebar-item">Job Postings</li>
                    <li class="sidebar-item">Integrations</li>
                    <li class="sidebar-item">Reports</li>
                </ul>
            </div>
            <div class="sidebar-section sidebar-note">
                <p class="sidebar-label">Environment</p>
                <p class="sidebar-caption">Frontend foundation only. Parsing and ATS logic are intentionally excluded.</p>
            </div>
        </aside>
        """,
        unsafe_allow_html=True,
    )
