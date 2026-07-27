"""
ATS Analysis Module - Production-grade resume ATS scoring engine.

Provides comprehensive ATS analysis with scoring, validation, completeness checks,
experience calculation, and actionable recommendations.

Example usage:
    from parser import ResumeParser
    from ats import ATSAnalyzer

    # Parse resume
    parser = ResumeParser()
    resume = parser.parse("resume.pdf")

    # Analyze with ATS
    analyzer = ATSAnalyzer()
    report = analyzer.analyze(resume)

    # Get JSON output
    json_data = report.model_dump_clean()
    print(f"ATS Score: {report.overall_score}/100")
    print(f"Rating: {report.score_rating}")
"""

from ats.analyzer import ATSAnalyzer
from ats.exceptions import (
    ATSException,
    AnalysisException,
    CompletenessException,
    ConfigurationException,
    ScoringException,
    ValidationException,
)
from ats.models import (
    ATSReport,
    CompletenessReport,
    FormattingAnalysis,
    KeywordAnalysis,
    Recommendation,
    ScoreBreakdown,
    Strength,
    Weakness,
)

__version__ = "1.0.0"

__all__ = [
    # Main analyzer
    "ATSAnalyzer",
    # Models
    "ATSReport",
    "ScoreBreakdown",
    "Strength",
    "Weakness",
    "Recommendation",
    "CompletenessReport",
    "KeywordAnalysis",
    "FormattingAnalysis",
    # Exceptions
    "ATSException",
    "ValidationException",
    "ScoringException",
    "ConfigurationException",
    "AnalysisException",
    "CompletenessException",
]
