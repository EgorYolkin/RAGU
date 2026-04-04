from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from src.synth.context_compiler import CompiledContext
from src.synth.prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: tuple[str, ...]
    related_notes: tuple[str, ...]


class OllamaAnswerer:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        keep_alive: str = "10m",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive

    def answer(self, compiled_context: CompiledContext) -> AnswerResult:
        user_prompt = build_user_prompt(compiled_context)
        content = self._chat(user_prompt)

        return AnswerResult(
            answer=content,
            citations=compiled_context.citations,
            related_notes=compiled_context.related_notes,
        )

    def _chat(self, user_prompt: str) -> str:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": self.keep_alive,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response_text = self._post_json("/api/chat", payload)
            parsed = json.loads(response_text)
            message = parsed.get("message", {})
            return message.get("content", "").strip()
        except error.HTTPError as exc:
            if exc.code != 404:
                raise

        try:
            response_text = self._post_json(
                "/v1/chat/completions",
                payload,
                extra_headers={
                    "Authorization": "Bearer ollama",
                },
            )
            parsed = json.loads(response_text)
            choices = parsed.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "").strip()
        except error.HTTPError as exc:
            if exc.code != 404:
                raise

        response_text = self._post_json(
            "/api/generate",
            {
                "model": self.model,
                "stream": False,
                "keep_alive": self.keep_alive,
                "prompt": full_prompt,
            },
        )
        parsed = json.loads(response_text)
        return parsed.get("response", "").strip()

    def _post_json(
        self,
        path: str,
        payload: dict,
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        encoded = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        req = request.Request(
            f"{self.base_url}{path}",
            data=encoded,
            headers=headers,
            method="POST",
        )
        with request.urlopen(req) as response:
            return response.read().decode("utf-8")
