from __future__ import annotations

import json
from urllib import error, request


def _parse_keep_alive(value: str) -> int | str:
    """Return int for numeric values so Ollama accepts them (-1 = indefinite)."""
    try:
        return int(value)
    except ValueError:
        return value


class OllamaEmbedder:
    # Conservative char limit per text: 512 tokens × 4 chars/token.
    # Prevents context-length errors regardless of Ollama's num_ctx setting.
    _MAX_CHARS = 2048

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        keep_alive: str = "-1",
        batch_size: int = 8,
        num_ctx: int = 8192,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.batch_size = batch_size
        self.num_ctx = num_ctx

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        truncated = [t[: self._MAX_CHARS] for t in texts]
        results: list[list[float]] = []
        for i in range(0, len(truncated), self.batch_size):
            batch = truncated[i : i + self.batch_size]
            results.extend(self._embed_batch(batch))
        return results

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts,
            "keep_alive": _parse_keep_alive(self.keep_alive),
            "options": {"num_ctx": self.num_ctx},
        }
        encoded = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/embed",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req) as response:
                parsed = json.loads(response.read().decode("utf-8"))
            return parsed.get("embeddings", [])
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama /api/embed returned {exc.code}: {body}\n"
                f"model={self.model!r} batch_size={len(texts)}"
            ) from exc
