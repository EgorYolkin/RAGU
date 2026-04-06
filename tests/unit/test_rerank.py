from src.domain.models import Candidate
from src.retrieve.rerank import NoOpReranker


def test_noop_reranker_preserves_candidate_order() -> None:
    candidates = [
        Candidate(
            chunk_id="c1",
            note_id="n1",
            path="a.md",
            text="alpha",
            source="lexical",
            scores={"lexical_score": 0.5},
        ),
        Candidate(
            chunk_id="c2",
            note_id="n2",
            path="b.md",
            text="beta",
            source="dense",
            scores={"dense_score": 0.7},
        ),
    ]

    reranked = NoOpReranker().rerank("query", candidates)

    assert reranked == candidates
