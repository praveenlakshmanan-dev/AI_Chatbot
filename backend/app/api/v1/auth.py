from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service, get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.schemas.chat import MessageRead
from app.schemas.thread import ThreadRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name, created_at=user.created_at)


def _to_message_response(message) -> MessageRead:
    return MessageRead(
        id=message.id,
        thread_id=message.thread_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


def _to_thread_response(thread) -> ThreadRead:
    return ThreadRead(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.register_employee(email=request.email, password=request.password)
    return _to_user_response(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    token, user, messages, threads = await auth_service.login_employee(
        email=request.email,
        password=request.password,
    )

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT != "development",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )

    return LoginResponse(
        user=_to_user_response(user),
        messages=[_to_message_response(msg) for msg in messages],
        threads=[_to_thread_response(thread) for thread in threads],
    )


@router.get("/google/login", response_model=None)
async def google_login(auth_service: AuthService = Depends(get_auth_service)) -> RedirectResponse:
    redirect_url = auth_service.build_google_login_url()
    return RedirectResponse(url=redirect_url)


@router.get("/google/callback", response_model=None)
async def google_callback(
    code: str = Query(...),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    token, _user, _messages, _threads = await auth_service.login_with_google_code(code=code)

    response = RedirectResponse(url=settings.FRONTEND_URL or "http://localhost:5173")
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT != "development",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return response


@router.post("/logout", response_model=dict[str, str])
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=settings.COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)
