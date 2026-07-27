"""
Job Matching Module — semantic resume-to-JD matching engine.

Provides a modular pipeline for:
  - Parsing unstructured job descriptions
  - Normalising skill tokens
  - Generating sentence embeddings (sentence-transformers)
  - Computing multi-dimensional similarity scores
  - Ranking candidate pools
  - Producing explainable JSON match reports

Quick-start::

    from parser import ResumeParser
    from job_matching import JobMatcher

    resume  = ResumeParser().parse("resume.pdf")
    matcher = JobMatcher()

    # Match against raw text
    result  = matcher.match(resume, jd_text=open("job_post.txt").read())
    print(f"Match score: {result.overall_score}/100 ({result.match_rating.value})")
    print(f"Missing required skills: {result.missing_required_skills}")

    # Rank multiple candidates
    resumes = [ResumeParser().parse(f) for f in resume_files]
    ranking = matcher.rank_candidates(resumes, jd_text=jd_text)
    for candidate in ranking.ranked_candidates:
        print(f"#{candidate.rank}  {candidate.candidate_name}  {candidate.overall_score:.1f}")
"""

from job_matching.exceptions import (
    ConfigurationException,
    EmbeddingException,
    JDParsingException,
    JobMatchingException,
    NormalizationException,
    RankingException,
    SimilarityException,
)
from job_matching.jd_parser import JDParser
from job_matching.matcher import JobMatcher
from job_matching.models import (
    CandidateMatch,
    JobDescription,
    MatchRating,
    MatchResult,
    MatchType,
    Priority,
    RankingResult,
    Recommendation,
    ScoreBreakdown,
    SkillMatch,
)
from job_matching.normalizer import SkillNormalizer

__version__ = "1.0.0"

__all__ = [
    # Primary interface
    "JobMatcher",
    "JDParser",
    "SkillNormalizer",
    # Models
    "JobDescription",
    "MatchResult",
    "RankingResult",
    "CandidateMatch",
    "ScoreBreakdown",
    "SkillMatch",
    "Recommendation",
    # Enumerations
    "MatchRating",
    "MatchType",
    "Priority",
    # Exceptions
    "JobMatchingException",
    "JDParsingException",
    "NormalizationException",
    "EmbeddingException",
    "SimilarityException",
    "RankingException",
    "ConfigurationException",
]
