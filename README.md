# Claude Code Mental Models

Analysis of how Claude Code's changelog and Anthropic's blogs reveal the
evolving mental models of Claude Code use — 4,919 changelog entries across
380 releases (v0.2.21 – v2.1.251, April 2025 – August 2026) and 45 blog
posts. The 13 themes were derived on the corpus through 2026-05-23 and
extended by an incremental refresh (`cmm.refresh`, see
`docs/methodology.md` §5). See the design spec and plan in
`docs/superpowers/`, and findings in `docs/findings.md`.

## Run the pipeline

```bash
uv sync
# LLM calls use the local `claude` CLI (subscription auth) — no API key needed.
uv run python -m cmm.collect_changelog
uv run python -m cmm.collect_blogs
uv run python -m cmm.tag_and_join
uv run python -m cmm.embed_cluster
uv run python -m cmm.thematic_coding
uv run marimo run notebooks/analysis.py
```

To extend the corpus to the latest upstream release **without** re-deriving
the themes (incremental refresh — themes and clusters stay fixed, only new
entries are assigned):

```bash
uv run python -m cmm.collect_changelog   # checks out origin/main, re-parses
uv run python -m cmm.collect_blogs       # carries previous URLs forward
uv run python -m cmm.tag_and_join
uv run python -m cmm.refresh             # writes refresh_report.json; stops if a trigger fires
```

All network and LLM calls are cached in `data/cache/`.

## Deliverable

`notebooks/analysis.py` — a marimo notebook: feature-volume / churn / blog-coverage
/ mental-model-emergence charts, an interactive cluster explorer, a themes
reference table, and a RAG chat panel grounded in the corpus.

## Licensing

- **Code** (`src/`, `notebooks/`, `tests/`): [MIT](LICENSE), © 2026 Vishal Sachdev.
- **Derived data** (`data/processed/` theme, assignment, join, persona and
  coherence tables, and the JSON summaries): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  — see the [data card](data/README.md) for the per-file table, provenance
  and a suggested citation.
- **Upstream text**: the changelog entries reproduced in
  `data/processed/changelog.parquet` are Anthropic's, from
  [anthropics/claude-code](https://github.com/anthropics/claude-code), and
  stay under Anthropic's terms; `blogs.parquet` carries short excerpts and
  links to anthropic.com posts, not full articles.

