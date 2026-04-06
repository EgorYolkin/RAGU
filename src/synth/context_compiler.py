from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import Candidate

# Rough chars-per-token ratio for mixed Russian/English/code text.
_CHARS_PER_TOKEN = 4
# Approximate token overhead: system prompt + instructions + query + note paths.
_PROMPT_OVERHEAD_TOKENS = 200


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
    def __init__(
        self,
        max_notes: int = 3,
        max_snippets_per_note: int = 1,
        token_budget: int = 400,
    ) -> None:
        self.max_notes = max_notes
        self.max_snippets_per_note = max_snippets_per_note
        self.token_budget = token_budget
        # Subtract fixed prompt overhead so total prompt tokens ≈ token_budget.
        snippet_tokens = max(token_budget - _PROMPT_OVERHEAD_TOKENS, 100)
        self._char_budget = snippet_tokens * _CHARS_PER_TOKEN

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
        notes_list: list[CompiledNote] = []
        chars_used = 0

        for path in selected_paths:
            trimmed: list[str] = []
            for snippet in note_to_snippets[path]:
                remaining = self._char_budget - chars_used
                if remaining <= 0:
                    break
                text = snippet[:remaining]
                trimmed.append(text)
                chars_used += len(text)
            if trimmed:
                notes_list.append(CompiledNote(path=path, snippets=tuple(trimmed)))

        citations = tuple(n.path for n in notes_list)
        related_notes = tuple(
            path for path in ordered_paths if path not in citations
        )

        return CompiledContext(
            query=query,
            notes=tuple(notes_list),
            citations=citations,
            related_notes=related_notes,
        )
