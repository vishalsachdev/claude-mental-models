import pytest
from cmm.triangulate import confidence_tier


def test_confidence_tier_high_when_both_corroborate():
    assert confidence_tier(True, True) == "high"


def test_confidence_tier_provisional_when_one_corroborates():
    assert confidence_tier(True, False) == "provisional"
    assert confidence_tier(False, True) == "provisional"


def test_confidence_tier_bottom_up_only_when_neither():
    assert confidence_tier(False, False) == "bottom_up_only"
