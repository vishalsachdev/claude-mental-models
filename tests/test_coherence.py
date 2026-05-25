from cmm.coherence import coherence_row


def test_coherence_row_concentrated_theme_scores_high():
    # all 10 entries in one cluster -> spread 1, share 1.0, score 1.0
    row = coherence_row("T1", cluster_labels=[3] * 10)
    assert row["cluster_spread"] == 1
    assert row["top_cluster"] == 3
    assert row["top_cluster_share"] == 1.0
    assert row["coherence_score"] == 1.0


def test_coherence_row_smeared_theme_scores_low():
    # evenly across 5 clusters -> share 0.2
    row = coherence_row("T2", cluster_labels=[0, 1, 2, 3, 4] * 2)
    assert row["cluster_spread"] == 5
    assert row["top_cluster_share"] == 0.2
    assert row["coherence_score"] < 0.5


def test_coherence_row_ignores_noise_cluster():
    row = coherence_row("T3", cluster_labels=[-1, -1, 7, 7, 7])
    assert row["top_cluster"] == 7
    assert row["top_cluster_share"] == 1.0  # noise excluded from denominator
