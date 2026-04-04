from __future__ import annotations

import argparse

from src.core.config import Settings
from src.retrieve.fusion import FusionEngine
from src.retrieve.graph import SQLiteGraphRetriever
from src.retrieve.lexical import SQLiteLexicalRetriever
from src.retrieve.planner import QueryPlanner
from src.retrieve.service import RetrievalService
from src.storage.sqlite_db import SQLiteDatabase
from src.synth.answerer import OllamaAnswerer
from src.synth.context_compiler import ContextCompiler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query local notes through Ollama.")
    parser.add_argument("query", help="Natural language query")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.from_env()
    database = SQLiteDatabase(settings.sqlite_path)
    retrieval_service = RetrievalService(
        planner=QueryPlanner(),
        lexical_retriever=SQLiteLexicalRetriever(database),
        graph_retriever=SQLiteGraphRetriever(database),
        fusion_engine=FusionEngine(),
    )
    candidates = retrieval_service.retrieve(args.query)
    compiler = ContextCompiler()
    compiled_context = compiler.compile(args.query, candidates)
    answerer = OllamaAnswerer(
        base_url=settings.ollama_base_url,
        model=settings.generator_model,
    )
    result = answerer.answer(compiled_context)

    print(result.answer)
    print()
    print("Sources:")
    for citation in result.citations:
        print(f"- {citation}")
    if result.related_notes:
        print()
        print("Related notes:")
        for path in result.related_notes[:5]:
            print(f"- {path}")


if __name__ == "__main__":
    main()
