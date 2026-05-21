# Methodological Rebuild — Design Spec

**Date:** 2026-05-21
**Status:** Spec — for review
**Supersedes:** `docs/superpowers/plans/2026-05-21-analysis-improvement.md` (the
draft plan that seeded this spec; this document is the authoritative version).

---

## Goal

Turn the analysis from *"a well-grounded description with a plausible but
unvalidated interpretive story laid over it"* into an analysis whose
interpretive layer is **triangulated, evidence-derived, and falsifiable** —
without losing the descriptive layer that already works.

## Problems being fixed (provenance)

| # | Problem | Source |
|---|---------|--------|
| P1 | The 36 embedding clusters and 10 LLM themes were never reconciled | Council; methodology §3 |
| P2 | Themes imposed top-down from a 150-entry (5%) sample — confirmation bias | Council; Gemini |
| P3 | Theme descriptions blend corpus evidence with the model's training knowledge | methodology §4; Claude R1 |
| P4 | The instrument is Claude; the analysis is not independent of its subject | methodology §4 (reflexivity) |
| P5 | 33% of entries assigned to no theme | Council; methodology §4 |
| P6 | Two tiny themes (27, 41 entries) presented as equal-weight peers | methodology §4 |
| P7 | `all-MiniLM-L6-v2` + aggressive 5-D UMAP may produce lexical, not semantic, clusters | Gemini R2 |
| P8 | Corpus gaps: depth-1000 clone clamps dates; blog corpus thin (14/32 undated, JS-SPA) | methodology §4 |
| P9 | "Mental models developers held" overreaches what the changelog can evidence | Council #1 |

## Non-goals

- Rebuilding the descriptive layer (volume/churn/change-type charts) — it is
  sound, leave it.
- Phase 3 personal-artifact overlay — separate, still deferred.

## Scope & structure

One spec, one implementation plan, executed **group by group** (A → B → C) with
a review checkpoint between groups. Not decomposed into sub-projects: the 14
tasks form one coherent dependency chain over shared artifacts.

---

## Resolved design decisions (from brainstorm, 2026-05-21)

1. **Independent model (B3)** → **GPT-5.5**, invoked via **`codex exec` headless**
   (mirrors the `claude` CLI pattern in `src/cmm/llm.py`; no API key).
2. **Unassigned residual (B6)** → an explicit labelled `Maintenance / no
   conceptual shift` category **and** its own short analysis section in the
   notebook + `findings.md` — not a silent bucket.
3. **Blog re-scrape (A2)** → **yes, timeboxed**: a single headless render pass,
   accept whatever date recovery it yields, no iteration.
4. **Triangulation method (B4)** → **anchor-on-B1**: the consolidated bottom-up
   theme set is canonical; B2 and B3 are checked per-theme for corroboration.
5. **B1 granularity** → add a **B1.5 consolidation pass**: per-cluster
   mini-themes are consolidated into ~10–15 anchor themes before B4.

---

## Workstreams

Three groups, run in order. Group A changes the inputs everything else
consumes; Group B rebuilds the theme layer; Group C reconciles and presents.

### Group A — Corpus & representation

**A1. Full-depth changelog history.** Re-clone `anthropics/claude-code` without
`--depth 1000` (deep enough that the earliest `## version` heading is captured).
Re-run `version_dates`. Assert no theme's `first_seen_date` sits exactly on the
clone horizon. *Fixes P8.*

**A2. Render the blog corpus.** Replace the static `httpx` scrape with a
headless-browser render (`claude-in-chrome` / agent-browser) so JS-injected post
bodies and `<time>` dates are captured. Keep the ±14-day join.
**Timeboxed — one render pass; accept partial date recovery; do not iterate.**
Whatever dates remain unrecovered become a documented limitation. *Fixes P8.*

**A3. Stronger embeddings.** Replace `all-MiniLM-L6-v2` with a higher-capacity
sentence-transformer (`all-mpnet-base-v2` or a current top-MTEB model). Re-fit
HDBSCAN on a less aggressive UMAP reduction (10–15 components, not 5); tune
`min_cluster_size` / `min_samples`. Record the new cluster count and hand-inspect
5 clusters for semantic (not lexical) coherence. *Fixes P7.*

A1/A2 are independent and run in parallel. A3 follows once the corpus is settled.

### Group B — Triangulated theme layer

The theme layer is currently one top-down pass. Replace it with **three
independent derivations, then anchored triangulation.**

**B1. Bottom-up mini-themes from clusters.** For each HDBSCAN cluster, send the
LLM a sample of that cluster's member entries and ask for the *latent user
assumption* those features share. Yields ~30–40 cluster-grounded mini-themes,
each tied to its source cluster. *Fixes P2.*

**B1.5. Consolidation pass.** A second LLM pass groups the ~30–40 mini-themes
into ~10–15 consolidated themes. Each consolidated theme records which clusters
feed it. **This consolidated set is the canonical anchor for B4.** The
cluster → mini-theme → theme provenance chain is preserved and feeds C1.

**B2. Top-down pass.** Keep the current `discover_themes` pass as the second
derivation — still useful as a high-level scheme.

**B3. Independent-model derivation.** Re-run theme discovery + assignment with
**GPT-5.5 via `codex exec` headless**. Same prompts, same corpus.
*Implementation caveat:* `codex exec` is an agentic CLI, not a JSON endpoint.
The B3 wrapper MUST force structured output (instruct the model to write JSON to
a named file; parse robustly with a schema check) and MUST cache the result in
`data/cache/`. Pin the model identifier and commit the cached output so B3 never
re-runs nondeterministically. *Fixes P4.*

**B4. Triangulate (anchor-on-B1).** For each B1.5 consolidated theme, the
independent model (GPT-5.5) judges two per-pair questions: *is this theme
corroborated by a B2 theme?* and *is it corroborated by a B3 theme?* — each with
a one-line rationale. The two booleans yield the confidence tier:

- corroborated by **both** B2 and B3 → **high-confidence**
- corroborated by **one** → **provisional**
- corroborated by **neither** → **B1-only** (data-derived but uncorroborated)

This replaces the single unvalidated pass with a cross-validated one and avoids
unstable many-to-many theme matching.

**B5. Descriptions from member entries.** Once themes are final, regenerate each
description from a sample of that theme's *actually assigned* member entries —
never from the discovery sample. Add an extractive check: every feature named in
a description must appear in ≥1 assigned entry. *Fixes P3.*

**B6. Handle the unassigned.** Add an explicit `Maintenance / no conceptual
shift` labelled category so the residual is an honest labelled bucket. **In
addition**, give the residual its own short analysis section in the notebook and
`findings.md` (size, composition, why these entries resist the taxonomy). If a
coherent extra theme emerges from the residual, add it. *Fixes P5.*

**B7. Theme tiering.** Present themes in tiers by evidence weight (entry_count +
number of supporting derivations). The two sub-1.5% themes go to a clearly
labelled "minor / emerging" tier or merge into a neighbour. *Fixes P6.*

### Group C — Reconciliation & honest presentation

**C1. Cluster↔theme reconciliation as a first-class output.** Compute the
cluster×theme cross-tab in the pipeline (not after the fact); write
`coherence.parquet` with, per theme: cluster spread, top-cluster concentration,
and a coherence score. The B1.5 provenance chain feeds this directly. *Fixes P1.*

**C2. Notebook: coherence view.** Add a cluster×theme heatmap and a per-theme
confidence badge (high / provisional / B1-only, from B4 + C1). The cluster
explorer gains a "bottom-up theme" column alongside the top-down one.

**C3. Claim reframing.** Sweep the notebook, generated descriptions, and
`findings.md` to replace "mental models developers held" with "competencies /
expectations the tool's surface increasingly demanded." Keep "mental models"
only as an explicitly-labelled organizing lens. *Fixes P9.*

**C4. Manual audit.** The pipeline emits a stratified ~40-item sample
(high-confidence theme matches, no-theme items, cluster/theme disagreements).
The **user** audits it by hand; the agreement rate is recorded in `findings.md`.
This is the one irreducibly non-automated check. *Council (Codex) recommendation.*

---

## Sequencing & dependencies

```
A1 ─┐
A2 ─┼─► A3 ─► B1 ─► B1.5 ─┐
    │              B2 ────┼─► B4 ─► B5 ─► B6 ─► B7 ─► C1 ─► C2 ─► C3 ─► C4
    │   B3 ───────────────┘
```

A1/A2 are independent and run in parallel. A3 needs the corpus settled. B1→B1.5,
B2, and B3 are independent once A3 is done. B4 gates the rest of Group B.
A review checkpoint sits at each group boundary (A→B, B→C).

## What "done" looks like

- Every theme carries: supporting derivations (of 3), entry_count, a coherence
  score vs. the embedding clusters, and a confidence tier.
- No theme description names a feature absent from its member entries.
- The unassigned residual is a labelled category with its own analysis section
  and a reported size — not a silent 33% gap.
- `findings.md` reports the manual-audit agreement rate and the cross-model
  theme overlap.
- The notebook shows the coherence heatmap; claim wording is downgraded
  throughout.
- `docs/methodology.md` is updated to describe the triangulated design.

## Process

Promote this spec to an implementation plan via `superpowers:writing-plans`, run
the plan past the Codex Plan Reviewer (REJECT→fix→APPROVE), then execute via
`superpowers:subagent-driven-development` — the workflow that produced v1.
