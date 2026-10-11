# Graph Report - curated-space  (2026-10-11)

## Corpus Check
- 32 files · ~58,206 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: .csv 2, (none) 1, .ini 1)

## Summary
- 166 nodes · 260 edges · 22 communities (8 shown, 14 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- gemini_service.py
- models.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- app/main.py
- Graphify project guidance
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- Gemini screenshot extraction pipeline
- README.md
- curated-space-backend
- Frozen evaluation datasets
- ready
- 0001_backend_foundation.py
- True-crime thriller movie poster collage
- test_foundation.py
- logging.py

## God Nodes (most connected - your core abstractions)
1. `Curated Space — Backend + ML Build Brief (for the coding agent)` - 18 edges
2. `create_app()` - 13 edges
3. `ready()` - 10 edges
4. `Settings` - 9 edges
5. `get_settings()` - 7 edges
6. `make_database_url()` - 7 edges
7. `create_database_engine()` - 7 edges
8. `upgrade()` - 7 edges
9. `Base` - 6 edges
10. `create_session_factory()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `Item`  [INFERRED]
  build.md → backend/app/db/models.py
- `6. Classifier (`services/classification/` + `ml/src/curated_ml`)` --references--> `lifespan()`  [INFERRED]
  build.md → backend/app/main.py

## Import Cycles
- None detected.

## Communities (22 total, 14 thin omitted)

### Community 1 - "models.py"
Cohesion: 0.27
Nodes (5): AnalysisCache, Base, Item, LLMUsage, 4. Data model (replace the current `Item`)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.10
Nodes (21): lifespan(), 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate) (+13 more)

### Community 3 - "app/main.py"
Cohesion: 0.11
Nodes (10): get_settings(), Settings, configure_logging(), create_database_engine(), create_session_factory(), get_session(), make_database_url(), create_app() (+2 more)

### Community 4 - "Graphify project guidance"
Cohesion: 0.83
Nodes (3): Graphify project guidance, Curated Space backend guidance, Curated Space screenshot knowledge library

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 11 - "ready"
Cohesion: 0.18
Nodes (8): _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status(), 13a. Demo acceptance and targets, 8. Pipeline, jobs, API

### Community 12 - "0001_backend_foundation.py"
Cohesion: 0.40
Nodes (6): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade()

### Community 14 - "test_foundation.py"
Cohesion: 0.33
Nodes (4): _migrate(), _migration_config(), test_migration_preserves_legacy_item_fields(), test_readiness_checks_schema_and_storage()

## Knowledge Gaps
- **5 isolated node(s):** `curated-space-backend`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger`, `True-crime thriller movie poster collage`, `Intent and Domain taxonomy`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 72 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Curated Space — Backend + ML Build Brief (for the coding agent)` connect `Curated Space — Backend + ML Build Brief (for the coding agent)` to `models.py`, `ready`, `Graphify project guidance`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `create_app()` (e.g. with `Settings` and `lifespan()`) actually correct?**
  _`create_app()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Why does `build_text()` connect `Curated Space — Backend + ML Build Brief (for the coding agent)` to `benchmark.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ready()` (e.g. with `13a. Demo acceptance and targets` and `4. Data model (replace the current `Item`)`) actually correct?**
  _`ready()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `app/main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10634920634920635 - nodes in this community are weakly interconnected._