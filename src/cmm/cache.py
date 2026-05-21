# src/cmm/cache.py
"""Content-hash disk cache for expensive network/LLM calls."""
import hashlib
import json
from pathlib import Path
from typing import Callable

DEFAULT_CACHE = Path("data/cache")


def _path(key: str, cache_dir: Path) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.json"


def cached_call(key: str, fn: Callable[[], object], cache_dir: Path = DEFAULT_CACHE):
    """Return cached result for `key`, else run `fn`, cache, and return it.

    Results must be JSON-serializable.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = _path(key, cache_dir)
    if p.exists():
        return json.loads(p.read_text())["value"]
    value = fn()
    p.write_text(json.dumps({"key": key, "value": value}))
    return value
