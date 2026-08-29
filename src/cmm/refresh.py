"""Incremental corpus refresh — choice (a): extend the corpus, keep the themes.

The 13 anchor themes (B1.5, derived on the corpus through v2.1.150 /
2026-05-23) are held FIXED. New changelog entries and blog posts are:

1. embedded with the same sentence-transformer (no UMAP/HDBSCAN refit —
   `cluster_label` is set to UNCLUSTERED and `umap_x/y` left null, so
   `coherence.parquet` remains the May cluster solution and says so);
2. assigned to the fixed anchor set with a per-entry, content-keyed cache
   (`assign::<theme-set hash>::<entry_id>::<text hash>`), so batching is an
   implementation detail and a later refresh never re-bills an entry;
3. summarised in `refresh_report.json` with the two escalation triggers
   agreed on 2026-08-29: new-item residual > 5 %, or any single theme
   absorbing > 40 % of new items. If either fires, nothing is written unless
   `force=True` — re-deriving the theme model (choice (b)) is a human call.

Re-deriving themes, refitting clusters, or touching `anchor_themes.parquet`
is deliberately out of scope here.
"""
import concurrent.futures
import hashlib
import json
from datetime import date
from pathlib import Path

import polars as pl

from cmm.cache import DEFAULT_CACHE, _path
from cmm.collect_changelog import latest_version, sort_versions
from cmm.thematic_coding import BATCH_SIZE, _assign_batch
from cmm.triangulate import MAINTENANCE_LABEL, finalize_themes, label_unassigned

PROCESSED = Path("data/processed")
CLUSTER_SOLUTION_DATE = "2026-05-23"   # corpus ceiling when clusters were fit
UNCLUSTERED = -2                       # cluster_label for post-solution items
RESIDUAL_TRIGGER = 0.05
THEME_SHARE_TRIGGER = 0.40


# ---------------------------------------------------------------- corpus --

def corpus_items(changelog: pl.DataFrame, blogs: pl.DataFrame) -> pl.DataFrame:
    """All corpus items in the embeddings schema (minus vectors/clusters).

    Mirrors cmm.embed_cluster.build so refreshed rows are shaped identically.
    """
    cl = changelog.select(
        pl.col("id").alias("entry_id"), pl.col("text"),
        pl.lit("changelog").alias("source"), pl.col("date"), pl.col("version"))
    bl = (blogs.filter(pl.col("cc_relevant"))
          .select(pl.col("url").alias("entry_id"),
                  (pl.col("title") + ". " + pl.col("body").str.slice(0, 800)).alias("text"),
                  pl.lit("blog").alias("source"), pl.col("date"),
                  pl.lit(None, dtype=pl.Utf8).alias("version")))
    return pl.concat([cl, bl])


def new_items(items: pl.DataFrame, codes: pl.DataFrame) -> pl.DataFrame:
    """Items whose entry_id is not yet in codes.parquet."""
    return items.filter(~pl.col("entry_id").is_in(codes["entry_id"].implode()))


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode with the pipeline's embedding model (import deferred: heavy)."""
    from sentence_transformers import SentenceTransformer

    from cmm.embed_cluster import EMBED_MODEL
    model = SentenceTransformer(EMBED_MODEL)
    return [v.tolist() for v in model.encode(texts, show_progress_bar=False)]


# ------------------------------------------------------------ assignment --

def theme_block(anchor: pl.DataFrame) -> str:
    return "\n".join(f"- {t['name']}: {t['description']}"
                     for t in anchor.iter_rows(named=True))


def _entry_key(theme_hash: str, entry_id: str, text: str) -> str:
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
    return f"assign::{theme_hash}::{entry_id}::{text_hash}"


def assign_new(items: pl.DataFrame, anchor: pl.DataFrame,
               cache_dir: Path = DEFAULT_CACHE,
               assign_batch=None, max_workers: int = 12) -> pl.DataFrame:
    """Assign `items` to the fixed anchor set; per-entry content-keyed cache.

    Only cache misses are batched (sorted by entry_id, BATCH_SIZE each) and
    sent to the LLM; every returned assignment is stored under its own key,
    so the next refresh skips already-assigned entries regardless of how the
    batches fall. Returns entry_id, source, date, themes (unlabelled: [] for
    no theme).
    """
    if assign_batch is None:           # resolved at call time (patchable)
        assign_batch = _assign_batch
    block = theme_block(anchor)
    thash = hashlib.sha256(block.encode()).hexdigest()[:12]
    valid = set(anchor["name"].to_list())
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    assigned: dict[str, list[str]] = {}
    misses: list[dict] = []
    for r in items.iter_rows(named=True):
        p = _path(_entry_key(thash, r["entry_id"], r["text"]), cache_dir)
        if p.exists():
            assigned[r["entry_id"]] = json.loads(p.read_text())["value"]
        else:
            misses.append(r)
    misses.sort(key=lambda r: r["entry_id"])
    batches = [misses[i:i + BATCH_SIZE] for i in range(0, len(misses), BATCH_SIZE)]
    print(f"assign_new: {len(assigned)} cached, {len(misses)} to assign "
          f"in {len(batches)} batches")
    def do_batch(batch: list[dict]) -> dict[str, list[str]]:
        returned = {a["entry_id"]: [t for t in a.get("themes", []) if t in valid]
                    for a in assign_batch(batch, block)}
        out = {}
        for r in batch:
            themes = returned.get(r["entry_id"], [])   # absent == no theme
            key = _entry_key(thash, r["entry_id"], r["text"])
            _path(key, cache_dir).write_text(
                json.dumps({"key": key, "value": themes}))
            out[r["entry_id"]] = themes
        return out

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for i, fut in enumerate(
                concurrent.futures.as_completed([ex.submit(do_batch, b) for b in batches]), 1):
            assigned.update(fut.result())
            if i % 10 == 0:
                print(f"  batch {i}/{len(batches)}", flush=True)
    return items.with_columns(
        pl.col("entry_id").map_elements(lambda e: assigned.get(e, []),
                                        return_dtype=pl.List(pl.Utf8)).alias("themes")
    ).select("entry_id", "source", "date", "themes")


# ---------------------------------------------------------------- report --

def refresh_report(new_codes: pl.DataFrame, anchor: pl.DataFrame,
                   changelog: pl.DataFrame, prior_max_version: str) -> dict:
    """Residual rate, per-theme share of new items, and trigger evaluation."""
    n = new_codes.height
    residual = new_codes.filter(pl.col("themes").list.len() == 0).height
    shares = (new_codes.explode("themes").drop_nulls("themes")
              .group_by("themes").len().sort("len", descending=True))
    per_theme = {t: {"count": c, "share_of_new_items": round(c / n, 3) if n else 0.0}
                 for t, c in shares.iter_rows()}
    for t in anchor["name"].to_list():
        per_theme.setdefault(t, {"count": 0, "share_of_new_items": 0.0})
    top_theme, top_share = (shares.row(0)[0], shares.row(0)[1] / n) if n and shares.height else (None, 0.0)
    versions = sort_versions(changelog["version"])
    return {
        "refreshed_on": date.today().isoformat(),
        "cluster_solution_date": CLUSTER_SOLUTION_DATE,
        "prior_max_version": prior_max_version,
        "new_max_version": versions[-1] if versions else None,
        "new_items": n,
        "new_items_by_source": dict(new_codes.group_by("source").len().iter_rows()),
        "residual_count": residual,
        "residual_fraction": round(residual / n, 4) if n else 0.0,
        "per_theme": per_theme,
        "triggers": {
            "residual_over_5pct": {"fired": (residual / n if n else 0) > RESIDUAL_TRIGGER,
                                   "value": round(residual / n, 4) if n else 0.0},
            "theme_over_40pct": {"fired": top_share > THEME_SHARE_TRIGGER,
                                 "theme": top_theme, "value": round(top_share, 4)},
        },
    }


def any_trigger(report: dict) -> bool:
    return any(t["fired"] for t in report["triggers"].values())


# ------------------------------------------------------------------ run ---

def run(processed: Path = PROCESSED, force: bool = False,
        cache_dir: Path = DEFAULT_CACHE) -> dict:
    """Probe + (if no trigger fires, or force) write the refreshed tables.

    Assumes collect_changelog, collect_blogs and tag_and_join have run, so
    changelog.parquet / blogs.parquet / joins.parquet are already current.
    """
    processed = Path(processed)
    changelog = pl.read_parquet(processed / "changelog.parquet")
    blogs = pl.read_parquet(processed / "blogs.parquet")
    emb = pl.read_parquet(processed / "embeddings.parquet")
    codes = pl.read_parquet(processed / "codes.parquet")
    anchor = pl.read_parquet(processed / "anchor_themes.parquet")
    themes = pl.read_parquet(processed / "themes.parquet")

    prior_max = latest_version(
        emb.filter((pl.col("source") == "changelog")
                   & (pl.col("cluster_label") != UNCLUSTERED))["version"])
    items = corpus_items(changelog, blogs)
    # Entries edited/removed upstream keep their old id in codes/embeddings;
    # drop those orphans so every coded row is a live corpus item.
    live = items["entry_id"].implode()
    orphans = codes.filter(~pl.col("entry_id").is_in(live))
    if orphans.height:
        print(f"refresh: dropping {orphans.height} orphan row(s) no longer in "
              f"the corpus: {orphans['entry_id'].to_list()[:5]}")
        codes = codes.filter(pl.col("entry_id").is_in(live))
        emb = emb.filter(pl.col("entry_id").is_in(live))
    fresh = new_items(items, codes)
    print(f"refresh: corpus {items.height} items, {fresh.height} new "
          f"(prior ceiling v{prior_max}, now v{latest_version(changelog['version'])})")

    new_codes = assign_new(fresh, anchor, cache_dir=cache_dir)
    if fresh.height:
        report_subject = new_codes
    else:
        # No-op re-run: report on everything added since the cluster
        # solution, so refresh_report.json keeps describing the last delta.
        since = emb.filter(pl.col("cluster_label") == UNCLUSTERED)["entry_id"].implode()
        report_subject = codes.filter(pl.col("entry_id").is_in(since)).with_columns(
            pl.when(pl.col("themes") == [MAINTENANCE_LABEL]).then(pl.lit([], dtype=pl.List(pl.Utf8)))
            .otherwise(pl.col("themes")).alias("themes"))
    report = refresh_report(report_subject, anchor, changelog, prior_max)
    (processed / "refresh_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["triggers"], indent=2))
    if any_trigger(report) and not force:
        print("TRIGGER FIRED — nothing else written. Re-deriving the theme "
              "model is choice (b): a human decision.")
        return report

    # -- embeddings: append new rows; sync blog dates (DATE_OVERRIDES) ----
    vectors = embed_texts(fresh["text"].to_list()) if fresh.height else []
    new_emb = fresh.with_columns(
        pl.lit(UNCLUSTERED, dtype=emb["cluster_label"].dtype).alias("cluster_label"),
        pl.lit(None, dtype=emb["umap_x"].dtype).alias("umap_x"),
        pl.lit(None, dtype=emb["umap_y"].dtype).alias("umap_y"),
        pl.Series("vector", vectors, dtype=emb["vector"].dtype),
    ).select(emb.columns)
    date_by_id = dict(zip(items["entry_id"].to_list(), items["date"].to_list()))
    emb = emb.with_columns(
        pl.col("entry_id").map_elements(lambda e: date_by_id.get(e),
                                        return_dtype=pl.Utf8).fill_null(pl.col("date")).alias("date"))
    emb = pl.concat([emb, new_emb])

    # -- codes: append (Maintenance label for unassigned), themes: re-tally --
    codes = pl.concat([codes, label_unassigned(new_codes)])
    codes = codes.with_columns(
        pl.col("entry_id").map_elements(lambda e: date_by_id.get(e),
                                        return_dtype=pl.Utf8).fill_null(pl.col("date")).alias("date"))
    themes = finalize_themes(themes, codes, emb)   # descriptions/tiers fixed

    # -- residual over the full corpus (Maintenance == unassigned) ----------
    all_unassigned = codes.filter(pl.col("themes") == [MAINTENANCE_LABEL])
    text_by_id = dict(zip(emb["entry_id"].to_list(), emb["text"].to_list()))
    residual = {
        "residual_count": all_unassigned.height,
        "residual_fraction": round(all_unassigned.height / codes.height, 3),
        "by_source": dict(all_unassigned.group_by("source").len().iter_rows()),
        "examples": [text_by_id.get(e, "")[:160]
                     for e in all_unassigned["entry_id"].to_list()[:12]],
        "note": f"Corpus through v{report['new_max_version']}; themes fixed at "
                f"the {CLUSTER_SOLUTION_DATE} derivation (incremental refresh).",
    }

    emb.write_parquet(processed / "embeddings.parquet")
    codes.write_parquet(processed / "codes.parquet")
    themes.write_parquet(processed / "themes.parquet")
    (processed / "residual_analysis.json").write_text(json.dumps(residual, indent=2))
    audit = json.loads((processed / "coding_audit.json").read_text())
    audit.update({"n_entries": codes.height,
                  "residual_count": residual["residual_count"],
                  "residual_fraction": residual["residual_fraction"],
                  "refreshed_on": report["refreshed_on"],
                  "cluster_solution_date": CLUSTER_SOLUTION_DATE})
    (processed / "coding_audit.json").write_text(json.dumps(audit, indent=2))
    metrics = json.loads((processed / "run_metrics.json").read_text())
    metrics.update({"blog_total": blogs.height,
                    "blog_undated_count": blogs["date"].null_count(),
                    "changelog_entries": changelog.height,
                    "changelog_versions": changelog["version"].n_unique(),
                    "max_version": report["new_max_version"],
                    "cluster_solution_date": CLUSTER_SOLUTION_DATE})
    (processed / "run_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"refresh: wrote {codes.height} codes, {emb.height} embeddings, "
          f"{themes.height} themes; residual {residual['residual_fraction']}")
    return report


if __name__ == "__main__":
    import sys
    run(force="--force" in sys.argv)
