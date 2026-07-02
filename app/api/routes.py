"""Маршруты API: здоровье, авторизация и действия модерации."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app import __version__
from app.api.deps import CurrentUser, require_moderator
from app.api.schemas import (
    ActionResponse,
    HealthResponse,
    LoginRequest,
    TokenResponse,
    WarnRequest,
)
from app.api.security import create_access_token, verify_password
from app.core.logging import get_logger
from app.core.metrics import record_action, render_metrics

logger = get_logger(__name__)

router = APIRouter()

# Демо-учётка администратора. В реальном проекте — таблица пользователей в БД.
# Пароль "admin" (хэш bcrypt), роль owner.
_DEMO_USERS: dict[str, dict[str, str]] = {
    "admin": {
        "password_hash": "$2b$12$vq7w6v9IkRM34pCT2P9UBOpooqqw.B4wzoiqSLSK/qAR2wKyey8.C",
        "role": "owner",
    },
}


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Проверка работоспособности сервиса."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/metrics", tags=["system"])
async def metrics() -> Response:
    """Метрики Prometheus для мониторинга."""
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@router.post("/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(data: LoginRequest) -> TokenResponse:
    """Выдать JWT по логину и паролю.

    Raises:
        HTTPException 401: при неверных учётных данных.
    """
    user = _DEMO_USERS.get(data.username)
    if user is None or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    token = create_access_token(data.username, role=user["role"])
    logger.info("Успешный вход: %s", data.username)
    return TokenResponse(access_token=token)


@router.post("/moderation/warn", response_model=ActionResponse, tags=["moderation"])
async def warn_user(
    data: WarnRequest, user: CurrentUser = Depends(require_moderator)
) -> ActionResponse:
    """Выдать предупреждение (требует роль модератора и выше)."""
    logger.info("%s выдал предупреждение пользователю %s", user.username, data.user_id)
    record_action("warn")
    return ActionResponse(
        ok=True, detail=f"Пользователь {data.user_id} предупреждён: {data.reason}"
    )
