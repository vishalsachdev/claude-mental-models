# CLAUDE.md — claude-mental-models

Research project: analyzes Claude Code's release history (changelog + Anthropic
blogs) as a proxy for the mental models a developer had to evolve over ~14
months. `@research` project — pin versions, `uv` venv.

## Stack & commands

- Python 3.13 via `uv`. Package: `src/cmm/`. Notebook: `notebooks/analysis.py` (marimo).
- Run the pipeline: `uv run python -m cmm.{collect_changelog,collect_blogs,tag_and_join,embed_cluster,thematic_coding}`
- View deliverable: `uv run marimo run notebooks/analysis.py`
- Tests: `uv run pytest -q`

## Gotchas (non-obvious)

- **LLM calls = headless `claude` CLI**, not the Anthropic API — subscription auth, no API key, no credits. See `src/cmm/llm.py` (model: `claude-sonnet-4-6`).
- All network/LLM calls cached in `data/cache/` (gitignored) — re-runs never re-hit network.
- `marimo run` + `sentence-transformers` needs `ipython` installed (transformers imports `IPython.display` in notebook context). Already a dep.
- `data/raw/`, `data/cache/` gitignored; `data/processed/*.parquet` committed.
- v1 thematic coding was redesigned mid-build: per-item open coding produced 17k non-recurring codes; now two-stage (discover themes from a sample → batch-assign).

## Current Focus

**v1 shipped and merged to `main`.** Council-reviewed; limitations in `docs/methodology.md`.

**Next: methodological rebuild** — plan at `docs/superpowers/plans/2026-05-21-analysis-improvement.md`.
Fixes 9 named problems (cluster↔theme reconciliation, top-down bias, reflexivity,
33% unassigned, etc.). 3 open questions need decisions before execution:
1. Independent model for cross-model theme pass — GPT-5.5, Gemini, or both?
2. Unassigned residual — explicit "Maintenance" category, or its own analysis section?
3. Is the headless blog re-scrape (A2) worth it, or defer?

Recommended path: brainstorm → spec → Codex Plan Reviewer → subagent-driven execution.

## Roadmap

- Phase 1 (done): v1 pipeline + marimo notebook + methodology note.
- Phase 2 (planned): methodological rebuild — see improvement plan above.
- Phase 3 (deferred): overlay the user's ~100 personal artifacts as a parallel
  adoption timeline (`personal_artifact` table reserved in the spec).

## Session Log

### 2026-05-20 / 05-21
- Built v1 end-to-end (spec → plan → 12 tasks via subagent-driven dev): two-corpus
  pipeline, embeddings spine, two-stage thematic coding, RAG, marimo notebook.
  Merged to `main`.
- Council-validated the methodology; wrote `docs/methodology.md`; ran the
  cluster×theme cross-tab (confirmed abstract themes smear across clusters).
- Wrote the improvement plan (methodological rebuild) — see Current Focus.
- Next: resolve the 3 open questions, then brainstorm the rebuild into a spec.
