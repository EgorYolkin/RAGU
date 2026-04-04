from __future__ import annotations

from src.domain.models import Candidate
from src.retrieve.fusion import FusionEngine
from src.retrieve.graph import SQLiteGraphRetriever
from src.retrieve.lexical import SQLiteLexicalRetriever
from src.retrieve.planner import QueryPlanner


class RetrievalService:
    def __init__(
        self,
        *,
        planner: QueryPlanner,
        lexical_retriever: SQLiteLexicalRetriever,
        graph_retriever: SQLiteGraphRetriever,
        fusion_engine: FusionEngine,
    ) -> None:
        self.planner = planner
        self.lexical_retriever = lexical_retriever
        self.graph_retriever = graph_retriever
        self.fusion_engine = fusion_engine

    def retrieve(self, query: str) -> list[Candidate]:
        plan = self.planner.plan(query)
        lexical_candidates = self.lexical_retriever.retrieve(query, plan.lexical_k)
        seed_note_ids = [
            candidate.note_id for candidate in lexical_candidates[: plan.seed_k]
        ]
        graph_candidates = self.graph_retriever.retrieve(
            query,
            seed_note_ids=seed_note_ids,
            limit=plan.graph_k,
        )
        return self.fusion_engine.merge(
            lexical=lexical_candidates,
            graph=graph_candidates,
        )
