import numpy as np

from src.retrieve.dense import SQLiteDenseRetriever


def _cosine(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def test_cosine_similarity_returns_expected_scores() -> None:
    assert round(_cosine([1.0, 0.0], [1.0, 0.0]), 6) == 1.0
    assert round(_cosine([1.0, 0.0], [0.0, 1.0]), 6) == 0.0
