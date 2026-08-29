# src/cmm/collect_blogs.py
"""Crawl Anthropic news/engineering posts (broad collection)."""
import json
import re
import time
from datetime import date, datetime
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
# Since ~2026-08 anthropic.com renders the publish date as visible text
# (`<div class="body-3 agate">Aug 27, 2026</div>`) and no longer ships a
# `publishedOn` SSR field. Month may be full ("May") or abbreviated ("Aug").
VISIBLE_DATE_RE = re.compile(r'class="body-3 agate">\s*([A-Z][a-z]+ \d{1,2}, \d{4})\s*<')
# /engineering posts render the same visible date without the agate class;
# take the first "Mon D, YYYY" text node only after the h1 (so a related-post
# card above the title cannot win). Control: how-we-contain-claude -> 2026-05-25.
ANY_VISIBLE_DATE_RE = re.compile(r'>\s*([A-Z][a-z]{2,8} \d{1,2}, \d{4})\s*<')


# Manual date corrections with provenance. Applied in collect() AFTER
# extraction, so a fixed extractor never silently re-breaks them.
DATE_OVERRIDES: dict[str, tuple[str, str]] = {
    "https://www.anthropic.com/engineering/claude-code-best-practices": (
        "2025-04-18",
        "URL now 302s to code.claude.com/docs/en/best-practices; the only "
        "date on that page is a docs `lastModified` (2026-05-14), which the "
        "v2 collector's bare-date fallback took as the publish date. The "
        "engineering post was published 2025-04-18; Wayback's earliest "
        "capture is 2025-04-20 (checked 2026-08-29).",
    ),
}


def apply_date_overrides(posts: list[dict]) -> list[dict]:
    """Overwrite `date` for URLs in DATE_OVERRIDES; log each application."""
    for post in posts:
        if post["url"] in DATE_OVERRIDES:
            new_date, why = DATE_OVERRIDES[post["url"]]
            if post.get("date") != new_date:
                print(f"DATE OVERRIDE {post['url']}: {post.get('date')} -> "
                      f"{new_date} ({why[:60]}...)")
            post["date"] = new_date
    return posts


def parse_visible_date(text: str) -> str | None:
    """'Aug 27, 2026' / 'May 19, 2026' -> ISO date, else None."""
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


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
        # Cache key carries the collection date: an undated key served the
        # May-2026 front page forever, so an Aug refresh found 0 new posts
        # (found 2026-08-29). Same-day re-runs still hit the cache.
        key = f"index::{page_url}::{date.today().isoformat()}"
        html = cached_call(key, lambda u=page_url: fetch(u, client))
        new = [u for u in extract_post_links(html, "https://www.anthropic.com")
               if u not in links]
        if not new:
            if page == 2:
                # KNOWN BLIND SPOT (2026-08-29): `?page=2` now returns the same
                # links as page 1, so only the most recent ~11 /news posts are
                # discoverable. Posts that scrolled off the index between two
                # collection runs are never seen (for the Aug-2026 refresh:
                # anything published 2026-05-20 .. 2026-06-29).
                print(f"WARNING: {index} does not paginate — only "
                      f"{len(links)} links visible; older uncached posts are "
                      "a blind spot")
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
    # Look in order: explicit <time datetime=…>, the visible "Mon D, YYYY"
    # text (current markup), then the legacy `publishedOn` SSR field (pages
    # cached before 2026-08). There is deliberately NO `_createdAt` / bare-
    # date fallback: on current markup those match `siteSettings._createdAt`
    # (2023-11-03) for every post, and a confident wrong date is worse than
    # None, which collect() surfaces as a warning.
    date: str | None = None
    m = re.search(r'datetime="(\d{4}-\d{2}-\d{2})', html)
    if m:
        date = m.group(1)
    if not date:
        m = VISIBLE_DATE_RE.search(html)
        date = parse_visible_date(m.group(1)) if m else None
    if not date:
        m = re.search(r'publishedOn\\?":\s*\\?"(\d{4}-\d{2}-\d{2})', html)
        date = m.group(1) if m else None
    if not date and title_m:
        m = ANY_VISIBLE_DATE_RE.search(html, title_m.end())
        date = parse_visible_date(m.group(1)) if m else None
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
    out = Path(out)
    # The index only exposes recent posts (see crawl_index); every URL from a
    # previous collection must be carried forward or the corpus silently
    # shrinks to whatever is on the front page today.
    previous = [p["url"] for p in json.loads(out.read_text())] if out.exists() else []
    with httpx.Client() as client:
        links: list[str] = []
        for index in INDEX_URLS:
            links += crawl_index(index, client)
        links = list(dict.fromkeys(links + previous))
        print(f"Found {len(links)} post links "
              f"({len(links) - len(previous)} not in previous collection)")
        for url in links:
            html = cached_call(f"post::{url}", lambda u=url: fetch(u, client))
            post = extract_post(html)
            post["url"] = url
            post = render_post(post)  # A2: overlay headless-rendered date/body
            posts.append(post)

    posts = apply_date_overrides(posts)
    missing = [p["url"] for p in posts if not p["date"]]
    if missing:
        print(f"WARNING: {len(missing)} posts have no parsed date (kept): {missing}")
    kept = [p for p in posts if p["date"] is None or p["date"] >= WINDOW_START]
    print(f"Kept {len(kept)}/{len(posts)} posts in window (>= {WINDOW_START})")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kept, indent=2))
    print(f"Wrote {len(kept)} posts to {out}")
    return out


if __name__ == "__main__":
    collect()
