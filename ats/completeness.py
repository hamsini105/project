"""
Resume completeness analysis for ATS.

Analyzes how complete each section of the resume is and overall completeness.
"""

import logging
from typing import List

from parser.models import Resume

from ats.config import (
    MIN_SKILLS_REQUIRED,
    SECTION_COMPLETENESS_SCORES,
)
from ats.models import CompletenessReport

logger = logging.getLogger(__name__)


class CompletenessAnalyzer:
    """Analyzes resume completeness for each section."""

    def __init__(self, resume: Resume) -> None:
        """
        Initialize analyzer with resume data.

        Args:
            resume: Resume object to analyze.
        """
        self.resume = resume

    def analyze(self) -> CompletenessReport:
        """
        Analyze overall and section-level completeness.

        Returns:
            CompletenessReport with detailed breakdown.
        """
        try:
            # Contact details analysis
            contact_complete, missing_fields = self._analyze_contact_details()

            # Section presence checks
            summary_present = bool(self.resume.summary and len(self.resume.summary) > 10)
            skills_present = bool(self.resume.skills and len(self.resume.skills) > 0)
            skills_count = len(self.resume.skills or [])
            education_present = bool(self.resume.education and len(self.resume.education) > 0)
            education_count = len(self.resume.education or [])
            experience_present = bool(self.resume.experience and len(self.resume.experience) > 0)
            experience_count = len(self.resume.experience or [])
            projects_present = bool(self.resume.projects and len(self.resume.projects) > 0)
            projects_count = len(self.resume.projects or [])
            certifications_present = bool(
                self.resume.certifications and len(self.resume.certifications) > 0
            )
            certifications_count = len(self.resume.certifications or [])

            # Calculate overall completeness
            overall_completeness = self._calculate_overall_completeness(
                contact_complete,
                summary_present,
                skills_present,
                education_present,
                experience_present,
                projects_present,
                certifications_present,
            )

            report = CompletenessReport(
                contact_details_complete=contact_complete,
                contact_details_missing_fields=missing_fields,
                professional_summary_present=summary_present,
                skills_present=skills_present,
                skills_count=skills_count,
                education_present=education_present,
                education_count=education_count,
                experience_present=experience_present,
                experience_count=experience_count,
                projects_present=projects_present,
                projects_count=projects_count,
                certifications_present=certifications_present,
                certifications_count=certifications_count,
                overall_completeness=overall_completeness,
            )

            logger.debug(f"Completeness analysis: {overall_completeness:.1f}%")
            return report

        except Exception as e:
            logger.error(f"Completeness analysis failed: {e}")
            raise

    def _analyze_contact_details(self) -> tuple[bool, List[str]]:
        """
        Analyze contact details completeness.

        Returns:
            Tuple of (is_complete, missing_fields_list).
        """
        if not self.resume.contact:
            return False, ["all"]

        missing_fields = []

        if not self.resume.contact.full_name:
            missing_fields.append("full_name")
        if not self.resume.contact.email:
            missing_fields.append("email")
        if not self.resume.contact.phone:
            missing_fields.append("phone")

        is_complete = len(missing_fields) == 0

        logger.debug(f"Contact completeness: {is_complete}, missing: {missing_fields}")
        return is_complete, missing_fields

    def _calculate_overall_completeness(
        self,
        contact_complete: bool,
        summary_present: bool,
        skills_present: bool,
        education_present: bool,
        experience_present: bool,
        projects_present: bool,
        certifications_present: bool,
    ) -> float:
        """
        Calculate overall completeness percentage.

        Returns:
            Completeness percentage (0-100).
        """
        # Weight each section
        weights = {
            "contact": 20,      # Essential
            "summary": 10,      # Important
            "skills": 15,       # Important
            "education": 15,    # Important
            "experience": 25,   # Critical
            "projects": 10,     # Nice to have
            "certifications": 5,  # Nice to have
        }

        total_weight = 0
        score = 0

        # Contact details
        total_weight += weights["contact"]
        if contact_complete:
            score += weights["contact"]

        # Summary
        total_weight += weights["summary"]
        if summary_present:
            score += weights["summary"]

        # Skills
        total_weight += weights["skills"]
        if skills_present:
            score += weights["skills"]

        # Education
        total_weight += weights["education"]
        if education_present:
            score += weights["education"]

        # Experience
        total_weight += weights["experience"]
        if experience_present:
            score += weights["experience"]

        # Projects
        total_weight += weights["projects"]
        if projects_present:
            score += weights["projects"]

        # Certifications
        total_weight += weights["certifications"]
        if certifications_present:
            score += weights["certifications"]

        completeness = (score / total_weight) * 100 if total_weight > 0 else 0
        return round(completeness, 1)

    def get_missing_sections(self) -> List[str]:
        """
        Get list of missing sections.

        Returns:
            List of missing major sections.
        """
        missing = []

        if not self.resume.summary or len(self.resume.summary) < 20:
            missing.append("Professional Summary")

        if not self.resume.skills or len(self.resume.skills) < MIN_SKILLS_REQUIRED:
            missing.append("Skills")

        if not self.resume.education or len(self.resume.education) == 0:
            missing.append("Education")

        if not self.resume.experience or len(self.resume.experience) == 0:
            missing.append("Work Experience")

        if not self.resume.projects or len(self.resume.projects) == 0:
            missing.append("Projects")

        if not self.resume.certifications or len(self.resume.certifications) == 0:
            missing.append("Certifications")

        logger.debug(f"Missing sections: {missing}")
        return missing

    def section_quality_estimate(self) -> dict[str, float]:
        """
        Estimate quality of each section (0-100).

        Returns:
            Dictionary of section name to quality estimate.
        """
        quality = {}

        # Contact quality: 100 if complete, less otherwise
        contact_complete, missing = self._analyze_contact_details()
        quality["contact"] = 100 if contact_complete else max(0, 100 - (len(missing) * 30))

        # Summary quality: based on length
        summary_length = len(self.resume.summary or "")
        quality["summary"] = min(100, max(0, (summary_length / 200) * 100))

        # Skills quality: based on count
        skills_count = len(self.resume.skills or [])
        quality["skills"] = min(100, (skills_count / 10) * 100)

        # Education quality: presence and count
        edu_count = len(self.resume.education or [])
        quality["education"] = 100 if edu_count >= 1 else 0

        # Experience quality: presence and count
        exp_count = len(self.resume.experience or [])
        quality["experience"] = min(100, (exp_count / 3) * 100)

        # Projects quality: presence
        quality["projects"] = 100 if len(self.resume.projects or []) > 0 else 0

        # Certifications quality: presence
        quality["certifications"] = 100 if len(self.resume.certifications or []) > 0 else 0

        logger.debug(f"Section quality estimates: {quality}")
        return quality
