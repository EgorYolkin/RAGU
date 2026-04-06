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
            # Resolve wikilink targets to actual note paths using three strategies:
            # 1. Exact path match (target_path = notes.path)
            # 2. Basename match: "notes/people.md" → "People.md"
            #    (case-insensitive filename stem comparison)
            # 3. Backlinks: notes that link TO any seed note
            rows = connection.execute(
                f"""
                WITH outbound_targets AS (
                    SELECT DISTINCT target_path
                    FROM links
                    WHERE source_path IN ({path_placeholders})
                ),
                resolved_outbound AS (
                    -- exact match
                    SELECT DISTINCT n.path
                    FROM outbound_targets ot
                    JOIN notes n ON n.path = ot.target_path
                    UNION
                    -- basename match (handles [[WikiLink]] → any/folder/WikiLink.md)
                    SELECT DISTINCT n.path
                    FROM outbound_targets ot
                    JOIN notes n ON lower(
                        CASE
                            WHEN instr(n.path, '/') > 0
                            THEN substr(n.path, length(n.path) - length(n.path) + instr(n.path, '/') + 1)
                            ELSE n.path
                        END
                    ) = lower(
                        CASE
                            WHEN instr(ot.target_path, '/') > 0
                            THEN substr(ot.target_path, length(ot.target_path) - length(ot.target_path) + instr(ot.target_path, '/') + 1)
                            ELSE ot.target_path
                        END
                    )
                ),
                inbound_sources AS (
                    SELECT DISTINCT source_path AS path
                    FROM links
                    WHERE target_path IN ({path_placeholders})
                ),
                neighbor_paths AS (
                    SELECT path FROM resolved_outbound
                    UNION
                    SELECT path FROM inbound_sources
                )
                SELECT
                    chunks.chunk_id,
                    chunks.note_id,
                    chunks.path,
                    chunks.chunk_text
                FROM neighbor_paths
                JOIN chunks ON chunks.path = neighbor_paths.path
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
