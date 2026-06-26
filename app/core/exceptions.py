"""Иерархия исключений приложения.

Единая база `SmartModeratorError` позволяет ловить любые доменные ошибки
проекта одним `except`, при этом каждая подсистема имеет собственный тип.
"""

from __future__ import annotations


class SmartModeratorError(Exception):
    """Базовое исключение проекта.

    Args:
        message: Человекочитаемое описание ошибки.
        details: Необязательные дополнительные данные для логирования.
    """

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class ConfigurationError(SmartModeratorError):
    """Некорректная или отсутствующая конфигурация (.env / переменные среды)."""


class DatabaseError(SmartModeratorError):
    """Ошибка работы с базой данных PostgreSQL."""


class CacheError(SmartModeratorError):
    """Ошибка работы с кэшем Redis."""


class TelegramAPIError(SmartModeratorError):
    """Ошибка взаимодействия с Telegram Bot API (лимиты, сеть, ответы 4xx/5xx)."""


class ModelError(SmartModeratorError):
    """Ошибка ML-модели: загрузка, инференс, некорректный вход/выход."""


class ModerationError(SmartModeratorError):
    """Ошибка в процессе применения правил модерации."""
