from __future__ import annotations

from dataclasses import dataclass

from src.domain.protocols import Chunker, Embedder, NoteParser, NoteSource
from src.storage.chunk_repo import ChunkRepository
from src.storage.embedding_repo import EmbeddingRepository
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
        embedder: Embedder | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.source = source
        self.parser = parser
        self.chunker = chunker
        self.database = database
        self.embedder = embedder
        self.embedding_model = embedding_model

    def reindex_all(self) -> IndexingStats:
        self.database.initialize()
        indexed_notes = 0
        skipped_notes = 0

        all_paths = self.source.list_paths()
        # Give the parser the full path list so it can resolve [[wikilinks]]
        # to actual vault paths (e.g. [[People]] → notes/people/People.md).
        if hasattr(self.parser, "set_paths"):
            self.parser.set_paths(all_paths)

        with self.database.connect() as connection:
            note_repo = NoteRepository(connection)
            chunk_repo = ChunkRepository(connection)
            embedding_repo = EmbeddingRepository(connection)
            link_repo = LinkRepository(connection)

            for path in all_paths:
                raw_note = self.source.read_note(path)
                if raw_note.read_status != "ok" or raw_note.text is None:
                    skipped_notes += 1
                    continue

                parsed_note = self.parser.parse(raw_note)
                chunks = self.chunker.chunk(parsed_note)

                note_repo.upsert(parsed_note, raw_note.mtime)
                chunk_repo.replace_for_note(parsed_note.note_id, chunks)
                if self.embedder and self.embedding_model:
                    title = parsed_note.title
                    texts_for_embedding = [
                        f"{title}\n{chunk.text}" for chunk in chunks
                    ]
                    embeddings = self.embedder.embed(texts_for_embedding)
                    embedding_repo.replace_for_chunks(
                        chunks,
                        embeddings,
                        model=self.embedding_model,
                    )
                link_repo.replace_for_source(parsed_note.path, list(parsed_note.links))
                indexed_notes += 1

            connection.commit()

        return IndexingStats(indexed_notes=indexed_notes, skipped_notes=skipped_notes)
