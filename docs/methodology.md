# Methodology & Limitations

*A note for anyone reading the `claude-mental-models` analysis. Read this before
trusting — or dismissing — the charts and themes in the notebook.*

This analysis was reviewed for methodology by a three-model council (Claude,
GPT-5.5, Gemini) before this note was written. Their criticisms are reflected
throughout, especially in §3 and §4.

---

## 1. What this analysis claims — and what it does not

**The question.** How did the mental models a developer needs to use Claude
Code well evolve over its first ~14 months?

**The proxy.** We cannot observe what developers actually believed. We observe
only what Claude Code *shipped* — its public `CHANGELOG.md` and Anthropic's blog
posts. The whole analysis rests on one interpretive leap: **that the tool's
changing surface is a usable proxy for the competencies its users had to
develop.** That leap is reasonable but unproven.

Consequently:

- **Defensible claim:** "Claude Code's surface increasingly demanded that users
  notice, configure, and manage things that were previously implicit." The
  release history is direct evidence for this.
- **Overreach:** "Developers held mental model X at time T." The changelog is
  *not* evidence of anyone's interior state. Where the notebook or its
  generated text says "developers had to internalize…", read it as *"the tool's
  surface increasingly demanded…"* — the headline framing of "mental models"
  is a **lens for organizing the release data, not a measured finding.**

Treat the deliverable as two layers with very different reliability:

| Layer | What it is | Reliability |
|---|---|---|
| **Descriptive** — volume, churn, dates, change-types, blog coverage | Counted directly from the changelog | High |
| **Interpretive** — the 10 named "mental models" and their narratives | LLM-generated overlay | Provisional; unvalidated |

---

## 2. The pipeline, stage by stage

1. **Corpus.** Claude Code's `CHANGELOG.md` — 2,996 entries, each dated by the
   git commit that introduced its version heading (depth-1000 clone). Plus 32
   Anthropic blog posts scraped from anthropic.com.
2. **Change-type tagging.** Each changelog entry labelled add / change / fix /
   deprecate / remove by word-boundary keyword rules.
3. **Blog relevance & join.** An LLM tags each blog for Claude Code relevance;
   blogs are joined to changelog versions by date proximity (±14 days) plus
   shared feature words.
4. **Embedding spine.** All 3,018 items embedded with a local
   `all-MiniLM-L6-v2` sentence-transformer; HDBSCAN over a 5-D UMAP reduction
   yields 36 clusters.
5. **Theme layer.** One LLM call reads a 150-entry stratified timeline sample
   and proposes 10 named themes; the LLM then assigns all 3,018 items to those
   themes in batches.
6. **Output.** A marimo notebook: descriptive charts, a cluster explorer, a
   themes table, and a corpus-grounded RAG chat.

The LLM throughout is Claude Sonnet 4.6, via the local `claude` CLI.

---

## 3. Do the two methods agree? (A coherence diagnostic)

The pipeline produces **two independent structures**: 36 embedding clusters
(stage 4) and 10 LLM themes (stage 5). A genuine mixed-method design would have
them check each other. They were not reconciled during analysis — so we ran the
check here, after the fact.

Cross-tabulating cluster membership against theme assignment:

- **Mean themes per cluster: 5.5.** Only 2 of 37 clusters map cleanly to a
  single theme; 24 span five or more.
- Themes vary widely in how localized they are in embedding space:

| Theme | Spread | Top cluster holds |
|---|---|---|
| MCP as the Integration Protocol | 12 clusters | 71% |
| Delegation to Subagents | 24 clusters | 60% |
| Plans as Explicit, Reviewable Artifacts | 8 clusters | 56% |
| Hooks as Automation Seams | 20 clusters | 35% |
| Skills and Plugins as the Extension Model | 26 clusters | 33% |
| Permissions as Declarative Policy | 20 clusters | 29% |
| Context Is a Managed Resource | 27 clusters | 25% |
| Sessions as Resumable Artifacts | 26 clusters | 20% |
| **The Harness Is Configurable** | **33 of 36 clusters** | **27%** |

**What this means.** This diagnostic can *falsify* — it cannot *validate*. It
shows that concrete, lexically distinctive themes (**MCP**, **Delegation**,
**Plans**) are reasonably grounded: both methods, run independently, find the
same structure. But the **abstract themes** — above all "The Harness Is
Configurable," smeared across 33 of 36 clusters — are **not** reflected in the
embedding structure. They are LLM narrative constructs that organize the data
top-down rather than patterns that emerge from it. Trust the concrete themes
more than the abstract ones.

---

## 4. Limitations & caveats

**The "mental models" framing is a lens, not a measurement.** See §1.

**The theme layer is the weakest stage.** The project's *original* design — per-
item qualitative open coding, then axial aggregation — was attempted and
**failed**: it produced 17,149 unique, non-recurring codes. That failure is
itself a finding: the corpus has no naturally emergent code vocabulary. The
replacement (10 themes from a 5% sample, then force-assign everything) is
faster and produces clean output, but it imposes a taxonomy top-down and so
risks **narrative confirmation bias** — the model's preferred story becomes the
result. The 33% of entries assigned to *no* theme is corroborating evidence
that the 10-theme scheme does not fully fit the corpus.

**Two themes are barely evidenced.** "Memory as a Multi-Layer System" (27
entries) and "Plans as Explicit, Reviewable Artifacts" (41) rest on <1.5% of the
corpus each. They are presented alongside themes 10–16× larger; do not read the
ten as equal-weight.

**Generated descriptions outrun the evidence.** Spot-checking the theme
descriptions: version/date citations (e.g. v1.0.8 → 2025-06-02) are *accurate*,
but some features named as central to a theme appear only 1–4 times in the
actual changelog (`hard_deny`, `allowUnsandboxedCommands` — one mention each).
The descriptions blend corpus evidence with the model's own training knowledge
of Claude Code. They are readable and broadly correct, but more confident than
the data underneath them.

**The blog corpus is thin.** 32 posts, 14 with no parseable date —
anthropic.com is a JavaScript single-page app and was scraped statically.
Blog-coverage figures are indicative only.

**`first_seen` dates are clamped.** They come from a depth-1000 git clone;
several themes show first-seen dates at the clone's history horizon
(2025-04-02), meaning those themes may predate the window we can observe.

**Reflexivity.** The instrument analyzing Claude Code is itself Claude. The
relevance tagging, theme discovery, and assignment were all done by the same
model family the analysis is about. This is unavoidable here but worth stating
plainly: the analysis is not independent of its subject.

---

## 5. How to read the deliverable responsibly

- **Trust the descriptive charts** — feature volume, change-type mix, churn
  (adds vs. deprecations/removals). These are counts.
- **Read the 10 themes as an organizing lens**, not a result. Weight the
  concrete, embedding-corroborated ones (MCP, Delegation, Plans) above the
  abstract ones (especially "The Harness Is Configurable").
- **Discount the per-theme prose.** For any claim that matters, re-derive it
  from a theme's actual member entries (the entry→theme map is in
  `codes.parquet`), not from the sample-based generated narrative.
- **The RAG chat** answers only from retrieved corpus text, with version/URL
  citations — but it is still Claude Sonnet 4.6 and can still over-elaborate.
  Check its citations.
- The honest one-line summary of the whole analysis: *a well-grounded
  description of how Claude Code's surface area grew and changed, with a
  plausible but unvalidated interpretive story laid over it.*

---

*Reproduce or re-derive anything: see `README.md` and the spec/plan in
`docs/superpowers/`.*
