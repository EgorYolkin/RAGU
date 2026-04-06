from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from src.core.timing import PipelineTimer
from src.domain.models import Candidate
from src.retrieve.dense import SQLiteDenseRetriever
from src.retrieve.fusion import FusionEngine
from src.retrieve.graph import SQLiteGraphRetriever
from src.retrieve.lexical import SQLiteLexicalRetriever
from src.retrieve.planner import QueryPlanner
from src.retrieve.rerank import NoOpReranker

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        *,
        planner: QueryPlanner,
        dense_retriever: SQLiteDenseRetriever,
        lexical_retriever: SQLiteLexicalRetriever,
        graph_retriever: SQLiteGraphRetriever,
        fusion_engine: FusionEngine,
        reranker: NoOpReranker,
    ) -> None:
        self.planner = planner
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.graph_retriever = graph_retriever
        self.fusion_engine = fusion_engine
        self.reranker = reranker

    def retrieve(
        self, query: str, timer: PipelineTimer | None = None
    ) -> list[Candidate]:
        t = timer or PipelineTimer()
        plan = self.planner.plan(query)

        # Dense and lexical run in parallel; each uses its own local timer
        # so writes don't race. We merge results into the shared timer after.
        dense_local = PipelineTimer()
        lexical_local = PipelineTimer()

        with t.span("parallel_retrieval"):
            with ThreadPoolExecutor(max_workers=2) as executor:
                dense_future = executor.submit(
                    self.dense_retriever.retrieve, query, plan.dense_k, dense_local
                )
                lexical_future = executor.submit(
                    self._retrieve_lexical, query, plan.lexical_k, lexical_local
                )
                dense_candidates = dense_future.result()
                lexical_candidates = lexical_future.result()

        # Merge sub-timings into the shared timer
        for name, ms in dense_local._spans.items():
            t.record(f"  dense.{name}", ms)
        for name, ms in lexical_local._spans.items():
            t.record(f"  lexical.{name}", ms)

        seed_note_ids = [
            candidate.note_id
            for candidate in (dense_candidates + lexical_candidates)[: plan.seed_k]
        ]
        with t.span("graph"):
            graph_candidates = self.graph_retriever.retrieve(
                query,
                seed_note_ids=seed_note_ids,
                limit=plan.graph_k,
            )

        with t.span("fusion"):
            fused_candidates = self.fusion_engine.merge(
                dense=dense_candidates,
                lexical=lexical_candidates,
                graph=graph_candidates,
            )

        with t.span("rerank"):
            reranked_candidates = self.reranker.rerank(
                query,
                fused_candidates[: plan.rerank_k],
            )

        logger.debug(
            "retrieval: dense=%d lexical=%d graph=%d fused=%d final=%d",
            len(dense_candidates),
            len(lexical_candidates),
            len(graph_candidates),
            len(fused_candidates),
            len(reranked_candidates[: plan.final_k]),
        )
        return reranked_candidates[: plan.final_k]

    def _retrieve_lexical(
        self, query: str, limit: int, timer: PipelineTimer
    ) -> list[Candidate]:
        with timer.span("db"):
            return self.lexical_retriever.retrieve(query, limit)
