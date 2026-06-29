"""Оркестратор модерации.

Прогоняет сообщение через набор фильтров и собирает итоговое решение.
Движок не знает о конкретных фильтрах — он работает с протоколом `Filter`,
поэтому расширяется без изменения своего кода (open/closed principle).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.logging import get_logger
from app.moderation.filters import (
    AdvertisingFilter,
    Filter,
    LinkFilter,
    ProfanityFilter,
    RepeatSpamFilter,
)
from app.moderation.types import (
    MessageContext,
    ModerationDecision,
    Severity,
)

logger = get_logger(__name__)


class ModerationEngine:
    """Применяет список фильтров к сообщению и формирует решение."""

    def __init__(self, filters: Sequence[Filter]) -> None:
        self._filters = list(filters)

    @property
    def filters(self) -> list[Filter]:
        return list(self._filters)

    def check(self, ctx: MessageContext) -> ModerationDecision:
        """Проверить сообщение всеми фильтрами.

        Администраторы не модерируются. Каждый фильтр изолирован: ошибка
        одного не роняет проверку — она логируется, и движок продолжает.

        Returns:
            Итоговое решение с максимальной серьёзностью и списком причин.
        """
        if ctx.is_admin:
            return ModerationDecision(allowed=True, severity=Severity.OK)

        reasons: list[str] = []
        max_severity = Severity.OK

        for flt in self._filters:
            try:
                verdict = flt.check(ctx)
            except Exception:  # noqa: BLE001 - изолируем сбой отдельного фильтра
                logger.exception("Ошибка в фильтре %s", getattr(flt, "name", flt))
                continue

            if verdict.triggered:
                reasons.append(verdict.reason)
                max_severity = max(max_severity, verdict.severity)

        allowed = max_severity == Severity.OK
        if not allowed:
            logger.info(
                "Сообщение отклонено (severity=%s, chat=%s, user=%s): %s",
                max_severity.name, ctx.chat_id, ctx.user_id, "; ".join(reasons),
            )
        return ModerationDecision(
            allowed=allowed, severity=max_severity, reasons=reasons
        )


def build_default_engine(is_flooding=None, classifier=None) -> ModerationEngine:  # noqa: ANN001
    """Собрать движок со стандартным набором фильтров.

    Args:
        is_flooding: Необязательная функция антифлуда (обычно из RedisCache).
            Если не передана — антифлуд-фильтр не подключается.
        classifier: Необязательный ML-классификатор токсичности. Если не
            передан — ML-фильтр не подключается (работают только правила).
    """
    from app.moderation.filters import FloodFilter, ToxicityFilter

    filters: list[Filter] = [
        LinkFilter(),
        ProfanityFilter(),
        AdvertisingFilter(),
        RepeatSpamFilter(),
    ]
    if is_flooding is not None:
        filters.append(FloodFilter(is_flooding))
    if classifier is not None:
        filters.append(ToxicityFilter(classifier))
    return ModerationEngine(filters)
