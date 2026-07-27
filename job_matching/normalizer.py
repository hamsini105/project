"""
Skill normalisation utilities.

Converts raw skill strings (from resumes or JDs) to a canonical lowercase
form so that "JS", "react.js", and "ReactJS" all resolve to the same token
before embedding or exact-match comparison.
"""

from __future__ import annotations

import logging
import re
from typing import List

from job_matching.config import SKILL_ALIASES
from job_matching.exceptions import NormalizationException

logger = logging.getLogger(__name__)

# Normalise whitespace and strip surrounding non-alphanum characters in one pass
_WHITESPACE_RE = re.compile(r"\s+")
_STRIP_CHARS = str.maketrans("", "", "\"'()[]{}")


class SkillNormalizer:
    """
    Normalises skill strings to a canonical representation.

    Normalisation steps (applied in order):
      1. Strip surrounding punctuation and quotes.
      2. Collapse internal whitespace.
      3. Lowercase.
      4. Resolve known aliases (e.g. "js" → "javascript").

    The normaliser is stateless; a single instance can be shared safely
    across threads.
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def normalize(self, skill: str) -> str:
        """
        Normalise a single skill string.

        Args:
            skill: Raw skill text, e.g. "ReactJS", "node.JS", "ML".

        Returns:
            Canonical skill string, e.g. "react", "node.js", "machine learning".

        Raises:
            NormalizationException: If the input cannot be processed.
        """
        if not isinstance(skill, str):
            raise NormalizationException(
                f"Expected a string skill, got {type(skill).__name__}: {skill!r}"
            )

        clean = self._clean(skill)
        if not clean:
            return ""

        resolved = SKILL_ALIASES.get(clean, clean)
        logger.debug("Normalized skill %r → %r", skill, resolved)
        return resolved

    def normalize_list(self, skills: List[str]) -> List[str]:
        """
        Normalise a list of skills, silently dropping empty results.

        Args:
            skills: List of raw skill strings.

        Returns:
            Deduplicated list of normalised skill strings preserving
            first-seen ordering.
        """
        seen: dict[str, None] = {}
        for raw in skills:
            try:
                normalised = self.normalize(raw)
            except NormalizationException as exc:
                logger.warning("Skipping skill that could not be normalised: %s", exc)
                continue
            if normalised:
                seen[normalised] = None  # order-preserving dedup via dict key

        return list(seen)

    # ── Internals ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clean(raw: str) -> str:
        """Strip, transliterate punctuation, collapse whitespace, lowercase."""
        cleaned = raw.translate(_STRIP_CHARS)
        cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip().lower()
        return cleaned
