"""Чистая логика команд бота, независимая от aiogram.

Здесь нет обращений к Telegram API — только формирование текстов и разбор
аргументов. Благодаря этому логику легко покрыть unit-тестами без запуска бота
и без реального токена.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Список команд бота для /help и регистрации в BotFather.
COMMANDS: dict[str, str] = {
    "start": "start the bot and show a greeting",
    "help": "show the list of commands",
    "warn": "warn a user (reply to their message)",
    "mute": "temporarily restrict a user, e.g. /mute 30m",
    "ban": "ban a user from the chat",
    "stats": "show moderation statistics for the chat",
}

_DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(slots=True)
class CommandResult:
    """Результат обработки команды.

    Attributes:
        text: Текст ответа пользователю.
        success: Признак успешного выполнения.
    """

    text: str
    success: bool = True


def build_start_text() -> str:
    """Build the greeting message for /start."""
    return (
        "Hi! I'm Smart Moderator, I keep order in the chat.\n"
        "I automatically catch spam, flood, toxicity and ads.\n\n"
        "Commands: /help"
    )


def build_help_text() -> str:
    """Build the command list for /help."""
    lines = ["Available commands:"]
    lines.extend(f"/{name} — {desc}" for name, desc in COMMANDS.items())
    return "\n".join(lines)


def parse_duration(text: str) -> int | None:
    """Разобрать длительность вида `30m`, `2h`, `1d` в секунды.

    Args:
        text: Строка длительности (число + единица s/m/h/d).

    Returns:
        Количество секунд или None, если формат не распознан.
    """
    match = _DURATION_RE.match(text.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if amount <= 0:
        return None
    return amount * _UNIT_SECONDS[unit]
