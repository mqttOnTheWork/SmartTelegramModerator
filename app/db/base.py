"""Базовая инфраструктура работы с PostgreSQL через SQLAlchemy (async).

Содержит декларативную базу моделей и класс `Database`, инкапсулирующий
асинхронный движок и фабрику сессий. Подключение настраивается из `Settings`,
все ошибки оборачиваются в доменное исключение `DatabaseError`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Декларативная база для всех ORM-моделей проекта."""


class Database:
    """Обёртка над асинхронным движком и фабрикой сессий SQLAlchemy.

    Управляет жизненным циклом подключения к PostgreSQL и предоставляет
    контекстный менеджер `session()` с автоматическим commit/rollback.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Ленивая инициализация асинхронного движка."""
        if self._engine is None:
            self._engine = create_async_engine(
                self._settings.database_url,
                pool_size=self._settings.db_pool_size,
                max_overflow=self._settings.db_max_overflow,
                pool_pre_ping=True,
                echo=self._settings.debug,
            )
            self._sessionmaker = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
            )
            logger.info("Движок БД инициализирован (pool_size=%s)",
                        self._settings.db_pool_size)
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Выдать сессию с авто-commit при успехе и rollback при ошибке.

        Yields:
            Активную асинхронную сессию SQLAlchemy.

        Raises:
            DatabaseError: при любой ошибке уровня SQLAlchemy.
        """
        if self._sessionmaker is None:
            _ = self.engine  # триггерим ленивую инициализацию

        assert self._sessionmaker is not None
        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.exception("Ошибка БД, выполнен откат транзакции")
            raise DatabaseError("Сбой операции с базой данных",
                                details={"error": str(exc)}) from exc
        finally:
            await session.close()

    async def create_all(self) -> None:
        """Создать все таблицы (для разработки/тестов; в проде — миграции)."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Схема БД создана (create_all)")
        except SQLAlchemyError as exc:
            raise DatabaseError("Не удалось создать схему БД",
                                details={"error": str(exc)}) from exc

    async def dispose(self) -> None:
        """Закрыть пул соединений и освободить ресурсы."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
            logger.info("Соединения с БД закрыты")


_database: Database | None = None


def get_database() -> Database:
    """Вернуть процесс-синглтон `Database`."""
    global _database
    if _database is None:
        _database = Database()
    return _database
