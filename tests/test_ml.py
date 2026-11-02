"""The machine learning parts: behaviour, integration and a minimum quality."""

import json
from pathlib import Path

import pytest

from app.config import get_settings
from app.ml.predictor import CategoryPredictor
from app.ml.similarity import SimilarityIndex
from tests.conftest import auth

CATEGORIES = {"bug", "feature", "documentation", "performance", "security"}


@pytest.fixture(scope="module")
def predictor() -> CategoryPredictor:
    loaded = CategoryPredictor.load(get_settings().classifier_file)
    assert loaded is not None, "Train the model first: python -m ml.train"
    return loaded


def test_prediction_has_the_promised_shape(predictor):
    result = predictor.predict(
        "App crashes on start", "It closes at once with a stack trace."
    )
    assert result.category in CATEGORIES
    assert 0 <= result.confidence <= 1
    assert all(probability <= result.confidence for _, probability in result.alternatives)


def test_missing_model_file_means_no_predictor():
    assert CategoryPredictor.load("no/such/file.joblib") is None


def test_model_beats_the_baseline_by_a_clear_margin():
    metrics = json.loads(
        Path(get_settings().classifier_metrics_file).read_text(encoding="utf-8")
    )
    assert metrics["test"]["macro_f1"] >= 0.65
    assert metrics["test"]["macro_f1"] >= metrics["baseline_test"]["macro_f1"] + 0.30


def test_similar_text_scores_higher_than_unrelated_text():
    index = SimilarityIndex(
        [1, 2],
        ["payment button fails on mobile phones", "add a dark theme to the settings page"],
    )
    matches = index.query("the payment button fails on my phone", top_k=2, min_score=0.0)
    assert matches[0][0] == 1
    assert matches[0][1] > matches[1][1]


def test_query_respects_threshold_and_exclusion():
    index = SimilarityIndex([1, 2], ["payment button fails", "payment button fails today"])
    assert (
        index.query("payment button fails", top_k=5, min_score=0.1, exclude_id=1)[0][0] == 2
    )
    assert index.query("completely different words", top_k=5, min_score=0.1) == []


def test_empty_index_answers_politely():
    index = SimilarityIndex([], [])
    assert index.query("anything", top_k=5, min_score=0.1) == []
    assert index.similar_pairs(0.1) == []


def test_similar_pairs_finds_near_duplicates_only():
    index = SimilarityIndex(
        [1, 2, 3],
        [
            "the checkout page crashes when paying by card",
            "checkout page crashes when I pay with a card",
            "please add a dark theme to the settings",
        ],
    )
    pairs = index.similar_pairs(0.2)
    assert [(a, b) for a, b, _ in pairs] == [(1, 2)]


def test_new_issue_stores_the_prediction(client, lina, project):
    response = client.post(
        "/api/issues",
        json={
            "project_id": project.id,
            "title": "Application crashes on start",
            "description": "It closes at once with a stack trace on every launch.",
            "category": "bug",
        },
        headers=auth(lina),
    )
    body = response.json()
    assert body["predicted_category"] in CATEGORIES
    assert 0 <= body["prediction_confidence"] <= 1


def test_analyze_endpoint_returns_suggestion_and_related(client, lina, issue):
    response = client.post(
        "/api/insights/analyze",
        json={
            "title": "Pay button does nothing",
            "description": "Tapping the pay button on my phone has no effect.",
        },
        headers=auth(lina),
    )
    body = response.json()
    assert body["suggestion"]["category"] in CATEGORIES
    assert body["related"][0]["id"] == issue.id


def test_analyze_waits_for_enough_text(client, lina):
    response = client.post(
        "/api/insights/analyze", json={"title": "abc"}, headers=auth(lina)
    )
    assert response.json() == {"suggestion": None, "related": []}


def test_app_keeps_working_without_a_model(client, lina, project):
    saved = client.app.state.predictor
    client.app.state.predictor = None
    try:
        response = client.post(
            "/api/issues",
            json={
                "project_id": project.id,
                "title": "Works without the model",
                "description": "The issue is saved with no prediction.",
                "category": "feature",
            },
            headers=auth(lina),
        )
        assert response.status_code == 201
        assert response.json()["predicted_category"] is None
        assert client.get("/health").json()["model"] == "not loaded"
    finally:
        client.app.state.predictor = saved
