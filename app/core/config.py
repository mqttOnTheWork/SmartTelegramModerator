"""Конфигурация приложения на основе pydantic-settings.

Все значения читаются из переменных окружения или файла `.env`. Это
обеспечивает требование ТЗ о настраиваемости через `.env` и отсутствие
секретов в коде.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Типизированные настройки приложения.

    Поля сгруппированы по подсистемам. Значения по умолчанию подходят для
    локальной разработки; для production они должны переопределяться через
    переменные окружения.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Общее ---
    app_name: str = "smart-telegram-moderator"
    environment: Environment = "development"
    debug: bool = True
    log_level: LogLevel = "INFO"
    log_json: bool = False

    # --- Telegram ---
    telegram_bot_token: str = "CHANGE_ME"
    telegram_api_timeout: int = 30
    telegram_max_retries: int = 5

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "moderator"
    postgres_password: str = "CHANGE_ME"
    postgres_db: str = "moderator"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # --- ML ---
    ml_model_path: str = "models/toxicity.joblib"
    ml_toxicity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    ml_spam_threshold: float = Field(default=0.85, ge=0.0, le=1.0)

    # --- Модерация ---
    max_warnings: int = Field(default=3, ge=1)
    mute_duration_minutes: int = Field(default=60, ge=1)
    flood_messages: int = Field(default=5, ge=1)
    flood_interval_seconds: int = Field(default=10, ge=1)

    # --- API / Авторизация ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Асинхронный DSN для SQLAlchemy/asyncpg."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """DSN для подключения к Redis."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Вернуть закэшированный экземпляр настроек.

    Кэширование через `lru_cache` гарантирует единственный объект настроек
    на процесс и удобно подменяется в тестах через `get_settings.cache_clear()`.
    """
    return Settings()
