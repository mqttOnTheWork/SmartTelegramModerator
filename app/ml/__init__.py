"""ML pipeline: препроцессинг, обучение и инференс классификатора токсичности."""

from app.ml.inference import ToxicityClassifier, get_classifier
from app.ml.preprocess import normalize_text, tokenize
from app.ml.training import train_and_save, train_model
from app.ml.types import Prediction

__all__ = [
    "normalize_text",
    "tokenize",
    "train_model",
    "train_and_save",
    "ToxicityClassifier",
    "get_classifier",
    "Prediction",
]
