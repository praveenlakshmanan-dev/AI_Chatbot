from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import chat_chain
from app.models.message import Message
from app.models.thread import ChatThread
from app.models.user import User
from app.services.thread_service import ThreadService


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.thread_service = ThreadService(db)

    async def reply(self, *, message: str, current_user: User, thread_id: UUID | None) -> tuple[str, UUID]:
        thread: ChatThread
        if thread_id is None:
            thread = await self.thread_service.create_thread_from_message(
                current_user=current_user,
                first_message=message,
            )
        else:
            thread = await self.db.scalar(
                select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == current_user.id)
            )
            if not thread:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "not_found", "message": "Thread not found"},
                )

            existing_count = await self.db.scalar(
                select(func.count(Message.id)).where(Message.thread_id == thread.id)
            )
            if (thread.title or "").strip().lower() == "new chat" and (existing_count or 0) == 0:
                thread.title = self.thread_service._auto_title(message)

        user_message = Message(
            user_id=current_user.id,
            thread_id=thread.id,
            role="user",
            content=message,
        )
        self.db.add(user_message)

        reply = await chat_chain.ainvoke(
            {"message": message},
            config={"metadata": {"user_email": current_user.email}},
        )

        assistant_message = Message(
            user_id=current_user.id,
            thread_id=thread.id,
            role="assistant",
            content=reply,
        )
        self.db.add(assistant_message)

        thread.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        return reply, thread.id

    async def list_messages(self, *, user_id: UUID, thread_id: UUID | None = None) -> list[Message]:
        stmt = select(Message).where(Message.user_id == user_id)
        if thread_id is not None:
            stmt = stmt.where(Message.thread_id == thread_id)

        result = await self.db.scalars(
            stmt.order_by(Message.created_at.asc())
        )
        return list(result.all())
