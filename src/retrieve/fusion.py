from __future__ import annotations

from src.domain.models import Candidate


class FusionEngine:
    def merge(
        self,
        *,
        dense: list[Candidate],
        lexical: list[Candidate],
        graph: list[Candidate],
    ) -> list[Candidate]:
        by_chunk_id: dict[str, Candidate] = {}

        for candidate in dense + lexical + graph:
            existing = by_chunk_id.get(candidate.chunk_id)
            if existing is None:
                by_chunk_id[candidate.chunk_id] = candidate
                continue

            merged_scores = {**existing.scores, **candidate.scores}
            by_chunk_id[candidate.chunk_id] = Candidate(
                chunk_id=candidate.chunk_id,
                note_id=candidate.note_id,
                path=candidate.path,
                text=candidate.text,
                source="hybrid",
                scores=merged_scores,
            )

        candidates = list(by_chunk_id.values())
        candidates.sort(key=_candidate_sort_key, reverse=True)
        return candidates


def _candidate_sort_key(candidate: Candidate) -> float:
    dense_score = candidate.scores.get("dense_score", 0.0)
    lexical_score = candidate.scores.get("lexical_score", 0.0)
    title_match = candidate.scores.get("title_match", 0.0)
    graph_score = candidate.scores.get("graph_score", 0.0)
    # title_match gets its own weight so title-matched notes beat
    # irrelevant high-volume body matches when dense retrieval misses them.
    return (
        (0.45 * dense_score)
        + (0.25 * lexical_score)
        + (0.20 * title_match)
        + (0.10 * graph_score)
    )
