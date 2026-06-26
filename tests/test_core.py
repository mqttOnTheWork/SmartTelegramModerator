"""Тесты ядра приложения (конфигурация, логирование, исключения)."""

from __future__ import annotations

import logging

import pytest

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ConfigurationError,
    SmartModeratorError,
)
from app.core.logging import JsonFormatter


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "smart-telegram-moderator"
    assert settings.environment == "development"
    assert 0.0 <= settings.ml_toxicity_threshold <= 1.0


def test_database_and_redis_urls() -> None:
    settings = Settings(
        postgres_user="u",
        postgres_password="p",
        postgres_host="h",
        postgres_port=1234,
        postgres_db="d",
    )
    assert settings.database_url == "postgresql+asyncpg://u:p@h:1234/d"
    assert settings.redis_url.startswith("redis://")


def test_redis_url_with_password() -> None:
    settings = Settings(redis_password="secret", redis_host="r", redis_port=6380)
    assert settings.redis_url == "redis://:secret@r:6380/0"


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_exception_str_with_details() -> None:
    err = SmartModeratorError("boom", details={"code": 42})
    assert "boom" in str(err)
    assert "42" in str(err)


def test_configuration_error_is_subclass() -> None:
    assert issubclass(ConfigurationError, SmartModeratorError)


def test_json_formatter_outputs_json() -> None:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello %s", args=("world",), exc_info=None,
    )
    formatted = JsonFormatter().format(record)
    assert '"message": "hello world"' in formatted
    assert '"level": "INFO"' in formatted


@pytest.mark.parametrize("env", ["development", "staging", "production"])
def test_environment_values(env: str) -> None:
    settings = Settings(environment=env)  # type: ignore[arg-type]
    assert settings.is_production == (env == "production")
