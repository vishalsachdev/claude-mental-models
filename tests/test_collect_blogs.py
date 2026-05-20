from pathlib import Path
from cmm.collect_blogs import extract_post_links

FIXTURE = Path(__file__).parent.parent / "data" / "fixtures" / "news_index.html"


def test_extract_post_links_finds_news_urls():
    links = extract_post_links(FIXTURE.read_text(), base="https://www.anthropic.com")
    assert len(links) > 0
    assert all(u.startswith("https://www.anthropic.com/") for u in links)
    assert all("/news/" in u or "/engineering/" in u or "/research/" in u for u in links)
    assert len(links) == len(set(links))  # deduped
