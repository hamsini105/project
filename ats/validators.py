"""
Resume validators for ATS analysis.

Validates resume data for ATS compatibility and identifies issues.
"""

import logging
from typing import List, Tuple

from parser.models import Resume

from ats.config import (
    CONTACT_DETAILS_REQUIRED,
    MIN_SKILLS_REQUIRED,
    MIN_EDUCATION_REQUIRED,
    MIN_EXPERIENCE_REQUIRED,
    MIN_PROFESSIONAL_SUMMARY_LENGTH,
    WEAKNESS_THRESHOLDS,
)
from ats.exceptions import ValidationException
from ats.models import Weakness

logger = logging.getLogger(__name__)


class ResumeValidator:
    """Validates resume data for ATS analysis."""

    def __init__(self, resume: Resume) -> None:
        """
        Initialize validator with resume data.

        Args:
            resume: Resume object to validate.
        """
        self.resume = resume
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate resume for basic requirements.

        Returns:
            True if resume passes validation, False otherwise.

        Raises:
            ValidationException: If critical validation fails.
        """
        try:
            # Check required contact details
            self._validate_contact_details()

            # Check for essential sections
            self._validate_essential_sections()

            if self.errors:
                error_msg = f"Validation failed: {'; '.join(self.errors)}"
                logger.error(error_msg)
                raise ValidationException(error_msg)

            logger.debug("Resume validation passed")
            return True

        except ValidationException:
            raise
        except Exception as e:
            msg = f"Unexpected error during validation: {e}"
            logger.error(msg)
            raise ValidationException(msg) from e

    def _validate_contact_details(self) -> None:
        """Validate required contact details are present."""
        if not self.resume.contact:
            self.errors.append("Contact details are missing")
            return

        if not self.resume.contact.full_name:
            self.errors.append("Full name is missing")

        if not self.resume.contact.email:
            self.errors.append("Email is missing")

        if not self.resume.contact.phone:
            self.warnings.append("Phone number is missing")

        logger.debug("Contact details validation completed")

    def _validate_essential_sections(self) -> None:
        """Validate essential resume sections are present."""
        if not self.resume.skills or len(self.resume.skills) < MIN_SKILLS_REQUIRED:
            self.warnings.append(f"Resume has fewer than {MIN_SKILLS_REQUIRED} skills")

        if not self.resume.education or len(self.resume.education) < MIN_EDUCATION_REQUIRED:
            self.warnings.append("Resume missing education history")

        if not self.resume.experience or len(self.resume.experience) < MIN_EXPERIENCE_REQUIRED:
            self.warnings.append("Resume missing work experience")

        logger.debug("Essential sections validation completed")

    def check_gaps_in_employment(self) -> List[Tuple[str, str, float]]:
        """
        Check for employment gaps in work history.

        Returns:
            List of tuples (gap_description, severity, gap_years).
        """
        gaps = []

        if not self.resume.experience or len(self.resume.experience) < 2:
            return gaps

        # Sort experience by end date (most recent first)
        sorted_exp = sorted(
            self.resume.experience,
            key=lambda x: x.end_date or x.start_date,
            reverse=True,
        )

        for i in range(len(sorted_exp) - 1):
            current_exp = sorted_exp[i]
            next_exp = sorted_exp[i + 1]

            # Skip if missing dates
            if not current_exp.start_date or not next_exp.end_date:
                continue

            # Calculate gap
            gap_days = (current_exp.start_date - next_exp.end_date).days
            gap_years = gap_days / 365.25

            if gap_years > WEAKNESS_THRESHOLDS.get("gaps_in_employment", 0.5):
                gap_description = f"{gap_years:.1f} years between {next_exp.company} and {current_exp.company}"
                severity = "High" if gap_years > 1 else "Medium"
                gaps.append((gap_description, severity, gap_years))

        logger.debug(f"Found {len(gaps)} employment gaps")
        return gaps

    def check_text_quality(self) -> List[Weakness]:
        """
        Check text quality of descriptions and achievements.

        Returns:
            List of identified weaknesses.
        """
        weaknesses = []

        if not self.resume.experience:
            return weaknesses

        short_descriptions_count = 0

        for exp in self.resume.experience:
            if exp.description:
                for desc in exp.description:
                    if len(desc) < WEAKNESS_THRESHOLDS.get("short_descriptions", 20):
                        short_descriptions_count += 1

        if short_descriptions_count > len(self.resume.experience) * 0.5:
            weaknesses.append(
                Weakness(
                    category="text_quality",
                    description="Multiple short or vague job descriptions found",
                    severity="Medium",
                )
            )

        logger.debug(f"Found {len(weaknesses)} text quality issues")
        return weaknesses

    def check_quantified_achievements(self) -> float:
        """
        Check percentage of achievements with quantified results.

        Returns:
            Percentage of descriptions with quantified results (0-100).
        """
        if not self.resume.experience:
            return 0

        total_descriptions = 0
        quantified_count = 0
        quantified_keywords = {"increased", "reduced", "saved", "grew", "improved", "achieved"}

        for exp in self.resume.experience:
            if exp.description:
                total_descriptions += len(exp.description)
                for desc in exp.description:
                    if any(keyword in desc.lower() for keyword in quantified_keywords):
                        # Check if numbers are present
                        if any(char.isdigit() for char in desc):
                            quantified_count += 1

        if total_descriptions == 0:
            return 0

        percentage = (quantified_count / total_descriptions) * 100
        logger.debug(f"Quantified achievements: {percentage:.1f}%")
        return percentage

    def get_warnings(self) -> List[str]:
        """
        Get list of validation warnings.

        Returns:
            List of warning messages.
        """
        return self.warnings

    def get_errors(self) -> List[str]:
        """
        Get list of validation errors.

        Returns:
            List of error messages.
        """
        return self.errors
