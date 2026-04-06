from __future__ import annotations

from src.domain.models import Candidate


class NoOpReranker:
    def rerank(self, query: str, candidates: list[Candidate]) -> list[Candidate]:
        del query
        return candidates


class FlagEmbeddingReranker:
    def __init__(
        self,
        *,
        model_name: str,
        use_fp16: bool = False,
        devices: list[str] | None = None,
    ) -> None:
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.devices = devices
        self._reranker = None

    def rerank(self, query: str, candidates: list[Candidate]) -> list[Candidate]:
        if not candidates:
            return []

        reranker = self._load_reranker()
        pairs = [[query, candidate.text] for candidate in candidates]
        scores = reranker.compute_score(pairs, normalize=True)

        reranked: list[Candidate] = []
        for candidate, score in zip(candidates, scores, strict=True):
            reranked.append(
                Candidate(
                    chunk_id=candidate.chunk_id,
                    note_id=candidate.note_id,
                    path=candidate.path,
                    text=candidate.text,
                    source="hybrid",
                    scores={**candidate.scores, "rerank_score": float(score)},
                )
            )

        reranked.sort(
            key=lambda candidate: candidate.scores.get("rerank_score", 0.0),
            reverse=True,
        )
        return reranked

    def _load_reranker(self):
        if self._reranker is not None:
            return self._reranker

        from FlagEmbedding import FlagReranker

        kwargs = {
            "query_max_length": 256,
            "passage_max_length": 512,
            "use_fp16": self.use_fp16,
        }
        if self.devices:
            kwargs["devices"] = self.devices

        self._reranker = FlagReranker(self.model_name, **kwargs)
        return self._reranker
