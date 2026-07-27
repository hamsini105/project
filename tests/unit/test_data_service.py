"""Unit tests for utils.data_service.CandidateService."""

from __future__ import annotations

import pytest

from utils.data_service import CandidateService


@pytest.fixture
def service() -> CandidateService:
    return CandidateService()


class TestGetAll:
    def test_returns_dataframe(self, service):
        import pandas as pd
        df = service.get_all()
        assert isinstance(df, pd.DataFrame)

    def test_has_expected_columns(self, service):
        df = service.get_all()
        for col in ("id", "name", "email", "role", "status", "ats_score"):
            assert col in df.columns, f"Missing column: {col}"

    def test_returns_150_rows(self, service):
        df = service.get_all()
        assert len(df) == 150

    def test_deterministic_across_calls(self, service):
        df1 = service.get_all()
        df2 = service.get_all()
        assert list(df1["id"]) == list(df2["id"])


class TestSearch:
    def test_search_by_name_substring(self, service):
        df = service.get_all()
        first_name = df.iloc[0]["name"].split()[0]
        result = service.search(first_name, df)
        assert len(result) >= 1
        assert first_name.lower() in result.iloc[0]["name"].lower()

    def test_empty_query_returns_all(self, service):
        df = service.get_all()
        result = service.search("", df)
        assert len(result) == len(df)

    def test_no_match_returns_empty(self, service):
        df = service.get_all()
        result = service.search("zzzz_no_match_zzzz", df)
        assert len(result) == 0


class TestApplyFilters:
    def test_status_filter(self, service):
        df = service.get_all()
        result = service.apply_filters(df, statuses=["Hired"])
        assert all(result["status"] == "Hired")

    def test_score_range_filter(self, service):
        df = service.get_all()
        result = service.apply_filters(df, min_score=70, max_score=90)
        assert result["ats_score"].between(70, 90).all()

    def test_education_filter(self, service):
        df = service.get_all()
        result = service.apply_filters(df, education=["PhD"])
        assert all(result["education"] == "PhD")

    def test_empty_status_list_returns_all(self, service):
        df = service.get_all()
        result = service.apply_filters(df, statuses=None)
        assert len(result) == len(df)


class TestGetKpiSummary:
    def test_has_expected_keys(self, service):
        kpi = service.get_kpi_summary()
        for key in ("total_candidates", "active_roles", "avg_ats_score",
                    "hired_this_month", "pending_review", "rejection_rate"):
            assert key in kpi

    def test_total_candidates_correct(self, service):
        kpi = service.get_kpi_summary()
        assert kpi["total_candidates"] == 150

    def test_avg_score_in_valid_range(self, service):
        kpi = service.get_kpi_summary()
        assert 0 <= kpi["avg_ats_score"] <= 100


class TestGetSkillsFrequency:
    def test_returns_dataframe_with_columns(self, service):
        df = service.get_skills_frequency()
        assert "skill" in df.columns
        assert "count" in df.columns

    def test_respects_top_n(self, service):
        df = service.get_skills_frequency(top_n=5)
        assert len(df) <= 5

    def test_sorted_descending(self, service):
        df = service.get_skills_frequency()
        counts = df["count"].tolist()
        assert counts == sorted(counts, reverse=True)
