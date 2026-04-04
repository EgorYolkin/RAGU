from src.domain.models import ParsedNote, ParsedSection
from src.ingest.chunker import MarkdownChunker


def test_chunker_preserves_heading_path_and_splits_large_sections() -> None:
    chunker = MarkdownChunker(chunk_size=6, chunk_overlap=2)
    note = ParsedNote(
        note_id="note-1",
        path="notes/example.md",
        title="Example",
        frontmatter={},
        tags=(),
        aliases=(),
        sections=(
            ParsedSection(
                heading_path=("Intro",),
                text="one two three four\n\nfive six seven eight nine",
            ),
        ),
        links=(),
    )

    chunks = chunker.chunk(note)

    assert len(chunks) >= 2
    assert all(chunk.heading_path == ("Intro",) for chunk in chunks)
    assert chunks[0].token_count <= 6
