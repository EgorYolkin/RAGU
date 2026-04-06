from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class PipelineTimer:
    _spans: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _starts: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self._spans[name] = (time.perf_counter() - start) * 1000  # ms

    def record(self, name: str, value_ms: float) -> None:
        self._spans[name] = value_ms

    def get(self, name: str) -> float | None:
        return self._spans.get(name)

    def summary(self) -> str:
        if not self._spans:
            return "(no spans recorded)"

        max_name = max(len(k) for k in self._spans)
        # Child spans (prefixed with spaces) are sub-measurements of a parent span.
        # Exclude them from the TOTAL to avoid double-counting.
        top_level = {k: v for k, v in self._spans.items() if not k.startswith("  ")}
        total = sum(top_level.values())
        lines = [f"  {'stage':<{max_name}}  {'ms':>8}  {'%':>6}"]
        lines.append("  " + "-" * (max_name + 18))
        for name, ms in self._spans.items():
            is_child = name.startswith("  ")
            pct = 100 * ms / total if (total > 0 and not is_child) else 0
            pct_str = f"{pct:>5.1f}%" if not is_child else "      "
            lines.append(f"  {name:<{max_name}}  {ms:>7.1f}  {pct_str}")
        lines.append("  " + "-" * (max_name + 18))
        lines.append(f"  {'TOTAL':<{max_name}}  {total:>7.1f}")
        return "\n".join(lines)
