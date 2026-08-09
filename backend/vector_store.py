"""Persistent ChromaDB storage for embedded document chunks."""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence

import chromadb

import config
import embedding_service

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


def replace_document_chunks(document_id: int, filename: str, chunks: List[str]) -> int:
    """Embed and replace every vector belonging to one document.

    Embeddings are generated before existing vectors are removed.  Replacing
    the complete document set prevents stale higher-index chunks when a
    reprocessing run produces fewer chunks.
    """
    if not chunks:
        raise ValueError("Cannot store an empty chunk list.")

    embeddings = embedding_service.embed_texts(chunks)
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


def has_indexed_chunks() -> bool:
    """Return whether the persistent collection currently contains vectors."""
    return _get_collection().count() > 0


def search_chunks(
    query_embedding: List[float],
    top_k: int,
    document_ids: Optional[Sequence[int]] = None,
) -> List[VectorSearchResult]:
    """Return nearest stored chunks without exposing ChromaDB's raw response."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_kwargs: Dict[str, Any] = {}
    if document_ids:
        # The optional filter is intentionally internal for now. It keeps the
        # retrieval component ready for later document/user scoping.
        query_kwargs["where"] = {"document_id": {"$in": list(document_ids)}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        **query_kwargs,
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
