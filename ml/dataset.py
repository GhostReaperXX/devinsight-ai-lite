"""Load the labeled dataset and check its quality before anything is trained on it."""

from pathlib import Path

import pandas as pd

from app.ml.text import combine_text

DATA_FILE = Path("data/issues_labeled.csv")
REQUIRED_COLUMNS = {"title", "description", "category"}
CATEGORIES = {"bug", "feature", "documentation", "performance", "security"}


def load_dataset(path: Path = DATA_FILE) -> pd.DataFrame:
    """Return a clean DataFrame with the columns text and category."""
    data = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    unknown = set(data["category"].dropna().unique()) - CATEGORIES
    if unknown:
        raise ValueError(f"{path} has unknown categories: {sorted(unknown)}")

    data = data.dropna(subset=["title", "description", "category"])
    # An identical report in both train and test would inflate the score: this is leakage.
    data = data.drop_duplicates(subset=["title", "description"])

    data = data.assign(
        text=[
            combine_text(t, d)
            for t, d in zip(data["title"], data["description"], strict=True)
        ]
    )
    return data[["text", "category"]].reset_index(drop=True)
