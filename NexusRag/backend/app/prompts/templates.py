"""RAG prompt templates and construction functions.

Responsibility: Take retrieved context chunks and a user question,
produce a complete prompt string ready for LLM generation.

This module does NOT:
- Retrieve documents (Phase 7).
- Call the LLM (Phase 8).
- Orchestrate the pipeline (Phase 9 pipeline.py).
"""

from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


# =====================================================================
# System Prompt Template
# =====================================================================

RAG_SYSTEM_PROMPT = """You are a knowledgeable assistant for the NexusRag Knowledge Base.

Your task is to answer the user's question accurately and concisely,
using ONLY the context provided below.

Rules:
1. Base your answer strictly on the provided context.
2. If the context does not contain enough information to answer
   the question, say so explicitly. Do not guess or fabricate.
3. When citing information, reference the source document and page
   number where applicable.
4. Be concise and direct. Avoid unnecessary filler.
5. If the context contains conflicting information, acknowledge
   the conflict and present both perspectives.
"""


# =====================================================================
# Prompt Construction
# =====================================================================


def format_context_block(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks into a numbered context block for the prompt.

    Each chunk is rendered with its source metadata (file name, page)
    and its text content, separated by clear delimiters.

    Args:
        chunks: List of dictionaries, each containing:
            - content (str): The chunk text.
            - metadata (Dict[str, Any]): Chunk metadata with at least
              'source' and optionally 'page'.

    Returns:
        Formatted context string with numbered chunks.
    """
    if not chunks:
        return ""

    blocks: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "unknown")
        page = metadata.get("page")

        header = f"[Source {i}: {source}"
        if page is not None:
            header += f", Page {page}"
        header += "]"

        text = chunk.get("content", "").strip()
        blocks.append(f"{header}\n{text}")

    return "\n\n---\n\n".join(blocks)


def build_rag_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """Constructs the complete RAG prompt from a user question and retrieved chunks.

    The prompt structure is:
        1. System instructions (grounding rules).
        2. Retrieved context block (numbered, with source citations).
        3. User question (unchanged).

    Args:
        question: The user's original question, passed through unchanged.
        chunks: List of chunk dictionaries from retrieved results. Each must
            contain 'content' (str) and 'metadata' (Dict).

    Returns:
        Complete prompt string ready for BaseLLMService.generate().
    """
    context_block = format_context_block(chunks)

    prompt_parts = [
        RAG_SYSTEM_PROMPT.strip(),
        "",
        "--- CONTEXT ---",
        "",
        context_block,
        "",
        "--- QUESTION ---",
        "",
        question,
        "",
        "--- ANSWER ---",
    ]

    prompt = "\n".join(prompt_parts)

    logger.info(
        "RAG prompt constructed: question_length=%d, context_chunks=%d, prompt_length=%d",
        len(question),
        len(chunks),
        len(prompt),
    )

    return prompt
