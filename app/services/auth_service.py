from datetime import datetime, timezone
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.message import Message
from app.models.thread import ChatThread
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _validate_employee_email(self, email: str) -> None:
        domain = (settings.EMPLOYEE_EMAIL_DOMAIN or "amzur.com").lower().strip()
        normalized = email.lower().strip()

        if domain.startswith("@"):
            is_valid = normalized.endswith(domain)
        elif "@" in domain:
            is_valid = normalized == domain or normalized.endswith("@" + domain.split("@", 1)[-1])
        else:
            is_valid = normalized.endswith("@" + domain)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "forbidden", "message": "Employee email is required"},
            )

    async def register_employee(self, *, email: str, password: str) -> User:
        self._validate_employee_email(email)
        existing = await self.db.scalar(select(User).where(User.email == email.lower()))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "already_exists", "message": "User already exists"},
            )

        user = User(email=email.lower(), hashed_password=hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login_employee(self, *, email: str, password: str) -> tuple[str, User, list[Message], list[ChatThread]]:
        self._validate_employee_email(email)
        user = await self.db.scalar(select(User).where(User.email == email.lower()))
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_credentials", "message": "Invalid email or password"},
            )

        token = create_access_token(str(user.id))
        messages = await self.list_messages(user.id)
        threads = await self.list_threads(user.id)
        return token, user, messages, threads

    def build_google_login_url(self) -> str:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "config_error", "message": "Google OAuth is not configured"},
            )

        query = urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    async def login_with_google_code(self, *, code: str) -> tuple[str, User, list[Message], list[ChatThread]]:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "config_error", "message": "Google OAuth is not configured"},
            )

        token_payload = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                token_resp = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
                token_resp.raise_for_status()
                token_data = token_resp.json()
                access_token = token_data.get("access_token")

                profile_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                profile_resp.raise_for_status()
                profile = profile_resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "oauth_error", "message": "Google authentication failed"},
            ) from exc

        email = (profile.get("email") or "").lower().strip()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "oauth_error", "message": "Google profile email not available"},
            )

        self._validate_employee_email(email)
        google_id = profile.get("id")
        full_name = profile.get("name")

        user = await self.db.scalar(select(User).where(User.email == email))
        if user:
            user.google_id = google_id
            if full_name:
                user.full_name = full_name
        else:
            user = User(
                email=email,
                hashed_password=None,
                google_id=google_id,
                full_name=full_name,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        token = create_access_token(str(user.id))
        messages = await self.list_messages(user.id)
        threads = await self.list_threads(user.id)
        return token, user, messages, threads

    async def get_current_user_from_token(self, token: str) -> User:
        try:
            user_id = UUID(decode_access_token(token))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "unauthorized", "message": "Invalid authentication token"},
            ) from exc

        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "unauthorized", "message": "User not found"},
            )
        return user

    async def list_messages(self, user_id: UUID) -> list[Message]:
        result = await self.db.scalars(
            select(Message).where(Message.user_id == user_id).order_by(Message.created_at.asc())
        )
        return list(result.all())

    async def list_threads(self, user_id: UUID) -> list[ChatThread]:
        result = await self.db.scalars(
            select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.updated_at.desc())
        )
        return list(result.all())
