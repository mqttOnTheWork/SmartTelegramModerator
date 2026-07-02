"""Pydantic-схемы запросов и ответов API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Данные для входа."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Ответ с access-токеном."""

    access_token: str
    token_type: str = "bearer"


class WarnRequest(BaseModel):
    """Запрос на выдачу предупреждения."""

    user_id: int
    chat_id: int
    reason: str = Field(min_length=1)


class ActionResponse(BaseModel):
    """Обобщённый ответ о выполненном действии."""

    ok: bool
    detail: str


class HealthResponse(BaseModel):
    """Ответ проверки здоровья сервиса."""

    status: str
    version: str
