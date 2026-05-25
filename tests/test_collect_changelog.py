import pytest
from pathlib import Path
from cmm.collect_changelog import parse_changelog, classify_change

FIXTURE = Path(__file__).parent.parent / "data" / "fixtures" / "changelog_sample.md"


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


def test_parse_changelog_raises_on_bullet_before_heading():
    with pytest.raises(ValueError):
        parse_changelog("- orphan bullet with no heading")


def test_parse_changelog_raises_on_no_entries():
    with pytest.raises(ValueError):
        parse_changelog("# Changelog\n\nNo bullets here.\n")


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
