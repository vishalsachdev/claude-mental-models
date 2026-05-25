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

Of 292 versioned releases, **90 (30.8%)** are "narrated" — they have at least one
matching Anthropic blog post that covers that release period. The remaining 202 releases
(69.2%) are "silent" from a public-communication standpoint.

Important caveat: the blog corpus is thin. 32 posts were scraped from anthropic.com.
Of those, only **18 are dated**; 14 have no publish date because anthropic.com is a
JavaScript SPA that renders dates client-side — static scraping cannot recover them.
Only 22 of the 32 posts were classified as Claude Code-relevant.

The 30.8% narration rate should be read as a floor, not a ceiling. Anthropic likely
publishes more relevant content on YouTube, in changelogs themselves, and in the
Claude.ai in-app notes — none of which were collected. What this corpus does show is
that high-velocity changelog changes consistently outpace the documentation and
explanation that would help users keep up with what the tool now expects of them.

---

## The Competency Timeline (mental-model lens)

Thematic coding identified **10 recurring competency themes** the tool's surface
demanded — organized here under a mental-model lens. Entry counts reflect how
persistently each theme recurs across the changelog and blogs:

| Theme | Entry Count | First Seen |
|-------|-------------|------------|
| Context Is a Managed Resource | 285 | 2025-04-02 |
| The Harness Is Configurable | 433 | 2025-04-02 |
| Permissions as Declarative Policy | 275 | 2025-04-02 |
| Skills and Plugins as the Extension Model | 301 | 2025-04-02 |
| MCP as the Integration Protocol | 237 | 2025-04-02 |
| Memory as a Multi-Layer System | 27 | 2025-04-02 |
| Plans as Explicit, Reviewable Artifacts | 41 | 2025-04-02 |
| Delegation to Subagents | 243 | 2025-04-17 |
| Sessions as Resumable Artifacts | 342 | 2025-04-30 |
| Hooks as Automation Seams | 145 | 2025-06-30 |

Seven of ten themes trace to 2025-04-02 — the earliest date in the depth-1000 git clone.
This is an artifact of clone depth, not evidence that these concepts appeared on that date.
The more accurate reading is: by the time we have reliable changelog history, all seven
of these models were already well-established. **"First seen" is a lower bound, not an
origin date.**

The three themes with later first-seen dates are more interpretable:

- **Delegation to Subagents** (2025-04-17) — multi-agent task splitting entered the
  changelog just two weeks into the visible history, suggesting it was an early
  architectural bet that remained active throughout.
- **Sessions as Resumable Artifacts** (2025-04-30) — session persistence, compaction,
  and resumability became a sustained focus from late April onward, with 342 entries
  making it the most frequently surfaced theme.
- **Hooks as Automation Seams** (2025-06-30) — the hook system (pre/post-tool, stop
  hooks) appears to have been introduced or substantially expanded in mid-2025, making
  this the most clearly "late-arriving" competency the surface began demanding.

The **most entry-heavy theme** is "The Harness Is Configurable" (433 entries), followed
by "Sessions as Resumable Artifacts" (342) and "Skills and Plugins as the Extension
Model" (301). Configuration, session management, and extensibility dominate the
intellectual surface area — not the AI inference itself.

The **least entry-heavy themes** are "Memory as a Multi-Layer System" (27) and "Plans
as Explicit, Reviewable Artifacts" (41). These are conceptually important but narrowly
targeted in the changelog; they appear in blog posts and conceptual documentation rather
than in high-frequency fix cycles.

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
