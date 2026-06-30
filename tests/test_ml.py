"""Тесты ML-пайплайна: препроцессинг, обучение, инференс.

Обучение идёт на встроенном мини-датасете (быстро, офлайн). Инференс
проверяется и с обученной моделью, и в режиме fallback-эвристики.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import ModelError
from app.ml.inference import ToxicityClassifier
from app.ml.preprocess import normalize_text, tokenize
from app.ml.training import train_and_save, train_model

# --- preprocess ---

def test_normalize_lowercases_and_trims() -> None:
    assert normalize_text("  Привет   МИР  ") == "привет мир"


def test_normalize_unmasks_leet() -> None:
    # "ид0т" -> "идот" (0 → о)
    assert "о" in normalize_text("ид0т")


def test_tokenize_splits_words() -> None:
    assert tokenize("привет, как дела?") == ["привет", "как", "дела"]


# --- training ---

def test_train_model_on_builtin_dataset() -> None:
    model = train_model()
    proba = model.predict_proba(["ты полный идиот"])[0]
    assert len(proba) == 2


def test_train_model_rejects_bad_data() -> None:
    with pytest.raises(ModelError):
        train_model(texts=["a", "b"], labels=[1])


def test_train_and_save_creates_file(tmp_path) -> None:
    target = tmp_path / "model.joblib"
    saved = train_and_save(target)
    assert saved.exists()


# --- inference: обученная модель ---

def test_classifier_uses_trained_model(tmp_path) -> None:
    model_path = tmp_path / "model.joblib"
    train_and_save(model_path)

    settings = Settings(ml_model_path=str(model_path), ml_toxicity_threshold=0.5)
    clf = ToxicityClassifier(settings=settings)

    toxic = clf.predict("ты полный идиот и придурок")
    clean = clf.predict("спасибо большое за помощь")
    assert toxic.score >= clean.score


# --- inference: fallback без модели ---

def test_classifier_fallback_when_no_model(tmp_path) -> None:
    settings = Settings(
        ml_model_path=str(tmp_path / "missing.joblib"),
        ml_toxicity_threshold=0.3,
    )
    clf = ToxicityClassifier(settings=settings)

    result = clf.predict("ты идиот и мразь")
    assert result.toxic is True
    assert result.label == "toxic"


def test_classifier_fallback_clean_text(tmp_path) -> None:
    settings = Settings(ml_model_path=str(tmp_path / "missing.joblib"))
    clf = ToxicityClassifier(settings=settings)

    result = clf.predict("хорошего дня всем")
    assert result.toxic is False
    assert 0.0 <= result.score <= 1.0


def test_classifier_empty_text(tmp_path) -> None:
    settings = Settings(ml_model_path=str(tmp_path / "missing.joblib"))
    clf = ToxicityClassifier(settings=settings)
    assert clf.predict("").score == 0.0
