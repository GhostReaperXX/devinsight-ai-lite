"""Connect the machine learning parts to the application data."""

import json
import threading
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.ml.predictor import CategoryPredictor
from app.ml.similarity import SimilarityIndex
from app.ml.text import combine_text
from app.models import Issue

_index: SimilarityIndex | None = None
_index_signature: tuple | None = None
_index_lock = threading.Lock()


def _current_index(db: Session) -> SimilarityIndex:
    """Rebuild the index only when issues have changed since the last build."""
    global _index, _index_signature
    signature = tuple(
        db.execute(
            select(func.count(Issue.id), func.max(Issue.id), func.max(Issue.updated_at))
        ).one()
    )
    with _index_lock:
        if _index is None or signature != _index_signature:
            rows = db.execute(select(Issue.id, Issue.title, Issue.description)).all()
            _index = SimilarityIndex(
                [row.id for row in rows],
                [combine_text(row.title, row.description) for row in rows],
            )
            _index_signature = signature
        return _index


def _related_view(issue: Issue, score: float) -> dict:
    return {
        "id": issue.id,
        "title": issue.title,
        "status": issue.status,
        "project_key": issue.project.key,
        "score": score,
    }


def suggest_category(
    predictor: CategoryPredictor | None, title: str, description: str
) -> dict | None:
    """Return a suggestion, or None when there is no model or not enough text to judge."""
    if predictor is None or len(f"{title} {description}".strip()) < 15:
        return None
    prediction = predictor.predict(title, description)
    return {
        "category": prediction.category,
        "confidence": prediction.confidence,
        "is_confident": prediction.confidence >= get_settings().suggestion_min_confidence,
        "alternatives": [
            {"category": name, "probability": probability}
            for name, probability in prediction.alternatives
        ],
    }


def find_related(
    db: Session,
    title: str,
    description: str,
    exclude_issue_id: int | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Return existing issues that resemble this text, most similar first."""
    if len(f"{title} {description}".strip()) < 15:
        return []
    matches = _current_index(db).query(
        combine_text(title, description),
        top_k=top_k,
        min_score=get_settings().related_min_score,
        exclude_id=exclude_issue_id,
    )
    return [_related_view(db.get(Issue, issue_id), score) for issue_id, score in matches]


def duplicate_candidates(
    db: Session, project_id: int | None = None, limit: int = 50
) -> list[dict]:
    """Return pairs of active issues in the same project that look like the same report."""
    pairs = _current_index(db).similar_pairs(get_settings().duplicate_min_score)
    wanted = {
        issue_id for first_id, second_id, _ in pairs for issue_id in (first_id, second_id)
    }
    issues = {
        issue.id: issue
        for issue in db.scalars(
            select(Issue).where(Issue.id.in_(wanted)).options(selectinload(Issue.project))
        )
    }
    candidates = []
    for first_id, second_id, score in pairs:
        first, second = issues[first_id], issues[second_id]
        if (
            first.project_id != second.project_id
            or first.duplicate_of_id
            or second.duplicate_of_id
        ):
            continue
        if project_id is not None and first.project_id != project_id:
            continue
        candidates.append(
            {
                "first": _related_view(first, score),
                "second": _related_view(second, score),
                "score": score,
            }
        )
    return candidates[:limit]


def read_model_metrics() -> dict | None:
    """Return the evaluation saved by ml/train.py, or None if it has not been run."""
    path = Path(get_settings().classifier_metrics_file)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def summary(db: Session, predictor: CategoryPredictor | None) -> dict:
    """Return the AI numbers shown on the dashboard."""
    predicted = db.scalar(
        select(func.count(Issue.id)).where(Issue.predicted_category.is_not(None))
    )
    agreed = db.scalar(
        select(func.count(Issue.id)).where(Issue.predicted_category == Issue.category)
    )
    metrics = read_model_metrics()
    return {
        "model_available": predictor is not None,
        "model_macro_f1": metrics["test"]["macro_f1"] if metrics else None,
        "predictions_made": predicted,
        "agreement_rate": round(agreed / predicted, 3) if predicted else None,
        "duplicate_candidates": len(duplicate_candidates(db)),
    }
