# Obsidian RAG

Локальный RAG-ассистент по заметкам Obsidian. Работает полностью офлайн — все модели запускаются локально через Ollama.

## Установка (Mac)

```bash
git clone <repo>
cd obsidian_rag
./install.sh
```

Скрипт автоматически:
1. Устанавливает Homebrew, uv, Ollama (если не установлены)
2. Скачивает модели `nomic-embed-text` и `gemma3:4b`
3. Создаёт `.env` из `.env.example`
4. Индексирует vault (если путь уже указан в `.env`)

После установки отредактируй `.env` и укажи путь к vault:

```
OBSIDIAN_RAG_VAULT_PATH="/Users/you/Documents/notes"
```

Затем:

```bash
make reindex
```

## Использование

```bash
# Задать вопрос
make query QUERY="с какими людьми я знаком?"

# С подробным выводом timing и метрик LLM
make query QUERY="напиши алгоритм фибоначчи на golang" ARGS="--debug"

# Переиндексировать vault после изменений
make reindex
```

Или напрямую:

```bash
uv run python scripts/query_ollama.py "твой вопрос"
uv run python scripts/query_ollama.py "твой вопрос" --debug
```

## Конфигурация (.env)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `OBSIDIAN_RAG_VAULT_PATH` | — | Путь к Obsidian vault |
| `OBSIDIAN_RAG_GENERATOR_MODEL` | `gemma3:4b` | Модель генерации |
| `OBSIDIAN_RAG_EMBEDDING_MODEL` | `nomic-embed-text` | Модель эмбеддингов |
| `OBSIDIAN_RAG_CONTEXT_TOKEN_BUDGET` | `400` | Макс. токенов контекста |
| `OBSIDIAN_RAG_OLLAMA_KEEP_ALIVE` | `-1` | Время жизни модели в памяти (`-1` = бесконечно) |

Рекомендуемые модели генерации по скорости/качеству:

| Модель | Скорость (M3 Pro) | Качество |
|---|---|---|
| `gemma3:4b` | ~40 tok/s | базовое |
| `gemma3:12b` | ~15 tok/s | хорошее |
| `qwen3:8b` | ~20 tok/s | хорошее |

## Архитектура

```
запрос
→ dense retrieval (nomic-embed-text + numpy cosine)  ┐ параллельно
→ lexical retrieval (SQLite FTS5 + title search)     ┘
→ graph retrieval (wikilinks + backlinks)
→ fusion (dense 0.45 + lexical 0.25 + title 0.20 + graph 0.10)
→ rerank (FlagEmbedding если установлен, иначе fusion score)
→ context compiler (token budget)
→ Ollama streaming
→ ответ с источниками
```

- **Хранилище**: SQLite (метаданные, FTS5, граф ссылок, эмбеддинги как BLOB)
- **Граф**: wikilinks `[[Note]]` резолвятся в реальные пути vault
- **Эмбеддинги**: title-prepended (`"NoteTitle\nchunk text"`) для лучшего recall

## Разработка

```bash
make test      # pytest
make lint      # ruff check
make format    # ruff format
```
