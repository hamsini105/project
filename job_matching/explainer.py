"""
Match explanation and insight generation.

Takes the raw numeric output from the similarity engine and produces
human-readable strengths, gap narratives, and a prioritised list of
Recommendations.  All logic is rule-based — no ML involved.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from parser.models import Resume

from job_matching.config import (
    EDUCATION_LEVELS,
    SCORE_RANGES,
    SEMANTIC_SKILL_MATCH_THRESHOLD,
    STRONG_SKILL_MATCH_THRESHOLD,
)
from job_matching.models import (
    JobDescription,
    MatchRating,
    MatchType,
    Priority,
    Recommendation,
    ScoreBreakdown,
    SkillMatch,
)
from job_matching.similarity import _total_experience_years

logger = logging.getLogger(__name__)


class MatchExplainer:
    """
    Converts numerical match data into human-readable explanations.

    All public methods are stateless and safe to call in parallel.
    """

    # ── Rating ─────────────────────────────────────────────────────────────────

    def get_match_rating(self, score: float) -> MatchRating:
        """Map a 0–100 score to a MatchRating enum value."""
        if score >= SCORE_RANGES["excellent"][0]:
            return MatchRating.EXCELLENT
        if score >= SCORE_RANGES["good"][0]:
            return MatchRating.GOOD
        if score >= SCORE_RANGES["fair"][0]:
            return MatchRating.FAIR
        return MatchRating.POOR

    # ── Skill Gaps ─────────────────────────────────────────────────────────────

    def get_missing_skills(
        self,
        jd_skills_normalised:    List[str],
        matched_skills:          List[SkillMatch],
    ) -> List[str]:
        """
        Return the JD skills that were not matched by any resume skill.

        The result list preserves the original JD ordering.
        """
        matched_jd_skills = {m.jd_skill for m in matched_skills}
        return [s for s in jd_skills_normalised if s not in matched_jd_skills]

    def get_extra_skills(
        self,
        resume_skills_normalised: List[str],
        all_jd_skills_normalised: List[str],
    ) -> List[str]:
        """
        Return resume skills not mentioned (even approximately) in the JD.

        These are surfaced as positive differentiators for the candidate.
        """
        jd_set = set(all_jd_skills_normalised)
        return [s for s in resume_skills_normalised if s not in jd_set]

    # ── Narrative Gaps ─────────────────────────────────────────────────────────

    def experience_gap_narrative(
        self,
        resume: Resume,
        jd: JobDescription,
    ) -> Optional[str]:
        """
        Return a single sentence describing the experience gap, or None if
        the candidate meets or the JD has no requirement.
        """
        if jd.min_experience_years is None:
            return None

        candidate_years = _total_experience_years(resume.experience or [])
        required        = jd.min_experience_years
        gap             = required - candidate_years

        if gap <= 0:
            return None

        max_clause = (
            f"–{jd.max_experience_years:.0f}" if jd.max_experience_years else "+"
        )
        return (
            f"Position requires {required:.0f}{max_clause} years of experience; "
            f"candidate has approximately {candidate_years:.1f} years "
            f"(gap: {gap:.1f} years)."
        )

    def education_gap_narrative(
        self,
        resume: Resume,
        jd: JobDescription,
    ) -> Optional[str]:
        """
        Return a sentence describing the education gap, or None if satisfied.
        """
        if not jd.education_level:
            return None

        required_ordinal = EDUCATION_LEVELS.get(jd.education_level.lower(), 0)
        if required_ordinal == 0:
            return None

        candidate_ordinal = 0
        candidate_level   = "not specified"
        for edu in (resume.education or []):
            if edu.degree:
                for level, ordinal in EDUCATION_LEVELS.items():
                    if level in edu.degree.lower():
                        if ordinal > candidate_ordinal:
                            candidate_ordinal = ordinal
                            candidate_level   = level

        if candidate_ordinal >= required_ordinal:
            return None

        return (
            f"Position requires at least a {jd.education_level} degree; "
            f"candidate's highest qualification is {candidate_level}."
        )

    # ── Strengths ──────────────────────────────────────────────────────────────

    def identify_strengths(
        self,
        resume: Resume,
        jd: JobDescription,
        overall_score: float,
        score_breakdown: ScoreBreakdown,
        matched_required: List[SkillMatch],
        matched_preferred: List[SkillMatch],
    ) -> List[str]:
        """
        Produce a list of human-readable strength statements.
        """
        strengths: List[str] = []

        # Skill strengths
        exact_or_alias = [
            m for m in matched_required
            if m.match_type in (MatchType.EXACT, MatchType.ALIAS)
        ]
        if exact_or_alias:
            skills_str = ", ".join(m.jd_skill for m in exact_or_alias[:5])
            suffix = f" and {len(exact_or_alias) - 5} more" if len(exact_or_alias) > 5 else ""
            strengths.append(
                f"Direct skill matches for required skills: {skills_str}{suffix}."
            )

        strong_semantic = [
            m for m in matched_required
            if m.match_type == MatchType.SEMANTIC
            and m.confidence >= STRONG_SKILL_MATCH_THRESHOLD
        ]
        if strong_semantic:
            strengths.append(
                f"Strong semantic skill coverage across "
                f"{len(strong_semantic)} additional required skill(s)."
            )

        # Experience strength
        if score_breakdown.experience_match == 100.0 and jd.min_experience_years:
            candidate_years = _total_experience_years(resume.experience or [])
            strengths.append(
                f"Meets experience requirement: "
                f"{candidate_years:.1f} years vs. {jd.min_experience_years:.0f}+ required."
            )

        # Education strength
        if score_breakdown.education_match == 100.0 and jd.education_level:
            strengths.append(
                f"Education meets or exceeds the {jd.education_level} degree requirement."
            )

        # Semantic similarity strength
        if score_breakdown.semantic_similarity >= 70.0:
            strengths.append(
                "Resume content is highly contextually relevant to the job description."
            )

        # Preferred skills coverage
        if matched_preferred:
            strengths.append(
                f"Covers {len(matched_preferred)} out of {len(jd.preferred_skills)} "
                "preferred / nice-to-have skills."
            )

        # Overall excellence
        if overall_score >= SCORE_RANGES["excellent"][0]:
            strengths.append("Overall profile is an excellent match for this position.")

        return strengths

    # ── Gaps ───────────────────────────────────────────────────────────────────

    def identify_gaps(
        self,
        missing_required: List[str],
        missing_preferred: List[str],
        experience_gap_text: Optional[str],
        education_gap_text: Optional[str],
        score_breakdown: ScoreBreakdown,
    ) -> List[str]:
        """
        Produce a concise list of gap statements for the match report.
        """
        gaps: List[str] = []

        if missing_required:
            skills_str = ", ".join(missing_required[:6])
            suffix = f" (+{len(missing_required) - 6} more)" if len(missing_required) > 6 else ""
            gaps.append(f"Missing required skills: {skills_str}{suffix}.")

        if missing_preferred:
            skills_str = ", ".join(missing_preferred[:4])
            suffix = f" (+{len(missing_preferred) - 4} more)" if len(missing_preferred) > 4 else ""
            gaps.append(f"Missing preferred skills: {skills_str}{suffix}.")

        if experience_gap_text:
            gaps.append(experience_gap_text)

        if education_gap_text:
            gaps.append(education_gap_text)

        if score_breakdown.semantic_similarity < 40.0:
            gaps.append(
                "Resume text has low contextual overlap with the job description — "
                "consider aligning language to the posting."
            )

        return gaps

    # ── Recommendations ───────────────────────────────────────────────────────

    def generate_recommendations(
        self,
        resume: Resume,
        jd: JobDescription,
        missing_required: List[str],
        missing_preferred: List[str],
        experience_gap_text: Optional[str],
        education_gap_text: Optional[str],
        overall_score: float,
        score_breakdown: ScoreBreakdown,
    ) -> List[Recommendation]:
        """
        Generate a prioritised list of actionable recommendations.

        Recommendations are deduplicated and sorted Critical → Low.
        """
        recs: List[Recommendation] = []

        recs.extend(self._skill_recommendations(missing_required, missing_preferred))
        recs.extend(self._experience_recommendations(experience_gap_text, jd))
        recs.extend(self._education_recommendations(education_gap_text, jd))
        recs.extend(self._semantic_recommendations(score_breakdown))
        recs.extend(self._general_recommendations(overall_score, resume))

        return self._sort_by_priority(recs)

    # ── Recommendation Builders ───────────────────────────────────────────────

    @staticmethod
    def _skill_recommendations(
        missing_required:  List[str],
        missing_preferred: List[str],
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []

        if missing_required:
            skill_list = ", ".join(missing_required[:5])
            recs.append(Recommendation(
                action=f"Acquire or demonstrate proficiency in: {skill_list}.",
                reason=(
                    f"{len(missing_required)} required skill(s) are absent from the resume. "
                    "ATS systems filter on exact-match keywords."
                ),
                priority=Priority.CRITICAL if len(missing_required) >= 3 else Priority.HIGH,
                category="skills",
            ))

        if missing_preferred:
            skill_list = ", ".join(missing_preferred[:4])
            recs.append(Recommendation(
                action=f"Consider adding preferred skills: {skill_list}.",
                reason=(
                    "Preferred skills differentiate candidates with otherwise similar profiles."
                ),
                priority=Priority.MEDIUM,
                category="skills",
            ))

        return recs

    @staticmethod
    def _experience_recommendations(
        experience_gap_text: Optional[str],
        jd: JobDescription,
    ) -> List[Recommendation]:
        if not experience_gap_text:
            return []
        return [Recommendation(
            action=(
                "Highlight projects, freelance work, or contributions that demonstrate "
                f"additional experience to meet the {jd.min_experience_years:.0f}+ year requirement."
            ),
            reason=experience_gap_text,
            priority=Priority.HIGH,
            category="experience",
        )]

    @staticmethod
    def _education_recommendations(
        education_gap_text: Optional[str],
        jd: JobDescription,
    ) -> List[Recommendation]:
        if not education_gap_text:
            return []
        return [Recommendation(
            action=(
                f"Consider pursuing a {jd.education_level} degree or an equivalent "
                "professional certification to meet the stated requirement."
            ),
            reason=education_gap_text,
            priority=Priority.MEDIUM,
            category="education",
        )]

    @staticmethod
    def _semantic_recommendations(score_breakdown: ScoreBreakdown) -> List[Recommendation]:
        if score_breakdown.semantic_similarity >= 50.0:
            return []
        return [Recommendation(
            action=(
                "Mirror the language and terminology from the job description in your "
                "resume summary and experience bullet points."
            ),
            reason=(
                "Low contextual overlap between resume text and job description reduces "
                "relevance scoring and risks automated rejection by ATS keyword filters."
            ),
            priority=Priority.HIGH,
            category="content",
        )]

    @staticmethod
    def _general_recommendations(
        overall_score: float,
        resume: Resume,
    ) -> List[Recommendation]:
        recs: List[Recommendation] = []

        if not resume.summary:
            recs.append(Recommendation(
                action=(
                    "Add a concise professional summary (3–5 sentences) to the top of your resume."
                ),
                reason=(
                    "A targeted summary boosts semantic similarity with the job description "
                    "and captures recruiter attention in the first few seconds."
                ),
                priority=Priority.MEDIUM,
                category="content",
            ))

        if overall_score < SCORE_RANGES["fair"][0]:
            recs.append(Recommendation(
                action=(
                    "Thoroughly review the full job description and address each "
                    "stated requirement explicitly in your resume."
                ),
                reason=(
                    f"An overall match score of {overall_score:.0f} suggests significant "
                    "gaps. Targeted revision can substantially improve ATS pass-through rates."
                ),
                priority=Priority.CRITICAL,
                category="general",
            ))

        return recs

    # ── Explanation Prose ─────────────────────────────────────────────────────

    def build_explanation(
        self,
        overall_score:    float,
        match_rating:     MatchRating,
        matched_required: List[SkillMatch],
        missing_required: List[str],
        experience_gap:   Optional[str],
        score_breakdown:  ScoreBreakdown,
        jd: JobDescription,
    ) -> str:
        """
        Compose a single coherent paragraph explaining the match result.
        """
        lines: List[str] = []

        lines.append(
            f"Overall match score: {overall_score:.1f}/100 ({match_rating.value})."
        )

        if matched_required:
            skills = ", ".join(m.jd_skill for m in matched_required[:4])
            suffix = f" among others" if len(matched_required) > 4 else ""
            lines.append(
                f"The resume directly covers {len(matched_required)} of the required skills "
                f"({skills}{suffix})."
            )

        if missing_required:
            skills = ", ".join(missing_required[:3])
            suffix = f" and {len(missing_required) - 3} more" if len(missing_required) > 3 else ""
            lines.append(
                f"{len(missing_required)} required skill(s) are not evidenced in the resume "
                f"({skills}{suffix})."
            )

        if experience_gap:
            lines.append(experience_gap)

        if score_breakdown.semantic_similarity >= 70.0:
            lines.append(
                "The overall content of the resume is contextually well-aligned with "
                "the job description."
            )
        elif score_breakdown.semantic_similarity < 40.0:
            lines.append(
                "The resume content shows limited contextual alignment with the job description."
            )

        return " ".join(lines)

    # ── Sorting ───────────────────────────────────────────────────────────────

    _PRIORITY_ORDER = {
        Priority.CRITICAL: 0,
        Priority.HIGH:     1,
        Priority.MEDIUM:   2,
        Priority.LOW:      3,
    }

    def _sort_by_priority(
        self, recs: List[Recommendation]
    ) -> List[Recommendation]:
        return sorted(recs, key=lambda r: self._PRIORITY_ORDER.get(r.priority, 99))
