"""Сервис репутации пользователей.

Репутация растёт за нормальную активность и падает за нарушения. Может
использоваться для авто-действий (например, бан при слишком низкой репутации).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import User

logger = get_logger(__name__)


class ReputationService:
    """Изменение и чтение репутации."""

    def __init__(self, session: AsyncSession, *, ban_threshold: int = -10) -> None:
        self._session = session
        self._ban_threshold = ban_threshold

    async def adjust(self, telegram_id: int, delta: int) -> int:
        """Изменить репутацию на `delta` и вернуть новое значение."""
        user = await self._get_or_create(telegram_id)
        user.reputation += delta
        await self._session.flush()
        logger.info("Репутация %s изменена на %+d → %d",
                    telegram_id, delta, user.reputation)
        return user.reputation

    async def get(self, telegram_id: int) -> int:
        """Вернуть текущую репутацию (0, если пользователь неизвестен)."""
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        return user.reputation if user else 0

    async def should_autoban(self, telegram_id: int) -> bool:
        """Проверить, упала ли репутация ниже порога авто-бана."""
        return await self.get(telegram_id) <= self._ban_threshold

    async def _get_or_create(self, telegram_id: int) -> User:
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            user = User(telegram_id=telegram_id)
            self._session.add(user)
            await self._session.flush()
        return user
