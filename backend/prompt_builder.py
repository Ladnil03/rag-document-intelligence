"""Grounding instructions and prompt construction for Phase 4."""

SYSTEM_INSTRUCTIONS = """You answer questions using only the supplied document context.
Do not invent facts or rely on unsupported outside knowledge. If the context
does not contain enough information, say so clearly. Give a concise, useful
answer and refer to source labels such as [Source 1] where appropriate."""


def build_rag_prompt(question: str, context: str) -> str:
    """Create the user prompt passed to the configured LLM provider."""
    return f"""Document context:
{context}

Question: {question}

Answer only from the document context above."""
