"""
Similarity calculation engine.

Computes multi-dimensional match scores between a resume and a job description:

  ┌─────────────────────┬────────────────────────────────────────────────────┐
  │ Dimension           │ Method                                              │
  ├─────────────────────┼────────────────────────────────────────────────────┤
  │ skills_match        │ Exact + alias + semantic per-skill matching (0–100) │
  │ semantic_similarity │ Cosine similarity of full-text embeddings (0–100)   │
  │ experience_match    │ Rule-based gap calculation (0–100)                  │
  │ education_match     │ Ordinal education level comparison (0–100)          │
  └─────────────────────┴────────────────────────────────────────────────────┘

Each dimension is computed independently so callers can inspect breakdown
scores and the overall weighted score separately.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from parser.models import ExperienceEntry, Resume

from job_matching.config import (
    EDUCATION_LEVELS,
    SCORING_WEIGHTS,
    SEMANTIC_SKILL_MATCH_THRESHOLD,
    STRONG_SKILL_MATCH_THRESHOLD,
)
from job_matching.embeddings import EmbeddingEngine, cosine_similarity
from job_matching.exceptions import SimilarityException
from job_matching.models import JobDescription, MatchType, ScoreBreakdown, SkillMatch

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """
    Computes all similarity dimensions between a Resume and a JobDescription.

    A shared EmbeddingEngine can be injected at construction time so a single
    model instance is reused across many calculations.

    Usage::

        engine = EmbeddingEngine()
        calc   = SimilarityCalculator(engine)

        overall, breakdown, req_matches, pref_matches = calc.compute(resume, jd)
    """

    def __init__(self, embedding_engine: EmbeddingEngine) -> None:
        self._engine = embedding_engine

    # ── Public API ─────────────────────────────────────────────────────────────

    def compute(
        self,
        resume: Resume,
        jd: JobDescription,
        resume_skills_normalised: List[str],
        jd_required_normalised:   List[str],
        jd_preferred_normalised:  List[str],
    ) -> Tuple[float, ScoreBreakdown, List[SkillMatch], List[SkillMatch]]:
        """
        Compute the full match between resume and job description.

        Args:
            resume:                   Parsed resume object.
            jd:                       Parsed job description.
            resume_skills_normalised: Normalised resume skill list.
            jd_required_normalised:   Normalised JD required skills.
            jd_preferred_normalised:  Normalised JD preferred skills.

        Returns:
            Tuple of:
              - overall_score (float 0–100)
              - ScoreBreakdown (all component scores 0–100)
              - List[SkillMatch] for required skills
              - List[SkillMatch] for preferred skills

        Raises:
            SimilarityException: On unexpected computation failure.
        """
        try:
            req_matches, req_score   = self._match_skill_set(
                resume_skills_normalised, jd_required_normalised
            )
            pref_matches, pref_score = self._match_skill_set(
                resume_skills_normalised, jd_preferred_normalised
            )

            # Blend required (70 %) and preferred (30 %) skill scores
            skills_score = req_score * 0.70 + pref_score * 0.30

            semantic_score  = self._semantic_text_similarity(resume, jd)
            experience_score = self._experience_match_score(resume, jd)
            education_score  = self._education_match_score(resume, jd)

            breakdown = ScoreBreakdown(
                skills_match=round(skills_score, 2),
                semantic_similarity=round(semantic_score, 2),
                experience_match=round(experience_score, 2),
                education_match=round(education_score, 2),
            )

            overall = self._weighted_overall(breakdown)
            logger.debug(
                "Similarity scores — skills: %.1f, semantic: %.1f, "
                "experience: %.1f, education: %.1f → overall: %.1f",
                skills_score, semantic_score,
                experience_score, education_score, overall,
            )
            return overall, breakdown, req_matches, pref_matches

        except SimilarityException:
            raise
        except Exception as exc:
            raise SimilarityException(
                f"Similarity computation failed: {exc}"
            ) from exc

    # ── Skill Matching ─────────────────────────────────────────────────────────

    def _match_skill_set(
        self,
        resume_skills: List[str],
        jd_skills:     List[str],
    ) -> Tuple[List[SkillMatch], float]:
        """
        Match resume skills against a JD skill list using a three-pass strategy:
          1. Exact / alias match (confidence 1.0)
          2. Semantic match via embeddings (confidence = cosine similarity)

        Returns the list of SkillMatch records and a coverage score 0–100.
        """
        if not jd_skills:
            return [], 100.0  # No requirement → full score

        matches:      List[SkillMatch] = []
        unmatched_jd: List[str]        = []

        # Pass 1 — exact or alias match
        for jd_skill in jd_skills:
            hit = self._exact_match(jd_skill, resume_skills)
            if hit:
                match_type = MatchType.EXACT if hit == jd_skill else MatchType.ALIAS
                matches.append(SkillMatch(
                    jd_skill=jd_skill,
                    resume_skill=hit,
                    match_type=match_type,
                    confidence=1.0,
                ))
            else:
                unmatched_jd.append(jd_skill)

        # Pass 2 — semantic match for remaining JD skills
        if unmatched_jd and resume_skills:
            semantic_hits = self._semantic_match(unmatched_jd, resume_skills)
            for jd_skill, resume_skill, sim in semantic_hits:
                matches.append(SkillMatch(
                    jd_skill=jd_skill,
                    resume_skill=resume_skill,
                    match_type=MatchType.SEMANTIC,
                    confidence=round(sim, 4),
                ))

        coverage = len(matches) / len(jd_skills) * 100.0
        return matches, coverage

    @staticmethod
    def _exact_match(jd_skill: str, resume_skills: List[str]) -> Optional[str]:
        """Return the resume skill that exactly matches jd_skill, or None."""
        for rs in resume_skills:
            if rs == jd_skill:
                return rs
        return None

    def _semantic_match(
        self,
        jd_skills:     List[str],
        resume_skills: List[str],
    ) -> List[Tuple[str, str, float]]:
        """
        For each unmatched JD skill, find the closest resume skill by cosine
        similarity.  Skills below SEMANTIC_SKILL_MATCH_THRESHOLD are discarded.

        Returns list of (jd_skill, resume_skill, similarity) triples.
        """
        jd_vecs     = self._engine.encode_batch(jd_skills)
        resume_vecs = self._engine.encode_batch(resume_skills)
        results:  List[Tuple[str, str, float]] = []

        for jd_skill, jd_vec in zip(jd_skills, jd_vecs):
            best_sim   = 0.0
            best_skill = ""
            for rs_skill, rs_vec in zip(resume_skills, resume_vecs):
                sim = cosine_similarity(jd_vec, rs_vec)
                if sim > best_sim:
                    best_sim   = sim
                    best_skill = rs_skill

            if best_sim >= SEMANTIC_SKILL_MATCH_THRESHOLD:
                results.append((jd_skill, best_skill, best_sim))

        return results

    # ── Semantic Text Similarity ──────────────────────────────────────────────

    def _semantic_text_similarity(
        self, resume: Resume, jd: JobDescription
    ) -> float:
        """
        Compute cosine similarity between a resume text summary and the full
        JD text.  Returns a score in 0–100.
        """
        resume_text = self._build_resume_text(resume)
        jd_text     = jd.raw_text

        if not resume_text.strip() or not jd_text.strip():
            return 0.0

        resume_vec = self._engine.encode(resume_text)
        jd_vec     = self._engine.encode(jd_text)

        return cosine_similarity(resume_vec, jd_vec) * 100.0

    @staticmethod
    def _build_resume_text(resume: Resume) -> str:
        """
        Concatenate the most informative resume fields into a single string
        for full-text embedding.
        """
        parts: List[str] = []
        if resume.summary:
            parts.append(resume.summary)
        if resume.skills:
            parts.append("Skills: " + ", ".join(resume.skills))
        if resume.experience:
            for exp in resume.experience:
                parts.append(f"{exp.position} at {exp.company}")
                if exp.description:
                    parts.extend(exp.description)
        if resume.education:
            for edu in resume.education:
                edu_str = edu.institution
                if edu.degree:
                    edu_str = f"{edu.degree}, {edu_str}"
                parts.append(edu_str)
        return " ".join(parts)

    # ── Experience Match ──────────────────────────────────────────────────────

    def _experience_match_score(
        self, resume: Resume, jd: JobDescription
    ) -> float:
        """
        Score how well the candidate's total experience meets the JD requirement.

        Rule table:
          - No JD requirement → 100
          - Candidate meets or exceeds requirement → 100
          - Candidate is within 1 year short → 80
          - Candidate is 1–2 years short → 60
          - Candidate is 2–3 years short → 40
          - Candidate is 3+ years short → 20
        """
        if jd.min_experience_years is None:
            return 100.0

        candidate_years = _total_experience_years(resume.experience or [])
        required_years  = jd.min_experience_years
        gap             = required_years - candidate_years

        if gap <= 0:
            return 100.0
        if gap <= 1:
            return 80.0
        if gap <= 2:
            return 60.0
        if gap <= 3:
            return 40.0
        return 20.0

    # ── Education Match ───────────────────────────────────────────────────────

    def _education_match_score(
        self, resume: Resume, jd: JobDescription
    ) -> float:
        """
        Compare the candidate's highest education level against the JD
        requirement using ordinal ranking from config.EDUCATION_LEVELS.
        """
        if not jd.education_level:
            return 100.0

        required_ordinal = EDUCATION_LEVELS.get(jd.education_level.lower(), 0)
        if required_ordinal == 0:
            return 100.0

        candidate_ordinal = 0
        for edu in (resume.education or []):
            if edu.degree:
                for level, ordinal in EDUCATION_LEVELS.items():
                    if level in edu.degree.lower():
                        candidate_ordinal = max(candidate_ordinal, ordinal)

        if candidate_ordinal >= required_ordinal:
            return 100.0
        if candidate_ordinal == required_ordinal - 1:
            return 60.0
        return 20.0

    # ── Overall Score ─────────────────────────────────────────────────────────

    @staticmethod
    def _weighted_overall(breakdown: ScoreBreakdown) -> float:
        """Compute weighted sum of component scores, capped at 100."""
        w = SCORING_WEIGHTS
        total = (
            breakdown.skills_match        * w["skills_match"]
            + breakdown.semantic_similarity * w["semantic_similarity"]
            + breakdown.experience_match    * w["experience_match"]
            + breakdown.education_match     * w["education_match"]
        )
        return round(min(total, 100.0), 2)


# ── Standalone Helpers ────────────────────────────────────────────────────────

def _total_experience_years(entries: List[ExperienceEntry]) -> float:
    """
    Sum the durations of all non-overlapping experience entries.

    Uses end_date or today for currently-active positions.
    """
    today = date.today()
    total_days = 0

    for entry in entries:
        start = entry.start_date
        if start is None:
            continue
        end = date.today() if (entry.is_current or entry.end_date is None) else entry.end_date
        duration = (end - start).days
        if duration > 0:
            total_days += duration

    return round(total_days / 365.25, 2)
