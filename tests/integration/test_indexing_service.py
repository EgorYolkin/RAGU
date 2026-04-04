import sqlite3

from src.ingest.chunker import MarkdownChunker
from src.ingest.parser import MarkdownNoteParser
from src.ingest.source import FileSystemNoteSource
from src.services.indexing_service import IndexingService
from src.storage.sqlite_db import SQLiteDatabase


def test_indexing_service_reindexes_markdown_vault(tmp_path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "alpha.md").write_text(
        "# Alpha\n\nThis note links to [[beta]].\n",
        encoding="utf-8",
    )
    (vault_path / "beta.md").write_text(
        "---\ntags: [test]\n---\n# Beta\n\nSecond note.\n",
        encoding="utf-8",
    )

    database = SQLiteDatabase(tmp_path / "app.db")
    service = IndexingService(
        source=FileSystemNoteSource(vault_path),
        parser=MarkdownNoteParser(),
        chunker=MarkdownChunker(chunk_size=50, chunk_overlap=10),
        database=database,
    )

    stats = service.reindex_all()

    assert stats.indexed_notes == 2
    assert stats.skipped_notes == 0

    with sqlite3.connect(tmp_path / "app.db") as connection:
        note_count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        link_count = connection.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        tag_count = connection.execute("SELECT COUNT(*) FROM tags").fetchone()[0]

    assert note_count == 2
    assert chunk_count >= 2
    assert link_count == 1
    assert tag_count == 1
