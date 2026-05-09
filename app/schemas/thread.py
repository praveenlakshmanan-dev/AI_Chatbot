from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ThreadCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ThreadUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ThreadRead(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ThreadListResponse(BaseModel):
    threads: list[ThreadRead]
