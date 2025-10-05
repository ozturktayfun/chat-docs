from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    total: int
