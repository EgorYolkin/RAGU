from __future__ import annotations

import re

from src.domain.models import Candidate
from src.storage.sqlite_db import SQLiteDatabase


class SQLiteLexicalRetriever:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def retrieve(self, query: str, limit: int) -> list[Candidate]:
        match_query = build_match_query(query)
        if not match_query:
            return []

        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunk_id,
                    note_id,
                    path,
                    chunk_text,
                    bm25(chunks_fts) AS rank
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, limit),
            ).fetchall()

        return [
            Candidate(
                chunk_id=row["chunk_id"],
                note_id=row["note_id"],
                path=row["path"],
                text=row["chunk_text"],
                source="lexical",
                scores={
                    "lexical_rank": float(row["rank"]),
                    "lexical_score": _rank_to_score(float(row["rank"])),
                },
            )
            for row in rows
        ]


def _rank_to_score(rank: float) -> float:
    safe_rank = rank if rank > 0 else 0.0
    return 1.0 / (1.0 + safe_rank)


TOKEN_RE = re.compile(r"[\w\-]+", re.UNICODE)


def build_match_query(query: str) -> str:
    tokens = [token.lower() for token in TOKEN_RE.findall(query)]
    if not tokens:
        return ""

    unique_tokens: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique_tokens.append(token)

    return " OR ".join(f'"{token}"' for token in unique_tokens)
