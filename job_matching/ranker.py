"""
Candidate ranking engine.

Accepts a list of (Resume, MatchResult) pairs and produces a sorted
RankingResult with 1-based ranks.  Ties are broken by candidate name
(alphabetical) for deterministic ordering.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from parser.models import Resume

from job_matching.config import MAX_CANDIDATES_PER_RANKING
from job_matching.exceptions import RankingException
from job_matching.models import (
    CandidateMatch,
    JobDescription,
    MatchRating,
    MatchResult,
    RankingResult,
)

logger = logging.getLogger(__name__)


class CandidateRanker:
    """
    Ranks a pool of pre-scored candidates for a single job description.

    Ranking is purely by overall_score (descending).  The ranker does not
    perform any scoring itself — it expects fully-computed MatchResult objects
    from the JobMatcher.

    Usage::

        ranker  = CandidateRanker()
        results = ranker.rank(scored_candidates, jd)
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def rank(
        self,
        scored_candidates: List[Tuple[Resume, MatchResult]],
        jd: JobDescription,
    ) -> RankingResult:
        """
        Sort and rank candidates for the given job description.

        Args:
            scored_candidates: List of (Resume, MatchResult) pairs.
            jd:                The job description used for all matches.

        Returns:
            RankingResult with ranked_candidates in descending score order.

        Raises:
            RankingException: If the candidate list is empty or exceeds the
                              configured maximum.
        """
        if not scored_candidates:
            raise RankingException("Cannot rank an empty candidate pool.")

        if len(scored_candidates) > MAX_CANDIDATES_PER_RANKING:
            raise RankingException(
                f"Candidate pool size {len(scored_candidates)} exceeds the "
                f"configured maximum of {MAX_CANDIDATES_PER_RANKING}. "
                "Split the request into smaller batches."
            )

        logger.info(
            "Ranking %d candidates for '%s'.", len(scored_candidates), jd.title
        )

        try:
            # Stable sort: primary key = score (desc), secondary = name (asc)
            sorted_pairs = sorted(
                scored_candidates,
                key=lambda pair: (-pair[1].overall_score, pair[0].contact.full_name),
            )

            ranked: List[CandidateMatch] = []
            for rank, (resume, match_result) in enumerate(sorted_pairs, start=1):
                ranked.append(
                    CandidateMatch(
                        rank=rank,
                        candidate_name=resume.contact.full_name,
                        candidate_email=(
                            str(resume.contact.email) if resume.contact.email else None
                        ),
                        overall_score=match_result.overall_score,
                        match_rating=match_result.match_rating,
                        match_result=match_result,
                    )
                )
                logger.debug(
                    "Rank %d: %s — %.1f (%s)",
                    rank,
                    resume.contact.full_name,
                    match_result.overall_score,
                    match_result.match_rating.value,
                )

            return RankingResult(
                job_title=jd.title,
                company=jd.company,
                total_candidates=len(ranked),
                ranked_candidates=ranked,
            )

        except RankingException:
            raise
        except Exception as exc:
            raise RankingException(
                f"Unexpected error during candidate ranking: {exc}"
            ) from exc

    # ── Convenience Queries ───────────────────────────────────────────────────

    @staticmethod
    def top_n(result: RankingResult, n: int) -> List[CandidateMatch]:
        """Return the top-n candidates from a RankingResult."""
        return result.ranked_candidates[:n]

    @staticmethod
    def filter_by_rating(
        result: RankingResult, minimum_rating: MatchRating
    ) -> List[CandidateMatch]:
        """
        Return only candidates whose rating is at or above minimum_rating.

        Rating order (ascending): Poor < Fair < Good < Excellent.
        """
        _order = {
            MatchRating.POOR:      0,
            MatchRating.FAIR:      1,
            MatchRating.GOOD:      2,
            MatchRating.EXCELLENT: 3,
        }
        min_ordinal = _order[minimum_rating]
        return [
            c for c in result.ranked_candidates
            if _order.get(c.match_rating, 0) >= min_ordinal
        ]
