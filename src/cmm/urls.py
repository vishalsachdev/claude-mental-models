# src/cmm/urls.py
"""Build canonical, click-throughable URLs for corpus entries.

Blogs already carry an absolute URL as their `entry_id`. Changelog entries
need a URL synthesized from the version heading. The GitHub-rendered
CHANGELOG.md uses GFM-slugged anchors on each `## <version>` heading; for a
heading like `## 2.1.150` the slug strips dots and lowercases, producing
`21150`. The browser will scroll to that section.
"""
import re

CHANGELOG_BASE = "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md"


def github_slug(text: str) -> str:
    """Approximate GitHub's GFM heading-slug algorithm.

    Lowercase, replace whitespace runs with `-`, then drop everything that
    isn't alphanumeric or hyphen. Good enough for version strings like
    `2.1.150`, `0.2.1`, or `2.0.0-rc1`.
    """
    s = text.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    return s


def entry_url(entry_id: str, source: str, version: str | None) -> str:
    """Return the best canonical URL for one corpus entry.

    - blog → `entry_id` (already an absolute URL)
    - changelog → CHANGELOG.md anchored to the version section
    - anything else → empty string
    """
    if source == "blog":
        return entry_id
    if source == "changelog" and version:
        return f"{CHANGELOG_BASE}#{github_slug(version)}"
    return ""
