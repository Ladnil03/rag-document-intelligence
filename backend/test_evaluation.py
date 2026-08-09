"""Unit tests for Phase 7 evaluation metrics, dataset parsing, and report generation."""

import json
import pytest
from pathlib import Path
from evaluation import metrics, evaluate


def test_recall_at_k_calculation():
    retrieved = [{"filename": "doc1.pdf", "chunk_index": 0}, {"filename": "doc2.pdf", "chunk_index": 1}]
    expected = [{"filename": "doc1.pdf", "chunk_index": 0}, {"filename": "doc3.pdf", "chunk_index": 0}]
    rec = metrics.recall_at_k(retrieved, expected)
    assert rec == 0.5


def test_precision_at_k_calculation():
    retrieved = [{"filename": "doc1.pdf"}, {"filename": "doc2.pdf"}]
    expected = [{"filename": "doc1.pdf"}]
    prec = metrics.precision_at_k(retrieved, expected)
    assert prec == 0.5


def test_hit_rate_at_k_calculation():
    retrieved = [{"filename": "doc1.pdf"}]
    expected = [{"filename": "doc1.pdf"}]
    assert metrics.hit_rate_at_k(retrieved, expected) == 1.0

    retrieved_miss = [{"filename": "doc2.pdf"}]
    assert metrics.hit_rate_at_k(retrieved_miss, expected) == 0.0


def test_mrr_at_k_calculation():
    retrieved = [{"filename": "noise.pdf"}, {"filename": "target.pdf"}, {"filename": "other.pdf"}]
    expected = [{"filename": "target.pdf"}]
    # target is at rank 2 -> MRR = 1/2 = 0.5
    mrr = metrics.mrr_at_k(retrieved, expected)
    assert mrr == 0.5


def test_deterministic_answer_relevance():
    terms = ["retrieval", "generation"]
    score, coverage = metrics.deterministic_answer_relevance("RAG combines retrieval and generation.", terms)
    assert score == 2
    assert coverage == 1.0

    score_part, cov_part = metrics.deterministic_answer_relevance("RAG uses retrieval.", terms)
    assert score_part == 1
    assert cov_part == 0.5


def test_unanswerable_safety():
    score_safe, is_safe = metrics.unanswerable_safety(has_relevant_context=False, sources_returned=[])
    assert score_safe == 2
    assert is_safe is True

    score_unsafe, is_unsafe = metrics.unanswerable_safety(has_relevant_context=True, sources_returned=["doc1.pdf"])
    assert score_unsafe == 0
    assert is_unsafe is False


def test_dataset_loading_validation(tmp_path: Path):
    valid_data = {
        "dataset_version": "1.0",
        "examples": [
            {
                "id": "q1",
                "question": "What is X?",
                "answerable": True,
                "expected_sources": [{"filename": "doc1.pdf"}]
            }
        ]
    }
    dataset_file = tmp_path / "test_dataset.json"
    dataset_file.write_text(json.dumps(valid_data), encoding="utf-8")
    loaded = evaluate.load_dataset(dataset_file)
    assert loaded["dataset_version"] == "1.0"
    assert len(loaded["examples"]) == 1
