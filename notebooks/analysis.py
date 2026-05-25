import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    return mo, pl, alt


@app.cell
def _(pl):
    import json
    changelog = pl.read_parquet("data/processed/changelog.parquet")
    blogs = pl.read_parquet("data/processed/blogs.parquet")
    joins = pl.read_parquet("data/processed/joins.parquet")
    embeddings = pl.read_parquet("data/processed/embeddings.parquet")
    themes = pl.read_parquet("data/processed/themes.parquet")
    codes = pl.read_parquet("data/processed/codes.parquet")
    coherence = pl.read_parquet("data/processed/coherence.parquet")
    persona_relevance = pl.read_parquet("data/processed/persona_relevance.parquet")
    residual = json.load(open("data/processed/residual_analysis.json"))
    return (changelog, blogs, joins, embeddings, themes, codes,
            coherence, persona_relevance, residual)


@app.cell
def _(mo):
    mo.md(
"""
# Claude Code: How the Tool Guides Users to Build New Mental Models

*A study of how Claude Code's user-facing surface evolved across its first ~14
months of releases — and what mental models **a user encountering that surface
would have had to build** to use the tool well. The deliverable is
**persona-aware**: pick who you are below and the analysis re-orients around
the mental models the tool was teaching **you**.*

*The claim is not "developers held mental model X at time T" — we cannot
observe interior states. The claim is: **the tool's evolving surface
increasingly invited users to think about Y, Z, … in particular ways.** That
invitation is what the release record makes visible.*

---

## Why

The question this notebook asks is **not** "what does Claude Code do?" but
**"what did using Claude Code well demand that its users come to expect,
configure, and reason about — and when did each demand show up?"**

We cannot observe what any developer actually believed at any point in time.
We can only observe what Claude Code *shipped*: its public `CHANGELOG.md` and
Anthropic's blog posts. The whole analysis rests on one interpretive leap:

> **The tool's changing surface is a usable proxy for the competencies its users
> had to develop.**

That leap is reasonable — products only ship features they expect users to use
— but it is unproven. Read the deliverable in two layers with very different
reliability:

| Layer | What it is | Reliability |
|---|---|---|
| **Descriptive** — volume, churn, change-types, blog coverage | Counted directly from the data | High |
| **Interpretive** — the 13 named themes and their narratives | LLM-generated overlay (triangulated; see §How) | Tiered — `high` / `provisional` / `bottom_up_only` |

---

## How

The interpretive layer is **triangulated**, not a single LLM pass:

1. **Bottom-up (B1).** Embed all 3,079 corpus items with `all-mpnet-base-v2`;
   cluster with HDBSCAN over a 12-D UMAP reduction → **43 embedding clusters**.
   For each cluster, ask Claude what *latent user assumption* its items share.
   → 43 cluster-grounded **mini-themes**.
2. **Consolidate (B1.5).** A second LLM pass groups the 43 mini-themes into
   **13 consolidated anchor themes**, with cluster provenance preserved.
3. **Top-down (B2).** The original v1 LLM pass over a stratified sample of the
   timeline. → ~10 candidate themes.
4. **Independent (B3).** Re-run theme discovery with **GPT-5.5 via `codex
   exec`** — same prompts, same sample, a different model. → another ~10
   candidate themes.
5. **Triangulate (B4).** For each B1.5 anchor theme, the independent model
   judges per-pair whether **B2 corroborates** it and whether **B3 corroborates**
   it. The two booleans set the `confidence_tier`:
   - **`high`** — corroborated by both
   - **`provisional`** — corroborated by one
   - **`bottom_up_only`** — corroborated by neither (data-derived but not
     surfaced by either top-down pass)
6. **Coherence diagnostic (C1).** For each theme, measure how concentrated its
   assigned entries are in a single embedding cluster (`coherence_score`).
   This is the rebuild's most honest output — see §3.3 of `docs/methodology.md`
   for what it revealed.
7. **Unassigned residual (B6).** Entries that no anchor theme claims get an
   explicit `Maintenance / no conceptual shift` label — not silently dropped.

Full pipeline + limitations: `docs/methodology.md`. Numerical findings:
`docs/findings.md`.

---

## What

The sections below walk through the analysis in order:

- **Descriptive layer** — pace, churn, narration coverage (high-reliability)
- **Interpretive layer** — theme emergence over time
- **Theme details** — the 13-theme table, the cluster×theme heatmap, the
  residual (this is where the methodological caveats matter most)
- **Drill-downs** — cluster explorer + a RAG chat over the corpus

Each section has a short note on **how to read it** and **what to be suspicious
of**.
"""
    )


@app.cell
def _(mo):
    persona = mo.ui.radio(
        options={
            "Analyst — data person using Claude via Skills / notebooks": "analyst",
            "PM running ops — orchestrating agents, schedules, Skills": "pm_ops",
            "Researcher — long-form thinking partner across sessions": "researcher",
            "Vibe coder — high-level intent in, working code out": "vibe_coder",
        },
        value="Vibe coder — high-level intent in, working code out",
        label="**Who are you?** Pick a persona — the analysis below re-orients around the mental models the tool was teaching *you*.",
    )
    persona
    return (persona,)


@app.cell
def _(mo, pl, persona, persona_relevance, themes):
    selected = persona.value or "vibe_coder"
    pr = (persona_relevance.filter(pl.col("persona") == selected)
          .join(themes.select("name", "entry_count", "confidence_tier"),
                left_on="theme", right_on="name", how="left"))
    rank = {"high": 0, "medium": 1, "low": 2}
    pr = pr.with_columns(pl.col("relevance").replace_strict(rank).alias("_r")).sort("_r", "entry_count", descending=[False, True])

    persona_labels = {
        "analyst": "If you are a **data analyst**",
        "pm_ops": "If you are a **PM running ops**",
        "researcher": "If you are a **researcher**",
        "vibe_coder": "If you are a **vibe coder**",
    }
    high = pr.filter(pl.col("relevance") == "high")
    medium = pr.filter(pl.col("relevance") == "medium")
    low_count = pr.filter(pl.col("relevance") == "low").height

    def fmt(row):
        return (f"- **{row['theme']}** "
                f"<sub>({row['entry_count']} entries · {row['confidence_tier']})</sub>  \n"
                f"  {row['mental_model']}")

    md = [
        f"## Your mental-model map\n",
        f"{persona_labels[selected]}, the tool was actively teaching you these mental models:\n",
        f"### Core ({high.height})  — you cannot use Claude Code well without these\n",
        *[fmt(r) for r in high.iter_rows(named=True)],
        f"\n### Adjacent ({medium.height}) — you will brush against these\n",
        *[fmt(r) for r in medium.iter_rows(named=True)],
        f"\n*({low_count} additional themes are mostly developer / CLI concerns this persona can ignore — they are still in the full table below.)*",
    ]
    mo.md("\n".join(md))


@app.cell
def _(mo):
    mo.md(
"""
---

# Descriptive layer

This layer is counted directly from the corpus and carries the highest
reliability. There is no LLM judgment in any of these charts.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## Pace — feature volume per month

Each bar is one month, stacked by change-type (`add` / `change` / `fix` /
`deprecate` / `remove`). The colored bands show how the kinds of work shifted
over time.

**How to read it.** Total bar height is the release pace. The `fix` band is
typically the largest — most changelog entries are bug fixes, which is why a
small "Maintenance" residual at the theme layer is the right expectation, not
a problem to fix.

**What jumps out.** The cadence ramped from ~30–80 entries/month in early
2025 to ~600/month by early 2026 — an order-of-magnitude acceleration. That
acceleration is the *most reliable* finding in the whole notebook: it is
counted, not inferred. Read it as evidence that **whatever the tool is
demanding of users, it is demanding more of it, faster**.
"""
    )


@app.cell
def _(pl, alt, mo, changelog):
    vol = (changelog.filter(pl.col("date").is_not_null())
           .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
           .group_by("month", "change_type").len())
    chart_volume = alt.Chart(vol.to_pandas()).mark_bar().encode(
        x="month:T", y="len:Q", color="change_type:N"
    ).properties(title="Feature volume per month", width=700)
    mo.ui.altair_chart(chart_volume)


@app.cell
def _(mo):
    mo.md(
"""
## Churn — cumulative adds vs. removals

Two cumulative lines: things added vs. things deprecated/removed. The gap
between them is roughly the net feature surface of the product.

**How to read it.** A growing gap means the product is mostly accretive —
features pile up faster than they retire. A narrowing gap would mean active
pruning. The removal line trailing well below the add line is the normal
shape for a growing product; what would be surprising (and isn't here) is a
flat add-line or an accelerating remove-line.

**What jumps out.** Removals/deprecations exist but are modest — Claude Code
doesn't aggressively retire surface area. That has a real implication for
users: **the cognitive surface they must keep up with only grows**. There is
no equilibrium where one new thing replaces an old one.
"""
    )


@app.cell
def _(pl, alt, mo, changelog):
    churn = (changelog.filter(pl.col("date").is_not_null())
             .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
             .with_columns(pl.col("change_type")
                           .is_in(["deprecate", "remove"]).alias("is_removal"))
             .group_by("month", "is_removal").len().sort("month")
             .with_columns(pl.col("len").cum_sum().over("is_removal").alias("cumulative")))
    chart_churn = alt.Chart(churn.to_pandas()).mark_line(point=True).encode(
        x="month:T", y="cumulative:Q",
        color=alt.Color("is_removal:N", title="removal/deprecation"),
    ).properties(title="Cumulative adds vs. deprecations+removals", width=700)
    mo.ui.altair_chart(chart_churn)


@app.cell
def _(mo):
    mo.md(
"""
## Narration — how much of the release stream did Anthropic explain publicly?

For each month, the fraction of versioned releases that have **at least one
matching blog post** within ±14 days that also shares a feature word. A
release with no such match is "silent" from a public-communication
standpoint.

**How to read it.** This is a *floor*, not a *ceiling*. Anthropic publishes
elsewhere too — YouTube, the in-app changelog, Claude.ai notes — none of
which we collected. A low number means "we did not find a blog post tied to
this release"; it does not mean "Anthropic did not explain this anywhere."

**What jumps out.** Across the whole corpus, **37.8%** of releases are
narrated (112 of 296). The trough months are exactly the high-velocity
months. The takeaway: **changelog velocity routinely outpaces the
explanatory work** that would help users keep up with what the tool now
expects of them.
"""
    )


@app.cell
def _(pl, alt, mo, joins):
    cov = (joins.filter(pl.col("date").is_not_null())
           .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
           .with_columns((pl.col("impact_tier") == "narrated").alias("narrated"))
           .group_by("month").agg(pl.col("narrated").mean().alias("coverage")))
    chart_cov = alt.Chart(cov.to_pandas()).mark_area(opacity=0.6).encode(
        x="month:T", y=alt.Y("coverage:Q", title="% releases narrated"),
    ).properties(title="Blog coverage ratio", width=700)
    mo.ui.altair_chart(chart_cov)


@app.cell
def _(mo):
    mo.md(
"""
---

# Interpretive layer

This layer is LLM-generated and carries lower reliability than the descriptive
charts above. **Read every theme name as a label on top of evidence, not as a
neutral observation.** The pipeline that produced these themes is described in
§How above; the limitations are in `docs/methodology.md §3`.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## Theme emergence over time

Each band is one of the 13 anchor themes; band thickness is **cumulative
coded entries** for that theme. The stack is centered so growth in any
direction is visible.

**How to read it.** Bands that start at the left edge (2025-04-02) and grow
monotonically are themes that were already established when the upstream
`CHANGELOG.md` was first committed — see `methodology.md §A1` for why the
2025-04-02 floor is genuine batched seeding, not a scrape artifact. The two
themes with later first-seen dates *are* informative:

- **Multi-Agent Orchestration & Task Lifecycle** (2025-04-18) — concurrent
  agents, task IDs, and lifecycle hooks appeared two weeks into the visible
  history.
- **Workspace Isolation & File-System Operations** (2025-06-02) —
  git-worktree semantics and sandbox boundaries emerged in early summer 2025.

**What to be suspicious of.** Bands that "appear" at 2025-04-02 don't tell
you when those competencies actually emerged — they tell you when the public
record begins. For everything stacked at the left edge, the upstream record
cannot distinguish "introduced then" from "already established."

**Persona filter applied.** The bands shown below are only the themes the
selected persona must build a mental model for (relevance = `high` or
`medium`). Switching the persona above reshapes this chart.
"""
    )


@app.cell
def _(pl, alt, mo, codes, persona, persona_relevance):
    selected_p = persona.value or "vibe_coder"
    relevant_themes = set(
        persona_relevance.filter(
            (pl.col("persona") == selected_p) &
            (pl.col("relevance").is_in(["high", "medium"]))
        )["theme"].to_list()
    )
    theme_growth = (
        codes.explode("themes").drop_nulls("themes")
        .filter(pl.col("date").is_not_null())
        .filter(pl.col("themes").is_in(list(relevant_themes)))
        .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
        .group_by("month", "themes").len().sort("month")
        .with_columns(pl.col("len").cum_sum().over("themes").alias("weight"))
    )
    chart_emerge = alt.Chart(theme_growth.to_pandas()).mark_area().encode(
        x="month:T",
        y=alt.Y("weight:Q", stack="center", title="cumulative coded entries"),
        color=alt.Color("themes:N", title="competency theme"),
    ).properties(
        title=f"Theme emergence — {selected_p} (high + medium relevance only, "
              f"{len(relevant_themes)} themes)",
        width=700,
    )
    mo.ui.altair_chart(chart_emerge)


@app.cell
def _(mo):
    mo.md(
"""
---

# Theme details

This is where the methodological caveats matter most. Three views, in order:
the **theme table** (what the themes are and how much evidence each carries),
the **cluster×theme heatmap** (how cleanly themes map to embedding clusters —
the rebuild's most honest output), and the **unassigned residual**.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## The 13 anchor themes — confidence and coherence

Each row is one theme. Columns:

- **`confidence_tier`** — `high` if both top-down (B2) and independent
  (B3, GPT-5.5) derivations corroborated this anchor; `provisional` if
  exactly one did; `bottom_up_only` if neither did (the theme is
  data-derived but absent from top-down naming).
- **`evidence_tier`** — `core` (≥1.5% of corpus) or `minor`. After the
  rebuild every theme is `core` — v1's tiny 1.4% themes were folded into
  broader anchors.
- **`entry_count`** — how many corpus items the assignment step pegged to
  this theme.
- **`coherence_score`** — fraction of this theme's entries that sit in its
  single most common embedding cluster. **1.0 = perfect, ≥0.5 = strong,
  <0.3 = smeared.**
- **`corroborated_top_down` / `corroborated_independent`** — the two
  booleans that feed `confidence_tier`.

**How to read it (the prioritization rule).** Trust themes that are
**`high` AND `coherence > 0.5`** the most — they are corroborated by three
independent processes (your own bottom-up data-derivation + two top-down
LLM passes) AND their entries hang together in embedding space. Only **two**
themes clear that bar: **Permissions** (0.67) and **MCP / External
Connectivity** (0.65).

The **`bottom_up_only`** themes — Terminal Rendering, UI Navigation,
Workspace Isolation — are the rebuild's methodological value-add: the data
clusters demanded them, but neither top-down LLM pass surfaced them. They
are real competencies the tool demands, just ones that abstract theme
discovery underweights.
"""
    )


@app.cell
def _(mo, pl, themes, coherence, persona, persona_relevance):
    selected_p = persona.value or "vibe_coder"
    pr_sel = (persona_relevance.filter(pl.col("persona") == selected_p)
              .select("theme", "relevance", "mental_model"))
    rank_map = {"high": 0, "medium": 1, "low": 2}
    table = (themes.join(coherence, left_on="name", right_on="theme", how="left")
             .join(pr_sel, left_on="name", right_on="theme", how="left")
             .with_columns(pl.col("relevance").replace_strict(rank_map).alias("_r"))
             .sort("_r", "entry_count", descending=[False, True])
             .select("name", "relevance", "mental_model",
                     "confidence_tier", "coherence_score", "entry_count",
                     "evidence_tier", "first_seen_date"))
    mo.ui.table(table)


@app.cell
def _(mo):
    mo.md(
"""
## Cluster × theme heatmap — the coherence finding made visible

Rows are themes; columns are HDBSCAN embedding clusters (0–42, the residual
Maintenance label is excluded). Color intensity is the number of entries
tagged with both that theme AND that cluster.

**How to read it.** A theme whose entries concentrate in **one or two
columns** is coherent — its assigned items genuinely cluster together in
embedding space. A theme whose color smears horizontally across many
columns is **abstract / cross-cutting** — the label organizes entries that
the embedding model sees as disparate.

**What it reveals (the rebuild's most honest output).** Most themes smear.
Median coherence across the 13 themes is **0.30** — i.e. the modal cluster
for a typical theme holds only 30% of that theme's entries. The lowest are
*Configuration as a Layered Policy* (0.16), *Terminal Input* (0.20), *UI
Navigation* (0.21) — all abstract cross-cutting concepts whose vocabulary
is too diffuse for any single cluster to anchor.

The mechanism is in `methodology.md §3.3`: B4's multi-label theme assignment
is generous — entries get tagged with multiple themes including ones whose
original anchor clusters don't include the entry. **This is a methodological
choice (multi-label breadth vs. strict cluster-grounding); the rebuild made
the consequence visible rather than eliminating it.**
"""
    )


@app.cell
def _(mo, pl, alt, codes, embeddings):
    from cmm.triangulate import MAINTENANCE_LABEL
    cl = dict(zip(embeddings["entry_id"].to_list(),
                  embeddings["cluster_label"].to_list()))
    xt = (codes.explode("themes").drop_nulls("themes")
          .filter(pl.col("themes") != MAINTENANCE_LABEL)  # residual shown separately
          .with_columns(pl.col("entry_id")
                        .map_elements(lambda e: cl.get(e, -1),
                                      return_dtype=pl.Int64).alias("cluster"))
          .filter(pl.col("cluster") != -1)
          .group_by("themes", "cluster").len())
    heat = alt.Chart(xt.to_pandas()).mark_rect().encode(
        x="cluster:O", y="themes:N",
        color=alt.Color("len:Q", title="entries"),
    ).properties(title="Cluster x theme cross-tab", width=700)
    mo.ui.altair_chart(heat)


@app.cell
def _(mo, residual):
    mo.md(f"""
## Unassigned residual — the labelled "no conceptual shift" bucket

**{residual['residual_count']} entries ({residual['residual_fraction']:.1%}
of the corpus)** were not pegged to any anchor theme. They carry the
explicit `Maintenance / no conceptual shift` label rather than being
silently dropped.

**By source:** {residual['by_source']}.

**How to read it.** Read these as the *baseline rate* at which Claude Code
ships work that demands nothing new of its users — only that they trust a
known behavior was corrected. Down from v1's 33.6% (the anchor theme set
covers the corpus much more fully now); the remaining 1.5% is genuine
maintenance, not analytical failure.

**Examples (random sample):**
""" + "\n".join(f"- {x}" for x in residual["examples"]))


@app.cell
def _(mo):
    mo.md(
"""
---

# Drill-downs

Two interactive surfaces for poking at the data directly: a tabular cluster
explorer (every corpus entry with its cluster + assigned themes), and a RAG
chat that retrieves from the actual corpus.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## Cluster explorer

One row per corpus entry. Columns:

- **`cluster_label`** — which of the 43 HDBSCAN embedding clusters the entry
  was placed in (`-1` = noise / outlier; not assigned to any cluster).
- **`mini_theme`** — the **B1 bottom-up label** for that cluster. There are
  43 mini-themes (one per non-noise cluster). These are fine-grained and
  often more descriptive than the consolidated anchor themes.
- **`themes`** — the anchor themes the triangulated B4 assignment step
  pegged to this entry. Typically 1–2 themes; `["Maintenance / no
  conceptual shift"]` for the residual.
- **`umap_x` / `umap_y`** — 2-D UMAP coordinates for plotting (not visualized
  here; use them externally if you want a scatter).

**How to read it.** Filter on `cluster_label` to read everything inside one
embedding cluster — these are usually topically tight. Filter on `themes` to
audit one anchor theme's assignment quality. The interesting entries are the
ones where `mini_theme` (the bottom-up label) and `themes` (the consolidated
labels) disagree — those are the seams where consolidation lost information.
"""
    )


@app.cell
def _(mo, pl, embeddings, codes):
    mini = pl.read_parquet("data/processed/mini_themes.parquet")
    clusters = (embeddings
                .join(codes.select("entry_id", "themes"), on="entry_id", how="left")
                .join(mini.select("cluster_label", "mini_theme"),
                      on="cluster_label", how="left")
                .select("entry_id", "text", "cluster_label", "mini_theme",
                        "themes", "umap_x", "umap_y"))
    mo.ui.data_explorer(clusters)


@app.cell
def _(mo):
    mo.md(
"""
## Ask the corpus

A RAG chat over the embedded corpus entries. Useful for questions like "when
was X first mentioned?" or "what does the changelog say about Y?" — the
model retrieves matching entries before answering.

**How to read its answers.** Each answer is grounded in the actual corpus
text the retriever surfaced — not in the model's prior knowledge of Claude
Code. If the retrieval misses the right entries, the answer will miss too;
treat it as a search aid, not an oracle. Suggested starting questions are
below.
"""
    )


@app.cell
def _(mo):
    from cmm.rag import chat_model
    mo.ui.chat(chat_model, prompts=[
        "What competency did subagents demand of users?",
        "Which features were later deprecated or removed?",
        "How did context management change over the year?",
    ])


if __name__ == "__main__":
    app.run()
