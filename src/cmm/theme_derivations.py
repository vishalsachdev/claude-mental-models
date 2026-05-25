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


CONSOLIDATE_SYSTEM = (
    "You are a qualitative researcher. You are given a list of fine-grained "
    "mini-themes (each tied to an embedding cluster id). Group them into "
    "10-15 consolidated themes -- coherent user competencies/expectations. "
    "Every cluster id must appear in exactly one theme's source_clusters. "
    'Return JSON {"themes": [{"name": "short", "description": "one sentence", '
    '"source_clusters": [int, ...]}]}.'
)


def validate_consolidation(consolidated: list[dict], mini: pl.DataFrame) -> None:
    """Raise unless every mini-theme cluster is covered exactly once."""
    all_clusters = set(mini["cluster_label"].to_list())
    seen: list[int] = []
    for t in consolidated:
        seen += t["source_clusters"]
    covered = set(seen)
    if covered != all_clusters:
        missing = sorted(all_clusters - covered)
        extra = sorted(covered - all_clusters)
        raise ValueError(f"cluster cover mismatch: missing={missing} extra={extra}")
    if len(seen) != len(covered):
        raise ValueError(f"cluster assigned to >1 theme: {sorted(seen)}")


def consolidate_mini_themes(mini: pl.DataFrame) -> pl.DataFrame:
    """B1.5: group mini-themes into the canonical 10-15 anchor themes.

    Returns columns: name, description, source_clusters (list[int]).
    """
    listing = "\n".join(
        f"- cluster {r['cluster_label']}: {r['mini_theme']} — {r['description']}"
        for r in mini.iter_rows(named=True))
    r = claude_json(f"Mini-themes:\n{listing}",
                    system=CONSOLIDATE_SYSTEM, max_tokens=3000)
    consolidated = r["themes"]
    validate_consolidation(consolidated, mini)
    return pl.DataFrame(consolidated,
                        schema_overrides={"source_clusters": pl.List(pl.Int64)})


def run_b15(mini_path: Path = Path("data/processed/mini_themes.parquet"),
            out: Path = Path("data/processed/derivations.parquet")) -> None:
    """Run B1.5 and write the bottom_up rows of derivations.parquet."""
    mini = pl.read_parquet(mini_path)
    anchor = consolidate_mini_themes(mini)
    rows = anchor.select(
        pl.lit("bottom_up").alias("derivation"),
        pl.col("name").alias("theme_name"),
        pl.col("description"),
    )
    rows.write_parquet(out)
    # source_clusters is needed later by C1; keep it in a sidecar parquet.
    anchor.write_parquet(Path("data/processed/anchor_themes.parquet"))
    print(f"B1.5: consolidated to {anchor.height} anchor themes")


if __name__ == "__main__":
    run_b1()
