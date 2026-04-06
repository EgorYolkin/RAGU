from __future__ import annotations

import re
from ast import literal_eval

from src.core.ids import stable_id
from src.domain.models import NoteLink, ParsedNote, ParsedSection, RawNote

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
WIKILINK_RE = re.compile(r"(!)?\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_\-/]+)")
ATTACHMENT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
    ".csv",
    ".json",
    ".excalidraw",
}


def _parse_scalar(value: str) -> object:
    stripped = value.strip()
    if stripped.lower() in {"true", "false"}:
        return stripped.lower() == "true"
    if stripped.isdigit():
        return int(stripped)
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        if "'" not in inner and '"' not in inner:
            return [item.strip() for item in inner.split(",") if item.strip()]
        try:
            parsed = literal_eval(stripped)
        except (ValueError, SyntaxError):
            return stripped
        if isinstance(parsed, list):
            return parsed
    return stripped.strip("\"'")


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    data: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_scalar(value)
    return data, text[match.end() :]


def _normalize_wikilink_target(target: str) -> str:
    normalized = target.strip()
    suffix = "".join(__import__("pathlib").Path(normalized).suffixes).lower()
    if not suffix:
        normalized = f"{normalized}.md"
    elif suffix not in {".md", *ATTACHMENT_EXTENSIONS}:
        normalized = f"{normalized}.md"
    return normalized


def _build_basename_index(all_paths: list[str]) -> dict[str, str]:
    """Map lowercase basename → first full path (for wikilink resolution)."""
    index: dict[str, str] = {}
    for path in all_paths:
        basename = path.rsplit("/", 1)[-1].lower()
        index.setdefault(basename, path)
    return index


class MarkdownNoteParser:
    def __init__(self, all_paths: list[str] | None = None) -> None:
        self._basename_index: dict[str, str] = (
            _build_basename_index(all_paths) if all_paths else {}
        )

    def set_paths(self, all_paths: list[str]) -> None:
        self._basename_index = _build_basename_index(all_paths)

    def parse(self, raw_note: RawNote) -> ParsedNote:
        if raw_note.text is None:
            raise ValueError(f"cannot parse note without text: {raw_note.path}")

        frontmatter, body = _parse_frontmatter(raw_note.text)
        title = str(
            frontmatter.get("title")
            or raw_note.path.rsplit("/", 1)[-1].removesuffix(".md")
        )
        tags = tuple(
            sorted(
                {
                    *self._frontmatter_list(frontmatter, "tags"),
                    *TAG_RE.findall(body),
                }
            )
        )
        aliases = tuple(self._frontmatter_list(frontmatter, "aliases"))
        sections = tuple(self._parse_sections(body))
        links = tuple(self._parse_links(raw_note.path, body))

        return ParsedNote(
            note_id=stable_id("note", raw_note.path),
            path=raw_note.path,
            title=title,
            frontmatter=frontmatter,
            tags=tags,
            aliases=aliases,
            sections=sections,
            links=links,
        )

    def _frontmatter_list(self, frontmatter: dict, key: str) -> list[str]:
        value = frontmatter.get(key)
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    def _parse_sections(self, body: str) -> list[ParsedSection]:
        sections: list[ParsedSection] = []
        heading_stack: list[str] = []
        current_lines: list[str] = []
        current_path: tuple[str, ...] = tuple()

        def flush() -> None:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append(ParsedSection(heading_path=current_path, text=text))

        for line in body.splitlines():
            heading_match = HEADING_RE.match(line)
            if heading_match:
                flush()
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                heading_stack[:] = heading_stack[: level - 1]
                heading_stack.append(heading_text)
                current_path = tuple(heading_stack)
                current_lines = []
                continue
            current_lines.append(line)

        flush()

        if not sections and body.strip():
            sections.append(ParsedSection(heading_path=tuple(), text=body.strip()))
        return sections

    def _resolve_target(self, raw_target: str) -> str:
        normalized = _normalize_wikilink_target(raw_target)
        if self._basename_index:
            basename = normalized.rsplit("/", 1)[-1].lower()
            resolved = self._basename_index.get(basename)
            if resolved:
                return resolved
        return normalized

    def _parse_links(self, source_path: str, body: str) -> list[NoteLink]:
        links: list[NoteLink] = []
        for embed_flag, target, heading, _alias in WIKILINK_RE.findall(body):
            edge_type = "embed" if embed_flag else "links_to"
            if heading:
                edge_type = "links_to_heading"
            links.append(
                NoteLink(
                    source_path=source_path,
                    target_path=self._resolve_target(target),
                    target_anchor=heading or None,
                    edge_type=edge_type,
                )
            )
        return links
