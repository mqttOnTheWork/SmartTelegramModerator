"""Асинхронный клиент Redis.

Используется для кэширования, счётчиков антифлуда и rate-limit. Все сетевые
ошибки оборачиваются в `CacheError`. Клиент создаётся лениво и переиспользуется
как процесс-синглтон.
"""

from __future__ import annotations

from typing import Final

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings
from app.core.exceptions import CacheError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Префиксы ключей, чтобы не пересекаться с другими потребителями Redis.
FLOOD_KEY: Final = "flood:{chat_id}:{user_id}"
RATELIMIT_KEY: Final = "ratelimit:{scope}:{identity}"


class RedisCache:
    """Тонкая обёртка над `redis.asyncio` с доменными помощниками."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: aioredis.Redis | None = None

    @property
    def client(self) -> aioredis.Redis:
        """Ленивая инициализация подключения к Redis."""
        if self._client is None:
            self._client = aioredis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Клиент Redis инициализирован")
        return self._client

    async def ping(self) -> bool:
        """Проверить доступность Redis.

        Returns:
            True, если сервер ответил на ping.

        Raises:
            CacheError: при ошибке соединения.
        """
        try:
            return bool(await self.client.ping())
        except RedisError as exc:
            raise CacheError("Redis недоступен",
                             details={"error": str(exc)}) from exc

    async def get(self, key: str) -> str | None:
        """Получить значение по ключу (или None)."""
        try:
            return await self.client.get(key)
        except RedisError as exc:
            raise CacheError("Ошибка чтения из Redis",
                             details={"key": key, "error": str(exc)}) from exc

    async def set(self, key: str, value: str, *, ttl: int | None = None) -> None:
        """Записать значение с необязательным TTL (в секундах)."""
        try:
            await self.client.set(key, value, ex=ttl)
        except RedisError as exc:
            raise CacheError("Ошибка записи в Redis",
                             details={"key": key, "error": str(exc)}) from exc

    async def incr_with_ttl(self, key: str, *, ttl: int) -> int:
        """Атомарно увеличить счётчик и выставить TTL при первом инкременте.

        Применяется для антифлуда: считаем сообщения пользователя за окно
        времени. TTL ставится только когда счётчик создан (значение == 1).

        Returns:
            Текущее значение счётчика после инкремента.
        """
        try:
            async with self.client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, ttl)
                value, _ = await pipe.execute()
            return int(value)
        except RedisError as exc:
            raise CacheError("Ошибка инкремента счётчика в Redis",
                             details={"key": key, "error": str(exc)}) from exc

    async def is_flooding(self, chat_id: int, user_id: int) -> bool:
        """Проверить, превысил ли пользователь лимит сообщений (антифлуд).

        Returns:
            True, если число сообщений за окно превысило порог из настроек.
        """
        key = FLOOD_KEY.format(chat_id=chat_id, user_id=user_id)
        count = await self.incr_with_ttl(
            key, ttl=self._settings.flood_interval_seconds
        )
        return count > self._settings.flood_messages

    async def close(self) -> None:
        """Закрыть соединение с Redis."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Соединение с Redis закрыто")


_cache: RedisCache | None = None


def get_cache() -> RedisCache:
    """Вернуть процесс-синглтон `RedisCache`."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
