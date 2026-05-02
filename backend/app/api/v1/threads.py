from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_thread_service
from app.models.user import User
from app.schemas.thread import ThreadCreateRequest, ThreadListResponse, ThreadRead, ThreadUpdateRequest
from app.services.thread_service import ThreadService

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _to_thread_response(thread) -> ThreadRead:
    return ThreadRead(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.get("", response_model=ThreadListResponse)
async def list_threads(
    current_user: User = Depends(get_current_user),
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadListResponse:
    threads = await thread_service.list_threads(user_id=current_user.id)
    return ThreadListResponse(threads=[_to_thread_response(thread) for thread in threads])


@router.post("", response_model=ThreadRead)
async def create_thread(
    request: ThreadCreateRequest,
    current_user: User = Depends(get_current_user),
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadRead:
    thread = await thread_service.create_thread(current_user=current_user, title=request.title)
    return _to_thread_response(thread)


@router.patch("/{thread_id}", response_model=ThreadRead)
async def rename_thread(
    thread_id: UUID,
    request: ThreadUpdateRequest,
    current_user: User = Depends(get_current_user),
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadRead:
    thread = await thread_service.update_thread(
        current_user=current_user,
        thread_id=thread_id,
        title=request.title,
    )
    return _to_thread_response(thread)


@router.delete("/{thread_id}", response_model=dict[str, str])
async def delete_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    thread_service: ThreadService = Depends(get_thread_service),
) -> dict[str, str]:
    await thread_service.delete_thread(current_user=current_user, thread_id=thread_id)
    return {"status": "ok"}
