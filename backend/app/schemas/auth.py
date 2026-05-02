from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.chat import MessageRead
from app.schemas.thread import ThreadRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    created_at: datetime


class LoginResponse(BaseModel):
    user: UserResponse
    messages: list[MessageRead]
    threads: list[ThreadRead]
