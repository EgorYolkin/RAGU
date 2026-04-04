from dataclasses import dataclass, field

from typing_extensions import Literal


@dataclass(frozen=True)
class RawNote:
    path: str
    text: str | None
    mtime: float
    exists: bool
    read_status: Literal["ok", "missing", "icloud_deferred", "error"]


@dataclass(frozen=True)
class ParsedSection:
    heading_path: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class NoteLink:
    source_path: str
    target_path: str
    edge_type: Literal["links_to", "links_to_heading", "links_to_block", "embed"]


@dataclass(frozen=True)
class ParsedNote:
    note_id: str
    path: str
    title: str
    frontmatter: dict
    tags: tuple[str, ...]
    aliases: tuple[str, ...]
    sections: tuple[ParsedSection, ...]
    links: tuple[NoteLink, ...]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    note_id: str
    path: str
    heading_path: tuple[str, ...]
    text: str
    chunk_order: int
    token_count: int


@dataclass(frozen=True)
class Candidate:
    chunk_id: str
    note_id: str
    path: str
    text: str
    source: Literal["dense", "lexical", "graph", "hybrid"]
    scores: dict[str, float] = field(default_factory=dict)
