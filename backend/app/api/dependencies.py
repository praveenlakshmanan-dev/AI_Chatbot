from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.thread_service import ThreadService


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


async def get_thread_service(db: AsyncSession = Depends(get_db)) -> ThreadService:
    return ThreadService(db)


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Authentication required"},
        )
    return await auth_service.get_current_user_from_token(access_token)
