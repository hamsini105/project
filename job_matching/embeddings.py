"""
Sentence embedding generation and caching.

Wraps sentence-transformers with:
  - Lazy model loading (no startup penalty until embeddings are first needed).
  - In-process LRU memoisation keyed on normalised text.
  - Graceful error surfacing when the optional dependency is absent.
"""

from __future__ import annotations

import functools
import hashlib
import logging
from typing import TYPE_CHECKING, List, Sequence

import numpy as np

from job_matching.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_CACHE_SIZE,
    EMBEDDING_MAX_SEQ_LENGTH,
    EMBEDDING_MODEL_NAME,
)
from job_matching.exceptions import EmbeddingException

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def _require_sentence_transformers() -> None:
    """Raise a descriptive error when sentence-transformers is not installed."""
    try:
        import sentence_transformers  # noqa: F401
    except ImportError as exc:
        raise EmbeddingException(
            "sentence-transformers is required for semantic matching. "
            "Install it with: pip install sentence-transformers"
        ) from exc


class EmbeddingEngine:
    """
    Generates and caches sentence embeddings using Sentence Transformers.

    Embedding vectors are stored in a bounded LRU cache keyed by a SHA-256
    digest of the input text.  This avoids re-encoding identical strings
    (e.g. the same JD analysed against many candidates) without unbounded
    memory growth.

    Thread safety: the underlying SentenceTransformer model is not
    thread-safe by default.  In concurrent environments, instantiate one
    EmbeddingEngine per thread or protect calls with a lock.

    Usage::

        engine = EmbeddingEngine()
        vec = engine.encode("Senior Python Engineer with Django experience")
        vecs = engine.encode_batch(["skill A", "skill B", "skill C"])
    """

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        max_seq_length: int = EMBEDDING_MAX_SEQ_LENGTH,
        cache_size: int = EMBEDDING_CACHE_SIZE,
    ) -> None:
        self._model_name     = model_name
        self._max_seq_length = max_seq_length
        self._cache_size     = cache_size
        self._model: "SentenceTransformer | None" = None

        # LRU cache is built once per instance when encode() is first called.
        # We use a dict as an ordered (Python 3.7+) bounded deque for simplicity.
        self._cache: dict[str, np.ndarray] = {}

    # ── Public API ─────────────────────────────────────────────────────────────

    def encode(self, text: str) -> np.ndarray:
        """
        Return a 1-D unit-normalised embedding vector for the given text.

        Args:
            text: Input string.  Empty strings return a zero vector.

        Returns:
            numpy float32 array of shape (embedding_dim,).

        Raises:
            EmbeddingException: On model load failure or encoding error.
        """
        if not text or not text.strip():
            return self._zero_vector()

        cache_key = _digest(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        model = self._get_model()
        try:
            vector: np.ndarray = model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingException(
                f"Failed to encode text (first 80 chars): {text[:80]!r}"
            ) from exc

        self._evict_if_full()
        self._cache[cache_key] = vector
        return vector

    def encode_batch(self, texts: Sequence[str]) -> List[np.ndarray]:
        """
        Encode a sequence of texts, returning one vector per input.

        Texts already present in the cache are not re-encoded.  The
        remaining texts are batched and sent to the model in one call.

        Args:
            texts: Sequence of input strings.

        Returns:
            List of float32 numpy arrays in the same order as the input.
        """
        results: List[np.ndarray | None] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts:   List[str] = []

        for idx, text in enumerate(texts):
            if not text or not text.strip():
                results[idx] = self._zero_vector()
                continue
            key = _digest(text)
            if key in self._cache:
                results[idx] = self._cache[key]
            else:
                uncached_indices.append(idx)
                uncached_texts.append(text)

        if uncached_texts:
            model = self._get_model()
            try:
                vectors: np.ndarray = model.encode(
                    uncached_texts,
                    batch_size=EMBEDDING_BATCH_SIZE,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
            except Exception as exc:
                raise EmbeddingException(
                    f"Batch encoding failed for {len(uncached_texts)} texts."
                ) from exc

            for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                vec = vectors[i]
                self._evict_if_full()
                self._cache[_digest(text)] = vec
                results[idx] = vec

        return results  # type: ignore[return-value]  # all slots filled above

    # ── Internals ──────────────────────────────────────────────────────────────

    def _get_model(self) -> "SentenceTransformer":
        """Lazily load the sentence transformer model on first use."""
        if self._model is None:
            _require_sentence_transformers()
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self._model_name)
            try:
                self._model = SentenceTransformer(self._model_name)
                self._model.max_seq_length = self._max_seq_length
                logger.info("Embedding model loaded successfully.")
            except Exception as exc:
                raise EmbeddingException(
                    f"Could not load embedding model '{self._model_name}': {exc}"
                ) from exc
        return self._model

    def _zero_vector(self) -> np.ndarray:
        """Return a zero vector matching the model's output dimension."""
        if self._model is None:
            # Return a sensible default before model is loaded
            return np.zeros(384, dtype=np.float32)
        dim = self._model.get_sentence_embedding_dimension()
        return np.zeros(dim, dtype=np.float32)

    def _evict_if_full(self) -> None:
        """Remove the oldest entry when the cache is at capacity."""
        if len(self._cache) >= self._cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _digest(text: str) -> str:
    """SHA-256 hex digest of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1-D vectors.

    Both vectors are assumed to be already unit-normalised (as produced by
    EmbeddingEngine.encode()), so this reduces to a dot product.  We still
    guard against zero-vectors to avoid NaN.

    Returns:
        Similarity in [-1, 1]; clamped to [0, 1] for practical use.
    """
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    sim = float(np.dot(a, b) / (norm_a * norm_b))
    return max(0.0, min(1.0, sim))
