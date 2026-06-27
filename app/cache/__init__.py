"""Слой кэширования на Redis: клиент, rate-limit и ключи."""

from app.cache.redis_client import RedisCache, get_cache

__all__ = ["RedisCache", "get_cache"]
