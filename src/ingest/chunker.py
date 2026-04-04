from __future__ import annotations

from src.core.ids import stable_id
from src.domain.models import Chunk, ParsedNote


class MarkdownChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, note: ParsedNote) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_order = 0

        for section in note.sections:
            paragraphs = [
                part.strip() for part in section.text.split("\n\n") if part.strip()
            ]
            if not paragraphs:
                continue

            current = ""
            for paragraph in paragraphs:
                candidate = paragraph if not current else f"{current}\n\n{paragraph}"
                if self._token_count(candidate) <= self.chunk_size:
                    current = candidate
                    continue

                if current:
                    chunks.append(
                        self._make_chunk(
                            note=note,
                            heading_path=section.heading_path,
                            text=current,
                            chunk_order=chunk_order,
                        )
                    )
                    chunk_order += 1
                    current = self._with_overlap(current, paragraph)
                else:
                    split_paragraphs = self._split_large_paragraph(paragraph)
                    for split_text in split_paragraphs:
                        chunks.append(
                            self._make_chunk(
                                note=note,
                                heading_path=section.heading_path,
                                text=split_text,
                                chunk_order=chunk_order,
                            )
                        )
                        chunk_order += 1
                    current = ""

            if current:
                chunks.append(
                    self._make_chunk(
                        note=note,
                        heading_path=section.heading_path,
                        text=current,
                        chunk_order=chunk_order,
                    )
                )
                chunk_order += 1

        return chunks

    def _make_chunk(
        self,
        *,
        note: ParsedNote,
        heading_path: tuple[str, ...],
        text: str,
        chunk_order: int,
    ) -> Chunk:
        chunk_text = text.strip()
        return Chunk(
            chunk_id=stable_id("chunk", f"{note.note_id}:{chunk_order}:{chunk_text}"),
            note_id=note.note_id,
            path=note.path,
            heading_path=heading_path,
            text=chunk_text,
            chunk_order=chunk_order,
            token_count=self._token_count(chunk_text),
        )

    def _split_large_paragraph(self, text: str) -> list[str]:
        words = text.split()
        parts: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            parts.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return parts

    def _with_overlap(self, previous: str, next_paragraph: str) -> str:
        overlap_words = previous.split()[-self.chunk_overlap :]
        overlap_text = " ".join(overlap_words).strip()
        if not overlap_text:
            return next_paragraph
        return f"{overlap_text}\n\n{next_paragraph}"

    def _token_count(self, text: str) -> int:
        return len(text.split())
