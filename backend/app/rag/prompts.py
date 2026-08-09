"""Grounding instructions and prompt construction for the RAG pipeline."""

SYSTEM_INSTRUCTIONS = """You answer questions using only the supplied document context.
Do not invent facts or rely on unsupported outside knowledge. If the context
does not contain enough information, say so clearly. Give a concise, useful
answer and refer to source labels such as [Source 1] where appropriate."""

CHAT_SYSTEM_INSTRUCTIONS = """You are a conversational document assistant.
Use retrieved document context as the source of factual claims about documents.
Conversation history provides continuity for follow-up questions but is not new
document evidence. If the retrieved context and history are insufficient, say
so clearly. Do not invent sources or unsupported facts. Be concise and refer
to source labels such as [Source 1] where appropriate."""


def build_rag_prompt(question: str, context: str) -> str:
    """Create the user prompt passed to the configured LLM provider."""
    return f"""Document context:
{context}

Question: {question}

Answer only from the document context above."""


def build_conversational_rag_prompt(
    history: list[tuple[str, str]], document_context: str, question: str
) -> str:
    """Keep chat history and retrieved knowledge visibly separate for the LLM."""
    history_text = "\n".join(
        f"{role.title()}: {content}" for role, content in history
    ) or "(No previous messages.)"
    knowledge_text = document_context or "(No relevant document chunks were retrieved.)"
    return f"""Conversation History:
{history_text}

Retrieved Document Context:
{knowledge_text}

Current User Question:
{question}

Answer the current question using the sections above."""
