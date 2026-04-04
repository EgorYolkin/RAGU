from __future__ import annotations

import sqlite3
from pathlib import Path

from src.core.paths import ensure_parent_dir
from src.storage.sqlite_schema import SCHEMA_STATEMENTS


class SQLiteDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        ensure_parent_dir(self.path)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)
