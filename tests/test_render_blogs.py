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
