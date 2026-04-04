from __future__ import annotations

from src.domain.models import Candidate


class FusionEngine:
    def merge(
        self,
        *,
        lexical: list[Candidate],
        graph: list[Candidate],
    ) -> list[Candidate]:
        by_chunk_id: dict[str, Candidate] = {}

        for candidate in lexical + graph:
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
    lexical_score = candidate.scores.get("lexical_score", 0.0)
    graph_score = candidate.scores.get("graph_score", 0.0)
    return (0.7 * lexical_score) + (0.3 * graph_score)
