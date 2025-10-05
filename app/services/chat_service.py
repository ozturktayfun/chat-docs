from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatMessage as ChatMessageSchema
from app.services.llm_service import ask_gemini, chunk_text
from app.services.pdf_service import PDFService


class ChatService:
    def __init__(self, db: Session, pdf_service: PDFService) -> None:
        self.db = db
        self.pdf_service = pdf_service

    def _get_session(self, user: User) -> ChatSession:
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id, ChatSession.pdf_id == user.selected_pdf_id)
            .order_by(ChatSession.created_at.desc())
            .first()
        )
        if not session:
            session = ChatSession(user_id=user.id, pdf_id=user.selected_pdf_id)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session

    async def chat(self, user: User, message: str) -> ChatMessageSchema:
        if not user.selected_pdf_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No PDF selected")

        session = self._get_session(user)
        text = await self.pdf_service.get_parsed_text(user.selected_pdf_id, user.id)
        context_chunks = chunk_text(text)

        try:
            response_text = ask_gemini(context_chunks, message)
        except Exception as exc:  # pragma: no cover - network/service errors
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        user_msg = ChatMessage(session_id=session.id, user_id=user.id, role="user", content=message)
        bot_msg = ChatMessage(session_id=session.id, user_id=user.id, role="assistant", content=response_text)
        self.db.add_all([user_msg, bot_msg])
        self.db.commit()
        self.db.refresh(user_msg)
        self.db.refresh(bot_msg)

        return ChatMessageSchema(role=bot_msg.role, content=bot_msg.content, created_at=bot_msg.created_at)

    def history(self, user: User) -> ChatHistoryResponse:
        sessions = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user.id)
            .order_by(ChatSession.created_at.asc())
            .all()
        )
        messages: List[ChatMessageSchema] = []
        for session in sessions:
            for msg in session.messages:
                messages.append(ChatMessageSchema(role=msg.role, content=msg.content, created_at=msg.created_at))

        return ChatHistoryResponse(messages=messages, total=len(messages))
