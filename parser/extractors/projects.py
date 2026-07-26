"""
Projects extractor from resume text.

Extracts project information including title, description, technologies used,
and links.
"""

import logging
import re
from datetime import date
from typing import List, Optional

from parser.config import YEAR_PATTERN
from parser.extractors.base import BaseExtractor
from parser.models import ProjectEntry

logger = logging.getLogger(__name__)


class ProjectsExtractor(BaseExtractor):
    """Extracts project entries from resume text."""

    def extract(self, text: str) -> List[ProjectEntry]:
        """
        Extract project entries from text.

        Args:
            text: Resume text section containing projects.

        Returns:
            List of ProjectEntry objects.
        """
        try:
            projects = []
            lines = text.split("\n")

            current_project = None
            project_lines = []

            for line in lines:
                cleaned = self.clean_line(line)
                if not cleaned:
                    continue

                # Check if this looks like a project title
                if self._is_project_header(cleaned):
                    # Save previous project
                    if current_project:
                        projects.append(current_project)

                    # Parse new project
                    current_project = self._parse_project(cleaned, project_lines)
                    project_lines = []
                else:
                    project_lines.append(cleaned)

            # Save last project
            if current_project:
                projects.append(current_project)

            logger.debug(f"Extracted {len(projects)} projects")
            return projects

        except Exception as e:
            logger.error(f"Failed to extract projects: {e}")
            return []

    def _is_project_header(self, line: str) -> bool:
        """Check if line looks like a project title."""
        # Usually short, doesn't contain certain action words
        if len(line) > 120:
            return False

        # Check for URL (common in project entries)
        has_url = "http" in line.lower() or ".com" in line.lower()

        # Check if it has pipe separator
        has_pipe = "|" in line

        return has_url or has_pipe or (len(line) > 5 and len(line) < 80)

    def _parse_project(self, header: str, detail_lines: List[str]) -> ProjectEntry:
        """Parse project from header and detail lines."""
        title = None
        description = None
        technologies = []
        link = None
        start_date = None
        end_date = None

        # Extract title and link from header
        if "|" in header:
            parts = header.split("|")
            title = parts[0].strip()
            # Check if second part is a URL
            if "http" in parts[1].lower():
                link = parts[1].strip()
            else:
                title = header
        else:
            # Extract URL if present
            url = self.find_pattern(
                re.compile(
                    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b"
                ),
                header,
            )
            if url:
                link = url
                title = header.replace(url, "").strip()
            else:
                title = header

        # Process detail lines
        combined_details = " ".join(detail_lines)
        description = combined_details if combined_details else None

        # Extract technologies
        technologies = self._extract_technologies(combined_details)

        # Extract dates
        start_date, end_date = self._extract_dates(combined_details)

        return ProjectEntry(
            title=title or "Untitled Project",
            description=description,
            technologies=technologies if technologies else None,
            link=link,
            start_date=start_date,
            end_date=end_date,
        )

    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technologies used in project."""
        tech_keywords = {
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "django",
            "flask",
            "fastapi",
            "react",
            "angular",
            "vue",
            "node.js",
            "express",
            "spring",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "postgresql",
            "mongodb",
            "mysql",
            "redis",
            "elasticsearch",
            "git",
        }

        found_techs = []
        text_lower = text.lower()

        for tech in tech_keywords:
            if re.search(r"\b" + re.escape(tech) + r"\b", text_lower, re.IGNORECASE):
                found_techs.append(tech.title() if tech.islower() else tech)

        return found_techs

    def _extract_dates(self, text: str) -> tuple[Optional[date], Optional[date]]:
        """Extract project dates."""
        years = YEAR_PATTERN.findall(text)

        if len(years) >= 2:
            try:
                return date(int(years[0]), 1, 1), date(int(years[1]), 12, 31)
            except ValueError:
                pass
        elif len(years) == 1:
            try:
                return date(int(years[0]), 1, 1), None
            except ValueError:
                pass

        return None, None
