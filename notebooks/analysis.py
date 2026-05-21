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
    changelog = pl.read_parquet("data/processed/changelog.parquet")
    blogs = pl.read_parquet("data/processed/blogs.parquet")
    joins = pl.read_parquet("data/processed/joins.parquet")
    embeddings = pl.read_parquet("data/processed/embeddings.parquet")
    themes = pl.read_parquet("data/processed/themes.parquet")
    codes = pl.read_parquet("data/processed/codes.parquet")
    mo.md("# Claude Code Mental Models")
    return changelog, blogs, joins, embeddings, themes, codes


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
        color=alt.Color("themes:N", title="mental model"),
    ).properties(title="Mental-model emergence and growth", width=700)
    mo.ui.altair_chart(chart_emerge)


@app.cell
def _(mo):
    mo.md("## Cluster explorer")


@app.cell
def _(mo, embeddings, codes):
    clusters = (
        embeddings.join(codes.select("entry_id", "themes"), on="entry_id", how="left")
        .select("entry_id", "source", "version", "date", "text",
                "cluster_label", "themes", "umap_x", "umap_y")
    )
    mo.ui.data_explorer(clusters)


@app.cell
def _(mo):
    mo.md("## Mental models reference")


@app.cell
def _(mo, themes):
    mo.ui.data_explorer(themes.select(
        "name", "description", "first_seen_date", "member_codes",
        "supporting_blog_urls"
    ))


@app.cell
def _(mo):
    mo.md("## Ask the corpus")


@app.cell
def _(mo):
    from cmm.rag import chat_model
    mo.ui.chat(chat_model, prompts=[
        "What mental model shift did subagents require?",
        "Which features were later deprecated or removed?",
        "How did context management change over the year?",
    ])


if __name__ == "__main__":
    app.run()
