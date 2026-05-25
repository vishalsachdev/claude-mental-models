# src/cmm/thematic_coding.py
"""Thematic coding: discover competency themes, then assign every entry.

Two-stage design (replaces per-item free-text open coding, which produced
~17k unique non-recurring codes that could not be axially aggregated):

1. discover_themes  -- one LLM call over a stratified timeline sample yields
   6-10 named competency themes (organized here under a "mental models" lens,
   which is a framing — not a measured claim about individual developers).
2. assign_themes    -- every entry is assigned to those themes in parallel
   batches, giving a direct entry->theme mapping.
"""
import concurrent.futures
import json
from pathlib import Path

import polars as pl

from cmm.llm import complete_json

DISCOVER_SYSTEM = (
    "You are a qualitative researcher studying what competencies and "
    "expectations using Claude Code (the CLI coding agent) increasingly "
    "demanded of a developer over a year of releases. From the sample of "
    "release notes and blog excerpts, identify 6-10 named themes -- competencies "
    "or expectations the tool's surface required users to develop (examples of "
    "the KIND of thing: 'context is a managed resource', 'delegation to "
    "subagents', 'the harness is configurable'). Return JSON "
    "{\"themes\": [{\"name\": ..., \"description\": ...}]}. Names are short; "
    "each description is one sentence naming the competency or expectation."
)

ASSIGN_SYSTEM = (
    "You assign Claude Code release items to competency themes. You are "
    "given the theme list and a batch of items. For each item return the "
    "theme name(s) it reflects -- usually 1, at most 2, or [] if none apply. "
    "Use theme names exactly as given. Return JSON {\"assignments\": "
    "[{\"entry_id\": ..., \"themes\": [...]}]}."
)

SAMPLE_SIZE = 150
BATCH_SIZE = 25


def discover_themes(items: pl.DataFrame) -> pl.DataFrame:
    """One LLM call over a stratified timeline sample -> named themes.

    Returns a DataFrame with columns: name, description.
    """
    dated = items.filter(pl.col("date").is_not_null()).sort("date")
    n = dated.height
    if n > SAMPLE_SIZE:
        idx = [round(i * (n - 1) / (SAMPLE_SIZE - 1)) for i in range(SAMPLE_SIZE)]
        sample = dated[idx]
    else:
        sample = dated
    listing = "\n".join(f"- ({r['source']}, {r['date']}) {r['text'][:200]}"
                        for r in sample.iter_rows(named=True))
    result = complete_json(
        f"Sample of {sample.height} Claude Code release items, oldest first:\n"
        f"{listing}",
        system=DISCOVER_SYSTEM, max_tokens=2000,
    )
    return pl.DataFrame(result["themes"])


def _assign_batch(batch: list[dict], theme_block: str) -> list[dict]:
    """Assign one batch of items to themes via a single LLM call."""
    listing = "\n".join(f"[{r['entry_id']}] ({r['source']}) {r['text'][:200]}"
                        for r in batch)
    result = complete_json(
        f"Themes:\n{theme_block}\n\nItems:\n{listing}",
        system=ASSIGN_SYSTEM, max_tokens=2000,
    )
    return result["assignments"]


def assign_themes(items: pl.DataFrame, themes_df: pl.DataFrame,
                  max_workers: int = 12) -> pl.DataFrame:
    """Assign every entry to theme(s) in parallel batches.

    Returns a DataFrame with columns: entry_id, source, date, themes.
    """
    theme_block = "\n".join(f"- {t['name']}: {t['description']}"
                            for t in themes_df.iter_rows(named=True))
    valid = set(themes_df["name"].to_list())
    rows = list(items.iter_rows(named=True))
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]

    assigned: dict[str, list[str]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_assign_batch, b, theme_block) for b in batches]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            for a in fut.result():
                assigned[a["entry_id"]] = [t for t in a.get("themes", [])
                                           if t in valid]
            if i % 20 == 0:
                print(f"  assigned batch {i}/{len(batches)}")

    return items.with_columns(
        pl.col("entry_id").map_elements(
            lambda e: assigned.get(e, []), return_dtype=pl.List(pl.Utf8)
        ).alias("themes")
    ).select("entry_id", "source", "date", "themes")


def finalize_themes(themes_df: pl.DataFrame, codes_df: pl.DataFrame,
                    items: pl.DataFrame) -> pl.DataFrame:
    """Enrich themes with first_seen_date, entry_count, blog support, examples.

    Columns out: name, description, first_seen_date, entry_count,
    supporting_blog_urls, example_entries.
    """
    text_by_id = dict(zip(items["entry_id"].to_list(), items["text"].to_list()))
    exploded = codes_df.explode("themes").drop_nulls("themes")
    rows = []
    for t in themes_df.iter_rows(named=True):
        mem = exploded.filter(pl.col("themes") == t["name"])
        dates = [d for d in mem["date"].to_list() if d]
        blog_urls = sorted(mem.filter(pl.col("source") == "blog")
                           ["entry_id"].to_list())
        examples = [text_by_id.get(e, "")[:160]
                    for e in mem["entry_id"].to_list()[:3]]
        rows.append({
            "name": t["name"],
            "description": t["description"],
            "first_seen_date": min(dates) if dates else None,
            "entry_count": mem.height,
            "supporting_blog_urls": blog_urls,
            "example_entries": examples,
        })
    return pl.DataFrame(rows, schema_overrides={"supporting_blog_urls": pl.List(pl.Utf8)})


def run(embeddings: Path = Path("data/processed/embeddings.parquet")) -> None:
    items = pl.read_parquet(embeddings).select("entry_id", "text", "source", "date")

    themes_df = discover_themes(items)
    print(f"Discovered {themes_df.height} mental-model themes")

    codes_df = assign_themes(items, themes_df)
    themes_df = finalize_themes(themes_df, codes_df, items)
    codes_df.write_parquet("data/processed/codes.parquet")
    themes_df.write_parquet("data/processed/themes.parquet")

    # Audit: how cleanly the corpus partitioned into themes.
    unassigned = codes_df.filter(pl.col("themes").list.len() == 0).height
    audit = {
        "n_themes": themes_df.height,
        "n_entries": codes_df.height,
        "n_unassigned": unassigned,
        "unassigned_fraction": round(unassigned / codes_df.height, 3),
        "theme_entry_counts": dict(zip(themes_df["name"].to_list(),
                                       themes_df["entry_count"].to_list())),
    }
    Path("data/processed/coding_audit.json").write_text(json.dumps(audit, indent=2))

    print(f"Assigned {codes_df.height} entries ({unassigned} unassigned):")
    for t in themes_df.iter_rows(named=True):
        print(f"  - {t['name']} ({t['entry_count']}, first {t['first_seen_date']})")


if __name__ == "__main__":
    run()
