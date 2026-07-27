"""
Custom exceptions for the ATS analysis engine.

Provides domain-specific exception classes for different failure scenarios
during resume scoring and analysis.
"""


class ATSException(Exception):
    """Base exception for all ATS analysis errors."""

    pass


class ValidationException(ATSException):
    """Raised when resume validation fails."""

    pass


class ScoringException(ATSException):
    """Raised when scoring calculation fails."""

    pass


class ConfigurationException(ATSException):
    """Raised when ATS configuration is invalid."""

    pass


class AnalysisException(ATSException):
    """Raised when ATS analysis fails."""

    pass


class CompletenessException(ATSException):
    """Raised when completeness check fails."""

    pass
