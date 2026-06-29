"""Фильтры модерации.

Каждый фильтр реализует общий протокол `Filter` и отвечает за одну задачу
(принцип единственной ответственности). Новые правила добавляются без
изменения существующих — движок просто получает расширенный список фильтров.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from app.moderation.types import FilterVerdict, MessageContext, Severity

# Ссылки: http/https, www и голые домены вида example.com/...
_URL_RE = re.compile(
    r"(https?://|www\.|t\.me/|@\w+|\b\w[\w-]*\.(?:com|ru|net|org|io|me|xyz)\b)",
    re.IGNORECASE,
)

# Базовый словарь нежелательной лексики (демо-набор, расширяется через конфиг).
_PROFANITY = {
    "дурак", "идиот", "придурок", "тупой", "мразь", "ублюдок",
    "spam", "scam", "casino", "porn",
}

# Рекламные маркеры для эвристики антирекламы.
_AD_MARKERS = {"куплю", "продам", "скидка", "промокод", "заработок", "инвестиции"}


@runtime_checkable
class Filter(Protocol):
    """Протокол фильтра: принимает контекст, возвращает вердикт."""

    name: str

    def check(self, ctx: MessageContext) -> FilterVerdict:
        """Проверить сообщение и вернуть вердикт."""
        ...


class LinkFilter:
    """Ловит ссылки, упоминания каналов и голые домены."""

    name = "links"

    def __init__(self, *, allow_admins: bool = True) -> None:
        self._allow_admins = allow_admins

    def check(self, ctx: MessageContext) -> FilterVerdict:
        if self._allow_admins and ctx.is_admin:
            return FilterVerdict.ok()
        if _URL_RE.search(ctx.text):
            return FilterVerdict(
                triggered=True, severity=Severity.MEDIUM,
                reason="сообщение содержит ссылку",
            )
        return FilterVerdict.ok()


class ProfanityFilter:
    """Ловит мат и оскорбления по словарю (с учётом словоформ)."""

    name = "profanity"

    def __init__(self, extra_words: set[str] | None = None) -> None:
        self._words = {w.lower() for w in _PROFANITY}
        if extra_words:
            self._words |= {w.lower() for w in extra_words}

    def check(self, ctx: MessageContext) -> FilterVerdict:
        tokens = re.findall(r"\w+", ctx.text.lower())
        hits = [t for t in tokens if any(t.startswith(w) for w in self._words)]
        if hits:
            return FilterVerdict(
                triggered=True, severity=Severity.HIGH,
                reason=f"недопустимая лексика: {', '.join(sorted(set(hits)))}",
            )
        return FilterVerdict.ok()


class AdvertisingFilter:
    """Эвристика антирекламы: рекламные слова в сочетании со ссылкой/контактом."""

    name = "advertising"

    def check(self, ctx: MessageContext) -> FilterVerdict:
        lowered = ctx.text.lower()
        has_marker = any(m in lowered for m in _AD_MARKERS)
        has_contact = bool(_URL_RE.search(ctx.text))
        if has_marker and has_contact:
            return FilterVerdict(
                triggered=True, severity=Severity.MEDIUM,
                reason="похоже на рекламу",
            )
        return FilterVerdict.ok()


class RepeatSpamFilter:
    """Ловит спам одинаковыми сообщениями подряд от одного пользователя.

    Состояние хранится в памяти процесса (последнее сообщение на пользователя).
    Для распределённого режима подменяется реализацией на Redis.
    """

    name = "repeat_spam"

    def __init__(self, *, threshold: int = 3) -> None:
        self._threshold = threshold
        self._last: dict[tuple[int, int], tuple[str, int]] = {}

    def check(self, ctx: MessageContext) -> FilterVerdict:
        key = (ctx.chat_id, ctx.user_id)
        normalized = ctx.text.strip().lower()
        prev_text, count = self._last.get(key, ("", 0))

        if normalized and normalized == prev_text:
            count += 1
        else:
            count = 1
        self._last[key] = (normalized, count)

        if count >= self._threshold:
            return FilterVerdict(
                triggered=True, severity=Severity.MEDIUM,
                reason=f"повтор сообщения {count} раз подряд",
            )
        return FilterVerdict.ok()


class FloodFilter:
    """Антифлуд: слишком много сообщений за короткое окно времени.

    Логику подсчёта инкапсулирует внешняя функция `is_flooding(chat_id,
    user_id) -> bool` (обычно на Redis). Так фильтр не зависит от конкретного
    хранилища и легко тестируется с фейковой функцией.
    """

    name = "flood"

    def __init__(self, is_flooding) -> None:  # noqa: ANN001 - callable
        self._is_flooding = is_flooding

    def check(self, ctx: MessageContext) -> FilterVerdict:
        if self._is_flooding(ctx.chat_id, ctx.user_id):
            return FilterVerdict(
                triggered=True, severity=Severity.LOW,
                reason="превышен лимит сообщений (флуд)",
            )
        return FilterVerdict.ok()


class ToxicityFilter:
    """ML-фильтр токсичности.

    Делегирует оценку классификатору (обученная модель или эвристика).
    Классификатор внедряется извне, чтобы фильтр не зависел от способа его
    получения и легко тестировался.
    """

    name = "toxicity"

    def __init__(self, classifier) -> None:  # noqa: ANN001 - duck-typed predictor
        self._classifier = classifier

    def check(self, ctx: MessageContext) -> FilterVerdict:
        prediction = self._classifier.predict(ctx.text)
        if prediction.toxic:
            return FilterVerdict(
                triggered=True, severity=Severity.HIGH,
                reason=f"токсичность (score={prediction.score})",
            )
        return FilterVerdict.ok()
