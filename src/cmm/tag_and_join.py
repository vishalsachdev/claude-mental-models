# src/cmm/tag_and_join.py
"""Tag blogs for Claude Code relevance and join them to changelog versions."""
import json
from datetime import date
from pathlib import Path

import polars as pl

from cmm.llm import complete_json

TAG_SYSTEM = (
    "You classify Anthropic blog posts by whether they are relevant to "
    "competencies and expectations of a Claude Code (CLI / coding agent / "
    "agent SDK) user. Respond ONLY with JSON: "
    "{\"cc_relevant\": bool, \"cc_confidence\": 0..1}."
)


def tag_blog(post: dict) -> dict:
    """Return the post dict augmented with cc_relevant and cc_confidence."""
    prompt = (
        f"Title: {post['title']}\n\n"
        f"Excerpt: {post['body'][:1500]}\n\n"
        "Is this relevant to how someone uses Claude Code (the coding agent)?"
    )
    verdict = complete_json(prompt, system=TAG_SYSTEM, max_tokens=200)
    return {**post, "cc_relevant": bool(verdict["cc_relevant"]),
            "cc_confidence": float(verdict["cc_confidence"])}


def _name_overlap(entry_text: str, blog_title: str) -> bool:
    """True if a salient word from the changelog entry appears in the title."""
    stop = {"the", "a", "an", "for", "and", "with", "to", "of", "in", "on",
            "added", "fixed", "support", "new", "now", "when"}
    words = {w.lower().strip(".,`") for w in entry_text.split() if len(w) > 3}
    words -= stop
    title = blog_title.lower()
    return any(w in title for w in words)


def join_changelog_blogs(changelog: pl.DataFrame, blogs: pl.DataFrame,
                         window_days: int = 14) -> pl.DataFrame:
    """Join each changelog version to blogs within +/- window_days that also
    share a feature word. Returns one row per version with blog_urls + tier.
    """
    rows = []
    versions = (changelog.filter(pl.col("date").is_not_null())
                .group_by("version")
                .agg(pl.col("date").first(), pl.col("text")))
    cc_blogs = blogs.filter(pl.col("cc_relevant") & pl.col("date").is_not_null())
    for v in versions.iter_rows(named=True):
        vdate = date.fromisoformat(v["date"])
        matched = []
        for b in cc_blogs.iter_rows(named=True):
            bdate = date.fromisoformat(b["date"])
            if abs((bdate - vdate).days) > window_days:
                continue
            if any(_name_overlap(t, b["title"]) for t in v["text"]):
                matched.append(b["url"])
        rows.append({
            "version": v["version"],
            "date": v["date"],
            "blog_urls": sorted(set(matched)),
            "impact_tier": "narrated" if matched else "silent",
        })
    return pl.DataFrame(rows)


def run(blogs_raw: Path = Path("data/raw/blogs.json"),
        changelog: Path = Path("data/processed/changelog.parquet")) -> None:
    posts = json.loads(Path(blogs_raw).read_text())
    tagged = [tag_blog(p) for p in posts]
    blogs_df = pl.DataFrame(tagged)
    blogs_df.write_parquet("data/processed/blogs.parquet")
    print(f"Tagged {len(blogs_df)} blogs; "
          f"{blogs_df['cc_relevant'].sum()} CC-relevant")

    joins = join_changelog_blogs(pl.read_parquet(changelog), blogs_df)
    joins.write_parquet("data/processed/joins.parquet")
    narrated = joins.filter(pl.col("impact_tier") == "narrated").height
    print(f"Joined {joins.height} versions; {narrated} narrated")


if __name__ == "__main__":
    run()
