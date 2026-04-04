from __future__ import annotations

import hashlib


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:16]}"
