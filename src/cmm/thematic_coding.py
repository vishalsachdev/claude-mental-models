# src/cmm/thematic_coding.py
"""LLM thematic coding: two-pass open coding -> axial mental-model themes."""
import concurrent.futures
import json
from pathlib import Path

import polars as pl

from cmm.llm import complete_json

OPEN_SYSTEM = (
    "You are doing qualitative open coding of Claude Code release notes and "
    "blog posts. For the given item, return JSON {\"codes\": [..]} with 1-3 "
    "short conceptual codes describing what the user must understand or how "
    "they must think differently. Codes are reusable phrases, not summaries."
)

# Pass 2 deliberately differs in framing so its cache key differs and the two
# passes are genuinely independent — their agreement is the consistency audit.
OPEN_SYSTEM_REVIEW = (
    "You are independently re-coding a Claude Code release item for a "
    "qualitative study. Ignore any prior coding. Return JSON {\"codes\": [..]} "
    "with 1-3 short, reusable conceptual codes naming the shift in how a user "
    "must think to use this feature well."
)

AXIAL_SYSTEM = (
    "You are doing axial coding. Given a list of open codes from Claude Code's "
    "release history, group them into 6-10 named 'mental models' a user had to "
    "develop. Return JSON {\"themes\": [{\"name\":..., \"description\":..., "
    "\"member_codes\":[...]}]}. Every input code must belong to exactly one theme."
)


def _codes_for(text: str, source: str, system: str) -> list[str]:
    prompt = f"Source: {source}\nItem: {text[:1200]}"
    return complete_json(prompt, system=system, max_tokens=300)["codes"]


def _code_one(row: dict) -> dict:
    """Run both open-coding passes for a single item and score stability."""
    a = _codes_for(row["text"], row["source"], OPEN_SYSTEM)
    b = _codes_for(row["text"], row["source"], OPEN_SYSTEM_REVIEW)
    sa, sb = set(a), set(b)
    jaccard = len(sa & sb) / len(sa | sb) if (sa | sb) else 1.0
    return {
        "entry_id": row["entry_id"], "source": row["source"],
        "date": row["date"],
        "codes": sorted(sa | sb), "codes_a": a, "codes_b": b,
        "stability": jaccard,
    }


def open_code(items: pl.DataFrame, max_workers: int = 8) -> pl.DataFrame:
    """Two independent open-coding passes per item, plus a stability score.

    Each item makes two `claude` CLI calls; calls are I/O-bound subprocesses,
    so a thread pool parallelizes them. `ex.map` preserves input order and
    re-raises any worker exception.

    Columns: entry_id, source, date, codes (union of both passes), codes_a,
    codes_b, stability (Jaccard overlap of the two passes — the audit signal).
    """
    work = list(items.iter_rows(named=True))
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for i, result in enumerate(ex.map(_code_one, work), 1):
            rows.append(result)
            if i % 100 == 0:
                print(f"  open-coded {i}/{len(work)}")
    return pl.DataFrame(rows)


def axial_code(codes_df: pl.DataFrame) -> pl.DataFrame:
    """Group all open codes into named mental-model themes."""
    all_codes = sorted({c for codes in codes_df["codes"].to_list() for c in codes})
    result = complete_json(
        "Open codes:\n" + "\n".join(f"- {c}" for c in all_codes),
        system=AXIAL_SYSTEM, max_tokens=4000,
    )
    # earliest date any member code appears => theme first_seen_date
    code_dates: dict[str, str] = {}
    for row in codes_df.iter_rows(named=True):
        for c in row["codes"]:
            if row["date"] and (c not in code_dates or row["date"] < code_dates[c]):
                code_dates[c] = row["date"]
    themes = []
    for t in result["themes"]:
        member_dates = [code_dates[c] for c in t["member_codes"] if c in code_dates]
        themes.append({
            "name": t["name"],
            "description": t["description"],
            "member_codes": t["member_codes"],
            "first_seen_date": min(member_dates) if member_dates else None,
        })
    return pl.DataFrame(themes)


def assign_themes(codes_df: pl.DataFrame, themes_df: pl.DataFrame) -> pl.DataFrame:
    """Add a `themes` column: theme name(s) each entry belongs to.

    An entry belongs to a theme if any of its codes is one of the theme's
    member_codes. This is the entry<->theme mapping the notebook needs to
    color clusters and chart theme weight over time.
    """
    code_to_theme = {c: t["name"]
                     for t in themes_df.iter_rows(named=True)
                     for c in t["member_codes"]}
    return codes_df.with_columns(
        pl.col("codes").map_elements(
            lambda cs: sorted({code_to_theme[c] for c in cs if c in code_to_theme}),
            return_dtype=pl.List(pl.Utf8),
        ).alias("themes")
    )


def add_supporting_blogs(themes_df: pl.DataFrame,
                         codes_df: pl.DataFrame) -> pl.DataFrame:
    """Attach `supporting_blog_urls[]` to each theme.

    A blog supports a theme if the blog entry was assigned to that theme. Blog
    entries store their URL in `entry_id`, so the URLs are read directly.
    """
    per_theme: dict[str, set] = {}
    for row in codes_df.iter_rows(named=True):
        if row["source"] != "blog":
            continue
        for theme in row["themes"]:
            per_theme.setdefault(theme, set()).add(row["entry_id"])
    return themes_df.with_columns(
        pl.col("name").map_elements(
            lambda n: sorted(per_theme.get(n, set())),
            return_dtype=pl.List(pl.Utf8),
        ).alias("supporting_blog_urls")
    )


def run(embeddings: Path = Path("data/processed/embeddings.parquet")) -> None:
    items = pl.read_parquet(embeddings).select("entry_id", "text", "source", "date")
    codes_df = open_code(items)
    print(f"Open-coded {codes_df.height} items "
          f"(mean pass-agreement {codes_df['stability'].mean():.2f})")

    themes_df = axial_code(codes_df)
    codes_df = assign_themes(codes_df, themes_df)
    themes_df = add_supporting_blogs(themes_df, codes_df)
    codes_df.write_parquet("data/processed/codes.parquet")
    themes_df.write_parquet("data/processed/themes.parquet")

    # Consistency audit: entries whose two open-coding passes disagreed most.
    low = codes_df.filter(pl.col("stability") < 0.5)
    audit = {
        "mean_stability": codes_df["stability"].mean(),
        "n_low_stability": low.height,
        "low_stability_entries": low.select(
            "entry_id", "codes_a", "codes_b", "stability"
        ).to_dicts(),
    }
    Path("data/processed/coding_audit.json").write_text(json.dumps(audit, indent=2))

    print(f"Derived {themes_df.height} mental-model themes:")
    for name in themes_df["name"].to_list():
        print(f"  - {name}")
    print(f"Audit: {low.height} low-stability entries -> "
          f"data/processed/coding_audit.json")


if __name__ == "__main__":
    run()
