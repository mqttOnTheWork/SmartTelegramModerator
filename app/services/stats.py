"""Сбор статистики модерации для дашборда и API.

Считает действия по типам за период на основе журнала `ModerationAction`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ActionType, ModerationAction


@dataclass(slots=True)
class ModerationStats:
    """Агрегированная статистика действий модерации."""

    warns: int = 0
    mutes: int = 0
    bans: int = 0
    unbans: int = 0
    deleted_messages: int = 0
    total: int = 0

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


_ACTION_FIELD: dict[ActionType, str] = {
    ActionType.WARN: "warns",
    ActionType.MUTE: "mutes",
    ActionType.BAN: "bans",
    ActionType.UNBAN: "unbans",
    ActionType.DELETE_MESSAGE: "deleted_messages",
}


class StatsService:
    """Считает статистику по журналу действий."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def collect(self, chat_id: int | None = None) -> ModerationStats:
        """Собрать статистику действий, опционально по конкретному чату."""
        query = select(
            ModerationAction.action, func.count()
        ).group_by(ModerationAction.action)
        if chat_id is not None:
            query = query.where(ModerationAction.chat_id == chat_id)

        rows = (await self._session.execute(query)).all()
        stats = ModerationStats()
        for action, count in rows:
            field = _ACTION_FIELD.get(action)
            if field:
                setattr(stats, field, int(count))
                stats.total += int(count)
        return stats
