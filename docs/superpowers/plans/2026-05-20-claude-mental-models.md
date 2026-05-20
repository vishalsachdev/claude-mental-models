# Claude Code Mental Models — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-corpus, cached pipeline that analyzes Claude Code's changelog and Anthropic's blogs, then surfaces the evolving "mental models" of Claude Code use through a reactive marimo notebook.

**Architecture:** Plain Python scripts (`src/`) collect and process data into `data/processed/` (Parquet); all network/LLM calls are content-hash cached. A marimo notebook (`notebooks/analysis.py`) reads only processed data and renders charts plus a RAG chat panel. Parsers are TDD'd against saved HTML/Markdown fixtures; analysis stages are validated by inspection.

**Tech Stack:** Python 3.12, `uv`, `marimo`, `polars`, `httpx`, `sentence-transformers`, `hdbscan`, `umap-learn`, `anthropic`, `altair`, `pytest`.

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | uv project, pinned deps |
| `src/cmm/cache.py` | content-hash disk cache for HTTP + LLM calls |
| `src/cmm/collect_changelog.py` | clone repo, parse CHANGELOG.md, date via git log |
| `src/cmm/collect_blogs.py` | crawl Anthropic news/engineering, fetch posts |
| `src/cmm/tag_and_join.py` | CC-relevance tagging + changelog↔blog join |
| `src/cmm/embed_cluster.py` | embeddings + HDBSCAN + UMAP |
| `src/cmm/thematic_coding.py` | LLM open→axial coding |
| `src/cmm/rag.py` | retriever + Claude chat model for the notebook |
| `src/cmm/llm.py` | thin cached Anthropic API wrapper |
| `notebooks/analysis.py` | the marimo deliverable |
| `tests/test_collect_changelog.py` | parser unit tests |
| `tests/test_collect_blogs.py` | parser unit tests |
| `tests/test_cache.py` | cache unit tests |
| `docs/findings.md` | narrative conclusions |

`src/cmm/` is a package so modules import cleanly (`from cmm.cache import ...`).

---

## Task 0: Project scaffold

**Files:**
- Create: `pyproject.toml`, `src/cmm/__init__.py`, `.gitignore`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/cache/.gitkeep`, `data/fixtures/.gitkeep`

- [ ] **Step 1: Initialize the uv project**

Run:
```bash
cd /Users/vishal/research/claude-mental-models
uv init --no-readme --package --name cmm .
```

- [ ] **Step 2: Pin dependencies**

Run:
```bash
uv add marimo polars httpx sentence-transformers hdbscan umap-learn anthropic altair
uv add --dev pytest
```

- [ ] **Step 3: Create directory placeholders and .gitignore**

Create `.gitignore`:
```
.venv/
__pycache__/
*.pyc
data/raw/*
data/cache/*
!data/raw/.gitkeep
!data/cache/.gitkeep
.marimo.toml
```

Run:
```bash
mkdir -p src/cmm data/raw data/processed data/cache data/fixtures tests notebooks
touch src/cmm/__init__.py data/raw/.gitkeep data/processed/.gitkeep data/cache/.gitkeep data/fixtures/.gitkeep tests/__init__.py
```

`data/processed/` is committed (small Parquet); `data/raw/` and `data/cache/` are gitignored.

- [ ] **Step 4: Verify the environment**

Run: `uv run python -c "import marimo, polars, httpx, anthropic; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold uv project and package layout"
```

---

## Task 1: Content-hash disk cache

**Files:**
- Create: `src/cmm/cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cache.py
from cmm.cache import cached_call


def test_cached_call_runs_once(tmp_path):
    calls = []

    def expensive(x):
        calls.append(x)
        return x * 2

    key = "double-21"
    first = cached_call(key, lambda: expensive(21), cache_dir=tmp_path)
    second = cached_call(key, lambda: expensive(21), cache_dir=tmp_path)

    assert first == 42
    assert second == 42
    assert calls == [21]  # underlying function ran only once
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cache.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cmm.cache'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/cmm/cache.py
"""Content-hash disk cache for expensive network/LLM calls."""
import hashlib
import json
from pathlib import Path
from typing import Callable

DEFAULT_CACHE = Path("data/cache")


def _path(key: str, cache_dir: Path) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.json"


def cached_call(key: str, fn: Callable[[], object], cache_dir: Path = DEFAULT_CACHE):
    """Return cached result for `key`, else run `fn`, cache, and return it.

    Results must be JSON-serializable.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = _path(key, cache_dir)
    if p.exists():
        return json.loads(p.read_text())["value"]
    value = fn()
    p.write_text(json.dumps({"key": key, "value": value}))
    return value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cache.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cmm/cache.py tests/test_cache.py
git commit -m "feat: content-hash disk cache"
```

---

## Task 2: Changelog parser

The Claude Code `CHANGELOG.md` uses `## <version>` headings followed by `- ` bullet entries. This task parses that structure. Dating from git log is added in Task 3.

**Files:**
- Create: `src/cmm/collect_changelog.py`, `data/fixtures/changelog_sample.md`
- Test: `tests/test_collect_changelog.py`

- [ ] **Step 1: Create the fixture file**

Create `data/fixtures/changelog_sample.md`:
```markdown
# Changelog

## 1.2.0

- Added support for subagents
- Fixed a crash when resuming sessions
- Deprecated the legacy `--print` flag

## 1.1.0

- Added MCP server configuration
- Changed default model selection
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_collect_changelog.py
from pathlib import Path
from cmm.collect_changelog import parse_changelog, classify_change

FIXTURE = Path("data/fixtures/changelog_sample.md")


def test_parse_changelog_extracts_versions_and_entries():
    entries = parse_changelog(FIXTURE.read_text())
    versions = {e["version"] for e in entries}
    assert versions == {"1.2.0", "1.1.0"}
    v12 = [e["text"] for e in entries if e["version"] == "1.2.0"]
    assert "Added support for subagents" in v12
    assert len(v12) == 3


def test_parse_changelog_assigns_stable_ids():
    entries = parse_changelog(FIXTURE.read_text())
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids))  # unique


def test_classify_change_keyword_rules():
    assert classify_change("Added support for subagents") == "add"
    assert classify_change("Fixed a crash when resuming") == "fix"
    assert classify_change("Deprecated the legacy flag") == "deprecate"
    assert classify_change("Removed the old API") == "remove"
    assert classify_change("Changed default model selection") == "change"
    assert classify_change("Improved startup time") == "change"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_collect_changelog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cmm.collect_changelog'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/cmm/collect_changelog.py
"""Collect and parse the Claude Code CHANGELOG.md."""
import hashlib
import re
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/anthropics/claude-code.git"
VERSION_RE = re.compile(r"^##\s+v?(\d+\.\d+\.\d+\S*)\s*$")
BULLET_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")

_RULES = [
    ("deprecate", ("deprecat",)),
    ("remove", ("removed", "remove ", "deleted")),
    ("add", ("added", "add ", "new ", "introduc")),
    ("fix", ("fixed", "fix ", "bug")),
]


def classify_change(text: str) -> str:
    """Map a changelog entry to a change_type via keyword rules."""
    low = text.lower()
    for label, keywords in _RULES:
        if any(k in low for k in keywords):
            return label
    return "change"


def _entry_id(version: str, text: str) -> str:
    return hashlib.sha256(f"{version}|{text}".encode()).hexdigest()[:12]


def parse_changelog(markdown: str) -> list[dict]:
    """Parse CHANGELOG.md text into a list of entry dicts.

    Each dict: {id, version, text, change_type}. Raises ValueError if a
    bullet appears before any version heading (structure changed upstream).
    """
    entries: list[dict] = []
    current: str | None = None
    for lineno, line in enumerate(markdown.splitlines(), 1):
        vm = VERSION_RE.match(line)
        if vm:
            current = vm.group(1)
            continue
        bm = BULLET_RE.match(line)
        if bm:
            if current is None:
                raise ValueError(f"Bullet before any version heading at line {lineno}")
            text = bm.group(1)
            entries.append({
                "id": _entry_id(current, text),
                "version": current,
                "text": text,
                "change_type": classify_change(text),
            })
    if not entries:
        raise ValueError("No changelog entries parsed — upstream format may have changed")
    return entries


def clone_or_update_repo(dest: Path) -> Path:
    """Clone anthropics/claude-code (or fetch if already present)."""
    dest = Path(dest)
    if (dest / ".git").exists():
        subprocess.run(["git", "-C", str(dest), "fetch", "--all"], check=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1000", REPO_URL, str(dest)], check=True)
    return dest
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_collect_changelog.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/cmm/collect_changelog.py tests/test_collect_changelog.py data/fixtures/changelog_sample.md
git commit -m "feat: changelog parser with change-type classification"
```

---

## Task 3: Date changelog entries and write Parquet

Dates come from the git history of `CHANGELOG.md`: the first commit that introduced a given `## version` heading. This requires the real cloned repo, so it is verified by running, not by a fixture test.

**Files:**
- Modify: `src/cmm/collect_changelog.py`

- [ ] **Step 1: Add dating + main entrypoint to `collect_changelog.py`**

Append to `src/cmm/collect_changelog.py`:
```python
import json


def version_dates(repo: Path) -> dict[str, str]:
    """Map version -> ISO date of the commit that first added its heading.

    Walks `git log` of CHANGELOG.md oldest-first; the first commit whose diff
    adds `## <version>` dates that version.
    """
    repo = Path(repo)
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--date=short",
         "--format=%H%x09%ad", "--", "CHANGELOG.md"],
        check=True, capture_output=True, text=True,
    ).stdout.strip().splitlines()
    dates: dict[str, str] = {}
    for line in log:
        commit, date = line.split("\t")
        diff = subprocess.run(
            ["git", "-C", str(repo), "show", commit, "--", "CHANGELOG.md"],
            check=True, capture_output=True, text=True,
        ).stdout
        for added in re.findall(r"^\+##\s+v?(\d+\.\d+\.\d+\S*)\s*$", diff, re.M):
            dates.setdefault(added, date)
    return dates


def collect(repo_dir: Path = Path("data/raw/claude-code"),
            out: Path = Path("data/processed/changelog.parquet")) -> Path:
    """End-to-end: clone repo, parse, date, write Parquet."""
    import polars as pl

    repo = clone_or_update_repo(repo_dir)
    entries = parse_changelog((repo / "CHANGELOG.md").read_text())
    dates = version_dates(repo)
    undated = sorted({e["version"] for e in entries} - set(dates))
    if undated:
        print(f"WARNING: {len(undated)} versions have no git date: {undated}")
    for e in entries:
        e["date"] = dates.get(e["version"])
    df = pl.DataFrame(entries)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"Wrote {len(df)} changelog entries to {out}")
    return out


if __name__ == "__main__":
    collect()
```

- [ ] **Step 2: Run the collector against the real repo**

Run: `uv run python -m cmm.collect_changelog`
Expected: clones `anthropics/claude-code`, prints `Wrote <N> changelog entries to data/processed/changelog.parquet` where N is in the hundreds. Note any undated-version warning.

- [ ] **Step 3: Eyeball the output**

Run:
```bash
uv run python -c "import polars as pl; df=pl.read_parquet('data/processed/changelog.parquet'); print(df.head()); print(df['change_type'].value_counts()); print('null dates:', df['date'].null_count())"
```
Expected: a table with `id, version, text, change_type, date`; a change_type distribution; ideally `null dates: 0` (a small nonzero count is acceptable if Step 2 warned).

- [ ] **Step 4: Re-run tests (regression check)**

Run: `uv run pytest tests/test_collect_changelog.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cmm/collect_changelog.py data/processed/changelog.parquet
git commit -m "feat: date changelog entries from git log and write Parquet"
```

---

## Task 4: Blog crawler

Crawls Anthropic's news index and engineering index, broadly (no CC pre-filter). Index-page HTML structure is unknown until fetched, so Step 1 saves a live fixture, then the parser is TDD'd against it.

**Files:**
- Create: `src/cmm/collect_blogs.py`
- Test: `tests/test_collect_blogs.py`
- Create (Step 1, live): `data/fixtures/news_index.html`

- [ ] **Step 1: Save a live fixture of the news index**

Run:
```bash
uv run python -c "import httpx; open('data/fixtures/news_index.html','w').write(httpx.get('https://www.anthropic.com/news', follow_redirects=True, timeout=30).text)"
```
Then open `data/fixtures/news_index.html` and identify the repeating element that wraps each post link (the anchor `href` pattern, e.g. `/news/<slug>`). Record the CSS/regex selector you will use in Step 3.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_collect_blogs.py
from pathlib import Path
from cmm.collect_blogs import extract_post_links

FIXTURE = Path("data/fixtures/news_index.html")


def test_extract_post_links_finds_news_urls():
    links = extract_post_links(FIXTURE.read_text(), base="https://www.anthropic.com")
    assert len(links) > 0
    assert all(u.startswith("https://www.anthropic.com/") for u in links)
    assert all("/news/" in u or "/engineering/" in u or "/research/" in u for u in links)
    assert len(links) == len(set(links))  # deduped
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_collect_blogs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cmm.collect_blogs'`

- [ ] **Step 4: Write minimal implementation**

Adjust the `href` regex in `extract_post_links` to match the pattern observed in Step 1.
```python
# src/cmm/collect_blogs.py
"""Crawl Anthropic news/engineering posts (broad collection)."""
import json
import re
from pathlib import Path

import httpx

INDEX_URLS = [
    "https://www.anthropic.com/news",
    "https://www.anthropic.com/engineering",
]
# Matches post links like /news/<slug>, /engineering/<slug>, /research/<slug>.
HREF_RE = re.compile(r'href="(/(?:news|engineering|research)/[a-z0-9][a-z0-9-]+)"')


def extract_post_links(html: str, base: str) -> list[str]:
    """Return a deduped, absolute list of post URLs found in an index page."""
    seen: dict[str, None] = {}
    for path in HREF_RE.findall(html):
        seen.setdefault(base.rstrip("/") + path, None)
    return list(seen)


def fetch(url: str, client: httpx.Client) -> str:
    return client.get(url, follow_redirects=True, timeout=30).text
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_collect_blogs.py -v`
Expected: PASS

- [ ] **Step 6: Add post-body extraction and the collect entrypoint**

Append to `src/cmm/collect_blogs.py`:
```python
from cmm.cache import cached_call


def extract_post(html: str) -> dict:
    """Extract title, date, and body text from a post page.

    Title from <h1> or <title>; date from a <time> tag or an ISO date in the
    page; body as visible text with tags stripped.
    """
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""
    date_m = re.search(r'datetime="(\d{4}-\d{2}-\d{2})', html) \
        or re.search(r"\b(\d{4}-\d{2}-\d{2})\b", html)
    date = date_m.group(1) if date_m else None
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return {"title": title, "date": date, "body": body}


def collect(out: Path = Path("data/raw/blogs.json")) -> Path:
    """Crawl index pages, fetch each post (cached), write raw JSON."""
    posts: list[dict] = []
    with httpx.Client() as client:
        links: list[str] = []
        for index in INDEX_URLS:
            html = cached_call(f"index::{index}", lambda i=index: fetch(i, client))
            links += extract_post_links(html, base="https://www.anthropic.com")
        links = list(dict.fromkeys(links))
        print(f"Found {len(links)} post links")
        for url in links:
            html = cached_call(f"post::{url}", lambda u=url: fetch(u, client))
            post = extract_post(html)
            post["url"] = url
            posts.append(post)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(posts, indent=2))
    print(f"Wrote {len(posts)} posts to {out}")
    return out


if __name__ == "__main__":
    collect()
```

- [ ] **Step 7: Run the crawler and eyeball output**

Run: `uv run python -m cmm.collect_blogs`
Expected: prints `Found <N> post links` and `Wrote <N> posts to data/raw/blogs.json`. Spot-check `data/raw/blogs.json` — titles non-empty, dates mostly present, bodies are readable prose.

- [ ] **Step 8: Commit**

```bash
git add src/cmm/collect_blogs.py tests/test_collect_blogs.py data/fixtures/news_index.html
git commit -m "feat: Anthropic blog crawler with cached fetches"
```

---

## Task 5: Cached Anthropic LLM wrapper

**Files:**
- Create: `src/cmm/llm.py`

- [ ] **Step 1: Write the wrapper**

```python
# src/cmm/llm.py
"""Thin, cached wrapper around the Anthropic Messages API."""
import json
import os

from anthropic import Anthropic

from cmm.cache import cached_call

MODEL = "claude-opus-4-7"
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _client = Anthropic()
    return _client


def complete(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Return the model's text response. Cached by (system, prompt, model)."""
    key = "llm::" + json.dumps({"s": system, "p": prompt, "m": MODEL, "t": max_tokens})

    def run() -> str:
        msg = _get_client().messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system or "You are a precise research assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")

    return cached_call(key, run)


def complete_json(prompt: str, system: str = "", max_tokens: int = 2000):
    """Like `complete`, but parse the response as JSON.

    Strips a leading ```json fence if present.
    """
    raw = complete(prompt, system, max_tokens).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)
```

- [ ] **Step 2: Smoke-test the wrapper**

Ensure `ANTHROPIC_API_KEY` is set in the environment, then run:
```bash
uv run python -c "from cmm.llm import complete_json; print(complete_json('Reply with JSON: {\"ok\": true}'))"
```
Expected: `{'ok': True}`

- [ ] **Step 3: Commit**

```bash
git add src/cmm/llm.py
git commit -m "feat: cached Anthropic LLM wrapper"
```

---

## Task 6: Tag blogs for CC-relevance and join to changelog

**Files:**
- Create: `src/cmm/tag_and_join.py`

- [ ] **Step 1: Write the tagging + join module**

```python
# src/cmm/tag_and_join.py
"""Tag blogs for Claude Code relevance and join them to changelog versions."""
import json
from datetime import date
from pathlib import Path

import polars as pl

from cmm.llm import complete_json

TAG_SYSTEM = (
    "You classify Anthropic blog posts by whether they are relevant to a "
    "Claude Code (CLI / coding agent / agent SDK) user's mental model. "
    "Respond ONLY with JSON: {\"cc_relevant\": bool, \"cc_confidence\": 0..1}."
)


def tag_blog(post: dict) -> dict:
    """Return the post dict augmented with cc_relevant and cc_confidence."""
    prompt = (
        f"Title: {post['title']}\n\n"
        f"Excerpt: {post['body'][:1500]}\n\n"
        "Is this relevant to how someone uses Claude Code (the coding agent)?"
    )
    verdict = complete_json(prompt, system=TAG_SYSTEM, max_tokens=200)
    return {**post, "cc_relevant": bool(verdict["cc_relevant"]),
            "cc_confidence": float(verdict["cc_confidence"])}


def _name_overlap(entry_text: str, blog_title: str) -> bool:
    """True if a salient word from the changelog entry appears in the title."""
    stop = {"the", "a", "an", "for", "and", "with", "to", "of", "in", "on",
            "added", "fixed", "support", "new", "now", "when"}
    words = {w.lower().strip(".,`") for w in entry_text.split() if len(w) > 3}
    words -= stop
    title = blog_title.lower()
    return any(w in title for w in words)


def join_changelog_blogs(changelog: pl.DataFrame, blogs: pl.DataFrame,
                         window_days: int = 14) -> pl.DataFrame:
    """Join each changelog version to blogs within +/- window_days that also
    share a feature word. Returns one row per version with blog_urls + tier.
    """
    rows = []
    versions = (changelog.filter(pl.col("date").is_not_null())
                .group_by("version")
                .agg(pl.col("date").first(), pl.col("text")))
    cc_blogs = blogs.filter(pl.col("cc_relevant") & pl.col("date").is_not_null())
    for v in versions.iter_rows(named=True):
        vdate = date.fromisoformat(v["date"])
        matched = []
        for b in cc_blogs.iter_rows(named=True):
            bdate = date.fromisoformat(b["date"])
            if abs((bdate - vdate).days) > window_days:
                continue
            if any(_name_overlap(t, b["title"]) for t in v["text"]):
                matched.append(b["url"])
        rows.append({
            "version": v["version"],
            "date": v["date"],
            "blog_urls": sorted(set(matched)),
            "impact_tier": "narrated" if matched else "silent",
        })
    return pl.DataFrame(rows)


def run(blogs_raw: Path = Path("data/raw/blogs.json"),
        changelog: Path = Path("data/processed/changelog.parquet")) -> None:
    posts = json.loads(Path(blogs_raw).read_text())
    tagged = [tag_blog(p) for p in posts]
    blogs_df = pl.DataFrame(tagged)
    blogs_df.write_parquet("data/processed/blogs.parquet")
    print(f"Tagged {len(blogs_df)} blogs; "
          f"{blogs_df['cc_relevant'].sum()} CC-relevant")

    joins = join_changelog_blogs(pl.read_parquet(changelog), blogs_df)
    joins.write_parquet("data/processed/joins.parquet")
    narrated = joins.filter(pl.col("impact_tier") == "narrated").height
    print(f"Joined {joins.height} versions; {narrated} narrated")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run it and eyeball output**

Run: `uv run python -m cmm.tag_and_join`
Expected: prints tag counts and join counts. Spot-check `data/processed/joins.parquet`: some versions `narrated`, most `silent`; `blog_urls` look plausible for the matched versions.

- [ ] **Step 3: Commit**

```bash
git add src/cmm/tag_and_join.py data/processed/blogs.parquet data/processed/joins.parquet
git commit -m "feat: tag blogs for CC-relevance and join to changelog versions"
```

---

## Task 7: Embeddings spine — embed, cluster, project

**Files:**
- Create: `src/cmm/embed_cluster.py`

- [ ] **Step 1: Write the module**

```python
# src/cmm/embed_cluster.py
"""Quantitative spine: embed entries, cluster (HDBSCAN), project (UMAP)."""
from pathlib import Path

import hdbscan
import polars as pl
import umap
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"  # pinned local model


def build(changelog: Path = Path("data/processed/changelog.parquet"),
          blogs: Path = Path("data/processed/blogs.parquet"),
          out: Path = Path("data/processed/embeddings.parquet")) -> Path:
    """Embed changelog entries + CC-relevant blogs, cluster, and 2D-project."""
    cl = pl.read_parquet(changelog).select(
        pl.col("id").alias("entry_id"),
        pl.col("text"),
        pl.lit("changelog").alias("source"),
        pl.col("date"),
    )
    bl = (pl.read_parquet(blogs).filter(pl.col("cc_relevant"))
          .select(
              pl.col("url").alias("entry_id"),
              (pl.col("title") + ". " + pl.col("body").str.slice(0, 800)).alias("text"),
              pl.lit("blog").alias("source"),
              pl.col("date"),
          ))
    df = pl.concat([cl, bl])

    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode(df["text"].to_list(), show_progress_bar=True)

    labels = hdbscan.HDBSCAN(min_cluster_size=5).fit_predict(vectors)
    coords = umap.UMAP(n_components=2, random_state=42).fit_transform(vectors)

    out_df = df.with_columns(
        pl.Series("cluster_label", labels),
        pl.Series("umap_x", coords[:, 0]),
        pl.Series("umap_y", coords[:, 1]),
        pl.Series("vector", [v.tolist() for v in vectors]),
    )
    out = Path(out)
    out_df.write_parquet(out)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"Embedded {out_df.height} items into {n_clusters} clusters")
    return out


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Run it and eyeball output**

Run: `uv run python -m cmm.embed_cluster`
Expected: progress bar, then `Embedded <N> items into <K> clusters` with K roughly 6–20. Spot-check `data/processed/embeddings.parquet` has `cluster_label`, `umap_x`, `umap_y`, `vector`.

- [ ] **Step 3: Commit**

```bash
git add src/cmm/embed_cluster.py data/processed/embeddings.parquet
git commit -m "feat: embeddings spine with HDBSCAN clustering and UMAP projection"
```

---

## Task 8: Thematic coding — open → axial → mental models

**Files:**
- Create: `src/cmm/thematic_coding.py`

- [ ] **Step 1: Write the module**

```python
# src/cmm/thematic_coding.py
"""LLM thematic coding: open codes -> axial mental-model themes."""
import json
from pathlib import Path

import polars as pl

from cmm.llm import complete_json

OPEN_SYSTEM = (
    "You are doing qualitative open coding of Claude Code release notes and "
    "blog posts. For the given item, return JSON {\"codes\": [..]} with 1-3 "
    "short conceptual codes describing what the user must understand or how "
    "they must think differently. Codes are reusable phrases, not summaries."
)

AXIAL_SYSTEM = (
    "You are doing axial coding. Given a list of open codes from Claude Code's "
    "release history, group them into 6-10 named 'mental models' a user had to "
    "develop. Return JSON {\"themes\": [{\"name\":..., \"description\":..., "
    "\"member_codes\":[...]}]}. Every input code must belong to exactly one theme."
)


def open_code(items: pl.DataFrame) -> pl.DataFrame:
    """Add a `codes` list column to each entry via LLM open coding."""
    coded = []
    for row in items.iter_rows(named=True):
        prompt = f"Source: {row['source']}\nItem: {row['text'][:1200]}"
        result = complete_json(prompt, system=OPEN_SYSTEM, max_tokens=300)
        coded.append({"entry_id": row["entry_id"], "date": row["date"],
                      "codes": result["codes"]})
    return pl.DataFrame(coded)


def axial_code(codes_df: pl.DataFrame) -> pl.DataFrame:
    """Group all open codes into named mental-model themes."""
    all_codes = sorted({c for codes in codes_df["codes"].to_list() for c in codes})
    result = complete_json(
        "Open codes:\n" + "\n".join(f"- {c}" for c in all_codes),
        system=AXIAL_SYSTEM, max_tokens=4000,
    )
    # earliest date any member code appears => theme first_seen_date
    code_dates: dict[str, str] = {}
    for row in codes_df.iter_rows(named=True):
        for c in row["codes"]:
            if row["date"] and (c not in code_dates or row["date"] < code_dates[c]):
                code_dates[c] = row["date"]
    themes = []
    for t in result["themes"]:
        member_dates = [code_dates[c] for c in t["member_codes"] if c in code_dates]
        themes.append({
            "name": t["name"],
            "description": t["description"],
            "member_codes": t["member_codes"],
            "first_seen_date": min(member_dates) if member_dates else None,
        })
    return pl.DataFrame(themes)


def run(embeddings: Path = Path("data/processed/embeddings.parquet")) -> None:
    items = pl.read_parquet(embeddings).select("entry_id", "text", "source", "date")
    codes_df = open_code(items)
    codes_df.write_parquet("data/processed/codes.parquet")
    print(f"Open-coded {codes_df.height} items")

    themes_df = axial_code(codes_df)
    themes_df.write_parquet("data/processed/themes.parquet")
    print(f"Derived {themes_df.height} mental-model themes:")
    for name in themes_df["name"].to_list():
        print(f"  - {name}")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run it and eyeball output**

Run: `uv run python -m cmm.thematic_coding`
Expected: prints `Open-coded <N> items` then 6–10 theme names. Read the theme names — they should read like mental models ("context as a managed resource", "delegation to subagents"), not topic labels ("MCP", "bug fixes"). If they read as topics, tighten `AXIAL_SYSTEM` and re-run (cache makes open-coding instant on re-run).

- [ ] **Step 3: Commit**

```bash
git add src/cmm/thematic_coding.py data/processed/codes.parquet data/processed/themes.parquet
git commit -m "feat: LLM thematic coding into named mental-model themes"
```

---

## Task 9: RAG retriever + chat model

**Files:**
- Create: `src/cmm/rag.py`

- [ ] **Step 1: Write the module**

```python
# src/cmm/rag.py
"""Retriever over the embeddings spine + a Claude chat model for marimo."""
from pathlib import Path

import numpy as np
import polars as pl
from sentence_transformers import SentenceTransformer

from cmm.embed_cluster import EMBED_MODEL
from cmm.llm import complete

_model: SentenceTransformer | None = None
_corpus: pl.DataFrame | None = None
_matrix: np.ndarray | None = None

RAG_SYSTEM = (
    "You answer questions about how Claude Code's features evolved and what "
    "mental models a user had to develop. Answer ONLY from the provided "
    "context. Cite changelog versions and blog URLs inline. If the context "
    "does not contain the answer, say so."
)


def _load(embeddings: Path = Path("data/processed/embeddings.parquet")):
    global _model, _corpus, _matrix
    if _corpus is None:
        _corpus = pl.read_parquet(embeddings)
        _matrix = np.array(_corpus["vector"].to_list())
        _model = SentenceTransformer(EMBED_MODEL)


def retrieve(question: str, k: int = 8) -> pl.DataFrame:
    """Return the k most similar corpus rows to the question."""
    _load()
    q = _model.encode([question])[0]
    sims = _matrix @ q / (np.linalg.norm(_matrix, axis=1) * np.linalg.norm(q))
    top = np.argsort(sims)[::-1][:k]
    return _corpus[top.tolist()]


def answer(question: str) -> str:
    """Retrieve context and have Claude answer, grounded with citations."""
    hits = retrieve(question)
    context = "\n\n".join(
        f"[{r['source']} | {r['entry_id']} | {r['date']}] {r['text'][:600]}"
        for r in hits.iter_rows(named=True)
    )
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    return complete(prompt, system=RAG_SYSTEM, max_tokens=1500)


def chat_model(messages, config) -> str:
    """marimo `mo.ui.chat` custom model: answer the latest user message."""
    return answer(messages[-1].content)
```

- [ ] **Step 2: Smoke-test retrieval and answering**

Run:
```bash
uv run python -c "from cmm.rag import answer; print(answer('What mental model shift did subagents require?'))"
```
Expected: a grounded paragraph citing changelog versions and/or blog URLs.

- [ ] **Step 3: Commit**

```bash
git add src/cmm/rag.py
git commit -m "feat: RAG retriever and Claude chat model"
```

---

## Task 10: The marimo notebook

**Files:**
- Create: `notebooks/analysis.py`

- [ ] **Step 1: Create the notebook skeleton with data loading**

Run: `uv run marimo edit notebooks/analysis.py` to open the editor, then build the cells below. Each fenced block is one marimo cell.

Cell — imports and data load:
```python
import marimo as mo
import polars as pl
import altair as alt

changelog = pl.read_parquet("data/processed/changelog.parquet")
blogs = pl.read_parquet("data/processed/blogs.parquet")
joins = pl.read_parquet("data/processed/joins.parquet")
embeddings = pl.read_parquet("data/processed/embeddings.parquet")
themes = pl.read_parquet("data/processed/themes.parquet")
codes = pl.read_parquet("data/processed/codes.parquet")
mo.md("# Claude Code Mental Models")
```

- [ ] **Step 2: Add Chart 1 — feature volume over time**

Cell:
```python
vol = (changelog.filter(pl.col("date").is_not_null())
       .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
       .group_by("month", "change_type").len())
chart_volume = alt.Chart(vol.to_pandas()).mark_bar().encode(
    x="month:T", y="len:Q", color="change_type:N"
).properties(title="Feature volume per month", width=700)
mo.ui.altair_chart(chart_volume)
```

- [ ] **Step 3: Add Chart 2 — churn (cumulative adds vs removals)**

Cell:
```python
churn = (changelog.filter(pl.col("date").is_not_null())
         .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
         .with_columns(pl.col("change_type")
                       .is_in(["deprecate", "remove"]).alias("is_removal"))
         .group_by("month", "is_removal").len().sort("month")
         .with_columns(pl.col("len").cum_sum().over("is_removal").alias("cumulative")))
chart_churn = alt.Chart(churn.to_pandas()).mark_line(point=True).encode(
    x="month:T", y="cumulative:Q",
    color=alt.Color("is_removal:N", title="removal/deprecation"),
).properties(title="Cumulative adds vs. deprecations+removals", width=700)
mo.ui.altair_chart(chart_churn)
```

- [ ] **Step 4: Add Chart 3 — blog coverage ratio over time**

Cell:
```python
cov = (joins.filter(pl.col("date").is_not_null())
       .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
       .with_columns((pl.col("impact_tier") == "narrated").alias("narrated"))
       .group_by("month").agg(pl.col("narrated").mean().alias("coverage")))
chart_cov = alt.Chart(cov.to_pandas()).mark_area(opacity=0.6).encode(
    x="month:T", y=alt.Y("coverage:Q", title="% releases narrated"),
).properties(title="Blog coverage ratio", width=700)
mo.ui.altair_chart(chart_cov)
```

- [ ] **Step 5: Add Chart 4 — mental-model emergence**

Cell:
```python
emergence = (themes.filter(pl.col("first_seen_date").is_not_null())
             .select("name", "first_seen_date")
             .with_columns(pl.col("first_seen_date").str.to_date()))
chart_emerge = alt.Chart(emergence.to_pandas()).mark_circle(size=200).encode(
    x="first_seen_date:T",
    y=alt.Y("name:N", title="mental model", sort="x"),
).properties(title="When each mental model first emerged", width=700)
mo.ui.altair_chart(chart_emerge)
```

- [ ] **Step 6: Add Chart 5 — cluster explorer**

Cell:
```python
mo.md("## Cluster explorer")
```
Cell:
```python
mo.ui.data_explorer(embeddings.select(
    "entry_id", "source", "date", "text", "cluster_label", "umap_x", "umap_y"
))
```

- [ ] **Step 7: Add the theme reference table**

Cell:
```python
mo.md("## Mental models reference")
```
Cell:
```python
mo.ui.data_explorer(themes.select(
    "name", "description", "first_seen_date", "member_codes"
))
```

- [ ] **Step 8: Add the RAG chat panel**

Cell:
```python
mo.md("## Ask the corpus")
```
Cell:
```python
from cmm.rag import chat_model
mo.ui.chat(chat_model, prompts=[
    "What mental model shift did subagents require?",
    "Which features were later deprecated or removed?",
    "How did context management change over the year?",
])
```

- [ ] **Step 9: Verify the notebook runs end-to-end**

Run: `uv run marimo run notebooks/analysis.py`
Expected: the app opens; all five charts render; the data explorers are interactive; the chat panel answers a question with citations. Close the app.

- [ ] **Step 10: Commit**

```bash
git add notebooks/analysis.py
git commit -m "feat: marimo notebook with five charts, explorers, and RAG chat"
```

---

## Task 11: Findings doc and README

**Files:**
- Create: `docs/findings.md`
- Modify: `README.md`

- [ ] **Step 1: Write `docs/findings.md`**

Open the notebook, read the charts, and write `docs/findings.md` with these sections, filled with the actual observed results (not placeholders):
- **Pace** — what the volume chart shows about release cadence.
- **Churn** — what got deprecated/removed, and what that implies users had to un-learn.
- **Narration** — whether blog coverage rose or fell as the tool matured.
- **Mental-model timeline** — the ordered list of emerged mental models with dates.
- **Where the methods disagree** — cases where HDBSCAN clusters and the LLM axial themes tell different stories.

- [ ] **Step 2: Write `README.md`**

```markdown
# Claude Code Mental Models

Analysis of how Claude Code's changelog and Anthropic's blogs reveal the
evolving mental models of Claude Code use. See
`docs/superpowers/specs/2026-05-20-claude-mental-models-design.md`.

## Run the pipeline

```bash
uv sync
export ANTHROPIC_API_KEY=...
uv run python -m cmm.collect_changelog
uv run python -m cmm.collect_blogs
uv run python -m cmm.tag_and_join
uv run python -m cmm.embed_cluster
uv run python -m cmm.thematic_coding
uv run marimo run notebooks/analysis.py
```

All network and LLM calls are cached in `data/cache/`.
```

- [ ] **Step 3: Run the full test suite**

Run: `uv run pytest -v`
Expected: all parser + cache tests PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/findings.md README.md
git commit -m "docs: findings and README"
```

---

## Phase 2 hook (not implemented now)

The `personal_artifact` table from the spec is intentionally unused in Phase 1.
Phase 2 gets its own spec: populate it with the user's ~100 projects (date +
features used) and overlay an adoption timeline against the emergence chart.
