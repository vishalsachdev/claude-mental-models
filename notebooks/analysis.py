import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    return mo, pl, alt


@app.cell
def _(mo, pl):
    import json
    changelog = pl.read_parquet("data/processed/changelog.parquet")
    blogs = pl.read_parquet("data/processed/blogs.parquet")
    joins = pl.read_parquet("data/processed/joins.parquet")
    embeddings = pl.read_parquet("data/processed/embeddings.parquet")
    themes = pl.read_parquet("data/processed/themes.parquet")
    codes = pl.read_parquet("data/processed/codes.parquet")
    coherence = pl.read_parquet("data/processed/coherence.parquet")
    residual = json.load(open("data/processed/residual_analysis.json"))
    mo.md(
        "# Claude Code: Competencies Demanded by the Tool's Surface\n\n"
        "*We use 'mental models' as an organizing lens for these competencies — "
        "it is a framing, not a measured claim about individual developers.*"
    )
    return (changelog, blogs, joins, embeddings, themes, codes,
            coherence, residual)


@app.cell
def _(mo, pl, alt, changelog):
    vol = (changelog.filter(pl.col("date").is_not_null())
           .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
           .group_by("month", "change_type").len())
    chart_volume = alt.Chart(vol.to_pandas()).mark_bar().encode(
        x="month:T", y="len:Q", color="change_type:N"
    ).properties(title="Feature volume per month", width=700)
    mo.ui.altair_chart(chart_volume)


@app.cell
def _(mo, pl, alt, changelog):
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
def _(mo, pl, alt, joins):
    cov = (joins.filter(pl.col("date").is_not_null())
           .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
           .with_columns((pl.col("impact_tier") == "narrated").alias("narrated"))
           .group_by("month").agg(pl.col("narrated").mean().alias("coverage")))
    chart_cov = alt.Chart(cov.to_pandas()).mark_area(opacity=0.6).encode(
        x="month:T", y=alt.Y("coverage:Q", title="% releases narrated"),
    ).properties(title="Blog coverage ratio", width=700)
    mo.ui.altair_chart(chart_cov)


@app.cell
def _(mo, pl, alt, codes):
    theme_growth = (
        codes.explode("themes").drop_nulls("themes")
        .filter(pl.col("date").is_not_null())
        .with_columns(pl.col("date").str.to_date().dt.truncate("1mo").alias("month"))
        .group_by("month", "themes").len().sort("month")
        .with_columns(pl.col("len").cum_sum().over("themes").alias("weight"))
    )
    chart_emerge = alt.Chart(theme_growth.to_pandas()).mark_area().encode(
        x="month:T",
        y=alt.Y("weight:Q", stack="center", title="cumulative coded entries"),
        color=alt.Color("themes:N", title="competency theme"),
    ).properties(title="Theme emergence and growth (competencies demanded over time)",
                 width=700)
    mo.ui.altair_chart(chart_emerge)


@app.cell
def _(mo):
    mo.md("## Cluster explorer")


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
    mo.md("## Competency themes reference (mental-model lens)")


@app.cell
def _(mo, themes):
    mo.ui.data_explorer(themes.select(
        "name", "description", "first_seen_date", "entry_count",
        "supporting_blog_urls", "example_entries"
    ))


@app.cell
def _(mo):
    mo.md("## Ask the corpus")


@app.cell
def _(mo):
    from cmm.rag import chat_model
    mo.ui.chat(chat_model, prompts=[
        "What competency did subagents demand of users?",
        "Which features were later deprecated or removed?",
        "How did context management change over the year?",
    ])


@app.cell
def _(mo, pl, alt, codes, embeddings):
    cl = dict(zip(embeddings["entry_id"].to_list(),
                  embeddings["cluster_label"].to_list()))
    xt = (codes.explode("themes").drop_nulls("themes")
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
def _(mo, themes, coherence):
    table = (themes.join(coherence, left_on="name", right_on="theme", how="left")
             .select("name", "confidence_tier", "evidence_tier", "entry_count",
                     "coherence_score", "corroborated_top_down",
                     "corroborated_independent", "first_seen_date"))
    mo.ui.table(table)


@app.cell
def _(mo, residual):
    mo.md(f"""
## Unassigned residual

**{residual['residual_count']} entries ({residual['residual_fraction']:.0%})**
fall under *Maintenance / no conceptual shift* — bug fixes and upkeep that
demanded no new user competency. By source: {residual['by_source']}.

Examples:
""" + "\n".join(f"- {x}" for x in residual["examples"]))


if __name__ == "__main__":
    app.run()
