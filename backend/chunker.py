"""Split extracted document text into bounded, overlapping semantic chunks."""

import re
from typing import List
import config


def chunk_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> List[str]:
    """
    Split *text* into overlapping chunks, preferring paragraph, sentence, and
    word boundaries (in that order) near the configured character limit.

    Parameters
    ----------
    text         : The full extracted document text.
    chunk_size   : Maximum number of characters per chunk.
    chunk_overlap: Number of characters shared between adjacent chunks.

    Returns
    -------
    A list of non-empty text chunks.
    """
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")
    if chunk_overlap < 0:
        raise ValueError(f"chunk_overlap must be >= 0, got {chunk_overlap}")
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be < chunk_size ({chunk_size})"
        )

    # Preserve source text while normalising platform-specific newlines.  The
    # boundary search is character based, so ``chunk_size`` remains a clear,
    # inexpensive configuration baseline rather than a claim about tokens.
    source = text.replace("\r\n", "\n").strip()
    chunks: List[str] = []
    start = 0

    while start < len(source):
        maximum_end = min(start + chunk_size, len(source))
        end = _find_end_boundary(source, start, maximum_end)
        chunk = source[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(source):
            break

        # Begin the next chunk close to the requested overlap but at a word
        # boundary. Moving forward here avoids beginning a chunk mid-word.
        proposed_start = max(start + 1, end - chunk_overlap)
        start = _find_start_boundary(source, proposed_start, end)

    return chunks


def _find_end_boundary(text: str, start: int, maximum_end: int) -> int:
    """Find the best natural end boundary at or before ``maximum_end``."""
    if maximum_end == len(text):
        return maximum_end

    # Avoid a very short fragment just to honour a nearby boundary.  If no
    # useful boundary exists in the latter half of the window, force progress.
    minimum_end = start + max(1, (maximum_end - start) // 2)
    window = text[minimum_end:maximum_end]

    for pattern in (r"\n\s*\n", r"(?<=[.!?])\s+", r"\s+"):
        matches = list(re.finditer(pattern, window))
        if matches:
            return minimum_end + matches[-1].end()
    return maximum_end


def _find_start_boundary(text: str, proposed_start: int, previous_end: int) -> int:
    """Move a proposed overlap start forward to a word boundary safely."""
    if proposed_start >= previous_end:
        return previous_end

    boundary = re.search(r"\s+", text[proposed_start:previous_end])
    if boundary:
        return proposed_start + boundary.end()
    return proposed_start
