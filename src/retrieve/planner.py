from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalPlan:
    dense_k: int = 12
    lexical_k: int = 10
    graph_k: int = 10
    seed_k: int = 5
    rerank_k: int = 24
    final_k: int = 6


class QueryPlanner:
    def __init__(self, *, rerank_k: int = 24, final_k: int = 6) -> None:
        self.rerank_k = rerank_k
        self.final_k = final_k

    def plan(self, query: str) -> RetrievalPlan:
        if len(query.split()) <= 2:
            return RetrievalPlan(
                dense_k=10,
                lexical_k=8,
                graph_k=6,
                seed_k=4,
                rerank_k=min(16, self.rerank_k),
                final_k=min(5, self.final_k),
            )
        return RetrievalPlan(rerank_k=self.rerank_k, final_k=self.final_k)
