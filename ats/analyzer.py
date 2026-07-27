"""
Main ATS analyzer that orchestrates the complete analysis pipeline.

Coordinates validation, scoring, analysis, and recommendation generation.
"""

import json
import logging
from pathlib import Path
from typing import Any

from parser.models import Resume

from ats.completeness import CompletenessAnalyzer
from ats.experience_calc import ExperienceCalculator
from ats.exceptions import ATSException
from ats.models import ATSReport, ScoreBreakdown, Strength, Weakness
from ats.recommendations import RecommendationGenerator
from ats.scorer import ATSScorer
from ats.validators import ResumeValidator

logger = logging.getLogger(__name__)


class ATSAnalyzer:
    """
    Production-grade ATS analysis engine.

    Orchestrates the complete analysis pipeline: validation, scoring,
    completeness checking, and recommendation generation.
    """

    def __init__(self) -> None:
        """Initialize ATS analyzer."""
        pass

    def analyze(self, resume: Resume) -> ATSReport:
        """
        Analyze a resume and generate comprehensive ATS report.

        Args:
            resume: Resume object to analyze.

        Returns:
            ATSReport with complete analysis.

        Raises:
            ATSException: If analysis fails.
        """
        try:
            logger.info("Starting ATS analysis")

            # Step 1: Validate resume
            validator = ResumeValidator(resume)
            validator.validate()
            logger.debug("Resume validation passed")

            # Step 2: Score resume
            scorer = ATSScorer(resume)
            overall_score, score_breakdown = scorer.score_resume()
            score_rating = scorer.get_score_rating(overall_score)
            logger.debug(f"Overall ATS score: {overall_score:.1f} ({score_rating})")

            # Step 3: Analyze completeness
            completeness_analyzer = CompletenessAnalyzer(resume)
            completeness_report = completeness_analyzer.analyze()
            logger.debug(f"Completeness: {completeness_report.overall_completeness:.1f}%")

            # Step 4: Calculate experience
            experience_calc = ExperienceCalculator(resume)
            total_experience = experience_calc.calculate_total_experience()
            experience_level = experience_calc.get_experience_level(total_experience)
            logger.debug(f"Experience: {total_experience} years ({experience_level})")

            # Step 5: Identify strengths
            strengths = self._identify_strengths(resume, overall_score, completeness_report)
            logger.debug(f"Identified {len(strengths)} strengths")

            # Step 6: Identify weaknesses
            weaknesses = self._identify_weaknesses(resume, validator, completeness_report)
            logger.debug(f"Identified {len(weaknesses)} weaknesses")

            # Step 7: Get missing sections
            missing_sections = completeness_analyzer.get_missing_sections()
            logger.debug(f"Missing sections: {missing_sections}")

            # Step 8: Generate recommendations
            rec_generator = RecommendationGenerator(resume)
            recommendations = rec_generator.generate_recommendations(overall_score)
            logger.debug(f"Generated {len(recommendations)} recommendations")

            # Step 9: Build score breakdown model
            score_breakdown_model = ScoreBreakdown(**score_breakdown)

            # Step 10: Create and return report
            report = ATSReport(
                overall_score=overall_score,
                score_rating=score_rating,
                score_breakdown=score_breakdown_model,
                completeness_percentage=completeness_report.overall_completeness,
                experience_years=total_experience,
                experience_level=experience_level,
                strengths=strengths,
                weaknesses=weaknesses,
                missing_sections=missing_sections,
                recommendations=recommendations,
                analysis_metadata={
                    "sections_count": self._count_resume_sections(resume),
                    "skills_diversity": len(set(resume.skills or [])),
                    "employment_gaps_detected": experience_calc.has_employment_gaps(),
                    "role_diversity": experience_calc.get_role_diversity(),
                    "company_diversity": experience_calc.get_company_diversity(),
                    "employment_stability": experience_calc.get_employment_stability(),
                },
            )

            logger.info(f"ATS analysis completed. Final score: {overall_score:.1f}")
            return report

        except ATSException:
            raise
        except Exception as e:
            msg = f"Unexpected error during ATS analysis: {e}"
            logger.error(msg, exc_info=True)
            raise ATSException(msg) from e

    def analyze_and_return_json(self, resume: Resume) -> dict[str, Any]:
        """
        Analyze resume and return results as JSON-serializable dict.

        Args:
            resume: Resume object to analyze.

        Returns:
            Dictionary representation of ATSReport.
        """
        report = self.analyze(resume)
        return report.model_dump_clean()

    def analyze_and_save_json(self, resume: Resume, output_path: str | Path) -> None:
        """
        Analyze resume and save report as JSON file.

        Args:
            resume: Resume object to analyze.
            output_path: Path where JSON report should be saved.
        """
        report_data = self.analyze_and_return_json(resume)
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"ATS report saved to: {output_path}")

    def _identify_strengths(
        self, resume: Resume, overall_score: float, completeness_report: Any
    ) -> list[Strength]:
        """
        Identify strengths in the resume.

        Args:
            resume: Resume object.
            overall_score: Overall ATS score.
            completeness_report: Completeness analysis report.

        Returns:
            List of identified strengths.
        """
        strengths = []

        # Strong contact details
        if completeness_report.contact_details_complete:
            strengths.append(
                Strength(
                    category="contact_details",
                    description="Complete and professional contact information",
                    impact="High",
                )
            )

        # Strong skills section
        if completeness_report.skills_count >= 10:
            strengths.append(
                Strength(
                    category="skills",
                    description=f"Comprehensive skills section with {completeness_report.skills_count}+ technologies",
                    impact="High",
                )
            )

        # Strong experience
        if completeness_report.experience_count >= 3:
            strengths.append(
                Strength(
                    category="experience",
                    description=f"Solid work history with {completeness_report.experience_count} positions",
                    impact="High",
                )
            )

        # Good education
        if completeness_report.education_present and completeness_report.education_count >= 1:
            strengths.append(
                Strength(
                    category="education",
                    description="Education history clearly documented",
                    impact="Medium",
                )
            )

        # Portfolio projects
        if completeness_report.projects_present and completeness_report.projects_count >= 2:
            strengths.append(
                Strength(
                    category="projects",
                    description=f"Portfolio with {completeness_report.projects_count} projects",
                    impact="Medium",
                )
            )

        # Certifications
        if completeness_report.certifications_present:
            strengths.append(
                Strength(
                    category="certifications",
                    description="Professional certifications demonstrating expertise",
                    impact="Medium",
                )
            )

        # Professional summary
        if completeness_report.professional_summary_present:
            strengths.append(
                Strength(
                    category="professional_summary",
                    description="Professional summary provides context",
                    impact="Medium",
                )
            )

        # High overall score
        if overall_score >= 80:
            strengths.append(
                Strength(
                    category="overall_quality",
                    description="Overall resume quality is excellent",
                    impact="High",
                )
            )

        return strengths

    def _identify_weaknesses(
        self, resume: Resume, validator: ResumeValidator, completeness_report: Any
    ) -> list[Weakness]:
        """
        Identify weaknesses in the resume.

        Args:
            resume: Resume object.
            validator: ResumeValidator instance.
            completeness_report: Completeness analysis report.

        Returns:
            List of identified weaknesses.
        """
        weaknesses = []

        # Missing contact details
        if not completeness_report.contact_details_complete:
            for field in completeness_report.contact_details_missing_fields:
                weaknesses.append(
                    Weakness(
                        category="contact_details",
                        description=f"Missing {field}",
                        severity="Critical",
                    )
                )

        # Missing professional summary
        if not completeness_report.professional_summary_present:
            weaknesses.append(
                Weakness(
                    category="professional_summary",
                    description="No professional summary provided",
                    severity="Medium",
                )
            )

        # Few skills
        if completeness_report.skills_count < 5:
            weaknesses.append(
                Weakness(
                    category="skills",
                    description=f"Only {completeness_report.skills_count} skills listed",
                    severity="High",
                )
            )

        # No projects
        if not completeness_report.projects_present:
            weaknesses.append(
                Weakness(
                    category="projects",
                    description="No projects or portfolio items",
                    severity="Medium",
                )
            )

        # No certifications
        if not completeness_report.certifications_present:
            weaknesses.append(
                Weakness(
                    category="certifications",
                    description="No professional certifications",
                    severity="Low",
                )
            )

        # Employment gaps
        gaps = validator.check_gaps_in_employment()
        for gap_desc, severity, gap_years in gaps:
            weaknesses.append(
                Weakness(
                    category="employment_history",
                    description=f"Employment gap: {gap_desc}",
                    severity=severity,
                )
            )

        # Text quality issues
        text_issues = validator.check_text_quality()
        weaknesses.extend(text_issues)

        return weaknesses

    def _count_resume_sections(self, resume: Resume) -> dict[str, int]:
        """
        Count items in each resume section.

        Args:
            resume: Resume object.

        Returns:
            Dictionary with section counts.
        """
        return {
            "skills": len(resume.skills or []),
            "education": len(resume.education or []),
            "experience": len(resume.experience or []),
            "projects": len(resume.projects or []),
            "certifications": len(resume.certifications or []),
        }
