"""Точка входа приложения.

Проверяет конфигурацию, инициализирует логирование и запускает Telegram-бота
в режиме long-polling.
"""

from __future__ import annotations

import asyncio

from app.core import configure_logging, get_logger, get_settings
from app.core.exceptions import ConfigurationError


def bootstrap() -> None:
    """Инициализировать приложение: настройки + логирование.

    Raises:
        ConfigurationError: если обязательные настройки не заданы.
    """
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    logger.info(
        "Запуск %s (env=%s, debug=%s)",
        settings.app_name,
        settings.environment,
        settings.debug,
    )

    if settings.is_production and settings.telegram_bot_token == "CHANGE_ME":
        raise ConfigurationError(
            "TELEGRAM_BOT_TOKEN не задан для production-окружения"
        )

    logger.info("Конфигурация загружена успешно. Готово к работе.")


def main() -> None:
    """CLI-обёртка для запуска через `python -m app.main`."""
    try:
        bootstrap()
    except ConfigurationError as exc:
        get_logger(__name__).error("Ошибка конфигурации: %s", exc)
        raise SystemExit(1) from exc

    # Запуск бота. Импорт здесь, чтобы bootstrap работал без установленного aiogram.
    from app.bot.bot import run

    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        get_logger(__name__).info("Остановка по сигналу пользователя")


if __name__ == "__main__":
    main()
