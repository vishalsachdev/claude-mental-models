# Refresh notes for "The Tool as Teacher" (2026-08-29)

Internal working notes, not for publication. The article
`2026-05-27-the-tool-as-teacher.md` is untouched; this file lists every claim
in it that the incremental refresh (corpus v2.1.150 → v2.1.251, themes held
fixed) made stale, with the replacement number, so the rewrite is mechanical.
Source of every number: `data/processed/*` as of commit on 2026-08-29;
`docs/findings.md` → "What changed May → August 2026" and "Method corrections".

## Numbers that changed

| Article says (line) | Now | Note |
|---|---|---|
| "14 Months" (title, l.1) and "first 14 months" (l.5) | 17 months (April 2025 – August 2026) | or keep the title as a dated May snapshot and add a refresh section |
| "3,057 entries across 296 releases" (l.15) | **4,919 entries across 380 releases** (v0.2.21 – v2.1.251) | +1,862 entries / +84 releases since 2026-05-23 |
| "33 related blog posts" (l.15) | **45 posts** (27 Claude Code-relevant; 44 dated) | index no longer paginates: 2026-05-20 → 06-29 is a known blind spot |
| "~600/month by early 2026" (l.22) | ~600–700/month through 2026; **August 2026 = 731**, the record | June dipped to 443, July 539 |
| "Only 37.8% of releases were narrated" (l.22) | **40.5%** (154/380) overall; 39.2% through May (was mis-reported: one post was dated 15 months late), **45.2%** for the 84 post-May releases (July 91%, carried by the Sonnet 5 / Opus 5 launch posts) | the "trough months are the highest-velocity ones" line still holds for Aug (22%) but not Jul |
| "Removals trail behind additions by a wide margin" (l.22) | still true overall (124/762 = 16.3%) but the post-May rate is **27.4%** (60/219) vs 11.8% before | new claim available: the surface is now being pruned as well as extended |
| "43 resulting clusters … 13 anchor themes" (l.32) | unchanged, but say **"derived on the 3,079 items available on 2026-05-23"** | the 1,868 new items are assigned to the 13 themes, not clustered |
| "Median coherence is 0.30 … Only two themes (Permissions and MCP) clear 0.5" (l.39) | unchanged — frozen at the May cluster solution; say so | |
| implicit: theme size ordering in the notebook table | Multi-Agent Orchestration rose from 6th to **2nd** (314 → 668); Extensibility fell 2nd → 6th | 19.0% of new items went to Multi-Agent Orchestration |

## Numbers that did not change

- 13 themes, 7 high / 3 provisional / 3 bottom_up_only; all `core`.
- Median coherence 0.30; Permissions 0.67, MCP 0.65 (frozen).
- Residual share ~1.5% (47/3,079 → 72/4,946).
- No theme's `first_seen_date` moved.
- Four personas × 13 themes: persona lens re-run, 100% cache hit.

## One methodological sentence the article needs

> The 13 themes were derived on the corpus through 2026-05-23 and extended to
> v2.1.251 on 2026-08-29 by assigning the 1,868 newer items to the fixed theme
> set; two escalation triggers (new-item residual >5%, any theme >40% of new
> items) would have forced a re-derivation, and neither fired (1.3%, 19.0%).

## Corrections to disclose (from `docs/findings.md` → Method corrections)

1. The 37.8% narration figure was low by ~1 point: the "Claude Code: Best
   practices" post had been dated 2026-05-14 (a docs-page `lastModified`)
   instead of 2025-04-18. Corrected value for the May corpus: 38.9–39.2%.
2. The change-type table in findings.md did not sum to 3,057 (it summed to
   2,996). Corrected May figures: fix 1,575 / change 875 / add 543 / remove
   49 / deprecate 15; removal rate 11.8% (was 11.7%).
3. The corpus ceiling had been read as v2.1.98 because versions were sorted as
   strings; it was v2.1.150. No published number depended on it.

## Still-open P2 polish notes from the May editorial review (unchanged)

- temple-wall echo in the opener
- the buried 37.8% (now 40.5% / 45.2%) stat — the churn shift may be the
  stronger lede now
- concrete "try it on Cursor / Linear" examples
