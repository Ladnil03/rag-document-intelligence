"""Small, replaceable LLM provider boundary for answer generation.

Uses the Groq SDK (OpenAI-compatible chat.completions API). The Groq
key never leaves the backend; the frontend never imports this module.
"""

import logging
from functools import lru_cache
from typing import Iterator

from groq import Groq

from app.core import config
from app.rag.prompts import CHAT_SYSTEM_INSTRUCTIONS, SYSTEM_INSTRUCTIONS

logger = logging.getLogger(__name__)


class LLMConfigurationError(RuntimeError):
    """Raised when the selected LLM provider has no usable configuration."""


class LLMGenerationError(RuntimeError):
    """Raised when the provider cannot produce a usable answer."""


@lru_cache(maxsize=1)
def _get_groq_client() -> Groq:
    if not config.GROQ_API_KEY:
        raise LLMConfigurationError("GROQ_API_KEY is not configured.")
    return Groq(api_key=config.GROQ_API_KEY)


def generate_answer(prompt: str) -> str:
    """Generate an answer through Groq chat.completions without logging content."""
    if config.LLM_PROVIDER != "groq":
        raise LLMConfigurationError(
            f"Unsupported LLM_PROVIDER '{config.LLM_PROVIDER}'. Only 'groq' is supported."
        )

    try:
        logger.info(
            "[LLM] Requesting answer from provider '%s' model '%s'.",
            config.LLM_PROVIDER,
            config.LLM_MODEL,
        )
        response = _get_groq_client().chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            stream=False,
        )
        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            raise LLMGenerationError("The LLM returned no text answer.")
        logger.info("[LLM] Answer generation completed.")
        return answer
    except LLMConfigurationError:
        raise
    except LLMGenerationError:
        raise
    except Exception as exc:
        logger.error("[LLM] Answer generation failed: %s", exc)
        raise LLMGenerationError("The LLM could not generate an answer.") from exc


def stream_chat_answer(prompt: str) -> Iterator[str]:
    """Yield genuine text deltas from the Groq streaming chat.completions API."""
    if config.LLM_PROVIDER != "groq":
        raise LLMConfigurationError(
            f"Unsupported LLM_PROVIDER '{config.LLM_PROVIDER}'. Only 'groq' is supported."
        )

    try:
        logger.info(
            "[LLM] Starting streamed chat answer with provider '%s' model '%s'.",
            config.LLM_PROVIDER,
            config.LLM_MODEL,
        )
        stream = _get_groq_client().chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
        logger.info("[LLM] Streamed chat answer completed.")
    except LLMConfigurationError:
        raise
    except LLMGenerationError:
        raise
    except Exception as exc:
        logger.error("[LLM] Streamed chat answer failed: %s", exc)
        raise LLMGenerationError("The LLM could not complete the streamed answer.") from exc
