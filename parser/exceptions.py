"""
Custom exceptions for the resume parsing engine.

Provides domain-specific exception classes for different failure scenarios
during resume parsing and data extraction.
"""


class ResumeParsingException(Exception):
    """Base exception for all resume parsing errors."""

    pass


class FileReadException(ResumeParsingException):
    """Raised when file reading fails (PDF, DOCX)."""

    pass


class FileValidationException(ResumeParsingException):
    """Raised when file validation fails."""

    pass


class ExtractionException(ResumeParsingException):
    """Raised when data extraction from text fails."""

    pass


class PreprocessingException(ResumeParsingException):
    """Raised when text preprocessing fails."""

    pass


class InvalidResumeDataException(ResumeParsingException):
    """Raised when resume data doesn't conform to expected schema."""

    pass
