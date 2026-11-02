"""Choose the duplicate threshold from labeled pairs instead of guessing it.

Run from the project root: python -m ml.evaluate_similarity
"""

import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

PAIRS_FILE = Path("data/duplicate_pairs.csv")
OUTPUT_FILE = Path("ml/artifacts/similarity_metrics.json")
THRESHOLDS = [round(0.05 * step, 2) for step in range(1, 13)]


def cosine_scores(pairs: pd.DataFrame):
    """Score each pair exactly as the application does: TF-IDF vectors and cosine."""
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    vectorizer.fit(pd.concat([pairs["text_a"], pairs["text_b"]]))
    first = vectorizer.transform(pairs["text_a"])
    second = vectorizer.transform(pairs["text_b"])
    # Both rows have length 1, so the sum of element-wise products is the cosine.
    return first.multiply(second).sum(axis=1).A1


def main() -> None:
    pairs = pd.read_csv(PAIRS_FILE)
    pairs["score"] = cosine_scores(pairs)
    truth = pairs["is_duplicate"]

    print(f"ROC AUC: {roc_auc_score(truth, pairs['score']):.3f}\n")
    print(f"{'threshold':>9} {'precision':>10} {'recall':>8} {'F1':>7} {'flagged':>8}")
    results = []
    for threshold in THRESHOLDS:
        flagged = pairs["score"] >= threshold
        row = {
            "threshold": threshold,
            "precision": round(precision_score(truth, flagged, zero_division=0), 3),
            "recall": round(recall_score(truth, flagged, zero_division=0), 3),
            "f1": round(f1_score(truth, flagged, zero_division=0), 3),
            "flagged": int(flagged.sum()),
        }
        results.append(row)
        print(
            f"{threshold:>9.2f} {row['precision']:>10.3f} {row['recall']:>8.3f}"
            f" {row['f1']:>7.3f} {row['flagged']:>8}"
        )

    best = max(results, key=lambda row: row["f1"])
    print(f"\nBest F1 at threshold {best['threshold']:.2f}")

    # Which kinds of pair does a word-based method get wrong at that threshold?
    pairs["flagged"] = pairs["score"] >= best["threshold"]
    by_kind = pairs.groupby("difficulty").agg(
        pairs=("score", "size"),
        mean_score=("score", "mean"),
        flagged=("flagged", "sum"),
    )
    print(f"\n{by_kind.round(3)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "results": results,
        "best": best,
        "by_difficulty": by_kind.round(3).to_dict("index"),
    }
    OUTPUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
