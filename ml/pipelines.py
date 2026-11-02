"""The candidate models. Each one is a complete text-to-category pipeline."""

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


def tfidf_features() -> TfidfVectorizer:
    """Turn text into numbers: single words and pairs of neighbouring words."""
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
        sublinear_tf=True,
    )


def candidate_pipelines() -> dict[str, Pipeline]:
    """Return every model we will compare, baseline first."""
    return {
        "baseline_most_frequent": Pipeline(
            [
                ("tfidf", tfidf_features()),
                ("model", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "naive_bayes": Pipeline(
            [("tfidf", tfidf_features()), ("model", MultinomialNB(alpha=0.3))]
        ),
        "logistic_regression": Pipeline(
            [
                ("tfidf", tfidf_features()),
                (
                    "model",
                    LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced"),
                ),
            ]
        ),
        "linear_svm": Pipeline(
            [
                ("tfidf", tfidf_features()),
                ("model", LinearSVC(C=1.0, class_weight="balanced")),
            ]
        ),
    }
