"""Unit tests for job_matching.jd_parser.JDParser."""

from __future__ import annotations

import pytest

from job_matching.jd_parser import JDParser
from job_matching.models import JobDescription


SAMPLE_JD_TEXT = """\
Senior Python Engineer

About the Role
We are building the next generation of data infrastructure and are looking
for an experienced Python engineer to join our core platform team.

Requirements
- 5+ years of professional software development experience
- Strong proficiency in Python and Django
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
- Bachelor's degree in Computer Science or equivalent

Preferred
- Experience with AWS (EC2, RDS, S3)
- Knowledge of machine learning workflows
- Open source contributions

Responsibilities
- Design and implement scalable backend services
- Collaborate with cross-functional product and data science teams
- Own the PostgreSQL performance optimisation roadmap
- Participate in code review and technical mentoring
"""

SPARSE_JD_TEXT = "Seeking a Python developer with experience in web development."


@pytest.fixture
def parser() -> JDParser:
    return JDParser()


class TestParseReturnsCorrectTypes:
    def test_returns_job_description(self, parser):
        sparse_jd = "Seeking a Python developer with experience in web development."
        jd = parser.parse(sparse_jd, title="Senior Python Engineer")
        assert isinstance(jd, JobDescription)

    def test_uses_provided_title(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT, title="Senior Python Engineer")
        assert jd.title == "Senior Python Engineer"

    def test_uses_provided_company(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT, title="SWE", company="Acme Corp")
        assert jd.company == "Acme Corp"

    def test_stores_raw_text(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        assert jd.raw_text == SAMPLE_JD_TEXT


class TestSkillExtraction:
    def test_extracts_required_skills(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        lower = [s.lower() for s in jd.required_skills]
        assert "python" in lower
        assert "django" in lower
        assert "postgresql" in lower

    def test_extracts_preferred_skills(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        lower = [s.lower() for s in jd.preferred_skills]
        assert "aws" in lower or "machine learning" in lower

    def test_all_skills_deduplicated(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        assert len(jd.all_skills) == len(set(jd.all_skills))

    def test_sparse_jd_still_extracts_skills(self, parser):
        jd = parser.parse(SPARSE_JD_TEXT)
        assert len(jd.required_skills) > 0


class TestExperienceExtraction:
    def test_extracts_minimum_years(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        assert jd.min_experience_years == 5.0

    def test_no_experience_requirement_returns_none(self, parser):
        jd = parser.parse(SPARSE_JD_TEXT)
        assert jd.min_experience_years is None

    @pytest.mark.parametrize("text,expected_min", [
        ("Requires 3+ years of experience", 3.0),
        ("Minimum 7 years of relevant experience", 7.0),
        ("At least 2 years experience", 2.0),
    ])
    def test_various_experience_phrasings(self, parser, text: str, expected_min: float):
        jd = parser.parse(text)
        assert jd.min_experience_years == expected_min


class TestEducationExtraction:
    def test_extracts_bachelor_level(self, parser):
        jd = parser.parse(SAMPLE_JD_TEXT)
        assert jd.education_level == "bachelor"

    def test_no_education_returns_none(self, parser):
        jd = parser.parse(SPARSE_JD_TEXT)
        assert jd.education_level is None

    @pytest.mark.parametrize("text,level", [
        ("Requires Master's degree",  "master"),
        ("PhD or equivalent required", "phd"),
    ])
    def test_various_education_levels(self, parser, text: str, level: str):
        jd = parser.parse(text)
        assert jd.education_level == level


class TestErrorHandling:
    def test_empty_text_raises(self, parser):
        from job_matching.exceptions import JDParsingException
        with pytest.raises(JDParsingException):
            parser.parse("")

    def test_whitespace_only_raises(self, parser):
        from job_matching.exceptions import JDParsingException
        with pytest.raises(JDParsingException):
            parser.parse("   \n\t  ")

    def test_sparse_jd_still_extracts_skills(self, parser):
        sparse = "Seeking a Python developer with experience in web development."
        jd = parser.parse(sparse)
        assert len(jd.required_skills) > 0
