"""Тесты дашборда: HTML-страница, JSON-статистика и StatsService."""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.app import create_app
from app.db.base import Base
from app.db.models import ActionType, ModerationAction
from app.services.stats import StatsService
from dashboard.routes import set_stats_provider


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


# --- dashboard endpoints ---

def test_dashboard_page_renders(client: TestClient) -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "Smart Telegram Moderator" in resp.text


def test_dashboard_stats_default(client: TestClient) -> None:
    resp = client.get("/dashboard/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"total", "warns", "mutes", "bans"}


def test_dashboard_stats_custom_provider(client: TestClient) -> None:
    set_stats_provider(lambda: {"total": 42, "warns": 10, "mutes": 5,
                                "bans": 2, "unbans": 1, "deleted_messages": 24})
    try:
        resp = client.get("/dashboard/stats")
        assert resp.json()["total"] == 42
    finally:
        # вернуть провайдер по умолчанию, чтобы не влиять на другие тесты
        set_stats_provider(lambda: {"total": 0, "warns": 0, "mutes": 0,
                                    "bans": 0, "unbans": 0, "deleted_messages": 0})


# --- StatsService ---

@pytest.mark.asyncio
async def test_stats_service_counts_actions(session) -> None:
    session.add_all([
        ModerationAction(user_id=1, chat_id=-100, action=ActionType.WARN),
        ModerationAction(user_id=1, chat_id=-100, action=ActionType.WARN),
        ModerationAction(user_id=2, chat_id=-100, action=ActionType.BAN),
    ])
    await session.commit()

    stats = await StatsService(session).collect()
    assert stats.warns == 2
    assert stats.bans == 1
    assert stats.total == 3


@pytest.mark.asyncio
async def test_stats_service_filter_by_chat(session) -> None:
    session.add_all([
        ModerationAction(user_id=1, chat_id=-100, action=ActionType.MUTE),
        ModerationAction(user_id=2, chat_id=-200, action=ActionType.MUTE),
    ])
    await session.commit()

    stats = await StatsService(session).collect(chat_id=-100)
    assert stats.mutes == 1
    assert stats.total == 1


@pytest.mark.asyncio
async def test_stats_service_empty(session) -> None:
    stats = await StatsService(session).collect()
    assert stats.total == 0
    assert stats.as_dict()["warns"] == 0
