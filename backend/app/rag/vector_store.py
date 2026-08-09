"""Persistent ChromaDB storage for embedded document chunks."""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional

import chromadb

from app.core import config
from app.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VectorSearchResult:
    """Application-level representation of one ChromaDB search result."""

    text: str
    document_id: int
    filename: str
    chunk_index: int
    distance: float
    page_number: Optional[int] = None


@lru_cache(maxsize=1)
def _get_collection():
    """Return the persistent collection; embeddings are supplied explicitly."""
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIRECTORY)
    return client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        embedding_function=None,
        metadata={"hnsw:space": "cosine"},
    )


def _document_chunk_ids(collection: Any, document_id: int) -> List[str]:
    result = collection.get(where={"document_id": document_id}, include=[])
    return result.get("ids", [])


def replace_document_chunks(
    document_id: int, filename: str, user_id: int, chunks: List[str]
) -> int:
    """Embed and replace every vector belonging to one document.

    Embeddings are generated before existing vectors are removed.  Replacing
    the complete document set prevents stale higher-index chunks when a
    reprocessing run produces fewer chunks.
    """
    if not chunks:
        raise ValueError("Cannot store an empty chunk list.")

    embeddings = embed_texts(chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("Embedding service returned an unexpected vector count.")

    collection = _get_collection()
    existing_ids = _document_chunk_ids(collection, document_id)
    if existing_ids:
        logger.info(
            "[VectorStore] Replacing %d existing vectors for document_id=%d.",
            len(existing_ids),
            document_id,
        )
        collection.delete(ids=existing_ids)

    ids = [f"doc_{document_id}_chunk_{index}" for index in range(len(chunks))]
    metadata: List[Dict[str, Any]] = [
        {
            "user_id": user_id,
            "document_id": document_id,
            "filename": filename,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    logger.info(
        "[VectorStore] Storing %d vectors for document_id=%d in '%s'.",
        len(ids), document_id, config.CHROMA_COLLECTION_NAME,
    )
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadata)
    return len(ids)


def delete_document_chunks(document_id: int) -> int:
    """Delete all vectors associated with a document or raise on failure."""
    collection = _get_collection()
    ids = _document_chunk_ids(collection, document_id)
    if ids:
        collection.delete(ids=ids)
    logger.info("[VectorStore] Deleted %d vectors for document_id=%d.", len(ids), document_id)
    return len(ids)


def has_indexed_chunks(user_id: int) -> bool:
    """Return whether this user has any persistent, searchable chunk vectors."""
    result = _get_collection().get(where={"user_id": user_id}, include=[], limit=1)
    return bool(result.get("ids"))


def search_chunks(
    query_embedding: List[float],
    top_k: int,
    user_id: int,
) -> List[VectorSearchResult]:
    """Return nearest stored chunks without exposing ChromaDB's raw response."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        where={"user_id": user_id},
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    search_results: List[VectorSearchResult] = []

    for text, metadata, distance in zip(documents, metadatas, distances):
        if not text or not metadata:
            continue
        page_number = metadata.get("page_number")
        search_results.append(
            VectorSearchResult(
                text=text,
                document_id=int(metadata["document_id"]),
                filename=str(metadata["filename"]),
                chunk_index=int(metadata["chunk_index"]),
                distance=float(distance),
                page_number=int(page_number) if page_number is not None else None,
            )
        )

    logger.info("[VectorStore] Retrieved %d candidate chunks.", len(search_results))
    return search_results
