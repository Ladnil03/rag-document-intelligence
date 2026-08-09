"""LLM-as-a-Judge evaluation helper using the Groq API.

Evaluates generated answers and retrieved context using structured rubrics (1-5 scale)
for Answer Relevance, Faithfulness/Groundedness, and Context Relevance.
"""

import json
import logging
from typing import Any
import config

logger = logging.getLogger(__name__)

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of a Retrieval-Augmented Generation (RAG) system.

Evaluate the following RAG interaction based on three distinct criteria.

### USER QUESTION
{question}

### RETRIEVED CONTEXT
{context}

### GENERATED ANSWER
{answer}

### REFERENCE GROUND TRUTH ANSWER (Optional)
{reference_answer}

---

### EVALUATION CRITERIA & SCORING RUBRICS (1 to 5 Scale):

1. **Answer Relevance (1-5)**:
   - 1: Irrelevant or completely fails to answer the question.
   - 2: Poor; addresses query tangentially or incompletely.
   - 3: Moderate; answers main point but lacks depth or clarity.
   - 4: Good; clear, direct answer with minor omissions.
   - 5: Excellent; complete, precise, and directly addresses the question.

2. **Faithfulness / Groundedness (1-5)**:
   - 1: Severe hallucination; claims contradict context or are entirely fabricated.
   - 2: Poor grounding; multiple claims lack context support.
   - 3: Moderate; mostly grounded but includes minor unverified assumptions.
   - 4: Good; almost all claims directly supported by context.
   - 5: Perfectly faithful; every statement is strictly backed by context.

3. **Context Relevance (1-5)**:
   - 1: Completely irrelevant context.
   - 2: Mostly irrelevant noise with minimal useful information.
   - 3: Moderately useful context; contains relevant passages along with noise.
   - 4: High relevance; context directly helps answer the query with slight excess text.
   - 5: Highly targeted; ideal context with zero irrelevant noise.

---

Return ONLY valid JSON matching this exact structure:
{{
  "answer_relevance": {{ "score": <1-5>, "reasoning": "<short explanation>" }},
  "faithfulness": {{ "score": <1-5>, "reasoning": "<short explanation>" }},
  "context_relevance": {{ "score": <1-5>, "reasoning": "<short explanation>" }}
}}
"""


def evaluate_with_llm_judge(
    question: str,
    retrieved_context: str,
    generated_answer: str,
    reference_answer: str | None = None
) -> dict[str, Any]:
    """Run LLM-as-a-Judge evaluation on RAG output.

    Returns structured ratings (1-5) and rationales or an error record if judge unavailable.
    """
    if not config.GROQ_API_KEY:
        return {
            "error": "LLM Judge unavailable: GROQ_API_KEY is not configured.",
            "judge_model": config.EVAL_LLM_JUDGE_MODEL,
        }

    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY)
        
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            question=question,
            context=retrieved_context if retrieved_context else "No context retrieved.",
            answer=generated_answer,
            reference_answer=reference_answer if reference_answer else "Not provided.",
        )

        response = client.chat.completions.create(
            model=config.EVAL_LLM_JUDGE_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise, unbiased RAG evaluation judge. Respond ONLY with raw valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            "judge_model": config.EVAL_LLM_JUDGE_MODEL,
            "answer_relevance": parsed.get("answer_relevance", {"score": 0, "reasoning": "Missing"}),
            "faithfulness": parsed.get("faithfulness", {"score": 0, "reasoning": "Missing"}),
            "context_relevance": parsed.get("context_relevance", {"score": 0, "reasoning": "Missing"}),
            "judge_note": "LLM-as-a-judge provides automated semantic scoring but may exhibit slight verbosity or model preference bias."
        }
    except Exception as exc:
        logger.warning(f"LLM Judge evaluation failed: {exc}")
        return {
            "error": f"LLM Judge execution error: {str(exc)}",
            "judge_model": config.EVAL_LLM_JUDGE_MODEL,
        }
