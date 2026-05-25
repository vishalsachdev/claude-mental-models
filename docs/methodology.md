# Methodology & Limitations

*A note for anyone reading the `claude-mental-models` analysis. Read this before
trusting — or dismissing — the charts and themes in the notebook.*

This analysis went through two rounds. v1 was reviewed for methodology by a
three-model council (Claude, GPT-5.5, Gemini); their criticisms are reflected
throughout. v2 (the current state) is a methodological rebuild that addresses
the named v1 problems via a triangulated theme design. The rebuild fixed some
issues — and surfaced a new, measured one (see §3.3).

---

## 1. What this analysis claims — and what it does not

**The question.** What competencies and expectations did Claude Code's surface
increasingly demand of its users over its first ~14 months?

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
  generated text uses the phrase "mental models", read it as an **organizing
  lens** for the competencies the surface demanded — a framing, not a measured
  claim about individual developers.

Treat the deliverable as two layers with very different reliability:

| Layer | What it is | Reliability |
|---|---|---|
| **Descriptive** — volume, churn, dates, change-types, blog coverage | Counted directly from the changelog | High |
| **Interpretive** — the named competency themes and their narratives | LLM-generated overlay (triangulated; see §3) | Tiered (high / provisional / bottom_up_only) |

---

## 2. The pipeline, stage by stage

1. **Corpus.** Claude Code's `CHANGELOG.md` — 3,057 entries across 296 releases,
   each dated by the git commit that introduced its version heading. Plus 33
   Anthropic blog posts scraped from anthropic.com (all 33 dated — see §3.4
   on A1).
2. **Change-type tagging.** Each changelog entry labelled add / change / fix /
   deprecate / remove by word-boundary keyword rules.
3. **Blog relevance & join.** An LLM tags each blog for Claude Code relevance;
   blogs are joined to changelog versions by date proximity (±14 days) plus
   shared feature words.
4. **Embedding spine.** All ~3,000 items embedded with a local
   `all-MiniLM-L6-v2` sentence-transformer; HDBSCAN over a 5-D UMAP reduction
   yields **43 clusters**.
5. **Theme layer (triangulated — see §3).** Three independent derivations are
   produced, then reconciled into 13 anchor themes, then used to assign every
   item.
6. **Output.** A marimo notebook: descriptive charts, a cluster explorer, a
   themes table with confidence and evidence tiers, a coherence diagnostic,
   and a corpus-grounded RAG chat.

The LLM throughout is Claude Sonnet 4.6 via the local `claude` CLI, except
for the **B3 independent derivation** which runs on GPT-5.5 via `codex exec`.

---

## 3. The triangulated theme design

The v1 theme stage was the weakest link: it was a single top-down LLM call over
a 5% sample, which then assigned every item to its own taxonomy. The council
flagged this as narrative confirmation bias. v2 replaces it with three
derivations that have to triangulate before a theme is trusted.

### 3.1 Three derivations + anchor reconciliation

| Derivation | What it does | Model |
|---|---|---|
| **B1 — bottom-up mini-themes** | One mini-theme per non-noise embedding cluster (43 calls, parallel). Each call sees only the cluster's items. | Claude Sonnet 4.6 |
| **B1.5 — anchor consolidation** | Group the 43 mini-themes into 10–15 anchor themes. Every cluster id appears in exactly one anchor; validated. | Claude Sonnet 4.6 |
| **B2 — top-down** | The original v1 design: one call over a stratified timeline sample. | Claude Sonnet 4.6 |
| **B3 — independent** | Same prompt and sample as B2, but run on a different model so the variable is the model. Result is persisted (`independent_derivation.json`, committed) so a fresh clone reproduces deterministically. | **GPT-5.5 (codex)** |

**Anchor-on-B1 triangulation.** We anchor on B1/B1.5 (which is grounded in the
embedding structure) and check whether each anchor theme is *corroborated* by
B2 (top-down) and B3 (independent). Each theme receives a **confidence tier**:

- `high` — corroborated by both B2 and B3
- `provisional` — corroborated by one of B2/B3
- `bottom_up_only` — visible in the clusters but neither external derivation
  surfaced it

For the current run (13 anchor themes): **7 high / 3 provisional / 3
bottom_up_only**. All 13 themes carry **evidence_tier = `core`** (they each
hold enough entries to be treated as primary findings rather than minor
mentions).

### 3.2 B4 multi-label assignment + B5 description grounding

- **B4** assigns every item to any number of the 13 anchor themes (usually 1
  or 2, occasionally 0 — those flow into the residual).
- **B5** is a description grounding check: for each theme description, extract
  content words and flag any that don't appear in the theme's actual member
  entries. All 13 themes have non-empty `description_flags`, but the flag
  vocabulary is dominated by **abstraction verbs** ("expect", "behave",
  "predictably", "platforms") rather than hallucinated features — the check is
  sensitive by design. One theme stands out and deserves human inspection:
  **Extensibility Ecosystem** has 19 flags including "pathological" and
  "recursion", suggesting the description elaborates beyond what the entries
  literally support.

### 3.3 Coherence diagnostic — the rebuild's most honest output

For every anchor theme we compute a **coherence_score**: the fraction of items
assigned to that theme that fall inside the theme's own
`source_clusters` (the embedding clusters the bottom-up derivation grounded it
in). High coherence = the theme is localized in embedding space. Low coherence
= the theme is being applied to items the embedding model thinks belong
elsewhere.

**Headline numbers from the current run:**

- **Median coherence: 0.30.**
- **Only 2 of 13 themes exceed 0.5** (Permission & Security Boundaries 0.67;
  External Connectivity 0.65).
- The **lowest-coherence** themes are abstract cross-cutting concepts —
  Configuration as a Layered Policy Hierarchy 0.16; Terminal Input 0.21; UI
  Navigation 0.21.

**What this means.** v1's headline problem was that abstract themes (e.g.
"The Harness Is Configurable") smeared across most embedding clusters. The
rebuild **did not eliminate that smearing — it made it measurable.** The
mechanism is a deliberate methodological choice: B4 is *multi-label generous*,
so an entry can be tagged with a theme even when the entry's cluster isn't in
the theme's anchor `source_clusters`. The alternative — strict
cluster-grounding — would make the themes more coherent but force-fit fewer
entries into each, defeating the point of anchor reconciliation.

Read the themes accordingly: trust the **high-coherence, high-confidence**
themes (Permission & Security Boundaries; External Connectivity / MCP) more
than the **low-coherence** ones (Configuration; the two Terminal themes; UI
Navigation), even when the latter are corroborated by all three derivations.
Cross-corroboration confirms that the *concept* is real; coherence is what
tells you whether the *embedding evidence* in the corpus tracks it.

### 3.4 Labelled residual

47 of 3,079 entries (1.5%) are unassigned by B4. These are labelled
**Maintenance / no conceptual shift** rather than discarded — almost all are
small bug fixes or version bumps that demanded no new user competency. The
v1 residual was 33.6% of entries; the drop reflects that multi-label
generosity now catches what was previously stranded.

---

## A1 — the changelog floor of 2025-04-02

v1 framed the earliest changelog date (2025-04-02) as a **clone-horizon clamp**
— an artifact of `--depth 1000`. The rebuild verified this against the upstream
repo and the framing was wrong: `anthropics/claude-code` committed its initial
`CHANGELOG.md` as a single batched commit containing 17 versions on
2025-04-02. The floor is **genuine batched upstream seeding**, not a shallow
clone artifact. The A1 task ships a forward-defensive safeguard (deeper clone
+ a date-sanity check), but no data was recovered — there is no earlier
changelog data to recover. Earlier text framing 2025-04-02 as a clone horizon
should be read in light of this correction.

---

## Limitations & caveats

**The "mental models" framing is a lens, not a measurement.** See §1.

**Coherence is low for abstract themes (median 0.30).** See §3.3. This is a
*measured* limitation surfaced by the rebuild's own diagnostic, not a
hand-wave.

**Description grounding flags abstractions, not hallucinations — except
Extensibility.** See §3.2. The B5 flags are mostly sensitivity to abstract
language. Extensibility Ecosystem's 19 flags include words like "pathological"
and "recursion" that may exceed what the corpus actually says — recommend
human spot-check.

**Reflexivity.** The instrument analyzing Claude Code is still partly Claude.
B1, B1.5, B2, B4, B5 are all Claude Sonnet 4.6. B3 (GPT-5.5) is the only fully
independent derivation; corroboration between B1 and B3 is the rebuild's
strongest independence claim, but the analysis is not fully independent of
its subject.

**The blog corpus is still thin.** 33 posts (up from 32 in v1, all now dated),
of which ~22 are Claude Code-relevant. Blog-coverage figures remain
indicative, not statistically robust.

---

## How to read the deliverable responsibly

- **Trust the descriptive charts** — feature volume, change-type mix, churn.
  These are counts.
- **Read the 13 themes through the tier signals.** A theme that is
  `confidence_tier=high` AND `coherence_score>0.5` is the strongest evidence
  the analysis offers (Permission & Security Boundaries; External
  Connectivity / MCP fit this). A theme that is `bottom_up_only` or has
  coherence_score<0.3 is a tentative signal, not a finding.
- **Discount the per-theme prose** for anything load-bearing. For any claim
  that matters, re-derive it from a theme's actual member entries
  (`codes.parquet`) rather than from the description.
- **The RAG chat** answers only from retrieved corpus text, with version/URL
  citations — but it is still Claude Sonnet 4.6 and can over-elaborate. Check
  its citations.
- The honest one-line summary: *a well-grounded description of how Claude
  Code's surface area grew and changed, with a triangulated interpretive
  overlay whose own diagnostics tell you which themes to trust.*

---

*Reproduce or re-derive anything: see `README.md` and the spec/plan in
`docs/superpowers/`.*
