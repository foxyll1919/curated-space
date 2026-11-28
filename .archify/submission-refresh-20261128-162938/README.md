# Diagram refresh for submission (2026-11-28)

The nine diagrams under `.archify/` were authored against revision `eb07f33`.
Five commits landed after that, so this folder holds rebuilt versions of the six
diagrams whose content changed. Every source citation is pinned to the current
`HEAD` (`c139892`) instead of `eb07f33`.

The earlier HTML files are untouched. Use the files below for submission.

## Rebuilt diagrams

| Diagram | File | What changed |
|---|---|---|
| 3.2.2 Agent Workflow | `3-2-2-agent-workflow/agent-workflow.html` | Supervisor now rewrites then routes; the LangChain tool node became a direct-call retrieval node; removed the "IDs discarded / retrieval runs again" claim; added follow-up rewrite card. |
| 3.2.7 User–Agent–LLM Sequence | `3-2-7-agent-sequence/agent-sequence.html` | Added rewrite and route calls; removed the tool round-trip and duplicate retrieval; retrieval calls the search functions once; added citation filtering and 0.35 cutoff notes. |
| 3.2.8 Agent State | `3-2-8-agent-state/agent-state.html` | Renamed "Invoke Search Tool" to direct search calls; "Rewrite + Route" supervisor; ranked results with cutoff; still one pass, no reasoning loop. |
| 3.2.5 RAG Pipeline | `3-2-5-rag-pipeline/rag-pipeline.html` | Added query rewrite stage, Postgres/SQLite index, 0.35 similarity cutoff, AND→OR keyword fallback and citation filtering. |
| 3.2.4 DFD Level 1 | `3-2-4-dfd-level-1/dfd-level-1.html` | Supabase Storage / local disk and Postgres / SQLite fallback replace the SQLite-only, local-disk-only stores; Ask path and session auth included. |
| Curated Space Runtime Architecture | `runtime-architecture/curated-space-runtime.html` | Added the Ask agent and session-auth path; Supabase Storage and Postgres/SQLite stores; boundary renamed from "local data" to backend and managed data stores. |

## Unchanged

These were checked against current source and remain accurate, so their original
files still apply:

- `3-2-3-use-case-view/use-case-view.html`
- `3-2-4-dfd-level-0/dfd-level-0.html`
- `sequence-local-origin-check-20261125-032522/local-origin-check.html`

## Verification

Every rebuilt diagram passed the Archify `finalize` gates: validate, deliver,
strict check and real-browser check. Receipts sit beside each candidate as
`*.finalize.json`, `*.finalize-summary.json` and `*.browser-check.json`.

The runtime architecture passes the automated gates but the layout check still
reports crossings around the `api` component (accounts, items, jobs, disk and
Ask all leave one side). It is usable, and the suggested reflow was attempted and
reverted because it introduced overlapping nodes. Treat that one as visually
reviewed by a human before submission.

## Key source references

- `backend/app/services/agent.py` — rewrite → route → retrieval → answer, no tool layer.
- `backend/app/services/retrieval.py` — 0.35 similarity cutoff, AND→OR fallback, dialect-aware keyword search.
- `backend/app/api/routes/intelligence.py` — `/ask` and `/agent` history, citation filtering.
- `backend/app/db/session.py`, `backend/app/services/storage.py` — Postgres and Supabase Storage with local fallbacks.
