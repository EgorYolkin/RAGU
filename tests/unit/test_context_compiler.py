from src.domain.models import Candidate
from src.synth.context_compiler import ContextCompiler


def test_context_compiler_groups_candidates_by_note() -> None:
    compiler = ContextCompiler(max_notes=2, max_snippets_per_note=2)
    candidates = [
        Candidate(
            chunk_id="c1",
            note_id="n1",
            path="a.md",
            text="alpha",
            source="lexical",
        ),
        Candidate(
            chunk_id="c2",
            note_id="n1",
            path="a.md",
            text="beta",
            source="graph",
        ),
        Candidate(
            chunk_id="c3",
            note_id="n2",
            path="b.md",
            text="gamma",
            source="lexical",
        ),
        Candidate(
            chunk_id="c4",
            note_id="n3",
            path="c.md",
            text="delta",
            source="graph",
        ),
    ]

    compiled = compiler.compile("test query", candidates)

    assert len(compiled.notes) == 2
    assert compiled.notes[0].path == "a.md"
    assert compiled.notes[0].snippets == ("alpha", "beta")
    assert compiled.citations == ("a.md", "b.md")
    assert compiled.related_notes == ("c.md",)
