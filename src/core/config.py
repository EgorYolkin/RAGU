from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    vault_path: Path
    sqlite_path: Path = Path(".local/app.db")
    qdrant_path: Path = Path(".local/qdrant")
    ollama_base_url: str = "http://localhost:11434"
    generator_model: str = "qwen3:8b"
    embedding_model: str = "embeddinggemma"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    ollama_keep_alive: str = "10m"
    chunk_size: int = 800
    chunk_overlap: int = 120

    @classmethod
    def from_env(cls) -> Settings:
        vault_path = Path(os.getenv("OBSIDIAN_RAG_VAULT_PATH", "vault")).expanduser()
        sqlite_path = Path(os.getenv("OBSIDIAN_RAG_SQLITE_PATH", ".local/app.db"))
        qdrant_path = Path(os.getenv("OBSIDIAN_RAG_QDRANT_PATH", ".local/qdrant"))

        return cls(
            vault_path=vault_path,
            sqlite_path=sqlite_path,
            qdrant_path=qdrant_path,
            ollama_base_url=os.getenv(
                "OBSIDIAN_RAG_OLLAMA_BASE_URL",
                "http://localhost:11434",
            ),
            generator_model=os.getenv("OBSIDIAN_RAG_GENERATOR_MODEL", "qwen3:8b"),
            embedding_model=os.getenv(
                "OBSIDIAN_RAG_EMBEDDING_MODEL",
                "embeddinggemma",
            ),
            reranker_model=os.getenv(
                "OBSIDIAN_RAG_RERANKER_MODEL",
                "BAAI/bge-reranker-v2-m3",
            ),
            ollama_keep_alive=os.getenv(
                "OBSIDIAN_RAG_OLLAMA_KEEP_ALIVE",
                "10m",
            ),
            chunk_size=int(os.getenv("OBSIDIAN_RAG_CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("OBSIDIAN_RAG_CHUNK_OVERLAP", "120")),
        )
