"""Обучение модели классификации токсичности.

Pipeline: TF-IDF по словам + логистическая регрессия. Модель сохраняется в
файл через joblib, чтобы инференс мог её загрузить без повторного обучения.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.core.exceptions import ModelError
from app.core.logging import get_logger
from app.ml.dataset import load_dataset
from app.ml.preprocess import normalize_text

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline

logger = get_logger(__name__)


def build_pipeline() -> Pipeline:
    """Собрать необученный pipeline TF-IDF + LogisticRegression."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=normalize_text,
                    ngram_range=(1, 2),
                    min_df=1,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train_model(
    texts: list[str] | None = None, labels: list[int] | None = None
) -> Pipeline:
    """Обучить модель на переданных данных или на встроенном датасете.

    Raises:
        ModelError: если данные пусты или не совпадают по длине.
    """
    if texts is None or labels is None:
        texts, labels = load_dataset()

    if not texts or len(texts) != len(labels):
        raise ModelError("Некорректные данные для обучения")

    pipeline = build_pipeline()
    pipeline.fit(texts, labels)
    logger.info("Модель обучена на %d примерах", len(texts))
    return pipeline


def train_and_save(path: str | Path) -> Path:
    """Обучить модель и сохранить её в файл.

    Args:
        path: Куда сохранить модель (.joblib).

    Returns:
        Путь к сохранённой модели.

    Raises:
        ModelError: при ошибке сохранения.
    """
    import joblib

    pipeline = train_model()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        joblib.dump(pipeline, target)
    except OSError as exc:
        raise ModelError("Не удалось сохранить модель",
                         details={"path": str(target), "error": str(exc)}) from exc
    logger.info("Модель сохранена в %s", target)
    return target
