# CLAUDE.md — claude-mental-models

Research project: analyzes Claude Code's release history (changelog + Anthropic
blogs) as a proxy for the mental models a developer had to evolve over ~17
months (themes derived at month 14, corpus extended incrementally). `@research` project — pin versions, `uv` venv.

## Stack & commands

- Python 3.13 via `uv`. Package: `src/cmm/`. Notebook: `notebooks/analysis.py` (marimo, full/local — has RAG chat).
- Run the pipeline: `uv run python -m cmm.{collect_changelog,collect_blogs,tag_and_join,embed_cluster,thematic_coding}`
- **Incremental refresh (themes fixed):** `uv run python -m cmm.{collect_changelog,collect_blogs,tag_and_join,refresh}` — `refresh` assigns only new entries, writes `data/processed/refresh_report.json`, and refuses to write tables if new-item residual >5% or one theme >40% of new items (that means choice (b), full re-derivation — a human call).
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

**Corpus refreshed to v2.1.251 (2026-08-29) with the May theme model held
fixed** — choice (a). 4,919 entries / 380 releases / 45 posts; 1,868 new items
assigned to the 13 anchors (residual 1.34%, top theme 19.0% — neither
escalation trigger fired). Notebook prose, findings, methodology §5, README
updated; WASM build rebuilt; article untouched, stale claims listed in
`articles/2026-08-29-refresh-notes.md`.

**Pushed to main + live on Pages 2026-08-29** (`d1e48a7`). The article draft
is updated to the refreshed numbers (second editorial review applied) but
**not published to any platform**.

**Open follow-ups (next session, in priority):**
1. **Finish distribution**: publish Substack draft 213283501; delete test
   draft 213286503; post the X thread by hand from `articles/social/`.
2. **Manual audit** — `data/processed/audit_sample.csv` (40 May rows, blank
   `agree`); record per-stratum agreement in `findings.md`.
3. Next refresh: watch the two triggers; if residual >5% or one theme >40%,
   that is choice (b) — full re-derivation.

## Publishing conventions (Vishal's ruling, 2026-08-29)

- The published article (`articles/<date>-<slug>.md/.html`) and its refresh
  notes stay tracked.
- `articles/social/` and `articles/drafts/` are gitignored, in this repo and
  in `~/.gitignore_global`. Posting plans and social drafts never go public.
- Before committing ANY new file under `articles/`, state what it is
  (draft / final / plan) and ask Vishal. A final piece is committed the day
  it is published, not before.
- Chart PNGs for articles live in `docs/img/` (public, served by Pages).

## Roadmap

- [x] Phase 1: v1 pipeline + marimo notebook + methodology note.
- [x] Phase 2: methodological rebuild + persona lens (merged 2026-05-25).
- [x] Phase 2b: publish notebook publicly — GitHub Pages WASM build, live at
      `vishalsachdev.github.io/claude-mental-models/` (2026-05-27).
- [x] Phase 2d: write the Hybrid Builder article (drafted 2026-05-27).
- [x] Phase 2f: incremental corpus refresh to v2.1.251 (`cmm.refresh`,
      2026-08-29) — themes fixed, triggers clean.
- [ ] Phase 2e: publish article to Substack / LinkedIn / Twitter (rewrite
      from `articles/2026-08-29-refresh-notes.md` first).
- [ ] Phase 2c: manual audit (40 stratified rows → agreement rates).
- [x] Phase 3 (Codex, 2026-08-26): personal-usage overlay —
      `docs/usage-evidence-2026-08-26.{md,html}` (11 of 13 models evidenced).

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

### 2026-08-29 — incremental refresh (merged ff to main, pushed, branch deleted)
- Feasibility first (read-only): delta was 84 versions / 1,862 entries
  (v2.1.152–2.1.251) + 12 posts; full re-derivation would invalidate every
  bottom-up artifact, so chose (a) with escalation triggers.
- Fixed three collector defects (fetch-without-checkout; blog date extractor
  returning `siteSettings._createdAt` for every post; undated index cache
  key) and the string version sort — each with a positive control.
- Method corrections logged in `findings.md`: best-practices post re-dated
  2026-05-14 → 2025-04-18 (narration 37.8% → 38.9/39.2%); change-type table
  had not summed to 3,057; one orphan row from an upstream edit.
- New `cmm.refresh`: fixed anchors, per-entry content-keyed assignment cache,
  clusters/coherence frozen as the 2026-05-23 solution (`cluster_label=-2`
  for new rows), `refresh_report.json` with triggers.
- Findings that moved: Aug 2026 = 731 entries (record); removal rate
  11.8% → 27.4% post-May; Multi-Agent Orchestration 6th → 2nd by size.
- Codex session 2026-08-26 (`5ef0614`) had already delivered Phase 3.
- Article updated to the refresh (`d1e48a7`): churn-shift lede, tripwire
  subsection, review P1s applied, no em-dashes.
- Licensing/metadata pass (`18c428b`, `fc7c394`): MIT + CC BY 4.0 data card,
  blog bodies truncated to 1,500-char excerpts, GitHub description/topics.
- Distribution: **LinkedIn newsletter edition published by Vishal today**
  (draft 7499490414584844288 staged by browser automation, images added by
  hand). **Substack draft 213283501 pending his publish** (cover og-pace.png
  set via python-substack). **X thread posted 2026-08-29 5:51 pm CDT** (8 of 9 live, tweet 1
  pinned: x.com/vishalsachdev/status/2093833846185660624; staged via the
  native composer, Vishal pressed Post all; the @AnthropicAI question
  did not appear live): the X API path is shelved (Free tier = 1 app,
  post cap 0; pay-per-use billing declined). LinkedIn developer app
  `Hybrid Builder Publisher` (263546090, Page ChatWithGpt) exists but the
  OAuth grant was not completed (password prompt). **Substack test draft
  213286503 to delete.**
- Social drafts + posting plan moved out of git (`bea2342`); chart PNGs in
  `docs/img/`.

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
