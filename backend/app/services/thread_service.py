from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thread import ChatThread
from app.models.user import User


class ThreadService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _auto_title(self, message: str) -> str:
        compact = " ".join(message.split()).strip()
        if not compact:
            return "New Chat"
        words = compact.split(" ")
        if len(words) <= 7:
            return compact[:255]
        return (" ".join(words[:7]) + "...")[:255]

    async def list_threads(self, *, user_id: UUID) -> list[ChatThread]:
        result = await self.db.scalars(
            select(ChatThread).where(ChatThread.user_id == user_id).order_by(ChatThread.updated_at.desc())
        )
        return list(result.all())

    async def create_thread(self, *, current_user: User, title: str | None = None) -> ChatThread:
        normalized_title = (title or "").strip() or "New Chat"
        thread = ChatThread(
            user_id=current_user.id,
            title=normalized_title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(thread)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def get_user_thread(self, *, current_user: User, thread_id: UUID) -> ChatThread:
        thread = await self.db.scalar(
            select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == current_user.id)
        )
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Thread not found"},
            )
        return thread

    async def update_thread(self, *, current_user: User, thread_id: UUID, title: str) -> ChatThread:
        thread = await self.get_user_thread(current_user=current_user, thread_id=thread_id)
        thread.title = title.strip()
        thread.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def delete_thread(self, *, current_user: User, thread_id: UUID) -> None:
        thread = await self.get_user_thread(current_user=current_user, thread_id=thread_id)
        await self.db.delete(thread)
        await self.db.commit()

    async def create_thread_from_message(self, *, current_user: User, first_message: str) -> ChatThread:
        return await self.create_thread(current_user=current_user, title=self._auto_title(first_message))
