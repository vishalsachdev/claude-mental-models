"""Headless-browser render of blog post pages (A2).

anthropic.com posts are a JS SPA; the static httpx body is a shell. This
renders each post URL once via the agent-browser CLI and re-extracts the
title/date/body with collect_blogs.extract_post. Timeboxed: one pass, no retry.
"""
import subprocess

from cmm.cache import cached_call

_RENDER_TIMEOUT = 60  # seconds; one shot, no retry per the spec's timebox


def render_html(url: str) -> str:
    """Return fully-rendered HTML for ``url`` via agent-browser. Cached.

    agent-browser is a stateful CLI: ``open`` navigates the persistent session
    to the URL, then ``get html body`` returns the rendered body HTML on
    stdout. The ``get`` subcommand requires a selector, so we pass ``body``
    (the full document body, which is what ``extract_post`` parses).

    On any failure returns "" — the caller falls back to the static body.
    """

    def run() -> str:
        try:
            nav = subprocess.run(
                ["agent-browser", "open", url],
                capture_output=True, text=True, timeout=_RENDER_TIMEOUT,
            )
            if nav.returncode != 0:
                return ""
            proc = subprocess.run(
                ["agent-browser", "get", "html", "body"],
                capture_output=True, text=True, timeout=_RENDER_TIMEOUT,
            )
            return proc.stdout if proc.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    return cached_call(f"render::{url}", run)


def merge_rendered(static: dict, rendered: dict) -> dict:
    """Overlay rendered title/date/body onto the static post, field by field.

    A rendered field wins only if it is non-empty; otherwise the static value
    is kept. ``url`` always comes from ``static``.
    """
    out = dict(static)
    for field in ("title", "date", "body"):
        val = rendered.get(field)
        if val:
            out[field] = val
    return out


def render_post(static_post: dict) -> dict:
    """Render one post URL and merge the result over the static post dict."""
    from cmm.collect_blogs import extract_post  # lazy: avoids circular import

    html = render_html(static_post["url"])
    if not html:
        return static_post
    return merge_rendered(static_post, extract_post(html))
