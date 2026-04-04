from __future__ import annotations

from src.domain.models import Candidate
from src.storage.sqlite_db import SQLiteDatabase


class SQLiteGraphRetriever:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def retrieve(
        self,
        query: str,
        seed_note_ids: list[str],
        limit: int,
    ) -> list[Candidate]:
        if not seed_note_ids:
            return []

        placeholders = ", ".join("?" for _ in seed_note_ids)
        with self.database.connect() as connection:
            seed_paths = [
                row["path"]
                for row in connection.execute(
                    f"SELECT path FROM notes WHERE note_id IN ({placeholders})",
                    seed_note_ids,
                ).fetchall()
            ]
            if not seed_paths:
                return []

            path_placeholders = ", ".join("?" for _ in seed_paths)
            rows = connection.execute(
                f"""
                WITH neighbor_paths AS (
                    SELECT DISTINCT target_path AS path
                    FROM links
                    WHERE source_path IN ({path_placeholders})
                    UNION
                    SELECT DISTINCT source_path AS path
                    FROM links
                    WHERE target_path IN ({path_placeholders})
                )
                SELECT
                    chunks.chunk_id,
                    chunks.note_id,
                    chunks.path,
                    chunks.chunk_text
                FROM neighbor_paths
                JOIN chunks ON chunks.path = neighbor_paths.path
                ORDER BY chunks.token_count DESC
                LIMIT ?
                """,
                [*seed_paths, *seed_paths, limit],
            ).fetchall()

        return [
            Candidate(
                chunk_id=row["chunk_id"],
                note_id=row["note_id"],
                path=row["path"],
                text=row["chunk_text"],
                source="graph",
                scores={"graph_score": 1.0},
            )
            for row in rows
        ]
