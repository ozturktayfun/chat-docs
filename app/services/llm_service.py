from __future__ import annotations

from typing import List

import google.generativeai as genai
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def _ensure_client_initialised() -> None:
    """Initialise the Gemini client lazily the first time it is required."""
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key is not configured")

    if not getattr(genai, "_client_configured", False):
        genai.configure(api_key=settings.gemini_api_key)
        setattr(genai, "_client_configured", True)


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks so Gemini can handle long documents."""
    logger.debug(
        "Chunking text for LLM processing length={} chunk_size={} overlap={}",
        len(text),
        chunk_size,
        overlap,
    )
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def build_prompt(context: str, question: str) -> str:
    """Create a prompt for Gemini that embeds the document context and user question."""
    return (
        "You are a helpful assistant that answers questions about the provided document.\n"
        "Document context:\n"
        f"{context}\n"
        "User question:\n"
        f"{question}\n"
        "Provide a concise and accurate answer referencing the document."
    )


def ask_gemini(context_chunks: List[str], question: str) -> str:
    """Send a question to Gemini and normalise the returned content to plain text."""
    _ensure_client_initialised()
    prompt = build_prompt("\n\n".join(context_chunks), question)
    model_name = settings.gemini_model or "gemini-1.5-flash-latest"
    model = genai.GenerativeModel(model_name)
    logger.info("Sending prompt to Gemini model={} chunks={} question_length={}", model_name, len(context_chunks), len(question))
    response = model.generate_content(prompt)

    if getattr(response, "text", None):
        logger.debug("Received direct text response from Gemini length={}", len(response.text))
        return response.text

    if getattr(response, "candidates", None):
        parts: List[str] = []
        for candidate in response.candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []):
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        if parts:
            logger.debug("Aggregated {} parts from Gemini candidates", len(parts))
            return "\n".join(parts)

    logger.error("Gemini response did not contain usable text model={} question_length={} chunks={}", model_name, len(question), len(context_chunks))
    raise RuntimeError("Failed to generate response from Gemini")
