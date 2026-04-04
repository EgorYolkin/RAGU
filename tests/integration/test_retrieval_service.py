from src.ingest.chunker import MarkdownChunker
from src.ingest.parser import MarkdownNoteParser
from src.ingest.source import FileSystemNoteSource
from src.retrieve.fusion import FusionEngine
from src.retrieve.graph import SQLiteGraphRetriever
from src.retrieve.lexical import SQLiteLexicalRetriever
from src.retrieve.planner import QueryPlanner
from src.retrieve.service import RetrievalService
from src.services.indexing_service import IndexingService
from src.storage.sqlite_db import SQLiteDatabase


def test_retrieval_service_returns_lexical_and_graph_candidates(tmp_path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "rag.md").write_text(
        (
            "# RAG\n\n"
            "Hybrid retrieval uses lexical and graph signals.\n\n"
            "[[context-engineering]]\n"
        ),
        encoding="utf-8",
    )
    (vault_path / "context-engineering.md").write_text(
        "# Context Engineering\n\nContext compilation improves answer quality.\n",
        encoding="utf-8",
    )
    (vault_path / "unrelated.md").write_text(
        "# Gardening\n\nTomatoes need water.\n",
        encoding="utf-8",
    )

    database = SQLiteDatabase(tmp_path / "app.db")
    indexing_service = IndexingService(
        source=FileSystemNoteSource(vault_path),
        parser=MarkdownNoteParser(),
        chunker=MarkdownChunker(chunk_size=50, chunk_overlap=10),
        database=database,
    )
    indexing_service.reindex_all()

    service = RetrievalService(
        planner=QueryPlanner(),
        lexical_retriever=SQLiteLexicalRetriever(database),
        graph_retriever=SQLiteGraphRetriever(database),
        fusion_engine=FusionEngine(),
    )

    candidates = service.retrieve("hybrid retrieval")

    assert candidates
    assert candidates[0].path == "rag.md"
    assert any(candidate.path == "context-engineering.md" for candidate in candidates)
    assert all(candidate.path != "unrelated.md" for candidate in candidates[:2])
