from __future__ import annotations

from sqlite3 import Connection

from src.domain.models import NoteLink


class LinkRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def replace_for_source(self, source_path: str, links: list[NoteLink]) -> None:
        self.connection.execute(
            "DELETE FROM links WHERE source_path = ?",
            (source_path,),
        )
        self.connection.executemany(
            """
            INSERT INTO links(source_path, target_path, target_anchor, edge_type)
            VALUES(?, ?, ?, ?)
            """,
            [
                (
                    link.source_path,
                    link.target_path,
                    link.target_anchor,
                    link.edge_type,
                )
                for link in links
            ],
        )
