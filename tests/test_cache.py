"""Тесты слоя кэширования (Redis).

Используют fakeredis — in-memory совместимую реализацию, не требующую
запущенного Redis-сервера. Проверяются базовые операции и логика антифлуда.
"""

from __future__ import annotations

import fakeredis.aioredis
import pytest

from app.cache.redis_client import RedisCache
from app.core.config import Settings


@pytest.fixture
def cache() -> RedisCache:
    c = RedisCache(settings=Settings(flood_messages=3, flood_interval_seconds=10))
    # Подменяем реальный клиент на in-memory fake.
    c._client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return c


@pytest.mark.asyncio
async def test_set_and_get(cache: RedisCache) -> None:
    await cache.set("k", "v")
    assert await cache.get("k") == "v"


@pytest.mark.asyncio
async def test_get_missing_returns_none(cache: RedisCache) -> None:
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_ping(cache: RedisCache) -> None:
    assert await cache.ping() is True


@pytest.mark.asyncio
async def test_incr_with_ttl(cache: RedisCache) -> None:
    assert await cache.incr_with_ttl("c", ttl=10) == 1
    assert await cache.incr_with_ttl("c", ttl=10) == 2


@pytest.mark.asyncio
async def test_is_flooding_triggers_after_threshold(cache: RedisCache) -> None:
    # Порог = 3 сообщения. Первые три — ок, четвёртое — флуд.
    results = [await cache.is_flooding(-100, 1) for _ in range(4)]
    assert results == [False, False, False, True]


@pytest.mark.asyncio
async def test_flood_counters_isolated_per_user(cache: RedisCache) -> None:
    await cache.is_flooding(-100, 1)
    assert await cache.is_flooding(-100, 2) is False
