"""
Unit tests for the ATS analysis engine.

Tests individual components and integration scenarios.
"""

from datetime import date
from unittest.mock import Mock

import pytest

from parser.models import (
    ContactDetails,
    EducationEntry,
    ExperienceEntry,
    Resume,
)

from ats.analyzer import ATSAnalyzer
from ats.completeness import CompletenessAnalyzer
from ats.exceptions import ValidationException, ScoringException
from ats.experience_calc import ExperienceCalculator
from ats.models import ATSReport
from ats.recommendations import RecommendationGenerator
from ats.scorer import ATSScorer
from ats.validators import ResumeValidator


class TestResumeValidator:
    """Tests for resume validation."""

    def test_validate_with_complete_contact(self):
        """Test validation with complete contact details."""
        contact = ContactDetails(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
        )
        resume = Resume(contact=contact)
        validator = ResumeValidator(resume)

        assert validator.validate() is True

    def test_validate_missing_email(self):
        """Test validation fails with missing email."""
        contact = ContactDetails(
            full_name="John Doe",
            phone="+1-555-123-4567",
        )
        resume = Resume(contact=contact)
        validator = ResumeValidator(resume)

        with pytest.raises(ValidationException):
            validator.validate()

    def test_validate_no_contact(self):
        """Test validation fails with no contact details."""
        resume = Resume(contact=None)
        validator = ResumeValidator(resume)

        with pytest.raises(ValidationException):
            validator.validate()

    def test_check_employment_gaps(self):
        """Test employment gap detection."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        exp1 = ExperienceEntry(
            company="Company A",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 6, 1),
        )
        exp2 = ExperienceEntry(
            company="Company B",
            position="Senior Developer",
            start_date=date(2023, 1, 1),
            end_date=None,
            is_current=True,
        )
        resume = Resume(
            contact=contact,
            experience=[exp1, exp2],
        )
        validator = ResumeValidator(resume)
        gaps = validator.check_gaps_in_employment()

        # Should detect 1.5+ year gap
        assert len(gaps) > 0


class TestExperienceCalculator:
    """Tests for experience calculation."""

    def test_calculate_total_experience(self):
        """Test total experience calculation."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        exp = ExperienceEntry(
            company="Company A",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 1, 1),
        )
        resume = Resume(contact=contact, experience=[exp])
        calc = ExperienceCalculator(resume)

        years = calc.calculate_total_experience()
        assert 2.9 < years < 3.1  # Approximately 3 years

    def test_get_experience_level(self):
        """Test experience level categorization."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        resume = Resume(contact=contact)
        calc = ExperienceCalculator(resume)

        # Test different experience levels
        assert calc.get_experience_level(1) == "Junior"
        assert calc.get_experience_level(5) == "Mid"
        assert calc.get_experience_level(12) == "Senior"
        assert calc.get_experience_level(20) == "Executive"

    def test_has_employment_gaps(self):
        """Test employment gap detection."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        exp1 = ExperienceEntry(
            company="Company A",
            position="Developer",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
        )
        exp2 = ExperienceEntry(
            company="Company B",
            position="Developer",
            start_date=date(2023, 1, 1),
            end_date=None,
            is_current=True,
        )
        resume = Resume(contact=contact, experience=[exp1, exp2])
        calc = ExperienceCalculator(resume)

        assert calc.has_employment_gaps() is True


class TestATSScorer:
    """Tests for ATS scoring engine."""

    def test_score_complete_resume(self):
        """Test scoring of complete resume."""
        contact = ContactDetails(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
            linkedin="https://linkedin.com/in/johndoe",
        )
        resume = Resume(
            contact=contact,
            summary="Experienced software engineer with 5+ years",
            skills=["Python", "Django", "PostgreSQL", "React", "Docker"],
            education=[
                EducationEntry(
                    institution="MIT",
                    degree="Bachelor",
                    field_of_study="Computer Science",
                )
            ],
            experience=[
                ExperienceEntry(
                    company="Tech Corp",
                    position="Senior Engineer",
                    start_date=date(2020, 1, 1),
                    end_date=None,
                    is_current=True,
                )
            ],
        )
        scorer = ATSScorer(resume)
        overall_score, breakdown = scorer.score_resume()

        assert 50 <= overall_score <= 100
        assert "contact_details" in breakdown
        assert "skills" in breakdown
        assert breakdown["contact_details"] > 0

    def test_score_empty_resume(self):
        """Test scoring of minimal resume."""
        contact = ContactDetails(
            full_name="Jane Doe",
            email="jane@example.com",
        )
        resume = Resume(contact=contact)
        scorer = ATSScorer(resume)
        overall_score, breakdown = scorer.score_resume()

        assert 0 <= overall_score <= 100
        assert breakdown["contact_details"] > 0
        assert breakdown["experience"] == 0

    def test_score_rating(self):
        """Test score rating categorization."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        resume = Resume(contact=contact)
        scorer = ATSScorer(resume)

        assert scorer.get_score_rating(90) == "Excellent"
        assert scorer.get_score_rating(75) == "Good"
        assert scorer.get_score_rating(65) == "Fair"
        assert scorer.get_score_rating(45) == "Poor"


class TestCompletenessAnalyzer:
    """Tests for completeness analysis."""

    def test_analyze_complete_resume(self):
        """Test completeness of full resume."""
        contact = ContactDetails(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
        )
        resume = Resume(
            contact=contact,
            summary="Professional summary",
            skills=["Python", "Java"],
            education=[
                EducationEntry(
                    institution="University",
                    degree="Bachelor",
                )
            ],
            experience=[
                ExperienceEntry(
                    company="Company",
                    position="Developer",
                )
            ],
        )
        analyzer = CompletenessAnalyzer(resume)
        report = analyzer.analyze()

        assert report.contact_details_complete is True
        assert report.skills_present is True
        assert report.education_present is True
        assert report.overall_completeness > 70

    def test_analyze_incomplete_resume(self):
        """Test completeness of minimal resume."""
        contact = ContactDetails(
            full_name="Jane Doe",
            email="jane@example.com",
        )
        resume = Resume(contact=contact)
        analyzer = CompletenessAnalyzer(resume)
        report = analyzer.analyze()

        assert report.contact_details_complete is True
        assert report.skills_present is False
        assert report.overall_completeness < 50

    def test_missing_sections(self):
        """Test missing sections detection."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        resume = Resume(contact=contact)
        analyzer = CompletenessAnalyzer(resume)
        missing = analyzer.get_missing_sections()

        assert "Skills" in missing
        assert "Work Experience" in missing


class TestRecommendationGenerator:
    """Tests for recommendation generation."""

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        contact = ContactDetails(
            full_name="John Doe", email="john@example.com"
        )
        resume = Resume(contact=contact)
        gen = RecommendationGenerator(resume)
        recs = gen.generate_recommendations(50)

        assert len(recs) > 0
        assert any(r.priority == "Critical" for r in recs)

    def test_recommendations_sorted_by_priority(self):
        """Test recommendations are sorted by priority."""
        contact = ContactDetails(
            full_name="Jane Doe", email="jane@example.com"
        )
        resume = Resume(contact=contact)
        gen = RecommendationGenerator(resume)
        recs = gen.generate_recommendations(40)

        # First recommendation should be Critical or High
        if recs:
            assert recs[0].priority in ["Critical", "High"]


class TestATSAnalyzer:
    """Tests for main ATS analyzer."""

    def test_analyze_complete_resume(self):
        """Test full ATS analysis."""
        contact = ContactDetails(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
        )
        resume = Resume(
            contact=contact,
            summary="Software engineer",
            skills=["Python", "Java", "Go"],
            education=[
                EducationEntry(
                    institution="MIT",
                    degree="Bachelor",
                )
            ],
            experience=[
                ExperienceEntry(
                    company="Tech Corp",
                    position="Engineer",
                    start_date=date(2020, 1, 1),
                    end_date=None,
                    is_current=True,
                )
            ],
        )
        analyzer = ATSAnalyzer()
        report = analyzer.analyze(resume)

        assert isinstance(report, ATSReport)
        assert 0 <= report.overall_score <= 100
        assert report.score_rating in ["Excellent", "Good", "Fair", "Poor"]
        assert report.experience_years >= 0
        assert len(report.strengths) > 0

    def test_analyze_and_json(self):
        """Test JSON output."""
        contact = ContactDetails(
            full_name="Jane Doe", email="jane@example.com"
        )
        resume = Resume(contact=contact, skills=["Python"])
        analyzer = ATSAnalyzer()
        json_data = analyzer.analyze_and_return_json(resume)

        assert isinstance(json_data, dict)
        assert "overall_score" in json_data
        assert "score_rating" in json_data
        assert "strengths" in json_data


if __name__ == "__main__":
    print("Running ATS Analysis Tests...")
    print("=" * 60)

    # Run tests manually
    print("\n✓ Testing ResumeValidator...")
    test_validator = TestResumeValidator()
    test_validator.test_validate_with_complete_contact()
    print("  - Complete contact validation passed")

    print("\n✓ Testing ExperienceCalculator...")
    test_exp = TestExperienceCalculator()
    test_exp.test_calculate_total_experience()
    print("  - Experience calculation passed")

    print("\n✓ Testing ATSScorer...")
    test_scorer = TestATSScorer()
    test_scorer.test_score_complete_resume()
    print("  - Score calculation passed")

    print("\n✓ Testing CompletenessAnalyzer...")
    test_completeness = TestCompletenessAnalyzer()
    test_completeness.test_analyze_complete_resume()
    print("  - Completeness analysis passed")

    print("\n✓ Testing RecommendationGenerator...")
    test_rec = TestRecommendationGenerator()
    test_rec.test_generate_recommendations()
    print("  - Recommendation generation passed")

    print("\n✓ Testing ATSAnalyzer...")
    test_ats = TestATSAnalyzer()
    test_ats.test_analyze_complete_resume()
    print("  - Full ATS analysis passed")

    print("\n" + "=" * 60)
    print("All tests passed!")
