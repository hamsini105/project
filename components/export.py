"""
Export button components for the Recruiter Dashboard.

Wraps st.download_button with consistent styling and error handling
for both CSV and PDF export scenarios.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import streamlit as st

from utils.report_generator import to_csv, to_pdf

logger = logging.getLogger(__name__)


def render_csv_export(
    df: pd.DataFrame,
    filename: str = "candidates.csv",
    label:    str = "⬇ Export CSV",
) -> None:
    """
    Render a CSV download button for the given DataFrame.

    Args:
        df:       DataFrame to export.
        filename: Downloaded filename.
        label:    Button label text.
    """
    try:
        csv_bytes = to_csv(df)
    except Exception as exc:
        logger.error("CSV generation failed: %s", exc)
        st.error("CSV export is currently unavailable.")
        return

    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def render_pdf_export(
    df:       pd.DataFrame,
    filename: str = "candidate_report.pdf",
    title:    str = "Candidate Report",
    label:    str = "⬇ Export PDF",
) -> None:
    """
    Render a PDF download button for the given DataFrame.

    Gracefully falls back to a disabled button with an error message if
    fpdf2 is not installed.

    Args:
        df:       DataFrame to include in the report.
        filename: Downloaded filename.
        title:    PDF report heading.
        label:    Button label text.
    """
    try:
        pdf_bytes = to_pdf(df, title=title)
    except ImportError:
        st.warning("PDF export requires fpdf2. Run: `pip install fpdf2`")
        return
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        st.error("PDF export is currently unavailable.")
        return

    st.download_button(
        label=label,
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True,
    )


def render_export_row(
    df:          pd.DataFrame,
    csv_filename: str = "candidates.csv",
    pdf_filename: str = "candidate_report.pdf",
    report_title: str = "Candidate Report",
) -> None:
    """
    Render a side-by-side CSV + PDF export button row.

    Intended for use at the top or bottom of candidate tables.
    """
    col_csv, col_pdf = st.columns(2)
    with col_csv:
        render_csv_export(df, filename=csv_filename)
    with col_pdf:
        render_pdf_export(df, filename=pdf_filename, title=report_title)
