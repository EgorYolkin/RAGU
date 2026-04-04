from src.ingest.chunker import MarkdownChunker
from src.ingest.parser import MarkdownNoteParser
from src.ingest.source import FileSystemNoteSource
from src.services.indexing_service import IndexingService
from src.storage.sqlite_db import SQLiteDatabase


def test_links_store_target_anchor_and_attachment_targets(tmp_path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "alpha.md").write_text(
        "# Alpha\n\nSee [[beta#Section]] and ![[image.png]].\n",
        encoding="utf-8",
    )

    database = SQLiteDatabase(tmp_path / "app.db")
    service = IndexingService(
        source=FileSystemNoteSource(vault_path),
        parser=MarkdownNoteParser(),
        chunker=MarkdownChunker(chunk_size=50, chunk_overlap=10),
        database=database,
    )

    service.reindex_all()

    with database.connect() as connection:
        rows = connection.execute(
            """
            SELECT target_path, target_anchor, edge_type
            FROM links
            ORDER BY target_path
            """
        ).fetchall()

    assert [(row[0], row[1], row[2]) for row in rows] == [
        ("beta.md", "Section", "links_to_heading"),
        ("image.png", None, "embed"),
    ]
