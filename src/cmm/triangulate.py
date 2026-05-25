# src/cmm/triangulate.py
"""B4-B7: anchored triangulation, descriptions, unassigned handling, tiering.

The anchor theme set (B1.5) is canonical. B2/B3 themes corroborate it; they
never add or rename anchor themes.
"""
import json
from pathlib import Path

import polars as pl

from cmm.codex_llm import complete_json as codex_json
from cmm.thematic_coding import assign_themes

CORROBORATE_SYSTEM = (
    "You are an independent reviewer. You are given one ANCHOR theme and a "
    "list of CANDIDATE themes from another analysis. Decide whether any "
    "candidate expresses substantially the same user competency/expectation "
    "as the anchor (same concept, wording may differ). Return JSON "
    '{"corroborated": bool, "match": "<candidate name or empty>", '
    '"rationale": "one sentence"}.'
)


def confidence_tier(corr_top_down: bool, corr_independent: bool) -> str:
    """Map the two corroboration booleans to a confidence tier."""
    if corr_top_down and corr_independent:
        return "high"
    if corr_top_down or corr_independent:
        return "provisional"
    return "bottom_up_only"


def _corroborates(anchor: dict, candidates: pl.DataFrame) -> dict:
    """Ask the independent model whether `candidates` corroborate `anchor`."""
    listing = "\n".join(f"- {r['theme_name']}: {r['description']}"
                        for r in candidates.iter_rows(named=True))
    return codex_json(
        f"ANCHOR theme:\n{anchor['name']}: {anchor['description']}\n\n"
        f"CANDIDATE themes:\n{listing}",
        system=CORROBORATE_SYSTEM, max_tokens=400)


def triangulate(anchor: pl.DataFrame, derivations: pl.DataFrame) -> pl.DataFrame:
    """B4: tag each anchor theme with corroboration booleans + confidence tier.

    `anchor` has columns name, description, source_clusters.
    Returns anchor + corroborated_top_down, corroborated_independent,
    confidence_tier, corroboration_notes.
    """
    top_down = derivations.filter(pl.col("derivation") == "top_down")
    independent = derivations.filter(pl.col("derivation") == "independent")
    rows = []
    for a in anchor.iter_rows(named=True):
        td = _corroborates(a, top_down)
        ind = _corroborates(a, independent)
        rows.append({
            **a,
            "corroborated_top_down": bool(td["corroborated"]),
            "corroborated_independent": bool(ind["corroborated"]),
            "confidence_tier": confidence_tier(bool(td["corroborated"]),
                                               bool(ind["corroborated"])),
            "corroboration_notes": json.dumps({"top_down": td, "independent": ind}),
        })
    return pl.DataFrame(rows, schema_overrides={"source_clusters": pl.List(pl.Int64)})


def assign_to_anchor(anchor: pl.DataFrame, embeddings: pl.DataFrame) -> pl.DataFrame:
    """Re-assign every corpus entry to the final anchor theme set.

    Reuses cmm.thematic_coding.assign_themes (the existing batched assigner),
    feeding it the anchor themes as the theme list.
    """
    items = embeddings.select("entry_id", "text", "source", "date")
    theme_list = anchor.select(pl.col("name"), pl.col("description"))
    return assign_themes(items, theme_list)
