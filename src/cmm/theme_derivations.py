"""The three theme derivations (B1 bottom-up, B1.5 consolidation, B3 independent).

B2 (top-down) reuses cmm.thematic_coding.discover_themes unchanged.
"""
import concurrent.futures
from pathlib import Path

import polars as pl

from cmm.llm import complete_json as claude_json

MINI_SYSTEM = (
    "You are a qualitative researcher. You are given a cluster of Claude Code "
    "release items that an embedding model grouped together. State the single "
    "latent user assumption or competency these items share -- the conceptual "
    "thing a user had to internalize. Return JSON "
    '{"mini_theme": "<=6 words", "description": "one sentence"}.'
)


def cluster_samples(embeddings: pl.DataFrame, sample_size: int = 15
                    ) -> dict[int, list[str]]:
    """Return {cluster_label: [entry texts]} for every non-noise cluster.

    Each cluster is capped at `sample_size` texts (evenly indexed).
    """
    out: dict[int, list[str]] = {}
    for c in sorted(embeddings["cluster_label"].unique()):
        if c == -1:
            continue
        texts = embeddings.filter(pl.col("cluster_label") == c)["text"].to_list()
        if len(texts) > sample_size:
            step = len(texts) / sample_size
            texts = [texts[int(i * step)] for i in range(sample_size)]
        out[int(c)] = texts
    return out


def _mini_theme(cluster: int, texts: list[str]) -> dict:
    """One LLM call -> the mini-theme for one cluster."""
    listing = "\n".join(f"- {t[:200]}" for t in texts)
    r = claude_json(f"Cluster {cluster} items:\n{listing}",
                    system=MINI_SYSTEM, max_tokens=400)
    return {"cluster_label": cluster, "mini_theme": r["mini_theme"],
            "description": r["description"]}


def bottom_up_mini_themes(embeddings: pl.DataFrame, max_workers: int = 8
                          ) -> pl.DataFrame:
    """B1: one mini-theme per non-noise cluster, in parallel.

    Returns columns: cluster_label, mini_theme, description.
    """
    samples = cluster_samples(embeddings)
    rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_mini_theme, c, t): c for c, t in samples.items()}
        for fut in concurrent.futures.as_completed(futs):
            rows.append(fut.result())
    return pl.DataFrame(rows).sort("cluster_label")


def run_b1(embeddings: Path = Path("data/processed/embeddings.parquet"),
           out: Path = Path("data/processed/mini_themes.parquet")) -> None:
    emb = pl.read_parquet(embeddings)
    mini = bottom_up_mini_themes(emb)
    mini.write_parquet(out)
    print(f"B1: {mini.height} mini-themes from clusters")


if __name__ == "__main__":
    run_b1()
