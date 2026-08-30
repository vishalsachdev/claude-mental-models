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

**Refresh shipped and distributed (2026-08-29).** Live notebook at v2.1.251;
article rewritten; LinkedIn newsletter published; X thread posted (8/9 live,
tweet 1 pinned); Substack draft 213283501 waiting on Vishal.

**Open follow-ups (next session, in priority):**
1. Publish Substack draft 213283501; delete test draft 213286503.
2. Manual audit — `data/processed/audit_sample.csv` (40 May rows, blank
   `agree`); record per-stratum agreement in `findings.md`.
3. Next refresh: watch the two triggers (new-item residual >5%, one theme
   >40%); either firing means choice (b), full re-derivation.

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

### 2026-08-29
- Completed: incremental corpus refresh to v2.1.251 with the May theme model
  held fixed (`cmm.refresh`, triggers 1.34% / 19.0%, neither fired); three
  collector defects + string version sort fixed with positive controls; method
  corrections logged in findings.md; notebook/WASM/findings/methodology/README
  updated and live on Pages; MIT + CC BY 4.0 data card; GitHub metadata;
  article rewritten to the refresh (two editorial reviews); publishing
  conventions added; social drafts moved out of git.
- Distribution: **LinkedIn newsletter edition published** by Vishal (draft
  7499490414584844288 staged by automation, images added by hand).
  **X thread posted by Vishal 2026-08-29 at 5:51 PM CDT** (tweet timestamp
  2026-08-29T22:51:05Z) via the native thread composer: 8 of 9 tweets verified
  live, tweet 1 pinned
  (x.com/vishalsachdev/status/2093833846185660624 … 2093833859489997017,
  full list in the local `.x.plan.txt`); tweet 9 (the @AnthropicAI/@claudeai
  question) was not found live (not under tweet 8, not on the Replies tab).
  **Substack draft 213283501** (cover og-pace.png set via python-substack)
  **pending Vishal's publish. Substack test draft 213286503 to delete.**
- Apps: LinkedIn developer app `Hybrid Builder Publisher` (263546090, Page
  ChatWithGpt) exists with products + redirect + 0600 env file, OAuth grant
  not completed (password prompt); X API shelved (1-app Free quota, post cap
  0, pay-per-use declined).
- Next: publish Substack 213283501; delete 213286503; optionally reply tweet 9
  by hand; finish LinkedIn OAuth (`authorize-linkedin.py`) if API posting is
  wanted; manual audit (`audit_sample.csv`); watch the two refresh triggers.

*Older entries archived to `docs/session-archive.md`.*
