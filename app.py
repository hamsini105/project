"""Frontend entrypoint for the Resume Parser System dashboard."""

from pathlib import Path

import streamlit as st

from pages.dashboard import render_dashboard
from utils.logger import get_logger

LOGGER = get_logger(__name__)
CSS_FILES: tuple[str, ...] = ("theme.css", "layout.css", "cards.css", "responsive.css")


def configure_page() -> None:
    """Configure global Streamlit page metadata."""
    st.set_page_config(
        page_title="Resume Parser System",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def load_css(css_dir: Path) -> None:
    """Load external CSS files into the app in a deterministic order."""
    for css_name in CSS_FILES:
        css_path = css_dir / css_name
        if not css_path.exists():
            LOGGER.warning("CSS file not found: %s", css_path)
            continue

        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def main() -> None:
    """Initialize the application shell and render the dashboard."""
    configure_page()
    load_css(Path(__file__).parent / "assets" / "css")

    try:
        render_dashboard()
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Failed to render dashboard")
        st.error(f"Unable to render dashboard: {exc}")


if __name__ == "__main__":
    main()
