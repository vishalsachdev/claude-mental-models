# Data card — `data/processed/`

Snapshot: **2026-08-29** (corpus through Claude Code v2.1.251, dated
2026-08-28). The theme model (clusters, anchors, coherence) was derived on
the corpus as of **2026-05-23** (v2.1.150, 3,079 items) and extended by an
incremental refresh; see `docs/methodology.md` §5.

`data/raw/` (full upstream clone and full blog bodies) and `data/cache/`
(every network and LLM response) are gitignored and never redistributed.

## Files

| File | What it is | Rows | Snapshot | Source / how produced |
|---|---|---:|---|---|
| `changelog.parquet` | One row per bullet in Claude Code's `CHANGELOG.md`: `id` (sha256 of version+text), `version`, `text`, `change_type` (keyword rule), `date` (git commit that added the version heading) | 4,919 | 2026-08-28 | Text is Anthropic's, parsed from [github.com/anthropics/claude-code](https://github.com/anthropics/claude-code) `CHANGELOG.md` at commit `f1af9b1` (full-history clone) |
| `blogs.parquet` | Anthropic news/engineering posts in the window: `title`, `date`, `url`, a **1,500-character excerpt** of the body (not the full post), plus LLM `cc_relevant` / `cc_confidence` tags | 45 | 2026-08-27 | Crawled from anthropic.com index pages (no pagination since 2026-08; 2026-05-20 → 06-29 is a known blind spot). One date corrected with provenance (`DATE_OVERRIDES` in `src/cmm/collect_blogs.py`) |
| `joins.parquet` | Per release: matching blog URLs within ±14 days sharing a feature word; `impact_tier` narrated / silent | 380 | 2026-08-28 | Derived (deterministic join) |
| `embeddings.parquet` | Every corpus item (changelog entry or CC-relevant blog excerpt): `text`, 768-d `vector` (`all-mpnet-base-v2`), `cluster_label` (HDBSCAN; `-1` noise, `-2` added after the cluster solution), 2-D UMAP coords | 4,946 | 2026-08-28 | Derived; clusters fit on the 2026-05-23 corpus only |
| `mini_themes.parquet` | One LLM-written "latent user assumption" per HDBSCAN cluster (B1) | 43 | 2026-05-23 | Derived (Claude Sonnet 4.6) |
| `anchor_themes.parquet` | The 13 consolidated anchor themes with their source clusters (B1.5) | 13 | 2026-05-23 | Derived (Claude Sonnet 4.6) |
| `derivations.parquet` | Candidate themes from the bottom-up, top-down and independent (GPT-5.5) derivations, for triangulation | 33 | 2026-05-23 | Derived |
| `independent_derivation.json` | The GPT-5.5 top-down derivation, frozen for reproducibility | 1 | 2026-05-23 | Derived (`codex exec`) |
| `codes.parquet` | Entry → anchor theme(s) assignment; `Maintenance / no conceptual shift` for the residual | 4,946 | 2026-08-28 | Derived (Claude Sonnet 4.6; post-May rows via `cmm.refresh`) |
| `themes.parquet` | Final theme table: description, `entry_count`, `first_seen_date`, `supporting_blog_urls`, examples, corroboration booleans, `confidence_tier`, `evidence_tier` | 13 | 2026-08-28 | Derived |
| `coherence.parquet` | Per theme: spread over clusters, top cluster and its share (`coherence_score`) | 13 | 2026-05-23 | Derived; frozen at the cluster solution |
| `persona_relevance.parquet` | 4 personas × 13 themes: relevance and a one-sentence mental-model statement | 52 | 2026-05-27 | Derived (Claude Sonnet 4.6) |
| `refresh_report.json` | The 2026-08-29 incremental-refresh probe: new items, residual, per-theme share, trigger evaluation | – | 2026-08-29 | Derived |
| `residual_analysis.json`, `coding_audit.json`, `run_metrics.json` | Summary statistics for the residual, the coding run, and the corpus | – | 2026-08-29 | Derived |
| `audit_sample.csv` | 40-row stratified sample for manual agreement audit (`agree` column blank until filled) | 40 | 2026-05-23 | Derived |

## Provenance and licensing

**Upstream text stays under its owner's terms.** The `text` column of
`changelog.parquet` reproduces Anthropic's `CHANGELOG.md` from
[anthropics/claude-code](https://github.com/anthropics/claude-code) for
analysis, with attribution; it is not relicensed here and remains subject to
Anthropic's terms for that repository. `blogs.parquet` holds titles, dates,
links and short excerpts of anthropic.com posts, not full articles; the
canonical text is at the linked URLs. Nothing in this directory should be
read as granting rights to Anthropic's content.

**Derived files are CC BY 4.0.** The analytical outputs listed above as
"Derived" (`codes.parquet`, `themes.parquet`, `anchor_themes.parquet`,
`joins.parquet`, `persona_relevance.parquet`, `coherence.parquet`,
`mini_themes.parquet`, `derivations.parquet`, `refresh_report.json` and the
other JSON summaries, `embeddings.parquet` minus the upstream `text` column)
are released under the
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
license. The code that produces them is MIT (root `LICENSE`).

**Suggested citation**

> Sachdev, V. (2026). *Claude Code mental models: a triangulated,
> persona-aware analysis of 17 months of releases* (data, v2.1.251
> snapshot, 2026-08-29). https://github.com/vishalsachdev/claude-mental-models

```bibtex
@misc{sachdev2026claudementalmodels,
  author = {Sachdev, Vishal},
  title  = {Claude Code mental models: a triangulated, persona-aware analysis of 17 months of releases},
  year   = {2026},
  note   = {Dataset and code, snapshot 2026-08-29 (Claude Code v2.1.251)},
  url    = {https://github.com/vishalsachdev/claude-mental-models}
}
```

**Caveats a reuser should know.** Theme names and assignments are
LLM-generated (triangulated across Claude Sonnet 4.6 and GPT-5.5, with a
per-theme coherence score; median 0.30). Versions must be compared with
`cmm.collect_changelog.version_key`, never as strings. The 2025-04-02
floor is when upstream first committed its changelog (17 versions in one
batch), not a clone artifact.
