"""Тесты метрик Prometheus и эндпоинта /metrics."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.core.metrics import record_action, record_message, render_metrics


def test_render_metrics_returns_prometheus_format() -> None:
    payload, content_type = render_metrics()
    assert isinstance(payload, bytes)
    assert "text/plain" in content_type


def test_record_message_increments() -> None:
    record_message(allowed=True)
    record_message(allowed=False)
    payload, _ = render_metrics()
    text = payload.decode()
    assert "moderator_messages_processed_total" in text


def test_record_action_increments() -> None:
    record_action("ban")
    payload, _ = render_metrics()
    assert "moderator_actions_total" in payload.decode()


def test_metrics_endpoint() -> None:
    client = TestClient(create_app())
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "moderator_" in resp.text
