"""
ATS configuration with scoring weights and thresholds.

Centralizes all scoring parameters, weights, and configuration values
to avoid hardcoding throughout the codebase.
"""

from typing import Dict

# ============================================================================
# SCORING WEIGHTS (Total should sum to 100)
# ============================================================================

SCORING_WEIGHTS = {
    "contact_details": 10,      # Contact information completeness
    "professional_summary": 8,  # Professional summary/objective
    "skills": 15,               # Skills section quality and relevance
    "education": 12,            # Education history
    "experience": 25,           # Work experience
    "projects": 10,             # Projects and portfolio
    "certifications": 8,        # Certifications and credentials
    "formatting": 7,            # Document formatting quality
    "keywords": 5,              # Keyword density and relevance
}

# Verify weights sum to 100
_total_weight = sum(SCORING_WEIGHTS.values())
if _total_weight != 100:
    raise ValueError(f"Scoring weights must sum to 100, got {_total_weight}")

# ============================================================================
# SCORE THRESHOLDS AND RANGES
# ============================================================================

SCORE_RANGES = {
    "excellent": (80, 100),     # 80-100: Excellent
    "good": (70, 79),           # 70-79: Good
    "fair": (60, 69),           # 60-69: Fair
    "poor": (0, 59),            # 0-59: Poor
}

# ============================================================================
# CONTACT DETAILS CONFIGURATION
# ============================================================================

CONTACT_DETAILS_REQUIRED = {
    "full_name": True,
    "email": True,
    "phone": True,
}

CONTACT_DETAILS_OPTIONAL = {
    "location": False,
    "linkedin": False,
    "github": False,
    "website": False,
}

# ============================================================================
# COMPLETENESS THRESHOLDS
# ============================================================================

MIN_SKILLS_REQUIRED = 3
MIN_EDUCATION_REQUIRED = 1
MIN_EXPERIENCE_REQUIRED = 1
MIN_PROFESSIONAL_SUMMARY_LENGTH = 50

# ============================================================================
# EXPERIENCE CALCULATION
# ============================================================================

EXPERIENCE_RANGES = {
    "entry_level": (0, 2),           # 0-2 years
    "junior": (2, 5),                # 2-5 years
    "mid_level": (5, 10),            # 5-10 years
    "senior": (10, 15),              # 10-15 years
    "lead": (15, 20),                # 15-20 years
    "executive": (20, float("inf")), # 20+ years
}

# ============================================================================
# SECTION COMPLETENESS SCORING
# ============================================================================

SECTION_COMPLETENESS_SCORES = {
    "contact_details": {
        "required": 25,         # Max points if all required fields present
        "optional_per_field": 5,  # Points per optional field (max 4 optional)
    },
    "professional_summary": {
        "missing": 0,
        "present": 8,
    },
    "skills": {
        "base": 10,
        "per_skill": 0.5,       # Points per skill (capped)
        "max_bonus": 5,
    },
    "education": {
        "base": 10,
        "per_entry": 1,
        "max_bonus": 2,
    },
    "experience": {
        "base": 20,
        "per_year": 1,
        "max_bonus": 5,
    },
    "projects": {
        "base": 5,
        "per_project": 1,
        "max_bonus": 5,
    },
    "certifications": {
        "base": 5,
        "per_certification": 1,
        "max_bonus": 3,
    },
}

# ============================================================================
# FORMATTING QUALITY
# ============================================================================

FORMATTING_CHECKS = {
    "no_special_characters": 1,
    "consistent_dates": 1,
    "consistent_formatting": 2,
    "proper_spacing": 1,
    "no_spelling_errors": 2,  # Inferred from text quality
}

# ============================================================================
# KEYWORD CATEGORIES FOR SCORING
# ============================================================================

HIGH_VALUE_KEYWORDS = {
    "leadership": 2,
    "management": 2,
    "strategy": 1.5,
    "innovation": 1.5,
    "optimization": 1.5,
    "automation": 1.5,
    "cross-functional": 1,
}

ACHIEVEMENT_KEYWORDS = {
    "increased": 1,
    "improved": 1,
    "reduced": 1,
    "saved": 1,
    "implemented": 0.5,
    "developed": 0.5,
    "designed": 0.5,
}

# ============================================================================
# MISSING SECTION PENALTIES
# ============================================================================

MISSING_SECTION_PENALTIES = {
    "contact_details": 15,      # Critical
    "skills": 10,               # Important
    "experience": 20,           # Critical
    "education": 8,             # Important
    "professional_summary": 5,  # Nice to have
    "projects": 3,              # Nice to have
    "certifications": 3,        # Nice to have
}

# ============================================================================
# WEAKNESS DETECTION THRESHOLDS
# ============================================================================

WEAKNESS_THRESHOLDS = {
    "few_skills": 5,                    # Less than this number of skills
    "short_summary": MIN_PROFESSIONAL_SUMMARY_LENGTH,
    "gaps_in_employment": 0.5,          # Years
    "no_quantified_achievements": 0.3,  # Percentage of descriptions
    "short_descriptions": 20,           # Characters minimum
    "no_certifications": True,          # Flag if missing
    "limited_projects": 2,              # Less than this number
}

# ============================================================================
# RECOMMENDATION PRIORITIES
# ============================================================================

RECOMMENDATION_PRIORITIES = {
    "critical": 1,      # Must fix for good ATS score
    "high": 2,          # Strongly recommended
    "medium": 3,        # Recommended
    "low": 4,           # Nice to have
}

# ============================================================================
# SCORING ADJUSTMENT FACTORS
# ============================================================================

# Multipliers for various conditions
SCORE_MULTIPLIERS = {
    "recent_experience_bonus": 1.05,    # 5% bonus if recent experience (<2 years)
    "multiple_positions_bonus": 1.03,   # 3% bonus per multiple position levels
    "relevant_skills_bonus": 1.02,      # 2% bonus for skills diversity
}

# ============================================================================
# TEXT ANALYSIS
# ============================================================================

MIN_WORDS_PER_DESCRIPTION = 5
MAX_WORDS_PER_BULLET = 30
IDEAL_BULLET_COUNT_PER_ROLE = (3, 5)  # Min, Max bullets per role

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FILE = "logs/ats.log"
