# src/cmm/embed_cluster.py
"""Quantitative spine: embed entries, cluster (HDBSCAN), project (UMAP)."""
from pathlib import Path

import hdbscan
import polars as pl
import umap
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"  # pinned local model


def build(changelog: Path = Path("data/processed/changelog.parquet"),
          blogs: Path = Path("data/processed/blogs.parquet"),
          out: Path = Path("data/processed/embeddings.parquet")) -> Path:
    """Embed changelog entries + CC-relevant blogs, cluster, and 2D-project."""
    cl = pl.read_parquet(changelog).select(
        pl.col("id").alias("entry_id"),
        pl.col("text"),
        pl.lit("changelog").alias("source"),
        pl.col("date"),
        pl.col("version"),
    )
    bl = (pl.read_parquet(blogs).filter(pl.col("cc_relevant"))
          .select(
              pl.col("url").alias("entry_id"),
              (pl.col("title") + ". " + pl.col("body").str.slice(0, 800)).alias("text"),
              pl.lit("blog").alias("source"),
              pl.col("date"),
              pl.lit(None, dtype=pl.Utf8).alias("version"),
          ))
    df = pl.concat([cl, bl])

    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode(df["text"].to_list(), show_progress_bar=True)

    labels = hdbscan.HDBSCAN(min_cluster_size=5).fit_predict(vectors)
    coords = umap.UMAP(n_components=2, random_state=42).fit_transform(vectors)

    out_df = df.with_columns(
        pl.Series("cluster_label", labels),
        pl.Series("umap_x", coords[:, 0]),
        pl.Series("umap_y", coords[:, 1]),
        pl.Series("vector", [v.tolist() for v in vectors]),
    )
    out = Path(out)
    out_df.write_parquet(out)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"Embedded {out_df.height} items into {n_clusters} clusters")
    return out


if __name__ == "__main__":
    build()
