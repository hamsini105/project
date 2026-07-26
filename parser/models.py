"""
Data models for resume parsing using Pydantic.

Defines the schema for resume data extraction with type validation,
JSON serialization, and documentation.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator


class ContactDetails(BaseModel):
    """Contact information extracted from resume."""

    full_name: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[HttpUrl] = None
    github: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None

    class Config:
        json_schema_extra = {"example": {"full_name": "John Doe", "email": "john@example.com"}}


class EducationEntry(BaseModel):
    """Single education entry."""

    institution: str = Field(..., min_length=1)
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    grade: Optional[str] = None  # GPA or grade
    details: Optional[List[str]] = None  # Additional achievements, coursework

    class Config:
        json_schema_extra = {
            "example": {
                "institution": "MIT",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
            }
        }


class ExperienceEntry(BaseModel):
    """Single work experience entry."""

    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = False
    description: Optional[List[str]] = None  # Job responsibilities/achievements
    location: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "company": "Tech Corp",
                "position": "Senior Software Engineer",
                "is_current": True,
            }
        }


class ProjectEntry(BaseModel):
    """Single project entry."""

    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    link: Optional[HttpUrl] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "E-commerce Platform",
                "technologies": ["Python", "Django", "PostgreSQL"],
            }
        }


class CertificationEntry(BaseModel):
    """Single certification entry."""

    title: str = Field(..., min_length=1)
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[HttpUrl] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "AWS Solutions Architect",
                "issuer": "Amazon",
            }
        }


class Resume(BaseModel):
    """
    Complete resume data model.

    Represents all extracted information from a resume in a standardized format.
    """

    contact: ContactDetails
    summary: Optional[str] = Field(None, max_length=1000)
    skills: Optional[List[str]] = None
    education: Optional[List[EducationEntry]] = None
    experience: Optional[List[ExperienceEntry]] = None
    projects: Optional[List[ProjectEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None
    languages: Optional[List[str]] = None
    additional_info: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "contact": {"full_name": "Jane Doe", "email": "jane@example.com"},
                "skills": ["Python", "Django", "PostgreSQL"],
            }
        }

    def model_dump_clean(self) -> dict:
        """
        Return model dump excluding None values for cleaner JSON output.

        Returns:
            Dictionary with None values filtered out.
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}
