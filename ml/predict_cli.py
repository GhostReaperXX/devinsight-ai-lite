"""Try the saved model from the terminal.

Run from the project root:
    python -m ml.predict_cli "Login page times out" "It spins for a minute"
"""

import sys

import joblib

from app.ml.text import combine_text

MODEL_FILE = "ml/artifacts/category_model.joblib"


def main() -> None:
    if len(sys.argv) != 3:
        print('Usage: python -m ml.predict_cli "title" "description"')
        raise SystemExit(1)

    model = joblib.load(MODEL_FILE)
    text = combine_text(sys.argv[1], sys.argv[2])
    probabilities = model.predict_proba([text])[0]
    pairs = zip(model.classes_, probabilities, strict=True)
    ranked = sorted(pairs, key=lambda pair: pair[1], reverse=True)
    for category, probability in ranked:
        print(f"{category:<15} {probability:6.1%}")


if __name__ == "__main__":
    main()
