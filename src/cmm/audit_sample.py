# src/cmm/audit_sample.py
"""C4: emit a stratified ~40-item sample for manual audit.

Four strata: high-confidence theme matches (theme is confidence_tier=high and
the entry's cluster is the theme's top cluster), provisional matches (coherent
but the theme is not high-confidence), the Maintenance residual, and
cluster<->theme disagreements (entry's cluster is not the theme's top cluster).
The user fills the `agree` column by hand; the rate goes into findings.md.
"""
import random
from pathlib import Path

import polars as pl

from cmm.triangulate import MAINTENANCE_LABEL

_PER_STRATUM = 10  # 4 strata x 10 ~= 40 audit rows


def stratum_for(themes: list[str], theme_tier: str, coherent: bool) -> str:
    """Classify one entry into an audit stratum.

    `theme_tier` is the confidence_tier of the entry's first assigned theme.
    """
    if MAINTENANCE_LABEL in themes:
        return "residual"
    if not coherent:
        return "disagreement"
    return "high_confidence" if theme_tier == "high" else "provisional_match"


def build_sample(codes: pl.DataFrame, embeddings: pl.DataFrame,
                 themes: pl.DataFrame, coherence: pl.DataFrame,
                 out: Path = Path("data/processed/audit_sample.csv"),
                 seed: int = 42) -> Path:
    """Write the stratified audit CSV."""
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    cluster_by_id = dict(zip(embeddings["entry_id"].to_list(),
                             embeddings["cluster_label"].to_list()))
    tier_by_theme = dict(zip(themes["name"].to_list(),
                             themes["confidence_tier"].to_list()))
    topcluster_by_theme = dict(zip(coherence["theme"].to_list(),
                                   coherence["top_cluster"].to_list()))

    buckets: dict[str, list[dict]] = {"high_confidence": [], "provisional_match": [],
                                      "residual": [], "disagreement": []}
    for r in codes.iter_rows(named=True):
        tlist = r["themes"]
        first = tlist[0] if tlist else MAINTENANCE_LABEL
        tier = tier_by_theme.get(first, "high")
        entry_cluster = cluster_by_id.get(r["entry_id"], -1)
        coherent = entry_cluster == topcluster_by_theme.get(first, entry_cluster)
        s = stratum_for(tlist, tier, coherent)
        buckets[s].append({
            "entry_id": r["entry_id"],
            "text": text_by_id.get(r["entry_id"], "")[:200],
            "stratum": s,
            "assigned_themes": "; ".join(tlist),
            "top_cluster": topcluster_by_theme.get(first, ""),
            "agree": "",
        })

    rng = random.Random(seed)
    picked: list[dict] = []
    for s, items in buckets.items():
        rng.shuffle(items)
        picked += items[:_PER_STRATUM]
    pl.DataFrame(picked).write_csv(out)
    print(f"C4: wrote {len(picked)} audit rows to {out}")
    return out


if __name__ == "__main__":
    build_sample(
        pl.read_parquet("data/processed/codes.parquet"),
        pl.read_parquet("data/processed/embeddings.parquet"),
        pl.read_parquet("data/processed/themes.parquet"),
        pl.read_parquet("data/processed/coherence.parquet"),
    )
