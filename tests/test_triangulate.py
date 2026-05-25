import pytest
from cmm.triangulate import confidence_tier


def test_confidence_tier_high_when_both_corroborate():
    assert confidence_tier(True, True) == "high"


def test_confidence_tier_provisional_when_one_corroborates():
    assert confidence_tier(True, False) == "provisional"
    assert confidence_tier(False, True) == "provisional"


def test_confidence_tier_bottom_up_only_when_neither():
    assert confidence_tier(False, False) == "bottom_up_only"


from cmm.triangulate import extractive_violations


def test_extractive_violations_none_when_all_words_grounded():
    # every salient word (>4 chars, non-stopword) appears verbatim in a member
    desc = "Users learned to manage the context window"
    member_texts = ["Added context window compaction", "manage long sessions"]
    assert extractive_violations(desc, member_texts) == []


def test_extractive_violations_flags_ungrounded_salient_word():
    desc = "Users adopted quantum telepathy for delegation"
    member_texts = ["Added subagent delegation support"]
    viol = extractive_violations(desc, member_texts)
    assert "quantum" in viol and "telepathy" in viol


import polars as _pl
from cmm.triangulate import label_unassigned

MAINTENANCE = "Maintenance / no conceptual shift"


def test_label_unassigned_labels_empty_theme_lists():
    codes = _pl.DataFrame({
        "entry_id": ["a", "b", "c"],
        "source": ["changelog"] * 3,
        "date": ["2025-03-01"] * 3,
        "themes": [["T1"], [], []],
    })
    out = label_unassigned(codes)
    assert out.filter(_pl.col("entry_id") == "a")["themes"].to_list()[0] == ["T1"]
    assert out.filter(_pl.col("entry_id") == "b")["themes"].to_list()[0] == [MAINTENANCE]
