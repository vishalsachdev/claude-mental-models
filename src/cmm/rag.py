# src/cmm/rag.py
"""Retriever over the embeddings spine + a Claude chat model for marimo."""
from pathlib import Path

import numpy as np
import polars as pl
from sentence_transformers import SentenceTransformer

from cmm.embed_cluster import EMBED_MODEL
from cmm.llm import complete

_model: SentenceTransformer | None = None
_corpus: pl.DataFrame | None = None
_matrix: np.ndarray | None = None

RAG_SYSTEM = (
    "You answer questions about how Claude Code's features evolved and what "
    "competencies and expectations the tool's surface increasingly demanded "
    "of its users (organized under a 'mental models' lens — a framing, not a "
    "measured claim about individual developers). Answer ONLY from the "
    "provided context. Cite changelog versions and blog URLs inline. If the "
    "context does not contain the answer, say so."
)


def _load(embeddings: Path = Path("data/processed/embeddings.parquet")):
    global _model, _corpus, _matrix
    if _corpus is None:
        _corpus = pl.read_parquet(embeddings)
        _matrix = np.array(_corpus["vector"].to_list())
        _model = SentenceTransformer(EMBED_MODEL)


def retrieve(question: str, k: int = 8) -> pl.DataFrame:
    """Return the k most similar corpus rows to the question."""
    _load()
    q = _model.encode([question])[0]
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        raise ValueError("query embedding is a zero vector")
    sims = _matrix @ q / (np.linalg.norm(_matrix, axis=1) * q_norm)
    top = np.argsort(sims)[::-1][:k]
    return _corpus[top.tolist()]


def answer(question: str, themes_path: Path = Path("data/processed/themes.parquet")) -> str:
    """Retrieve context and have Claude answer, grounded with citations.

    The named mental-model themes (only ~6-10) are always included in full so
    the model can frame answers against them; retrieved changelog/blog rows
    carry their version + date for inline citation.
    """
    hits = retrieve(question)
    themes = pl.read_parquet(themes_path)
    theme_block = "\n".join(
        f"- {t['name']}: {t['description']}" for t in themes.iter_rows(named=True)
    )
    # Changelog rows cite `version`; blog rows cite their URL (stored in
    # entry_id). Always give the model the exact citation token to use.
    context = "\n\n".join(
        f"[{r['source']} | "
        f"{'version ' + r['version'] if r['version'] else r['entry_id']} | "
        f"{r['date']}] {r['text'][:600]}"
        for r in hits.iter_rows(named=True)
    )
    prompt = (f"Mental-model themes:\n{theme_block}\n\n"
              f"Retrieved context:\n{context}\n\nQuestion: {question}")
    return complete(prompt, system=RAG_SYSTEM, max_tokens=1500)


def chat_model(messages, config) -> str:
    """marimo `mo.ui.chat` custom model: answer the latest user message."""
    return answer(messages[-1].content)
