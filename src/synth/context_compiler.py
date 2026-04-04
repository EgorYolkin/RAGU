from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import Candidate


@dataclass(frozen=True)
class CompiledNote:
    path: str
    snippets: tuple[str, ...]


@dataclass(frozen=True)
class CompiledContext:
    query: str
    notes: tuple[CompiledNote, ...]
    citations: tuple[str, ...]
    related_notes: tuple[str, ...]


class ContextCompiler:
    def __init__(self, max_notes: int = 4, max_snippets_per_note: int = 2) -> None:
        self.max_notes = max_notes
        self.max_snippets_per_note = max_snippets_per_note

    def compile(self, query: str, candidates: list[Candidate]) -> CompiledContext:
        note_to_snippets: dict[str, list[str]] = {}
        ordered_paths: list[str] = []

        for candidate in candidates:
            snippets = note_to_snippets.setdefault(candidate.path, [])
            if candidate.path not in ordered_paths:
                ordered_paths.append(candidate.path)
            if (
                len(snippets) < self.max_snippets_per_note
                and candidate.text not in snippets
            ):
                snippets.append(candidate.text)

        selected_paths = ordered_paths[: self.max_notes]
        notes = tuple(
            CompiledNote(path=path, snippets=tuple(note_to_snippets[path]))
            for path in selected_paths
        )
        citations = tuple(selected_paths)
        related_notes = tuple(
            path for path in ordered_paths if path not in selected_paths
        )

        return CompiledContext(
            query=query,
            notes=notes,
            citations=citations,
            related_notes=related_notes,
        )
