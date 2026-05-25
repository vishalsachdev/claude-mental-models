"""C1: cluster<->theme reconciliation as a first-class pipeline output.

Per theme: how its assigned entries distribute over the embedding clusters.
coherence_score = top_cluster_share (1.0 = all entries in one cluster).
"""
from collections import Counter
from pathlib import Path

import polars as pl

from cmm.triangulate import MAINTENANCE_LABEL


def coherence_row(theme: str, cluster_labels: list[int]) -> dict:
    """Coherence stats for one theme from its entries' cluster labels.

    The HDBSCAN noise label (-1) is excluded from all stats.
    """
    labels = [c for c in cluster_labels if c != -1]
    if not labels:
        return {"theme": theme, "cluster_spread": 0, "top_cluster": -1,
                "top_cluster_share": 0.0, "coherence_score": 0.0}
    counts = Counter(labels)
    top_cluster, top_n = counts.most_common(1)[0]
    share = top_n / len(labels)
    return {
        "theme": theme,
        "cluster_spread": len(counts),
        "top_cluster": int(top_cluster),
        "top_cluster_share": round(share, 3),
        "coherence_score": round(share, 3),
    }


def build_coherence(codes: pl.DataFrame, embeddings: pl.DataFrame,
                    out: Path = Path("data/processed/coherence.parquet")
                    ) -> pl.DataFrame:
    """Write coherence.parquet — one row per real theme (Maintenance excluded)."""
    cluster_by_id = dict(zip(embeddings["entry_id"].to_list(),
                             embeddings["cluster_label"].to_list()))
    exploded = codes.explode("themes").drop_nulls("themes")
    rows = []
    for theme in exploded["themes"].unique().to_list():
        if theme == MAINTENANCE_LABEL:
            continue
        ids = exploded.filter(pl.col("themes") == theme)["entry_id"].to_list()
        labels = [cluster_by_id.get(e, -1) for e in ids]
        rows.append(coherence_row(theme, labels))
    df = pl.DataFrame(rows)
    df.write_parquet(out)
    print(f"C1: coherence for {df.height} themes")
    return df


if __name__ == "__main__":
    build_coherence(pl.read_parquet("data/processed/codes.parquet"),
                    pl.read_parquet("data/processed/embeddings.parquet"))
