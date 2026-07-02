"""Зависимости FastAPI: извлечение текущего пользователя из JWT."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.security import AuthError, decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class CurrentUser:
    """Аутентифицированный пользователь из токена."""

    username: str
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """Проверить Bearer-токен и вернуть пользователя.

    Raises:
        HTTPException 401: если токен отсутствует или невалиден.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация"
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return CurrentUser(
        username=payload.get("sub", ""), role=payload.get("role", "user")
    )


def require_moderator(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Допустить только модераторов и выше.

    Raises:
        HTTPException 403: если роли недостаточно.
    """
    if user.role not in {"moderator", "admin", "owner"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    return user
