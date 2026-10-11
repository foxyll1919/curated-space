# Graph Report - curated-space  (2026-10-11)

## Corpus Check
- 19 files · ~56,089 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .csv 2, (none) 1, .lock 1)

## Summary
- 88 nodes · 110 edges · 12 communities (4 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- gemini_service.py
- main.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- test_health.py
- Graphify project guidance
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- Gemini screenshot extraction pipeline
- README.md
- curated-space-backend
- Frozen evaluation datasets
- True-crime thriller movie poster collage

## God Nodes (most connected - your core abstractions)
1. `Curated Space — Backend + ML Build Brief (for the coding agent)` - 18 edges
2. `Item` - 6 edges
3. `analyze_image()` - 5 edges
4. `create_item()` - 5 edges
5. `Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?` - 4 edges
6. `get_items()` - 3 edges
7. `build_text()` - 3 edges
8. `Graphify project guidance` - 3 edges
9. `Curated Space backend guidance` - 3 edges
10. `Gemini screenshot extraction pipeline` - 3 edges

## Surprising Connections (you probably didn't know these)
- `4. Data model (replace the current `Item`)` --references--> `Item`  [INFERRED]
  build.md → backend/models.py
- `13. Milestones (one PR each, in this order)` --references--> `build_text()`  [INFERRED]
  build.md → ml/legacy/eval_realistic.py
- `6. Classifier (`services/classification/` + `ml/src/curated_ml`)` --references--> `build_text()`  [INFERRED]
  build.md → ml/legacy/eval_realistic.py
- `Curated Space backend guidance` --references--> `Graphify project guidance`  [EXTRACTED]
  backend/AGENTS.md → AGENTS.md
- `Curated Space backend guidance` --references--> `Curated Space screenshot knowledge library`  [EXTRACTED]
  backend/AGENTS.md → readme.md

## Import Cycles
- None detected.

## Communities (12 total, 8 thin omitted)

### Community 1 - "main.py"
Cohesion: 0.16
Nodes (6): create_item(), get_items(), health(), home(), Item, 4. Data model (replace the current `Item`)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (18): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 13a. Demo acceptance and targets, 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate) (+10 more)

### Community 4 - "Graphify project guidance"
Cohesion: 0.83
Nodes (3): Graphify project guidance, Curated Space backend guidance, Curated Space screenshot knowledge library

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

## Knowledge Gaps
- **5 isolated node(s):** `curated-space-backend`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger`, `True-crime thriller movie poster collage`, `Intent and Domain taxonomy`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 43 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Curated Space — Backend + ML Build Brief (for the coding agent)` connect `Curated Space — Backend + ML Build Brief (for the coding agent)` to `main.py`, `Graphify project guidance`?**
  _High betweenness centrality (0.490) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Item` (e.g. with `create_item()` and `get_items()`) actually correct?**
  _`Item` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Why does `build_text()` connect `Curated Space — Backend + ML Build Brief (for the coding agent)` to `benchmark.py`?**
  _High betweenness centrality (0.329) - this node is a cross-community bridge._
- **Why does `4. Data model (replace the current `Item`)` connect `main.py` to `Curated Space — Backend + ML Build Brief (for the coding agent)`?**
  _High betweenness centrality (0.294) - this node is a cross-community bridge._