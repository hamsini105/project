"""
Job Description parser.

Converts unstructured job posting text into a well-typed JobDescription model
using pattern-based section detection and keyword extraction.  No ML or LLM
dependencies — the parser is deterministic and fast.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from job_matching.config import (
    EDUCATION_KEYWORDS,
    EDUCATION_LEVELS,
    EXPERIENCE_REGEX_PATTERNS,
    JD_SECTION_HEADERS,
    KNOWN_TECH_SKILLS,
)
from job_matching.exceptions import JDParsingException
from job_matching.models import JobDescription

logger = logging.getLogger(__name__)

# Pre-compiled experience patterns for performance
_EXP_PATTERNS: List[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in EXPERIENCE_REGEX_PATTERNS
]

# Bullet point markers commonly used in job postings
_BULLET_RE = re.compile(r"^[\s]*[•\-\*\u2022\u2023\u25e6◦‣⁃]\s+", re.MULTILINE)
_NUMBERED_RE = re.compile(r"^[\s]*\d+[\.\)]\s+", re.MULTILINE)


class JDParser:
    """
    Parses raw job description text into a structured JobDescription.

    Design notes:
    - Section detection uses substring matching against curated header lists
      rather than regex so the rules are readable and easy to extend.
    - Skill extraction matches against a curated KNOWN_TECH_SKILLS list
      ordered longest-first to prevent partial matches.
    - Experience patterns handle the most common phrasings ("3+ years",
      "3-5 years", "minimum 3 years") but intentionally avoid over-engineering
      for edge cases that rarely appear in practice.
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def parse(
        self,
        raw_text:  str,
        title:     str = "",
        company:   str = "",
        location:  str = "",
        job_type:  str = "",
    ) -> JobDescription:
        """
        Parse a raw job description into a structured model.

        Args:
            raw_text: The full text of the job posting.
            title:    Job title override.  If empty, the first non-blank line
                      of the text is used as a fallback.
            company:  Company name (optional).
            location: Work location (optional).
            job_type: Employment type, e.g. "Full-time" (optional).

        Returns:
            A populated JobDescription model.

        Raises:
            JDParsingException: If raw_text is blank or an unexpected error
                                 occurs during parsing.
        """
        if not raw_text or not raw_text.strip():
            raise JDParsingException("Job description text must not be empty.")

        logger.info("Parsing job description: %s", title or "(title not provided)")

        try:
            sections = self._split_into_sections(raw_text)

            required_skills  = self._extract_skills_from_section(sections.get("requirements", ""))
            preferred_skills = self._extract_skills_from_section(sections.get("preferred", ""))
            responsibilities = self._extract_bullet_items(sections.get("responsibilities", ""))

            # Fall back to scanning full text when dedicated sections are missing
            if not required_skills and not preferred_skills:
                required_skills = self._extract_skills_from_section(raw_text)
                logger.debug("No skill sections found; scanning full text for skills.")

            min_exp, max_exp  = self._extract_experience_years(raw_text)
            education_level   = self._extract_education_level(raw_text)
            resolved_title    = title or self._extract_title(raw_text)

            jd = JobDescription(
                title=resolved_title,
                company=company or None,
                raw_text=raw_text,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                responsibilities=responsibilities,
                min_experience_years=min_exp,
                max_experience_years=max_exp,
                education_level=education_level,
                location=location or None,
                job_type=job_type or None,
            )

            logger.debug(
                "Parsed JD '%s': %d required skills, %d preferred skills, "
                "experience %.0f–%.0f yrs.",
                resolved_title,
                len(required_skills),
                len(preferred_skills),
                min_exp or 0,
                max_exp or 0,
            )
            return jd

        except JDParsingException:
            raise
        except Exception as exc:
            raise JDParsingException(
                f"Unexpected error while parsing job description: {exc}"
            ) from exc

    # ── Section Detection ──────────────────────────────────────────────────────

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split JD text into named buckets based on section header detection.

        Returns a dict mapping canonical section names to the text that
        followed the corresponding header.  Unrecognised text lands in the
        "intro" bucket.
        """
        current_section = "intro"
        section_lines:  Dict[str, List[str]] = {current_section: []}

        for raw_line in text.split("\n"):
            matched = self._detect_section_header(raw_line)
            if matched:
                current_section = matched
                section_lines.setdefault(current_section, [])
            else:
                section_lines.setdefault(current_section, []).append(raw_line)

        return {sec: "\n".join(lines) for sec, lines in section_lines.items()}

    def _detect_section_header(self, line: str) -> Optional[str]:
        """Return canonical section name if the line is a recognisable header."""
        stripped = line.strip().lower()
        # Typical headers are short; skip long prose lines early.
        if not stripped or len(stripped) > 80:
            return None
        for section_key, patterns in JD_SECTION_HEADERS.items():
            for pattern in patterns:
                if pattern in stripped:
                    return section_key
        return None

    # ── Skill Extraction ───────────────────────────────────────────────────────

    def _extract_skills_from_section(self, text: str) -> List[str]:
        """
        Extract tech skills from a section of text.

        Matching is performed against KNOWN_TECH_SKILLS (longest-first) to
        prevent "python" from being consumed before "python 3" style phrases.
        Matches are case-preserved from the source list for consistency.
        """
        if not text.strip():
            return []

        text_lower = text.lower()
        found: List[str] = []
        # Track consumed character ranges to prevent double-counting
        consumed_spans: List[Tuple[int, int]] = []

        for skill in KNOWN_TECH_SKILLS:
            pattern = re.compile(
                r"(?<![a-z0-9\+\#])" + re.escape(skill) + r"(?![a-z0-9\+\#])",
                re.IGNORECASE,
            )
            for match in pattern.finditer(text_lower):
                start, end = match.span()
                if not self._overlaps(start, end, consumed_spans):
                    found.append(skill)
                    consumed_spans.append((start, end))
                    break  # Record each skill once per section

        return found

    @staticmethod
    def _overlaps(start: int, end: int, spans: List[Tuple[int, int]]) -> bool:
        return any(s < end and start < e for s, e in spans)

    # ── Bullet Point Extraction ───────────────────────────────────────────────

    def _extract_bullet_items(self, text: str) -> List[str]:
        """
        Extract individual responsibility lines from bulleted or numbered lists.

        Falls back to returning non-empty lines when no recognised bullet
        markers are present.
        """
        if not text.strip():
            return []

        # Try bullet markers first, then numbered, then plain lines
        lines: List[str] = []
        for raw_line in text.split("\n"):
            clean = _BULLET_RE.sub("", raw_line).strip()
            clean = _NUMBERED_RE.sub("", clean).strip()
            if clean and len(clean) > 10:  # skip very short lines (artefacts)
                lines.append(clean)

        return lines

    # ── Experience Extraction ─────────────────────────────────────────────────

    def _extract_experience_years(
        self, text: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract a (min, max) experience requirement from job description text.

        Returns (None, None) when no experience requirement is found.
        """
        for pattern in _EXP_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            groups = [g for g in match.groups() if g is not None]
            if len(groups) == 2:
                # Range pattern: "3-5 years"
                return float(groups[0]), float(groups[1])
            if len(groups) == 1:
                min_yrs = float(groups[0])
                return min_yrs, None
        return None, None

    # ── Education Extraction ──────────────────────────────────────────────────

    def _extract_education_level(self, text: str) -> Optional[str]:
        """
        Identify the minimum education level mentioned in the JD.

        Returns the canonical level name (e.g. "bachelor") or None.
        """
        text_lower = text.lower()
        highest_level: Optional[str] = None
        highest_ordinal: int = 0

        for level, keywords in EDUCATION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    ordinal = EDUCATION_LEVELS.get(level, 0)
                    if ordinal > highest_ordinal:
                        highest_ordinal = ordinal
                        highest_level = level
                    break  # one keyword match per level is sufficient

        return highest_level

    # ── Title Extraction ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_title(text: str) -> str:
        """Return the first non-blank line of the text, truncated to 120 chars."""
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                return stripped[:120]
        return "Unknown Position"
