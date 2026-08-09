"""Local embedding-model service for document ingestion."""

import logging
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the configured local model once per application process."""
    logger.info("[Embedding] Loading local model '%s'.", config.EMBEDDING_MODEL)
    model = SentenceTransformer(config.EMBEDDING_MODEL)
    dimensions = model.get_sentence_embedding_dimension()
    if dimensions != config.EMBEDDING_DIMENSIONS:
        raise ValueError(
            "Configured EMBEDDING_DIMENSIONS does not match the model output: "
            f"expected {config.EMBEDDING_DIMENSIONS}, got {dimensions}."
        )
    return model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return normalized embeddings for non-empty document chunks."""
    if not texts:
        return []

    logger.info("[Embedding] Generating embeddings for %d chunks.", len(texts))
    vectors = _get_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_text(text: str) -> List[float]:
    """Embed one non-empty query using the same model as document chunks."""
    if not text or not text.strip():
        raise ValueError("Text to embed must not be empty.")
    return embed_texts([text])[0]
