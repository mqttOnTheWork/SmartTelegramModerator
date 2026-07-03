"""Маршруты дашборда: HTML-страница и JSON со статистикой.

Статистику отдаёт провайдер, который можно подменить (в бою — из БД, в тестах
и демо — заглушкой). По умолчанию используется in-memory демо-провайдер, чтобы
дашборд работал даже без запущенной базы.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from dashboard.templates import INDEX_HTML

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Провайдер статистики: возвращает словарь метрик. Заменяется в бою на выборку
# из БД через StatsService.
StatsProvider = Callable[[], dict[str, int]]


def _demo_stats() -> dict[str, int]:
    return {
        "total": 0, "warns": 0, "mutes": 0,
        "bans": 0, "unbans": 0, "deleted_messages": 0,
    }


_provider: StatsProvider = _demo_stats


def set_stats_provider(provider: StatsProvider) -> None:
    """Задать источник статистики (например, из БД)."""
    global _provider
    _provider = provider


@router.get("", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Отдать HTML-страницу дашборда."""
    return HTMLResponse(content=INDEX_HTML)


@router.get("/stats", response_class=JSONResponse)
async def stats() -> JSONResponse:
    """Отдать текущую статистику модерации в JSON."""
    return JSONResponse(content=_provider())
