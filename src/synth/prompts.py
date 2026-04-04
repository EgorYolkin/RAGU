from __future__ import annotations

from src.synth.context_compiler import CompiledContext

SYSTEM_PROMPT = """You answer only from the provided note context.
If the context is insufficient, say so explicitly.
Always cite the note paths you used. Отвеччай СТРОГО на русском."""


def build_user_prompt(compiled_context: CompiledContext) -> str:
    parts = [f"User query: {compiled_context.query}", "", "Context notes:"]

    for note in compiled_context.notes:
        parts.append(f"- Note: {note.path}")
        for snippet in note.snippets:
            parts.append(f"  Snippet: {snippet}")

    parts.append("")
    parts.append("Instructions:")
    parts.append("- Answer using only the context notes.")
    parts.append("- If unsure, say the notes are insufficient.")
    parts.append("- End with a short Sources line listing note paths.")

    return "\n".join(parts)
