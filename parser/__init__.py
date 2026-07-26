"""
Resume Parser System - Production-grade resume parsing engine.

Provides a modular architecture for parsing and extracting data from resume
files (PDF and DOCX formats) into a standardized JSON schema.

Example usage:
    from parser import ResumeParser

    parser = ResumeParser()
    resume = parser.parse("resume.pdf")
    print(resume.model_dump_clean())

    # Or save to JSON
    parser.parse_and_save_json("resume.pdf", "output.json")
"""

from parser.exceptions import (
    ExtractionException,
    FileReadException,
    FileValidationException,
    InvalidResumeDataException,
    PreprocessingException,
    ResumeParsingException,
)
from parser.models import (
    CertificationEntry,
    ContactDetails,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Resume,
)
from parser.parser import ResumeParser

__version__ = "1.0.0"

__all__ = [
    # Main parser
    "ResumeParser",
    # Models
    "Resume",
    "ContactDetails",
    "EducationEntry",
    "ExperienceEntry",
    "ProjectEntry",
    "CertificationEntry",
    # Exceptions
    "ResumeParsingException",
    "FileReadException",
    "FileValidationException",
    "ExtractionException",
    "PreprocessingException",
    "InvalidResumeDataException",
]
