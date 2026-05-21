# Claude Code Mental Models

Analysis of how Claude Code's changelog and Anthropic's blogs reveal the
evolving mental models of Claude Code use over ~a year. See the design spec
and plan in `docs/superpowers/`, and findings in `docs/findings.md`.

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

All network and LLM calls are cached in `data/cache/`.

## Deliverable

`notebooks/analysis.py` — a marimo notebook: feature-volume / churn / blog-coverage
/ mental-model-emergence charts, an interactive cluster explorer, a themes
reference table, and a RAG chat panel grounded in the corpus.
