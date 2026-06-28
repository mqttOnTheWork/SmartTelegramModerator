"""Сборка и запуск Telegram-бота на aiogram.

Создаёт `Bot` и `Dispatcher`, подключает роутеры с обработчиками и запускает
long-polling. Токен и таймауты берутся из настроек (`.env`).
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_dispatcher() -> Dispatcher:
    """Создать диспетчер и подключить роутеры обработчиков."""
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def build_bot(settings: Settings | None = None) -> Bot:
    """Создать экземпляр бота.

    Raises:
        ConfigurationError: если токен не задан.
    """
    settings = settings or get_settings()
    if not settings.telegram_bot_token or settings.telegram_bot_token == "CHANGE_ME":
        raise ConfigurationError("TELEGRAM_BOT_TOKEN не задан в .env")

    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def run() -> None:
    """Запустить бота в режиме long-polling."""
    settings = get_settings()
    bot = build_bot(settings)
    dispatcher = build_dispatcher()

    logger.info("Запуск Telegram-бота (long-polling)")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот остановлен, сессия закрыта")
