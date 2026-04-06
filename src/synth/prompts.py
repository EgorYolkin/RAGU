from __future__ import annotations

from src.synth.context_compiler import CompiledContext

SYSTEM_PROMPT = """Ты персональный AI-ассистент. Отвечай СТРОГО на русском языке.

Тебе предоставлены заметки пользователя как контекст.
Используй их как основу: стиль, предпочтения, уже известные факты.
Если заметок достаточно — опирайся на них.
Если заметок недостаточно — используй свои знания, но сообщи об этом.
Всегда указывай, какие заметки использовал."""


def build_user_prompt(compiled_context: CompiledContext) -> str:
    parts = [f"Запрос: {compiled_context.query}", "", "Заметки пользователя:"]

    for note in compiled_context.notes:
        parts.append(f"\n[{note.path}]")
        for snippet in note.snippets:
            parts.append(snippet)

    parts.append("")
    parts.append("Ответь на запрос, опираясь на заметки. "
                 "В конце укажи использованные заметки в строке «Источники:».")

    return "\n".join(parts)
