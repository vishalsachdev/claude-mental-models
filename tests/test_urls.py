from cmm.urls import entry_url, github_slug


def test_github_slug_strips_dots():
    assert github_slug("2.1.150") == "21150"
    assert github_slug("0.2.1") == "021"


def test_github_slug_keeps_hyphens():
    assert github_slug("2.0.0-rc1") == "200-rc1"


def test_entry_url_blog_returns_entry_id_directly():
    assert entry_url(
        "https://www.anthropic.com/news/foo", "blog", None,
    ) == "https://www.anthropic.com/news/foo"


def test_entry_url_changelog_anchors_version_section():
    assert entry_url(
        "d3cd5bcb0010", "changelog", "2.1.150",
    ) == "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21150"


def test_entry_url_falls_back_to_empty():
    assert entry_url("x", "other", None) == ""
    assert entry_url("x", "changelog", None) == ""
