"""Find similar issue reports with TF-IDF vectors and cosine similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class SimilarityIndex:
    """An in-memory index of issue texts. Build it once, then ask it questions."""

    def __init__(self, ids: list[int], texts: list[str]) -> None:
        self._ids = ids
        self._vectorizer = None
        self._matrix = None
        if texts:
            # TF-IDF rows are scaled to length 1, so a plain dot product IS the cosine.
            self._vectorizer = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            self._matrix = self._vectorizer.fit_transform(texts)

    def query(
        self, text: str, top_k: int, min_score: float, exclude_id: int | None = None
    ) -> list[tuple[int, float]]:
        """Return up to top_k (issue id, score) pairs, best first."""
        if self._matrix is None:
            return []
        scores = linear_kernel(self._vectorizer.transform([text]), self._matrix)[0]
        pairs = zip(self._ids, scores, strict=True)
        ranked = sorted(pairs, key=lambda pair: pair[1], reverse=True)
        return [
            (issue_id, round(float(score), 3))
            for issue_id, score in ranked
            if score >= min_score and issue_id != exclude_id
        ][:top_k]

    def similar_pairs(self, min_score: float) -> list[tuple[int, int, float]]:
        """Return every pair of issues whose similarity reaches min_score, best first."""
        if self._matrix is None:
            return []
        scores = linear_kernel(self._matrix)
        pairs = [
            (self._ids[i], self._ids[j], round(float(scores[i, j]), 3))
            for i in range(len(self._ids))
            for j in range(i + 1, len(self._ids))
            if scores[i, j] >= min_score
        ]
        return sorted(pairs, key=lambda pair: pair[2], reverse=True)
