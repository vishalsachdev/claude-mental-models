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

**Methodological rebuild + persona lens shipped and merged to `main`.**
The interpretive layer is now triangulated (B1 bottom-up clusters → B1.5
consolidation → corroborated by B2 top-down + B3 GPT-5.5 via `codex exec`),
producing 13 anchor themes with confidence tiers (7 high / 3 provisional /
3 bottom-up-only) and a first-class `coherence.parquet` diagnostic
(median 0.30 — the smearing v1 had is now *measurable*, not fixed). The
notebook (`notebooks/analysis.py`) is persona-aware: pick analyst / pm_ops /
researcher / vibe_coder and the mental-model map + emergence chart + theme
table all re-orient.

**Open follow-ups (next session, in priority):**
1. Share the notebook publicly — molab is the canonical path (RAG chat
   won't work; everything else will). Probe `marimo export html-wasm`
   first to see if a fully-static version is viable.
2. Manual audit — `data/processed/audit_sample.csv` (40 rows, blank `agree`
   column), record per-stratum agreement rates in `findings.md`.
3. Phase 3 personal-artifact overlay (still deferred).

## Roadmap

- [x] Phase 1: v1 pipeline + marimo notebook + methodology note.
- [x] Phase 2: methodological rebuild + persona lens (merged 2026-05-25).
- [ ] Phase 2b: publish notebook publicly (molab or WASM static).
- [ ] Phase 2c: manual audit (40 stratified rows → agreement rates).
- [ ] Phase 3 (deferred): overlay ~100 personal artifacts as a parallel
      adoption timeline (`personal_artifact` table reserved in the spec).

## Gotchas (rebuild-era)

- **`codex exec` hangs without `stdin=DEVNULL`.** Even with a positional
  prompt, codex reads stdin and blocks if the parent has an open pipe/TTY.
  `src/cmm/codex_llm.py` passes `stdin=subprocess.DEVNULL` — don't remove
  it. Smoke-test via `uv run python -c "from cmm.codex_llm import
  complete_json; print(complete_json('Return {\"ok\": true}.'))"` (returns
  in ~10s).
- **B3 reproducibility:** `data/processed/independent_derivation.json` is
  committed. `independent_themes()` reads it if present and never re-calls
  Codex. Don't delete this file.
- **The 2025-04-02 changelog floor is real, not a clone-depth artifact.**
  Upstream `anthropics/claude-code` committed its initial `CHANGELOG.md`
  with 17 versions seeded in one batch. A1's full-history clone is a
  defensive safeguard, not a data fix.
- **marimo cell variables must be unique** across the notebook (reactive
  graph requirement). If two cells define `selected_p`, marimo errors
  on load — rename one.

## Session Log

### 2026-05-22 → 2026-05-26
- Brainstormed the rebuild into a spec (3 open questions resolved); plan
  through Codex Plan Reviewer (REJECT → R1 fixes → executed).
- Executed all 15 rebuild tasks via subagent-driven dev: A1–A3 corpus +
  embeddings, B1–B7 triangulated theme layer, C1–C4 reconciliation +
  presentation. Merged to main.
- **3 rounds of `codex review --base main`**, 6 findings caught and
  fixed (P1 shallow-clone, P1 stale theme table, P2 blog counts,
  P2 embedding docs, P2 maintenance leak in heatmap). Each round caught
  real bugs.
- Notebook reframed as Why/How/What with per-chart narrative; **persona
  lens** added (`src/cmm/persona_lens.py` → `persona_relevance.parquet`,
  52 rows). Notebook now persona-aware: title cell, "Your mental-model
  map" headline, theme-emergence chart, and theme table all reshape per
  persona.
- Coherence finding: median 0.30 across 13 themes; only 2 (Permissions,
  MCP) clear 0.5 — `methodology.md §3.3` engages this honestly as the
  rebuild's most honest output.
- Next: publish publicly (molab probe) → manual audit.

*Older entries archived to `docs/session-archive.md`.*
