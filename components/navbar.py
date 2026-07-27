"""Top navigation component."""

import streamlit as st


def render_navbar() -> None:
    """Render the dashboard top navigation shell with functional buttons."""
    col_brand, col_actions = st.columns([2, 1])
    
    with col_brand:
        st.markdown(
            """
            <div class="brand-group">
                <span class="brand-badge">RP</span>
                <div>
                    <p class="brand-title">Resume Parser System</p>
                    <p class="brand-subtitle">Recruiter intelligence workspace</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col_actions:
        col_invite, col_upload = st.columns(2)
        
        with col_invite:
            if st.button("👥 Invite Team", use_container_width=True):
                st.info("Team invitation feature coming soon!")
        
        with col_upload:
            if st.button("📤 Upload Resumes", use_container_width=True):
                st.session_state.show_upload = True
