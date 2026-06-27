"""ORM-модели предметной области.

Описывают пользователей, чаты, предупреждения, муты, баны и журнал действий
модерации. Соответствуют разделам ТЗ: предупреждения, муты, баны, роли,
репутация, база данных.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    """Текущее время в UTC (помощник для значений по умолчанию)."""
    return datetime.now(UTC)


class UserRole(enum.StrEnum):
    """Роли пользователя в системе модерации."""

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class ActionType(enum.StrEnum):
    """Тип действия модерации для журналирования."""

    WARN = "warn"
    MUTE = "mute"
    BAN = "ban"
    UNBAN = "unban"
    DELETE_MESSAGE = "delete_message"


class TimestampMixin:
    """Поля времени создания и обновления записи."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
        server_default=func.now(),
    )


class User(Base, TimestampMixin):
    """Пользователь Telegram, известный системе."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    reputation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    warnings: Mapped[list[Warning]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User tg={self.telegram_id} role={self.role.value}>"


class Chat(Base, TimestampMixin):
    """Telegram-чат (группа), в котором работает бот."""

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Chat tg={self.telegram_id} title={self.title!r}>"


class Warning(Base, TimestampMixin):
    """Предупреждение, выданное пользователю в конкретном чате."""

    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="warnings")

    def __repr__(self) -> str:
        return f"<Warning user_id={self.user_id} chat={self.chat_id}>"


class Mute(Base, TimestampMixin):
    """Временное ограничение (мут) пользователя в чате."""

    __tablename__ = "mutes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Mute user_id={self.user_id} until={self.until.isoformat()}>"


class Ban(Base, TimestampMixin):
    """Бан пользователя в чате (постоянный или до снятия)."""

    __tablename__ = "bans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Ban user_id={self.user_id} chat={self.chat_id}>"


class ModerationAction(Base, TimestampMixin):
    """Запись журнала: какое действие модерации и над кем было выполнено."""

    __tablename__ = "moderation_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    action: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ModerationAction {self.action.value} user={self.user_id}>"
