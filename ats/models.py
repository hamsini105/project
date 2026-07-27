"""
Pydantic models for ATS analysis results and reports.

Defines the schema for ATS analysis output with validation,
JSON serialization, and documentation.
"""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator


class ScoreBreakdown(BaseModel):
    """Breakdown of ATS score by category."""

    contact_details: float = Field(..., ge=0, le=100)
    professional_summary: float = Field(..., ge=0, le=100)
    skills: float = Field(..., ge=0, le=100)
    education: float = Field(..., ge=0, le=100)
    experience: float = Field(..., ge=0, le=100)
    projects: float = Field(..., ge=0, le=100)
    certifications: float = Field(..., ge=0, le=100)
    formatting: float = Field(..., ge=0, le=100)
    keywords: float = Field(..., ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "contact_details": 10,
                "professional_summary": 7,
                "skills": 14,
            }
        }


class Strength(BaseModel):
    """A resume strength identified in the analysis."""

    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    impact: str = Field(
        ..., description="High, Medium, or Low impact", regex="^(High|Medium|Low)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "category": "skills",
                "description": "Comprehensive technical skills with 15+ technologies",
                "impact": "High",
            }
        }


class Weakness(BaseModel):
    """A resume weakness identified in the analysis."""

    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: str = Field(
        ..., description="Critical, High, Medium, or Low", regex="^(Critical|High|Medium|Low)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "category": "experience",
                "description": "Employment gap of 1.5 years",
                "severity": "High",
            }
        }


class Recommendation(BaseModel):
    """An actionable recommendation to improve ATS score."""

    action: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    priority: str = Field(
        ..., description="Critical, High, Medium, or Low", regex="^(Critical|High|Medium|Low)$"
    )
    estimated_score_improvement: float = Field(
        default=0, ge=0, le=100, description="Estimated % improvement in ATS score"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "Add 2-3 more project examples with quantified results",
                "reason": "Projects section can improve portfolio credibility and ATS score by 3-5%",
                "priority": "High",
                "estimated_score_improvement": 4,
            }
        }


class ATSReport(BaseModel):
    """
    Complete ATS analysis report.

    Provides a comprehensive breakdown of resume ATS compatibility with
    scores, strengths, weaknesses, and actionable recommendations.
    """

    overall_score: float = Field(..., ge=0, le=100, description="Overall ATS score 0-100")
    score_rating: str = Field(
        ...,
        description="Rating category",
        regex="^(Excellent|Good|Fair|Poor)$",
    )
    score_breakdown: ScoreBreakdown = Field(..., description="Score by category")
    completeness_percentage: float = Field(
        ..., ge=0, le=100, description="How complete the resume is"
    )
    experience_years: float = Field(..., ge=0, description="Total years of experience")
    experience_level: str = Field(
        ...,
        description="Experience level",
        regex="^(Entry|Junior|Mid|Senior|Lead|Executive)$",
    )
    strengths: List[Strength] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[Weakness] = Field(default_factory=list, description="Identified weaknesses")
    missing_sections: List[str] = Field(
        default_factory=list, description="Major sections missing from resume"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    analysis_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional analysis metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 75,
                "score_rating": "Good",
                "completeness_percentage": 85,
                "experience_years": 8,
                "experience_level": "Mid",
            }
        }

    def model_dump_clean(self) -> dict:
        """
        Return model dump excluding empty lists and None values for cleaner JSON output.

        Returns:
            Dictionary with empty collections filtered out.
        """
        data = self.model_dump()
        return {
            k: v
            for k, v in data.items()
            if v is not None and (not isinstance(v, list) or len(v) > 0)
        }


class CompletenessReport(BaseModel):
    """Detailed completeness analysis of resume sections."""

    contact_details_complete: bool
    contact_details_missing_fields: List[str] = Field(default_factory=list)
    professional_summary_present: bool
    skills_present: bool
    skills_count: int = Field(default=0, ge=0)
    education_present: bool
    education_count: int = Field(default=0, ge=0)
    experience_present: bool
    experience_count: int = Field(default=0, ge=0)
    projects_present: bool
    projects_count: int = Field(default=0, ge=0)
    certifications_present: bool
    certifications_count: int = Field(default=0, ge=0)
    overall_completeness: float = Field(..., ge=0, le=100)


class KeywordAnalysis(BaseModel):
    """Analysis of keyword usage in resume."""

    high_value_keywords_found: List[str] = Field(default_factory=list)
    achievement_keywords_count: int = Field(default=0, ge=0)
    power_words_score: float = Field(default=0, ge=0, le=100)
    keyword_density: float = Field(default=0, ge=0, le=100)


class FormattingAnalysis(BaseModel):
    """Analysis of resume formatting quality."""

    consistency_score: float = Field(default=0, ge=0, le=100)
    spacing_score: float = Field(default=0, ge=0, le=100)
    date_format_consistency: bool = Field(default=True)
    has_unusual_characters: bool = Field(default=False)
    estimated_ats_parse_friendly: bool = Field(default=True)
