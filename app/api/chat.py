from fastapi import APIRouter, Depends

from app.api.deps import get_authenticated_user, get_chat_service
from app.models.user import User
from app.schemas import ChatHistoryResponse, ChatMessage, ChatRequest
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/pdf-chat", response_model=ChatMessage)
async def pdf_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_authenticated_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatMessage:
    return await chat_service.chat(current_user, payload.message)


@router.get("/chat-history", response_model=ChatHistoryResponse)
def chat_history(
    current_user: User = Depends(get_authenticated_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    return chat_service.history(current_user)
