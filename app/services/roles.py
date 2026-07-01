"""Управление ролями и проверка прав.

Определяет иерархию ролей и правила, кто кого может модерировать.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import User, UserRole

logger = get_logger(__name__)

# Чем выше значение — тем больше прав.
_ROLE_RANK: dict[UserRole, int] = {
    UserRole.USER: 0,
    UserRole.MODERATOR: 1,
    UserRole.ADMIN: 2,
    UserRole.OWNER: 3,
}


def can_moderate(actor: UserRole, target: UserRole) -> bool:
    """Может ли роль `actor` применять действия к роли `target`.

    Модерировать можно только тех, кто строго ниже по иерархии, и только если
    сам актор — модератор или выше.
    """
    if _ROLE_RANK[actor] < _ROLE_RANK[UserRole.MODERATOR]:
        return False
    return _ROLE_RANK[actor] > _ROLE_RANK[target]


class RoleService:
    """Чтение и изменение ролей пользователей в БД."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_role(self, telegram_id: int, role: UserRole) -> User:
        """Назначить пользователю роль, создав запись при необходимости."""
        user = await self._get_or_create(telegram_id)
        user.role = role
        await self._session.flush()
        logger.info("Роль пользователя %s изменена на %s", telegram_id, role.value)
        return user

    async def get_role(self, telegram_id: int) -> UserRole:
        """Вернуть роль пользователя (USER, если он неизвестен)."""
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        return user.role if user else UserRole.USER

    async def _get_or_create(self, telegram_id: int) -> User:
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            user = User(telegram_id=telegram_id)
            self._session.add(user)
            await self._session.flush()
        return user
