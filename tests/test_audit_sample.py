from cmm.audit_sample import stratum_for


def test_stratum_for_maintenance():
    assert stratum_for(["Maintenance / no conceptual shift"],
                       theme_tier="high", coherent=True) == "residual"


def test_stratum_for_high_confidence_match():
    assert stratum_for(["T1"], theme_tier="high", coherent=True) == "high_confidence"


def test_stratum_for_disagreement():
    # assigned a theme but the entry sits in a cluster the theme doesn't own
    assert stratum_for(["T1"], theme_tier="high", coherent=False) == "disagreement"


def test_stratum_for_provisional_match():
    # coherent, but the theme is not high-confidence -> its own stratum
    assert stratum_for(["T1"], theme_tier="provisional", coherent=True) == "provisional_match"
