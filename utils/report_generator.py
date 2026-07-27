"""
Report generation utilities.

Provides CSV and PDF export for candidate data.

PDF generation uses fpdf2 — a pure-Python library with no system
dependencies.  If fpdf2 is unavailable, the module degrades gracefully
by raising a descriptive ImportError at call time rather than at import.
"""

from __future__ import annotations

import io
import logging
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.formatters import format_date, format_experience, format_score

logger = logging.getLogger(__name__)

# ── Column configuration for exports ─────────────────────────────────────────

_CSV_COLUMNS = [
    "id", "name", "email", "phone", "role", "status",
    "ats_score", "experience_years", "education", "location", "applied_date",
]

_CSV_RENAME = {
    "id":               "Candidate ID",
    "name":             "Full Name",
    "email":            "Email",
    "phone":            "Phone",
    "role":             "Applied Role",
    "status":           "Pipeline Status",
    "ats_score":        "ATS Score",
    "experience_years": "Experience (Years)",
    "education":        "Education Level",
    "location":         "Location",
    "applied_date":     "Applied Date",
}


# ── CSV export ────────────────────────────────────────────────────────────────

def to_csv(df: pd.DataFrame) -> bytes:
    """
    Export a candidate DataFrame to UTF-8 CSV bytes.

    Only the columns listed in _CSV_COLUMNS are included.  Missing columns
    are silently ignored to handle filtered DataFrames gracefully.

    Returns:
        UTF-8 encoded CSV bytes with a BOM for Excel compatibility.
    """
    present_cols = [c for c in _CSV_COLUMNS if c in df.columns]
    export_df = df[present_cols].copy()

    if "applied_date" in export_df.columns:
        export_df["applied_date"] = export_df["applied_date"].apply(
            lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else ""
        )
    if "skills" in export_df.columns:
        export_df["skills"] = export_df["skills"].apply(
            lambda s: ", ".join(s) if isinstance(s, list) else s
        )

    export_df = export_df.rename(columns=_CSV_RENAME)

    buf = io.StringIO()
    export_df.to_csv(buf, index=False)
    # Return UTF-8 BOM + content for seamless Excel opening
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


# ── PDF export ────────────────────────────────────────────────────────────────

def to_pdf(
    df: pd.DataFrame,
    title: str = "Candidate Report",
    generated_by: str = "Resume Parser System",
) -> bytes:
    """
    Generate a PDF report from a candidate DataFrame.

    Requires ``fpdf2``.  Raises ImportError with an installation hint
    if the package is absent.

    Args:
        df:           Candidate DataFrame to include in the report.
        title:        Report heading displayed at the top.
        generated_by: Label shown in the report footer.

    Returns:
        PDF file as bytes.
    """
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise ImportError(
            "PDF export requires fpdf2. Install it with: pip install fpdf2"
        ) from exc

    logger.info("Generating PDF report: %s (%d candidates)", title, len(df))
    pdf = _build_pdf(df, title, generated_by)
    return bytes(pdf.output())


def _build_pdf(df: pd.DataFrame, title: str, generated_by: str) -> "FPDF":  # type: ignore[name-defined]
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", style="B", size=18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(
        0, 6,
        f"Generated {date.today().strftime('%B %d, %Y')}  ·  {len(df)} candidates  ·  {generated_by}",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    # ── Summary bar ──────────────────────────────────────────────────────────
    if len(df) > 0:
        avg_score = df["ats_score"].mean() if "ats_score" in df.columns else 0
        pdf.set_font("Helvetica", style="B", size=10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, "Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 5, f"Total candidates: {len(df)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"Average ATS score: {avg_score:.1f}", new_x="LMARGIN", new_y="NEXT")
        if "status" in df.columns:
            hired = int((df["status"] == "Hired").sum())
            pdf.cell(0, 5, f"Hired: {hired}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

    # ── Table ─────────────────────────────────────────────────────────────────
    columns = [
        ("Name",       "name",             48, "L"),
        ("Role",       "role",             46, "L"),
        ("Status",     "status",           26, "C"),
        ("ATS Score",  "ats_score",        18, "C"),
        ("Experience", "experience_years", 22, "C"),
        ("Applied",    "applied_date",     26, "C"),
    ]

    # Header row
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(15, 23, 42)
    for label, _, width, align in columns:
        pdf.cell(width, 7, label, border=1, align=align, fill=True)
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", size=8)
    for _, row in df.head(200).iterrows():
        fill = False
        pdf.set_fill_color(248, 250, 252)
        pdf.set_text_color(71, 85, 105)
        for _, col_key, width, align in columns:
            val = row.get(col_key, "")
            if col_key == "ats_score" and pd.notna(val):
                text = f"{float(val):.1f}"
            elif col_key == "experience_years" and pd.notna(val):
                text = f"{float(val):.1f} yr"
            elif col_key == "applied_date" and pd.notna(val):
                text = pd.Timestamp(val).strftime("%b %d, %Y") if val else ""
            else:
                text = str(val)[:32] if val else ""
            pdf.cell(width, 6, text, border="B", align=align, fill=fill)
        pdf.ln()

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-14)
    pdf.set_font("Helvetica", size=7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, f"Confidential · {generated_by}", align="C")

    return pdf
