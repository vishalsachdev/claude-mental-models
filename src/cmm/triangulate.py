# src/cmm/triangulate.py
"""B4-B7: anchored triangulation, descriptions, unassigned handling, tiering.

The anchor theme set (B1.5) is canonical. B2/B3 themes corroborate it; they
never add or rename anchor themes.
"""
import json
from pathlib import Path

import polars as pl

from cmm.codex_llm import complete_json as codex_json
from cmm.llm import complete_json as claude_json
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


MAINTENANCE_LABEL = "Maintenance / no conceptual shift"


def label_unassigned(codes: pl.DataFrame) -> pl.DataFrame:
    """Replace empty theme lists with the explicit Maintenance label."""
    return codes.with_columns(
        pl.when(pl.col("themes").list.len() == 0)
        .then(pl.lit([MAINTENANCE_LABEL]))
        .otherwise(pl.col("themes"))
        .alias("themes"))


def residual_analysis(codes_before_label: pl.DataFrame,
                      embeddings: pl.DataFrame) -> dict:
    """Summarise the unassigned residual: size, change-type mix, examples.

    `codes_before_label` is codes BEFORE label_unassigned ran (empty lists
    still empty). Returns a dict written to residual_analysis.json.
    """
    residual = codes_before_label.filter(pl.col("themes").list.len() == 0)
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    total = codes_before_label.height
    return {
        "residual_count": residual.height,
        "residual_fraction": round(residual.height / total, 3) if total else 0.0,
        "by_source": dict(residual.group_by("source").len()
                          .iter_rows()),
        "examples": [text_by_id.get(e, "")[:160]
                     for e in residual["entry_id"].to_list()[:12]],
    }


def assign_to_anchor(anchor: pl.DataFrame, embeddings: pl.DataFrame) -> pl.DataFrame:
    """Re-assign every corpus entry to the final anchor theme set.

    Reuses cmm.thematic_coding.assign_themes (the existing batched assigner),
    feeding it the anchor themes as the theme list.
    """
    items = embeddings.select("entry_id", "text", "source", "date")
    theme_list = anchor.select(pl.col("name"), pl.col("description"))
    return assign_themes(items, theme_list)


DESCRIBE_SYSTEM = (
    "You are a qualitative researcher. Given a theme name and a sample of the "
    "release items ACTUALLY assigned to it, write a one-sentence description "
    "of the user competency/expectation the theme captures. Use only what the "
    'items evidence. Return JSON {"description": "one sentence"}.'
)

_STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
         "users", "user", "learned", "adopted", "had", "this", "that", "as",
         "is", "are", "was", "were", "be", "by", "from", "their", "they"}


def extractive_violations(description: str, member_texts: list[str]) -> list[str]:
    """Return salient description words that appear in NO member text.

    Salient = length > 4, not a stopword. An empty list means the description
    is fully grounded in its assigned entries.
    """
    corpus = " ".join(member_texts).lower()
    words = {w.lower().strip(".,`'\"()") for w in description.split()}
    salient = {w for w in words if len(w) > 4 and w not in _STOP}
    return sorted(w for w in salient if w not in corpus)


def regenerate_descriptions(triangulated: pl.DataFrame, codes: pl.DataFrame,
                            embeddings: pl.DataFrame) -> pl.DataFrame:
    """B5: rewrite each theme description from its assigned entries.

    Adds `description` (regenerated) and `description_flags` (json list of
    ungrounded words, empty if clean).
    """
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    exploded = codes.explode("themes").drop_nulls("themes")
    rows = []
    for t in triangulated.iter_rows(named=True):
        members = exploded.filter(pl.col("themes") == t["name"])["entry_id"].to_list()
        member_texts = [text_by_id.get(e, "") for e in members]
        if not member_texts:
            # No assigned entries — keep existing description, flag it.
            rows.append({**t, "description_flags": json.dumps(["NO_MEMBERS"])})
            continue
        sample = member_texts[:25]
        listing = "\n".join(f"- {x[:200]}" for x in sample)
        r = claude_json(f"Theme: {t['name']}\nAssigned items:\n{listing}",
                        system=DESCRIBE_SYSTEM, max_tokens=300)
        new_desc = r["description"]
        flags = extractive_violations(new_desc, member_texts)
        rows.append({**t, "description": new_desc,
                     "description_flags": json.dumps(flags)})
    return pl.DataFrame(rows, schema_overrides={"source_clusters": pl.List(pl.Int64)})
