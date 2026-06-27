"""Тесты слоя данных: ORM-модели и сессии.

Используют SQLite в памяти (aiosqlite) — изолированно и без внешней БД.
Проверяется создание схемы, вставка и связи между сущностями.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import ActionType, ModerationAction, User, UserRole, Warning


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_defaults(session) -> None:
    user = User(telegram_id=111, username="alice")
    session.add(user)
    await session.commit()

    fetched = (await session.execute(select(User))).scalar_one()
    assert fetched.telegram_id == 111
    assert fetched.role is UserRole.USER
    assert fetched.reputation == 0
    assert fetched.is_banned is False


@pytest.mark.asyncio
async def test_user_warning_relationship(session) -> None:
    user = User(telegram_id=222, role=UserRole.USER)
    user.warnings.append(Warning(chat_id=-100, reason="спам"))
    session.add(user)
    await session.commit()

    fetched = (await session.execute(select(User))).scalar_one()
    assert len(fetched.warnings) == 1
    assert fetched.warnings[0].reason == "спам"


@pytest.mark.asyncio
async def test_moderation_action_log(session) -> None:
    action = ModerationAction(
        user_id=333, chat_id=-100, action=ActionType.BAN, details="фишинг"
    )
    session.add(action)
    await session.commit()

    fetched = (await session.execute(select(ModerationAction))).scalar_one()
    assert fetched.action is ActionType.BAN
    assert fetched.created_at is not None


@pytest.mark.asyncio
async def test_mute_until_in_future(session) -> None:
    from app.db.models import Mute

    until = datetime.now(UTC) + timedelta(minutes=60)
    mute = Mute(user_id=1, chat_id=-100, until=until)
    session.add(User(telegram_id=444))
    session.add(mute)
    await session.commit()

    fetched = (await session.execute(select(Mute))).scalar_one()
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_database_session_commit_and_query(monkeypatch) -> None:
    """`Database.session()` должна коммитить и отдавать рабочую сессию."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.db.base import Database

    db = Database()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Подменяем движок/фабрику на SQLite, чтобы не требовать PostgreSQL.
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with db.session() as s:
        s.add(User(telegram_id=999, username="bob"))

    async with db.session() as s:
        fetched = (await s.execute(select(User))).scalar_one()
        assert fetched.username == "bob"

    await db.dispose()
    assert db._engine is None


@pytest.mark.asyncio
async def test_database_session_rollback_on_error(monkeypatch) -> None:
    """Ошибка SQLAlchemy внутри сессии должна приводить к DatabaseError."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.exceptions import DatabaseError
    from app.db.base import Database

    db = Database()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    db._engine = engine
    db._sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    with pytest.raises(DatabaseError):
        async with db.session() as s:
            # Нарушаем NOT NULL (telegram_id обязателен) → IntegrityError.
            s.add(User(telegram_id=None))  # type: ignore[arg-type]
    await db.dispose()
