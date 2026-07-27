"""
Shared pytest fixtures for the Resume Parser System test suite.

Fixtures are organised in groups:
  1. Resume model factories — build Resume, Contact, Experience, Education objects
  2. Job description fixtures — sample JD text and parsed JobDescription
  3. ML mocking — deterministic EmbeddingEngine mock (no sentence-transformers needed in CI)
"""

from __future__ import annotations

from datetime import date
from typing import List
from unittest.mock import MagicMock

import numpy as np
import pytest

from parser.models import (
    ContactDetails,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Resume,
)


# ── Contact & Resume factories ─────────────────────────────────────────────────

@pytest.fixture
def sample_contact() -> ContactDetails:
    return ContactDetails(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1-555-000-1234",
        location="San Francisco, CA",
    )


@pytest.fixture
def sample_resume(sample_contact: ContactDetails) -> Resume:
    """
    A well-populated resume covering all major sections.
    Used as the baseline for tests that need a complete input.
    """
    return Resume(
        contact=sample_contact,
        summary=(
            "Experienced Python engineer with 5+ years building scalable "
            "web services and data pipelines.  Deep expertise in Django, "
            "PostgreSQL, and cloud infrastructure on AWS."
        ),
        skills=["Python", "Django", "PostgreSQL", "Docker", "AWS", "Redis", "Git"],
        education=[
            EducationEntry(
                institution="Massachusetts Institute of Technology",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                end_date=date(2018, 6, 1),
            )
        ],
        experience=[
            ExperienceEntry(
                company="Tech Corp",
                position="Senior Software Engineer",
                start_date=date(2020, 3, 1),
                end_date=None,
                is_current=True,
                description=[
                    "Led migration of monolith to microservices, reducing latency by 40%.",
                    "Owned PostgreSQL schema design and query optimisation.",
                    "Mentored 3 junior engineers.",
                ],
            ),
            ExperienceEntry(
                company="Startup Inc",
                position="Software Engineer",
                start_date=date(2018, 7, 1),
                end_date=date(2020, 2, 28),
                is_current=False,
                description=[
                    "Built Django REST API serving 100k daily active users.",
                    "Integrated Redis caching layer, improving p99 latency by 60%.",
                ],
            ),
        ],
        certifications=None,
        projects=[
            ProjectEntry(
                title="Open Source Data Pipeline",
                description="Apache Airflow DAG library for ETL workflows.",
                technologies=["Python", "Airflow", "PostgreSQL"],
            )
        ],
    )


@pytest.fixture
def minimal_resume(sample_contact: ContactDetails) -> Resume:
    """Bare-minimum resume with only required contact details."""
    return Resume(contact=sample_contact)


# ── Job description fixtures ───────────────────────────────────────────────────

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
def sample_jd_text() -> str:
    return SAMPLE_JD_TEXT


@pytest.fixture
def parsed_jd(sample_jd_text: str):
    """Pre-parsed JobDescription built from SAMPLE_JD_TEXT."""
    from job_matching.jd_parser import JDParser
    return JDParser().parse(sample_jd_text, title="Senior Python Engineer")


# ── Mock embedding engine ──────────────────────────────────────────────────────

@pytest.fixture
def mock_embedding_engine():
    """
    A deterministic mock EmbeddingEngine that returns unit-normalised
    constant vectors without loading sentence-transformers.

    All encoded texts receive the same vector so cosine similarity is
    always 1.0.  Tests that need differentiated similarity should build
    their own per-call side_effect.
    """
    from job_matching.embeddings import EmbeddingEngine

    engine = EmbeddingEngine()
    _dim   = 384
    _unit  = np.ones(_dim, dtype=np.float32) / np.sqrt(_dim)

    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = _dim
    mock_model.encode.side_effect = lambda texts, **kw: (
        _unit.copy()
        if isinstance(texts, str)
        else np.tile(_unit, (len(texts), 1))
    )
    engine._model = mock_model
    return engine

