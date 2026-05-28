# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "polars",
#     "pyarrow",
#     "altair",
#     "httpx",
# ]
# ///
"""Public WASM-friendly view of the Claude Code mental-models analysis.

Differences from notebooks/analysis.py:
- Data is fetched from raw.githubusercontent.com (the canonical Pyodide-safe
  source); no local-filesystem reads.
- No imports from cmm.* — the few constants/helpers we need are inlined
  (MAINTENANCE_LABEL, entry_url) so this notebook is self-contained.
- The RAG chat cell is replaced with a pointer at the local notebook —
  RAG needs the headless `claude` CLI, which has no WASM equivalent.

Run locally with `uv run marimo run notebooks/analysis_public.py` to see
what readers will see; build the deployable HTML with
`uv run marimo export html-wasm notebooks/analysis_public.py -o docs/`.
"""
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
    import httpx
    import json
    from io import BytesIO

    BASE_URL = (
        "https://raw.githubusercontent.com/vishalsachdev/"
        "claude-mental-models/main/data/processed"
    )

    def _fetch(name: str) -> bytes:
        r = httpx.get(f"{BASE_URL}/{name}", timeout=30)
        r.raise_for_status()
        return r.content

    def load_parquet(name: str):
        return pl.read_parquet(BytesIO(_fetch(name)))

    def load_json(name: str):
        return json.loads(_fetch(name))

    changelog = load_parquet("changelog.parquet")
    blogs = load_parquet("blogs.parquet")
    joins = load_parquet("joins.parquet")
    embeddings = load_parquet("embeddings.parquet")
    themes = load_parquet("themes.parquet")
    codes = load_parquet("codes.parquet")
    coherence = load_parquet("coherence.parquet")
    persona_relevance = load_parquet("persona_relevance.parquet")
    mini_themes = load_parquet("mini_themes.parquet")
    residual = load_json("residual_analysis.json")
    return (changelog, blogs, joins, embeddings, themes, codes,
            coherence, persona_relevance, mini_themes, residual)


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

> **You are viewing the public, in-browser version.** All the charts, the
> persona selector, the theme table, the heatmap, the cluster explorer, and
> the per-theme drill-down work here in your browser via WebAssembly. The
> only thing missing is the **"Ask the corpus" RAG chat** at the bottom —
> that one needs a local Claude CLI. Clone the
> [repo](https://github.com/vishalsachdev/claude-mental-models) and run
> `uv run marimo run notebooks/analysis.py` to use it.

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
3. **Top-down (B2).** A separate LLM pass over a stratified sample of the
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
   This is the rebuild's most honest output — see `docs/methodology.md §3.3`
   in the repo for what it revealed.
7. **Unassigned residual (B6).** Entries that no anchor theme claims get an
   explicit `Maintenance / no conceptual shift` label — not silently dropped.

Full pipeline + limitations: `docs/methodology.md`. Numerical findings:
`docs/findings.md`. Both live in the
[repo](https://github.com/vishalsachdev/claude-mental-models).

---

## What

The sections below walk through the analysis in order:

- **Descriptive layer** — pace, churn, narration coverage (high-reliability)
- **Interpretive layer** — theme emergence over time
- **Theme details** — the 13-theme table, the cluster×theme heatmap, the
  residual (this is where the methodological caveats matter most)
- **Drill-downs** — cluster explorer + per-theme entry list with
  click-through links to the canonical source

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

**What jumps out.** The cadence ramped from ~30–80 entries/month in early
2025 to ~600/month by early 2026 — an order-of-magnitude acceleration. Read
it as evidence that **whatever the tool is demanding of users, it is
demanding more of it, faster**.
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
matching blog post** within ±14 days that also shares a feature word.

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
§How above.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## Theme emergence over time — filtered by persona

Each band is one anchor theme the **selected persona** must build a mental
model for (relevance = `high` or `medium`). Band thickness is **cumulative
coded entries** for that theme. Switching the persona above reshapes the
chart — try it.

**What to be suspicious of.** Bands that "appear" at 2025-04-02 don't tell
you when those competencies actually emerged — they tell you when the public
record begins. The two themes with later first-seen dates are informative:
**Multi-Agent Orchestration** (2025-04-18) and **Workspace Isolation**
(2025-06-02).
"""
    )


@app.cell
def _(pl, alt, mo, codes, persona, persona_relevance):
    emerge_persona = persona.value or "vibe_coder"
    emerge_themes = set(
        persona_relevance.filter(
            (pl.col("persona") == emerge_persona) &
            (pl.col("relevance").is_in(["high", "medium"]))
        )["theme"].to_list()
    )
    emerge_growth = (
        codes.explode("themes").drop_nulls("themes")
        .filter(pl.col("date").is_not_null())
        .filter(pl.col("themes").is_in(list(emerge_themes)))
        .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
        .group_by("month", "themes").len().sort("month")
        .with_columns(pl.col("len").cum_sum().over("themes").alias("weight"))
    )
    chart_emerge = alt.Chart(emerge_growth.to_pandas()).mark_area().encode(
        x="month:T",
        y=alt.Y("weight:Q", stack="center", title="cumulative coded entries"),
        color=alt.Color("themes:N", title="competency theme"),
    ).properties(
        title=f"Theme emergence — {emerge_persona} (high + medium relevance, "
              f"{len(emerge_themes)} themes)",
        width=700,
    )
    mo.ui.altair_chart(chart_emerge)


@app.cell
def _(mo):
    mo.md(
"""
---

# Theme details

The 13-theme table sorted by relevance to the selected persona, then the
cluster×theme heatmap (the coherence diagnostic), then the labelled residual.
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

Rows are themes; columns are HDBSCAN embedding clusters (0–42). Color
intensity is the number of entries tagged with both that theme AND that
cluster. The residual Maintenance label is excluded.

**What it reveals.** Most themes smear. Median coherence is **0.30**. Only
**Permissions** (0.67) and **MCP / External Connectivity** (0.65) clear 0.5.
The lowest are *Configuration as a Layered Policy* (0.16), *Terminal Input*
(0.20), *UI Navigation* (0.21) — abstract cross-cutting concepts whose
vocabulary is too diffuse for any single cluster to anchor. The rebuild
made this measurable rather than eliminating it.
"""
    )


@app.cell
def _(mo, pl, alt, codes, embeddings):
    MAINTENANCE_LABEL = "Maintenance / no conceptual shift"
    cl = dict(zip(embeddings["entry_id"].to_list(),
                  embeddings["cluster_label"].to_list()))
    xt = (codes.explode("themes").drop_nulls("themes")
          .filter(pl.col("themes") != MAINTENANCE_LABEL)
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
explicit `Maintenance / no conceptual shift` label rather than being silently
dropped.

**By source:** {residual['by_source']}.

Down from v1's 33.6%; the remaining 1.5% is genuine maintenance, not
analytical failure.

**Examples (random sample):**
""" + "\n".join(f"- {x}" for x in residual["examples"]))


@app.cell
def _(mo):
    mo.md(
"""
---

# Drill-downs

Two surfaces for poking at the data directly: a tabular cluster explorer and
a theme-picker that shows every entry assigned to one theme with
click-through links to the canonical source.
"""
    )


@app.cell
def _(mo):
    mo.md(
"""
## Cluster explorer

One row per corpus entry. The **`url`** column links each entry back to its
canonical source: blog posts at anthropic.com; changelog entries at the
version section of the upstream `CHANGELOG.md` on GitHub. Click any URL to
verify the entry yourself.

Filter on `cluster_label` to read one embedding cluster (usually topically
tight); filter on `themes` to audit one anchor theme's assignment quality.
The interesting entries are the ones where `mini_theme` (the bottom-up
label) and `themes` (the consolidated labels) disagree.
"""
    )


@app.cell
def _(mo, pl, embeddings, codes, mini_themes):
    CHANGELOG_BASE = "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md"
    import re

    def github_slug(text):
        s = text.strip().lower()
        s = re.sub(r"\s+", "-", s)
        return re.sub(r"[^a-z0-9-]", "", s)

    def entry_url(entry_id, source, version):
        if source == "blog":
            return entry_id
        if source == "changelog" and version:
            return f"{CHANGELOG_BASE}#{github_slug(version)}"
        return ""

    clusters = (embeddings
                .join(codes.select("entry_id", "themes"), on="entry_id", how="left")
                .join(mini_themes.select("cluster_label", "mini_theme"),
                      on="cluster_label", how="left")
                .with_columns(
                    pl.struct(["entry_id", "source", "version"])
                    .map_elements(
                        lambda s: entry_url(s["entry_id"], s["source"], s["version"]),
                        return_dtype=pl.Utf8,
                    ).alias("url"))
                .select("entry_id", "text", "cluster_label", "mini_theme",
                        "themes", "url", "umap_x", "umap_y"))
    return clusters, entry_url


@app.cell
def _(mo, clusters):
    mo.ui.data_explorer(clusters)


@app.cell
def _(mo):
    mo.md(
"""
## Drill into a theme

Pick one of the 13 anchor themes to see the full list of corpus entries the
pipeline assigned to it, with **clickable links** back to the canonical
source. This is the verifiability surface: skeptical of a theme? Open its
drill-down and click through to source entries.
"""
    )


@app.cell
def _(mo, themes):
    theme_pick = mo.ui.dropdown(
        options=sorted(themes["name"].to_list()),
        value=sorted(themes["name"].to_list())[0],
        label="Theme to drill into",
    )
    theme_pick
    return (theme_pick,)


@app.cell
def _(mo, pl, embeddings, codes, theme_pick, entry_url):
    sel_theme = theme_pick.value
    members_ids = (codes.explode("themes").drop_nulls("themes")
                   .filter(pl.col("themes") == sel_theme)["entry_id"].to_list())
    drill = (embeddings.filter(pl.col("entry_id").is_in(members_ids))
             .with_columns(
                 pl.struct(["entry_id", "source", "version"])
                 .map_elements(
                     lambda s: entry_url(s["entry_id"], s["source"], s["version"]),
                     return_dtype=pl.Utf8,
                 ).alias("url"))
             .select("date", "version", "source", "text", "url")
             .sort("date", descending=True))
    mo.vstack([
        mo.md(f"**{sel_theme}** — {drill.height} entries assigned by the pipeline. Click any `url` to verify."),
        mo.ui.table(drill, page_size=25),
    ])


@app.cell
def _(mo):
    mo.md(
"""
---

## Ask the corpus (local only)

The original notebook has a RAG chat over the embedded corpus — useful for
questions like "when was X first mentioned?" or "what does the changelog say
about Y?" The chat needs the headless Claude CLI, which has no in-browser
equivalent, so it isn't available here.

To use it, clone the
[repo](https://github.com/vishalsachdev/claude-mental-models) and run:

```
uv sync
uv run marimo run notebooks/analysis.py
```

You'll need the `claude` CLI installed and logged in (no API key required —
subscription auth).
"""
    )


if __name__ == "__main__":
    app.run()
