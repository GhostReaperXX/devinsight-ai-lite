"""Load the trained classifier and use it to suggest a category."""

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.ml.text import combine_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Prediction:
    category: str
    confidence: float
    alternatives: list[tuple[str, float]]


class CategoryPredictor:
    """Wraps the saved scikit-learn pipeline behind one small method."""

    def __init__(self, pipeline) -> None:
        self._pipeline = pipeline

    @classmethod
    def load(cls, path: str) -> "CategoryPredictor | None":
        """Return a predictor, or None if the file is missing: the app works either way."""
        if not Path(path).exists():
            logger.warning(
                "No model file at %s: category suggestions are switched off", path
            )
            return None
        return cls(joblib.load(path))

    def predict(self, title: str, description: str) -> Prediction:
        text = combine_text(title, description)
        probabilities = self._pipeline.predict_proba([text])[0]
        ranked = sorted(
            zip(self._pipeline.classes_, probabilities, strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
        best_category, best_probability = ranked[0]
        return Prediction(
            category=str(best_category),
            confidence=round(float(best_probability), 4),
            alternatives=[(str(name), round(float(p), 4)) for name, p in ranked[1:3]],
        )
