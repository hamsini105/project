"""
Integration tests for the ATS analysis pipeline.

Tests the full flow: Resume → ResumeValidator → ATSScorer →
CompletenessAnalyzer → ExperienceCalculator → ATSAnalyzer.

No external services or ML models are required.
"""

from __future__ import annotations

from datetime import date

import pytest

from parser.models import ContactDetails, EducationEntry, ExperienceEntry, Resume
from ats.analyzer import ATSAnalyzer
from ats.completeness import CompletenessAnalyzer
from ats.experience_calc import ExperienceCalculator
from ats.models import ATSReport
from ats.scorer import ATSScorer
from ats.validators import ResumeValidator


# ── Full pipeline ─────────────────────────────────────────────────────────────

class TestATSAnalyzerFull:
    def test_analyze_returns_ats_report(self, sample_resume):
        analyzer = ATSAnalyzer()
        report   = analyzer.analyze(sample_resume)
        assert isinstance(report, ATSReport)

    def test_overall_score_in_valid_range(self, sample_resume):
        report = ATSAnalyzer().analyze(sample_resume)
        assert 0.0 <= report.overall_score <= 100.0

    def test_rating_is_valid_enum(self, sample_resume):
        report = ATSAnalyzer().analyze(sample_resume)
        assert report.score_rating in ("Excellent", "Good", "Fair", "Poor")

    def test_strengths_populated_for_strong_resume(self, sample_resume):
        report = ATSAnalyzer().analyze(sample_resume)
        assert len(report.strengths) > 0

    def test_json_output_is_serialisable(self, sample_resume):
        import json
        analyzer = ATSAnalyzer()
        data = analyzer.analyze_and_return_json(sample_resume)
        serialised = json.dumps(data, default=str)
        parsed = json.loads(serialised)
        assert "overall_score" in parsed

    def test_minimal_resume_gives_low_score(self, minimal_resume):
        report = ATSAnalyzer().analyze(minimal_resume)
        # A resume with only contact info should score in the poor/fair range
        assert report.overall_score < 60.0


# ── Validator ─────────────────────────────────────────────────────────────────

class TestResumeValidator:
    def test_valid_resume_passes(self, sample_resume):
        validator = ResumeValidator(sample_resume)
        assert validator.validate() is True

    def test_missing_email_raises(self):
        from ats.exceptions import ValidationException
        contact = ContactDetails(full_name="No Email")
        resume  = Resume(contact=contact)
        validator = ResumeValidator(resume)
        with pytest.raises(ValidationException):
            validator.validate()

    def test_gap_detection_returns_list(self, sample_resume):
        validator = ResumeValidator(sample_resume)
        gaps = validator.check_gaps_in_employment()
        assert isinstance(gaps, list)


# ── Scorer ────────────────────────────────────────────────────────────────────

class TestATSScorer:
    def test_score_resume_returns_tuple(self, sample_resume):
        scorer = ATSScorer(sample_resume)
        overall, breakdown = scorer.score_resume()
        assert isinstance(overall, float)
        assert isinstance(breakdown, dict)

    def test_breakdown_has_all_categories(self, sample_resume):
        _, breakdown = ATSScorer(sample_resume).score_resume()
        expected = {
            "contact_details", "professional_summary", "skills",
            "education", "experience", "projects",
            "certifications", "formatting", "keywords",
        }
        assert expected.issubset(set(breakdown.keys()))

    def test_score_with_skills_higher_than_without(self):
        contact = ContactDetails(full_name="Alice", email="a@example.com")
        with_skills    = Resume(contact=contact, skills=["Python", "Django", "PostgreSQL"])
        without_skills = Resume(contact=contact, skills=[])
        s_with,    _ = ATSScorer(with_skills).score_resume()
        s_without, _ = ATSScorer(without_skills).score_resume()
        assert s_with > s_without


# ── Experience calculator ─────────────────────────────────────────────────────

class TestExperienceCalculator:
    def test_total_experience_for_5yr_role(self, sample_resume):
        calc  = ExperienceCalculator(sample_resume)
        years = calc.calculate_total_experience()
        # sample_resume has 2020→now + 2018→2020 ≈ 8 years total
        assert years > 5

    def test_no_experience_returns_zero(self, minimal_resume):
        calc = ExperienceCalculator(minimal_resume)
        assert calc.calculate_total_experience() == 0.0

    @pytest.mark.parametrize("years,expected_level", [
        (0.5,  "Entry"),
        (3.0,  "Junior"),
        (7.0,  "Mid"),
        (12.0, "Senior"),
    ])
    def test_experience_level_mapping(self, minimal_resume, years, expected_level):
        calc = ExperienceCalculator(minimal_resume)
        assert calc.get_experience_level(years) == expected_level
