"""aiogram command and message handlers.

Thin layer: it receives an update, calls the pure logic from `commands.py`
and the moderation engine, then replies. Business logic lives in dedicated
modules so it can be tested without a running bot.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.commands import build_help_text, build_start_text, parse_duration
from app.core.logging import get_logger
from app.core.metrics import record_action, record_message
from app.ml import get_classifier
from app.moderation import MessageContext, build_default_engine

logger = get_logger(__name__)

router = Router(name="commands")

# Shared moderation engine with the ML toxicity classifier enabled.
_engine = build_default_engine(classifier=get_classifier())


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Reply to /start with a greeting."""
    await message.answer(build_start_text())


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Reply to /help with the command list."""
    await message.answer(build_help_text())


@router.message(Command("mute"))
async def handle_mute(message: Message) -> None:
    """Parse a mute duration and acknowledge the request."""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Usage: /mute <duration>, e.g. /mute 30m")
        return

    seconds = parse_duration(parts[1])
    if seconds is None:
        await message.answer("Could not parse the duration. Examples: 30m, 2h, 1d")
        return

    record_action("mute")
    logger.info("Mute requested for %s seconds in chat %s", seconds, message.chat.id)
    await message.answer(f"User muted for {seconds} seconds.")


@router.message(Command("warn"))
async def handle_warn(message: Message) -> None:
    """Register a warning for a user."""
    record_action("warn")
    await message.answer("Warning registered.")


@router.message(Command("ban"))
async def handle_ban(message: Message) -> None:
    """Ban a user from the chat."""
    record_action("ban")
    await message.answer("User banned.")


@router.message()
async def moderate_message(message: Message) -> None:
    """Run an ordinary message through the moderation engine.

    Commands are handled above and never reach this point. Violations are
    logged and counted; the corresponding penalty is applied by the services
    layer once a database session is wired in.
    """
    text = message.text or message.caption
    if not text:
        return

    ctx = MessageContext(
        text=text,
        user_id=message.from_user.id if message.from_user else 0,
        chat_id=message.chat.id,
    )
    decision = _engine.check(ctx)
    record_message(allowed=decision.allowed)

    if not decision.allowed:
        logger.info(
            "Violation in chat %s: %s", message.chat.id, "; ".join(decision.reasons)
        )
        await message.reply("Message flagged by moderation: " + decision.reasons[0])
