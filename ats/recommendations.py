"""
Recommendation generation for ATS improvement.

Generates actionable recommendations based on resume analysis.
"""

import logging
from typing import List

from parser.models import Resume

from ats.completeness import CompletenessAnalyzer
from ats.config import WEAKNESS_THRESHOLDS, RECOMMENDATION_PRIORITIES
from ats.experience_calc import ExperienceCalculator
from ats.models import Recommendation, Weakness

logger = logging.getLogger(__name__)


class RecommendationGenerator:
    """Generates actionable recommendations for resume improvement."""

    def __init__(self, resume: Resume) -> None:
        """
        Initialize generator with resume data.

        Args:
            resume: Resume object to analyze.
        """
        self.resume = resume
        self.completeness_analyzer = CompletenessAnalyzer(resume)
        self.experience_calc = ExperienceCalculator(resume)

    def generate_recommendations(self, current_score: float) -> List[Recommendation]:
        """
        Generate list of recommendations to improve ATS score.

        Args:
            current_score: Current ATS score (0-100).

        Returns:
            List of recommendations sorted by priority.
        """
        recommendations = []

        try:
            # Contact details recommendations
            recommendations.extend(self._recommend_contact_improvements())

            # Summary recommendations
            recommendations.extend(self._recommend_summary_improvements())

            # Skills recommendations
            recommendations.extend(self._recommend_skills_improvements())

            # Experience recommendations
            recommendations.extend(self._recommend_experience_improvements())

            # Education recommendations
            recommendations.extend(self._recommend_education_improvements())

            # Projects recommendations
            recommendations.extend(self._recommend_projects_improvements())

            # Certifications recommendations
            recommendations.extend(self._recommend_certifications_improvements())

            # General recommendations
            recommendations.extend(self._recommend_general_improvements(current_score))

            # Sort by priority
            priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
            recommendations.sort(key=lambda r: priority_order.get(r.priority, 5))

            logger.debug(f"Generated {len(recommendations)} recommendations")
            return recommendations

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return []

    def _recommend_contact_improvements(self) -> List[Recommendation]:
        """Generate contact details recommendations."""
        recommendations = []
        contact = self.resume.contact

        if not contact or not contact.full_name:
            recommendations.append(
                Recommendation(
                    action="Add or update full name at the top of resume",
                    reason="Full name is critical for ATS identification and recruiter tracking",
                    priority="Critical",
                    estimated_score_improvement=5,
                )
            )

        if not contact or not contact.email:
            recommendations.append(
                Recommendation(
                    action="Add professional email address",
                    reason="Email is essential for contact and ATS processing",
                    priority="Critical",
                    estimated_score_improvement=5,
                )
            )

        if not contact or not contact.phone:
            recommendations.append(
                Recommendation(
                    action="Add phone number",
                    reason="Phone numbers are important for recruiter outreach",
                    priority="High",
                    estimated_score_improvement=3,
                )
            )

        if contact and not contact.linkedin:
            recommendations.append(
                Recommendation(
                    action="Add LinkedIn profile URL",
                    reason="LinkedIn profiles enhance credibility and provide verification",
                    priority="Medium",
                    estimated_score_improvement=2,
                )
            )

        if contact and not contact.github:
            recommendations.append(
                Recommendation(
                    action="Add GitHub profile URL",
                    reason="GitHub shows hands-on experience for technical roles",
                    priority="Medium",
                    estimated_score_improvement=1,
                )
            )

        return recommendations

    def _recommend_summary_improvements(self) -> List[Recommendation]:
        """Generate professional summary recommendations."""
        recommendations = []

        summary_length = len(self.resume.summary or "")
        if summary_length < WEAKNESS_THRESHOLDS["short_summary"]:
            recommendations.append(
                Recommendation(
                    action="Write or expand professional summary to 50-150 words",
                    reason="Professional summary provides context and improves keyword matching for ATS",
                    priority="High",
                    estimated_score_improvement=4,
                )
            )

        return recommendations

    def _recommend_skills_improvements(self) -> List[Recommendation]:
        """Generate skills section recommendations."""
        recommendations = []

        skills_count = len(self.resume.skills or [])
        if skills_count < WEAKNESS_THRESHOLDS["few_skills"]:
            recommendations.append(
                Recommendation(
                    action="Add at least 3-5 more relevant technical or soft skills",
                    reason="More skills improve keyword matching and ATS compatibility",
                    priority="High",
                    estimated_score_improvement=5,
                )
            )

        if skills_count > 0:
            recommendations.append(
                Recommendation(
                    action="Ensure skills are listed separately and match job descriptions",
                    reason="Clear skill listing improves ATS parsing and keyword matching",
                    priority="Medium",
                    estimated_score_improvement=2,
                )
            )

        return recommendations

    def _recommend_experience_improvements(self) -> List[Recommendation]:
        """Generate work experience recommendations."""
        recommendations = []

        if not self.resume.experience or len(self.resume.experience) == 0:
            recommendations.append(
                Recommendation(
                    action="Add work experience section with at least one position",
                    reason="Work experience is critical for ATS scoring and recruiter evaluation",
                    priority="Critical",
                    estimated_score_improvement=20,
                )
            )
            return recommendations

        # Check for quantified achievements
        quant_percentage = self._get_quantified_percentage()
        if quant_percentage < 50:
            recommendations.append(
                Recommendation(
                    action="Add quantified results to job descriptions (e.g., 'Increased sales by 25%')",
                    reason="Quantified achievements make resumes more compelling and ATS-friendly",
                    priority="High",
                    estimated_score_improvement=5,
                )
            )

        # Check for employment gaps
        if self.experience_calc.has_employment_gaps():
            recommendations.append(
                Recommendation(
                    action="Address employment gaps by adding explanations or volunteer work",
                    reason="Employment gaps can raise concerns; address them proactively",
                    priority="Medium",
                    estimated_score_improvement=2,
                )
            )

        # Check for descriptions
        total_exp = len(self.resume.experience)
        exp_with_desc = sum(1 for e in self.resume.experience if e.description)
        if exp_with_desc < total_exp:
            recommendations.append(
                Recommendation(
                    action="Add bullet point descriptions for all work experiences",
                    reason="Descriptions provide context and improve ATS keyword matching",
                    priority="High",
                    estimated_score_improvement=4,
                )
            )

        return recommendations

    def _recommend_education_improvements(self) -> List[Recommendation]:
        """Generate education recommendations."""
        recommendations = []

        if not self.resume.education or len(self.resume.education) == 0:
            recommendations.append(
                Recommendation(
                    action="Add education history (degree, institution, graduation date)",
                    reason="Education is important for ATS filtering in many roles",
                    priority="High",
                    estimated_score_improvement=8,
                )
            )
            return recommendations

        # Check for missing fields
        for edu in self.resume.education:
            if not edu.degree or not edu.field_of_study:
                recommendations.append(
                    Recommendation(
                        action="Include degree type and field of study for all education entries",
                        reason="Complete education details improve ATS parsing",
                        priority="Medium",
                        estimated_score_improvement=2,
                    )
                )
                break

        return recommendations

    def _recommend_projects_improvements(self) -> List[Recommendation]:
        """Generate projects recommendations."""
        recommendations = []

        projects_count = len(self.resume.projects or [])
        if projects_count < WEAKNESS_THRESHOLDS["limited_projects"]:
            recommendations.append(
                Recommendation(
                    action="Add 2-3 portfolio projects with descriptions and links",
                    reason="Projects demonstrate practical skills and portfolio strength for technical roles",
                    priority="Medium",
                    estimated_score_improvement=5,
                )
            )
        elif projects_count > 0:
            recommendations.append(
                Recommendation(
                    action="Ensure projects include technologies used and outcomes",
                    reason="Project details help ATS match with technical requirements",
                    priority="Low",
                    estimated_score_improvement=2,
                )
            )

        return recommendations

    def _recommend_certifications_improvements(self) -> List[Recommendation]:
        """Generate certifications recommendations."""
        recommendations = []

        if not self.resume.certifications or len(self.resume.certifications) == 0:
            if not WEAKNESS_THRESHOLDS.get("no_certifications", True):
                return recommendations

            recommendations.append(
                Recommendation(
                    action="Add relevant professional certifications if applicable",
                    reason="Certifications validate expertise and improve ATS keyword matching",
                    priority="Low",
                    estimated_score_improvement=3,
                )
            )

        return recommendations

    def _recommend_general_improvements(self, current_score: float) -> List[Recommendation]:
        """Generate general recommendations."""
        recommendations = []

        if current_score < 60:
            recommendations.append(
                Recommendation(
                    action="Consider using ATS-friendly resume template and formatting",
                    reason="Clean, simple formatting ensures proper ATS parsing and data extraction",
                    priority="High",
                    estimated_score_improvement=5,
                )
            )

        # Check completeness
        completeness = self.completeness_analyzer.analyze()
        if completeness.overall_completeness < 70:
            recommendations.append(
                Recommendation(
                    action="Fill in missing resume sections for better overall coverage",
                    reason="More complete resumes score better with ATS systems",
                    priority="High",
                    estimated_score_improvement=10,
                )
            )

        return recommendations

    def _get_quantified_percentage(self) -> float:
        """
        Calculate percentage of descriptions with quantified results.

        Returns:
            Percentage 0-100.
        """
        if not self.resume.experience:
            return 0.0

        total = 0
        quantified = 0
        quantified_keywords = {"increased", "reduced", "saved", "grew", "improved", "achieved"}

        for exp in self.resume.experience:
            if exp.description:
                for desc in exp.description:
                    total += 1
                    desc_lower = desc.lower()
                    has_keyword = any(kw in desc_lower for kw in quantified_keywords)
                    has_numbers = any(c.isdigit() for c in desc)
                    if has_keyword and has_numbers:
                        quantified += 1

        if total == 0:
            return 0.0

        return (quantified / total) * 100
