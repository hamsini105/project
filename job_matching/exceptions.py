"""
Exception hierarchy for the Job Matching module.

All exceptions derive from JobMatchingException so callers can catch
either the base type for broad handling or a specific subtype for
granular recovery.
"""


class JobMatchingException(Exception):
    """
    Base exception for all job matching errors.

    Catching this type handles any failure originating from this module.
    """


class JDParsingException(JobMatchingException):
    """
    Raised when a job description cannot be parsed into structured data.

    Common causes: empty text, unrecognisable format, encoding issues.
    """


class NormalizationException(JobMatchingException):
    """
    Raised when skill normalisation fails unexpectedly.

    Typically indicates bad input data rather than a logic error.
    """


class EmbeddingException(JobMatchingException):
    """
    Raised when sentence embedding generation fails.

    Common causes: model not installed, out-of-memory, invalid input text.
    """


class SimilarityException(JobMatchingException):
    """
    Raised when similarity calculation produces an invalid result.

    May indicate shape mismatches or numerical instability in embeddings.
    """


class RankingException(JobMatchingException):
    """
    Raised when candidate ranking cannot be completed.

    Common causes: empty candidate list, inconsistent score types.
    """


class ConfigurationException(JobMatchingException):
    """
    Raised when module configuration is detected to be invalid at runtime.

    Examples: scoring weights do not sum to 1.0, unknown model name.
    """
