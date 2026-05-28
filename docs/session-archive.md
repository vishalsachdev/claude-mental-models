# Session Archive

Older session log entries, moved out of CLAUDE.md to keep that file focused.

---

## 2026-05-20 / 05-21
- Built v1 end-to-end (spec → plan → 12 tasks via subagent-driven dev): two-corpus
  pipeline, embeddings spine, two-stage thematic coding, RAG, marimo notebook.
  Merged to `main`.
- Council-validated the methodology; wrote `docs/methodology.md`; ran the
  cluster×theme cross-tab (confirmed abstract themes smear across clusters).
- Wrote the improvement plan (methodological rebuild).
- Next: resolve the 3 open questions, then brainstorm the rebuild into a spec.

---

## 2026-05-22 → 2026-05-26
- Brainstormed the rebuild into a spec (3 open questions resolved); plan through
  Codex Plan Reviewer (REJECT → R1 fixes → executed).
- Executed all 15 rebuild tasks via subagent-driven dev: A1–A3 corpus + embeddings,
  B1–B7 triangulated theme layer, C1–C4 reconciliation + presentation. Merged to main.
- 3 rounds of `codex review --base main`, 6 findings caught and fixed (P1 shallow-clone,
  P1 stale theme table, P2 blog counts, P2 embedding docs, P2 maintenance leak in heatmap).
- Notebook reframed as Why/How/What with per-chart narrative; persona lens added.
- Coherence finding: median 0.30 across 13 themes; only 2 (Permissions, MCP) clear 0.5.
