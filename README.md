# Obsidian RAG

Локальный RAG-проект для поиска и ответа по заметкам в стиле Obsidian.

Цель проекта: построить local-first систему, которая работает напрямую с Markdown-заметками, учитывает явный граф ссылок Obsidian и комбинирует несколько видов retrieval вместо наивного "только vector search".

Текущий статус: ранний каркас проекта. Структура модулей, доменные модели, `uv`-окружение, lockfile, базовые команды и smoke-test уже подготовлены. Большая часть прикладной логики пока не реализована.

## Что планируется

- чтение заметок напрямую из vault, в том числе из iCloud Drive
- парсинг Markdown, frontmatter, тегов, заголовков и `[[wikilinks]]`
- построение собственного графа заметок
- гибридный retrieval:
  - dense retrieval
  - lexical retrieval через SQLite FTS5 / BM25
  - graph expansion по ссылкам, тегам и соседям
- reranking кандидатов перед генерацией ответа
- сборка контекста с provenance и ссылками на источники
- локальная генерация ответа через небольшую модель

## Почему не только vector search

В личной базе знаний релевантность часто определяется не только семантической близостью. Важны также:

- прямые ссылки между заметками
- общие теги и frontmatter
- соседство по папкам
- временная близость изменений
- точные совпадения терминов и названий

Поэтому целевая архитектура проекта: graph-assisted local RAG, а не pure vector search.

## Архитектура

Целевой pipeline:

```text
запрос
-> planner
-> parallel retrieval
   -> dense retrieval
   -> lexical retrieval
   -> graph retrieval
-> fusion
-> rerank
-> context compiler
-> local LLM
-> ответ с цитатами
```

Планируемый стек:

- Python 3.12+
- `uv` для управления окружением и зависимостями
- FastAPI для локального API
- SQLite как каноническое хранилище метаданных, графа и FTS5 индекса
- Qdrant local mode для dense retrieval
- Ollama для локальных моделей

## Структура репозитория

```text
config/     конфигурация проекта
scripts/    служебные скрипты
src/        исходный код
tests/      unit/integration/e2e тесты
PLAN.md     архитектурный и продуктовый план
```

Основные каталоги внутри `src/`:

- `src/domain/` — доменные модели и protocol-контракты
- `src/ingest/` — ingestion pipeline
- `src/storage/` — SQLite/Qdrant адаптеры
- `src/retrieve/` — retrieval, fusion и rerank
- `src/synth/` — сборка контекста и генерация ответа
- `src/api/` — API слой
- `src/services/` — orchestration/use-case слой
- `src/eval/` — оценка качества RAG

## Быстрый старт

Требования:

- Python 3.12+
- установленный `uv`

Установка зависимостей:

```bash
uv sync
```

Основные команды:

```bash
make sync
make lock
make test
make lint
make format
make doctor
make reindex
make eval
```

Эквиваленты через `uv`:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Текущее состояние кода

Сейчас в репозитории уже есть:

- `pyproject.toml` с `uv`-конфигурацией
- `uv.lock`
- `.venv`-совместимый workflow через `uv run`
- `.gitignore`
- package layout и `__init__.py`
- базовые dataclass-модели в `src/domain/models.py`
- protocol-интерфейсы в `src/domain/protocols.py`
- минимальный smoke-test

Сейчас в репозитории ещё нет:

- рабочей реализации ingestion pipeline
- схемы SQLite и миграций
- реального индекса FTS5
- интеграции с Qdrant
- интеграции с Ollama
- готового FastAPI приложения

То есть это подготовленная основа под реализацию, а не завершённый продукт.

## Тесты и качество

Запуск тестов:

```bash
make test
```

Проверка линтером:

```bash
make lint
```

Форматирование:

```bash
make format
```

## Документация по архитектуре

Подробный план, мотивация выбора стека и целевая data model описаны в [`PLAN.md`](./PLAN.md).

Если нужен следующий шаг, логично продолжать в таком порядке:

1. заполнить `config/settings.toml` и `src/core/config.py`
2. реализовать чтение vault и Markdown parser
3. собрать SQLite schema + FTS5 индекс
4. реализовать dense/lexical/graph retrieval
5. добавить локальный API и end-to-end сценарий запроса
