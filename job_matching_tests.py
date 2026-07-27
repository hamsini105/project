"""
Unit and integration tests for the Job Matching module.

Each test class targets a single module so failures are easy to localise.
The test suite is intentionally self-contained — no real resume files or
network calls are required.  The embedding engine is mocked in unit tests
so sentence-transformers is not required to run the fast suite.

Run:
    pytest job_matching_tests.py -v
    pytest job_matching_tests.py -v -m "not slow"   # skip embedding tests
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from parser.models import (
    CertificationEntry,
    ContactDetails,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Resume,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_JD_TEXT = """
Senior Python Engineer

About the Role
We are looking for an experienced Python engineer to join our team.

Requirements
- 5+ years of experience in software development
- Strong proficiency in Python, Django, PostgreSQL
- Experience with Docker and Kubernetes
- Bachelor's degree in Computer Science or related field
- Familiarity with REST API design

Preferred
- Experience with AWS or GCP
- Knowledge of machine learning frameworks
- React frontend development experience

Responsibilities
- Design and implement backend services
- Write clean, testable code
- Collaborate with cross-functional teams
"""

SPARSE_JD_TEXT = "Looking for a developer with Python and Git experience."


def _make_contact(**kwargs) -> ContactDetails:
    defaults = {"full_name": "Jane Doe", "email": "jane@example.com"}
    defaults.update(kwargs)
    return ContactDetails(**defaults)


def _make_resume(
    name: str = "Jane Doe",
    skills: List[str] | None = None,
    experience_years: float = 5,
    has_summary: bool = True,
    education_degree: str = "Bachelor of Science",
) -> Resume:
    """Construct a Resume fixture with configurable properties."""
    start = date(int(date.today().year - experience_years), 1, 1)
    contact = _make_contact(full_name=name)

    exp = ExperienceEntry(
        company="Acme Corp",
        position="Software Engineer",
        start_date=start,
        end_date=None,
        is_current=True,
        description=["Developed Python microservices", "Maintained PostgreSQL database"],
    )
    edu = EducationEntry(
        institution="State University",
        degree=education_degree,
        field_of_study="Computer Science",
    )

    return Resume(
        contact=contact,
        summary="Experienced Python engineer with Django and PostgreSQL skills." if has_summary else None,
        skills=skills or ["Python", "Django", "PostgreSQL", "Docker", "Git"],
        experience=[exp],
        education=[edu],
    )


# ── JDParser Tests ─────────────────────────────────────────────────────────────

class TestJDParser:
    """Tests for job_matching.jd_parser.JDParser."""

    def setup_method(self):
        from job_matching.jd_parser import JDParser
        self.parser = JDParser()

    def test_parse_returns_job_description(self):
        from job_matching.models import JobDescription
        jd = self.parser.parse(SAMPLE_JD_TEXT, title="Senior Python Engineer")
        assert isinstance(jd, JobDescription)

    def test_parse_extracts_title(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT, title="Senior Python Engineer")
        assert jd.title == "Senior Python Engineer"

    def test_parse_extracts_required_skills(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        skill_names_lower = [s.lower() for s in jd.required_skills]
        assert "python" in skill_names_lower
        assert "django" in skill_names_lower
        assert "postgresql" in skill_names_lower

    def test_parse_extracts_preferred_skills(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        skill_names_lower = [s.lower() for s in jd.preferred_skills]
        assert "aws" in skill_names_lower or "machine learning" in skill_names_lower

    def test_parse_extracts_experience_years(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        assert jd.min_experience_years == 5.0

    def test_parse_extracts_education_level(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        assert jd.education_level == "bachelor"

    def test_parse_empty_text_raises(self):
        from job_matching.exceptions import JDParsingException
        with pytest.raises(JDParsingException):
            self.parser.parse("")

    def test_parse_whitespace_only_raises(self):
        from job_matching.exceptions import JDParsingException
        with pytest.raises(JDParsingException):
            self.parser.parse("   \n\t  ")

    def test_parse_sparse_jd_falls_back_gracefully(self):
        jd = self.parser.parse(SPARSE_JD_TEXT)
        assert jd.required_skills  # at least some skills found
        assert jd.min_experience_years is None

    def test_parse_stores_raw_text(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        assert jd.raw_text == SAMPLE_JD_TEXT

    def test_all_skills_property_deduplicates(self):
        jd = self.parser.parse(SAMPLE_JD_TEXT)
        assert len(jd.all_skills) == len(set(jd.all_skills))

    def test_parse_with_company_and_location(self):
        jd = self.parser.parse(
            SAMPLE_JD_TEXT, title="SWE", company="Acme", location="Remote"
        )
        assert jd.company == "Acme"
        assert jd.location == "Remote"


# ── SkillNormalizer Tests ─────────────────────────────────────────────────────

class TestSkillNormalizer:
    """Tests for job_matching.normalizer.SkillNormalizer."""

    def setup_method(self):
        from job_matching.normalizer import SkillNormalizer
        self.norm = SkillNormalizer()

    def test_lowercases_skill(self):
        assert self.norm.normalize("Python") == "python"

    def test_resolves_alias_js(self):
        assert self.norm.normalize("JS") == "javascript"

    def test_resolves_alias_k8s(self):
        assert self.norm.normalize("k8s") == "kubernetes"

    def test_resolves_alias_golang(self):
        assert self.norm.normalize("golang") == "go"

    def test_strips_quotes(self):
        assert self.norm.normalize('"Python"') == "python"

    def test_collapses_whitespace(self):
        assert self.norm.normalize("machine  learning") == "machine learning"

    def test_empty_string_returns_empty(self):
        assert self.norm.normalize("") == ""

    def test_non_string_raises(self):
        from job_matching.exceptions import NormalizationException
        with pytest.raises(NormalizationException):
            self.norm.normalize(123)  # type: ignore

    def test_normalize_list_deduplicates(self):
        result = self.norm.normalize_list(["Python", "python", "PYTHON"])
        assert result == ["python"]

    def test_normalize_list_preserves_order(self):
        result = self.norm.normalize_list(["django", "python", "postgresql"])
        assert result.index("django") < result.index("python") < result.index("postgresql")

    def test_normalize_list_skips_bad_entries(self):
        # Non-strings in list should be skipped with a warning, not crash
        result = self.norm.normalize_list(["python", None, "django"])  # type: ignore
        assert "python" in result
        assert "django" in result


# ── EmbeddingEngine Tests (mocked) ───────────────────────────────────────────

class TestEmbeddingEngine:
    """Tests for job_matching.embeddings.EmbeddingEngine (model is mocked)."""

    def _build_engine_with_mock(self):
        from job_matching.embeddings import EmbeddingEngine
        engine = EmbeddingEngine()
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.side_effect = lambda texts, **kw: (
            np.random.rand(384).astype(np.float32)
            if isinstance(texts, str)
            else np.random.rand(len(texts), 384).astype(np.float32)
        )
        engine._model = mock_model
        return engine

    def test_encode_returns_array(self):
        engine = self._build_engine_with_mock()
        vec = engine.encode("Senior Python Engineer")
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (384,)

    def test_encode_empty_string_returns_zeros(self):
        engine = self._build_engine_with_mock()
        vec = engine.encode("")
        assert np.all(vec == 0)

    def test_encode_caches_result(self):
        engine = self._build_engine_with_mock()
        v1 = engine.encode("Python engineer")
        v2 = engine.encode("Python engineer")
        # Same object (from cache)
        assert v1 is v2

    def test_encode_batch_returns_list(self):
        engine = self._build_engine_with_mock()
        texts = ["Python", "Django", "PostgreSQL"]
        vecs  = engine.encode_batch(texts)
        assert len(vecs) == 3
        assert all(isinstance(v, np.ndarray) for v in vecs)


class TestCosineSimilarity:
    """Tests for job_matching.embeddings.cosine_similarity."""

    def test_identical_vectors_return_one(self):
        from job_matching.embeddings import cosine_similarity
        v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self):
        from job_matching.embeddings import cosine_similarity
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector_returns_zero(self):
        from job_matching.embeddings import cosine_similarity
        a = np.zeros(4, dtype=np.float32)
        b = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        assert cosine_similarity(a, b) == 0.0

    def test_result_clamped_to_unit_interval(self):
        from job_matching.embeddings import cosine_similarity
        a = np.array([1.0, 1.0], dtype=np.float32)
        b = np.array([1.0, 1.0], dtype=np.float32)
        result = cosine_similarity(a, b)
        assert 0.0 <= result <= 1.0


# ── SimilarityCalculator Tests ────────────────────────────────────────────────

class TestSimilarityCalculator:
    """Tests for job_matching.similarity.SimilarityCalculator (engine mocked)."""

    def _make_calculator(self):
        from job_matching.embeddings import EmbeddingEngine
        from job_matching.similarity import SimilarityCalculator

        engine = EmbeddingEngine()
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        # Return reproducible embeddings
        mock_model.encode.side_effect = lambda texts, **kw: (
            np.ones(384, dtype=np.float32) / np.sqrt(384)
            if isinstance(texts, str)
            else np.tile(
                np.ones(384, dtype=np.float32) / np.sqrt(384),
                (len(texts), 1),
            )
        )
        engine._model = mock_model
        return SimilarityCalculator(engine)

    def test_compute_returns_tuple_of_four(self):
        from job_matching.jd_parser import JDParser
        from job_matching.normalizer import SkillNormalizer

        calc    = self._make_calculator()
        jd      = JDParser().parse(SAMPLE_JD_TEXT, title="SE")
        resume  = _make_resume()
        norm    = SkillNormalizer()

        result = calc.compute(
            resume, jd,
            resume_skills_normalised=norm.normalize_list(resume.skills or []),
            jd_required_normalised=norm.normalize_list(jd.required_skills),
            jd_preferred_normalised=norm.normalize_list(jd.preferred_skills),
        )
        overall, breakdown, req_matches, pref_matches = result
        assert 0.0 <= overall <= 100.0
        assert 0.0 <= breakdown.skills_match <= 100.0

    def test_no_jd_skills_gives_full_skills_score(self):
        from job_matching.jd_parser import JDParser
        from job_matching.normalizer import SkillNormalizer
        from job_matching.models import JobDescription

        calc   = self._make_calculator()
        norm   = SkillNormalizer()
        resume = _make_resume()
        jd = JobDescription(
            title="Any Role",
            raw_text="We're hiring.",
            required_skills=[],
            preferred_skills=[],
        )
        overall, breakdown, req_matches, pref_matches = calc.compute(
            resume, jd,
            resume_skills_normalised=norm.normalize_list(resume.skills or []),
            jd_required_normalised=[],
            jd_preferred_normalised=[],
        )
        assert breakdown.skills_match == 100.0


# ── MatchExplainer Tests ──────────────────────────────────────────────────────

class TestMatchExplainer:
    """Tests for job_matching.explainer.MatchExplainer."""

    def setup_method(self):
        from job_matching.explainer import MatchExplainer
        self.explainer = MatchExplainer()

    def test_get_match_rating_excellent(self):
        from job_matching.models import MatchRating
        assert self.explainer.get_match_rating(90.0) == MatchRating.EXCELLENT

    def test_get_match_rating_good(self):
        from job_matching.models import MatchRating
        assert self.explainer.get_match_rating(75.0) == MatchRating.GOOD

    def test_get_match_rating_fair(self):
        from job_matching.models import MatchRating
        assert self.explainer.get_match_rating(55.0) == MatchRating.FAIR

    def test_get_match_rating_poor(self):
        from job_matching.models import MatchRating
        assert self.explainer.get_match_rating(30.0) == MatchRating.POOR

    def test_get_missing_skills_returns_unmatched(self):
        from job_matching.models import MatchType, SkillMatch
        jd_skills = ["python", "django", "kubernetes"]
        matched   = [
            SkillMatch(jd_skill="python",  resume_skill="python",  match_type=MatchType.EXACT, confidence=1.0),
            SkillMatch(jd_skill="django",  resume_skill="django",  match_type=MatchType.EXACT, confidence=1.0),
        ]
        missing = self.explainer.get_missing_skills(jd_skills, matched)
        assert missing == ["kubernetes"]

    def test_get_extra_skills_excludes_jd_skills(self):
        resume_skills = ["python", "django", "rust"]
        jd_skills     = ["python", "django"]
        extra = self.explainer.get_extra_skills(resume_skills, jd_skills)
        assert extra == ["rust"]

    def test_experience_gap_returns_none_when_met(self):
        from job_matching.models import JobDescription
        resume = _make_resume(experience_years=6)
        jd     = JobDescription(
            title="SE", raw_text="need 5 years",
            min_experience_years=5,
        )
        assert self.explainer.experience_gap_narrative(resume, jd) is None

    def test_experience_gap_returns_string_when_short(self):
        from job_matching.models import JobDescription
        resume = _make_resume(experience_years=2)
        jd     = JobDescription(
            title="SE", raw_text="need 5 years",
            min_experience_years=5,
        )
        gap = self.explainer.experience_gap_narrative(resume, jd)
        assert gap is not None
        assert "gap" in gap.lower()

    def test_recommendations_sorted_by_priority(self):
        from job_matching.models import JobDescription, ScoreBreakdown
        resume = _make_resume(skills=["python"])
        jd = JobDescription(
            title="SE", raw_text=SAMPLE_JD_TEXT,
            required_skills=["python", "django", "kubernetes", "docker", "aws"],
            preferred_skills=["terraform"],
            min_experience_years=8,
        )
        breakdown = ScoreBreakdown(
            skills_match=40, semantic_similarity=45,
            experience_match=20, education_match=60,
        )
        recs = self.explainer.generate_recommendations(
            resume, jd,
            missing_required=["django", "kubernetes", "docker", "aws"],
            missing_preferred=["terraform"],
            experience_gap_text="Gap of 5 years",
            education_gap_text=None,
            overall_score=42.0,
            score_breakdown=breakdown,
        )
        assert len(recs) > 0
        # Critical before High before Medium
        priorities = [r.priority.value for r in recs]
        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        assert all(
            order[priorities[i]] <= order[priorities[i + 1]]
            for i in range(len(priorities) - 1)
        )


# ── CandidateRanker Tests ─────────────────────────────────────────────────────

class TestCandidateRanker:
    """Tests for job_matching.ranker.CandidateRanker."""

    def setup_method(self):
        from job_matching.ranker import CandidateRanker
        self.ranker = CandidateRanker()

    def _make_match_result(self, score: float) -> "MatchResult":
        from job_matching.models import MatchRating, MatchResult, ScoreBreakdown
        return MatchResult(
            overall_score=score,
            match_rating=MatchRating.GOOD,
            score_breakdown=ScoreBreakdown(
                skills_match=score, semantic_similarity=score,
                experience_match=score, education_match=score,
            ),
        )

    def _make_jd(self) -> "JobDescription":
        from job_matching.models import JobDescription
        return JobDescription(title="SWE", raw_text="Hiring Python devs.")

    def test_rank_sorts_descending(self):
        candidates = [
            (_make_resume("Alice"), self._make_match_result(60.0)),
            (_make_resume("Bob"),   self._make_match_result(80.0)),
            (_make_resume("Carol"), self._make_match_result(70.0)),
        ]
        result = self.ranker.rank(candidates, self._make_jd())
        scores = [c.overall_score for c in result.ranked_candidates]
        assert scores == sorted(scores, reverse=True)

    def test_rank_assigns_correct_ranks(self):
        candidates = [
            (_make_resume("A"), self._make_match_result(50.0)),
            (_make_resume("B"), self._make_match_result(90.0)),
        ]
        result = self.ranker.rank(candidates, self._make_jd())
        assert result.ranked_candidates[0].rank == 1
        assert result.ranked_candidates[1].rank == 2

    def test_rank_empty_raises(self):
        from job_matching.exceptions import RankingException
        with pytest.raises(RankingException):
            self.ranker.rank([], self._make_jd())

    def test_rank_ties_broken_by_name(self):
        candidates = [
            (_make_resume("Zara"),  self._make_match_result(75.0)),
            (_make_resume("Alice"), self._make_match_result(75.0)),
        ]
        result = self.ranker.rank(candidates, self._make_jd())
        assert result.ranked_candidates[0].candidate_name == "Alice"

    def test_top_n_helper(self):
        from job_matching.ranker import CandidateRanker
        candidates = [
            (_make_resume(f"Candidate {i}"), self._make_match_result(float(i * 10)))
            for i in range(5)
        ]
        result = self.ranker.rank(candidates, self._make_jd())
        top2   = CandidateRanker.top_n(result, 2)
        assert len(top2) == 2

    def test_total_candidates_count(self):
        candidates = [
            (_make_resume(f"C{i}"), self._make_match_result(50.0)) for i in range(3)
        ]
        result = self.ranker.rank(candidates, self._make_jd())
        assert result.total_candidates == 3


# ── JobMatcher Integration Tests ──────────────────────────────────────────────

class TestJobMatcherIntegration:
    """
    Integration tests for the full JobMatcher pipeline.
    The embedding model is mocked so sentence-transformers is not required.
    """

    def _patched_matcher(self):
        from job_matching.matcher import JobMatcher

        matcher = JobMatcher()
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.side_effect = lambda texts, **kw: (
            np.ones(384, dtype=np.float32) / np.sqrt(384)
            if isinstance(texts, str)
            else np.tile(np.ones(384, dtype=np.float32) / np.sqrt(384), (len(texts), 1))
        )
        matcher._engine._model = mock_model
        return matcher

    def test_match_returns_match_result(self):
        from job_matching.models import MatchResult
        matcher = self._patched_matcher()
        resume  = _make_resume()
        result  = matcher.match(resume, jd_text=SAMPLE_JD_TEXT, jd_title="SE")
        assert isinstance(result, MatchResult)

    def test_match_score_in_valid_range(self):
        matcher = self._patched_matcher()
        result  = matcher.match(_make_resume(), jd_text=SAMPLE_JD_TEXT)
        assert 0.0 <= result.overall_score <= 100.0

    def test_match_rating_is_valid(self):
        from job_matching.models import MatchRating
        matcher = self._patched_matcher()
        result  = matcher.match(_make_resume(), jd_text=SAMPLE_JD_TEXT)
        assert result.match_rating in list(MatchRating)

    def test_match_returns_recommendations(self):
        # A resume missing many skills should produce recommendations
        resume  = _make_resume(skills=["python"])
        matcher = self._patched_matcher()
        result  = matcher.match(resume, jd_text=SAMPLE_JD_TEXT)
        assert isinstance(result.recommendations, list)

    def test_match_missing_skills_subset_of_required(self):
        matcher    = self._patched_matcher()
        resume     = _make_resume(skills=["python"])
        jd         = JDParser().parse(SAMPLE_JD_TEXT)
        result     = matcher.match(resume, jd=jd)
        jd_req_set = set(SkillNormalizer().normalize_list(jd.required_skills))
        missing_set = set(result.missing_required_skills)
        assert missing_set.issubset(jd_req_set | {""}), (
            "Missing skills should be a subset of JD required skills"
        )

    def test_match_and_return_json_is_serialisable(self):
        matcher = self._patched_matcher()
        data    = matcher.match_and_return_json(_make_resume(), jd_text=SAMPLE_JD_TEXT)
        # Must be JSON-serialisable without errors
        serialised = json.dumps(data, default=str)
        assert "overall_score" in json.loads(serialised)

    def test_match_and_save_json_creates_file(self):
        matcher = self._patched_matcher()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "subdir", "result.json")
            matcher.match_and_save_json(_make_resume(), filepath, jd_text=SAMPLE_JD_TEXT)
            assert os.path.exists(filepath)
            with open(filepath) as fh:
                data = json.load(fh)
            assert "overall_score" in data

    def test_rank_candidates_returns_ranking_result(self):
        from job_matching.models import RankingResult
        matcher  = self._patched_matcher()
        resumes  = [_make_resume(f"Candidate {i}", skills=["python", "django"]) for i in range(3)]
        result   = matcher.rank_candidates(resumes, jd_text=SAMPLE_JD_TEXT)
        assert isinstance(result, RankingResult)
        assert result.total_candidates == 3
        ranks = [c.rank for c in result.ranked_candidates]
        assert ranks == list(range(1, 4))

    def test_no_jd_provided_raises(self):
        from job_matching.exceptions import JobMatchingException
        matcher = self._patched_matcher()
        with pytest.raises(JobMatchingException):
            matcher.match(_make_resume())  # neither jd nor jd_text supplied

    def test_experience_gap_detected(self):
        matcher = self._patched_matcher()
        resume  = _make_resume(experience_years=1)  # far below 5-year requirement
        result  = matcher.match(resume, jd_text=SAMPLE_JD_TEXT)
        assert result.experience_gap is not None

    def test_strong_candidate_has_more_exact_matches(self):
        # With a mocked embedding engine, cosine similarity is always 1.0,
        # so we compare exact/alias matches instead of missing skills — exact
        # matches require the normalised token to be present on the resume.
        from job_matching.models import MatchType
        matcher = self._patched_matcher()
        strong  = _make_resume(skills=["python", "django", "postgresql", "docker", "kubernetes", "rest api"])
        weak    = _make_resume(skills=["excel"])
        strong_result = matcher.match(strong, jd_text=SAMPLE_JD_TEXT)
        weak_result   = matcher.match(weak,   jd_text=SAMPLE_JD_TEXT)
        strong_exact = sum(
            1 for m in strong_result.matched_required_skills
            if m.match_type in (MatchType.EXACT, MatchType.ALIAS)
        )
        weak_exact = sum(
            1 for m in weak_result.matched_required_skills
            if m.match_type in (MatchType.EXACT, MatchType.ALIAS)
        )
        assert strong_exact > weak_exact, (
            f"Strong candidate should have more exact matches "
            f"({strong_exact} vs {weak_exact})"
        )


# ── Helpers imported by integration tests ────────────────────────────────────

from job_matching.jd_parser import JDParser
from job_matching.normalizer import SkillNormalizer


if __name__ == "__main__":
    print("Running Job Matching Tests")
    print("=" * 60)
    print(
        "Use: pytest job_matching_tests.py -v\n"
        "Or:  python -m pytest job_matching_tests.py -v"
    )
