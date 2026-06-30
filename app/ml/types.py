"""Типы данных ML-пайплайна."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Prediction:
    """Результат классификации текста.

    Attributes:
        label: Метка класса ("toxic" или "ok").
        score: Вероятность токсичности в диапазоне [0, 1].
        toxic: Признак токсичности с учётом порога.
    """

    label: str
    score: float
    toxic: bool
