"""Типы данных движка модерации.

Отделены от логики фильтров, чтобы их можно было переиспользовать в боте,
API и тестах без циклических импортов.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Severity(enum.IntEnum):
    """Серьёзность нарушения. Чем больше значение — тем строже реакция."""

    OK = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(slots=True)
class MessageContext:
    """Входные данные для проверки одного сообщения.

    Attributes:
        text: Текст сообщения.
        user_id: Telegram ID автора.
        chat_id: Telegram ID чата.
        is_admin: Является ли автор администратором (таких не модерируем).
    """

    text: str
    user_id: int
    chat_id: int
    is_admin: bool = False


@dataclass(slots=True)
class FilterVerdict:
    """Результат работы одного фильтра.

    Attributes:
        triggered: Сработал ли фильтр.
        severity: Серьёзность нарушения.
        reason: Причина срабатывания (для лога и ответа пользователю).
    """

    triggered: bool
    severity: Severity = Severity.OK
    reason: str = ""

    @classmethod
    def ok(cls) -> FilterVerdict:
        """Вердикт без нарушения."""
        return cls(triggered=False, severity=Severity.OK)


@dataclass(slots=True)
class ModerationDecision:
    """Итоговое решение движка по сообщению.

    Attributes:
        allowed: Можно ли оставить сообщение.
        severity: Максимальная серьёзность среди сработавших фильтров.
        reasons: Список причин от всех сработавших фильтров.
    """

    allowed: bool
    severity: Severity = Severity.OK
    reasons: list[str] = field(default_factory=list)
