"""Unit tests for utils.formatters — pure function coverage."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from utils.formatters import (
    format_date,
    format_experience,
    format_number,
    format_percent,
    format_score,
    initials,
    relative_date,
    score_color,
    score_label,
    skills_as_html_badges,
    truncate,
)


# ── format_score ──────────────────────────────────────────────────────────────

class TestFormatScore:
    def test_returns_one_decimal(self):
        assert format_score(82.456) == "82.5"

    def test_rounds_up(self):
        assert format_score(79.95) == "80.0"

    def test_integer_input(self):
        assert format_score(90) == "90.0"

    def test_zero(self):
        assert format_score(0) == "0.0"


# ── score_color ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (95.0, "#16a34a"),   # excellent → green
    (80.0, "#16a34a"),   # boundary excellent
    (79.9, "#2563eb"),   # just below excellent → blue
    (65.0, "#2563eb"),   # good
    (64.9, "#d97706"),   # just below good → amber
    (50.0, "#d97706"),   # fair boundary
    (49.9, "#dc2626"),   # below fair → red
    (0.0,  "#dc2626"),   # zero
])
def test_score_color_bands(score: float, expected: str):
    assert score_color(score) == expected


# ── score_label ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,label", [
    (85,  "Excellent"),
    (80,  "Excellent"),
    (79,  "Good"),
    (65,  "Good"),
    (64,  "Fair"),
    (50,  "Fair"),
    (49,  "Poor"),
    (0,   "Poor"),
])
def test_score_label_bands(score: float, label: str):
    assert score_label(score) == label


# ── relative_date ─────────────────────────────────────────────────────────────

class TestRelativeDate:
    def test_today(self):
        assert relative_date(date.today()) == "Today"

    def test_yesterday(self):
        assert relative_date(date.today() - timedelta(days=1)) == "Yesterday"

    def test_days_ago(self):
        assert relative_date(date.today() - timedelta(days=5)) == "5 days ago"

    def test_one_week_ago(self):
        assert relative_date(date.today() - timedelta(days=7)) == "1 week ago"

    def test_multiple_weeks_ago(self):
        assert relative_date(date.today() - timedelta(days=14)) == "2 weeks ago"

    def test_one_month_ago(self):
        assert relative_date(date.today() - timedelta(days=30)) == "1 month ago"

    def test_none_returns_dash(self):
        assert relative_date(None) == "—"


# ── format_date ───────────────────────────────────────────────────────────────

class TestFormatDate:
    def test_formats_correctly(self):
        assert format_date(date(2024, 1, 15)) == "Jan 15, 2024"

    def test_none_returns_dash(self):
        assert format_date(None) == "—"


# ── truncate ──────────────────────────────────────────────────────────────────

class TestTruncate:
    def test_short_string_unchanged(self):
        assert truncate("Hello", 10) == "Hello"

    def test_exact_length_unchanged(self):
        s = "A" * 35
        assert truncate(s, 35) == s

    def test_over_length_ellipsis(self):
        s = "A" * 40
        result = truncate(s, 35)
        assert result.endswith("…")
        assert len(result) == 35

    def test_empty_string(self):
        assert truncate("") == ""


# ── format_experience ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("years,expected", [
    (0.5,  "6 months"),
    (1.0,  "1.0 yr"),
    (5.0,  "5.0 yrs"),
    (0.25, "3 months"),
])
def test_format_experience(years: float, expected: str):
    assert format_experience(years) == expected


# ── initials ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("Jane Doe",       "JD"),
    ("Alice",          "A"),
    ("",               "?"),
    ("Mary Jane Watson", "MW"),
])
def test_initials(name: str, expected: str):
    assert initials(name) == expected


# ── skills_as_html_badges ─────────────────────────────────────────────────────

class TestSkillsBadges:
    def test_empty_returns_placeholder(self):
        html = skills_as_html_badges([])
        assert "—" in html

    def test_all_skills_shown_within_limit(self):
        skills = ["Python", "Django", "SQL"]
        html = skills_as_html_badges(skills, max_shown=6)
        for skill in skills:
            assert skill in html

    def test_overflow_shows_count(self):
        skills = ["Python", "Django", "SQL", "Redis", "Docker", "AWS", "Go"]
        html = skills_as_html_badges(skills, max_shown=6)
        assert "+1" in html


# ── format_number / format_percent ───────────────────────────────────────────

def test_format_number_comma_separated():
    assert format_number(1284) == "1,284"

def test_format_percent_default_decimals():
    assert format_percent(82.4) == "82.4%"

def test_format_percent_custom_decimals():
    assert format_percent(82.4444, decimals=0) == "82%"
