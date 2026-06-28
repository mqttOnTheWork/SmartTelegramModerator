"""Тесты бота: чистая логика команд и сборка бота/диспетчера.

Не требуют сети и реального токена. Проверяют формирование текстов, разбор
длительности и корректную инициализацию бота.
"""

from __future__ import annotations

import pytest

from app.bot.commands import (
    COMMANDS,
    build_help_text,
    build_start_text,
    parse_duration,
)
from app.core.config import Settings
from app.core.exceptions import ConfigurationError


def test_start_text_mentions_help() -> None:
    text = build_start_text()
    assert "/help" in text
    assert "Smart Moderator" in text


def test_help_lists_all_commands() -> None:
    text = build_help_text()
    for name in COMMANDS:
        assert f"/{name}" in text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("30s", 30),
        ("5m", 300),
        ("2h", 7200),
        ("1d", 86400),
        ("10 m", 600),
        ("15M", 900),
    ],
)
def test_parse_duration_valid(raw: str, expected: int) -> None:
    assert parse_duration(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "0m", "-5m", "10x", "m", "10"])
def test_parse_duration_invalid(raw: str) -> None:
    assert parse_duration(raw) is None


def test_build_bot_requires_token() -> None:
    with pytest.raises(ConfigurationError):
        from app.bot.bot import build_bot

        build_bot(Settings(telegram_bot_token="CHANGE_ME"))


def test_build_bot_ok_with_token() -> None:
    from app.bot.bot import build_bot

    bot = build_bot(Settings(telegram_bot_token="123456:VALID_TOKEN"))
    assert bot is not None


def test_dispatcher_has_router() -> None:
    from app.bot.bot import build_dispatcher

    dispatcher = build_dispatcher()
    assert dispatcher.sub_routers, "роутеры должны быть подключены"


class _FakeChat:
    id = -100123


class _FakeMessage:
    """Минимальный мок aiogram.Message: запоминает отправленные ответы."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.chat = _FakeChat()
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        self.answers.append(text)


@pytest.mark.asyncio
async def test_handle_start_answers_greeting() -> None:
    from app.bot.handlers import handle_start

    msg = _FakeMessage("/start")
    await handle_start(msg)  # type: ignore[arg-type]
    assert msg.answers and "/help" in msg.answers[0]


@pytest.mark.asyncio
async def test_handle_help_lists_commands() -> None:
    from app.bot.handlers import handle_help

    msg = _FakeMessage("/help")
    await handle_help(msg)  # type: ignore[arg-type]
    assert "/warn" in msg.answers[0]


@pytest.mark.asyncio
async def test_handle_mute_valid() -> None:
    from app.bot.handlers import handle_mute

    msg = _FakeMessage("/mute 30m")
    await handle_mute(msg)  # type: ignore[arg-type]
    assert "1800" in msg.answers[0]


@pytest.mark.asyncio
async def test_handle_mute_no_arg() -> None:
    from app.bot.handlers import handle_mute

    msg = _FakeMessage("/mute")
    await handle_mute(msg)  # type: ignore[arg-type]
    assert "Usage" in msg.answers[0]


@pytest.mark.asyncio
async def test_handle_mute_bad_duration() -> None:
    from app.bot.handlers import handle_mute

    msg = _FakeMessage("/mute xyz")
    await handle_mute(msg)  # type: ignore[arg-type]
    assert "duration" in msg.answers[0].lower()


@pytest.mark.asyncio
async def test_handle_warn_and_ban() -> None:
    from app.bot.handlers import handle_ban, handle_warn

    warn_msg = _FakeMessage("/warn")
    await handle_warn(warn_msg)  # type: ignore[arg-type]
    assert warn_msg.answers

    ban_msg = _FakeMessage("/ban")
    await handle_ban(ban_msg)  # type: ignore[arg-type]
    assert ban_msg.answers
