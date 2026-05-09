from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: UUID | None = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: UUID


class MessageRead(BaseModel):
    id: UUID
    thread_id: UUID | None = None
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[MessageRead]
