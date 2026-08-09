"""Document-processing orchestration for Phase 3 ingestion."""

import logging

import chunker
import extractor
import vector_store

logger = logging.getLogger(__name__)


def index_document(document_id: int, filename: str, file_path: str, file_type: str) -> str:
    """Extract, chunk, embed, and replace all vectors for one document."""
    logger.info("[Ingestion] document_id=%d processing started.", document_id)
    extracted_text = extractor.extract_text(file_path, file_type)
    logger.info(
        "[Ingestion] document_id=%d extraction completed (%d characters).",
        document_id,
        len(extracted_text),
    )

    chunks = chunker.chunk_text(extracted_text)
    if not chunks:
        raise ValueError("No indexable text chunks were produced from the document.")
    logger.info("[Ingestion] document_id=%d produced %d chunks.", document_id, len(chunks))

    stored = vector_store.replace_document_chunks(document_id, filename, chunks)
    logger.info("[Ingestion] document_id=%d stored %d vectors.", document_id, stored)
    return extracted_text
