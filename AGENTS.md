# Repository Guidelines

## Project Structure & Module Organization

Application code lives in `src/`, split by responsibility: `domain/` holds core models and protocols, `ingest/` parses and chunks Markdown notes, `storage/` manages SQLite and Qdrant access, `retrieve/` implements planning, retrieval, fusion, and reranking, `synth/` builds prompt context and answers, `services/` orchestrates end-to-end flows, and `api/` exposes the FastAPI surface. Evaluation helpers live in `src/eval/`. Operational scripts are in `scripts/`. Tests live in `tests/`, currently starting with `tests/unit/`. Keep planning and design notes in top-level docs such as `PLAN.md`.

## Build, Test, and Development Commands

- `make sync` installs dependencies with `uv`.
- `make lock` refreshes `uv.lock`.
- `make test` runs the test suite with `pytest`.
- `make lint` runs `ruff check .`.
- `make format` applies `ruff format .`.
- `make doctor` runs repository health checks from `scripts/doctor.py`.
- `make reindex` runs the indexing entrypoint in `scripts/reindex.py`.
- `make eval` runs RAG evaluation via `scripts/eval_rag.py`.

Run commands from the repository root.

## Coding Style & Naming Conventions

Target Python is `3.12+`. Use 4-space indentation, type hints, and immutable-first domain models where practical. Follow the existing module split instead of creating large mixed-purpose files. Use `snake_case` for modules, functions, and variables, `PascalCase` for classes, and clear nouns for repository and service names such as `note_repo.py` or `query_service.py`. Formatting and import ordering are enforced with `ruff` using an 88-character line length.

## Testing Guidelines

Use `pytest` for unit and integration tests. Name files `test_*.py` and keep test paths aligned with the source layout, for example `tests/unit/test_domain_models.py`. Prefer focused unit tests for parsers, chunkers, fusion, and reranking logic before adding API-level coverage. The project target is `80%+` coverage as the system grows.

## Commit & Pull Request Guidelines

This repository has no commit history yet; use Conventional Commits from the start, for example `feat: add graph retriever` or `test: cover chunk overlap logic`. Keep pull requests narrow and include a short description, affected modules, test evidence (`make test`, `make lint`), and sample request/response output when behavior changes.

## Security & Configuration Tips

Do not commit vault contents, local indexes, or secrets. Keep machine-specific configuration in environment variables or local config files outside version control. Index artifacts should stay outside the synced Obsidian vault.
