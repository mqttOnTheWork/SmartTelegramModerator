"""Инференс токсичности.

Классификатор пытается загрузить обученную модель из файла. Если файла нет
или он повреждён — используется простая эвристика по словарю, чтобы система
оставалась работоспособной (устойчивость к ошибкам модели по ТЗ).
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.ml.preprocess import tokenize
from app.ml.types import Prediction

logger = get_logger(__name__)

# Слова для fallback-эвристики, когда обученная модель недоступна.
_FALLBACK_TOXIC = {
    "идиот", "придурок", "дурак", "мразь", "ублюдок", "тупой",
    "ненавижу", "заткнись", "отстой", "мерзость", "ничтожество",
}


class ToxicityClassifier:
    """Классификатор токсичности с ленивой загрузкой модели и fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model = None
        self._loaded = False

    def _load(self) -> None:
        """Попытаться загрузить модель из файла один раз."""
        if self._loaded:
            return
        self._loaded = True
        path = Path(self._settings.ml_model_path)
        if not path.exists():
            logger.warning("Модель не найдена (%s), используется эвристика", path)
            return
        try:
            import joblib

            self._model = joblib.load(path)
            logger.info("Модель загружена из %s", path)
        except Exception:  # noqa: BLE001 - любая ошибка → fallback
            logger.exception("Не удалось загрузить модель, используется эвристика")
            self._model = None

    def _heuristic_score(self, text: str) -> float:
        """Оценка токсичности по доле «плохих» слов (fallback)."""
        tokens = tokenize(text)
        if not tokens:
            return 0.0
        hits = sum(
            1 for t in tokens if any(t.startswith(w) for w in _FALLBACK_TOXIC)
        )
        return min(1.0, hits / len(tokens) * 3)

    def predict(self, text: str) -> Prediction:
        """Классифицировать текст.

        Returns:
            Prediction с вероятностью токсичности и меткой по порогу из настроек.
        """
        self._load()
        threshold = self._settings.ml_toxicity_threshold

        if self._model is not None:
            try:
                proba = self._model.predict_proba([text])[0]
                # Класс 1 — токсичный.
                score = float(proba[1])
            except Exception:  # noqa: BLE001 - ошибка инференса → fallback
                logger.exception("Ошибка инференса, используется эвристика")
                score = self._heuristic_score(text)
        else:
            score = self._heuristic_score(text)

        toxic = score >= threshold
        return Prediction(
            label="toxic" if toxic else "ok", score=round(score, 4), toxic=toxic
        )


_classifier: ToxicityClassifier | None = None


def get_classifier() -> ToxicityClassifier:
    """Вернуть процесс-синглтон классификатора."""
    global _classifier
    if _classifier is None:
        _classifier = ToxicityClassifier()
    return _classifier
