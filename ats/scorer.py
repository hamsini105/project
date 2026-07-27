"""
ATS scoring engine for resume analysis.

Calculates ATS scores based on configurable weights and scoring rules.
"""

import logging
from typing import Dict

from parser.models import Resume

from ats.config import (
    SCORING_WEIGHTS,
    SCORE_RANGES,
    SECTION_COMPLETENESS_SCORES,
    HIGH_VALUE_KEYWORDS,
    ACHIEVEMENT_KEYWORDS,
    CONTACT_DETAILS_REQUIRED,
    CONTACT_DETAILS_OPTIONAL,
    MIN_PROFESSIONAL_SUMMARY_LENGTH,
)
from ats.completeness import CompletenessAnalyzer
from ats.experience_calc import ExperienceCalculator
from ats.exceptions import ScoringException

logger = logging.getLogger(__name__)


class ATSScorer:
    """Calculates ATS scores based on resume content and configuration."""

    def __init__(self, resume: Resume) -> None:
        """
        Initialize scorer with resume data.

        Args:
            resume: Resume object to score.
        """
        self.resume = resume
        self.completeness_analyzer = CompletenessAnalyzer(resume)
        self.experience_calc = ExperienceCalculator(resume)

    def score_resume(self) -> tuple[float, Dict[str, float]]:
        """
        Calculate overall ATS score and breakdown by category.

        Returns:
            Tuple of (overall_score, score_breakdown).

        Raises:
            ScoringException: If scoring fails.
        """
        try:
            scores = {
                "contact_details": self._score_contact_details(),
                "professional_summary": self._score_professional_summary(),
                "skills": self._score_skills(),
                "education": self._score_education(),
                "experience": self._score_experience(),
                "projects": self._score_projects(),
                "certifications": self._score_certifications(),
                "formatting": self._score_formatting(),
                "keywords": self._score_keywords(),
            }

            # Calculate weighted overall score
            overall_score = self._calculate_overall_score(scores)

            logger.debug(f"Scoring complete. Overall score: {overall_score:.1f}")
            logger.debug(f"Score breakdown: {scores}")

            return overall_score, scores

        except Exception as e:
            msg = f"Scoring failed: {e}"
            logger.error(msg)
            raise ScoringException(msg) from e

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall score from category scores.

        Args:
            scores: Dictionary of category scores.

        Returns:
            Weighted overall score (0-100).
        """
        total_score = 0.0

        for category, weight in SCORING_WEIGHTS.items():
            category_score = scores.get(category, 0)
            weighted_score = (category_score * weight) / 100
            total_score += weighted_score

        # Round to 1 decimal place
        total_score = round(total_score, 1)
        return total_score

    def _score_contact_details(self) -> float:
        """
        Score contact details section.

        Returns:
            Score 0-100.
        """
        if not self.resume.contact:
            return 0.0

        score = 0.0
        max_score = SECTION_COMPLETENESS_SCORES["contact_details"]["required"]

        # Check required fields
        required_score = 0
        for field, required in CONTACT_DETAILS_REQUIRED.items():
            if required:
                value = getattr(self.resume.contact, field, None)
                if value:
                    required_score += max_score / len(CONTACT_DETAILS_REQUIRED)

        score += required_score

        # Check optional fields for bonus
        optional_score = 0
        optional_points_per_field = SECTION_COMPLETENESS_SCORES["contact_details"][
            "optional_per_field"
        ]
        for field, included in CONTACT_DETAILS_OPTIONAL.items():
            if included:
                value = getattr(self.resume.contact, field, None)
                if value:
                    optional_score += optional_points_per_field

        score += min(optional_score, 20)  # Cap bonus

        logger.debug(f"Contact details score: {score:.1f}")
        return min(score, 100.0)

    def _score_professional_summary(self) -> float:
        """
        Score professional summary section.

        Returns:
            Score 0-100.
        """
        if not self.resume.summary:
            return 0.0

        summary_length = len(self.resume.summary)

        # Scoring logic
        if summary_length < MIN_PROFESSIONAL_SUMMARY_LENGTH:
            score = (summary_length / MIN_PROFESSIONAL_SUMMARY_LENGTH) * 50
        elif summary_length < 200:
            score = 75.0
        elif summary_length < 500:
            score = 90.0
        else:
            score = 100.0

        logger.debug(f"Professional summary score: {score:.1f}")
        return score

    def _score_skills(self) -> float:
        """
        Score skills section.

        Returns:
            Score 0-100.
        """
        if not self.resume.skills:
            return 0.0

        skills_count = len(self.resume.skills)
        base_score = SECTION_COMPLETENESS_SCORES["skills"]["base"]
        per_skill_points = SECTION_COMPLETENESS_SCORES["skills"]["per_skill"]
        max_bonus = SECTION_COMPLETENESS_SCORES["skills"]["max_bonus"]

        # Calculate score
        skill_bonus = min(skills_count * per_skill_points, max_bonus)
        score = min(base_score + skill_bonus, 100.0)

        logger.debug(f"Skills score: {score:.1f} ({skills_count} skills)")
        return score

    def _score_education(self) -> float:
        """
        Score education section.

        Returns:
            Score 0-100.
        """
        if not self.resume.education:
            return 0.0

        edu_count = len(self.resume.education)
        base_score = SECTION_COMPLETENESS_SCORES["education"]["base"]
        per_entry_points = SECTION_COMPLETENESS_SCORES["education"]["per_entry"]
        max_bonus = SECTION_COMPLETENESS_SCORES["education"]["max_bonus"]

        # Calculate score
        entry_bonus = min(edu_count * per_entry_points, max_bonus)
        score = min(base_score + entry_bonus, 100.0)

        # Bonus for degree information
        for edu in self.resume.education:
            if edu.degree and edu.field_of_study:
                score = min(score + 5, 100.0)
                break

        logger.debug(f"Education score: {score:.1f}")
        return score

    def _score_experience(self) -> float:
        """
        Score work experience section.

        Returns:
            Score 0-100.
        """
        if not self.resume.experience:
            return 0.0

        exp_count = len(self.resume.experience)
        total_years = self.experience_calc.calculate_total_experience()

        base_score = SECTION_COMPLETENESS_SCORES["experience"]["base"]
        per_year_points = SECTION_COMPLETENESS_SCORES["experience"]["per_year"]
        max_bonus = SECTION_COMPLETENESS_SCORES["experience"]["max_bonus"]

        # Calculate score based on years and count
        year_bonus = min(total_years * per_year_points, max_bonus)
        score = min(base_score + year_bonus, 100.0)

        # Bonus for good descriptions
        total_descriptions = 0
        good_descriptions = 0

        for exp in self.resume.experience:
            if exp.description:
                total_descriptions += len(exp.description)
                for desc in exp.description:
                    if len(desc) > 20:  # Good description
                        good_descriptions += 1

        if total_descriptions > 0:
            desc_quality = good_descriptions / total_descriptions
            if desc_quality > 0.7:
                score = min(score + 5, 100.0)

        logger.debug(f"Experience score: {score:.1f} ({total_years} years)")
        return score

    def _score_projects(self) -> float:
        """
        Score projects section.

        Returns:
            Score 0-100.
        """
        if not self.resume.projects:
            return 0.0

        projects_count = len(self.resume.projects)
        base_score = SECTION_COMPLETENESS_SCORES["projects"]["base"]
        per_project_points = SECTION_COMPLETENESS_SCORES["projects"]["per_project"]
        max_bonus = SECTION_COMPLETENESS_SCORES["projects"]["max_bonus"]

        # Calculate score
        project_bonus = min(projects_count * per_project_points, max_bonus)
        score = min(base_score + project_bonus, 100.0)

        logger.debug(f"Projects score: {score:.1f}")
        return score

    def _score_certifications(self) -> float:
        """
        Score certifications section.

        Returns:
            Score 0-100.
        """
        if not self.resume.certifications:
            return 0.0

        cert_count = len(self.resume.certifications)
        base_score = SECTION_COMPLETENESS_SCORES["certifications"]["base"]
        per_cert_points = SECTION_COMPLETENESS_SCORES["certifications"]["per_certification"]
        max_bonus = SECTION_COMPLETENESS_SCORES["certifications"]["max_bonus"]

        # Calculate score
        cert_bonus = min(cert_count * per_cert_points, max_bonus)
        score = min(base_score + cert_bonus, 100.0)

        logger.debug(f"Certifications score: {score:.1f}")
        return score

    def _score_formatting(self) -> float:
        """
        Score document formatting quality.

        Returns:
            Score 0-100.
        """
        score = 80.0  # Default good formatting

        # Check for issues
        if self.resume.contact and self.resume.contact.full_name:
            # Has name - formatting likely OK
            score += 10
        else:
            score -= 20

        # Additional formatting checks would go here
        # For now, based on data completeness

        logger.debug(f"Formatting score: {score:.1f}")
        return min(score, 100.0)

    def _score_keywords(self) -> float:
        """
        Score keyword usage and achievement metrics.

        Returns:
            Score 0-100.
        """
        if not self.resume.experience:
            return 0.0

        score = 50.0  # Base score
        high_value_found = 0
        achievement_count = 0
        total_descriptions = 0

        for exp in self.resume.experience:
            if exp.description:
                for desc in exp.description:
                    total_descriptions += 1
                    desc_lower = desc.lower()

                    # Check for high-value keywords
                    for keyword in HIGH_VALUE_KEYWORDS:
                        if keyword in desc_lower:
                            high_value_found += 1
                            score += 2

                    # Check for achievement keywords
                    for keyword in ACHIEVEMENT_KEYWORDS:
                        if keyword in desc_lower:
                            achievement_count += 1
                            score += 1

        if total_descriptions > 0:
            achievement_ratio = achievement_count / total_descriptions
            if achievement_ratio > 0.5:
                score += 10

        logger.debug(f"Keywords score: {score:.1f}")
        return min(score, 100.0)

    def get_score_rating(self, score: float) -> str:
        """
        Get rating category for a score.

        Args:
            score: ATS score (0-100).

        Returns:
            Rating category (Excellent, Good, Fair, Poor).
        """
        for rating, (min_score, max_score) in SCORE_RANGES.items():
            if min_score <= score <= max_score:
                return rating.capitalize()

        return "Poor"
