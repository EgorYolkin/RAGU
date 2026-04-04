from __future__ import annotations

from dataclasses import dataclass

from src.domain.protocols import Chunker, NoteParser, NoteSource
from src.storage.chunk_repo import ChunkRepository
from src.storage.link_repo import LinkRepository
from src.storage.note_repo import NoteRepository
from src.storage.sqlite_db import SQLiteDatabase


@dataclass(frozen=True)
class IndexingStats:
    indexed_notes: int
    skipped_notes: int


class IndexingService:
    def __init__(
        self,
        *,
        source: NoteSource,
        parser: NoteParser,
        chunker: Chunker,
        database: SQLiteDatabase,
    ) -> None:
        self.source = source
        self.parser = parser
        self.chunker = chunker
        self.database = database

    def reindex_all(self) -> IndexingStats:
        self.database.initialize()
        indexed_notes = 0
        skipped_notes = 0

        with self.database.connect() as connection:
            note_repo = NoteRepository(connection)
            chunk_repo = ChunkRepository(connection)
            link_repo = LinkRepository(connection)

            for path in self.source.list_paths():
                raw_note = self.source.read_note(path)
                if raw_note.read_status != "ok" or raw_note.text is None:
                    skipped_notes += 1
                    continue

                parsed_note = self.parser.parse(raw_note)
                chunks = self.chunker.chunk(parsed_note)

                note_repo.upsert(parsed_note, raw_note.mtime)
                chunk_repo.replace_for_note(parsed_note.note_id, chunks)
                link_repo.replace_for_source(parsed_note.path, list(parsed_note.links))
                indexed_notes += 1

            connection.commit()

        return IndexingStats(indexed_notes=indexed_notes, skipped_notes=skipped_notes)
