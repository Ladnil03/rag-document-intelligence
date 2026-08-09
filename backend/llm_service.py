"""Small, replaceable LLM provider boundary for answer generation."""

import logging
from functools import lru_cache

from openai import OpenAI

import config
from prompt_builder import SYSTEM_INSTRUCTIONS

logger = logging.getLogger(__name__)


class LLMConfigurationError(RuntimeError):
    """Raised when the selected LLM provider has no usable configuration."""


class LLMGenerationError(RuntimeError):
    """Raised when the provider cannot produce a usable answer."""


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    if not config.OPENAI_API_KEY:
        raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def generate_answer(prompt: str) -> str:
    """Generate an answer through the configured provider without logging content."""
    if config.LLM_PROVIDER != "openai":
        raise LLMConfigurationError(
            f"Unsupported LLM_PROVIDER '{config.LLM_PROVIDER}'."
        )

    try:
        logger.info("[LLM] Requesting answer from provider '%s' model '%s'.", config.LLM_PROVIDER, config.LLM_MODEL)
        response = _get_openai_client().responses.create(
            model=config.LLM_MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=prompt,
        )
        answer = (response.output_text or "").strip()
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
