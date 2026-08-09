"""Pure functions for RAG evaluation metrics (Retrieval and Generation)."""

from typing import Any


def source_key(source: dict[str, Any]) -> tuple[str, int | None]:
    """Extract (filename, chunk_index) key for source matching."""
    return source["filename"], source.get("chunk_index")


def matches_expected(source: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Check if retrieved source matches expected document and optional chunk index."""
    if source["filename"] != expected["filename"]:
        return False
    expected_chunk = expected.get("chunk_index")
    return expected_chunk is None or source.get("chunk_index") == expected_chunk


def recall_at_k(retrieved_sources: list[dict[str, Any]], expected_sources: list[dict[str, Any]]) -> float | None:
    """Recall@K: Ratio of expected sources retrieved within top K.

    Formula: |Retrieved Relevant Sources| / |Expected Sources|
    """
    if not expected_sources:
        return None
    relevant_retrieved = [
        source for source in retrieved_sources
        if any(matches_expected(source, expected) for expected in expected_sources)
    ]
    unique_relevant = {_source_key for _source_key in (source_key(s) for s in relevant_retrieved)}
    return len(unique_relevant) / len(expected_sources)


def precision_at_k(retrieved_sources: list[dict[str, Any]], expected_sources: list[dict[str, Any]]) -> float:
    """Precision@K: Ratio of retrieved top K sources that are expected.

    Formula: |Retrieved Relevant Sources| / K (where K = len(retrieved_sources))
    """
    if not retrieved_sources:
        return 0.0
    relevant_count = sum(
        1 for source in retrieved_sources
        if any(matches_expected(source, expected) for expected in expected_sources)
    )
    return relevant_count / len(retrieved_sources)


def hit_rate_at_k(retrieved_sources: list[dict[str, Any]], expected_sources: list[dict[str, Any]]) -> float:
    """Hit Rate@K: 1.0 if at least one expected source appears in top K, else 0.0."""
    if not expected_sources:
        return 1.0 if not retrieved_sources else 0.0
    return 1.0 if any(
        any(matches_expected(source, expected) for expected in expected_sources)
        for source in retrieved_sources
    ) else 0.0


def mrr_at_k(retrieved_sources: list[dict[str, Any]], expected_sources: list[dict[str, Any]]) -> float:
    """Mean Reciprocal Rank @ K: 1 / (rank of first relevant source).

    Returns 1.0 / rank (1-indexed) if found, or 0.0 if not found in top K.
    """
    if not expected_sources:
        return 0.0
    for rank, source in enumerate(retrieved_sources, start=1):
        if any(matches_expected(source, expected) for expected in expected_sources):
            return 1.0 / rank
    return 0.0


def deterministic_answer_relevance(answer: str, terms: list[str]) -> tuple[int, float]:
    """Deterministic coverage of expected reference terms in the generated answer.

    Returns:
        (score_0_to_2, coverage_ratio)
        Score 2: 100% coverage
        Score 1: Partial coverage (> 0%)
        Score 0: 0% coverage
    """
    if not terms:
        return 2, 1.0
    normalized = answer.lower()
    matches = sum(term.lower() in normalized for term in terms)
    coverage = matches / len(terms)
    score = 2 if coverage == 1.0 else 1 if coverage > 0.0 else 0
    return score, round(coverage, 4)


def deterministic_grounded_support(answer: str, context_text: str, terms: list[str]) -> tuple[int, float]:
    """Deterministic proxy checking whether expected terms appear in both answer and context.

    Returns:
        (score_0_to_2, grounding_term_coverage)
    """
    if not terms:
        return 2, 1.0
    ctx_norm = context_text.lower()
    matches = sum(term.lower() in ctx_norm for term in terms)
    coverage = matches / len(terms)
    ans_score, ans_cov = deterministic_answer_relevance(answer, terms)
    score = 2 if ans_score == 2 and coverage == 1.0 else 1 if ans_cov > 0 and coverage > 0 else 0
    return score, round(coverage, 4)


def unanswerable_safety(has_relevant_context: bool, sources_returned: list[Any]) -> tuple[int, bool]:
    """Evaluates safety on unanswerable questions.

    Returns (2, True) if system correctly reported no relevant context and returned no sources.
    Returns (0, False) if system incorrectly claimed relevant context or fabricated sources.
    """
    is_safe = (not has_relevant_context) and (not sources_returned)
    return (2 if is_safe else 0), is_safe
