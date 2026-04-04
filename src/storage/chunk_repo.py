from __future__ import annotations

import json
from sqlite3 import Connection

from src.domain.models import Chunk


class ChunkRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def replace_for_note(self, note_id: str, chunks: list[Chunk]) -> None:
        self.connection.execute("DELETE FROM chunks WHERE note_id = ?", (note_id,))
        if chunks:
            paths = {chunk.path for chunk in chunks}
            self.connection.executemany(
                "DELETE FROM chunks_fts WHERE path = ?",
                [(path,) for path in paths],
            )
        self.connection.executemany(
            """
            INSERT INTO chunks(
                chunk_id,
                note_id,
                path,
                heading_path,
                chunk_text,
                chunk_order,
                token_count
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.chunk_id,
                    chunk.note_id,
                    chunk.path,
                    json.dumps(chunk.heading_path),
                    chunk.text,
                    chunk.chunk_order,
                    chunk.token_count,
                )
                for chunk in chunks
            ],
        )
        self.connection.executemany(
            """
            INSERT INTO chunks_fts(
                chunk_id,
                note_id,
                path,
                heading_path,
                chunk_text
            )
            VALUES(?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk.chunk_id,
                    chunk.note_id,
                    chunk.path,
                    json.dumps(chunk.heading_path),
                    chunk.text,
                )
                for chunk in chunks
            ],
        )
