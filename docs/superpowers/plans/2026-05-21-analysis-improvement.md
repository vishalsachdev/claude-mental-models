# Analysis Improvement Plan — Methodological Rebuild

**Date:** 2026-05-21
**Status:** Draft — for review
**Context:** The v1 pipeline shipped and is merged to `main`. A three-model
council reviewed its methodology; `docs/methodology.md` records the limitations.
This plan addresses them with a methodological rebuild.

---

## Goal

Turn the analysis from *"a well-grounded description with a plausible but
unvalidated interpretive story laid over it"* into an analysis whose
interpretive layer is **triangulated, evidence-derived, and falsifiable** —
without losing what already works (the descriptive layer).

## Problems being fixed (with provenance)

| # | Problem | Source |
|---|---------|--------|
| P1 | The 36 embedding clusters and 10 LLM themes were never reconciled — the "quantitative skeleton" did no validation work | Council consensus; methodology §3 |
| P2 | Themes are imposed top-down from a 150-entry (5%) sample — narrative confirmation bias | Council; Gemini |
| P3 | Theme descriptions blend corpus evidence with the model's training knowledge — more confident than the data | methodology §4; Claude R1 |
| P4 | The instrument is Claude; the analysis is not independent of its subject | methodology §4 (reflexivity) |
| P5 | 33% of entries assigned to no theme — taxonomy does not fully fit | Council; methodology §4 |
| P6 | Two themes (27, 41 entries) presented as equal-weight peers of themes 10–16× larger | methodology §4 |
| P7 | `all-MiniLM-L6-v2` + aggressive 5-D UMAP may produce "lexical collisions," not semantic clusters | Gemini R2 |
| P8 | Corpus gaps: depth-1000 clone clamps `first_seen` dates; blog corpus thin (14/32 undated, JS-SPA statically scraped) | methodology §4 |
| P9 | "Mental models developers held" overreaches what the changelog can evidence | Council consensus #1 |

## Non-goals

- Rebuilding the descriptive layer (volume/churn/change-type charts) — it is
  sound, leave it.
- Phase 2 personal-artifact overlay (separate, still deferred).

---

## Workstreams

Three groups, run in order — Group A changes the inputs everything else
consumes, Group B rebuilds the theme layer, Group C reconciles and presents.

### Group A — Corpus & representation

Everything downstream depends on these; do them first.

**A1. Full-depth changelog history.** Re-clone `anthropics/claude-code` without
`--depth 1000` (or deep enough that the earliest `## version` heading is
captured). Re-run `version_dates`. Verify no theme's `first_seen_date` sits
exactly on the clone horizon. *Fixes P8.*

**A2. Render the blog corpus.** Replace the static `httpx` scrape with a
headless-browser render (the repo already has `claude-in-chrome` / agent-browser
available) so JS-injected post bodies and `<time>` dates are captured. Target:
recover dates for most of the 14 undated posts and fuller body text. Keep the
±14-day join. *Fixes P8.*

**A3. Stronger embeddings.** Replace `all-MiniLM-L6-v2` with a higher-capacity
sentence-transformer (e.g. `all-mpnet-base-v2` or a current top-MTEB model).
Re-fit HDBSCAN. Cluster on a less aggressive UMAP reduction (10–15 components,
not 5) or tune `min_cluster_size`/`min_samples`. Record the new cluster count
and inspect 5 clusters by hand for semantic (not lexical) coherence. *Fixes P7.*

### Group B — Triangulated theme layer

The core rebuild. The theme layer is currently one top-down pass; replace it
with **three independent derivations that are then compared.**

**B1. Bottom-up themes from clusters.** For each HDBSCAN cluster, send the LLM a
sample of that cluster's member entries and ask for the *latent user assumption*
those features share. This yields ~N cluster-grounded mini-themes derived from
the full data distribution, not a 5% sample. *Fixes P2.*

**B2. Keep the top-down pass** (current `discover_themes`) as the second
derivation — it is still useful as a high-level scheme.

**B3. Independent-model derivation.** Re-run theme discovery + assignment with a
non-Claude model (GPT-5.5 via `codex exec`, or Gemini CLI). Same prompts, same
corpus. *Fixes P4.*

**B4. Triangulate.** Reconcile B1/B2/B3 into a final theme set: themes that
appear in all three derivations are **high-confidence**; themes in one or two
are **provisional**; tag each theme with which derivations support it. This
replaces the single unvalidated pass with a cross-validated one.

**B5. Descriptions from member entries.** Once themes are final, regenerate each
description from a sample of that theme's *actually assigned* member entries —
never from the discovery sample. Add an extractive check: every feature named in
a description must appear in ≥1 assigned entry. *Fixes P3.*

**B6. Handle the unassigned.** Analyze the no-theme set. Add an explicit
`Maintenance / no conceptual shift` category so the residual is an honest
labelled bucket, not a silent gap; if a coherent extra theme emerges from the
residual, add it. Target: the truly-unexplained residual is reported, not
hidden. *Fixes P5.*

**B7. Theme tiering.** Present themes in tiers by evidence weight (entry_count +
number of supporting derivations). The two sub-1.5% themes go to a clearly
labelled "minor / emerging" tier or merge into a neighbour. *Fixes P6.*

### Group C — Reconciliation & honest presentation

**C1. Cluster↔theme reconciliation as a first-class output.** Compute the
cluster×theme cross-tab in the pipeline (not after the fact); write a
`coherence.parquet` with, per theme: cluster spread, top-cluster concentration,
and a coherence score. *Fixes P1.*

**C2. Notebook: coherence view.** Add a cluster×theme heatmap and a per-theme
confidence badge (high / provisional, from B4 + C1). The cluster explorer gains
a "bottom-up theme" column alongside the top-down one.

**C3. Claim reframing.** Sweep the notebook, generated descriptions, and
`findings.md` to replace "mental models developers held" with "competencies /
expectations the tool's surface increasingly demanded." Keep "mental models"
only as an explicitly-labelled organizing lens. *Fixes P9.*

**C4. Manual audit.** Human-audit a stratified sample (~40 items): high-
confidence theme matches, no-theme items, and cluster/theme disagreements.
Record agreement rate in `findings.md`. This is the one irreducibly non-
automated check. *Council (Codex) recommendation.*

---

## Sequencing & dependencies

```
A1 ─┐
A2 ─┼─► A3 ─► B1 ─┐
    │         B2 ─┼─► B4 ─► B5 ─► B6 ─► B7 ─► C1 ─► C2 ─► C3 ─► C4
    │   B3 ──────┘
```

A1/A2 are independent and can run in parallel. A3 needs the corpus settled.
B1/B2/B3 are independent once A3 is done. B4 gates the rest of Group B.

## What "done" looks like

- Every theme carries: supporting derivations (of 3), entry_count, a coherence
  score vs. the embedding clusters, and a confidence tier.
- No theme description names a feature absent from its member entries.
- The unassigned residual is a labelled category with a reported size, not a
  silent 33% gap.
- `findings.md` reports the manual-audit agreement rate and the cross-model
  theme overlap.
- The notebook shows the coherence heatmap; claim wording is downgraded
  throughout.
- `docs/methodology.md` is updated to describe the triangulated design.

## Open questions for review

1. Independent model for B3 — GPT-5.5 (`codex`), Gemini, or both?
2. B6 — is an explicit "Maintenance" category enough, or should the residual get
   its own short analysis section?
3. Effort ceiling — A2 (headless blog render) is the most open-ended task; is it
   worth it for a 32→maybe-60-post corpus, or defer A2 and accept the thin blog
   layer?

---

## Process

This is a methodology rebuild with real design decisions. Recommended path:
promote this to a spec via `superpowers:brainstorming`, run it past the Codex
Plan Reviewer (REJECT→fix→APPROVE), then execute via
`superpowers:subagent-driven-development` — the same workflow that produced v1.
