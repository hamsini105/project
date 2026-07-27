"""
JobMatcher — main orchestrator for the job matching pipeline.

Coordinates all sub-modules in a single entry point:

  JDParser → SkillNormalizer → EmbeddingEngine
      → SimilarityCalculator → MatchExplainer → CandidateRanker

The public surface is intentionally minimal:

  matcher.match(resume, jd)                   → MatchResult
  matcher.rank_candidates(resumes, jd)        → RankingResult
  matcher.match_and_return_json(resume, jd)   → dict
  matcher.rank_and_return_json(resumes, jd)   → dict
  matcher.match_and_save_json(resume, jd, fp) → dict
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from parser.models import Resume

from job_matching.config import EMBEDDING_MODEL_NAME
from job_matching.embeddings import EmbeddingEngine
from job_matching.exceptions import JobMatchingException
from job_matching.explainer import MatchExplainer
from job_matching.jd_parser import JDParser
from job_matching.models import JobDescription, MatchResult, RankingResult
from job_matching.normalizer import SkillNormalizer
from job_matching.ranker import CandidateRanker
from job_matching.similarity import SimilarityCalculator

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    End-to-end job-to-resume matching engine.

    A single JobMatcher instance owns its own EmbeddingEngine, which
    lazily loads the sentence-transformers model on first use.  Reuse
    one instance across multiple calls to benefit from embedding caching.

    Args:
        model_name: Override the default sentence-transformers model name.

    Example::

        from parser import ResumeParser
        from job_matching import JobMatcher

        resume  = ResumeParser().parse("resume.pdf")
        matcher = JobMatcher()
        result  = matcher.match(resume, jd_text="<raw job description>")
        print(result.model_dump_clean())
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self._engine     = EmbeddingEngine(model_name=model_name)
        self._normalizer = SkillNormalizer()
        self._jd_parser  = JDParser()
        self._similarity = SimilarityCalculator(self._engine)
        self._explainer  = MatchExplainer()
        self._ranker     = CandidateRanker()

    # ── Primary Entry Points ───────────────────────────────────────────────────

    def match(
        self,
        resume: Resume,
        jd: Optional[JobDescription] = None,
        *,
        jd_text:    str = "",
        jd_title:   str = "",
        jd_company: str = "",
    ) -> MatchResult:
        """
        Score a single resume against a job description.

        Provide either a pre-parsed JobDescription object or raw text via
        the ``jd_text`` keyword argument (the parser will handle the rest).

        Args:
            resume:     Parsed Resume object from the parser module.
            jd:         Pre-parsed JobDescription (takes precedence over jd_text).
            jd_text:    Raw job description text (used when jd is not provided).
            jd_title:   Job title hint passed to the JD parser.
            jd_company: Company name hint passed to the JD parser.

        Returns:
            MatchResult with overall score, component breakdown, matched /
            missing skills, and ranked recommendations.

        Raises:
            JobMatchingException: On any pipeline failure.
        """
        resolved_jd = self._resolve_jd(jd, jd_text, jd_title, jd_company)
        logger.info(
            "Matching resume '%s' against JD '%s'.",
            resume.contact.full_name,
            resolved_jd.title,
        )

        try:
            (
                overall_score,
                breakdown,
                req_matches,
                pref_matches,
                resume_norm,
                jd_req_norm,
                jd_pref_norm,
            ) = self._run_pipeline(resume, resolved_jd)

            missing_required  = self._explainer.get_missing_skills(
                jd_req_norm, req_matches
            )
            missing_preferred = self._explainer.get_missing_skills(
                jd_pref_norm, pref_matches
            )
            extra_skills      = self._explainer.get_extra_skills(
                resume_norm, jd_req_norm + jd_pref_norm
            )
            experience_gap    = self._explainer.experience_gap_narrative(resume, resolved_jd)
            education_gap     = self._explainer.education_gap_narrative(resume, resolved_jd)

            match_rating  = self._explainer.get_match_rating(overall_score)
            strengths     = self._explainer.identify_strengths(
                resume, resolved_jd, overall_score, breakdown,
                req_matches, pref_matches,
            )
            gaps          = self._explainer.identify_gaps(
                missing_required, missing_preferred,
                experience_gap, education_gap, breakdown,
            )
            recommendations = self._explainer.generate_recommendations(
                resume, resolved_jd, missing_required, missing_preferred,
                experience_gap, education_gap, overall_score, breakdown,
            )
            explanation   = self._explainer.build_explanation(
                overall_score, match_rating, req_matches,
                missing_required, experience_gap, breakdown, resolved_jd,
            )

            return MatchResult(
                overall_score=overall_score,
                match_rating=match_rating,
                score_breakdown=breakdown,
                matched_required_skills=req_matches,
                matched_preferred_skills=pref_matches,
                missing_required_skills=missing_required,
                missing_preferred_skills=missing_preferred,
                extra_skills=extra_skills,
                experience_gap=experience_gap,
                education_gap=education_gap,
                strengths=strengths,
                gaps=gaps,
                recommendations=recommendations,
                match_explanation=explanation,
            )

        except JobMatchingException:
            raise
        except Exception as exc:
            raise JobMatchingException(
                f"Unexpected failure during match for '{resume.contact.full_name}': {exc}"
            ) from exc

    def rank_candidates(
        self,
        resumes: List[Resume],
        jd: Optional[JobDescription] = None,
        *,
        jd_text:    str = "",
        jd_title:   str = "",
        jd_company: str = "",
    ) -> RankingResult:
        """
        Score and rank a pool of resumes against a single job description.

        Args:
            resumes:    List of parsed Resume objects.
            jd:         Pre-parsed JobDescription (takes precedence over jd_text).
            jd_text:    Raw job description text.
            jd_title:   Job title hint.
            jd_company: Company name hint.

        Returns:
            RankingResult with candidates sorted by descending match score.

        Raises:
            JobMatchingException: On any pipeline failure.
        """
        resolved_jd = self._resolve_jd(jd, jd_text, jd_title, jd_company)
        logger.info(
            "Ranking %d candidates for JD '%s'.", len(resumes), resolved_jd.title
        )

        scored: List[Tuple[Resume, MatchResult]] = []
        for resume in resumes:
            try:
                result = self.match(resume, jd=resolved_jd)
                scored.append((resume, result))
            except JobMatchingException as exc:
                logger.warning(
                    "Skipping candidate '%s' due to matching error: %s",
                    resume.contact.full_name, exc,
                )

        return self._ranker.rank(scored, resolved_jd)

    # ── JSON Convenience Methods ──────────────────────────────────────────────

    def match_and_return_json(
        self,
        resume: Resume,
        jd: Optional[JobDescription] = None,
        *,
        jd_text:    str = "",
        jd_title:   str = "",
        jd_company: str = "",
    ) -> Dict:
        """Return the MatchResult as a JSON-serialisable dictionary."""
        result = self.match(resume, jd, jd_text=jd_text, jd_title=jd_title, jd_company=jd_company)
        return result.model_dump_clean()

    def rank_and_return_json(
        self,
        resumes: List[Resume],
        jd: Optional[JobDescription] = None,
        *,
        jd_text:    str = "",
        jd_title:   str = "",
        jd_company: str = "",
    ) -> Dict:
        """Return the RankingResult as a JSON-serialisable dictionary."""
        result = self.rank_candidates(resumes, jd, jd_text=jd_text, jd_title=jd_title, jd_company=jd_company)
        return result.model_dump_clean()

    def match_and_save_json(
        self,
        resume: Resume,
        filepath: str,
        jd: Optional[JobDescription] = None,
        *,
        jd_text:    str = "",
        jd_title:   str = "",
        jd_company: str = "",
    ) -> Dict:
        """
        Run a match and persist the result to a JSON file.

        The parent directory is created automatically if it does not exist.

        Returns the same dict that was written to disk.
        """
        data = self.match_and_return_json(
            resume, jd, jd_text=jd_text, jd_title=jd_title, jd_company=jd_company
        )
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        logger.info("Match result saved to %s", out_path)
        return data

    # ── Internals ──────────────────────────────────────────────────────────────

    def _resolve_jd(
        self,
        jd: Optional[JobDescription],
        jd_text: str,
        jd_title: str,
        jd_company: str,
    ) -> JobDescription:
        """Return the supplied JD object or parse one from raw text."""
        if jd is not None:
            return jd
        if not jd_text:
            raise JobMatchingException(
                "Provide either a JobDescription object or non-empty jd_text."
            )
        return self._jd_parser.parse(jd_text, title=jd_title, company=jd_company)

    def _run_pipeline(
        self,
        resume: Resume,
        jd: JobDescription,
    ) -> Tuple:
        """
        Execute the normalisation + similarity pipeline for one resume.

        Returns a 7-tuple:
          (overall_score, breakdown, req_matches, pref_matches,
           resume_norm, jd_req_norm, jd_pref_norm)
        """
        resume_norm   = self._normalizer.normalize_list(resume.skills or [])
        jd_req_norm   = self._normalizer.normalize_list(jd.required_skills)
        jd_pref_norm  = self._normalizer.normalize_list(jd.preferred_skills)

        overall_score, breakdown, req_matches, pref_matches = (
            self._similarity.compute(
                resume, jd,
                resume_skills_normalised=resume_norm,
                jd_required_normalised=jd_req_norm,
                jd_preferred_normalised=jd_pref_norm,
            )
        )

        return (
            overall_score, breakdown,
            req_matches, pref_matches,
            resume_norm, jd_req_norm, jd_pref_norm,
        )
