from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from urllib import request

from src.synth.context_compiler import CompiledContext
from src.synth.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageMetrics:
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None

    @property
    def ttft_ms(self) -> float | None:
        """Time-to-first-token: load + prompt eval, in ms."""
        if self.load_duration is None or self.prompt_eval_duration is None:
            return None
        return (self.load_duration + self.prompt_eval_duration) / 1_000_000

    @property
    def tokens_per_second(self) -> float | None:
        if self.eval_count and self.eval_duration and self.eval_duration > 0:
            return self.eval_count / (self.eval_duration / 1_000_000_000)
        return None

    @property
    def total_ms(self) -> float | None:
        if self.total_duration is None:
            return None
        return self.total_duration / 1_000_000


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: tuple[str, ...]
    related_notes: tuple[str, ...]
    usage: UsageMetrics


class OllamaAnswerer:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        keep_alive: str = "-1",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive

    def answer(self, compiled_context: CompiledContext) -> AnswerResult:
        """Return full answer (non-streaming). Use stream_answer() for interactive use."""
        tokens = list(self.stream_answer(compiled_context))
        content = "".join(t for t in tokens if isinstance(t, str))
        usage = next((t for t in tokens if isinstance(t, UsageMetrics)), UsageMetrics())
        return AnswerResult(
            answer=content,
            citations=compiled_context.citations,
            related_notes=compiled_context.related_notes,
            usage=usage,
        )

    def stream_answer(
        self, compiled_context: CompiledContext
    ) -> Iterator[str | UsageMetrics]:
        """Yield text tokens as they arrive, then a final UsageMetrics object."""
        user_prompt = build_user_prompt(compiled_context)
        keep_alive: int | str
        try:
            keep_alive = int(self.keep_alive)
        except ValueError:
            keep_alive = self.keep_alive
        payload = {
            "model": self.model,
            "stream": True,
            "keep_alive": keep_alive,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        encoded = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        request_start = time.perf_counter()
        first_token = True
        with request.urlopen(req) as response:
            for raw_line in response:
                line = raw_line.strip()
                if not line:
                    continue
                parsed = json.loads(line)
                if parsed.get("done"):
                    usage = _parse_usage_metrics(parsed)
                    logger.debug(
                        "llm: ttft=%.0fms gen=%.0fms tokens=%s tps=%.1f load=%.0fms",
                        usage.ttft_ms or 0,
                        (usage.eval_duration or 0) / 1_000_000,
                        usage.eval_count,
                        usage.tokens_per_second or 0,
                        (usage.load_duration or 0) / 1_000_000,
                    )
                    yield usage
                    return
                token = parsed.get("message", {}).get("content", "")
                if token:
                    if first_token:
                        ttft = (time.perf_counter() - request_start) * 1000
                        logger.debug("llm: first token in %.0fms", ttft)
                        first_token = False
                    yield token


def _parse_usage_metrics(payload: dict) -> UsageMetrics:
    return UsageMetrics(
        total_duration=payload.get("total_duration"),
        load_duration=payload.get("load_duration"),
        prompt_eval_count=payload.get("prompt_eval_count"),
        prompt_eval_duration=payload.get("prompt_eval_duration"),
        eval_count=payload.get("eval_count"),
        eval_duration=payload.get("eval_duration"),
    )
