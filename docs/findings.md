# Findings: Competencies Demanded by Claude Code's Surface

*We use "mental models" as an organizing lens for these competencies — it is a
framing, not a measured claim about individual developers.*

*Analysis of 3,057 changelog entries and 33 blog posts spanning 2025-04-02 to 2026-05-23.*

---

## Overview

This project asks a practical question: what competencies and expectations did Claude
Code's surface increasingly demand of its users over time, and when did each demand
become visible in the release record? (We organize those competencies under a
"mental models" lens — see the note above.)

The primary corpus is the Claude Code CHANGELOG (3,057 entries across 296 releases),
supplemented by 33 Anthropic blog posts scraped as a proxy for what Anthropic chose to
explain publicly. The blog corpus is thin in volume — more on that below — but the
headless-render fix (rebuild §3.4) recovered a date for every post, so all 33 are now
join-eligible. Together they give a developer-facing view of Claude Code's evolution
over roughly 14 months.

---

## Pace

3,057 changelog entries span 14 calendar months (April 2025 – May 2026), with monthly
entry counts ranging from **32 to 669**. The low end reflects early months with sparse
upstream history (the initial `CHANGELOG.md` commit on 2025-04-02 seeded 17 versions in
one batch — see rebuild §A1); the high end reflects an acceleration period in early
2026. This is a fast-moving product: releases ship continuously, not on a monthly cycle.

Change-type breakdown:

| Type | Count | Share |
|------|-------|-------|
| fix | 1,528 | 51.0% |
| change | 867 | 28.9% |
| add | 538 | 17.9% |
| remove | 48 | 1.6% |
| deprecate | 15 | 0.5% |

More than half of all changelog entries are bug fixes — the harness is being continuously
hardened. New-feature additions (538) substantially outnumber all removals combined (63).

---

## Churn

538 additions vs. 63 deprecations and removals — a removal rate of **11.7%** relative to
additions. This is low by software standards, and the signal is deliberate: Claude Code
almost never walked features back. The few removals concentrated in specific areas
(legacy config keys, old permission flags) but the directional motion was always additive.

For a user adapting to the tool's surface, this matters: a competency demanded in
month 1 was almost never invalidated — it was extended. The cognitive cost the tool
imposed was accumulation, not churn.

---

## Blog Narration

Of 296 versioned releases, **112 (37.8%)** are "narrated" — they have at least one
matching Anthropic blog post that covers that release period. The remaining 184 releases
(62.2%) are "silent" from a public-communication standpoint.

Important caveat: the blog corpus is thin in volume. 33 posts were scraped from
anthropic.com — all 33 now carry a parsed publish date thanks to the headless-render fix
(rebuild §A2; v1's static scrape left 14 of 32 posts undated and excluded from the
±14-day join). Only 22 of the 33 posts were classified as Claude Code-relevant.

The 37.8% narration rate should be read as a floor, not a ceiling. Anthropic likely
publishes more relevant content on YouTube, in changelogs themselves, and in the
Claude.ai in-app notes — none of which were collected. What this corpus does show is
that high-velocity changelog changes consistently outpace the documentation and
explanation that would help users keep up with what the tool now expects of them.

---

## The Competency Timeline (mental-model lens)

The triangulated theme layer (see methodology.md §3) produced **13 anchor themes** the
tool's surface demanded — organized here under a mental-model lens. Each carries a
*confidence tier* (corroboration by the top-down and independent derivations), an
*entry count*, and a *coherence score* (how concentrated its assigned entries are in a
single embedding cluster; 1.0 = perfect, ≥0.5 = strong, <0.3 = smeared):

| Theme | Entries | First Seen | Confidence | Coherence |
|-------|---------|------------|------------|-----------|
| External Connectivity: MCP Servers, Providers & Network Reliability | 417 | 2025-04-02 | high | 0.65 |
| Extensibility Ecosystem: Plugins, Skills & Hooks | 384 | 2025-04-02 | high | 0.36 |
| UI Navigation & Command Surfaces | 363 | 2025-04-02 | bottom_up_only | 0.21 |
| Terminal Rendering & Display | 361 | 2025-04-02 | bottom_up_only | 0.24 |
| Terminal Input & Interaction | 348 | 2025-04-02 | provisional | 0.20 |
| Multi-Agent Orchestration & Task Lifecycle | 314 | 2025-04-18 | high | 0.30 |
| Permission & Security Boundaries | 310 | 2025-04-02 | high | 0.67 |
| Resource Monitoring, Observability & Performance | 299 | 2025-04-02 | provisional | 0.21 |
| Session Identity & Persistence | 281 | 2025-04-02 | high | 0.30 |
| Configuration as a Layered Policy Hierarchy | 263 | 2025-04-02 | high | 0.16 |
| Model Behavior & Inference Controls | 205 | 2025-04-02 | high | 0.41 |
| Workspace Isolation & File-System Operations | 169 | 2025-06-02 | bottom_up_only | 0.38 |
| Context Window as a Finite, Managed Resource | 152 | 2025-04-02 | provisional | 0.25 |

**How to read this table.** Eleven of thirteen themes trace `first_seen_date` to
2025-04-02 — that is the date `anthropics/claude-code` committed its initial
`CHANGELOG.md` with 17 versions seeded in one batch (see methodology.md §A1). It is the
earliest date in the public upstream history, not evidence that all these competencies
appeared simultaneously. **"First seen" is a lower bound; for everything dated
2025-04-02, the upstream record cannot distinguish "introduced then" from "already
established."**

The two themes with later first-seen dates *are* informative:

- **Multi-Agent Orchestration & Task Lifecycle** (2025-04-18) — concurrent agents,
  task IDs, and lifecycle hooks entered the changelog two weeks into the visible
  history. An early architectural bet that remained active throughout, and a `high`
  confidence theme corroborated by all three derivations.
- **Workspace Isolation & File-System Operations** (2025-06-02) — git-worktree
  semantics, sandbox allowlists, file-system boundaries — this competency emerged in
  early summer 2025. Flagged `bottom_up_only`: visible in the data clusters but not
  named by either top-down derivation; the rebuild's bottom-up pass is its value-add.

**Confidence-tier breakdown.** 7 themes are `high` (corroborated by both the top-down
and independent derivations); 3 are `provisional` (one of two); 3 are `bottom_up_only`
(data-derived but not named by any top-down pass). The three bottom-up-only themes
(Terminal Rendering, UI Navigation, Workspace Isolation) are precisely the
surface-level competencies that abstract top-down theme discovery underweights — they
are the rebuild's methodological value-add.

**Coherence caveats.** Of 13 themes, only 2 (Permissions 0.67; MCP 0.65) clear the 0.5
coherence threshold — meaning their assigned entries concentrate strongly in one
embedding cluster. The other 11 smear across many clusters, with the lowest-coherence
themes (Configuration as Policy 0.16; Terminal Input 0.20; UI Navigation 0.21) being
abstract cross-cutting concepts whose vocabulary is too diffuse to anchor in one
cluster. Read low-coherence themes as **organizing labels** rather than as crisply
delineated phenomena. See methodology.md §3.3 for the mechanism.

The **most entry-heavy themes** are MCP / Network (417), Extensibility (384), UI
Navigation (363), and Terminal Rendering (361). External integration, extensibility,
and terminal-UX dominate the surface area — not the AI inference itself.

The **smallest theme** (Context Window, 152 entries) still represents 5% of the corpus.
v1 had problematic 1.4% themes (27 and 41 entries); the rebuild's anchor consolidation
folded those into broader themes. All 13 themes land in the `core` evidence tier.

**47 of 3,079 entries (1.5%)** were unassigned to any theme and now carry an explicit
`Maintenance / no conceptual shift` label. The vast majority are pure bug fixes with no
conceptual shift — they did not require the user to update any competency or
expectation, just trust that a known behavior was corrected. (This is down from v1's
33.6% — the methodological rebuild's anchor theme set covers the corpus much more
fully; see methodology.md §3 for how.)

---

## Methodology Notes and Limitations

The full methodology — including the v1 redesign, the v2 triangulated rebuild, and the
honest measurement of what the rebuild did *not* fix — lives in `docs/methodology.md`.
Headline limitations:

**Blog corpus is thin in volume.** 33 posts, all dated after the headless-render fix,
22 Claude Code-relevant. The narration analysis is directionally useful but not
statistically robust.

**The 2025-04-02 corpus floor is genuine batched upstream seeding** (not a shallow-clone
artifact, as v1 incorrectly framed it). Whatever existed before that commit was never
in public git history. Several themes trace `first_seen_date` to 2025-04-02 because that
is when the upstream `CHANGELOG.md` itself was committed.

**Themes still smear across embedding clusters.** Median cluster↔theme coherence is
**0.30**; only 2 of 13 themes exceed 0.5. The rebuild made this measurable
(`coherence.parquet`, the heatmap in the notebook) rather than eliminating it. Read
`high` themes with `coherence_score > 0.5` (Permissions, MCP) with more confidence than
abstract cross-cutting themes (Configuration as Policy, UI Navigation). See
methodology.md §3.3 for the mechanism.

---

## Where the Methods Could Disagree

The embedding pipeline produced **43 HDBSCAN clusters** from 3,079 entries. The
triangulated theme layer produced **13 anchor themes** (7 high-confidence / 3
provisional / 3 bottom-up-only) assigned to 3,032 entries.

The cluster explorer in `notebooks/analysis.py` lets a reader compare them visually:
color entries by `cluster_label` to see the embedding-space topology, then re-color by
`themes` to see where the theme boundaries land. The new cluster×theme heatmap surfaces
the disagreement directly — themes whose entries spread broadly across clusters
(visible as a horizontal smear in the heatmap) are precisely the abstract cross-cutting
themes flagged as low-coherence. Themes whose entries concentrate in one or two clusters
(visible as a tight column) are the surface-distinct ones whose existence the data most
clearly supports.
