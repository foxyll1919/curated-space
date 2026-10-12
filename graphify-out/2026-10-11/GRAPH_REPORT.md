# Graph Report - curated-space  (2026-10-11)

## Corpus Check
- 63 files · ~68,977 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .csv 2, .pkl 2, (none) 1)

## Summary
- 557 nodes · 1433 edges · 25 communities (12 shown, 13 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 129 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6b1239f1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- GeminiExtractor
- test_pipeline.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- conftest.py
- sanitize_image
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- Gemini screenshot extraction pipeline
- README.md
- train.py
- curated-ml
- Frozen evaluation datasets
- test_items_api.py
- json
- test_classification.py
- LocalDiskStorage
- Backend + ML build progress
- _DecisionModel
- Human-labeled holdout

## God Nodes (most connected - your core abstractions)
1. `Settings` - 37 edges
2. `sanitize_image()` - 31 edges
3. `make_image()` - 29 edges
4. `create_app()` - 28 edges
5. `Item` - 27 edges
6. `process_item()` - 26 edges
7. `GeminiExtractor` - 25 edges
8. `ExtractedMetadata` - 25 edges
9. `SklearnSvcClassifier` - 24 edges
10. `upload_item()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Decisions and constraints` --references--> `build_text()`  [INFERRED]
  PROGRESS.md → ml/src/curated_ml/text.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `Item`  [INFERRED]
  build.md → backend/app/db/models.py
- `6. Classifier (`services/classification/` + `ml/src/curated_ml`)` --references--> `Classifier`  [INFERRED]
  build.md → backend/app/services/classification/base.py

## Import Cycles
- None detected.

## Communities (25 total, 13 thin omitted)

### Community 0 - "GeminiExtractor"
Cohesion: 0.07
Nodes (19): ExtractionUnavailableError, ExtractionResult, ModelInput, TokenUsage, GeminiExtractor, _clean_text(), ExtractedMetadata, sanitize_metadata() (+11 more)

### Community 1 - "test_pipeline.py"
Cohesion: 0.06
Nodes (40): get_classifier(), get_extractor(), get_pipeline_context(), get_settings_dep(), get_storage(), get_item(), list_items_route(), upload_item() (+32 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.07
Nodes (29): Graphify project guidance, Curated Space backend guidance, _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse (+21 more)

### Community 3 - "conftest.py"
Cohesion: 0.06
Nodes (22): get_settings(), create_database_engine(), create_session_factory(), get_session(), make_database_url(), create_app(), run_migrations_offline(), run_migrations_online() (+14 more)

### Community 4 - "sanitize_image"
Cohesion: 0.09
Nodes (33): AnimatedImageError, AppError, BadRequestError, ErrorBody, ErrorResponse, PayloadTooLargeError, UnprocessableImageError, UnsupportedMediaTypeError (+25 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 8 - "train.py"
Cohesion: 0.08
Nodes (12): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv(), assert_labels_match_taxonomy(), build_model() (+4 more)

### Community 11 - "test_items_api.py"
Cohesion: 0.20
Nodes (19): LLMUsage, make_image(), test_analysis_disabled_defers_the_item(), test_item_is_fetched_by_id(), test_list_filters_by_status(), test_list_hides_items_owned_by_someone_else(), test_list_paginates_newest_first(), test_prompt_injection_image_still_yields_validated_metadata() (+11 more)

### Community 12 - "json"
Cohesion: 0.10
Nodes (14): configure_logging(), JsonFormatter, _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade() (+6 more)

### Community 13 - "test_classification.py"
Cohesion: 0.05
Nodes (35): build_classifier(), Prediction, ClassifierLoadError, ClassifierStatus, SklearnSvcClassifier, UnavailableClassifier, test_abstains_on_ambiguous_text_and_returns_no_labels(), test_build_classifier_falls_back_in_development() (+27 more)

### Community 22 - "Backend + ML build progress"
Cohesion: 0.22
Nodes (7): Backend + ML build progress, Decisions and constraints, Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone status, Open questions for the owner

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

## Knowledge Gaps
- **5 isolated node(s):** `curated-space-backend`, `curated-ml`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger`, `Intent and Domain taxonomy`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 194 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `test_pipeline.py` to `GeminiExtractor`, `conftest.py`, `sanitize_image`, `test_classification.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Settings` (e.g. with `get_pipeline_context()` and `get_settings_dep()`) actually correct?**
  _`Settings` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `curated-ml`, `Frozen evaluation datasets` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `GeminiExtractor` be split into smaller, more focused modules?**
  _Cohesion score 0.06612021857923497 - nodes in this community are weakly interconnected._
- **Why does `Item` connect `test_pipeline.py` to `Curated Space — Backend + ML Build Brief (for the coding agent)`, `test_items_api.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `create_app()` (e.g. with `Settings` and `AppError`) actually correct?**
  _`create_app()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055921855921855924 - nodes in this community are weakly interconnected._