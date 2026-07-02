"""Тесты REST API: здоровье, авторизация и защищённые эндпоинты.

Используют FastAPI TestClient — без запуска реального сервера и сети.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import Settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


# --- security utils ---

def test_password_hash_roundtrip() -> None:
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_token_roundtrip() -> None:
    settings = Settings(jwt_secret="test-secret")
    token = create_access_token("alice", role="admin", settings=settings)
    payload = decode_access_token(token, settings=settings)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"


def test_decode_invalid_token_raises() -> None:
    from app.api.security import AuthError

    with pytest.raises(AuthError):
        decode_access_token("not-a-token", settings=Settings(jwt_secret="x"))


# --- endpoints ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_success(client: TestClient) -> None:
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient) -> None:
    resp = client.post("/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_warn_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/moderation/warn",
        json={"user_id": 1, "chat_id": -100, "reason": "спам"},
    )
    assert resp.status_code == 401


def test_warn_with_token(client: TestClient) -> None:
    login = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]

    resp = client.post(
        "/moderation/warn",
        json={"user_id": 1, "chat_id": -100, "reason": "спам"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_warn_forbidden_for_plain_user(client: TestClient) -> None:
    # Токен с ролью user не должен иметь доступ к действию модерации.
    token = create_access_token("bob", role="user")
    resp = client.post(
        "/moderation/warn",
        json={"user_id": 1, "chat_id": -100, "reason": "спам"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
