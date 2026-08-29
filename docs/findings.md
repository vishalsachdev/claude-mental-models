# Findings: Competencies Demanded by Claude Code's Surface

*We use "mental models" as an organizing lens for these competencies — it is a
framing, not a measured claim about individual developers.*

*Analysis of 4,919 changelog entries and 45 blog posts spanning 2025-04-02 to 2026-08-28.
The 13 themes were derived on the corpus through 2026-05-23 (v2.1.150, 3,079 items) and
extended to v2.1.251 by an incremental refresh on 2026-08-29 — see "What changed May →
August 2026" and "Method corrections" below.*

---

## Overview

This project asks a practical question: what competencies and expectations did Claude
Code's surface increasingly demand of its users over time, and when did each demand
become visible in the release record? (We organize those competencies under a
"mental models" lens — see the note above.)

The primary corpus is the Claude Code CHANGELOG (4,919 entries across 380 releases),
supplemented by 45 Anthropic blog posts scraped as a proxy for what Anthropic chose to
explain publicly. The blog corpus is thin in volume — more on that below — but 44 of
the 45 carry a parsed publish date and are join-eligible. Together they give a
developer-facing view of Claude Code's evolution over 17 months.

---

## Pace

4,919 changelog entries span 17 calendar months (April 2025 – August 2026), with monthly
entry counts ranging from **32 to 731**. The low end reflects early months with sparse
upstream history (the initial `CHANGELOG.md` commit on 2025-04-02 seeded 17 versions in
one batch — see rebuild §A1); the high end is August 2026 (731 entries through the 28th),
after a sustained 600–670/month plateau from March to May 2026 and a dip to 443 in June.
This is a fast-moving product: releases ship continuously, not on a monthly cycle.

Change-type breakdown:

| Type | Count | Share |
|------|-------|-------|
| fix | 2,670 | 54.3% |
| change | 1,363 | 27.7% |
| add | 762 | 15.5% |
| remove | 106 | 2.2% |
| deprecate | 18 | 0.4% |

More than half of all changelog entries are bug fixes — the harness is being continuously
hardened. New-feature additions (762) substantially outnumber all removals combined (124),
but the ratio is shifting — see Churn.

---

## Churn

762 additions vs. 124 deprecations and removals — a removal rate of **16.3%** relative to
additions over the whole record. That headline hides a break: through 2026-05-23 the rate
was **11.8%** (64/543); for the 84 releases since, it is **27.4%** (60/219). The first
14 months were almost purely additive — removals concentrated in legacy config keys and
old permission flags — and that is still the shape of most of the record. But the
post-May surface is being pruned as well as extended.

For a user adapting to the tool's surface, this matters: a competency demanded in
month 1 was almost never invalidated — it was extended. The cognitive cost the tool
imposed was accumulation, not churn. Whether the summer-2026 pruning is a new regime or
a clean-up pass is the question the next refresh should answer.

---

## Blog Narration

Of 380 versioned releases, **154 (40.5%)** are "narrated" — they have at least one
matching Anthropic blog post that covers that release period. The remaining 226 releases
(59.5%) are "silent" from a public-communication standpoint. Through 2026-05-23 the rate
is 39.2% (116/296; see Method corrections for why this is not the 37.8% first reported);
for the 84 releases since, 45.2% (38/84), carried almost entirely by the Sonnet 5 and
Opus 5 launch posts — July 2026 is 91% narrated, June 32%, August 22%.

Important caveat: the blog corpus is thin in volume. 45 posts were scraped from
anthropic.com; 44 carry a parsed publish date (v1's static scrape left 14 of 32 posts
undated and excluded from the ±14-day join). 27 of the 45 were classified as Claude
Code-relevant. The index page on anthropic.com no longer paginates, so posts published
between 2026-05-20 and 2026-06-29 that had scrolled off the front page by 2026-08-29 are
a **known blind spot** (one engineering post from that window was recovered).

The 40.5% narration rate should be read as a floor, not a ceiling. Anthropic likely
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
| External Connectivity: MCP Servers, Providers & Network Reliability | 699 (417) | 2025-04-02 | high | 0.65 |
| Multi-Agent Orchestration & Task Lifecycle | 668 (314) | 2025-04-18 | high | 0.30 |
| Permission & Security Boundaries | 565 (310) | 2025-04-02 | high | 0.67 |
| Terminal Rendering & Display | 555 (361) | 2025-04-02 | bottom_up_only | 0.24 |
| UI Navigation & Command Surfaces | 553 (363) | 2025-04-02 | bottom_up_only | 0.21 |
| Extensibility Ecosystem: Plugins, Skills & Hooks | 550 (384) | 2025-04-02 | high | 0.36 |
| Terminal Input & Interaction | 500 (348) | 2025-04-02 | provisional | 0.20 |
| Session Identity & Persistence | 496 (281) | 2025-04-02 | high | 0.30 |
| Resource Monitoring, Observability & Performance | 465 (299) | 2025-04-02 | provisional | 0.21 |
| Configuration as a Layered Policy Hierarchy | 419 (263) | 2025-04-02 | high | 0.16 |
| Model Behavior & Inference Controls | 332 (205) | 2025-04-02 | high | 0.41 |
| Workspace Isolation & File-System Operations | 273 (169) | 2025-06-02 | bottom_up_only | 0.38 |
| Context Window as a Finite, Managed Resource | 201 (152) | 2025-04-02 | provisional | 0.25 |

*Entries: through v2.1.251, with the 2026-05-23 count in parentheses. Coherence is
frozen at the 2026-05-23 cluster solution (3,079 items); no `first_seen_date` moved.*

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

The **most entry-heavy themes** are MCP / Network (699), Multi-Agent Orchestration (668),
Permissions (565), and Terminal Rendering (555). External integration, orchestration, and
terminal-UX dominate the surface area — not the AI inference itself. The ordering shifted
with the refresh: Multi-Agent Orchestration took 19.0% of the 1,868 post-May items (354)
and rose from sixth to second; Extensibility fell from second to sixth.

The **smallest theme** (Context Window, 201 entries) still represents 4% of the corpus.
v1 had problematic 1.4% themes (27 and 41 entries); the rebuild's anchor consolidation
folded those into broader themes. All 13 themes land in the `core` evidence tier.

**72 of 4,946 entries (1.5%; 47 of 3,079 at derivation time)** were unassigned to any theme and now carry an explicit
`Maintenance / no conceptual shift` label. The vast majority are pure bug fixes with no
conceptual shift — they did not require the user to update any competency or
expectation, just trust that a known behavior was corrected. (This is down from v1's
33.6% — the methodological rebuild's anchor theme set covers the corpus much more
fully; see methodology.md §3 for how.)

---

## What changed May → August 2026

The corpus was extended on 2026-08-29 from v2.1.150 (2026-05-23) to v2.1.251
(2026-08-28) by an incremental refresh (methodology.md §5): **84 new releases, 1,862 new
changelog entries** (+61%), 12 new blog posts (5 of them Claude Code-relevant). The 13
themes were held fixed; escalation triggers (new-item residual >5%, any theme >40% of new
items) did not fire (1.34% and 19.0%).

| | through 2026-05-23 | 2026-05-27 → 2026-08-28 |
|---|---|---|
| changelog entries | 3,057 | 1,862 |
| releases | 296 | 84 |
| entries / month | 32 – 669 | Jun 443, Jul 539, **Aug 731** |
| removals + deprecations / additions | 64 / 543 = **11.8%** | 60 / 219 = **27.4%** |
| narrated releases | 116 / 296 = 39.2% | 38 / 84 = 45.2% |
| fix share of entries | 51.5% | 58.8% |

Three things moved. **Pace** did not level off: August 2026 (731 entries through the
28th) is the busiest month in the record, after a June dip. **Churn** more than doubled —
the post-May surface is being pruned as well as extended, which qualifies the "the tool
never walked a feature back" reading above. **Where new work landed**: Multi-Agent
Orchestration absorbed 19.0% of new items, then External Connectivity (15.1%) and
Permissions (13.7%); Context Window took only 2.6%.

---

## Method corrections (2026-08-29)

Found while building the refresh; each was verified against a known object before the
fix was accepted. Before → after numbers are for the May corpus unless stated.

1. **Versions compared as strings.** `max(version)` on the May parquet returned
   `2.1.98`; the real ceiling was **2.1.150** (`"2.1.98" > "2.1.150"` lexically). No
   published number depended on it, but the refresh planning did. Fixed by
   `cmm.collect_changelog.version_key` / `sort_versions`, used wherever versions are
   ordered.
2. **One blog post dated 15 months late.** `engineering/claude-code-best-practices` was
   dated 2026-05-14 — the page now redirects to code.claude.com and the collector's
   bare-date fallback took a docs `lastModified`. Corrected to 2025-04-18 (Wayback's
   earliest capture is 2025-04-20) via a provenance-logged `DATE_OVERRIDES` entry.
   Narrated releases through 2026-05-23: 112 (37.8%) → 115 (38.9%) with the May blog
   set; 116 (39.2%) once the refreshed blog set adds an engineering post dated
   2026-05-25.
3. **Change-type table did not sum to the corpus.** The table previously in this file
   summed to 2,996, not 3,057. Correct May figures: fix 1,575 (51.5%), change 875
   (28.6%), add 543 (17.8%), remove 49 (1.6%), deprecate 15 (0.5%). Removal rate 63/538
   = 11.7% → **64/543 = 11.8%**. The table above is now computed from the parquet.
4. **Blog date extraction silently broken.** anthropic.com dropped its `publishedOn`
   field; the fallback regex then returned `siteSettings._createdAt` (2023-11-03) for
   *every* post, including the control post. The extractor now reads the visible
   "Mon D, YYYY" text, has no decoy fallback (undated posts are kept and warned about),
   and passes a positive control (2026-05-19 post → 2026-05-19).
5. **Collector re-runs were no-ops.** The changelog collector fetched but never checked
   out (re-collect returned the May file); the blog index cache key carried no date
   (re-crawl served the May front page). Both fixed with positive controls (4,919 / 380
   after re-collect; 15 previously unseen links after re-crawl).
6. **One orphan row.** Upstream re-worded one 2.1.15 entry, changing its content-hash id;
   `cmm.refresh` now drops rows no longer in the corpus (3,079 → 3,078 May items in
   `codes.parquet`; totals in this file use 4,946).

---

## Methodology Notes and Limitations

The full methodology — including the v1 redesign, the v2 triangulated rebuild, and the
honest measurement of what the rebuild did *not* fix — lives in `docs/methodology.md`.
Headline limitations:

**Blog corpus is thin in volume.** 45 posts (44 dated), 27 Claude Code-relevant, with a
known 2026-05-20 → 06-29 blind spot (see Blog Narration). The narration analysis is
directionally useful but not statistically robust.

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

The embedding pipeline produced **43 HDBSCAN clusters** from the 3,079 entries available
on 2026-05-23. The triangulated theme layer produced **13 anchor themes** (7
high-confidence / 3 provisional / 3 bottom-up-only) assigned to 3,032 of them, and the
August refresh assigned a further 1,843 of 1,868 new entries to the same 13 without
clustering them.

The cluster explorer in `notebooks/analysis.py` lets a reader compare them visually:
color entries by `cluster_label` to see the embedding-space topology, then re-color by
`themes` to see where the theme boundaries land. The new cluster×theme heatmap surfaces
the disagreement directly — themes whose entries spread broadly across clusters
(visible as a horizontal smear in the heatmap) are precisely the abstract cross-cutting
themes flagged as low-coherence. Themes whose entries concentrate in one or two clusters
(visible as a tight column) are the surface-distinct ones whose existence the data most
clearly supports.
