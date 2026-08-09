"""Build a bounded, source-labelled context for the RAG prompt."""

from dataclasses import dataclass
from typing import List

import config
from retrieval_service import RetrievedChunk


@dataclass(frozen=True)
class ContextBuildResult:
    context: str
    chunks: List[RetrievedChunk]


def build_context(chunks: List[RetrievedChunk]) -> ContextBuildResult:
    """Keep highest-ranked chunks that fit within the configured character cap."""
    parts: List[str] = []
    included: List[RetrievedChunk] = []
    used_length = 0

    for index, chunk in enumerate(chunks, start=1):
        source_label = (
            f"[Source {index}: {chunk.filename}; document_id={chunk.document_id}; "
            f"chunk_index={chunk.chunk_index}]"
        )
        candidate = f"{source_label}\n{chunk.text}\n"
        if used_length + len(candidate) > config.MAX_CONTEXT_LENGTH:
            break
        parts.append(candidate)
        included.append(chunk)
        used_length += len(candidate)

    return ContextBuildResult(context="\n".join(parts).strip(), chunks=included)
