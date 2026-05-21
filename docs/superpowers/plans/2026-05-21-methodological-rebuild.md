# Methodological Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single top-down theme pass with a triangulated, evidence-derived theme layer, on a corpus with fixed dates and stronger embeddings, presented honestly.

**Architecture:** Three groups run in order. Group A fixes the inputs (full-depth changelog, headless-rendered blogs, stronger embeddings + re-clustering). Group B builds three independent theme derivations (bottom-up from clusters, the existing top-down pass, and a GPT-5.5 pass via `codex exec`), then anchors triangulation on the bottom-up set. Group C reconciles clusters↔themes into a first-class output, updates the notebook, and downgrades claim wording. Each new stage writes its own Parquet artifact so stages are independently inspectable.

**Tech Stack:** Python 3.13 (`uv`), polars, sentence-transformers, hdbscan, umap-learn, marimo. LLM calls: headless `claude` CLI (`src/cmm/llm.py`) for Claude derivations; headless `codex exec` (new `src/cmm/codex_llm.py`) for the GPT-5.5 derivation. All calls cached in `data/cache/`.

**Spec:** `docs/superpowers/specs/2026-05-21-analysis-improvement-design.md`

---

## Artifacts (schemas — referenced by every task)

New / changed Parquet files under `data/processed/`:

| File | Producer | Columns |
|------|----------|---------|
| `changelog.parquet` | A1 (unchanged schema) | `id, version, text, change_type, date` |
| `blogs.parquet` | A2 (unchanged schema) | `url, title, date, body, cc_relevant, cc_confidence` |
| `embeddings.parquet` | A3 (unchanged schema) | `entry_id, text, source, date, version, cluster_label, umap_x, umap_y, vector` |
| `mini_themes.parquet` | B1 | `cluster_label (int), mini_theme (str), description (str)` |
| `derivations.parquet` | B1.5 + B2 + B3 | `derivation (str: "bottom_up"\|"top_down"\|"independent"), theme_name (str), description (str)` |
| `themes.parquet` | B4→B7 (final) | `name, description, entry_count, first_seen_date, supporting_blog_urls, example_entries, corroborated_top_down (bool), corroborated_independent (bool), confidence_tier (str), evidence_tier (str), source_clusters (list[int])` |
| `codes.parquet` | B4 (re-assigned) | `entry_id, source, date, themes (list[str])` |
| `coherence.parquet` | C1 | `theme (str), cluster_spread (int), top_cluster (int), top_cluster_share (float), coherence_score (float)` |
| `audit_sample.csv` | C4 | `entry_id, text, stratum, assigned_themes, top_cluster, agree (blank)` |

`confidence_tier` ∈ `{high, provisional, bottom_up_only}`. `evidence_tier` ∈ `{core, minor}`.

The canonical theme set is the **bottom-up consolidated set** (B1.5). `themes.parquet` carries exactly those theme rows; B2 and B3 themes live only in `derivations.parquet` as corroboration sources.

---

## Group A — Corpus & representation

### Task 1: A1 — Full-depth changelog history

**Files:**
- Modify: `src/cmm/collect_changelog.py:62-69` (`clone_or_update_repo`)
- Modify: `src/cmm/collect_changelog.py:96-114` (`collect` — add horizon assertion)
- Test: `tests/test_collect_changelog.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_collect_changelog.py`:

```python
from cmm.collect_changelog import assert_no_horizon_clamp


def test_assert_no_horizon_clamp_passes_when_first_date_is_distinct():
    # earliest version dated well after the others -> not clamped
    dates = {"0.2.1": "2025-02-24", "0.2.2": "2025-02-25", "1.0.0": "2025-05-22"}
    assert_no_horizon_clamp(dates)  # should not raise


def test_assert_no_horizon_clamp_raises_when_many_versions_share_oldest_date():
    # >1 version stamped with the identical oldest date == clone-horizon clamp
    dates = {"0.2.1": "2025-02-24", "0.2.2": "2025-02-24",
             "0.2.3": "2025-02-24", "1.0.0": "2025-05-22"}
    import pytest
    with pytest.raises(ValueError, match="clone horizon"):
        assert_no_horizon_clamp(dates)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_collect_changelog.py -k horizon -v`
Expected: FAIL — `ImportError: cannot import name 'assert_no_horizon_clamp'`

- [ ] **Step 3: Implement**

In `src/cmm/collect_changelog.py`, change the clone command (remove `--depth 1000`):

```python
def clone_or_update_repo(dest: Path) -> Path:
    """Clone anthropics/claude-code (full history) or fetch if already present.

    Full history (no --depth) is required: a shallow clone clamps the oldest
    versions' git dates to the clone horizon (fixes P8).
    """
    dest = Path(dest)
    if (dest / ".git").exists():
        subprocess.run(["git", "-C", str(dest), "fetch", "--all"], check=True)
    else:
        subprocess.run(["git", "clone", REPO_URL, str(dest)], check=True)
    return dest
```

Add the assertion function near `version_dates`:

```python
def assert_no_horizon_clamp(dates: dict[str, str]) -> None:
    """Raise if >1 version shares the oldest date (a shallow-clone artifact).

    With full history every version heading was added in its own commit, so
    the oldest date should belong to exactly one version.
    """
    if not dates:
        return
    oldest = min(dates.values())
    clamped = sorted(v for v, d in dates.items() if d == oldest)
    if len(clamped) > 1:
        raise ValueError(
            f"{len(clamped)} versions share the oldest date {oldest} "
            f"({clamped}) — likely clamped to the clone horizon. "
            "Re-clone with full history.")
```

In `collect`, call it right after `dates = version_dates(repo)`:

```python
    dates = version_dates(repo)
    assert_no_horizon_clamp(dates)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_collect_changelog.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Re-run the collector and verify the corpus**

Run:
```bash
rm -rf data/raw/claude-code
uv run python -m cmm.collect_changelog
```
Expected: prints `Wrote N changelog entries`, no `ValueError`. Confirm the new earliest date predates the old one:
```bash
uv run python -c "import polars as pl; d=pl.read_parquet('data/processed/changelog.parquet'); print(d['date'].min(), d['date'].max(), d.height)"
```
Expected: min date is on/before 2025-02-24 and is not shared by many versions.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/collect_changelog.py tests/test_collect_changelog.py data/processed/changelog.parquet
git commit -m "fix(A1): full-depth changelog clone + clone-horizon assertion"
```

---

### Task 2: A2 — Headless-rendered blog corpus

**Files:**
- Create: `src/cmm/render_blogs.py`
- Modify: `src/cmm/collect_blogs.py:82-111` (`collect` — use rendered HTML for post bodies)
- Test: `tests/test_render_blogs.py`

**Context:** `collect_blogs.py` already crawls index pages and extracts posts with `extract_post` (regex over HTML). The index crawl is fine. The problem is post *bodies* and *dates*: anthropic.com post pages are a JS SPA, so `httpx` gets a shell. A2 renders each post URL in a headless browser and feeds the rendered HTML to the existing `extract_post`. **Timeboxed: one render pass per URL, accept whatever dates come back.**

The render uses the `agent-browser` CLI (available in this environment). It exposes `agent-browser navigate <url>` and `agent-browser get-html`. The wrapper shells out to it, mirroring the `claude` CLI pattern in `llm.py`, and caches each rendered page.

- [ ] **Step 1: Write the failing test**

Create `tests/test_render_blogs.py`:

```python
from cmm.render_blogs import merge_rendered


def test_merge_rendered_prefers_rendered_date_and_body():
    static = {"url": "/news/x", "title": "X", "date": None, "body": "shell"}
    rendered = {"title": "X", "date": "2025-06-01", "body": "full rendered body"}
    merged = merge_rendered(static, rendered)
    assert merged["date"] == "2025-06-01"
    assert merged["body"] == "full rendered body"
    assert merged["url"] == "/news/x"


def test_merge_rendered_keeps_static_when_rendered_field_empty():
    static = {"url": "/news/x", "title": "X", "date": "2025-05-01", "body": "ok body"}
    rendered = {"title": "", "date": None, "body": ""}
    merged = merge_rendered(static, rendered)
    assert merged["date"] == "2025-05-01"
    assert merged["body"] == "ok body"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_render_blogs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.render_blogs'`

- [ ] **Step 3: Implement `render_blogs.py`**

Create `src/cmm/render_blogs.py`:

```python
# src/cmm/render_blogs.py
"""Headless-browser render of blog post pages (A2).

anthropic.com posts are a JS SPA; the static httpx body is a shell. This
renders each post URL once via the agent-browser CLI and re-extracts the
title/date/body with collect_blogs.extract_post. Timeboxed: one pass, no retry.
"""
import subprocess

from cmm.cache import cached_call
from cmm.collect_blogs import extract_post

_RENDER_TIMEOUT = 60  # seconds; one shot, no retry per the spec's timebox


def render_html(url: str) -> str:
    """Return fully-rendered HTML for `url` via agent-browser. Cached.

    On any failure returns "" — the caller falls back to the static body.
    """
    def run() -> str:
        try:
            proc = subprocess.run(
                ["agent-browser", "render", "--url", url, "--wait", "networkidle"],
                capture_output=True, text=True, timeout=_RENDER_TIMEOUT,
            )
            return proc.stdout if proc.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    return cached_call(f"render::{url}", run)


def merge_rendered(static: dict, rendered: dict) -> dict:
    """Overlay rendered title/date/body onto the static post, field by field.

    A rendered field wins only if it is non-empty; otherwise the static value
    is kept. `url` always comes from `static`.
    """
    out = dict(static)
    for field in ("title", "date", "body"):
        val = rendered.get(field)
        if val:
            out[field] = val
    return out


def render_post(static_post: dict) -> dict:
    """Render one post URL and merge the result over the static post dict."""
    html = render_html(static_post["url"])
    if not html:
        return static_post
    return merge_rendered(static_post, extract_post(html))
```

> **Note for the implementer:** confirm the exact `agent-browser` subcommand and flags by running `agent-browser --help` first. The command above (`render --url <u> --wait networkidle`, HTML to stdout) is the expected shape; adjust the argv list if the CLI differs, but keep the contract: takes a URL, returns rendered HTML on stdout, exit 0 on success. Do not add retries — the spec timeboxes this.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_render_blogs.py -v`
Expected: PASS

- [ ] **Step 5: Wire rendering into `collect`**

In `src/cmm/collect_blogs.py`, add the import at the top:

```python
from cmm.render_blogs import render_post
```

In `collect`, after `post["url"] = url` and before `posts.append(post)`, render it:

```python
            post = extract_post(html)
            post["url"] = url
            post = render_post(post)  # A2: overlay headless-rendered date/body
            posts.append(post)
```

- [ ] **Step 6: Re-run the blog collector and verify date recovery**

Run:
```bash
uv run python -m cmm.collect_blogs
uv run python -m cmm.tag_and_join
```
Expected: the `WARNING: N posts have no parsed date` line reports fewer undated posts than the v1 baseline of 14. Record the new number — that recovery figure goes into `docs/methodology.md` in Task 14.

Verify:
```bash
uv run python -c "import polars as pl; b=pl.read_parquet('data/processed/blogs.parquet'); print('posts',b.height,'undated',b['date'].null_count())"
```

- [ ] **Step 7: Commit**

```bash
git add src/cmm/render_blogs.py src/cmm/collect_blogs.py tests/test_render_blogs.py data/processed/blogs.parquet data/processed/joins.parquet
git commit -m "feat(A2): headless-render blog posts to recover dates and full bodies"
```

---

### Task 3: A3 — Stronger embeddings + re-clustering

**Files:**
- Modify: `src/cmm/embed_cluster.py:10` (`EMBED_MODEL`)
- Modify: `src/cmm/embed_cluster.py:37-39` (UMAP components + HDBSCAN params)

**Context:** No test — embedding quality is judged by hand-inspection, not assertion. This task swaps the model, loosens the UMAP reduction, and re-clusters.

- [ ] **Step 1: Change the embedding model and clustering params**

In `src/cmm/embed_cluster.py`, line 10:

```python
EMBED_MODEL = "all-mpnet-base-v2"  # higher-capacity than MiniLM (fixes P7)
```

Replace lines 37-39 (the cluster block) with:

```python
    # HDBSCAN clusters poorly in 768-d; reduce first — but less aggressively
    # than v1's 5-D, which risked lexical (not semantic) collisions.
    reduced = umap.UMAP(n_components=12, random_state=42).fit_transform(vectors)
    labels = hdbscan.HDBSCAN(min_cluster_size=15, min_samples=5).fit_predict(reduced)
```

- [ ] **Step 2: Re-run the embedding stage**

Run:
```bash
uv run python -m cmm.embed_cluster
```
Expected: prints `Embedded N items into M clusters`. Record M (the new cluster count) — B1 generates one mini-theme per cluster.

- [ ] **Step 3: Hand-inspect 5 clusters for semantic coherence**

Run:
```bash
uv run python -c "
import polars as pl
e = pl.read_parquet('data/processed/embeddings.parquet')
for c in sorted(e['cluster_label'].unique())[:6]:
    if c == -1: continue
    rows = e.filter(pl.col('cluster_label')==c)['text'].to_list()[:6]
    print(f'--- cluster {c} ({len(rows)} shown) ---')
    for t in rows: print('  ', t[:90])
"
```
Expected: read the output. Each cluster's entries should share a *topic* (e.g. all about MCP, all about permissions), not just a surface word. If clusters look lexical/incoherent, tune `min_cluster_size` (try 10 or 20) and re-run Step 2. Stop after one tuning round — record the chosen params in the commit message.

- [ ] **Step 4: Commit**

```bash
git add src/cmm/embed_cluster.py data/processed/embeddings.parquet
git commit -m "feat(A3): all-mpnet-base-v2 embeddings + 12-D UMAP re-clustering"
```

---

## Group B — Triangulated theme layer

### Task 4: B-infra — `codex exec` LLM wrapper

**Files:**
- Create: `src/cmm/codex_llm.py`
- Test: `tests/test_codex_llm.py`

**Context:** B3 needs GPT-5.5 to do theme discovery + assignment. This wrapper parallels `llm.py` but shells out to `codex exec`. Codex is agentic and prints prose around any JSON, so the wrapper reuses a strict JSON extractor and caches every call. **The CLI gotcha from the global CLAUDE.md applies: never pipe codex output through `tail`.**

- [ ] **Step 1: Write the failing test**

Create `tests/test_codex_llm.py`:

```python
import pytest
from cmm.codex_llm import extract_json


def test_extract_json_plain():
    assert extract_json('{"themes": [1, 2]}') == {"themes": [1, 2]}


def test_extract_json_with_fence_and_prose():
    raw = 'Here is the result:\n```json\n{"a": 1}\n```\nDone.'
    assert extract_json(raw) == {"a": 1}


def test_extract_json_embedded_array():
    assert extract_json('prose [{"x": 1}] trailing') == [{"x": 1}]


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError, match="no JSON"):
        extract_json("there is nothing parseable here")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_codex_llm.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.codex_llm'`

- [ ] **Step 3: Implement `codex_llm.py`**

Create `src/cmm/codex_llm.py`:

```python
# src/cmm/codex_llm.py
"""Cached LLM wrapper that shells out to the local `codex exec` CLI.

Used only for the B3 independent derivation (GPT-5.5). Codex is an agentic
CLI, not a JSON endpoint, so responses are parsed leniently and every call is
cached — the cached output is committed so B3 never re-runs nondeterministically.
"""
import json
import re
import subprocess
import time

from cmm.cache import cached_call

MODEL = "gpt-5.5"          # pinned: the independent derivation's model
_TIMEOUT = 600             # codex can be slow; generous one-shot timeout
_MAX_RETRIES = 3


def extract_json(text: str):
    """Parse JSON from a codex response, tolerating fences and surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"no JSON found in codex response: {text[:200]!r}")


def complete_json(prompt: str, system: str = "", max_tokens: int = 2000):
    """Run `codex exec` with the given prompt; return parsed JSON. Cached.

    `max_tokens` only varies the cache key. The prompt is prefixed with the
    system instruction and an explicit JSON-only directive because codex has
    no separate system-prompt flag.
    """
    system = system or "You are a precise qualitative-research assistant."
    full = (f"{system}\n\n{prompt}\n\n"
            "Respond with valid JSON only. Do not run tools, do not read or "
            "modify files, do not print anything except the JSON object.")
    key = "codex::" + json.dumps({"p": full, "m": MODEL, "t": max_tokens})

    def run():
        last_err = ""
        for attempt in range(_MAX_RETRIES):
            try:
                proc = subprocess.run(
                    ["codex", "exec", "--sandbox", "read-only",
                     "--model", MODEL, full],
                    capture_output=True, text=True, timeout=_TIMEOUT,
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"rc={proc.returncode}: {proc.stderr.strip()}")
                return extract_json(proc.stdout)
            except (RuntimeError, ValueError, json.JSONDecodeError,
                    subprocess.TimeoutExpired) as exc:
                last_err = str(exc)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"codex exec failed after {_MAX_RETRIES}: {last_err}")

    return cached_call(key, run)
```

> **Note for the implementer:** verify the `codex exec` invocation with `codex exec --help` before relying on it. The flags `--sandbox read-only` and `--model` are expected to exist; the prompt is passed as the trailing positional argument. Never pipe codex output through `tail` (global CLAUDE.md gotcha). If `codex` is not installed or unauthenticated, stop and surface that to the user — B3 cannot proceed without it.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_codex_llm.py -v`
Expected: PASS

- [ ] **Step 5: Smoke-test the live wrapper**

Run:
```bash
uv run python -c "
from cmm.codex_llm import complete_json
print(complete_json('Return the JSON object {\"ok\": true}.'))
"
```
Expected: prints `{'ok': True}`. If codex errors, resolve auth/install before continuing — every later B3 step depends on this.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/codex_llm.py tests/test_codex_llm.py
git commit -m "feat(B3-infra): cached codex exec wrapper for the GPT-5.5 derivation"
```

---

### Task 5: B1 — Bottom-up mini-themes from clusters

**Files:**
- Create: `src/cmm/theme_derivations.py`
- Test: `tests/test_theme_derivations.py`

**Context:** For each HDBSCAN cluster (excluding noise label `-1`), send the LLM a sample of that cluster's member entries and ask for the single latent user assumption they share. One mini-theme per cluster.

- [ ] **Step 1: Write the failing test**

Create `tests/test_theme_derivations.py`:

```python
import polars as pl
from cmm.theme_derivations import cluster_samples


def test_cluster_samples_excludes_noise_and_caps_sample():
    df = pl.DataFrame({
        "entry_id": [str(i) for i in range(25)],
        "text": [f"entry {i}" for i in range(25)],
        "cluster_label": [-1] * 5 + [0] * 12 + [1] * 8,
    })
    samples = cluster_samples(df, sample_size=10)
    assert set(samples) == {0, 1}                 # noise cluster -1 dropped
    assert len(samples[0]) == 10                  # capped at sample_size
    assert len(samples[1]) == 8                   # smaller cluster kept whole
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_theme_derivations.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.theme_derivations'`

- [ ] **Step 3: Implement B1 in `theme_derivations.py`**

Create `src/cmm/theme_derivations.py`:

```python
# src/cmm/theme_derivations.py
"""The three theme derivations (B1 bottom-up, B1.5 consolidation, B3 independent).

B2 (top-down) reuses cmm.thematic_coding.discover_themes unchanged.
"""
import concurrent.futures
from pathlib import Path

import polars as pl

from cmm.llm import complete_json as claude_json

MINI_SYSTEM = (
    "You are a qualitative researcher. You are given a cluster of Claude Code "
    "release items that an embedding model grouped together. State the single "
    "latent user assumption or competency these items share -- the conceptual "
    "thing a user had to internalize. Return JSON "
    '{"mini_theme": "<=6 words", "description": "one sentence"}.'
)


def cluster_samples(embeddings: pl.DataFrame, sample_size: int = 15
                    ) -> dict[int, list[str]]:
    """Return {cluster_label: [entry texts]} for every non-noise cluster.

    Each cluster is capped at `sample_size` texts (evenly indexed).
    """
    out: dict[int, list[str]] = {}
    for c in sorted(embeddings["cluster_label"].unique()):
        if c == -1:
            continue
        texts = embeddings.filter(pl.col("cluster_label") == c)["text"].to_list()
        if len(texts) > sample_size:
            step = len(texts) / sample_size
            texts = [texts[int(i * step)] for i in range(sample_size)]
        out[int(c)] = texts
    return out


def _mini_theme(cluster: int, texts: list[str]) -> dict:
    """One LLM call -> the mini-theme for one cluster."""
    listing = "\n".join(f"- {t[:200]}" for t in texts)
    r = claude_json(f"Cluster {cluster} items:\n{listing}",
                    system=MINI_SYSTEM, max_tokens=400)
    return {"cluster_label": cluster, "mini_theme": r["mini_theme"],
            "description": r["description"]}


def bottom_up_mini_themes(embeddings: pl.DataFrame, max_workers: int = 8
                          ) -> pl.DataFrame:
    """B1: one mini-theme per non-noise cluster, in parallel.

    Returns columns: cluster_label, mini_theme, description.
    """
    samples = cluster_samples(embeddings)
    rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_mini_theme, c, t): c for c, t in samples.items()}
        for fut in concurrent.futures.as_completed(futs):
            rows.append(fut.result())
    return pl.DataFrame(rows).sort("cluster_label")


def run_b1(embeddings: Path = Path("data/processed/embeddings.parquet"),
           out: Path = Path("data/processed/mini_themes.parquet")) -> None:
    emb = pl.read_parquet(embeddings)
    mini = bottom_up_mini_themes(emb)
    mini.write_parquet(out)
    print(f"B1: {mini.height} mini-themes from clusters")


if __name__ == "__main__":
    run_b1()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_theme_derivations.py -v`
Expected: PASS

- [ ] **Step 5: Run B1 and inspect**

Run:
```bash
uv run python -c "from cmm.theme_derivations import run_b1; run_b1()"
uv run python -c "import polars as pl; print(pl.read_parquet('data/processed/mini_themes.parquet'))"
```
Expected: one row per non-noise cluster; each `mini_theme` is a short phrase, each `description` a sentence.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/theme_derivations.py tests/test_theme_derivations.py data/processed/mini_themes.parquet
git commit -m "feat(B1): bottom-up mini-themes, one per embedding cluster"
```

---

### Task 6: B1.5 — Consolidation pass (the canonical anchor set)

**Files:**
- Modify: `src/cmm/theme_derivations.py` (add consolidation)
- Test: `tests/test_theme_derivations.py` (append)

**Context:** B1 yields ~30–40 mini-themes — too granular to be the triangulation anchor. One LLM pass consolidates them into ~10–15 themes, each recording which clusters feed it. This consolidated set is canonical.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_theme_derivations.py`:

```python
from cmm.theme_derivations import validate_consolidation


def test_validate_consolidation_accepts_full_cluster_cover():
    mini = pl.DataFrame({"cluster_label": [0, 1, 2], "mini_theme": ["a", "b", "c"],
                         "description": ["", "", ""]})
    consolidated = [{"name": "T1", "description": "d", "source_clusters": [0, 1]},
                    {"name": "T2", "description": "d", "source_clusters": [2]}]
    validate_consolidation(consolidated, mini)  # every cluster covered -> ok


def test_validate_consolidation_rejects_missing_cluster():
    mini = pl.DataFrame({"cluster_label": [0, 1, 2], "mini_theme": ["a", "b", "c"],
                         "description": ["", "", ""]})
    consolidated = [{"name": "T1", "description": "d", "source_clusters": [0, 1]}]
    import pytest
    with pytest.raises(ValueError, match="cluster"):
        validate_consolidation(consolidated, mini)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_theme_derivations.py -k consolidation -v`
Expected: FAIL — `ImportError: cannot import name 'validate_consolidation'`

- [ ] **Step 3: Implement consolidation in `theme_derivations.py`**

Add to `src/cmm/theme_derivations.py`:

```python
CONSOLIDATE_SYSTEM = (
    "You are a qualitative researcher. You are given a list of fine-grained "
    "mini-themes (each tied to an embedding cluster id). Group them into "
    "10-15 consolidated themes -- coherent user competencies/expectations. "
    "Every cluster id must appear in exactly one theme's source_clusters. "
    'Return JSON {"themes": [{"name": "short", "description": "one sentence", '
    '"source_clusters": [int, ...]}]}.'
)


def validate_consolidation(consolidated: list[dict], mini: pl.DataFrame) -> None:
    """Raise unless every mini-theme cluster is covered exactly once."""
    all_clusters = set(mini["cluster_label"].to_list())
    seen: list[int] = []
    for t in consolidated:
        seen += t["source_clusters"]
    covered = set(seen)
    if covered != all_clusters:
        missing = sorted(all_clusters - covered)
        extra = sorted(covered - all_clusters)
        raise ValueError(f"cluster cover mismatch: missing={missing} extra={extra}")
    if len(seen) != len(covered):
        raise ValueError(f"cluster assigned to >1 theme: {sorted(seen)}")


def consolidate_mini_themes(mini: pl.DataFrame) -> pl.DataFrame:
    """B1.5: group mini-themes into the canonical 10-15 anchor themes.

    Returns columns: name, description, source_clusters (list[int]).
    """
    listing = "\n".join(
        f"- cluster {r['cluster_label']}: {r['mini_theme']} — {r['description']}"
        for r in mini.iter_rows(named=True))
    r = claude_json(f"Mini-themes:\n{listing}",
                    system=CONSOLIDATE_SYSTEM, max_tokens=3000)
    consolidated = r["themes"]
    validate_consolidation(consolidated, mini)
    return pl.DataFrame(consolidated,
                        schema_overrides={"source_clusters": pl.List(pl.Int64)})
```

> If `validate_consolidation` raises, the LLM dropped or double-assigned a cluster. `claude_json` already retries with a JSON nudge; for a cover error, re-run `run_b15` once (a fresh call). If it still fails, surface to the user — do not silently patch the cover.

Add a runner:

```python
def run_b15(mini_path: Path = Path("data/processed/mini_themes.parquet"),
            out: Path = Path("data/processed/derivations.parquet")) -> None:
    """Run B1.5 and write the bottom_up rows of derivations.parquet."""
    mini = pl.read_parquet(mini_path)
    anchor = consolidate_mini_themes(mini)
    rows = anchor.select(
        pl.lit("bottom_up").alias("derivation"),
        pl.col("name").alias("theme_name"),
        pl.col("description"),
    )
    rows.write_parquet(out)
    # source_clusters is needed later by C1; keep it in a sidecar parquet.
    anchor.write_parquet(Path("data/processed/anchor_themes.parquet"))
    print(f"B1.5: consolidated to {anchor.height} anchor themes")
```

> **Schema note:** `anchor_themes.parquet` (`name, description, source_clusters`) is an intermediate consumed by Task 8 (B4) and Task 12 (C1). It is added to the Artifacts set implicitly; commit it like the others.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_theme_derivations.py -k consolidation -v`
Expected: PASS

- [ ] **Step 5: Run B1.5 and inspect**

Run:
```bash
uv run python -c "from cmm.theme_derivations import run_b15; run_b15()"
uv run python -c "import polars as pl; print(pl.read_parquet('data/processed/anchor_themes.parquet'))"
```
Expected: 10–15 anchor themes, each with a non-empty `source_clusters` list; no `ValueError`.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/theme_derivations.py tests/test_theme_derivations.py data/processed/derivations.parquet data/processed/anchor_themes.parquet
git commit -m "feat(B1.5): consolidate mini-themes into the canonical anchor set"
```

---

### Task 7: B2 + B3 — Top-down and independent derivations

**Files:**
- Modify: `src/cmm/theme_derivations.py` (add B3 + the derivations runner)

**Context:** B2 reuses `cmm.thematic_coding.discover_themes` unchanged (the existing top-down pass). B3 re-runs theme discovery with GPT-5.5 via `codex_llm`. Both append their rows to `derivations.parquet` alongside the B1.5 `bottom_up` rows. No new pure logic → verification is by inspection.

- [ ] **Step 1: Implement B3 + the runner in `theme_derivations.py`**

Add to `src/cmm/theme_derivations.py`:

```python
from cmm.codex_llm import complete_json as codex_json
from cmm.thematic_coding import DISCOVER_SYSTEM, SAMPLE_SIZE


def independent_themes(items: pl.DataFrame) -> pl.DataFrame:
    """B3: top-down theme discovery run on GPT-5.5 via codex.

    Uses the SAME discovery prompt as B2 (cmm.thematic_coding.DISCOVER_SYSTEM)
    and the same stratified-sample construction, so the only variable is the
    model. Returns columns: name, description.
    """
    dated = items.filter(pl.col("date").is_not_null()).sort("date")
    n = dated.height
    if n > SAMPLE_SIZE:
        idx = [round(i * (n - 1) / (SAMPLE_SIZE - 1)) for i in range(SAMPLE_SIZE)]
        sample = dated[idx]
    else:
        sample = dated
    listing = "\n".join(f"- ({r['source']}, {r['date']}) {r['text'][:200]}"
                        for r in sample.iter_rows(named=True))
    r = codex_json(
        f"Sample of {sample.height} Claude Code release items, oldest first:\n"
        f"{listing}",
        system=DISCOVER_SYSTEM, max_tokens=2000)
    return pl.DataFrame(r["themes"])


def run_derivations(embeddings: Path = Path("data/processed/embeddings.parquet"),
                    out: Path = Path("data/processed/derivations.parquet")) -> None:
    """Append B2 (top_down) and B3 (independent) rows to derivations.parquet.

    Assumes run_b15 has already written the bottom_up rows.
    """
    from cmm.thematic_coding import discover_themes

    emb = pl.read_parquet(embeddings)
    items = emb.select("entry_id", "text", "source", "date")

    b2 = discover_themes(items).select(
        pl.lit("top_down").alias("derivation"),
        pl.col("name").alias("theme_name"), pl.col("description"))
    b3 = independent_themes(items).select(
        pl.lit("independent").alias("derivation"),
        pl.col("name").alias("theme_name"), pl.col("description"))

    existing = pl.read_parquet(out)  # bottom_up rows from run_b15
    combined = pl.concat([existing.filter(pl.col("derivation") == "bottom_up"),
                          b2, b3])
    combined.write_parquet(out)
    print(f"Derivations: bottom_up={existing.height} top_down={b2.height} "
          f"independent={b3.height}")
```

- [ ] **Step 2: Run B2 + B3 and inspect**

Run:
```bash
uv run python -c "from cmm.theme_derivations import run_derivations; run_derivations()"
uv run python -c "
import polars as pl
d = pl.read_parquet('data/processed/derivations.parquet')
for grp in ['bottom_up','top_down','independent']:
    print('===', grp, '==='); print(d.filter(pl.col('derivation')==grp))
"
```
Expected: three derivation groups present. `bottom_up` has 10–15 rows; `top_down` and `independent` each have ~6–10. Eyeball that `independent` themes are recognizably about Claude Code (sanity-check the codex output is real).

- [ ] **Step 3: Commit**

```bash
git add src/cmm/theme_derivations.py data/processed/derivations.parquet
git commit -m "feat(B2/B3): top-down + GPT-5.5 independent theme derivations"
```

---

### Task 8: B4 — Anchored triangulation + confidence tiers

**Files:**
- Create: `src/cmm/triangulate.py`
- Test: `tests/test_triangulate.py`

**Context:** For each anchor theme (B1.5), the independent model judges: is it corroborated by a top-down theme? by an independent theme? The two booleans set `confidence_tier`. Then every corpus entry is re-assigned to the final anchor theme set via the existing `assign_themes`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_triangulate.py`:

```python
import pytest
from cmm.triangulate import confidence_tier


def test_confidence_tier_high_when_both_corroborate():
    assert confidence_tier(True, True) == "high"


def test_confidence_tier_provisional_when_one_corroborates():
    assert confidence_tier(True, False) == "provisional"
    assert confidence_tier(False, True) == "provisional"


def test_confidence_tier_bottom_up_only_when_neither():
    assert confidence_tier(False, False) == "bottom_up_only"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_triangulate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.triangulate'`

- [ ] **Step 3: Implement B4 in `triangulate.py`**

Create `src/cmm/triangulate.py`:

```python
# src/cmm/triangulate.py
"""B4-B7: anchored triangulation, descriptions, unassigned handling, tiering.

The anchor theme set (B1.5) is canonical. B2/B3 themes corroborate it; they
never add or rename anchor themes.
"""
import json
from pathlib import Path

import polars as pl

from cmm.codex_llm import complete_json as codex_json
from cmm.thematic_coding import assign_themes

CORROBORATE_SYSTEM = (
    "You are an independent reviewer. You are given one ANCHOR theme and a "
    "list of CANDIDATE themes from another analysis. Decide whether any "
    "candidate expresses substantially the same user competency/expectation "
    "as the anchor (same concept, wording may differ). Return JSON "
    '{"corroborated": bool, "match": "<candidate name or empty>", '
    '"rationale": "one sentence"}.'
)


def confidence_tier(corr_top_down: bool, corr_independent: bool) -> str:
    """Map the two corroboration booleans to a confidence tier."""
    if corr_top_down and corr_independent:
        return "high"
    if corr_top_down or corr_independent:
        return "provisional"
    return "bottom_up_only"


def _corroborates(anchor: dict, candidates: pl.DataFrame) -> dict:
    """Ask the independent model whether `candidates` corroborate `anchor`."""
    listing = "\n".join(f"- {r['theme_name']}: {r['description']}"
                        for r in candidates.iter_rows(named=True))
    return codex_json(
        f"ANCHOR theme:\n{anchor['name']}: {anchor['description']}\n\n"
        f"CANDIDATE themes:\n{listing}",
        system=CORROBORATE_SYSTEM, max_tokens=400)


def triangulate(anchor: pl.DataFrame, derivations: pl.DataFrame) -> pl.DataFrame:
    """B4: tag each anchor theme with corroboration booleans + confidence tier.

    `anchor` has columns name, description, source_clusters.
    Returns anchor + corroborated_top_down, corroborated_independent,
    confidence_tier, corroboration_notes.
    """
    top_down = derivations.filter(pl.col("derivation") == "top_down")
    independent = derivations.filter(pl.col("derivation") == "independent")
    rows = []
    for a in anchor.iter_rows(named=True):
        td = _corroborates(a, top_down)
        ind = _corroborates(a, independent)
        rows.append({
            **a,
            "corroborated_top_down": bool(td["corroborated"]),
            "corroborated_independent": bool(ind["corroborated"]),
            "confidence_tier": confidence_tier(bool(td["corroborated"]),
                                               bool(ind["corroborated"])),
            "corroboration_notes": json.dumps({"top_down": td, "independent": ind}),
        })
    return pl.DataFrame(rows, schema_overrides={"source_clusters": pl.List(pl.Int64)})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_triangulate.py -v`
Expected: PASS

- [ ] **Step 5: Add the assignment step**

Add to `src/cmm/triangulate.py`:

```python
def assign_to_anchor(anchor: pl.DataFrame, embeddings: pl.DataFrame) -> pl.DataFrame:
    """Re-assign every corpus entry to the final anchor theme set.

    Reuses cmm.thematic_coding.assign_themes (the existing batched assigner),
    feeding it the anchor themes as the theme list.
    """
    items = embeddings.select("entry_id", "text", "source", "date")
    theme_list = anchor.select(pl.col("name"), pl.col("description"))
    return assign_themes(items, theme_list)
```

- [ ] **Step 6: Run B4 end-to-end and inspect**

Run:
```bash
uv run python -c "
import polars as pl
from cmm.triangulate import triangulate, assign_to_anchor
anchor = pl.read_parquet('data/processed/anchor_themes.parquet')
deriv = pl.read_parquet('data/processed/derivations.parquet')
emb = pl.read_parquet('data/processed/embeddings.parquet')
tri = triangulate(anchor, deriv)
codes = assign_to_anchor(anchor, emb)
tri.write_parquet('data/processed/_b4_themes.parquet')
codes.write_parquet('data/processed/codes.parquet')
print(tri.select('name','confidence_tier','corroborated_top_down','corroborated_independent'))
print('unassigned:', codes.filter(pl.col('themes').list.len()==0).height, '/', codes.height)
"
```
Expected: every anchor theme has a `confidence_tier`; a mix of `high`/`provisional`/`bottom_up_only`. `_b4_themes.parquet` is an intermediate consumed by Task 9.

- [ ] **Step 7: Commit**

```bash
git add src/cmm/triangulate.py tests/test_triangulate.py data/processed/codes.parquet data/processed/_b4_themes.parquet
git commit -m "feat(B4): anchored triangulation + confidence tiers + re-assignment"
```

---

### Task 9: B5 — Descriptions from member entries + extractive check

**Files:**
- Modify: `src/cmm/triangulate.py` (add description regeneration)
- Test: `tests/test_triangulate.py` (append)

**Context:** Regenerate each final theme's description from a sample of its *actually assigned* entries. Then an extractive check: every salient word the LLM names must appear in ≥1 assigned entry, else flag the description.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_triangulate.py`:

```python
from cmm.triangulate import extractive_violations


def test_extractive_violations_none_when_all_words_grounded():
    desc = "Users learned to manage context windows"
    member_texts = ["Added context window compaction", "manage long sessions"]
    assert extractive_violations(desc, member_texts) == []


def test_extractive_violations_flags_ungrounded_salient_word():
    desc = "Users adopted quantum telepathy for delegation"
    member_texts = ["Added subagent delegation support"]
    viol = extractive_violations(desc, member_texts)
    assert "quantum" in viol and "telepathy" in viol
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_triangulate.py -k extractive -v`
Expected: FAIL — `ImportError: cannot import name 'extractive_violations'`

- [ ] **Step 3: Implement B5 in `triangulate.py`**

Add to `src/cmm/triangulate.py`:

```python
from cmm.llm import complete_json as claude_json

DESCRIBE_SYSTEM = (
    "You are a qualitative researcher. Given a theme name and a sample of the "
    "release items ACTUALLY assigned to it, write a one-sentence description "
    "of the user competency/expectation the theme captures. Use only what the "
    'items evidence. Return JSON {"description": "one sentence"}.'
)

_STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
         "users", "user", "learned", "adopted", "had", "this", "that", "as",
         "is", "are", "was", "were", "be", "by", "from", "their", "they"}


def extractive_violations(description: str, member_texts: list[str]) -> list[str]:
    """Return salient description words that appear in NO member text.

    Salient = length > 4, not a stopword. An empty list means the description
    is fully grounded in its assigned entries.
    """
    corpus = " ".join(member_texts).lower()
    words = {w.lower().strip(".,`'\"()") for w in description.split()}
    salient = {w for w in words if len(w) > 4 and w not in _STOP}
    return sorted(w for w in salient if w not in corpus)


def regenerate_descriptions(triangulated: pl.DataFrame, codes: pl.DataFrame,
                            embeddings: pl.DataFrame) -> pl.DataFrame:
    """B5: rewrite each theme description from its assigned entries.

    Adds `description` (regenerated) and `description_flags` (json list of
    ungrounded words, empty if clean).
    """
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    exploded = codes.explode("themes").drop_nulls("themes")
    rows = []
    for t in triangulated.iter_rows(named=True):
        members = exploded.filter(pl.col("themes") == t["name"])["entry_id"].to_list()
        member_texts = [text_by_id.get(e, "") for e in members]
        sample = member_texts[:25]
        listing = "\n".join(f"- {x[:200]}" for x in sample)
        r = claude_json(f"Theme: {t['name']}\nAssigned items:\n{listing}",
                        system=DESCRIBE_SYSTEM, max_tokens=300)
        new_desc = r["description"]
        flags = extractive_violations(new_desc, member_texts)
        rows.append({**t, "description": new_desc,
                     "description_flags": json.dumps(flags)})
    return pl.DataFrame(rows, schema_overrides={"source_clusters": pl.List(pl.Int64)})
```

> If a theme has zero assigned members, `regenerate_descriptions` would send an empty listing. Guard it: if `member_texts` is empty, keep the existing description and set `description_flags` to `json.dumps(["NO_MEMBERS"])`. Add that branch before the `claude_json` call.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_triangulate.py -k extractive -v`
Expected: PASS

- [ ] **Step 5: Run B5 and inspect flags**

Run:
```bash
uv run python -c "
import polars as pl
from cmm.triangulate import regenerate_descriptions
tri = pl.read_parquet('data/processed/_b4_themes.parquet')
codes = pl.read_parquet('data/processed/codes.parquet')
emb = pl.read_parquet('data/processed/embeddings.parquet')
out = regenerate_descriptions(tri, codes, emb)
out.write_parquet('data/processed/_b5_themes.parquet')
print(out.select('name','description','description_flags'))
"
```
Expected: each description rewritten; `description_flags` mostly `[]`. Any non-empty flag means the description still names an ungrounded feature — note it for the user (do not auto-fix).

- [ ] **Step 6: Commit**

```bash
git add src/cmm/triangulate.py tests/test_triangulate.py data/processed/_b5_themes.parquet
git commit -m "feat(B5): regenerate theme descriptions from member entries + extractive check"
```

---

### Task 10: B6 — Handle the unassigned residual

**Files:**
- Modify: `src/cmm/triangulate.py` (add residual analysis)
- Test: `tests/test_triangulate.py` (append)

**Context:** Entries assigned to no theme get an explicit `Maintenance / no conceptual shift` label, and the residual gets its own analysis (size + composition) written to a JSON the notebook reads.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_triangulate.py`:

```python
import polars as _pl
from cmm.triangulate import label_unassigned

MAINTENANCE = "Maintenance / no conceptual shift"


def test_label_unassigned_labels_empty_theme_lists():
    codes = _pl.DataFrame({
        "entry_id": ["a", "b", "c"],
        "source": ["changelog"] * 3,
        "date": ["2025-03-01"] * 3,
        "themes": [["T1"], [], []],
    })
    out = label_unassigned(codes)
    assert out.filter(_pl.col("entry_id") == "a")["themes"].item().to_list() == ["T1"]
    assert out.filter(_pl.col("entry_id") == "b")["themes"].item().to_list() == [MAINTENANCE]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_triangulate.py -k unassigned -v`
Expected: FAIL — `ImportError: cannot import name 'label_unassigned'`

- [ ] **Step 3: Implement B6 in `triangulate.py`**

Add to `src/cmm/triangulate.py`:

```python
MAINTENANCE_LABEL = "Maintenance / no conceptual shift"


def label_unassigned(codes: pl.DataFrame) -> pl.DataFrame:
    """Replace empty theme lists with the explicit Maintenance label."""
    return codes.with_columns(
        pl.when(pl.col("themes").list.len() == 0)
        .then(pl.lit([MAINTENANCE_LABEL]))
        .otherwise(pl.col("themes"))
        .alias("themes"))


def residual_analysis(codes_before_label: pl.DataFrame,
                      embeddings: pl.DataFrame) -> dict:
    """Summarise the unassigned residual: size, change-type mix, examples.

    `codes_before_label` is codes BEFORE label_unassigned ran (empty lists
    still empty). Returns a dict written to residual_analysis.json.
    """
    residual = codes_before_label.filter(pl.col("themes").list.len() == 0)
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    total = codes_before_label.height
    return {
        "residual_count": residual.height,
        "residual_fraction": round(residual.height / total, 3) if total else 0.0,
        "by_source": dict(residual.group_by("source").len()
                          .iter_rows()),
        "examples": [text_by_id.get(e, "")[:160]
                     for e in residual["entry_id"].to_list()[:12]],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_triangulate.py -k unassigned -v`
Expected: PASS

- [ ] **Step 5: Run B6 and inspect**

Run:
```bash
uv run python -c "
import json, polars as pl
from cmm.triangulate import label_unassigned, residual_analysis
codes = pl.read_parquet('data/processed/codes.parquet')
emb = pl.read_parquet('data/processed/embeddings.parquet')
analysis = residual_analysis(codes, emb)
json.dump(analysis, open('data/processed/residual_analysis.json','w'), indent=2)
label_unassigned(codes).write_parquet('data/processed/codes.parquet')
print(analysis['residual_count'], analysis['residual_fraction'])
"
```
Expected: prints the residual count and fraction; `residual_analysis.json` written.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/triangulate.py tests/test_triangulate.py data/processed/codes.parquet data/processed/residual_analysis.json
git commit -m "feat(B6): label unassigned residual + residual analysis output"
```

---

### Task 11: B7 — Theme tiering + final `themes.parquet`

**Files:**
- Modify: `src/cmm/triangulate.py` (add tiering + the `finalize` runner)
- Test: `tests/test_triangulate.py` (append)

**Context:** Tag each theme `core` or `minor` by evidence weight, enrich with `entry_count` / `first_seen_date` / blog support / examples (the v1 `finalize_themes` fields), and write the final `themes.parquet`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_triangulate.py`:

```python
from cmm.triangulate import evidence_tier


def test_evidence_tier_minor_below_threshold():
    # entry_count below 1.5% of corpus -> minor
    assert evidence_tier(entry_count=20, corpus_size=3000) == "minor"


def test_evidence_tier_core_above_threshold():
    assert evidence_tier(entry_count=200, corpus_size=3000) == "core"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_triangulate.py -k evidence_tier -v`
Expected: FAIL — `ImportError: cannot import name 'evidence_tier'`

- [ ] **Step 3: Implement B7 + finalize in `triangulate.py`**

Add to `src/cmm/triangulate.py`:

```python
def evidence_tier(entry_count: int, corpus_size: int,
                  min_share: float = 0.015) -> str:
    """`minor` if the theme covers < min_share of the corpus, else `core`."""
    if corpus_size == 0:
        return "minor"
    return "minor" if entry_count / corpus_size < min_share else "core"


def finalize_themes(b5_themes: pl.DataFrame, codes: pl.DataFrame,
                    embeddings: pl.DataFrame) -> pl.DataFrame:
    """B7: enrich + tier the triangulated themes into the final themes.parquet.

    `codes` here is post-B6 (Maintenance label applied). The Maintenance label
    is NOT a theme row — it is filtered out of the enrichment join.
    """
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    date_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["date"].to_list()))
    exploded = codes.explode("themes").drop_nulls("themes")
    corpus_size = codes.height
    rows = []
    for t in b5_themes.iter_rows(named=True):
        mem = exploded.filter(pl.col("themes") == t["name"])
        ids = mem["entry_id"].to_list()
        dates = [date_by_id.get(e) for e in ids if date_by_id.get(e)]
        blog_urls = sorted(e for e in ids if str(e).startswith("http"))
        rows.append({
            "name": t["name"],
            "description": t["description"],
            "description_flags": t["description_flags"],
            "entry_count": mem.height,
            "first_seen_date": min(dates) if dates else None,
            "supporting_blog_urls": blog_urls,
            "example_entries": [text_by_id.get(e, "")[:160] for e in ids[:3]],
            "corroborated_top_down": t["corroborated_top_down"],
            "corroborated_independent": t["corroborated_independent"],
            "confidence_tier": t["confidence_tier"],
            "corroboration_notes": t["corroboration_notes"],
            "source_clusters": t["source_clusters"],
            "evidence_tier": evidence_tier(mem.height, corpus_size),
        })
    return pl.DataFrame(rows, schema_overrides={
        "supporting_blog_urls": pl.List(pl.Utf8),
        "source_clusters": pl.List(pl.Int64),
    })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_triangulate.py -k evidence_tier -v`
Expected: PASS

- [ ] **Step 5: Add the full Group-B orchestrator**

Add to `src/cmm/triangulate.py`:

```python
def run(embeddings: Path = Path("data/processed/embeddings.parquet")) -> None:
    """B4-B7 end-to-end. Assumes mini_themes, anchor_themes, derivations exist.

    Run order upstream: theme_derivations.run_b1 -> run_b15 -> run_derivations.
    """
    emb = pl.read_parquet(embeddings)
    anchor = pl.read_parquet("data/processed/anchor_themes.parquet")
    deriv = pl.read_parquet("data/processed/derivations.parquet")

    tri = triangulate(anchor, deriv)                       # B4
    codes = assign_to_anchor(anchor, emb)                  # B4
    b5 = regenerate_descriptions(tri, codes, emb)          # B5

    residual = residual_analysis(codes, emb)               # B6
    json.dump(residual, open("data/processed/residual_analysis.json", "w"),
              indent=2)
    codes = label_unassigned(codes)                        # B6

    themes = finalize_themes(b5, codes, emb)               # B7
    codes.write_parquet("data/processed/codes.parquet")
    themes.write_parquet("data/processed/themes.parquet")

    audit = {
        "n_themes": themes.height,
        "n_entries": codes.height,
        "residual_count": residual["residual_count"],
        "residual_fraction": residual["residual_fraction"],
        "confidence_tiers": dict(themes.group_by("confidence_tier").len()
                                 .iter_rows()),
        "evidence_tiers": dict(themes.group_by("evidence_tier").len()
                               .iter_rows()),
    }
    json.dump(audit, open("data/processed/coding_audit.json", "w"), indent=2)
    print(f"Final: {themes.height} themes, "
          f"{residual['residual_count']} residual ({residual['residual_fraction']})")


if __name__ == "__main__":
    run()
```

> Delete the now-superseded intermediates after `run()` works: `_b4_themes.parquet`, `_b5_themes.parquet` were only step-by-step inspection aids. Remove them with `git rm` if they were committed.

- [ ] **Step 6: Run the full Group-B layer and verify**

Run:
```bash
uv run python -m cmm.triangulate
uv run python -c "
import polars as pl
t = pl.read_parquet('data/processed/themes.parquet')
print(t.select('name','entry_count','confidence_tier','evidence_tier','description_flags'))
"
git rm -q --cached data/processed/_b4_themes.parquet data/processed/_b5_themes.parquet 2>/dev/null; rm -f data/processed/_b4_themes.parquet data/processed/_b5_themes.parquet
```
Expected: `themes.parquet` has 10–15 rows, each with both tier columns and (mostly empty) `description_flags`.

- [ ] **Step 7: Commit**

```bash
git add src/cmm/triangulate.py tests/test_triangulate.py data/processed/themes.parquet data/processed/codes.parquet data/processed/coding_audit.json data/processed/residual_analysis.json
git commit -m "feat(B7): theme tiering + final themes.parquet via Group-B orchestrator"
```

---

## Group C — Reconciliation & honest presentation

### Task 12: C1 — Cluster↔theme coherence as a first-class output

**Files:**
- Create: `src/cmm/coherence.py`
- Test: `tests/test_coherence.py`

**Context:** Compute, per theme, how its assigned entries spread across embedding clusters. A theme whose entries concentrate in one cluster is coherent; one smeared across many is not. Write `coherence.parquet`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_coherence.py`:

```python
from cmm.coherence import coherence_row


def test_coherence_row_concentrated_theme_scores_high():
    # all 10 entries in one cluster -> spread 1, share 1.0, score 1.0
    row = coherence_row("T1", cluster_labels=[3] * 10)
    assert row["cluster_spread"] == 1
    assert row["top_cluster"] == 3
    assert row["top_cluster_share"] == 1.0
    assert row["coherence_score"] == 1.0


def test_coherence_row_smeared_theme_scores_low():
    # evenly across 5 clusters -> share 0.2
    row = coherence_row("T2", cluster_labels=[0, 1, 2, 3, 4] * 2)
    assert row["cluster_spread"] == 5
    assert row["top_cluster_share"] == 0.2
    assert row["coherence_score"] < 0.5


def test_coherence_row_ignores_noise_cluster():
    row = coherence_row("T3", cluster_labels=[-1, -1, 7, 7, 7])
    assert row["top_cluster"] == 7
    assert row["top_cluster_share"] == 1.0  # noise excluded from denominator
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_coherence.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.coherence'`

- [ ] **Step 3: Implement `coherence.py`**

Create `src/cmm/coherence.py`:

```python
# src/cmm/coherence.py
"""C1: cluster<->theme reconciliation as a first-class pipeline output.

Per theme: how its assigned entries distribute over the embedding clusters.
coherence_score = top_cluster_share (1.0 = all entries in one cluster).
"""
from collections import Counter
from pathlib import Path

import polars as pl

from cmm.triangulate import MAINTENANCE_LABEL


def coherence_row(theme: str, cluster_labels: list[int]) -> dict:
    """Coherence stats for one theme from its entries' cluster labels.

    The HDBSCAN noise label (-1) is excluded from all stats.
    """
    labels = [c for c in cluster_labels if c != -1]
    if not labels:
        return {"theme": theme, "cluster_spread": 0, "top_cluster": -1,
                "top_cluster_share": 0.0, "coherence_score": 0.0}
    counts = Counter(labels)
    top_cluster, top_n = counts.most_common(1)[0]
    share = top_n / len(labels)
    return {
        "theme": theme,
        "cluster_spread": len(counts),
        "top_cluster": int(top_cluster),
        "top_cluster_share": round(share, 3),
        "coherence_score": round(share, 3),
    }


def build_coherence(codes: pl.DataFrame, embeddings: pl.DataFrame,
                    out: Path = Path("data/processed/coherence.parquet")
                    ) -> pl.DataFrame:
    """Write coherence.parquet — one row per real theme (Maintenance excluded)."""
    cluster_by_id = dict(zip(embeddings["entry_id"].to_list(),
                             embeddings["cluster_label"].to_list()))
    exploded = codes.explode("themes").drop_nulls("themes")
    rows = []
    for theme in exploded["themes"].unique().to_list():
        if theme == MAINTENANCE_LABEL:
            continue
        ids = exploded.filter(pl.col("themes") == theme)["entry_id"].to_list()
        labels = [cluster_by_id.get(e, -1) for e in ids]
        rows.append(coherence_row(theme, labels))
    df = pl.DataFrame(rows)
    df.write_parquet(out)
    print(f"C1: coherence for {df.height} themes")
    return df


if __name__ == "__main__":
    build_coherence(pl.read_parquet("data/processed/codes.parquet"),
                    pl.read_parquet("data/processed/embeddings.parquet"))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_coherence.py -v`
Expected: PASS

- [ ] **Step 5: Run C1 and inspect**

Run:
```bash
uv run python -m cmm.coherence
uv run python -c "import polars as pl; print(pl.read_parquet('data/processed/coherence.parquet'))"
```
Expected: one row per theme; `coherence_score` between 0 and 1.

- [ ] **Step 6: Commit**

```bash
git add src/cmm/coherence.py tests/test_coherence.py data/processed/coherence.parquet
git commit -m "feat(C1): cluster-theme coherence as a first-class pipeline output"
```

---

### Task 13: C2 — Notebook coherence view

**Files:**
- Modify: `notebooks/analysis.py`

**Context:** Add a cluster×theme heatmap, per-theme confidence + evidence badges, a residual section, and a "bottom-up theme" column in the cluster explorer. No test — marimo cells are verified by running the notebook.

- [ ] **Step 1: Load the new artifacts**

In `notebooks/analysis.py`, find the data-loading cell (the one reading `themes`/`codes`) and add `coherence` plus the residual JSON. Replace that cell's body so it reads:

```python
@app.cell
def _(mo, pl):
    import json
    changelog = pl.read_parquet("data/processed/changelog.parquet")
    blogs = pl.read_parquet("data/processed/blogs.parquet")
    joins = pl.read_parquet("data/processed/joins.parquet")
    embeddings = pl.read_parquet("data/processed/embeddings.parquet")
    themes = pl.read_parquet("data/processed/themes.parquet")
    codes = pl.read_parquet("data/processed/codes.parquet")
    coherence = pl.read_parquet("data/processed/coherence.parquet")
    residual = json.load(open("data/processed/residual_analysis.json"))
    mo.md("# Claude Code Mental Models")
    return (changelog, blogs, joins, embeddings, themes, codes,
            coherence, residual)
```

- [ ] **Step 2: Add the cluster×theme heatmap cell**

Append a new cell:

```python
@app.cell
def _(mo, pl, alt, codes, embeddings):
    cl = dict(zip(embeddings["entry_id"].to_list(),
                  embeddings["cluster_label"].to_list()))
    xt = (codes.explode("themes").drop_nulls("themes")
          .with_columns(pl.col("entry_id")
                        .map_elements(lambda e: cl.get(e, -1),
                                      return_dtype=pl.Int64).alias("cluster"))
          .filter(pl.col("cluster") != -1)
          .group_by("themes", "cluster").len())
    heat = alt.Chart(xt.to_pandas()).mark_rect().encode(
        x="cluster:O", y="themes:N",
        color=alt.Color("len:Q", title="entries"),
    ).properties(title="Cluster x theme cross-tab", width=700)
    mo.ui.altair_chart(heat)
```

- [ ] **Step 3: Add the theme table with confidence + evidence badges**

Append:

```python
@app.cell
def _(mo, themes, coherence):
    table = (themes.join(coherence, left_on="name", right_on="theme", how="left")
             .select("name", "confidence_tier", "evidence_tier", "entry_count",
                     "coherence_score", "corroborated_top_down",
                     "corroborated_independent", "first_seen_date"))
    mo.ui.table(table)
```

- [ ] **Step 4: Add the residual section**

Append:

```python
@app.cell
def _(mo, residual):
    mo.md(f"""
## Unassigned residual

**{residual['residual_count']} entries ({residual['residual_fraction']:.0%})**
fall under *Maintenance / no conceptual shift* — bug fixes and upkeep that
demanded no new user competency. By source: {residual['by_source']}.

Examples:
""" + "\n".join(f"- {x}" for x in residual["examples"]))
```

- [ ] **Step 5: Add the bottom-up theme column to the cluster explorer**

Find the existing cluster-explorer cell (around line 88, the `data_explorer` over `embeddings.join(codes...)`). Add `mini_themes` to that join. Replace that cell's body:

```python
@app.cell
def _(mo, pl, embeddings, codes):
    mini = pl.read_parquet("data/processed/mini_themes.parquet")
    clusters = (embeddings
                .join(codes.select("entry_id", "themes"), on="entry_id", how="left")
                .join(mini.select("cluster_label", "mini_theme"),
                      on="cluster_label", how="left")
                .select("entry_id", "text", "cluster_label", "mini_theme",
                        "themes", "umap_x", "umap_y"))
    mo.ui.data_explorer(clusters)
```

- [ ] **Step 6: Run the notebook to verify it loads**

Run: `uv run marimo run notebooks/analysis.py` (open the URL, confirm no cell errors, close it).
Expected: heatmap, theme table, residual section, and cluster explorer all render.

- [ ] **Step 7: Commit**

```bash
git add notebooks/analysis.py
git commit -m "feat(C2): notebook coherence heatmap, confidence badges, residual section"
```

---

### Task 14: C3 — Claim reframing sweep

**Files:**
- Modify: `notebooks/analysis.py`, `docs/findings.md`, `docs/methodology.md`
- Modify (prompts): `src/cmm/thematic_coding.py`, `src/cmm/theme_derivations.py`

**Context:** Replace "mental models developers held" with "competencies / expectations the tool's surface increasingly demanded." Keep "mental models" only where explicitly labelled as an organizing lens. Also update `methodology.md` to describe the triangulated design and record the A2 date-recovery figure (from Task 2 Step 6) and the new cluster count (Task 3 Step 2).

- [ ] **Step 1: Find every overreaching claim**

Run:
```bash
grep -rn -i "mental model" notebooks/analysis.py docs/findings.md docs/methodology.md src/cmm/
```
Expected: a list of occurrences. For each, decide: is it a *claim* about what developers held (downgrade it), or a *labelled lens* (keep, but ensure it is explicitly labelled)?

- [ ] **Step 2: Downgrade claim wording**

In `notebooks/analysis.py` and `docs/findings.md`, rewrite claim sentences. Pattern: "the mental models developers held" → "the competencies and expectations the tool's surface increasingly demanded of its users". Keep one explicitly-labelled sentence where the lens is introduced, e.g.: *"We use 'mental models' as an organizing lens for these competencies — it is a framing, not a measured claim about individual developers."*

- [ ] **Step 3: Soften the discovery prompts**

In `src/cmm/thematic_coding.py`, the `DISCOVER_SYSTEM` string says "how a developer's mental model ... had to evolve". Change to: "what competencies and expectations using Claude Code increasingly demanded of a developer over a year of releases". Make the same edit anywhere `theme_derivations.py` echoes that phrasing. (These prompt strings feed B2/B3; the cached results from earlier tasks stay valid — this only affects future re-runs, which is acceptable.)

- [ ] **Step 4: Update `methodology.md`**

In `docs/methodology.md`, add a section describing the triangulated design: the three derivations, anchor-on-B1 triangulation, confidence tiers, the coherence output, and the labelled residual. Record the A2 date-recovery number and the A3 cluster count. State that B3 used GPT-5.5 via `codex exec`.

- [ ] **Step 5: Verify no stray overreach remains**

Run:
```bash
grep -rn -i "developers held\|mental models developers" notebooks/analysis.py docs/
```
Expected: no output (every overreaching phrase rewritten).

- [ ] **Step 6: Commit**

```bash
git add notebooks/analysis.py docs/findings.md docs/methodology.md src/cmm/thematic_coding.py src/cmm/theme_derivations.py
git commit -m "docs(C3): downgrade claim wording; document triangulated methodology"
```

---

### Task 15: C4 — Stratified manual-audit sample

**Files:**
- Create: `src/cmm/audit_sample.py`
- Test: `tests/test_audit_sample.py`

**Context:** Emit a ~40-row CSV stratified across three strata — high-confidence theme matches, Maintenance/no-theme items, and cluster↔theme disagreements — for the user to audit by hand. The agreement rate goes into `findings.md` (done by the user, not this task).

- [ ] **Step 1: Write the failing test**

Create `tests/test_audit_sample.py`:

```python
from cmm.audit_sample import stratum_for


def test_stratum_for_maintenance():
    assert stratum_for(["Maintenance / no conceptual shift"],
                       theme_tier="high", coherent=True) == "residual"


def test_stratum_for_high_confidence_match():
    assert stratum_for(["T1"], theme_tier="high", coherent=True) == "high_confidence"


def test_stratum_for_disagreement():
    # assigned a theme but the entry sits in a cluster the theme doesn't own
    assert stratum_for(["T1"], theme_tier="high", coherent=False) == "disagreement"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_sample.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cmm.audit_sample'`

- [ ] **Step 3: Implement `audit_sample.py`**

Create `src/cmm/audit_sample.py`:

```python
# src/cmm/audit_sample.py
"""C4: emit a stratified ~40-item sample for manual audit.

Three strata: high-confidence theme matches, the Maintenance residual, and
cluster<->theme disagreements (entry's cluster is not the theme's top cluster).
The user fills the `agree` column by hand; the rate goes into findings.md.
"""
import random
from pathlib import Path

import polars as pl

from cmm.triangulate import MAINTENANCE_LABEL

_PER_STRATUM = 14


def stratum_for(themes: list[str], theme_tier: str, coherent: bool) -> str:
    """Classify one entry into an audit stratum."""
    if MAINTENANCE_LABEL in themes:
        return "residual"
    if not coherent:
        return "disagreement"
    return "high_confidence"


def build_sample(codes: pl.DataFrame, embeddings: pl.DataFrame,
                 themes: pl.DataFrame, coherence: pl.DataFrame,
                 out: Path = Path("data/processed/audit_sample.csv"),
                 seed: int = 42) -> Path:
    """Write the stratified audit CSV."""
    text_by_id = dict(zip(embeddings["entry_id"].to_list(),
                          embeddings["text"].to_list()))
    cluster_by_id = dict(zip(embeddings["entry_id"].to_list(),
                             embeddings["cluster_label"].to_list()))
    tier_by_theme = dict(zip(themes["name"].to_list(),
                             themes["confidence_tier"].to_list()))
    topcluster_by_theme = dict(zip(coherence["theme"].to_list(),
                                   coherence["top_cluster"].to_list()))

    buckets: dict[str, list[dict]] = {"high_confidence": [], "residual": [],
                                      "disagreement": []}
    for r in codes.iter_rows(named=True):
        tlist = r["themes"]
        first = tlist[0] if tlist else MAINTENANCE_LABEL
        tier = tier_by_theme.get(first, "high")
        entry_cluster = cluster_by_id.get(r["entry_id"], -1)
        coherent = entry_cluster == topcluster_by_theme.get(first, entry_cluster)
        s = stratum_for(tlist, tier, coherent)
        buckets[s].append({
            "entry_id": r["entry_id"],
            "text": text_by_id.get(r["entry_id"], "")[:200],
            "stratum": s,
            "assigned_themes": "; ".join(tlist),
            "top_cluster": topcluster_by_theme.get(first, ""),
            "agree": "",
        })

    rng = random.Random(seed)
    picked: list[dict] = []
    for s, items in buckets.items():
        rng.shuffle(items)
        picked += items[:_PER_STRATUM]
    pl.DataFrame(picked).write_csv(out)
    print(f"C4: wrote {len(picked)} audit rows to {out}")
    return out


if __name__ == "__main__":
    build_sample(
        pl.read_parquet("data/processed/codes.parquet"),
        pl.read_parquet("data/processed/embeddings.parquet"),
        pl.read_parquet("data/processed/themes.parquet"),
        pl.read_parquet("data/processed/coherence.parquet"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_audit_sample.py -v`
Expected: PASS

- [ ] **Step 5: Run C4 and verify the CSV**

Run:
```bash
uv run python -m cmm.audit_sample
uv run python -c "import polars as pl; print(pl.read_csv('data/processed/audit_sample.csv').group_by('stratum').len())"
```
Expected: a CSV with up to ~42 rows spread across the three strata; `agree` column blank.

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/cmm/audit_sample.py tests/test_audit_sample.py data/processed/audit_sample.csv
git commit -m "feat(C4): stratified manual-audit sample emitter"
```

- [ ] **Step 8: Hand off the manual audit to the user**

The audit itself is non-automated. After this task, tell the user: open `data/processed/audit_sample.csv`, fill the `agree` column (`y`/`n`) for each row, and record the agreement rate per stratum in `docs/findings.md`. The pipeline is complete; this is the one irreducibly human step.

---

## Self-review

**Spec coverage:** A1→T1, A2→T2, A3→T3, B-infra→T4, B1→T5, B1.5→T6, B2+B3→T7, B4→T8, B5→T9, B6→T10, B7→T11, C1→T12, C2→T13, C3→T14, C4→T15. All 9 problems (P1–P9) trace to a task: P1→T12, P2→T5/T6, P3→T9, P4→T4/T7, P5→T10, P6→T11, P7→T3, P8→T1/T2, P9→T14. No gaps.

**"Done" criteria:** every theme carries derivations/count/coherence/tier (T8,T11,T12); descriptions grounded (T9); residual labelled with its own section (T10,T13); findings reports audit rate + overlap (T14,T15 handoff); notebook heatmap + downgraded wording (T13,T14); methodology updated (T14). Covered.

**Type consistency:** `MAINTENANCE_LABEL` defined in `triangulate.py` (T10), imported by `coherence.py` (T12) and `audit_sample.py` (T15). `confidence_tier`/`evidence_tier` strings consistent across T8/T11/T12/T15. `anchor_themes.parquet` produced in T6, consumed in T8/T11. `codes.parquet` schema (`entry_id, source, date, themes`) consistent T8→T15.
