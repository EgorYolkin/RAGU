from __future__ import annotations

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS notes (
        note_id TEXT PRIMARY KEY,
        path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        mtime REAL NOT NULL,
        frontmatter_json TEXT NOT NULL,
        summary TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        note_id TEXT NOT NULL,
        path TEXT NOT NULL,
        heading_path TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_order INTEGER NOT NULL,
        token_count INTEGER NOT NULL,
        FOREIGN KEY(note_id) REFERENCES notes(note_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS links (
        source_path TEXT NOT NULL,
        target_path TEXT NOT NULL,
        target_anchor TEXT,
        edge_type TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tags (
        note_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        FOREIGN KEY(note_id) REFERENCES notes(note_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ingestion_state (
        path TEXT PRIMARY KEY,
        mtime REAL NOT NULL,
        indexed_at REAL NOT NULL
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
        path UNINDEXED,
        title,
        body
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        chunk_id UNINDEXED,
        note_id UNINDEXED,
        path UNINDEXED,
        heading_path UNINDEXED,
        chunk_text
    )
    """,
)
