"""
Skills extractor from resume text.

Extracts technical and soft skills using keyword matching and common
skill patterns found in resumes.
"""

import logging
import re
from typing import List, Set

from parser.config import ALL_TECHNICAL_SKILLS
from parser.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

# Common soft skills
SOFT_SKILLS = {
    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "critical thinking",
    "time management",
    "organization",
    "presentation",
    "negotiation",
    "adaptability",
    "creativity",
    "project management",
    "agile",
    "scrum",
    "kanban",
    "documentation",
    "testing",
    "debugging",
}


class SkillsExtractor(BaseExtractor):
    """Extracts skills from resume text."""

    def extract(self, text: str) -> List[str]:
        """
        Extract skills from text.

        Args:
            text: Resume text to extract from.

        Returns:
            List of extracted skills.
        """
        try:
            skills: Set[str] = set()

            # Extract technical skills
            technical_skills = self._extract_technical_skills(text)
            skills.update(technical_skills)

            # Extract soft skills
            soft_skills = self._extract_soft_skills(text)
            skills.update(soft_skills)

            # Extract skills listed in bullet points
            bullet_skills = self._extract_bullet_skills(text)
            skills.update(bullet_skills)

            # Remove duplicates and sort
            unique_skills = sorted(list(skills))

            logger.debug(f"Extracted {len(unique_skills)} skills")
            return unique_skills

        except Exception as e:
            logger.error(f"Failed to extract skills: {e}")
            return []

    def _extract_technical_skills(self, text: str) -> List[str]:
        """Extract technical skills using keyword matching."""
        skills = []
        text_lower = text.lower()

        for skill in ALL_TECHNICAL_SKILLS:
            # Use word boundaries to match whole words/phrases
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower, re.IGNORECASE):
                skills.append(skill.title() if skill.islower() else skill)

        return skills

    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills using keyword matching."""
        skills = []
        text_lower = text.lower()

        for skill in SOFT_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower, re.IGNORECASE):
                skills.append(skill.title())

        return skills

    def _extract_bullet_skills(self, text: str) -> List[str]:
        """Extract skills from bullet-point lists."""
        skills = []
        lines = text.split("\n")

        for line in lines:
            # Check if line starts with bullet point
            if re.match(r"^\s*[•\-\*]\s+", line):
                # Extract skill item - typically short phrases
                skill = re.sub(r"^\s*[•\-\*]\s+", "", line).strip()

                # Filter for actual skill items
                if (
                    skill
                    and len(skill) < 80
                    and not any(
                        keyword in skill.lower()
                        for keyword in ["designed", "developed", "created", "managed", "led"]
                    )
                ):
                    # Check if it contains a known skill
                    for known_skill in ALL_TECHNICAL_SKILLS | SOFT_SKILLS:
                        if known_skill.lower() in skill.lower():
                            skills.append(skill)
                            break

        return skills
