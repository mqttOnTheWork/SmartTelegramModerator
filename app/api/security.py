"""Безопасность API: JWT-токены и хэширование паролей.

Токены подписываются секретом из настроек. Пароли хэшируются bcrypt через
passlib. Все ошибки проверки токена приводят к `AuthError`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import Settings, get_settings
from app.core.exceptions import SmartModeratorError

# bcrypt ограничивает пароль 72 байтами — длинные обрезаем заранее.
_MAX_PASSWORD_BYTES = 72


class AuthError(SmartModeratorError):
    """Ошибка аутентификации или проверки токена."""


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_PASSWORD_BYTES]


def hash_password(password: str) -> str:
    """Вернуть bcrypt-хэш пароля."""
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Проверить пароль против хэша."""
    try:
        return bcrypt.checkpw(_encode(password), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    subject: str, *, role: str = "user", settings: Settings | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Создать подписанный JWT.

    Args:
        subject: Идентификатор субъекта (обычно имя пользователя).
        role: Роль, зашиваемая в токен.
        settings: Настройки (по умолчанию из get_settings).
        expires_minutes: Время жизни; по умолчанию — из настроек.
    """
    settings = settings or get_settings()
    minutes = expires_minutes or settings.jwt_expire_minutes
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> dict:
    """Проверить и декодировать JWT.

    Raises:
        AuthError: если токен просрочен или некорректен.
    """
    settings = settings or get_settings()
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise AuthError("Некорректный или просроченный токен",
                        details={"error": str(exc)}) from exc
