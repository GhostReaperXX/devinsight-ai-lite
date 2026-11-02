"""Train, compare and evaluate the classifiers, then save the chosen one.

Run from the project root: python -m ml.train
"""

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # draw to a file, no window needed

import matplotlib.pyplot as plt
import pandas as pd
import sklearn
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from ml.dataset import load_dataset
from ml.pipelines import candidate_pipelines

ARTIFACTS = Path("ml/artifacts")
RANDOM_STATE = 42
TEST_SIZE = 0.20

# The model the application will use. Logistic regression gives a probability
# for every category, and the application needs that as its confidence value.
DEPLOYED_MODEL = "logistic_regression"


def compare_with_cross_validation(train_text, train_labels) -> dict[str, dict[str, float]]:
    """Score every candidate on the training data only, using five folds."""
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = {}
    print(f"{'candidate':<25} {'macro F1':>9} {'std':>7} {'accuracy':>9}")
    for name, pipeline in candidate_pipelines().items():
        f1_scores = cross_val_score(
            pipeline, train_text, train_labels, cv=folds, scoring="f1_macro"
        )
        accuracy = cross_val_score(
            pipeline, train_text, train_labels, cv=folds, scoring="accuracy"
        )
        results[name] = {
            "macro_f1": round(float(f1_scores.mean()), 4),
            "macro_f1_std": round(float(f1_scores.std()), 4),
            "accuracy": round(float(accuracy.mean()), 4),
        }
        print(
            f"{name:<25} {f1_scores.mean():>9.3f}"
            f" {f1_scores.std():>7.3f} {accuracy.mean():>9.3f}"
        )
    return results


def save_confusion_matrix(test_labels, predictions, labels: list[str]) -> None:
    matrix = confusion_matrix(test_labels, predictions, labels=labels)
    figure, axes = plt.subplots(figsize=(6.4, 5.4))
    ConfusionMatrixDisplay(matrix, display_labels=labels).plot(
        ax=axes, cmap="Blues", colorbar=False, xticks_rotation=30
    )
    axes.set_title("Confusion matrix on the held-out test set")
    figure.tight_layout()
    figure.savefig(ARTIFACTS / "confusion_matrix.png", dpi=160)
    plt.close(figure)


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    data = load_dataset()
    print(f"Dataset: {len(data)} rows after cleaning\n")

    # Stratify keeps the same category mix in both parts. The test set is set
    # aside now and is not touched again until the final evaluation below.
    train_text, test_text, train_labels, test_labels = train_test_split(
        data["text"],
        data["category"],
        test_size=TEST_SIZE,
        stratify=data["category"],
        random_state=RANDOM_STATE,
    )

    comparison = compare_with_cross_validation(train_text, train_labels)

    pipelines = candidate_pipelines()
    baseline = pipelines["baseline_most_frequent"].fit(train_text, train_labels)
    baseline_predictions = baseline.predict(test_text)

    model = pipelines[DEPLOYED_MODEL].fit(train_text, train_labels)
    predictions = model.predict(test_text)

    labels = sorted(data["category"].unique())
    report = classification_report(
        test_labels, predictions, labels=labels, output_dict=True, zero_division=0
    )
    print(f"\nFinal evaluation of {DEPLOYED_MODEL} on the test set:\n")
    print(
        classification_report(
            test_labels, predictions, labels=labels, digits=3, zero_division=0
        )
    )

    save_confusion_matrix(test_labels, predictions, labels)

    # Error analysis: keep every mistake so that a person can read them.
    mistakes = test_text[predictions != test_labels]
    errors = {
        "text": mistakes,
        "true_category": test_labels[predictions != test_labels],
        "predicted_category": predictions[predictions != test_labels],
    }
    pd.DataFrame(errors).to_csv(ARTIFACTS / "misclassified.csv", index=False)

    metrics = {
        "model": DEPLOYED_MODEL,
        "scikit_learn_version": sklearn.__version__,
        "rows": {"total": len(data), "train": len(train_text), "test": len(test_text)},
        "random_state": RANDOM_STATE,
        "labels": labels,
        "cross_validation": comparison,
        "test": {
            "accuracy": round(accuracy_score(test_labels, predictions), 4),
            "macro_f1": round(f1_score(test_labels, predictions, average="macro"), 4),
            "weighted_f1": round(f1_score(test_labels, predictions, average="weighted"), 4),
            "per_class": {
                label: {
                    "precision": round(report[label]["precision"], 4),
                    "recall": round(report[label]["recall"], 4),
                    "f1": round(report[label]["f1-score"], 4),
                    "support": int(report[label]["support"]),
                }
                for label in labels
            },
            "confusion_matrix": confusion_matrix(
                test_labels, predictions, labels=labels
            ).tolist(),
        },
        "baseline_test": {
            "accuracy": round(accuracy_score(test_labels, baseline_predictions), 4),
            "macro_f1": round(
                f1_score(
                    test_labels, baseline_predictions, average="macro", zero_division=0
                ),
                4,
            ),
        },
    }
    (ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    joblib.dump(model, ARTIFACTS / "category_model.joblib", compress=3)
    size_kb = (ARTIFACTS / "category_model.joblib").stat().st_size / 1024
    print(f"Saved model to {ARTIFACTS / 'category_model.joblib'} ({size_kb:.0f} KB)")
    print(f"Saved metrics, confusion matrix and {len(mistakes)} mistakes to {ARTIFACTS}")


if __name__ == "__main__":
    main()
