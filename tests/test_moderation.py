"""Тесты движка модерации и отдельных фильтров.

Полностью офлайн: без сети и Redis. Антифлуд проверяется через подставную
функцию `is_flooding`.
"""

from __future__ import annotations

import pytest

from app.moderation import (
    AdvertisingFilter,
    FloodFilter,
    LinkFilter,
    MessageContext,
    ProfanityFilter,
    RepeatSpamFilter,
    Severity,
    build_default_engine,
)
from app.moderation.engine import ModerationEngine


def ctx(text: str, *, is_admin: bool = False, user_id: int = 1) -> MessageContext:
    return MessageContext(text=text, user_id=user_id, chat_id=-100, is_admin=is_admin)


# --- LinkFilter ---

@pytest.mark.parametrize(
    "text",
    ["зайди на https://spam.io", "смотри www.site.ru", "пиши @channel", "test.com тут"],
)
def test_link_filter_triggers(text: str) -> None:
    assert LinkFilter().check(ctx(text)).triggered


def test_link_filter_allows_plain_text() -> None:
    assert not LinkFilter().check(ctx("просто обычное сообщение")).triggered


def test_link_filter_skips_admin() -> None:
    assert not LinkFilter().check(ctx("https://spam.io", is_admin=True)).triggered


# --- ProfanityFilter ---

def test_profanity_triggers_on_wordform() -> None:
    verdict = ProfanityFilter().check(ctx("ты идиот и придурок"))
    assert verdict.triggered
    assert verdict.severity is Severity.HIGH


def test_profanity_extra_words() -> None:
    flt = ProfanityFilter(extra_words={"балбес"})
    assert flt.check(ctx("вот балбес")).triggered


def test_profanity_clean_text() -> None:
    assert not ProfanityFilter().check(ctx("хорошего дня")).triggered


# --- AdvertisingFilter ---

def test_advertising_needs_marker_and_contact() -> None:
    assert AdvertisingFilter().check(ctx("скидка 50% пиши @shop")).triggered
    # только маркер без контакта — не реклама
    assert not AdvertisingFilter().check(ctx("сегодня скидка на всё")).triggered


# --- RepeatSpamFilter ---

def test_repeat_spam_triggers_after_threshold() -> None:
    flt = RepeatSpamFilter(threshold=3)
    results = [flt.check(ctx("одно и то же")).triggered for _ in range(3)]
    assert results == [False, False, True]


def test_repeat_spam_resets_on_new_text() -> None:
    flt = RepeatSpamFilter(threshold=2)
    flt.check(ctx("aaa"))
    assert not flt.check(ctx("bbb")).triggered


# --- FloodFilter ---

def test_flood_filter_uses_injected_callable() -> None:
    flt = FloodFilter(lambda chat_id, user_id: True)
    verdict = flt.check(ctx("hi"))
    assert verdict.triggered
    assert verdict.severity is Severity.LOW


# --- Engine ---

def test_engine_allows_clean_message() -> None:
    engine = build_default_engine()
    decision = engine.check(ctx("всем привет, как дела"))
    assert decision.allowed
    assert decision.severity is Severity.OK


def test_engine_blocks_profanity_with_high_severity() -> None:
    engine = build_default_engine()
    decision = engine.check(ctx("ты идиот"))
    assert not decision.allowed
    assert decision.severity is Severity.HIGH
    assert decision.reasons


def test_engine_skips_admins() -> None:
    engine = build_default_engine()
    decision = engine.check(ctx("https://spam.io идиот", is_admin=True))
    assert decision.allowed


def test_engine_collects_multiple_reasons() -> None:
    engine = build_default_engine()
    decision = engine.check(ctx("купи тут https://shop.io, идиот"))
    assert not decision.allowed
    assert len(decision.reasons) >= 2


def test_engine_with_flood(monkeypatch) -> None:
    engine = build_default_engine(is_flooding=lambda c, u: True)
    decision = engine.check(ctx("норм текст"))
    assert not decision.allowed
    assert decision.severity is Severity.LOW


def test_engine_isolates_failing_filter() -> None:
    class Boom:
        name = "boom"

        def check(self, ctx):  # noqa: ANN001
            raise RuntimeError("сломался")

    engine = ModerationEngine([Boom(), ProfanityFilter()])
    # Сломанный фильтр не должен ронять проверку.
    decision = engine.check(ctx("ты идиот"))
    assert not decision.allowed
