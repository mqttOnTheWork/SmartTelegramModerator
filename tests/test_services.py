"""Тесты сервисного слоя: предупреждения, муты, баны, репутация, роли.

Работают на SQLite в памяти, без внешней БД.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.db.models import UserRole
from app.services import (
    ModerationService,
    ReputationService,
    RoleService,
    can_moderate,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


# --- roles ---

@pytest.mark.parametrize(
    ("actor", "target", "expected"),
    [
        (UserRole.ADMIN, UserRole.USER, True),
        (UserRole.MODERATOR, UserRole.USER, True),
        (UserRole.OWNER, UserRole.ADMIN, True),
        (UserRole.USER, UserRole.USER, False),
        (UserRole.MODERATOR, UserRole.MODERATOR, False),
        (UserRole.MODERATOR, UserRole.ADMIN, False),
    ],
)
def test_can_moderate(actor, target, expected) -> None:
    assert can_moderate(actor, target) is expected


@pytest.mark.asyncio
async def test_role_service_set_and_get(session) -> None:
    svc = RoleService(session)
    await svc.set_role(111, UserRole.ADMIN)
    assert await svc.get_role(111) is UserRole.ADMIN


@pytest.mark.asyncio
async def test_role_service_unknown_defaults_to_user(session) -> None:
    svc = RoleService(session)
    assert await svc.get_role(999) is UserRole.USER


# --- reputation ---

@pytest.mark.asyncio
async def test_reputation_adjust(session) -> None:
    svc = ReputationService(session)
    assert await svc.adjust(111, 5) == 5
    assert await svc.adjust(111, -2) == 3


@pytest.mark.asyncio
async def test_reputation_autoban_threshold(session) -> None:
    svc = ReputationService(session, ban_threshold=-5)
    await svc.adjust(111, -6)
    assert await svc.should_autoban(111) is True
    assert await svc.should_autoban(222) is False


# --- moderation actions ---

@pytest.mark.asyncio
async def test_warn_increments_count(session) -> None:
    svc = ModerationService(session, settings=Settings(max_warnings=3))
    r1 = await svc.warn(111, -100, "спам")
    r2 = await svc.warn(111, -100, "спам")
    assert r1["warnings"] == 1
    assert r2["warnings"] == 2
    assert not r2["auto_muted"]


@pytest.mark.asyncio
async def test_warn_auto_mutes_at_limit(session) -> None:
    svc = ModerationService(session, settings=Settings(max_warnings=2))
    await svc.warn(111, -100, "раз")
    result = await svc.warn(111, -100, "два")
    assert result["auto_muted"] is True
    assert await svc.is_muted(111, -100) is True


@pytest.mark.asyncio
async def test_mute_and_check(session) -> None:
    svc = ModerationService(session, settings=Settings(mute_duration_minutes=30))
    await svc.mute(111, -100, reason="флуд")
    assert await svc.is_muted(111, -100) is True
    assert await svc.is_muted(111, -999) is False


@pytest.mark.asyncio
async def test_ban_and_unban(session) -> None:
    svc = ModerationService(session)
    await svc.ban(111, -100, reason="реклама")
    assert await svc.unban(111, -100) is True
    # повторный анбан — уже нечего снимать
    assert await svc.unban(111, -100) is False


@pytest.mark.asyncio
async def test_unban_unknown_user(session) -> None:
    svc = ModerationService(session)
    assert await svc.unban(555, -100) is False
