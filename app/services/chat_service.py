from __future__ import annotations

from datetime import datetime
from typing import List, cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatMessage as ChatMessageSchema
from app.services.llm_service import ask_gemini, chunk_text
from app.services.pdf_service import PDFService


class ChatService:
    """Provide conversational interactions over PDFs for a specific user."""

    def __init__(self, db: Session, pdf_service: PDFService) -> None:
        self.db = db
        self.pdf_service = pdf_service

    def _get_session(self, user: User) -> ChatSession:
        """Return the most recent chat session for the user's selected PDF.

        A new session is created when the user has not chatted with the
        currently selected document yet. Persisting the session ID ensures
        that chat history is tied to the combination of user and PDF.
        """
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id, ChatSession.pdf_id == user.selected_pdf_id)
            .order_by(ChatSession.created_at.desc())
            .first()
        )
        if not session:
            # First interaction with this PDF; create a fresh session bucket.
            session = ChatSession(user_id=user.id, pdf_id=user.selected_pdf_id)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session

    async def chat(self, user: User, message: str) -> ChatMessageSchema:
        """Generate an AI response for the provided message.

        The PDF must be selected beforehand to scope the chat context.
        Parsed PDF text is chunked for Gemini, and both user and assistant
        messages are persisted for later retrieval.
        """
        if user.selected_pdf_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No PDF selected")

        session = self._get_session(user)
        pdf_id = cast(str, user.selected_pdf_id)
        user_id = cast(int, user.id)
        text = await self.pdf_service.get_parsed_text(pdf_id, user_id)
        context_chunks = chunk_text(text)

        try:
            response_text = ask_gemini(context_chunks, message)
        except Exception as exc:  # pragma: no cover - network/service errors
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        # Store both sides of the conversation to keep chronology intact.
        user_msg = ChatMessage(session_id=session.id, user_id=user.id, role="user", content=message)
        bot_msg = ChatMessage(session_id=session.id, user_id=user.id, role="assistant", content=response_text)
        self.db.add_all([user_msg, bot_msg])
        self.db.commit()
        self.db.refresh(user_msg)
        self.db.refresh(bot_msg)

        return ChatMessageSchema(
            role=cast(str, bot_msg.role),
            content=cast(str, bot_msg.content),
            created_at=cast(datetime, bot_msg.created_at),
        )

    def history(self, user: User) -> ChatHistoryResponse:
        """Return all chat messages for the user across PDFs."""
        sessions = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id)
            .order_by(ChatSession.created_at.asc())
            .all()
        )
        messages: List[ChatMessageSchema] = []
        for session in sessions:
            # Aggregate all messages from each session to preserve ordering.
            for msg in session.messages:
                messages.append(ChatMessageSchema(role=msg.role, content=msg.content, created_at=msg.created_at))

        return ChatHistoryResponse(messages=messages, total=len(messages))
