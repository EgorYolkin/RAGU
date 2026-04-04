from __future__ import annotations

from src.core.config import Settings
from src.ingest.chunker import MarkdownChunker
from src.ingest.parser import MarkdownNoteParser
from src.ingest.source import FileSystemNoteSource
from src.services.indexing_service import IndexingService
from src.storage.sqlite_db import SQLiteDatabase


def main() -> None:
    settings = Settings.from_env()
    service = IndexingService(
        source=FileSystemNoteSource(settings.vault_path),
        parser=MarkdownNoteParser(),
        chunker=MarkdownChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        database=SQLiteDatabase(settings.sqlite_path),
    )
    stats = service.reindex_all()
    print(
        f"indexed_notes={stats.indexed_notes} skipped_notes={stats.skipped_notes}"
    )


if __name__ == "__main__":
    main()
