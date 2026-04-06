from __future__ import annotations

import logging

import numpy as np

from src.core.timing import PipelineTimer
from src.domain.models import Candidate
from src.ingest.embedder import OllamaEmbedder
from src.storage.sqlite_db import SQLiteDatabase

logger = logging.getLogger(__name__)


class SQLiteDenseRetriever:
    def __init__(
        self,
        *,
        database: SQLiteDatabase,
        embedder: OllamaEmbedder,
        embedding_model: str,
    ) -> None:
        self.database = database
        self.embedder = embedder
        self.embedding_model = embedding_model

    def retrieve(
        self,
        query: str,
        limit: int,
        timer: PipelineTimer | None = None,
    ) -> list[Candidate]:
        t = timer or PipelineTimer()
        query = query.strip()
        if not query:
            return []

        with t.span("embed"):
            query_embedding = self.embedder.embed([query])[0]
        query_vec = np.array(query_embedding, dtype=np.float32)

        with t.span("db_fetch"):
            with self.database.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        chunks.chunk_id,
                        chunks.note_id,
                        chunks.path,
                        chunks.chunk_text,
                        chunk_embeddings.embedding_blob
                    FROM chunk_embeddings
                    JOIN chunks ON chunks.chunk_id = chunk_embeddings.chunk_id
                    WHERE chunk_embeddings.model = ?
                    """,
                    (self.embedding_model,),
                ).fetchall()

        if not rows:
            return []

        with t.span("cosine"):
            dim = len(query_embedding)
            matrix = np.frombuffer(
                b"".join(row["embedding_blob"] for row in rows),
                dtype=np.float32,
            ).reshape(len(rows), dim)

            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0.0:
                return []
            query_unit = query_vec / query_norm

            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            unit_matrix = matrix / norms

            scores = unit_matrix @ query_unit

        top_indices = np.argpartition(scores, -min(limit, len(scores)))[-limit:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        logger.debug(
            "dense: embed=%.0fms db=%.0fms cosine=%.0fms chunks=%d",
            t.get("embed") or 0,
            t.get("db_fetch") or 0,
            t.get("cosine") or 0,
            len(rows),
        )

        return [
            Candidate(
                chunk_id=rows[i]["chunk_id"],
                note_id=rows[i]["note_id"],
                path=rows[i]["path"],
                text=rows[i]["chunk_text"],
                source="dense",
                scores={"dense_score": float(scores[i])},
            )
            for i in top_indices
        ]
