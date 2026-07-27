"""
Pydantic data models for the Job Matching module.

Every public surface of the matching pipeline is represented as a typed,
validated Pydantic model.  This guarantees that JSON serialisation is
always safe and that downstream consumers receive well-defined contracts.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class MatchType(str, Enum):
    """How a resume skill was matched to a JD skill."""
    EXACT    = "exact"     # case-insensitive identical match
    ALIAS    = "alias"     # matched via the alias lookup table
    SEMANTIC = "semantic"  # matched via embedding similarity


class MatchRating(str, Enum):
    """Human-readable band for an overall match score."""
    EXCELLENT = "Excellent"  # ≥ 85
    GOOD      = "Good"       # 70–84
    FAIR      = "Fair"       # 50–69
    POOR      = "Poor"       # < 50


class Priority(str, Enum):
    """Priority level used for recommendations."""
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"


# ── Job Description ───────────────────────────────────────────────────────────

class JobDescription(BaseModel):
    """
    Structured representation of a job posting after parsing.

    Created by JDParser.parse(); consumed by the similarity and scoring
    components.
    """

    title:               str
    company:             Optional[str]  = None
    raw_text:            str
    required_skills:     List[str]      = Field(default_factory=list)
    preferred_skills:    List[str]      = Field(default_factory=list)
    responsibilities:    List[str]      = Field(default_factory=list)
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    education_level:     Optional[str]  = None
    location:            Optional[str]  = None
    job_type:            Optional[str]  = None  # full-time, contract, etc.

    @property
    def all_skills(self) -> List[str]:
        """Combined deduplicated list of required and preferred skills."""
        return list(dict.fromkeys(self.required_skills + self.preferred_skills))

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Python Engineer",
                "company": "Acme Corp",
                "required_skills": ["Python", "Django", "PostgreSQL"],
                "preferred_skills": ["Docker", "Kubernetes"],
                "min_experience_years": 5,
            }
        }


# ── Per-Skill Match Detail ────────────────────────────────────────────────────

class SkillMatch(BaseModel):
    """
    Record of a single skill matching event between resume and JD.
    """

    jd_skill:     str
    resume_skill: str
    match_type:   MatchType
    confidence:   float = Field(ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "jd_skill": "Kubernetes",
                "resume_skill": "k8s",
                "match_type": "alias",
                "confidence": 1.0,
            }
        }


# ── Score Breakdown ───────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    """
    Weighted component scores that combine into the overall match score.

    Each field is 0–100 before weighting.
    """

    skills_match:        float = Field(ge=0.0, le=100.0)
    semantic_similarity: float = Field(ge=0.0, le=100.0)
    experience_match:    float = Field(ge=0.0, le=100.0)
    education_match:     float = Field(ge=0.0, le=100.0)


# ── Recommendation ────────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    """
    A single actionable recommendation for the candidate to improve their match.
    """

    action:   str
    reason:   str
    priority: Priority
    category: str  # e.g. "skills", "experience", "education"

    class Config:
        json_schema_extra = {
            "example": {
                "action": "Add Docker and Kubernetes to your skills section",
                "reason": "Both are required skills for this position",
                "priority": "High",
                "category": "skills",
            }
        }


# ── Full Match Result ─────────────────────────────────────────────────────────

class MatchResult(BaseModel):
    """
    Complete output of a single resume ↔ job description match.

    Returned by JobMatcher.match() and embedded in CandidateMatch records.
    """

    overall_score:           float       = Field(ge=0.0, le=100.0)
    match_rating:            MatchRating
    score_breakdown:         ScoreBreakdown

    # Skill-level detail
    matched_required_skills:  List[SkillMatch] = Field(default_factory=list)
    matched_preferred_skills: List[SkillMatch] = Field(default_factory=list)
    missing_required_skills:  List[str]        = Field(default_factory=list)
    missing_preferred_skills: List[str]        = Field(default_factory=list)
    extra_skills:             List[str]        = Field(default_factory=list)

    # Gap narratives
    experience_gap: Optional[str] = None  # human-readable gap description
    education_gap:  Optional[str] = None

    # Explainability
    strengths:         List[str]           = Field(default_factory=list)
    gaps:              List[str]           = Field(default_factory=list)
    recommendations:   List[Recommendation] = Field(default_factory=list)
    match_explanation: str                 = ""

    # Audit
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

    def model_dump_clean(self) -> Dict[str, Any]:
        """JSON-serialisable dict with ISO timestamp strings."""
        data = self.model_dump()
        data["analysis_timestamp"] = self.analysis_timestamp.isoformat()
        return data

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 78.5,
                "match_rating": "Good",
                "missing_required_skills": ["Kubernetes"],
            }
        }


# ── Candidate in a Ranked List ────────────────────────────────────────────────

class CandidateMatch(BaseModel):
    """
    One entry in a multi-candidate ranking result.
    """

    rank:            int
    candidate_name:  str
    candidate_email: Optional[str] = None
    overall_score:   float
    match_rating:    MatchRating
    match_result:    MatchResult


# ── Ranking Result ────────────────────────────────────────────────────────────

class RankingResult(BaseModel):
    """
    Ordered list of candidates ranked against a single job description.

    Returned by JobMatcher.rank_candidates().
    """

    job_title:         str
    company:           Optional[str] = None
    total_candidates:  int
    ranked_candidates: List[CandidateMatch] = Field(default_factory=list)
    ranking_timestamp: datetime             = Field(default_factory=datetime.utcnow)

    def model_dump_clean(self) -> Dict[str, Any]:
        """JSON-serialisable dict with ISO timestamp strings."""
        data = self.model_dump()
        data["ranking_timestamp"] = self.ranking_timestamp.isoformat()
        for c in data["ranked_candidates"]:
            ts = c["match_result"].get("analysis_timestamp")
            if isinstance(ts, datetime):
                c["match_result"]["analysis_timestamp"] = ts.isoformat()
        return data
