# src/cmm/persona_lens.py
"""Score each anchor theme's relevance to four user personas.

For each persona, one cached Claude call asks: of the 13 anchor themes, which
mental models does *this* user encountering Claude Code's evolving surface need
to build, and why? Returns high/medium/low per theme with a one-sentence
rationale that becomes the per-persona narrative in the notebook.
"""
import json
from pathlib import Path

import polars as pl

from cmm.llm import complete_json as claude_json

PERSONAS = {
    "analyst": (
        "A data analyst using Claude (via Skills and notebooks) to wrangle "
        "and explore data. Writes some SQL and Python but does not think of "
        "themselves as a software developer; never opens a terminal if a "
        "notebook or chat will do."
    ),
    "pm_ops": (
        "A product manager using Claude as an operations automation tool — "
        "scheduled tasks, multi-agent workflows, dashboards. Their interface "
        "is configuration files, system prompts, and Skills — not code. "
        "Cares about reliability, cost, and who is allowed to do what."
    ),
    "researcher": (
        "An academic or scientific researcher using Claude for literature "
        "review, paper writing, and reproducible long-form analysis. "
        "Sessions span days; context, citations, and provenance matter more "
        "than IDE integration."
    ),
    "vibe_coder": (
        "A non-professional coder who builds projects by letting the agent "
        "drive — high-level intent in, working code out. Reads diffs only "
        "when something breaks; lives mostly in the chat surface, not the "
        "terminal."
    ),
}

PERSONA_SYSTEM = (
    "You are reframing a list of named themes (each one a competency the "
    "surface of Claude Code increasingly demands of its users) through one "
    "specific user persona. For EACH theme, decide whether the persona has "
    "to build a new mental model around it — high (this is core to using "
    "Claude Code well as this persona), medium (occasionally relevant; the "
    "persona will brush against it), or low (a CLI / developer concern this "
    "persona can mostly ignore). Then write one sentence describing the "
    "MENTAL MODEL the persona must build — phrased as 'You will need to "
    "understand that …' or 'You will have to internalize …'. Be concrete; "
    "do not parrot the theme name back. Return JSON "
    '{"themes": [{"theme": "<exact theme name>", "relevance": "high|medium|low", '
    '"mental_model": "<one sentence, 2nd person>"}]}. Include ALL themes from '
    "the input list, in the same order."
)


def _score_persona(persona: str, description: str,
                   themes_df: pl.DataFrame) -> list[dict]:
    """One LLM call: persona-relevance scores for all themes."""
    theme_listing = "\n".join(
        f"- {t['name']}: {t['description']}"
        for t in themes_df.iter_rows(named=True))
    prompt = (
        f"Persona: {persona}\n"
        f"Persona description: {description}\n\n"
        f"Themes (anchor competencies from the Claude Code analysis):\n"
        f"{theme_listing}"
    )
    r = claude_json(prompt, system=PERSONA_SYSTEM, max_tokens=3000)
    return r["themes"]


def compute_persona_relevance(themes_path: Path = Path("data/processed/themes.parquet"),
                              out: Path = Path("data/processed/persona_relevance.parquet"),
                              ) -> pl.DataFrame:
    """For each persona, score all themes; write a long-format parquet.

    Columns: persona, theme, relevance, mental_model.
    """
    themes = pl.read_parquet(themes_path).select("name", "description")
    rows: list[dict] = []
    valid_themes = set(themes["name"].to_list())
    for persona, desc in PERSONAS.items():
        scored = _score_persona(persona, desc, themes)
        for s in scored:
            if s["theme"] not in valid_themes:
                # Skip hallucinated theme names rather than poisoning the join.
                continue
            rows.append({
                "persona": persona,
                "theme": s["theme"],
                "relevance": s["relevance"].lower(),
                "mental_model": s["mental_model"],
            })
    df = pl.DataFrame(rows)
    df.write_parquet(out)
    print(f"persona_lens: scored {df.height} (persona, theme) pairs "
          f"({len(PERSONAS)} personas x {themes.height} themes)")
    return df


if __name__ == "__main__":
    compute_persona_relevance()
