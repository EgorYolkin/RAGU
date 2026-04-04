from src.domain.models import RawNote
from src.ingest.parser import MarkdownNoteParser


def test_markdown_note_parser_extracts_structure() -> None:
    parser = MarkdownNoteParser()
    raw_note = RawNote(
        path="notes/example.md",
        text=(
            "---\n"
            "title: Example Note\n"
            "tags: [rag, notes]\n"
            "aliases: [Example]\n"
            "---\n"
            "# Intro\n"
            "Hello #local-first.\n\n"
            "## Links\n"
            "See [[Target Note]] and [[Other Note#Section]].\n"
        ),
        mtime=1.0,
        exists=True,
        read_status="ok",
    )

    parsed = parser.parse(raw_note)

    assert parsed.title == "Example Note"
    assert parsed.tags == ("local-first", "notes", "rag")
    assert parsed.aliases == ("Example",)
    assert parsed.sections[0].heading_path == ("Intro",)
    assert parsed.sections[1].heading_path == ("Intro", "Links")
    assert parsed.links[0].target_path == "Target Note.md"
    assert parsed.links[1].edge_type == "links_to_heading"
    assert parsed.links[1].target_anchor == "Section"


def test_markdown_note_parser_preserves_attachment_targets() -> None:
    parser = MarkdownNoteParser()
    raw_note = RawNote(
        path="notes/example.md",
        text="![[diagram.excalidraw]] and ![[image.png]]",
        mtime=1.0,
        exists=True,
        read_status="ok",
    )

    parsed = parser.parse(raw_note)

    assert parsed.links[0].target_path == "diagram.excalidraw"
    assert parsed.links[0].edge_type == "embed"
    assert parsed.links[1].target_path == "image.png"
