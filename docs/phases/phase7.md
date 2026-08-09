# Phase 7 — RAG Evaluation and Quality

## Status

Completed

## Objective

Build a reusable, objective evaluation suite for the RAG Document Intelligence Platform to measure retrieval performance and answer generation quality, establish system baselines, categorize failure modes, and guide evaluation-driven system improvements.

---

## Evaluation Dataset

The evaluation suite uses a version-controlled benchmark dataset stored in `backend/evaluation/dataset.json`. It contains 10 curated test cases across 5 distinct categories mapped directly to real project documents (`rag-guide.pdf` and `machine-learning.pdf`):
- **Direct Factual**: Questions explicitly answered in a single document section (e.g., `rag-definition`, `ml-supervised-learning`, `rag-vector-db`).
- **Multi-Step**: Questions requiring synthesis of information across multiple chunks (e.g., `rag-pipeline-flow`, `ml-model-training-eval`).
- **Contextual**: Questions testing conceptual understanding rather than exact keyword overlap (e.g., `rag-embeddings-purpose`, `ml-overfitting-generalization`).
- **Unanswerable**: Questions whose answers are absent from the document corpus to evaluate refusal safety (e.g., `unanswerable-kubernetes-config`, `unanswerable-stock-prices`).
- **Ambiguous**: Questions spanning multiple documents where retrieval selection is critical (e.g., `ambiguous-model-role`).

---

## Retrieval Metrics

Implemented in `backend/evaluation/metrics.py`:
- **Recall@K**: Proportion of expected ground-truth sources retrieved within top $K$ results.
- **Precision@K**: Proportion of retrieved top $K$ chunks that are relevant ground-truth sources.
- **Hit Rate@K**: Binary indicator ($1.0$ or $0.0$) whether at least one expected source is present in top $K$.
- **MRR@K (Mean Reciprocal Rank)**: Reciprocal rank ($1/\text{rank}$) of the first retrieved ground-truth source.

---

## Generation Metrics

- **Answer Relevance (0-2)**: Deterministic coverage of expected ground-truth reference terms in the generated response.
- **Grounded Reference Support (0-2)**: Deterministic proxy checking whether expected terms appear in both the generated answer and retrieved context text.
- **Unanswerable Safety (0 or 2)**: Evaluates whether the system returns `has_relevant_context=False` and no sources for queries missing in the document corpus.
- **LLM-as-a-Judge Ratings (1-5 Rubric)**: Optional 1-5 scale scoring for Answer Relevance, Faithfulness/Groundedness, and Context Relevance via `judge.py`.

---

## Evaluation Method

The evaluation suite is executed off-line using `backend/evaluation/evaluate.py`. It:
1. Loads `evaluation/dataset.json`.
2. Calls `retrieval_service.retrieve_relevant_chunks()` to measure vector search performance for a specified user ID.
3. Calls `query_service.answer_question()` to run full RAG generation.
4. Computes deterministic metrics and optional LLM-as-a-Judge ratings (`gpt-4.1-mini`).
5. Categorizes failed test cases and generates a structured JSON report at `evaluation/reports/latest_report.json`.

---

## Baseline Configuration

Default configuration parameters recorded in evaluation reports:
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Chunk Size**: `1000` characters
- **Chunk Overlap**: `200` characters
- **Top-K (`EVAL_TOP_K`)**: `4`
- **Similarity Threshold**: `0.35` (cosine similarity)
- **Max Context Length**: `6000` characters

---

## Improvement Experiments

The evaluation script supports CLI parameter overrides (e.g. `--top-k 5`) and report comparison via `--compare evaluation/reports/baseline.json`. This allows developers to change ONE variable at a time, execute evaluation, and measure exact metric deltas (e.g. Recall@K or Precision@K change).

---

## Results

Evaluation results have NOT been claimed by the coding agent. The developer will execute the evaluation manually.

---

## Failure Analysis

`evaluate.py` automatically categorizes failed test cases into explicit categories:
- `wrong_retrieval_or_missing_source`: ChromaDB did not return expected chunk in top K.
- `insufficient_context_retrieval`: Only partial ground-truth chunks retrieved.
- `poor_answer_or_reference_mismatch`: Generated answer missed key reference terms.
- `hallucination_on_unanswerable`: System returned context for a missing query.

Each failure record includes `failure_type`, `likely_cause`, and `potential_improvement`.

---

## Dependencies Added

No external dependencies added beyond existing environment packages inside `backend/env/`:
- `numpy`
- `scikit-learn`
- `chromadb`
- `openai`
- `pytest`

---

## Environment Variables

Added to `backend/config.py`:
- `EVAL_TOP_K`: Retrieval top K parameter for evaluation runs (default: `4`).
- `EVAL_DATASET_PATH`: Path to evaluation benchmark JSON (default: `backend/evaluation/dataset.json`).
- `EVAL_OUTPUT_PATH`: Path to write report JSON (default: `backend/evaluation/reports/latest_report.json`).
- `EVAL_USE_LLM_JUDGE`: Flag to enable LLM-as-a-Judge evaluation (default: `false`).
- `EVAL_LLM_JUDGE_MODEL`: Model name for LLM judge (default: `gpt-4.1-mini`).

---

## Files Changed

- `backend/config.py`: Added Phase 7 evaluation environment variables.
- `backend/evaluation/dataset.json`: Version-controlled 10-example benchmark test suite.
- `backend/evaluation/metrics.py`: Pure functions for Recall@K, Precision@K, Hit Rate@K, MRR@K, deterministic relevance, grounded support, and unanswerable safety.
- `backend/evaluation/judge.py`: Structured 1-5 LLM-as-a-Judge scoring module using OpenAI API.
- `backend/evaluation/evaluate.py`: CLI evaluation runner, report generator, and report comparison tool.
- `backend/evaluation/README.md`: Evaluation guide, formulas, baseline setup, and CLI usage.
- `backend/test_evaluation.py`: Unit tests for evaluation metrics and dataset validation.
- `docs/understanding.md`: Added Phase 7 RAG evaluation concepts.
- `docs/system_architecture.md`: Updated architecture diagram with Evaluation Layer.
- `docs/workflow.md`: Added Evaluation Workflow and Failure Analysis workflow.
- `docs/decisions.md`: Recorded ADR-025, ADR-026, and ADR-027.
- `README.md`: Updated root README with full platform documentation and evaluation commands.

---

## Known Limitations

- **Dataset Size**: Benchmark dataset currently contains 10 curated test cases; larger domain datasets can be added to `dataset.json`.
- **Deterministic Proxy Metrics**: Term coverage metrics serve as fast proxies; semantic judging requires enabling `--use-llm-judge` with an active `OPENAI_API_KEY`.
- **Manual Execution Rule**: Final evaluation metrics must be generated by developer execution.

---

## What Was NOT Implemented

The following Phase 8+ production infrastructure components were explicitly excluded from Phase 7:
- Docker containers and Docker Compose
- Redis caching layer
- Celery / background task workers
- Production CI/CD pipelines
- Kubernetes manifests and deployment charts
- Multi-agent orchestration / MCP servers
- Frontend UI redesign

---

## Next Phase

**Phase 8 — Productionization**
