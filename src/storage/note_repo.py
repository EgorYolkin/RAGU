from __future__ import annotations

import json
import time
from sqlite3 import Connection

from src.domain.models import ParsedNote


class NoteRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def upsert(self, note: ParsedNote, mtime: float) -> None:
        self.connection.execute(
            """
            INSERT INTO notes(note_id, path, title, mtime, frontmatter_json, summary)
            VALUES(?, ?, ?, ?, ?, NULL)
            ON CONFLICT(note_id) DO UPDATE SET
                path = excluded.path,
                title = excluded.title,
                mtime = excluded.mtime,
                frontmatter_json = excluded.frontmatter_json
            """,
            (
                note.note_id,
                note.path,
                note.title,
                mtime,
                json.dumps(note.frontmatter, sort_keys=True),
            ),
        )
        self.connection.execute(
            "DELETE FROM tags WHERE note_id = ?",
            (note.note_id,),
        )
        self.connection.executemany(
            "INSERT INTO tags(note_id, tag) VALUES(?, ?)",
            [(note.note_id, tag) for tag in note.tags],
        )
        body = "\n\n".join(section.text for section in note.sections)
        self.connection.execute(
            "DELETE FROM notes_fts WHERE path = ?",
            (note.path,),
        )
        self.connection.execute(
            "INSERT INTO notes_fts(path, title, body) VALUES(?, ?, ?)",
            (note.path, note.title, body),
        )
        self.connection.execute(
            """
            INSERT INTO ingestion_state(path, mtime, indexed_at)
            VALUES(?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                mtime = excluded.mtime,
                indexed_at = excluded.indexed_at
            """,
            (note.path, mtime, time.time()),
        )
