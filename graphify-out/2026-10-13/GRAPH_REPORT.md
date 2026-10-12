# Graph Report - curated-space  (2026-10-13)

## Corpus Check
- 108 files · ~111,488 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 45 file(s) not represented in the graph (top: .csv 20, (none) 15, .pkl 6)

## Summary
- 1071 nodes · 2828 edges · 77 communities (45 shown, 32 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 276 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6b1239f1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cost_layer.py
- routes/items.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- make_image
- middleware.py
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- Gemini screenshot extraction pipeline
- README.md
- datasets.py
- curated-ml
- Frozen evaluation datasets
- upload_item
- dataset.py
- model_card.py
- errors.py
- test_api_security.py
- ._validate
- Human-labeled holdout
- load_pricing_table
- SklearnSvcClassifier
- PipelineContext
- build_text
- test_jobs.py
- runner.py
- delete_item
- metrics.py
- GeminiExtractor
- budget.py
- test_evals.py
- routes/usage.py
- pipeline.py
- health.py
- report.py
- ExtractedMetadata
- typing
- Item
- create_app
- Backend + ML build progress
- deps.py
- Eval harness
- gemini.py
- test_blocked_and_truncated_responses_map_to_error_codes
- Milestone 6 verification
- Graphify project guidance
- app/main.py
- Settings
- train.py
- services/usage.py
- jobs.py
- test_classification.py
- ItemPatch
- LocalDiskStorage
- test_a_failing_item_is_a_data_0/synthetic/README.md
- test_a_second_pass_over_the_sa0/synthetic/README.md
- test_loader_reads_images_label0/synthetic/README.md
- test_loader_rejects_a_gold_lab0/synthetic/README.md
- test_loader_rejects_a_row_poin0/synthetic/README.md
- test_provider_label_and_classi0/synthetic/README.md
- test_report_carries_the_proven0/synthetic/README.md
- test_report_flags_a_synthetic_0/synthetic/README.md
- test_report_is_json_serializab0/synthetic/README.md
- test_report_prints_n_a_rather_0/synthetic/README.md
- test_runner_marks_an_unpriced_0/synthetic/README.md
- test_runner_scores_against_gol0/synthetic/README.md
- test_the_classifier_is_challen0/synthetic/README.md
- test_unlabeled_rows_still_load0/synthetic/README.md
- rate_limit.py
- ._read_label
- FakeExtractor

## God Nodes (most connected - your core abstractions)
1. `make_image()` - 61 edges
2. `Item` - 49 edges
3. `Settings` - 47 edges
4. `create_app()` - 44 edges
5. `GeminiExtractor` - 42 edges
6. `process_item()` - 39 edges
7. `ExtractedMetadata` - 38 edges
8. `sanitize_image()` - 36 edges
9. `ModelInput` - 33 edges
10. `_create_ready_item()` - 33 edges

## Surprising Connections (you probably didn't know these)
- `Milestone 7 verification (2026-10-13)` --references--> `read_bounded()`  [INFERRED]
  PROGRESS.md → backend/app/services/image_firewall.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `Milestone 5 verification` --references--> `ready()`  [INFERRED]
  PROGRESS.md → backend/app/api/routes/health.py

## Import Cycles
- None detected.

## Communities (77 total, 32 thin omitted)

### Community 0 - "test_cost_layer.py"
Cohesion: 0.15
Nodes (19): ExtractionError, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response(), _server_error(), test_400_is_not_retried() (+11 more)

### Community 1 - "routes/items.py"
Cohesion: 0.17
Nodes (6): list_items_route(), AcceptedItem, _as_utc(), ImageInfo, ItemListResponse, ItemResponse

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (15): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+7 more)

### Community 3 - "make_image"
Cohesion: 0.07
Nodes (60): AnimatedImageError, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale(), _encode(), _normalized() (+52 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 8 - "datasets.py"
Cohesion: 0.19
Nodes (7): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv(), evaluate_holdout()

### Community 11 - "upload_item"
Cohesion: 0.18
Nodes (4): reanalyze_item(), upload_item(), JobRunner, 8. Pipeline, jobs, API

### Community 12 - "dataset.py"
Cohesion: 0.08
Nodes (17): synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load(), EvalItem (+9 more)

### Community 13 - "model_card.py"
Cohesion: 0.21
Nodes (10): test_abstains_on_ambiguous_text_and_returns_no_labels(), test_development_warns_instead_of_refusing(), test_model_card_roundtrips(), test_production_refuses_a_sklearn_version_mismatch(), test_shipped_card_records_unvalidated_threshold(), card_path_for(), ClassMetrics, ModelCard (+2 more)

### Community 14 - "errors.py"
Cohesion: 0.15
Nodes (7): AppError, BadRequestError, ConflictError, ErrorBody, ErrorResponse, NotFoundError, list_items()

### Community 22 - "test_api_security.py"
Cohesion: 0.20
Nodes (5): FakeExtractor, test_app_body_limit_and_cors_allowlist(), test_other_owner_cannot_read_image_edit_delete_or_reanalyze(), test_skip_analysis_stores_owner_bound_deferred_item_without_provider_call(), test_upload_rate_limit_is_enforced_per_key_and_ip()

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "load_pricing_table"
Cohesion: 0.13
Nodes (10): estimate_cost_usd(), load_pricing_table(), ModelPrice, PricingTable, test_default_model_is_priced(), test_every_benchmarked_model_is_priced(), test_known_price_arithmetic(), test_price_table_records_provenance() (+2 more)

### Community 26 - "SklearnSvcClassifier"
Cohesion: 0.08
Nodes (13): build_classifier(), Classifier, Prediction, ClassifierLoadError, ClassifierStatus, SklearnSvcClassifier, UnavailableClassifier, test_build_classifier_falls_back_in_development() (+5 more)

### Community 27 - "PipelineContext"
Cohesion: 0.13
Nodes (6): BackgroundJobRunner, _apply_classification(), _budget_deferral(), _complete(), PipelineContext, Milestone 8 verification (2026-10-13)

### Community 28 - "build_text"
Cohesion: 0.18
Nodes (9): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), normalize_tags() (+1 more)

### Community 29 - "test_jobs.py"
Cohesion: 0.36
Nodes (4): create_database_engine(), create_session_factory(), test_app_startup_requeues_stale_processing_item(), test_recovery_resets_only_stale_processing_and_returns_pending_ids()

### Community 30 - "runner.py"
Cohesion: 0.11
Nodes (12): EvalConfig, agreement(), LabelMetrics, summarize_to_dict(), _error_code(), ItemRecord, PreparedInput, run_config() (+4 more)

### Community 31 - "delete_item"
Cohesion: 0.24
Nodes (5): delete_item(), get_item(), get_item_image(), _owned_item(), patch_item()

### Community 32 - "metrics.py"
Cohesion: 0.16
Nodes (12): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), test_percentiles_are_deterministic(), ClassScore, CostMetrics, LabelObservation (+4 more)

### Community 33 - "GeminiExtractor"
Cohesion: 0.14
Nodes (3): ExtractionUnavailableError, GeminiExtractor, test_extractor_cache_identity_tracks_the_label_flag()

### Community 34 - "budget.py"
Cohesion: 0.29
Nodes (6): BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), test_budget_allows_a_fresh_daily_budget(), test_yesterday_spend_does_not_count_towards_today()

### Community 35 - "test_evals.py"
Cohesion: 0.10
Nodes (20): DictCache, _prepare(), __init__(), _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call(), test_cache_identity_includes_everything_that_changes_the_answer() (+12 more)

### Community 36 - "routes/usage.py"
Cohesion: 0.21
Nodes (4): get_usage(), UsageResponse, UsageWindow, UsageBucket

### Community 37 - "pipeline.py"
Cohesion: 0.14
Nodes (13): AnalysisCache, Base, utcnow(), cache_key(), lookup(), store(), CacheIdentity, create_item() (+5 more)

### Community 38 - "health.py"
Cohesion: 0.18
Nodes (9): _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status(), 13a. Demo acceptance and targets (+1 more)

### Community 39 - "report.py"
Cohesion: 0.23
Nodes (7): _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "ExtractedMetadata"
Cohesion: 0.23
Nodes (9): ExtractedMetadata, sanitize_metadata(), test_rejects_oversized_title(), test_rejects_short_tag(), test_rejects_too_many_tags(), test_sanitize_drops_tags_that_normalize_to_nothing(), test_sanitize_lowercases_and_dedupes_tags(), test_sanitize_rejects_empty_after_cleaning() (+1 more)

### Community 41 - "typing"
Cohesion: 0.08
Nodes (14): _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main(), Prepared, _run_one() (+6 more)

### Community 42 - "Item"
Cohesion: 0.18
Nodes (25): Item, _finish(), process_item(), _seed_usage(), test_cache_hit_still_serves_under_a_budget_block(), test_cache_hits_do_not_consume_rate_budget(), test_cache_miss_when_versions_change(), test_daily_cap_defers_the_item() (+17 more)

### Community 43 - "create_app"
Cohesion: 0.18
Nodes (4): create_app(), lifespan(), retain_task(), 6. Classifier (`services/classification/` + `ml/src/curated_ml`)

### Community 44 - "Backend + ML build progress"
Cohesion: 0.18
Nodes (9): Backend + ML build progress, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone 7 verification (2026-10-13), Milestone 9 implementation (2026-10-13) (+1 more)

### Community 46 - "deps.py"
Cohesion: 0.17
Nodes (9): get_classifier(), get_current_owner(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), AuthenticationError (+1 more)

### Community 47 - "Eval harness"
Cohesion: 0.29
Nodes (6): Eval harness, Labeling a set, Layout, Running it, The synthetic set, What the report contains

### Community 48 - "gemini.py"
Cohesion: 0.18
Nodes (4): ExtractionResult, build_labeled_schema(), _clean_text(), test_labeled_schema_enum_is_built_from_the_taxonomy()

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "Graphify project guidance"
Cohesion: 0.83
Nodes (3): Graphify project guidance, Curated Space backend guidance, Curated Space screenshot knowledge library

### Community 53 - "Settings"
Cohesion: 0.06
Nodes (26): get_settings(), Settings, get_session(), make_database_url(), run_migrations_offline(), run_migrations_online(), _create_items_table(), _create_supporting_tables() (+18 more)

### Community 54 - "train.py"
Cohesion: 0.09
Nodes (8): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main(), assert_labels_match_taxonomy(), build_model(), evaluate(), main(), parse_args()

### Community 55 - "services/usage.py"
Cohesion: 0.16
Nodes (11): LLMUsage, TokenUsage, estimate_cost_usd(), record_cache_hit(), record_usage(), summarize_usage(), _unknown_cost_models(), usage_windows() (+3 more)

### Community 56 - "jobs.py"
Cohesion: 0.16
Nodes (3): purge_expired_items(), recover_interrupted_items(), Storage

### Community 57 - "test_classification.py"
Cohesion: 0.17
Nodes (9): test_legacy_taxonomy_has_eight_unique_labels(), test_missing_card_raises(), test_model_card_path_sits_next_to_the_artifact(), test_realistic_eval_is_not_the_legacy_taxonomy(), test_refuses_numeric_classes_rather_than_guessing(), test_taxonomy_rejects_duplicate_labels(), test_taxonomy_rejects_missing_version(), load_taxonomy() (+1 more)

### Community 59 - "LocalDiskStorage"
Cohesion: 0.27
Nodes (3): LocalDiskStorage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 76 - "rate_limit.py"
Cohesion: 0.31
Nodes (3): RateLimitError, enforce_rate_limit(), FixedWindowRateLimiter

### Community 78 - "._read_label"
Cohesion: 0.20
Nodes (5): validate_labels(), _Parsed, test_label_reading_is_off_unless_asked_for(), test_labeled_extractor_reads_and_validates_the_provider_label(), test_validate_labels_accepts_a_case_variant_and_refuses_an_invented_one()

## Knowledge Gaps
- **5 isolated node(s):** `curated-space-backend`, `curated-ml`, `Frozen evaluation datasets`, `TF-IDF and LinearSVC challenger`, `Intent and Domain taxonomy`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_cost_layer.py`, `GeminiExtractor`, `budget.py`, `make_image`, `pipeline.py`, `typing`, `Item`, `create_app`, `deps.py`, `gemini.py`, `app/main.py`, `services/usage.py`, `test_classification.py`, `SklearnSvcClassifier`, `PipelineContext`, `test_jobs.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `Item` (e.g. with `_owned_item()` and `ItemResponse`) actually correct?**
  _`Item` has 28 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `curated-ml`, `Frozen evaluation datasets` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Why does `GeminiExtractor` connect `GeminiExtractor` to `test_cost_layer.py`, `test_evals.py`, `pipeline.py`, `health.py`, `ExtractedMetadata`, `typing`, `Item`, `create_app`, `._labels_enabled`, `._read_label`, `gemini.py`, `test_blocked_and_truncated_responses_map_to_error_codes`, `app/main.py`, `Settings`, `services/usage.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_pipeline_context()`) actually correct?**
  _`Settings` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Should `make_image` be split into smaller, more focused modules?**
  _Cohesion score 0.07056798623063683 - nodes in this community are weakly interconnected._