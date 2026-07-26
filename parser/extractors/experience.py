"""
Work experience extractor from resume text.

Extracts employment history including company, position, dates,
and job responsibilities/achievements.
"""

import logging
import re
from datetime import date
from typing import List, Optional

from parser.config import MONTH_PATTERN, YEAR_PATTERN
from parser.extractors.base import BaseExtractor
from parser.models import ExperienceEntry

logger = logging.getLogger(__name__)

# Words that typically precede job descriptions
DESCRIPTION_INDICATORS = {
    "responsible",
    "managed",
    "led",
    "developed",
    "designed",
    "created",
    "implemented",
    "improved",
    "increased",
    "reduced",
    "achieved",
    "collaborated",
}


class ExperienceExtractor(BaseExtractor):
    """Extracts work experience entries from resume text."""

    def extract(self, text: str) -> List[ExperienceEntry]:
        """
        Extract experience entries from text.

        Args:
            text: Resume text section containing experience.

        Returns:
            List of ExperienceEntry objects.
        """
        try:
            experience_entries = []
            lines = text.split("\n")

            current_entry = None
            entry_lines = []

            for line in lines:
                cleaned = self.clean_line(line)
                if not cleaned:
                    continue

                # Check if this looks like a job title/company header
                if self._is_experience_header(cleaned):
                    # Save previous entry
                    if current_entry:
                        experience_entries.append(current_entry)

                    # Parse new entry
                    current_entry = self._parse_experience_entry(cleaned, entry_lines)
                    entry_lines = []
                else:
                    entry_lines.append(cleaned)

            # Save last entry
            if current_entry:
                experience_entries.append(current_entry)

            logger.debug(f"Extracted {len(experience_entries)} experience entries")
            return experience_entries

        except Exception as e:
            logger.error(f"Failed to extract experience: {e}")
            return []

    def _is_experience_header(self, line: str) -> bool:
        """Check if line looks like an experience entry header."""
        # Typically: "Company Name | Job Title" or "Job Title at Company"
        # Or on separate lines with dates

        has_pipe = "|" in line
        has_at = " at " in line.lower()
        has_date = bool(YEAR_PATTERN.search(line))

        # Check for common job title indicators
        job_title_indicators = [
            "engineer",
            "developer",
            "manager",
            "analyst",
            "architect",
            "consultant",
            "director",
            "lead",
            "specialist",
            "coordinator",
        ]
        has_job_title = any(title in line.lower() for title in job_title_indicators)

        return (has_pipe or has_at or has_job_title) and len(line) < 150

    def _parse_experience_entry(self, header: str, detail_lines: List[str]) -> ExperienceEntry:
        """Parse experience entry from header and detail lines."""
        company = None
        position = None
        location = None
        start_date = None
        end_date = None
        is_current = False
        description = []

        # Parse company and position from header
        if "|" in header:
            parts = header.split("|")
            company = parts[0].strip()
            position = parts[1].strip() if len(parts) > 1 else None
        elif " at " in header.lower():
            match = re.split(r"\s+at\s+", header, flags=re.IGNORECASE)
            position = match[0].strip()
            company = match[1].strip() if len(match) > 1 else None
        else:
            # Assume first part is position or company
            position = header.strip()

        # Extract dates and location from detail lines
        for line in detail_lines:
            # Check for date line
            dates = self._extract_dates(line)
            if dates[0]:
                start_date = dates[0]
                end_date = dates[1]
                is_current = "present" in line.lower() or "current" in line.lower()

            # Check for location
            if self._is_location_line(line):
                location = line.strip()
            # Otherwise treat as description
            elif line and not self._is_date_line(line):
                description.append(line)

        return ExperienceEntry(
            company=company or "Unknown",
            position=position or "Unknown",
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description if description else None,
        )

    def _extract_dates(self, text: str) -> tuple[Optional[date], Optional[date]]:
        """Extract start and end dates."""
        # Look for patterns like "Jan 2020 - Dec 2023" or "2020-2023"

        years = YEAR_PATTERN.findall(text)
        months = MONTH_PATTERN.findall(text)

        start_date = None
        end_date = None

        # Parse dates
        if len(years) >= 2:
            try:
                month_idx = 1
                if months:
                    month_idx = self._month_to_number(months[0])
                start_date = date(int(years[0]), month_idx, 1)

                if "present" not in text.lower() and "current" not in text.lower():
                    month_idx = 12
                    if len(months) > 1:
                        month_idx = self._month_to_number(months[1])
                    end_date = date(int(years[1]), month_idx, 1)
            except (ValueError, IndexError):
                pass

        elif len(years) == 1:
            try:
                month_idx = 1
                if months:
                    month_idx = self._month_to_number(months[0])
                start_date = date(int(years[0]), month_idx, 1)
            except ValueError:
                pass

        return start_date, end_date

    def _month_to_number(self, month_str: str) -> int:
        """Convert month name to number."""
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "sept": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        return months.get(month_str.lower(), 1)

    def _is_location_line(self, line: str) -> bool:
        """Check if line appears to be a location."""
        # Pattern: "City, State" or "City, Country"
        return bool(re.search(r"^[A-Z][a-z]+,\s*[A-Z]", line)) and len(line) < 50

    def _is_date_line(self, line: str) -> bool:
        """Check if line is primarily a date indicator."""
        return bool(YEAR_PATTERN.search(line)) and len(line) < 50
