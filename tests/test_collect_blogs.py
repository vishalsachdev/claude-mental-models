from pathlib import Path
from cmm.collect_blogs import extract_post_links

FIXTURE = Path(__file__).parent.parent / "data" / "fixtures" / "news_index.html"


def test_extract_post_links_finds_news_urls():
    links = extract_post_links(FIXTURE.read_text(), base="https://www.anthropic.com")
    assert len(links) > 0
    assert all(u.startswith("https://www.anthropic.com/") for u in links)
    assert all("/news/" in u or "/engineering/" in u or "/research/" in u for u in links)
    assert len(links) == len(set(links))  # deduped


from cmm.collect_blogs import extract_post, parse_visible_date


def test_parse_visible_date_accepts_full_and_abbreviated_months():
    assert parse_visible_date("May 19, 2026") == "2026-05-19"
    assert parse_visible_date("Aug 27, 2026") == "2026-08-27"
    assert parse_visible_date("September 3, 2025") == "2025-09-03"
    assert parse_visible_date("not a date") is None


def test_extract_post_reads_visible_date_from_current_markup():
    # Positive control: shape of anthropic.com markup as of 2026-08-29, with
    # the decoy `siteSettings._createdAt` that used to win the fallback.
    html = (
        '<html><body><h1>Widening the conversation about frontier AI</h1>'
        '<div class="body-3 agate">May 19, 2026</div>'
        '<script>self.__next_f.push(["siteSettings\\":{\\"_createdAt\\":'
        '\\"2023-11-03T16:49:36Z\\"}"])</script></body></html>'
    )
    post = extract_post(html)
    assert post["date"] == "2026-05-19"
    assert post["title"] == "Widening the conversation about frontier AI"


def test_extract_post_keeps_legacy_published_on_field():
    html = '<h1>Old post</h1><script>{\\"publishedOn\\":\\"2025-11-24T00:00:00Z\\"}</script>'
    assert extract_post(html)["date"] == "2025-11-24"


def test_extract_post_returns_none_rather_than_created_at_decoy():
    html = '<h1>Undated</h1><script>{"_createdAt":"2023-11-03T16:49:36Z"}</script>'
    assert extract_post(html)["date"] is None


from cmm.collect_blogs import apply_date_overrides, DATE_OVERRIDES


def test_date_override_corrects_best_practices_post():
    url = "https://www.anthropic.com/engineering/claude-code-best-practices"
    assert url in DATE_OVERRIDES
    posts = apply_date_overrides([{"url": url, "date": "2026-05-14"},
                                  {"url": "https://x/other", "date": "2026-01-01"}])
    assert posts[0]["date"] == "2025-04-18"
    assert posts[1]["date"] == "2026-01-01"
