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
            chunk_rows = connection.execute(
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

            # Title-scoped search: find notes whose TITLE matches the query.
            # Uses a column-specific FTS filter to avoid body noise.
            # Returns the first chunk of each matching note (one chunk per note).
            title_match = build_title_match_query(query)
            title_rows = []
            if title_match:
                raw_title_rows = connection.execute(
                    """
                    SELECT
                        c.chunk_id,
                        c.note_id,
                        c.path,
                        c.chunk_text,
                        bm25(notes_fts) AS rank,
                        c.chunk_order
                    FROM notes_fts
                    JOIN chunks c ON c.path = notes_fts.path
                    WHERE notes_fts MATCH ?
                    ORDER BY rank, c.chunk_order
                    LIMIT ?
                    """,
                    (title_match, max(limit // 2, 5) * 10),
                ).fetchall()
                # Keep only the first (best-ranked) chunk per note path
                seen_paths: set[str] = set()
                title_rows = []
                for row in raw_title_rows:
                    if row["path"] not in seen_paths:
                        seen_paths.add(row["path"])
                        title_rows.append(row)
                        if len(title_rows) >= max(limit // 2, 5):
                            break

        seen_chunk_ids: set[str] = set()
        candidates: list[Candidate] = []

        for row in chunk_rows:
            seen_chunk_ids.add(row["chunk_id"])
            candidates.append(
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
            )

        for row in title_rows:
            title_score = _rank_to_score(float(row["rank"]))
            if row["chunk_id"] in seen_chunk_ids:
                # Chunk already found via body search — add title_match bonus to it.
                for i, c in enumerate(candidates):
                    if c.chunk_id == row["chunk_id"]:
                        candidates[i] = Candidate(
                            chunk_id=c.chunk_id,
                            note_id=c.note_id,
                            path=c.path,
                            text=c.text,
                            source=c.source,
                            scores={**c.scores, "title_match": title_score},
                        )
                continue
            seen_chunk_ids.add(row["chunk_id"])
            candidates.append(
                Candidate(
                    chunk_id=row["chunk_id"],
                    note_id=row["note_id"],
                    path=row["path"],
                    text=row["chunk_text"],
                    source="lexical",
                    scores={
                        "lexical_rank": float(row["rank"]),
                        "lexical_score": title_score,
                        "title_match": title_score,
                    },
                )
            )

        # title_rows are additive — don't cap at `limit` so they reach fusion.
        return candidates


def _rank_to_score(rank: float) -> float:
    # BM25 from SQLite FTS5 returns negative values: more negative = better match.
    # Map to [0, 1) where higher = better.
    abs_rank = abs(rank)
    return abs_rank / (1.0 + abs_rank)


TOKEN_RE = re.compile(r"[\w\-]+", re.UNICODE)

# Common Russian and English stop words to skip in FTS matching.
_STOP_WORDS = frozenset(
    "а б в г д е ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я "
    "на из в с по для от до как или но что это не так же при через за "
    "the a an in of to for and or but is are was were be been "
    "i me my we our you your he she they it its".split()
)


def build_match_query(query: str, *, min_len: int = 3) -> str:
    tokens = [token.lower() for token in TOKEN_RE.findall(query)]
    unique_tokens: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen or token in _STOP_WORDS or len(token) < min_len:
            continue
        seen.add(token)
        unique_tokens.append(token)
    if not unique_tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in unique_tokens)


def build_title_match_query(query: str) -> str:
    """FTS5 column-scoped query: title:(token1 OR token2 ...)"""
    inner = build_match_query(query)
    if not inner:
        return ""
    return f"title:({inner})"
