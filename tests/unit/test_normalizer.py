"""Unit tests for job_matching.normalizer.SkillNormalizer."""

from __future__ import annotations

import pytest

from job_matching.normalizer import SkillNormalizer


@pytest.fixture
def norm() -> SkillNormalizer:
    return SkillNormalizer()


class TestNormalize:
    def test_lowercases(self, norm):
        assert norm.normalize("Python") == "python"

    def test_strips_quotes(self, norm):
        assert norm.normalize('"Python"') == "python"

    def test_collapses_whitespace(self, norm):
        assert norm.normalize("machine  learning") == "machine learning"

    def test_empty_string_returns_empty(self, norm):
        assert norm.normalize("") == ""

    def test_non_string_raises(self, norm):
        from job_matching.exceptions import NormalizationException
        with pytest.raises(NormalizationException):
            norm.normalize(42)  # type: ignore[arg-type]

    @pytest.mark.parametrize("raw,canonical", [
        ("JS",       "javascript"),
        ("js",       "javascript"),
        ("k8s",      "kubernetes"),
        ("golang",   "go"),
        ("ML",       "machine learning"),
        ("NodeJS",   "node.js"),
        ("Postgres", "postgresql"),
        ("ReactJS",  "react"),
        ("rest",     "rest api"),
        ("AWS",      "aws"),          # alias not in map → lowercased only
    ])
    def test_alias_resolution(self, norm, raw: str, canonical: str):
        assert norm.normalize(raw) == canonical


class TestNormalizeList:
    def test_deduplicates(self, norm):
        result = norm.normalize_list(["Python", "python", "PYTHON"])
        assert result == ["python"]

    def test_preserves_first_seen_order(self, norm):
        result = norm.normalize_list(["django", "python", "postgresql"])
        assert result.index("django") < result.index("python") < result.index("postgresql")

    def test_drops_empty_results(self, norm):
        result = norm.normalize_list(["", "  ", "python"])
        assert "" not in result
        assert "python" in result

    def test_skips_non_string_entries_gracefully(self, norm):
        result = norm.normalize_list(["python", None, "django"])  # type: ignore[list-item]
        assert "python" in result
        assert "django" in result

    def test_empty_input_returns_empty_list(self, norm):
        assert norm.normalize_list([]) == []
