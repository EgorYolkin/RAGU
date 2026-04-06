from __future__ import annotations

from sqlite3 import Connection

import numpy as np

from src.domain.models import Chunk


class EmbeddingRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def replace_for_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        *,
        model: str,
    ) -> None:
        if not chunks:
            return
        self.connection.executemany(
            "DELETE FROM chunk_embeddings WHERE chunk_id = ?",
            [(chunk.chunk_id,) for chunk in chunks],
        )
        self.connection.executemany(
            """
            INSERT INTO chunk_embeddings(chunk_id, embedding_blob, model)
            VALUES(?, ?, ?)
            """,
            [
                (
                    chunk.chunk_id,
                    np.array(embedding, dtype=np.float32).tobytes(),
                    model,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ],
        )
