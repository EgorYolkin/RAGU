PYTHON := .venv/bin/python
UV := uv

.PHONY: sync lock test lint format doctor reindex eval

sync:
	$(UV) sync

lock:
	$(UV) lock

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

doctor:
	$(UV) run python scripts/doctor.py

reindex:
	$(UV) run python scripts/reindex.py

eval:
	$(UV) run python scripts/eval_rag.py
