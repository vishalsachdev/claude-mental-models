# Findings: Claude Code Mental Models

*Analysis of 2,996 changelog entries and 32 blog posts spanning 2025-04-02 to 2026-05-19.*

---

## Overview

This project asks a practical question: what mental models does a power user have to
develop to work effectively with Claude Code, and when did each model become necessary?

The primary corpus is the Claude Code CHANGELOG (2,996 entries across 292 releases),
supplemented by 32 Anthropic blog posts scraped as a proxy for what Anthropic chose to
explain publicly. The blog corpus is thin — more on that below. Together they give a
developer-facing view of Claude Code's evolution over roughly 13 months.

---

## Pace

2,996 changelog entries span 14 calendar months (April 2025 – May 2026), with monthly
entry counts ranging from **32 to 669**. The low end reflects early months with sparse
history at the depth-1000 clone boundary; the high end reflects a brief acceleration
period before cadence settled. This is a fast-moving product: releases ship continuously,
not on a monthly cycle.

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

For a user building mental models, this matters: a model learned in month 1 was almost
never invalidated — it was extended. The cognitive cost was accumulation, not churn.

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
explanation that would help users build accurate mental models.

---

## The Mental-Model Timeline

Thematic coding identified **10 recurring mental models** from the corpus. Entry counts
reflect how persistently each model recurs across the changelog and blogs:

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
  this the most clearly "late-arriving" mental model.

The **most entry-heavy theme** is "The Harness Is Configurable" (433 entries), followed
by "Sessions as Resumable Artifacts" (342) and "Skills and Plugins as the Extension
Model" (301). Configuration, session management, and extensibility dominate the
intellectual surface area — not the AI inference itself.

The **least entry-heavy themes** are "Memory as a Multi-Layer System" (27) and "Plans
as Explicit, Reviewable Artifacts" (41). These are conceptually important but narrowly
targeted in the changelog; they appear in blog posts and conceptual documentation rather
than in high-frequency fix cycles.

**1,013 of 3,018 entries (33.6%)** were unassigned to any theme. The vast majority are
pure bug fixes with no conceptual shift — they do not require the user to update any
mental model, just trust that a known behavior was corrected.

---

## Methodology Notes and Limitations

**Redesign mid-project.** The original spec called for per-item open-coding followed by
axial coding — a qualitative grounded-theory approach adapted for LLM execution. On real
data, this produced approximately 17,149 unique non-recurring codes: the LLM generated
novel labels for every entry rather than converging. The design was revised (with project
owner approval) to two-stage theme discovery: (1) embed all entries, cluster with HDBSCAN,
and use cluster centroids as theme seeds; (2) use a fixed theme vocabulary for batched
assignment. This produced stable, reproducible results.

**Two-pass stability audit dropped.** The original plan included a second coding pass for
inter-rater reliability. Free-text codes never matched between passes (measured Cohen's
kappa: 0.003), making the metric meaningless for this LLM-executed workflow. The audit
was dropped in favor of a simpler verification: manual inspection of random samples from
each theme.

**33.6% unassigned.** Bug-fix entries without conceptual content were left unassigned
rather than force-fit into themes. This is by design: a theme should represent a mental
model the user must hold, not merely a code change that occurred.

**Blog corpus is thin.** 32 posts, 14 undated, 22 Claude Code-relevant. The narration
analysis is directionally useful but not statistically robust.

**`first_seen_date` is bounded by the git clone depth.** The repository was cloned with
`--depth 1000`. Seven of ten themes trace to the earliest visible date (2025-04-02),
which is the boundary of that clone — not evidence of origin.

---

## Where the Methods Could Disagree

The embedding pipeline produced **36 HDBSCAN clusters** (plus 691 noise points) from
3,018 entries. The thematic coding produced **10 LLM themes** assigned to 2,005 entries.
These are different granularities and they cut the data differently.

The cluster explorer in `notebooks/analysis.py` lets a reader compare them visually:
color entries by `cluster_label` to see the embedding-space topology, then re-color by
`themes` to see where the LLM theme boundaries land. Areas of disagreement — a single
embedding cluster that spans two LLM themes, or a single LLM theme scattered across
multiple clusters — are the most analytically interesting regions and the most likely
candidates for refinement in a follow-on pass.
