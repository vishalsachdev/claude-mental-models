# tests/test_cache.py
from cmm.cache import cached_call


def test_cached_call_runs_once(tmp_path):
    calls = []

    def expensive(x):
        calls.append(x)
        return x * 2

    key = "double-21"
    first = cached_call(key, lambda: expensive(21), cache_dir=tmp_path)
    second = cached_call(key, lambda: expensive(21), cache_dir=tmp_path)

    assert first == 42
    assert second == 42
    assert calls == [21]  # underlying function ran only once
