from src.domain.models import (
    Candidate,
    Chunk,
    NoteLink,
    ParsedNote,
    ParsedSection,
    RawNote,
)


def test_domain_dataclasses_capture_expected_values() -> None:
    raw_note = RawNote(
        path="notes/example.md",
        text="hello",
        mtime=1.0,
        exists=True,
        read_status="ok",
    )
    section = ParsedSection(heading_path=("Root", "Child"), text="section body")
    link = NoteLink(
        source_path="notes/example.md",
        target_path="notes/target.md",
        target_anchor=None,
        edge_type="links_to",
    )
    note = ParsedNote(
        note_id="note-1",
        path=raw_note.path,
        title="Example",
        frontmatter={"type": "note"},
        tags=("tag-a", "tag-b"),
        aliases=("Alias",),
        sections=(section,),
        links=(link,),
    )
    chunk = Chunk(
        chunk_id="chunk-1",
        note_id=note.note_id,
        path=note.path,
        heading_path=section.heading_path,
        text=section.text,
        chunk_order=0,
        token_count=2,
    )
    candidate = Candidate(
        chunk_id=chunk.chunk_id,
        note_id=note.note_id,
        path=note.path,
        text=chunk.text,
        source="hybrid",
        scores={"bm25": 0.2},
    )

    assert raw_note.read_status == "ok"
    assert note.sections[0].heading_path == ("Root", "Child")
    assert candidate.scores == {"bm25": 0.2}
