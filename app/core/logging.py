"""Настройка логирования приложения.

Поддерживает два формата вывода: человекочитаемый (для разработки) и JSON
(для production / агрегаторов логов). Уровень и формат берутся из настроек.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from app.core.config import Settings, get_settings

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Форматтер, выводящий запись лога одной JSON-строкой."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Дополнительные поля, переданные через extra=...
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload.setdefault(key, value)
        return json.dumps(payload, ensure_ascii=False)


_RESERVED_ATTRS = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime"}


def configure_logging(settings: Settings | None = None) -> None:
    """Сконфигурировать корневой логгер один раз за процесс.

    Args:
        settings: Настройки приложения; если не переданы — берутся из
            `get_settings()`.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = settings or get_settings()
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Получить именованный логгер, гарантируя инициализацию конфигурации."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
