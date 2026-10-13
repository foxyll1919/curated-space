# Graph Report - curated-space  (2026-10-13)

## Corpus Check
- 165 files · ~129,752 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 48 file(s) not represented in the graph (top: .csv 20, (none) 16, .pkl 6)

## Summary
- 1504 nodes · 3718 edges · 95 communities (63 shown, 32 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 279 edges (avg confidence: 0.93)
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
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- api.ts
- README.md
- train.py
- curated-ml
- ItemDetailDialog.tsx
- upload_item
- dataset.py
- model_card.py
- AppError
- test_api_security.py
- ._validate
- Human-labeled holdout
- test_evals.py
- SklearnSvcClassifier
- PipelineContext
- build_text
- react
- runner.py
- list_items_route
- App.tsx
- GeminiExtractor
- LLMUsage
- EvalConfig
- summarize_usage
- pipeline.py
- health.py
- report.py
- LibraryPage.tsx
- run.py
- Item
- create_app
- Backend + ML build progress
- LibraryControls.tsx
- deps.py
- Eval harness
- compilerOptions
- test_blocked_and_truncated_responses_map_to_error_codes
- Milestone 6 verification
- components.json
- app/main.py
- Settings
- benchmark.py
- field.tsx
- compilerOptions
- test_classification.py
- ItemPatch
- Storage
- command.tsx
- UploadSurface.tsx
- package.json
- test_foundation.py
- core/config.py
- dependencies
- Curated Space frontend
- select.tsx
- ready
- sqlalchemy
- devDependencies
- scripts
- .oxlintrc.json
- tsconfig.json
- gemini.py
- vite.config.ts
- JobRunner
- FakeExtractor
- read_bounded
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

## God Nodes (most connected - your core abstractions)
1. `make_image()` - 61 edges
2. `Item` - 48 edges
3. `Settings` - 47 edges
4. `create_app()` - 44 edges
5. `GeminiExtractor` - 42 edges
6. `process_item()` - 39 edges
7. `ExtractedMetadata` - 38 edges
8. `sanitize_image()` - 36 edges
9. `react` - 34 edges
10. `ModelInput` - 33 edges

## Surprising Connections (you probably didn't know these)
- `Decisions and constraints` --references--> `build_text()`  [INFERRED]
  PROGRESS.md → ml/src/curated_ml/text.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `Milestone 5 verification` --references--> `ready()`  [INFERRED]
  PROGRESS.md → backend/app/api/routes/health.py
- `6. Classifier (`services/classification/` + `ml/src/curated_ml`)` --references--> `Classifier`  [INFERRED]
  build.md → backend/app/services/classification/base.py

## Import Cycles
- None detected.

## Communities (95 total, 32 thin omitted)

### Community 0 - "test_cost_layer.py"
Cohesion: 0.16
Nodes (18): ExtractionError, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response(), _server_error(), test_400_is_not_retried() (+10 more)

### Community 1 - "routes/items.py"
Cohesion: 0.25
Nodes (6): get_item(), AcceptedItem, _as_utc(), ImageInfo, ItemListResponse, ItemResponse

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.13
Nodes (14): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+6 more)

### Community 3 - "make_image"
Cohesion: 0.07
Nodes (61): AnimatedImageError, ErrorBody, ErrorResponse, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale() (+53 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "api.ts"
Cohesion: 0.06
Nodes (41): ItemCardInner(), MASONRY_CAPTION_PX, MasonryItemProps, CardFooter(), PendingCard(), PendingCardProps, STATUS_CHIP, StatusChip() (+33 more)

### Community 8 - "train.py"
Cohesion: 0.13
Nodes (12): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv(), assert_labels_match_taxonomy(), build_model() (+4 more)

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.15
Nodes (24): EditForm(), Field(), ItemDetailBody(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent(), AlertDialogDescription() (+16 more)

### Community 11 - "upload_item"
Cohesion: 0.16
Nodes (5): delete_item(), get_item_image(), _owned_item(), reanalyze_item(), upload_item()

### Community 12 - "dataset.py"
Cohesion: 0.08
Nodes (17): synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), EvalItem, EvalSetError (+9 more)

### Community 13 - "model_card.py"
Cohesion: 0.21
Nodes (10): test_abstains_on_ambiguous_text_and_returns_no_labels(), test_development_warns_instead_of_refusing(), test_model_card_roundtrips(), test_production_refuses_a_sklearn_version_mismatch(), test_shipped_card_records_unvalidated_threshold(), card_path_for(), ClassMetrics, ModelCard (+2 more)

### Community 14 - "AppError"
Cohesion: 0.25
Nodes (4): patch_item(), AppError, ConflictError, NotFoundError

### Community 22 - "test_api_security.py"
Cohesion: 0.18
Nodes (6): ExtractionResult, FakeExtractor, test_app_body_limit_and_cors_allowlist(), test_other_owner_cannot_read_image_edit_delete_or_reanalyze(), test_skip_analysis_stores_owner_bound_deferred_item_without_provider_call(), test_upload_rate_limit_is_enforced_per_key_and_ip()

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "test_evals.py"
Cohesion: 0.08
Nodes (15): estimate_cost_usd(), load_pricing_table(), ModelPrice, PricingTable, DictCache, test_cache_identity_includes_everything_that_changes_the_answer(), test_default_model_is_priced(), test_every_benchmarked_model_is_priced() (+7 more)

### Community 26 - "SklearnSvcClassifier"
Cohesion: 0.07
Nodes (14): build_classifier(), Classifier, Prediction, ClassifierLoadError, ClassifierStatus, SklearnSvcClassifier, UnavailableClassifier, FakeClassifier (+6 more)

### Community 27 - "PipelineContext"
Cohesion: 0.19
Nodes (5): BackgroundJobRunner, _budget_deferral(), _finish(), PipelineContext, Milestone 8 verification (2026-10-13)

### Community 28 - "build_text"
Cohesion: 0.19
Nodes (8): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), normalize_tags()

### Community 29 - "react"
Cohesion: 0.14
Nodes (17): buttonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), InputGroupTextarea(), Input(), ScrollArea(), ScrollBar() (+9 more)

### Community 30 - "runner.py"
Cohesion: 0.09
Nodes (22): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), agreement(), ClassScore, CostMetrics, LabelMetrics (+14 more)

### Community 31 - "list_items_route"
Cohesion: 0.17
Nodes (3): list_items_route(), BadRequestError, list_items()

### Community 32 - "App.tsx"
Cohesion: 0.13
Nodes (19): App(), queryClient, router, ItemDetailDialog(), Empty(), EmptyContent(), EmptyDescription(), EmptyHeader() (+11 more)

### Community 33 - "GeminiExtractor"
Cohesion: 0.06
Nodes (20): ExtractionUnavailableError, GeminiExtractor, build_labeled_schema(), _clean_text(), ExtractedMetadata, sanitize_metadata(), validate_labels(), _Parsed (+12 more)

### Community 34 - "LLMUsage"
Cohesion: 0.29
Nodes (7): LLMUsage, BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), test_budget_allows_a_fresh_daily_budget(), test_yesterday_spend_does_not_count_towards_today()

### Community 35 - "EvalConfig"
Cohesion: 0.11
Nodes (17): _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call(), test_provider_label_and_classifier_label_agreement_is_reported(), test_report_carries_the_provenance_a_reader_needs(), test_report_flags_a_synthetic_set_loudly(), test_report_is_json_serializable_and_holds_no_metadata() (+9 more)

### Community 36 - "summarize_usage"
Cohesion: 0.14
Nodes (8): get_usage(), UsageResponse, UsageWindow, summarize_usage(), _unknown_cost_models(), usage_windows(), UsageBucket, test_summarize_usage_separates_failures()

### Community 37 - "pipeline.py"
Cohesion: 0.09
Nodes (21): AnalysisCache, Base, utcnow(), cache_key(), lookup(), store(), CacheIdentity, TokenUsage (+13 more)

### Community 38 - "health.py"
Cohesion: 0.28
Nodes (4): health(), HealthResponse, ReadyResponse, _storage_status()

### Community 39 - "report.py"
Cohesion: 0.26
Nodes (7): _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "LibraryPage.tsx"
Cohesion: 0.16
Nodes (22): ItemCard, MasonryItem(), InfiniteScrollSentinel(), Alert(), AlertDescription(), AlertTitle(), alertVariants, Skeleton() (+14 more)

### Community 41 - "run.py"
Cohesion: 0.09
Nodes (14): _prepare(), __init__(), _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main() (+6 more)

### Community 42 - "Item"
Cohesion: 0.18
Nodes (25): Item, process_item(), _seed_usage(), test_cache_hit_still_serves_under_a_budget_block(), test_cache_hits_do_not_consume_rate_budget(), test_cache_miss_when_versions_change(), test_daily_cap_defers_the_item(), test_disabled_cache_always_calls_the_provider() (+17 more)

### Community 43 - "create_app"
Cohesion: 0.12
Nodes (10): create_database_engine(), create_session_factory(), create_app(), lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task(), test_app_startup_requeues_stale_processing_item() (+2 more)

### Community 44 - "Backend + ML build progress"
Cohesion: 0.18
Nodes (9): Backend + ML build progress, Decisions and constraints, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone 9 implementation (2026-10-13) (+1 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.14
Nodes (21): Filters, LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), ServerStrip(), Verdict, VERDICT_DOT (+13 more)

### Community 46 - "deps.py"
Cohesion: 0.19
Nodes (9): get_classifier(), get_current_owner(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), AuthenticationError (+1 more)

### Community 47 - "Eval harness"
Cohesion: 0.29
Nodes (6): Eval harness, Labeling a set, Layout, Running it, The synthetic set, What the report contains

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "app/main.py"
Cohesion: 0.12
Nodes (3): configure_logging(), JsonFormatter, RequestSecurityMiddleware

### Community 53 - "Settings"
Cohesion: 0.16
Nodes (10): Settings, classifier(), client(), extractor(), make_settings(), migrated_settings(), migration_config(), _live_settings() (+2 more)

### Community 54 - "benchmark.py"
Cohesion: 0.11
Nodes (3): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main()

### Community 55 - "field.tsx"
Cohesion: 0.13
Nodes (11): AppShell(), NAV, currentTheme(), Theme, ThemeToggle(), toggle(), Field(), FieldLabel() (+3 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 57 - "test_classification.py"
Cohesion: 0.21
Nodes (8): test_legacy_taxonomy_has_eight_unique_labels(), test_missing_card_raises(), test_model_card_path_sits_next_to_the_artifact(), test_realistic_eval_is_not_the_legacy_taxonomy(), test_refuses_numeric_classes_rather_than_guessing(), test_taxonomy_rejects_duplicate_labels(), test_taxonomy_rejects_missing_version(), load_taxonomy()

### Community 59 - "Storage"
Cohesion: 0.14
Nodes (4): LocalDiskStorage, Storage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 60 - "command.tsx"
Cohesion: 0.19
Nodes (13): CommandDialog(), CommandInput(), Dialog(), DialogContent(), DialogDescription(), DialogHeader(), DialogOverlay(), DialogPortal() (+5 more)

### Community 61 - "UploadSurface.tsx"
Cohesion: 0.16
Nodes (17): Switch(), JOB_TEXT, looksLikeImage(), readFiles(), UploadSurface(), onDrop(), onPaste(), UploadSurfaceProps (+9 more)

### Community 62 - "package.json"
Cohesion: 0.13
Nodes (14): name, private, type, version, cmdk, next-themes, openapi-typescript, oxlint (+6 more)

### Community 64 - "test_foundation.py"
Cohesion: 0.19
Nodes (4): _migrate(), _migration_config(), test_migration_preserves_legacy_item_fields(), test_readiness_checks_schema_and_storage()

### Community 65 - "core/config.py"
Cohesion: 0.24
Nodes (5): get_settings(), get_session(), make_database_url(), run_migrations_offline(), run_migrations_online()

### Community 66 - "dependencies"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, cmdk, cn, lucide-react, next-themes, radix-ui, react (+6 more)

### Community 67 - "Curated Space frontend"
Cohesion: 0.18
Nodes (10): Curated Space frontend, Environment variables, Generated types, How the key proxy works, Notes on behaviour, Project layout, Run it, Scripts (+2 more)

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "ready"
Cohesion: 0.24
Nodes (6): _classifier_status(), _database_status(), ready(), 13a. Demo acceptance and targets, 4. Data model (replace the current `Item`), Milestone 5 verification

### Community 70 - "sqlalchemy"
Cohesion: 0.40
Nodes (6): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade()

### Community 71 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, openapi-typescript, oxlint, @types/node, @types/react, @types/react-dom, typescript, vite (+1 more)

### Community 72 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, api-types, build, check, dev, lint, preview, typecheck

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 76 - "gemini.py"
Cohesion: 0.11
Nodes (3): RateLimitError, enforce_rate_limit(), FixedWindowRateLimiter

### Community 77 - "vite.config.ts"
Cohesion: 0.33
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 612 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Settings` to `test_cost_layer.py`, `core/config.py`, `LLMUsage`, `GeminiExtractor`, `make_image`, `pipeline.py`, `test_foundation.py`, `Storage`, `Item`, `create_app`, `gemini.py`, `run.py`, `deps.py`, `app/main.py`, `test_classification.py`, `SklearnSvcClassifier`, `PipelineContext`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Item` (e.g. with `_owned_item()` and `ItemResponse`) actually correct?**
  _`Item` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Why does `GeminiExtractor` connect `GeminiExtractor` to `test_cost_layer.py`, `pipeline.py`, `ready`, `run.py`, `Item`, `create_app`, `gemini.py`, `test_blocked_and_truncated_responses_map_to_error_codes`, `app/main.py`, `Settings`, `test_api_security.py`, `test_evals.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_pipeline_context()`) actually correct?**
  _`Settings` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Should `make_image` be split into smaller, more focused modules?**
  _Cohesion score 0.06894664842681258 - nodes in this community are weakly interconnected._