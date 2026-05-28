# CLAUDE.md — claude-mental-models

Research project: analyzes Claude Code's release history (changelog + Anthropic
blogs) as a proxy for the mental models a developer had to evolve over ~14
months. `@research` project — pin versions, `uv` venv.

## Stack & commands

- Python 3.13 via `uv`. Package: `src/cmm/`. Notebook: `notebooks/analysis.py` (marimo, full/local — has RAG chat).
- Run the pipeline: `uv run python -m cmm.{collect_changelog,collect_blogs,tag_and_join,embed_cluster,thematic_coding}`
- View local deliverable: `uv run marimo run notebooks/analysis.py`
- Tests: `uv run pytest -q`

**Published artifacts (external — agent can't guess these):**
- Public repo: `https://github.com/vishalsachdev/claude-mental-models` (origin)
- Live notebook (GitHub Pages, WASM): `https://vishalsachdev.github.io/claude-mental-models/`
- Pages source: `main:/docs`. Public notebook = `notebooks/analysis_public.py` (WASM-safe;
  fetches data from raw.githubusercontent.com, no RAG). Rebuild + redeploy with:
  `uv run marimo export html-wasm notebooks/analysis_public.py -o docs/ --mode run -f` then commit `docs/` + push.
- Article draft: `articles/2026-05-27-the-tool-as-teacher.md` (Hybrid Builder; not yet published to platforms).

## Gotchas (non-obvious)

- **LLM calls = headless `claude` CLI**, not the Anthropic API — subscription auth, no API key, no credits. See `src/cmm/llm.py` (model: `claude-sonnet-4-6`).
- All network/LLM calls cached in `data/cache/` (gitignored) — re-runs never re-hit network.
- `marimo run` + `sentence-transformers` needs `ipython` installed (transformers imports `IPython.display` in notebook context). Already a dep.
- `data/raw/`, `data/cache/` gitignored; `data/processed/*.parquet` committed.
- v1 thematic coding was redesigned mid-build: per-item open coding produced 17k non-recurring codes; now two-stage (discover themes from a sample → batch-assign).

## Current Focus

**Rebuild shipped, notebook published, article drafted.** The triangulated
analysis (13 anchor themes, 7 high / 3 provisional / 3 bottom-up-only,
coherence median 0.30) is merged; the persona-aware notebook is **live on
GitHub Pages** as a WASM build; a 1,304-word Hybrid Builder article
(`articles/2026-05-27-the-tool-as-teacher.md`) is written, link-verified, and
editorially reviewed (3 P1s fixed, 4 P2s left for the user).

**Open follow-ups (next session, in priority):**
1. **Publish the article to platforms** — `/publish-to-substack`,
   `/publish-to-linkedin`, `/publish-to-twitter`. Optionally cover images
   (RSA-Animate sketches) + a session-transcript gist first. 4 P2 polish
   notes from the editorial review are still open (temple-wall echo,
   buried 37.8% stat, concrete "try it on Cursor/Linear" examples).
2. **Manual audit** — `data/processed/audit_sample.csv` (40 rows, blank
   `agree` column), record per-stratum agreement rates in `findings.md`.
3. Phase 3 personal-artifact overlay (still deferred).

## Roadmap

- [x] Phase 1: v1 pipeline + marimo notebook + methodology note.
- [x] Phase 2: methodological rebuild + persona lens (merged 2026-05-25).
- [x] Phase 2b: publish notebook publicly — GitHub Pages WASM build, live at
      `vishalsachdev.github.io/claude-mental-models/` (2026-05-27).
- [x] Phase 2d: write the Hybrid Builder article (drafted 2026-05-27).
- [ ] Phase 2e: publish article to Substack / LinkedIn / Twitter.
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

### 2026-05-27 / 05-28
- Reframed the deliverable around **"the tool guides users to build mental
  models"** (restored the foreground framing C3 had downgraded) and added a
  **persona lens**: `src/cmm/persona_lens.py` scores all 13 themes ×
  4 personas (analyst / pm_ops / researcher / vibe_coder) → 52-row
  `persona_relevance.parquet`. Notebook now has a persona radio; mental-model
  map, emergence chart, and theme table all reshape per persona.
  (analyst = 3 high themes, pm_ops = 8 — running ops touches nearly everything.)
- Added **click-through verification links** (`src/cmm/urls.py`): every entry
  links to anthropic.com (blogs) or the CHANGELOG.md version anchor (changelog).
  New "Drill into a theme" notebook section.
- **Published the notebook**: created public GitHub repo, WASM build via
  `analysis_public.py` (httpx-fetches data, no RAG), GitHub Pages from
  `main:/docs`. Live + verified 200.
- **Wrote the Hybrid Builder article** (`articles/2026-05-27-the-tool-as-teacher.md`,
  1,304 words) via the write-article skill: links verified, editorial review
  (0 P0, 3 P1 fixed, 4 P2 open).
- Next: publish article to platforms (Substack/LinkedIn/Twitter) + manual audit.

*Older entries archived to `docs/session-archive.md`.*
