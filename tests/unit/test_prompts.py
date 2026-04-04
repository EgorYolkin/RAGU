from src.synth.context_compiler import CompiledContext, CompiledNote
from src.synth.prompts import build_user_prompt


def test_build_user_prompt_contains_query_notes_and_instructions() -> None:
    context = CompiledContext(
        query="what is rag",
        notes=(
            CompiledNote(path="rag.md", snippets=("RAG uses retrieval.",)),
        ),
        citations=("rag.md",),
        related_notes=(),
    )

    prompt = build_user_prompt(context)

    assert "User query: what is rag" in prompt
    assert "- Note: rag.md" in prompt
    assert "Snippet: RAG uses retrieval." in prompt
    assert "Answer using only the context notes." in prompt
