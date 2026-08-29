import json
import polars as pl
from cmm.refresh import (assign_new, new_items, refresh_report, any_trigger,
                         corpus_items, theme_block)

ANCHOR = pl.DataFrame({"name": ["A", "B"], "description": ["a things", "b things"]})


def _items(n, prefix="e"):
    return pl.DataFrame({
        "entry_id": [f"{prefix}{i}" for i in range(n)],
        "text": [f"text {i}" for i in range(n)],
        "source": ["changelog"] * n,
        "date": ["2026-06-01"] * n,
        "version": ["2.1.200"] * n,
    })


def test_new_items_excludes_already_coded_entries():
    items = _items(4)
    codes = pl.DataFrame({"entry_id": ["e0", "e2"], "source": ["changelog"] * 2,
                          "date": ["2026-06-01"] * 2, "themes": [["A"], ["B"]]})
    assert new_items(items, codes)["entry_id"].to_list() == ["e1", "e3"]


def test_assign_new_caches_per_entry_and_skips_on_rerun(tmp_path):
    calls = []

    def fake_batch(batch, block):
        calls.append([r["entry_id"] for r in batch])
        # deliberately omit the last entry: absent == no theme
        return [{"entry_id": r["entry_id"], "themes": ["A", "Bogus"]} for r in batch[:-1]]

    out = assign_new(_items(3), ANCHOR, cache_dir=tmp_path, assign_batch=fake_batch)
    assert out["themes"].to_list() == [["A"], ["A"], []]   # Bogus filtered, e2 -> []
    assert len(calls) == 1
    # second run: all three cached, including the [] result -> zero LLM calls
    out2 = assign_new(_items(3), ANCHOR, cache_dir=tmp_path, assign_batch=fake_batch)
    assert len(calls) == 1 and out2["themes"].to_list() == out["themes"].to_list()
    # a changed theme set invalidates the cache
    other = ANCHOR.with_columns(pl.lit("changed").alias("description"))
    assign_new(_items(3), other, cache_dir=tmp_path, assign_batch=fake_batch)
    assert len(calls) == 2
    # cache files are keyed by content, not position
    keys = [json.loads(p.read_text())["key"] for p in tmp_path.glob("*.json")]
    assert all(k.startswith("assign::") and "::e" in k for k in keys)


def test_assign_new_is_batch_order_independent(tmp_path):
    seen = []

    def fake_batch(batch, block):
        seen.append(sorted(r["entry_id"] for r in batch))
        return [{"entry_id": r["entry_id"], "themes": ["B"]} for r in batch]

    items = _items(30)
    assign_new(items.reverse(), ANCHOR, cache_dir=tmp_path, assign_batch=fake_batch)
    # misses are sorted by entry_id before batching -> deterministic batches
    assert seen[0] == sorted(items["entry_id"].to_list())[:25]


def _report(themes_per_item):
    codes = pl.DataFrame({"entry_id": [f"e{i}" for i in range(len(themes_per_item))],
                          "source": ["changelog"] * len(themes_per_item),
                          "date": ["2026-06-01"] * len(themes_per_item),
                          "themes": themes_per_item},
                         schema_overrides={"themes": pl.List(pl.Utf8)})
    cl = pl.DataFrame({"version": ["2.1.98", "2.1.150", "2.1.251"]})
    return refresh_report(codes, ANCHOR, cl, "2.1.150")


def test_refresh_report_triggers_and_numeric_version():
    r = _report([["A"], ["B"], ["A"], ["B"], []] * 4)   # residual 20%, A 40%
    assert r["new_max_version"] == "2.1.251"            # not "2.1.98"
    assert r["residual_fraction"] == 0.2
    assert r["triggers"]["residual_over_5pct"]["fired"] is True
    assert r["triggers"]["theme_over_40pct"]["fired"] is False   # 0.40 is not > 0.40
    assert any_trigger(r)
    quiet = _report([["A"], ["B"], ["A", "B"], []] * 10)   # A 50%? no: shares are of items
    # A: 20/40 = 0.5 > 0.4 fires; use a spread that stays under 40% per theme
    quiet = _report([["A"], ["B"], ["A"], ["B"], ["A", "B"]] * 4 + [[]] * 0)
    assert quiet["triggers"]["residual_over_5pct"]["fired"] is False
    assert quiet["per_theme"]["A"]["share_of_new_items"] == 0.6  # 12/20
    assert quiet["triggers"]["theme_over_40pct"]["fired"] is True
    three = pl.DataFrame({"name": ["A", "B", "C"], "description": ["a", "b", "c"]})
    codes = pl.DataFrame({"entry_id": [f"e{i}" for i in range(30)],
                          "source": ["changelog"] * 30, "date": ["2026-06-01"] * 30,
                          "themes": ([["A"], ["B"], ["C"]] * 10)},
                         schema_overrides={"themes": pl.List(pl.Utf8)})
    ok = refresh_report(codes, three, pl.DataFrame({"version": ["2.1.251"]}), "2.1.150")
    assert not any_trigger(ok) and ok["per_theme"]["C"]["count"] == 10


def test_corpus_items_matches_embed_cluster_shape():
    cl = pl.DataFrame({"id": ["x"], "text": ["t"], "date": ["2026-01-01"], "version": ["1.0.0"]})
    bl = pl.DataFrame({"url": ["u1", "u2"], "title": ["T", "U"], "body": ["b" * 900, "c"],
                       "date": ["2026-01-02", None], "cc_relevant": [True, False]})
    out = corpus_items(cl, bl)
    assert out.columns == ["entry_id", "text", "source", "date", "version"]
    assert out["entry_id"].to_list() == ["x", "u1"]     # u2 not cc_relevant
    assert len(out["text"][1]) == len("T. ") + 800
    assert "- A: a things" in theme_block(ANCHOR)
