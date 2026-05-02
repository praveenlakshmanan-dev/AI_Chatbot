from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service, get_current_user
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse, MessageRead
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def create_chat_reply(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    reply, thread_id = await chat_service.reply(
        message=request.message,
        current_user=current_user,
        thread_id=request.thread_id,
    )
    return ChatResponse(reply=reply, thread_id=thread_id)


@router.get("/chat/messages", response_model=ChatHistoryResponse)
async def get_chat_messages(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    thread_id: UUID | None = None,
) -> ChatHistoryResponse:
    messages = await chat_service.list_messages(user_id=current_user.id, thread_id=thread_id)
    return ChatHistoryResponse(
        messages=[
            MessageRead(
                id=message.id,
                thread_id=message.thread_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in messages
        ]
    )
