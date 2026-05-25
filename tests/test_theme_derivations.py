import polars as pl
from cmm.theme_derivations import cluster_samples


def test_cluster_samples_excludes_noise_and_caps_sample():
    df = pl.DataFrame({
        "entry_id": [str(i) for i in range(25)],
        "text": [f"entry {i}" for i in range(25)],
        "cluster_label": [-1] * 5 + [0] * 12 + [1] * 8,
    })
    samples = cluster_samples(df, sample_size=10)
    assert set(samples) == {0, 1}                 # noise cluster -1 dropped
    assert len(samples[0]) == 10                  # capped at sample_size
    assert len(samples[1]) == 8                   # smaller cluster kept whole
