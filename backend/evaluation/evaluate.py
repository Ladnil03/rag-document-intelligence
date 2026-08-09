"""Reusable Phase 7 RAG Evaluation Suite.

Runs retrieval and RAG evaluation against the version-controlled dataset,
calculates Recall@K, Precision@K, Hit Rate@K, MRR@K, deterministic generation metrics,
optional LLM-as-a-Judge ratings, categorizes failure modes, and outputs a structured report.

Usage (from backend/):
    .\\env\\Scripts\\python evaluation/evaluate.py --user-id <user_id>
    .\\env\\Scripts\\python evaluation/evaluate.py --user-id <user_id> --use-llm-judge --top-k 5
    .\\env\\Scripts\\python evaluation/evaluate.py --user-id <user_id> --compare evaluation/reports/baseline.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import config
from app.rag import llm as llm_service
from app.rag import query as query_service
from app.rag import retrieval as retrieval_service
from evaluation import metrics
from evaluation import judge

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_dataset(path: Path) -> dict[str, Any]:
    """Load and validate the evaluation dataset JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {path}")
    with path.open(encoding="utf-8") as file:
        dataset = json.load(file)
    examples = dataset.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("Evaluation dataset must contain a non-empty 'examples' list.")
    for example in examples:
        if not example.get("id") or not example.get("question"):
            raise ValueError("Each evaluation example must have 'id' and 'question'.")
        if "answerable" not in example or "expected_sources" not in example:
            raise ValueError("Each evaluation example must specify 'answerable' and 'expected_sources'.")
    return dataset


def get_baseline_config(top_k_override: int | None = None) -> dict[str, Any]:
    """Record current RAG baseline parameters for reproducibility."""
    return {
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dimensions": config.EMBEDDING_DIMENSIONS,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "top_k": top_k_override if top_k_override is not None else config.EVAL_TOP_K,
        "similarity_threshold": config.SIMILARITY_THRESHOLD,
        "max_context_length": config.MAX_CONTEXT_LENGTH,
    }


def evaluate_single_example(
    example: dict[str, Any],
    user_id: int,
    top_k: int,
    use_llm_judge: bool
) -> dict[str, Any]:
    """Evaluate retrieval and generation quality for a single evaluation example."""
    question = example["question"]
    expected_sources = example["expected_sources"]
    is_answerable = example["answerable"]

    # 1. Retrieval Phase
    try:
        retrieved = retrieval_service.retrieve_relevant_chunks(
            question, user_id=user_id, top_k=top_k
        )
        retrieved_sources = [
            {
                "filename": chunk.filename,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "similarity": round(chunk.similarity, 4),
            }
            for chunk in retrieved
        ]

        rec = metrics.recall_at_k(retrieved_sources, expected_sources)
        prec = metrics.precision_at_k(retrieved_sources, expected_sources)
        hit = metrics.hit_rate_at_k(retrieved_sources, expected_sources)
        mrr = metrics.mrr_at_k(retrieved_sources, expected_sources)

    except retrieval_service.RetrievalError as exc:
        return {
            "id": example["id"],
            "type": example.get("type", "unspecified"),
            "question": question,
            "failure_type": "retrieval_error",
            "likely_cause": str(exc),
            "potential_improvement": "Check ChromaDB database connection and document index status."
        }

    record: dict[str, Any] = {
        "id": example["id"],
        "type": example.get("type", "unspecified"),
        "question": question,
        "answerable": is_answerable,
        "expected_sources": expected_sources,
        "retrieved_sources": retrieved_sources,
        "retrieval": {
            "recall_at_k": round(rec, 4) if rec is not None else None,
            "precision_at_k": round(prec, 4),
            "hit_at_k": round(hit, 4),
            "mrr_at_k": round(mrr, 4),
        },
    }

    # 2. Generation & Full RAG Pipeline Phase
    try:
        result = query_service.answer_question(question, user_id=user_id, top_k=top_k)
        generated_answer = result.answer
        retrieved_context_text = " ".join(chunk.text for chunk in result.chunks)
        expected_terms = example.get("expected_answer_terms", [])

        if is_answerable:
            ans_score, term_coverage = metrics.deterministic_answer_relevance(generated_answer, expected_terms)
            grounded_score, ground_coverage = metrics.deterministic_grounded_support(
                generated_answer, retrieved_context_text, expected_terms
            )

            record["generation"] = {
                "answer_relevance_0_to_2": ans_score,
                "reference_term_coverage": term_coverage,
                "grounded_reference_support_0_to_2": grounded_score,
                "grounding_term_coverage": ground_coverage,
                "generated_answer": generated_answer,
                "has_relevant_context": result.has_relevant_context,
            }
        else:
            safe_score, is_safe = metrics.unanswerable_safety(result.has_relevant_context, result.sources)
            record["generation"] = {
                "unanswerable_safety_0_to_2": safe_score,
                "is_safe_refusal": is_safe,
                "generated_answer": generated_answer,
                "has_relevant_context": result.has_relevant_context,
            }

        # 3. Optional LLM-as-a-Judge Evaluation
        if use_llm_judge and config.OPENAI_API_KEY:
            judge_res = judge.evaluate_with_llm_judge(
                question=question,
                retrieved_context=retrieved_context_text,
                generated_answer=generated_answer,
                reference_answer=example.get("reference_answer"),
            )
            record["llm_judge"] = judge_res

    except (llm_service.LLMConfigurationError, llm_service.LLMGenerationError) as exc:
        record["generation_error"] = str(exc)

    # 4. Failure Analysis Categorization
    _categorize_failure(record, expected_sources, is_answerable)

    return record


def _categorize_failure(record: dict[str, Any], expected_sources: list[dict[str, Any]], is_answerable: bool) -> None:
    """Analyze evaluation output and assign explicit failure category and likely cause."""
    retrieval_rec = record.get("retrieval", {}).get("recall_at_k")
    retrieval_hit = record.get("retrieval", {}).get("hit_at_k", 0)
    gen = record.get("generation", {})

    if is_answerable:
        if expected_sources and retrieval_hit == 0:
            record["failure_type"] = "wrong_retrieval_or_missing_source"
            record["likely_cause"] = "ChromaDB vector search did not return expected source in top K."
            record["potential_improvement"] = "Increase top_k, optimize chunking strategy, or use a higher dimension embedding model."
        elif retrieval_rec is not None and retrieval_rec < 1.0:
            record["failure_type"] = "insufficient_context_retrieval"
            record["likely_cause"] = "Only a subset of required ground truth chunks were retrieved."
            record["potential_improvement"] = "Adjust chunk overlap or query expansion."
        elif gen.get("answer_relevance_0_to_2", 2) < 2:
            record["failure_type"] = "poor_answer_or_reference_mismatch"
            record["likely_cause"] = "Generated answer did not cover all reference ground truth terms."
            record["potential_improvement"] = "Refine generation prompt to emphasize key concepts."
    else:
        if not gen.get("is_safe_refusal", True):
            record["failure_type"] = "hallucination_on_unanswerable"
            record["likely_cause"] = "System returned context or generated answer for query missing in documents."
            record["potential_improvement"] = "Increase SIMILARITY_THRESHOLD to filter out irrelevant chunks."


def build_evaluation_report(
    dataset: dict[str, Any],
    records: list[dict[str, Any]],
    user_id: int,
    top_k: int
) -> dict[str, Any]:
    """Aggregate overall metrics and assemble structured report."""
    successful = [r for r in records if "retrieval" in r]
    answerable = [r for r in successful if r["answerable"]]
    unanswerable = [r for r in successful if not r["answerable"]]

    recalls = [r["retrieval"]["recall_at_k"] for r in answerable if r["retrieval"]["recall_at_k"] is not None]
    precisions = [r["retrieval"]["precision_at_k"] for r in successful]
    hits = [r["retrieval"]["hit_at_k"] for r in answerable]
    mrrs = [r["retrieval"]["mrr_at_k"] for r in answerable]

    summary_retrieval = {
        "macro_recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else None,
        "macro_precision_at_k": round(sum(precisions) / len(precisions), 4) if precisions else None,
        "hit_rate_at_k": round(sum(hits) / len(hits), 4) if hits else None,
        "macro_mrr_at_k": round(sum(mrrs) / len(mrrs), 4) if mrrs else None,
    }

    ans_scores = [r["generation"]["answer_relevance_0_to_2"] for r in answerable if "generation" in r and "answer_relevance_0_to_2" in r["generation"]]
    ground_scores = [r["generation"]["grounded_reference_support_0_to_2"] for r in answerable if "generation" in r and "grounded_reference_support_0_to_2" in r["generation"]]
    safe_scores = [r["generation"]["unanswerable_safety_0_to_2"] for r in unanswerable if "generation" in r and "unanswerable_safety_0_to_2" in r["generation"]]

    summary_generation = {
        "avg_answer_relevance_0_to_2": round(sum(ans_scores) / len(ans_scores), 4) if ans_scores else None,
        "avg_grounded_support_0_to_2": round(sum(ground_scores) / len(ground_scores), 4) if ground_scores else None,
        "unanswerable_safety_rate": round(sum(s == 2 for s in safe_scores) / len(safe_scores), 4) if safe_scores else None,
    }

    failures = [r for r in records if "failure_type" in r or "generation_error" in r]

    return {
        "report_type": "rag_evaluation_report",
        "dataset_version": dataset.get("dataset_version", "1.0"),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_user_id": user_id,
        "baseline_configuration": get_baseline_config(top_k_override=top_k),
        "scoring_criteria": {
            "recall_at_k": "Retrieved ground truth sources / Total expected sources",
            "precision_at_k": "Retrieved expected sources / Top K retrieved count",
            "hit_rate_at_k": "1.0 if at least 1 expected source retrieved in top K, else 0.0",
            "mrr_at_k": "Mean Reciprocal Rank (1/rank of first retrieved ground truth source)",
            "answer_relevance_0_to_2": "0=no reference terms, 1=partial coverage, 2=full coverage",
            "grounded_support_0_to_2": "2=all expected terms present in answer and context, 0=otherwise",
            "unanswerable_safety_0_to_2": "2=no relevant context returned for missing query, 0=otherwise",
            "llm_judge_scale": "1-5 scale for Answer Relevance, Faithfulness, Context Relevance"
        },
        "summary": {
            "total_examples": len(records),
            "answerable_count": len(answerable),
            "unanswerable_count": len(unanswerable),
            "failure_count": len(failures),
            "retrieval_metrics": summary_retrieval,
            "generation_metrics": summary_generation,
        },
        "failure_analysis": failures,
        "examples": records,
    }


def compare_reports(current_report: dict[str, Any], previous_report_path: Path) -> None:
    """Print comparison deltas between current evaluation report and a previous baseline report."""
    if not previous_report_path.exists():
        logger.warning(f"Previous report for comparison not found at {previous_report_path}")
        return
    with previous_report_path.open(encoding="utf-8") as f:
        prev = json.load(f)

    logger.info("\n=== EVALUATION REPORT COMPARISON ===")
    logger.info(f"Current Executed At:  {current_report.get('executed_at')}")
    logger.info(f"Previous Executed At: {prev.get('executed_at')}")

    curr_ret = current_report.get("summary", {}).get("retrieval_metrics", {})
    prev_ret = prev.get("summary", {}).get("retrieval_metrics", {})

    for metric in ["macro_recall_at_k", "macro_precision_at_k", "hit_rate_at_k", "macro_mrr_at_k"]:
        c_val = curr_ret.get(metric)
        p_val = prev_ret.get(metric)
        if c_val is not None and p_val is not None:
            delta = c_val - p_val
            symbol = "▲" if delta > 0 else "▼" if delta < 0 else "="
            logger.info(f"  {metric:22s}: Current={c_val:.4f} | Previous={p_val:.4f} | Delta={delta:+.4f} ({symbol})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 7 RAG Evaluation Suite")
    parser.add_argument("--user-id", type=int, required=True, help="Authenticated owner ID of indexed evaluation documents.")
    parser.add_argument("--dataset", type=Path, default=Path(config.EVAL_DATASET_PATH), help="Path to evaluation dataset JSON.")
    parser.add_argument("--output", type=Path, default=Path(config.EVAL_OUTPUT_PATH), help="Path to write evaluation report JSON.")
    parser.add_argument("--top-k", type=int, default=config.EVAL_TOP_K, help="Override retrieval top K parameter for experiment.")
    parser.add_argument("--use-llm-judge", action="store_true", default=config.EVAL_USE_LLM_JUDGE, help="Enable LLM-as-a-Judge 1-5 scoring.")
    parser.add_argument("--compare", type=Path, default=None, help="Path to a previous report JSON to print metric comparison.")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    logger.info(f"Loaded dataset version {dataset.get('dataset_version')} with {len(dataset['examples'])} examples.")

    records = [
        evaluate_single_example(example, user_id=args.user_id, top_k=args.top_k, use_llm_judge=args.use_llm_judge)
        for example in dataset["examples"]
    ]

    report = build_evaluation_report(dataset, records, user_id=args.user_id, top_k=args.top_k)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out_file:
        json.dump(report, out_file, indent=2)

    logger.info(f"Successfully generated evaluation report -> {args.output}")
    logger.info(f"Summary Retrieval: {report['summary']['retrieval_metrics']}")
    logger.info(f"Summary Generation: {report['summary']['generation_metrics']}")
    logger.info(f"Total Failures Categorized: {report['summary']['failure_count']}")

    if args.compare:
        compare_reports(report, args.compare)


if __name__ == "__main__":
    main()
