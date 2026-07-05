"""Метрики Prometheus.

Определяет счётчики и гистограммы для наблюдаемости: обработанные сообщения,
действия модерации, задержка инференса модели. Экспортируются через эндпоинт
`/metrics` (см. app/api/routes.py).
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# Сколько сообщений прошло через модерацию, с разбивкой по вердикту.
MESSAGES_PROCESSED = Counter(
    "moderator_messages_processed_total",
    "Всего обработанных сообщений",
    labelnames=("verdict",),
)

# Применённые действия модерации по типу (warn/mute/ban/...).
ACTIONS_TAKEN = Counter(
    "moderator_actions_total",
    "Всего действий модерации",
    labelnames=("action",),
)

# Задержка инференса ML-модели в секундах.
INFERENCE_LATENCY = Histogram(
    "moderator_inference_seconds",
    "Время инференса классификатора токсичности",
)


def record_message(allowed: bool) -> None:
    """Учесть обработанное сообщение (allowed → verdict=ok/blocked)."""
    MESSAGES_PROCESSED.labels(verdict="ok" if allowed else "blocked").inc()


def record_action(action: str) -> None:
    """Учесть применённое действие модерации."""
    ACTIONS_TAKEN.labels(action=action).inc()


def render_metrics() -> tuple[bytes, str]:
    """Вернуть метрики в формате Prometheus и content-type."""
    return generate_latest(), CONTENT_TYPE_LATEST
