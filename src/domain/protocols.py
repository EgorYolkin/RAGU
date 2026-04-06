from typing import Protocol

from .models import Candidate, Chunk, ParsedNote, RawNote


class NoteSource(Protocol):
    def list_paths(self) -> list[str]: ...
    def read_note(self, path: str) -> RawNote: ...


class NoteParser(Protocol):
    def parse(self, raw_note: RawNote) -> ParsedNote: ...


class Chunker(Protocol):
    def chunk(self, note: ParsedNote) -> list[Chunk]: ...


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class DenseRetriever(Protocol):
    def retrieve(self, query: str, limit: int) -> list[Candidate]: ...


class LexicalRetriever(Protocol):
    def retrieve(self, query: str, limit: int) -> list[Candidate]: ...


class GraphRetriever(Protocol):
    def retrieve(
        self, query: str, seed_note_ids: list[str], limit: int
    ) -> list[Candidate]: ...


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[Candidate]) -> list[Candidate]: ...
