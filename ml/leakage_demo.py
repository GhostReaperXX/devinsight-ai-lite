"""Show how data leakage produces results that look wonderful and mean nothing.

Run from the project root: python -m ml.leakage_demo
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from ml.dataset import load_dataset
from ml.pipelines import tfidf_features

RANDOM_STATE = 42


def macro_f1(train_x, test_x, train_y, test_y) -> float:
    model = LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced")
    model.fit(train_x, train_y)
    return f1_score(test_y, model.predict(test_x), average="macro")


def split(text, labels):
    return train_test_split(
        text, labels, test_size=0.20, stratify=labels, random_state=RANDOM_STATE
    )


def honest(data) -> float:
    """Correct: the vectorizer learns its vocabulary from the training text only."""
    train_x, test_x, train_y, test_y = split(data["text"], data["category"])
    vectorizer = tfidf_features()
    return macro_f1(
        vectorizer.fit_transform(train_x), vectorizer.transform(test_x), train_y, test_y
    )


def preprocessing_leak(data) -> float:
    """Wrong: the vectorizer has already seen the test text before the split."""
    matrix = tfidf_features().fit_transform(data["text"])
    train_x, test_x, train_y, test_y = split(matrix, data["category"])
    return macro_f1(train_x, test_x, train_y, test_y)


def duplicate_leak(data) -> float:
    """Wrong: the same reports appear in both the training and the test split."""
    half = data.sample(frac=0.5, random_state=RANDOM_STATE)
    repeated = pd.concat([half, half, half])
    train_x, test_x, train_y, test_y = split(repeated["text"], repeated["category"])
    vectorizer = tfidf_features()
    return macro_f1(
        vectorizer.fit_transform(train_x), vectorizer.transform(test_x), train_y, test_y
    )


def target_leak(data) -> float:
    """Wrong: the answer itself was left inside the input text."""
    leaked_text = data["text"] + " category " + data["category"]
    train_x, test_x, train_y, test_y = split(leaked_text, data["category"])
    vectorizer = TfidfVectorizer()
    return macro_f1(
        vectorizer.fit_transform(train_x), vectorizer.transform(test_x), train_y, test_y
    )


if __name__ == "__main__":
    dataset = load_dataset()
    print(f"{'experiment':<42} {'macro F1':>9}")
    for label, experiment in (
        ("honest evaluation", honest),
        ("leak: vectorizer fitted before the split", preprocessing_leak),
        ("leak: duplicates across train and test", duplicate_leak),
        ("leak: label left inside the input text", target_leak),
    ):
        print(f"{label:<42} {experiment(dataset):>9.3f}")
