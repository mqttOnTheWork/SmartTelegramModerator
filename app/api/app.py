"""Фабрика приложения FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.core.logging import configure_logging
from dashboard import dashboard_router


def create_app() -> FastAPI:
    """Создать и настроить экземпляр FastAPI (API + дашборд)."""
    configure_logging()
    app = FastAPI(
        title="Smart Telegram Moderator API",
        version=__version__,
        description="REST API для управления модерацией Telegram-групп.",
    )
    app.include_router(router)
    app.include_router(dashboard_router)
    return app
