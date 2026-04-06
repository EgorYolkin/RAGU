from __future__ import annotations

import argparse
import logging
import time

from src.core.config import Settings
from src.core.logging import configure_logging
from src.core.timing import PipelineTimer
from src.ingest.embedder import OllamaEmbedder
from src.retrieve.dense import SQLiteDenseRetriever
from src.retrieve.fusion import FusionEngine
from src.retrieve.graph import SQLiteGraphRetriever
from src.retrieve.lexical import SQLiteLexicalRetriever
from src.retrieve.planner import QueryPlanner
from src.retrieve.rerank import FlagEmbeddingReranker, NoOpReranker
from src.retrieve.service import RetrievalService
from src.storage.sqlite_db import SQLiteDatabase
from src.synth.answerer import OllamaAnswerer, UsageMetrics
from src.synth.context_compiler import ContextCompiler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query local notes through Ollama.")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print timing breakdown, retrieval shortlist, and LLM metrics.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_logging(level=logging.DEBUG if args.debug else logging.WARNING)

    settings = Settings.from_env()
    database = SQLiteDatabase(settings.sqlite_path)
    embedder = OllamaEmbedder(
        base_url=settings.ollama_base_url,
        model=settings.embedding_model,
        keep_alive=settings.ollama_keep_alive,
    )
    reranker = build_reranker(settings)
    retrieval_service = RetrievalService(
        planner=QueryPlanner(
            rerank_k=settings.rerank_top_k,
            final_k=settings.final_top_k,
        ),
        dense_retriever=SQLiteDenseRetriever(
            database=database,
            embedder=embedder,
            embedding_model=settings.embedding_model,
        ),
        lexical_retriever=SQLiteLexicalRetriever(database),
        graph_retriever=SQLiteGraphRetriever(database),
        fusion_engine=FusionEngine(),
        reranker=reranker,
    )

    timer = PipelineTimer()
    wall_start = time.perf_counter()

    with timer.span("retrieval"):
        candidates = retrieval_service.retrieve(args.query, timer=timer)

    compiler = ContextCompiler(token_budget=settings.context_token_budget)
    with timer.span("compile"):
        compiled_context = compiler.compile(args.query, candidates)

    answerer = OllamaAnswerer(
        base_url=settings.ollama_base_url,
        model=settings.generator_model,
        keep_alive=settings.ollama_keep_alive,
    )

    usage: UsageMetrics | None = None
    with timer.span("llm_total"):
        for token in answerer.stream_answer(compiled_context):
            if isinstance(token, UsageMetrics):
                usage = token
            else:
                print(token, end="", flush=True)
    print()

    wall_ms = (time.perf_counter() - wall_start) * 1000
    timer.record("wall_total", wall_ms)

    print()
    print("Sources:")
    for citation in compiled_context.citations:
        print(f"- {citation}")
    if compiled_context.related_notes:
        print()
        print("Related notes:")
        for path in compiled_context.related_notes[:5]:
            print(f"- {path}")

    if args.debug:
        print()
        print("── Timing breakdown ─────────────────────")
        print(timer.summary())

        if usage:
            print()
            print("── LLM metrics ──────────────────────────")
            ttft = f"{usage.ttft_ms:.0f}ms" if usage.ttft_ms is not None else "n/a"
            tps = f"{usage.tokens_per_second:.1f}" if usage.tokens_per_second else "n/a"
            gen_ms = f"{(usage.eval_duration or 0) / 1_000_000:.0f}ms"
            load_ms = f"{(usage.load_duration or 0) / 1_000_000:.0f}ms"
            print(f"  model load        {load_ms:>10}")
            print(f"  time-to-1st-tok   {ttft:>10}")
            print(f"  generation        {gen_ms:>10}")
            print(f"  tokens generated  {usage.eval_count or 'n/a':>10}")
            print(f"  tokens/sec        {tps:>10}")
            print(f"  prompt tokens     {usage.prompt_eval_count or 'n/a':>10}")

        print()
        print("── Candidates ───────────────────────────")
        for candidate in candidates:
            print(f"  {candidate.path}")
            print(f"    chunk_id={candidate.chunk_id}  scores={candidate.scores}")


def build_reranker(settings: Settings):
    try:
        from FlagEmbedding import FlagReranker  # noqa: F401

        return FlagEmbeddingReranker(model_name=settings.reranker_model)
    except ModuleNotFoundError:
        return NoOpReranker()


if __name__ == "__main__":
    main()
