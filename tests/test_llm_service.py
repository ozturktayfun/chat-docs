from __future__ import annotations

from app.services.llm_service import build_prompt, chunk_text


def test_chunk_text_handles_short_text():
    result = chunk_text("short text", chunk_size=100)
    assert result == ["short text"]


def test_chunk_text_creates_overlapping_chunks():
    text = "abcdef" * 100
    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1
    assert chunks[0][-10:] == chunks[1][:10]


def test_build_prompt_contains_context_and_question():
    prompt = build_prompt("context", "question?")
    assert "context" in prompt
    assert "question?" in prompt
    assert "Document context" in prompt
