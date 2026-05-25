# src/cmm/collect_blogs.py
"""Crawl Anthropic news/engineering posts (broad collection)."""
import json
import re
import time
from pathlib import Path

import httpx

from cmm.cache import cached_call
from cmm.render_blogs import render_post

INDEX_URLS = [
    "https://www.anthropic.com/news",
    "https://www.anthropic.com/engineering",
]
WINDOW_START = "2025-02-01"  # Claude Code launch month; lower bound for posts
# Matches post links like /news/<slug>, /engineering/<slug>, /research/<slug>.
HREF_RE = re.compile(r'href="(/(?:news|engineering|research)/[a-z0-9][a-z0-9-]+)"')


def extract_post_links(html: str, base: str) -> list[str]:
    """Return a deduped, absolute list of post URLs found in an index page."""
    seen: dict[str, None] = {}
    for path in HREF_RE.findall(html):
        seen.setdefault(base.rstrip("/") + path, None)
    return list(seen)


def fetch(url: str, client: httpx.Client, retries: int = 3) -> str:
    """GET a URL, retrying with exponential backoff.

    Raises RuntimeError after `retries` failures — fail loudly, never return
    a partial/empty body silently.
    """
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = client.get(url, follow_redirects=True, timeout=30)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last}")


def crawl_index(index: str, client: httpx.Client, max_pages: int = 25) -> list[str]:
    """Collect post links from an index and all its paginated pages.

    Tries `<index>?page=N` for N=1.. until a page yields no new links.
    """
    links: dict[str, None] = {}
    for page in range(1, max_pages + 1):
        page_url = index if page == 1 else f"{index}?page={page}"
        html = cached_call(f"index::{page_url}", lambda u=page_url: fetch(u, client))
        new = [u for u in extract_post_links(html, "https://www.anthropic.com")
               if u not in links]
        if not new:
            break
        for u in new:
            links[u] = None
    return list(links)


def extract_post(html: str) -> dict:
    """Extract title, date, and body text from a post page.

    Title from <h1>; date from a <time datetime> or an ISO date in the page;
    body as visible text with tags stripped.
    """
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""
    # Look in order: explicit <time datetime=…>, then Next.js SSR JSON.
    # anthropic.com rendered pages store the publish date as `publishedOn`
    # in an escaped-JSON SSR blob (no <time> tag). Prefer that field over
    # `_createdAt`, which is the CMS creation date and can be months earlier
    # than the actual publish date.
    date_m = (
        re.search(r'datetime="(\d{4}-\d{2}-\d{2})', html)
        or re.search(r'publishedOn\\?":\s*\\?"(\d{4}-\d{2}-\d{2})', html)
        or re.search(r'_createdAt\\?":\s*\\?"(\d{4}-\d{2}-\d{2})', html)
        or re.search(r"(\d{4}-\d{2}-\d{2})", html)
    )
    date = date_m.group(1) if date_m else None
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return {"title": title, "date": date, "body": body}


def collect(out: Path = Path("data/raw/blogs.json")) -> Path:
    """Crawl paginated index pages, fetch each post, filter to the window.

    Posts dated before WINDOW_START are dropped. Posts with no parseable date
    are surfaced as a warning and KEPT (per spec: flag, never silently drop).
    """
    posts: list[dict] = []
    with httpx.Client() as client:
        links: list[str] = []
        for index in INDEX_URLS:
            links += crawl_index(index, client)
        links = list(dict.fromkeys(links))
        print(f"Found {len(links)} post links")
        for url in links:
            html = cached_call(f"post::{url}", lambda u=url: fetch(u, client))
            post = extract_post(html)
            post["url"] = url
            post = render_post(post)  # A2: overlay headless-rendered date/body
            posts.append(post)

    missing = [p["url"] for p in posts if not p["date"]]
    if missing:
        print(f"WARNING: {len(missing)} posts have no parsed date (kept): {missing}")
    kept = [p for p in posts if p["date"] is None or p["date"] >= WINDOW_START]
    print(f"Kept {len(kept)}/{len(posts)} posts in window (>= {WINDOW_START})")

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kept, indent=2))
    print(f"Wrote {len(kept)} posts to {out}")
    return out


if __name__ == "__main__":
    collect()
