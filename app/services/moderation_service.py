"""Сервис действий модерации: предупреждения, муты, баны.

Реализует эскалацию: при накоплении предупреждений пользователь автоматически
получает мут. Все действия пишутся в журнал `ModerationAction`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.models import (
    ActionType,
    Ban,
    ModerationAction,
    Mute,
    User,
    Warning,
)

logger = get_logger(__name__)


class ModerationService:
    """Применяет наказания и ведёт их учёт в БД."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    async def warn(self, telegram_id: int, chat_id: int, reason: str) -> dict:
        """Выдать предупреждение. При достижении лимита — автоматический мут.

        Returns:
            Словарь с числом предупреждений и признаком авто-мута.
        """
        user = await self._get_or_create(telegram_id)
        self._session.add(Warning(user_id=user.id, chat_id=chat_id, reason=reason))
        await self._session.flush()

        count = await self._session.scalar(
            select(func.count()).select_from(Warning).where(
                Warning.user_id == user.id, Warning.chat_id == chat_id
            )
        )
        await self._log(telegram_id, chat_id, ActionType.WARN, reason)
        logger.info("Предупреждение %s в чате %s (всего %d)",
                    telegram_id, chat_id, count)

        auto_muted = False
        if count >= self._settings.max_warnings:
            await self.mute(telegram_id, chat_id, reason="Превышен лимит предупреждений")
            auto_muted = True

        return {"warnings": int(count), "auto_muted": auto_muted}

    async def mute(
        self, telegram_id: int, chat_id: int, *, reason: str | None = None,
        minutes: int | None = None,
    ) -> Mute:
        """Замьютить пользователя на заданное время (по умолчанию — из настроек)."""
        user = await self._get_or_create(telegram_id)
        duration = minutes or self._settings.mute_duration_minutes
        until = datetime.now(UTC) + timedelta(minutes=duration)

        mute = Mute(user_id=user.id, chat_id=chat_id, reason=reason, until=until)
        self._session.add(mute)
        await self._session.flush()
        await self._log(telegram_id, chat_id, ActionType.MUTE, reason)
        logger.info("Мьют %s в чате %s до %s", telegram_id, chat_id, until.isoformat())
        return mute

    async def ban(
        self, telegram_id: int, chat_id: int, *, reason: str | None = None
    ) -> Ban:
        """Забанить пользователя в чате."""
        user = await self._get_or_create(telegram_id)
        user.is_banned = True
        ban = Ban(user_id=user.id, chat_id=chat_id, reason=reason)
        self._session.add(ban)
        await self._session.flush()
        await self._log(telegram_id, chat_id, ActionType.BAN, reason)
        logger.info("Бан %s в чате %s", telegram_id, chat_id)
        return ban

    async def unban(self, telegram_id: int, chat_id: int) -> bool:
        """Снять бан. Возвращает True, если были активные баны."""
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            return False

        bans = (await self._session.scalars(
            select(Ban).where(
                Ban.user_id == user.id, Ban.chat_id == chat_id, Ban.is_active.is_(True)
            )
        )).all()
        for ban in bans:
            ban.is_active = False
        user.is_banned = False
        await self._session.flush()
        await self._log(telegram_id, chat_id, ActionType.UNBAN, None)
        return bool(bans)

    async def is_muted(self, telegram_id: int, chat_id: int) -> bool:
        """Есть ли активный, не истёкший мут у пользователя в чате."""
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            return False
        now = datetime.now(UTC)
        mute = await self._session.scalar(
            select(Mute).where(
                Mute.user_id == user.id, Mute.chat_id == chat_id,
                Mute.is_active.is_(True), Mute.until > now,
            )
        )
        return mute is not None

    async def _log(
        self, telegram_id: int, chat_id: int, action: ActionType, details: str | None
    ) -> None:
        self._session.add(ModerationAction(
            user_id=telegram_id, chat_id=chat_id, action=action, details=details
        ))
        await self._session.flush()

    async def _get_or_create(self, telegram_id: int) -> User:
        user = await self._session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user is None:
            user = User(telegram_id=telegram_id)
            self._session.add(user)
            await self._session.flush()
        return user
