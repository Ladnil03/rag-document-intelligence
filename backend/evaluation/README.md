# RAG Evaluation Subsystem — Phase 7

This module provides reusable, deterministic, and optional LLM-as-a-Judge evaluation for the RAG Document Intelligence Platform. It measures retrieval performance and answer generation quality using a version-controlled benchmark dataset.

---

## Environment Setup

Always use the project's dedicated virtual environment (`backend/env/`):

```powershell
# Windows PowerShell
.\env\Scripts\python.exe evaluation/evaluate.py --user-id <user_id>
```

---

## Dataset Structure (`evaluation/dataset.json`)

The benchmark dataset contains test cases categorized into 5 distinct question types:
1. **Direct Factual**: Questions explicitly answered in a single document passage.
2. **Multi-Step**: Questions requiring info from multiple chunks or concepts.
3. **Contextual**: Questions testing conceptual comprehension rather than exact keywords.
4. **Unanswerable**: Questions whose answers do NOT exist in the document corpus.
5. **Ambiguous**: Questions spanning multiple documents where retrieval selection matters.

Each example specifies:
- `id`: Unique identifier.
- `type`: Question category.
- `question`: Input query string.
- `answerable`: Boolean flag.
- `expected_sources`: List of expected document filenames and optional chunk indices.
- `expected_answer_terms`: List of ground-truth reference terms.
- `reference_answer`: Human-authored ground-truth response.

---

## Evaluation Metrics

### Retrieval Metrics
- **Recall@K**: Ratio of expected ground-truth sources retrieved within top $K$.
  $$\text{Recall@K} = \frac{|\text{Retrieved Sources} \cap \text{Expected Sources}|}{|\text{Expected Sources}|}$$
- **Precision@K**: Ratio of retrieved top $K$ sources that match expected sources.
  $$\text{Precision@K} = \frac{|\text{Retrieved Sources} \cap \text{Expected Sources}|}{K}$$
- **Hit Rate@K**: $1.0$ if at least one expected source is present in top $K$, else $0.0$.
- **MRR@K (Mean Reciprocal Rank)**: $\frac{1}{\text{rank}}$ of the first retrieved ground-truth source ($1/\text{rank}$).

### Generation & Safety Metrics
- **Answer Relevance (0-2)**: Deterministic coverage of expected reference terms in the generated answer ($2 = 100\%$, $1 = >0\%$, $0 = 0\%$).
- **Grounded Reference Support (0-2)**: Deterministic proxy checking whether expected terms appear in both the generated answer and retrieved context.
- **Unanswerable Safety (0 or 2)**: Evaluates whether the system returns `has_relevant_context=False` and no sources for queries missing in the documents ($2 = \text{Safe refusal}$, $0 = \text{Hallucinated context}$).

### Optional LLM-as-a-Judge (1-5 Scale)
When enabled (`--use-llm-judge`), uses `gpt-4.1-mini` to judge:
- **Answer Relevance (1-5)**: Depth and directness of answer to query.
- **Faithfulness (1-5)**: Strict adherence to context without hallucination.
- **Context Relevance (1-5)**: Pertinence of retrieved context to query.

---

## Baseline Configuration & Execution

Before evaluating:
1. Register a user via `POST /auth/register` or database.
2. Upload and index `rag-guide.pdf` and `machine-learning.pdf` for that user.
3. Run evaluation:

```powershell
# Basic evaluation using default config
.\env\Scripts\python.exe evaluation/evaluate.py --user-id 1

# Evaluation with top_k override and LLM-as-a-Judge
.\env\Scripts\python.exe evaluation/evaluate.py --user-id 1 --top-k 5 --use-llm-judge

# Compare results against a baseline report
.\env\Scripts\python.exe evaluation/evaluate.py --user-id 1 --top-k 5 --compare evaluation/reports/baseline.json
```

---

## Output Reports & Failure Analysis

Evaluation reports are written to `backend/evaluation/reports/latest_report.json`.

Each report contains:
- `baseline_configuration`: Embedding model, chunk size, overlap, top-K, similarity threshold.
- `summary`: Macro average scores across all examples.
- `failure_analysis`: Categorized failures with `failure_type`, `likely_cause`, and `potential_improvement`.
- `examples`: Per-example detailed results.
