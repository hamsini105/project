"""
Integration tests for the Job Matching pipeline.

Tests the full flow: raw JD text → JDParser → SkillNormalizer →
SimilarityCalculator (mocked embeddings) → MatchExplainer →
CandidateRanker → JobMatcher.

The embedding engine is always mocked so the test suite runs without
sentence-transformers or GPU access.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from job_matching.jd_parser import JDParser
from job_matching.matcher import JobMatcher
from job_matching.models import MatchRating, MatchResult, MatchType, RankingResult
from job_matching.normalizer import SkillNormalizer
from job_matching.ranker import CandidateRanker


SAMPLE_JD_TEXT = """\
Senior Python Engineer

Requirements
- 5+ years of professional software development experience
- Strong proficiency in Python and Django
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
"""


# ── JDParser + Normalizer pipeline ────────────────────────────────────────────

class TestParseAndNormalize:
    def test_normalizer_lowercases_jd_skills(self, parsed_jd):
        norm = SkillNormalizer()
        normalised = norm.normalize_list(parsed_jd.required_skills)
        assert all(s == s.lower() for s in normalised)

    def test_alias_skills_resolved(self, parsed_jd):
        # "PostgreSQL" should normalise to "postgresql"
        norm      = SkillNormalizer()
        canonical = norm.normalize_list(parsed_jd.required_skills)
        assert "postgresql" in canonical


# ── JobMatcher (mocked engine) ────────────────────────────────────────────────

@pytest.fixture
def matcher(mock_embedding_engine) -> JobMatcher:
    m = JobMatcher()
    m._engine = mock_embedding_engine
    m._similarity._engine = mock_embedding_engine
    return m


class TestJobMatcherMatch:
    def test_returns_match_result(self, matcher, sample_resume):
        result = matcher.match(sample_resume, jd_text=SAMPLE_JD_TEXT)
        assert isinstance(result, MatchResult)

    def test_overall_score_in_range(self, matcher, sample_resume):
        result = matcher.match(sample_resume, jd_text=SAMPLE_JD_TEXT)
        assert 0.0 <= result.overall_score <= 100.0

    def test_score_rating_is_valid(self, matcher, sample_resume):
        result = matcher.match(sample_resume, jd_text=SAMPLE_JD_TEXT)
        assert result.match_rating in list(MatchRating)

    def test_recommendations_is_list(self, matcher, sample_resume):
        result = matcher.match(sample_resume, jd_text=SAMPLE_JD_TEXT)
        assert isinstance(result.recommendations, list)

    def test_missing_skills_are_subset_of_jd_required(self, matcher, sample_resume):
        jd     = JDParser().parse(SAMPLE_JD_TEXT)
        result = matcher.match(sample_resume, jd=jd)
        norm   = SkillNormalizer()
        jd_req = set(norm.normalize_list(jd.required_skills))
        assert set(result.missing_required_skills).issubset(jd_req | {""})

    def test_no_jd_provided_raises(self, matcher, sample_resume):
        from job_matching.exceptions import JobMatchingException
        with pytest.raises(JobMatchingException):
            matcher.match(sample_resume)

    def test_resume_with_matching_skills_has_exact_matches(self, matcher, sample_resume):
        result = matcher.match(sample_resume, jd_text=SAMPLE_JD_TEXT)
        exact = [m for m in result.matched_required_skills
                 if m.match_type == MatchType.EXACT]
        assert len(exact) > 0


class TestJobMatcherJson:
    def test_json_output_serialisable(self, matcher, sample_resume):
        data = matcher.match_and_return_json(sample_resume, jd_text=SAMPLE_JD_TEXT)
        assert "overall_score" in data
        json.dumps(data, default=str)  # must not raise

    def test_save_json_creates_file(self, matcher, sample_resume):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "result.json")
            matcher.match_and_save_json(sample_resume, path, jd_text=SAMPLE_JD_TEXT)
            assert os.path.isfile(path)
            with open(path) as fh:
                data = json.load(fh)
            assert "overall_score" in data


# ── Ranking ───────────────────────────────────────────────────────────────────

class TestCandidateRanking:
    def test_rank_candidates_returns_ranking_result(self, matcher, sample_resume):
        result = matcher.rank_candidates([sample_resume], jd_text=SAMPLE_JD_TEXT)
        assert isinstance(result, RankingResult)
        assert result.total_candidates == 1

    def test_multiple_candidates_sorted_descending(self, matcher, sample_resume, minimal_resume):
        result = matcher.rank_candidates(
            [minimal_resume, sample_resume], jd_text=SAMPLE_JD_TEXT
        )
        scores = [c.overall_score for c in result.ranked_candidates]
        assert scores == sorted(scores, reverse=True)

    def test_ranks_start_at_one(self, matcher, sample_resume):
        result = matcher.rank_candidates([sample_resume], jd_text=SAMPLE_JD_TEXT)
        assert result.ranked_candidates[0].rank == 1

    def test_ranker_empty_raises(self):
        from job_matching.exceptions import RankingException
        from job_matching.models import JobDescription
        ranker = CandidateRanker()
        jd = JobDescription(title="SWE", raw_text="test")
        with pytest.raises(RankingException):
            ranker.rank([], jd)
