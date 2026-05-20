# Claude Code Mental Models — Design Spec

**Date:** 2026-05-20
**Status:** Approved design — ready for implementation plan
**Author:** Vishal Sachdev (with Claude Code)

## 1. Purpose

Over the past ~year, building ~100 artifacts (apps, research projects,
knowledge-work tools, teaching tools) with Claude Code, the mental models
required to use the tool well have shifted — partly because Claude Code itself
kept shipping, refactoring, deprecating, and removing features.

This project treats **Claude Code's own release history as a proxy** for the
mental models a user had to develop. By analyzing what Anthropic shipped (the
changelog) and what they chose to narrate (the blogs), we reconstruct the
*sequence of conceptual shifts* a Claude Code user was implicitly asked to make.

The deliverable is a **data analysis with visuals**, delivered as a reactive
**marimo notebook**, plus a short written findings doc.

### Out of scope (Phase 1)

- The user's own ~100 artifacts. Phase 2 (separate spec) overlays a personal
  adoption timeline. The data model reserves a `personal_artifact` table so
  Phase 2 is a clean addition, not a refactor.

## 2. Approach summary

A **two-corpus, fully-cached pipeline** feeds a marimo notebook.

- **Corpus A — Changelog.** `anthropics/claude-code` `CHANGELOG.md`.
  Comprehensive but terse. Powers *volume* and *churn* (adds, changes,
  deprecations, removals).
- **Corpus B — Blogs.** Anthropic news + engineering posts. Sparse but rich.
  Provides an *impact signal* (a narrated release is, by Anthropic's editorial
  judgment, a bigger deal) and richer prose for interpretation.

Two analytical layers run over the joined corpora:

- **Quantitative spine** — local embeddings + HDBSCAN clustering. Deterministic
  and reproducible; does not drift between runs.
- **Interpretive layer** — LLM thematic coding (open → axial), producing named
  **mental models** with emergence dates. Inference is treated as unconstrained;
  multi-pass refinement and a consistency audit are expected.

The two layers **cross-check** each other: HDBSCAN clusters and axial themes
should roughly correspond. Divergences are themselves findings.

Expensive steps (network fetches, LLM calls) are plain scripts that write to
`data/`. The marimo notebook reads only processed data, so it stays fast and
reactive. Every network fetch and LLM call is cached to `data/cache/` keyed by
content hash — re-running never re-hits the network or the API.

## 3. Repository structure

```
claude-mental-models/
  pyproject.toml            # uv-managed, pinned versions
  src/
    collect_changelog.py    # 1. CHANGELOG.md + git-derived dates
    collect_blogs.py        # 2. crawl Anthropic news/engineering (broad)
    tag_and_join.py         # 3. CC-relevance tagging + changelog<->blog join
    embed_cluster.py        # 4. embeddings spine (quantitative)
    thematic_coding.py      # 5. LLM open->axial coding (interpretive)
    rag.py                  # 6. retriever + Claude chat model for the notebook
  data/
    raw/                    # untouched scrape output
    processed/              # normalized records (Parquet/JSON)
    cache/                  # HTTP + LLM response cache (content-hashed)
    fixtures/               # saved pages for parser unit tests
  notebooks/
    analysis.py             # marimo — the deliverable
  tests/
    test_collect_changelog.py
    test_collect_blogs.py
  docs/
    findings.md             # narrative conclusions
    superpowers/specs/      # this spec
```

## 4. Pipeline stages

### Stage 1 — Collect changelog (`collect_changelog.py`)

- Clone or fetch `anthropics/claude-code`.
- Parse `CHANGELOG.md` into `(version, entry_text)` pairs.
- Date each version from the **git log of `CHANGELOG.md`** (the commit that
  first introduced that version heading).
- Derive `change_type` per entry by keyword rules on the text:
  `{add, change, fix, deprecate, remove}`.
- Output: `data/processed/changelog.parquet`.

### Stage 2 — Collect blogs (`collect_blogs.py`)

- Crawl Anthropic news and engineering index pages for the window
  (2025-02-01 → present).
- For each post, fetch `title`, `date`, `url`, `body` (plain text).
- **Broad collection** — do not pre-filter for Claude Code relevance here.
- Output: `data/raw/blogs.json`.

### Stage 3 — Tag & join (`tag_and_join.py`)

- Classify each blog post for Claude Code relevance via LLM →
  `cc_relevant: bool`, `cc_confidence: float`.
- Join changelog versions to blogs by **date proximity + feature-name match**.
  Store matched `blog_urls[]` explicitly so the join is auditable.
- Derive `impact_tier` per version: `narrated` (has a blog) vs `silent`.
- Output: `data/processed/blogs.parquet`, `data/processed/joins.parquet`.

### Stage 4 — Embed & cluster (`embed_cluster.py`)

- Embed every changelog entry and every CC-relevant blog with
  `sentence-transformers` (local, no API, reproducible — pinned model).
- Cluster with HDBSCAN. Reduce to 2D with UMAP for plotting.
- Output: embeddings + cluster labels + 2D coords in
  `data/processed/embeddings.parquet`.

### Stage 5 — Thematic coding (`thematic_coding.py`)

- **Open coding:** LLM tags every changelog entry and every CC-relevant blog
  with short descriptive codes.
- **Axial coding:** LLM groups codes into ~6–10 named **mental models**, each
  with `name`, `description`, `member_codes[]`, `first_seen_date`,
  `supporting_blog_urls[]`.
- **Multi-pass refinement + consistency audit:** re-code and check theme
  stability; record disagreements.
- All LLM responses cached by content hash.
- Output: `data/processed/codes.parquet`, `data/processed/themes.parquet`.

### Stage 6 — RAG (`rag.py`)

- A retriever over the embeddings spine: given a question, return the most
  relevant changelog entries, blog excerpts, and themes.
- A custom marimo chat model: `(messages, config) -> response` that retrieves,
  then has Claude answer **grounded in retrieved data with inline citations**
  (version numbers, blog URLs).

## 5. Data model

Stored in `data/processed/` as Parquet (JSON for raw scrape output).

| Record | Fields |
|---|---|
| `changelog_entry` | `id, version, date, text, change_type` |
| `blog_post` | `url, title, date, body, cc_relevant, cc_confidence` |
| `join_record` | `version, date, blog_urls[], impact_tier` |
| `code` | `entry_id, codes[]` (open coding) |
| `theme` | `name, description, member_codes[], first_seen_date, supporting_blog_urls[]` |
| `embedding` | `entry_id, vector, cluster_label, umap_x, umap_y` |
| `personal_artifact` | *reserved, unused in Phase 1* |

`change_type ∈ {add, change, fix, deprecate, remove}`.
`impact_tier ∈ {narrated, silent}`.

## 6. The deliverable — `notebooks/analysis.py`

A reactive marimo notebook (also runnable as `marimo run` for a shareable app).
It reads only `data/processed/` and renders:

1. **Feature volume over time** — entries/month, stacked by `change_type`.
2. **Churn chart** — cumulative adds vs. deprecations/removals.
3. **Blog-coverage ratio** — % of releases narrated, over time.
4. **Mental-model emergence** — stream/area chart of when each named model
   first appears and how its weight grows. The centerpiece.
5. **Cluster explorer** — 2D UMAP scatter colored by theme, explored via
   `mo.ui.data_explorer`.
6. **Theme reference table** — each model → description → representative
   features → supporting blog links, via `mo.ui.data_explorer`.
7. **"Ask the corpus" RAG panel** — `mo.ui.chat` backed by the `rag.py` custom
   chat model. Answers questions about the changelog/blog/theme corpus, grounded
   with citations. Previews Phase 2: once personal artifacts are in the corpus,
   the same chat answers questions about the user's own trajectory.

`docs/findings.md` captures the narrative conclusions, explicitly including
where the embedding clusters and the LLM themes disagree.

## 7. Error handling

- Parsers (`collect_changelog`, `collect_blogs`) **fail loudly** with the
  offending URL or line if Anthropic changes page/file structure — no silent
  best-effort parsing.
- Entries with a missing or unresolvable date are **flagged and surfaced**,
  never silently dropped.
- HTTP and LLM caching keyed by content hash; cache hits are deterministic.
- Network calls retry with backoff before failing.

## 8. Testing

- **Unit tests** for the two parsers against saved fixture files in
  `data/fixtures/` — these are the brittle pieces most likely to break when
  upstream HTML/Markdown changes.
- Analysis stages (embedding, clustering, coding) are exploratory and validated
  by inspection within the notebook; no unit tests required.

## 9. Stack

Python via `uv` venv, all versions pinned (`@research` convention):

- `marimo` — notebook / app runtime
- `sentence-transformers` — local embeddings
- `hdbscan`, `umap-learn` — clustering + 2D projection
- `polars` — dataframes
- `httpx` — HTTP collection
- `anthropic` — LLM classification, thematic coding, RAG answering
- `altair` or `plotly` — charts

## 10. Phasing

- **Phase 1 (this spec):** two-corpus collection, both analytical layers, marimo
  notebook with the seven views including the RAG panel.
- **Phase 2 (later, separate spec):** populate `personal_artifact` with the
  user's ~100 projects (dates + features used) and overlay an adoption timeline
  to see where usage tracked or lagged releases.
