"""
Education extractor from resume text.

Extracts education history including institution, degree, field of study,
dates, and academic achievements.
"""

import logging
import re
from datetime import date
from typing import List, Optional

from parser.config import DEGREE_KEYWORDS, MONTH_PATTERN, YEAR_PATTERN
from parser.extractors.base import BaseExtractor
from parser.models import EducationEntry

logger = logging.getLogger(__name__)


class EducationExtractor(BaseExtractor):
    """Extracts education entries from resume text."""

    def extract(self, text: str) -> List[EducationEntry]:
        """
        Extract education entries from text.

        Args:
            text: Resume text section containing education.

        Returns:
            List of EducationEntry objects.
        """
        try:
            education_entries = []
            lines = text.split("\n")

            current_entry = None
            entry_lines = []

            for line in lines:
                cleaned = self.clean_line(line)
                if not cleaned:
                    continue

                # Check if this looks like a degree or institution name
                if self._is_education_header(cleaned):
                    # Save previous entry
                    if current_entry:
                        education_entries.append(current_entry)

                    # Parse new entry
                    current_entry = self._parse_education_entry(cleaned, entry_lines)
                    entry_lines = []
                else:
                    entry_lines.append(cleaned)

            # Save last entry
            if current_entry:
                education_entries.append(current_entry)

            logger.debug(f"Extracted {len(education_entries)} education entries")
            return education_entries

        except Exception as e:
            logger.error(f"Failed to extract education: {e}")
            return []

    def _is_education_header(self, line: str) -> bool:
        """Check if line looks like an education entry header."""
        line_lower = line.lower()

        # Check for degree keywords
        has_degree = any(degree in line_lower for degree in DEGREE_KEYWORDS)

        # Check for university/college indicators
        has_institution = any(
            keyword in line_lower for keyword in ["university", "college", "institute", "academy"]
        )

        return has_degree or has_institution

    def _parse_education_entry(self, header: str, detail_lines: List[str]) -> EducationEntry:
        """Parse education entry from header and detail lines."""
        institution = None
        degree = None
        field_of_study = None
        start_date = None
        end_date = None
        grade = None
        details = []

        # Extract institution and degree from header
        parts = header.split(",")
        if len(parts) >= 1:
            institution = parts[0].strip()

        # Look for degree in the header or first few detail lines
        combined_text = header + " " + " ".join(detail_lines[:3])
        degree = self._extract_degree(combined_text)
        field_of_study = self._extract_field_of_study(combined_text)

        # Extract dates
        start_date, end_date = self._extract_dates(combined_text)

        # Extract GPA/Grade
        grade = self._extract_grade(combined_text)

        # Collect detail lines
        for line in detail_lines:
            if line and not self._is_date_line(line):
                details.append(line)

        return EducationEntry(
            institution=institution or "Unknown",
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            grade=grade,
            details=details if details else None,
        )

    def _extract_degree(self, text: str) -> Optional[str]:
        """Extract degree type from text."""
        text_lower = text.lower()

        # Check for exact degree matches
        degree_patterns = {
            "Bachelor": r"\b(?:b\.?s\.?|b\.?a\.?|bachelor(?:\'s)?(?:\s+of)?(?:\s+science|\s+arts)?)",
            "Master": r"\b(?:m\.?s\.?|m\.?a\.?|master(?:\'s)?(?:\s+of)?(?:\s+science|\s+arts)?)",
            "PhD": r"\b(?:ph\.?d\.?|doctor(?:ate)?(?:\s+of)?)",
            "Diploma": r"\b(?:diploma|associate(?:\'s)?)",
        }

        for degree, pattern in degree_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return degree

        return None

    def _extract_field_of_study(self, text: str) -> Optional[str]:
        """Extract field of study from text."""
        # Common fields of study
        fields = [
            "Computer Science",
            "Engineering",
            "Business",
            "Information Technology",
            "Data Science",
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "Economics",
            "Psychology",
            "History",
            "Literature",
        ]

        text_lower = text.lower()
        for field in fields:
            if field.lower() in text_lower:
                return field

        return None

    def _extract_dates(self, text: str) -> tuple[Optional[date], Optional[date]]:
        """Extract start and end dates."""
        years = YEAR_PATTERN.findall(text)
        if len(years) >= 2:
            try:
                return date(int(years[0]), 1, 1), date(int(years[1]), 12, 31)
            except (ValueError, IndexError):
                pass
        elif len(years) == 1:
            try:
                return date(int(years[0]), 1, 1), None
            except ValueError:
                pass

        return None, None

    def _extract_grade(self, text: str) -> Optional[str]:
        """Extract GPA or grade."""
        # Look for GPA pattern like "3.8" or "3.8/4.0"
        gpa_pattern = r"\b([0-4]\.\d{2})\s*(?:/\s*4\.0)?\b"
        match = re.search(gpa_pattern, text)
        if match:
            return match.group(0)

        return None

    def _is_date_line(self, line: str) -> bool:
        """Check if line is primarily a date indicator."""
        return bool(re.search(r"\d{4}", line)) and len(line) < 30
