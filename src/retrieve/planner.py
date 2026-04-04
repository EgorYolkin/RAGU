from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalPlan:
    lexical_k: int = 10
    graph_k: int = 10
    seed_k: int = 5


class QueryPlanner:
    def plan(self, query: str) -> RetrievalPlan:
        if len(query.split()) <= 2:
            return RetrievalPlan(lexical_k=8, graph_k=6, seed_k=4)
        return RetrievalPlan()
