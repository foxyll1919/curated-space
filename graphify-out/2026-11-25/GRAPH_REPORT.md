# Graph Report - curated-space-main  (2026-11-25)

## Corpus Check
- 203 files · ~254,472 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 48 file(s) not represented in the graph (top: .csv 20, (none) 16, .pkl 6)

## Summary
- 1784 nodes · 4540 edges · 113 communities (80 shown, 33 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 350 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ModelInput
- routes/auth.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- make_image
- RequestSecurityMiddleware
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- pipeline.py
- README.md
- datasets.py
- curated-ml
- ItemDetailDialog.tsx
- upload_item
- dataset.py
- test_classification.py
- services/auth.py
- load_set
- _DecisionModel
- Human-labeled holdout
- intelligence.py
- build_text
- deps.py
- input-group.tsx
- react
- runner.py
- api.ts
- App.tsx
- GeminiExtractor
- pytest
- test_evals.py
- summarize_usage
- load_pricing_table
- ready
- curated_evals/__init__.py
- SettingsPage.tsx
- run.py
- test_cost_layer.py
- rate_limit.py
- Backend + ML build progress
- LibraryControls.tsx
- test_foundation.py
- security.py
- compilerOptions
- PipelineContext
- Milestone 6 verification
- components.json
- core/config.py
- conftest.py
- train.py
- test_auth_api.py
- compilerOptions
- LLMUsage
- SklearnSvcClassifier
- LocalDiskStorage
- readme.md
- json
- scripts
- dropdown-menu.tsx
- create_app
- CacheIdentity
- package.json
- vercel.json
- select.tsx
- useAuth.tsx
- sqlalchemy
- get_current_owner
- list_items_route
- metrics.py
- .oxlintrc.json
- tsconfig.json
- dependencies
- AGENTS.md
- errors.py
- Settings
- Curated Space frontend
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
- Eval harness
- test_intelligence.py
- FakeClassifier
- EvalConfig
- app/main.py
- retrieval_evaluation.py
- joblib
- test_api_security.py
- login
- field.tsx
- routes/items.py
- bootstrap_user.py
- synthetic.py
- ItemPatch
- DictCache
- get_session

## God Nodes (most connected - your core abstractions)
1. `make_image()` - 65 edges
2. `Settings` - 60 edges
3. `Item` - 60 edges
4. `create_app()` - 47 edges
5. `GeminiExtractor` - 42 edges
6. `react` - 41 edges
7. `process_item()` - 40 edges
8. `ExtractedMetadata` - 39 edges
9. `sanitize_image()` - 36 edges
10. `Button()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Milestone status` --references--> `Classifier`  [INFERRED]
  PROGRESS.md → backend/app/services/classification/base.py
- `Milestone 7 verification (2026-10-13)` --references--> `read_bounded()`  [INFERRED]
  PROGRESS.md → backend/app/services/image_firewall.py
- `Decisions and constraints` --references--> `build_text()`  [INFERRED]
  PROGRESS.md → ml/src/curated_ml/text.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py

## Import Cycles
- None detected.

## Communities (113 total, 33 thin omitted)

### Community 0 - "ModelInput"
Cohesion: 0.13
Nodes (18): ExtractionError, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response(), _server_error(), test_400_is_not_retried() (+10 more)

### Community 1 - "routes/auth.py"
Cohesion: 0.16
Nodes (11): auth_status(), me(), User, _as_utc(), AuthStatusResponse, LoginRequest, RegisterRequest, SessionResponse (+3 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (15): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+7 more)

### Community 3 - "make_image"
Cohesion: 0.16
Nodes (27): make_image(), test_usage_endpoint_counts_a_cache_hit(), test_usage_endpoint_counts_a_real_upload(), test_analysis_disabled_defers_the_item(), test_delete_item_removes_blob_and_only_unreferenced_cache(), test_item_image_hides_missing_and_owner_bound_items(), test_item_image_returns_sanitized_bytes_and_security_headers(), test_item_is_fetched_by_id() (+19 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "pipeline.py"
Cohesion: 0.14
Nodes (9): utcnow(), TokenUsage, _apply_classification(), _complete(), estimate_cost_usd(), record_cache_hit(), record_usage(), test_estimate_cost_uses_the_price_table() (+1 more)

### Community 8 - "datasets.py"
Cohesion: 0.22
Nodes (6): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv()

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.11
Nodes (33): EditForm(), Field(), ItemDetailBody(), ItemDetailDialog(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent() (+25 more)

### Community 11 - "upload_item"
Cohesion: 0.15
Nodes (8): delete_item(), get_item(), get_item_image(), _owned_item(), patch_item(), reanalyze_item(), upload_item(), NotFoundError

### Community 12 - "dataset.py"
Cohesion: 0.14
Nodes (5): EvalItem, LabeledSet, _load_from_csv(), summarize(), Taxonomy

### Community 13 - "test_classification.py"
Cohesion: 0.19
Nodes (12): test_development_warns_instead_of_refusing(), test_missing_card_raises(), test_model_card_path_sits_next_to_the_artifact(), test_model_card_roundtrips(), test_production_refuses_a_sklearn_version_mismatch(), test_refuses_numeric_classes_rather_than_guessing(), test_shipped_card_records_unvalidated_threshold(), card_path_for() (+4 more)

### Community 14 - "services/auth.py"
Cohesion: 0.16
Nodes (9): hash_session_token(), new_session_token(), Base, Session, _claim_legacy_items(), create_session(), purge_expired_sessions(), revoke_session() (+1 more)

### Community 22 - "load_set"
Cohesion: 0.16
Nodes (10): test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load(), EvalSetError, load_set() (+2 more)

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "intelligence.py"
Cohesion: 0.06
Nodes (30): get_embedding_provider(), agent(), AgentResponse, ask(), AskRequest, AskResponse, _history_text(), reindex() (+22 more)

### Community 26 - "build_text"
Cohesion: 0.19
Nodes (8): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), normalize_tags()

### Community 27 - "deps.py"
Cohesion: 0.17
Nodes (8): get_classifier(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), MetadataExtractor, Storage

### Community 28 - "input-group.tsx"
Cohesion: 0.11
Nodes (23): How sign-in works, The production equivalent, RedirectIfSignedIn(), RequireAccount(), AppShell(), NAV, currentTheme(), Theme (+15 more)

### Community 29 - "react"
Cohesion: 0.07
Nodes (29): Badge(), badgeVariants, buttonVariants, ScrollArea(), ScrollBar(), Switch(), ToggleGroupContext, ToggleGroupItem() (+21 more)

### Community 30 - "runner.py"
Cohesion: 0.14
Nodes (10): agreement(), summarize_to_dict(), _error_code(), ItemRecord, PreparedInput, run_config(), _run_item(), RunCache (+2 more)

### Community 31 - "api.ts"
Cohesion: 0.06
Nodes (50): Generated types, ItemCard, ItemCardInner(), MASONRY_CAPTION_PX, MasonryItem(), MasonryItemProps, CardFooter(), InfiniteScrollSentinel() (+42 more)

### Community 32 - "App.tsx"
Cohesion: 0.15
Nodes (19): App(), queryClient, router, Empty(), EmptyContent(), EmptyDescription(), EmptyHeader(), EmptyMedia() (+11 more)

### Community 33 - "GeminiExtractor"
Cohesion: 0.05
Nodes (19): GeminiExtractor, build_labeled_schema(), _clean_text(), ExtractedMetadata, sanitize_metadata(), validate_labels(), _Parsed, test_extractor_cache_identity_tracks_the_label_flag() (+11 more)

### Community 34 - "pytest"
Cohesion: 0.20
Nodes (22): UnprocessableImageError, prepare_model_input(), sanitize_image(), _settings(), test_accepts_png_jpeg_and_webp(), test_model_input_is_downscaled_and_deterministic(), test_normalizes_palette_and_alpha_to_opaque(), test_pixel_hash_is_stable_across_reencodes() (+14 more)

### Community 35 - "test_evals.py"
Cohesion: 0.12
Nodes (19): _prepare(), __init__(), _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call(), test_cache_identity_includes_everything_that_changes_the_answer(), test_labeled_and_unlabeled_schemas_have_different_cache_versions() (+11 more)

### Community 36 - "summarize_usage"
Cohesion: 0.14
Nodes (8): get_usage(), UsageResponse, UsageWindow, summarize_usage(), _unknown_cost_models(), usage_windows(), UsageBucket, test_summarize_usage_separates_failures()

### Community 37 - "load_pricing_table"
Cohesion: 0.13
Nodes (10): estimate_cost_usd(), load_pricing_table(), ModelPrice, PricingTable, test_default_model_is_priced(), test_every_benchmarked_model_is_priced(), test_known_price_arithmetic(), test_price_table_records_provenance() (+2 more)

### Community 38 - "ready"
Cohesion: 0.16
Nodes (12): _auth_status(), _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status() (+4 more)

### Community 39 - "curated_evals/__init__.py"
Cohesion: 0.20
Nodes (8): LabelMetrics, _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "SettingsPage.tsx"
Cohesion: 0.18
Nodes (16): Alert(), AlertDescription(), AlertTitle(), alertVariants, Skeleton(), Textarea(), api, AskPage() (+8 more)

### Community 41 - "run.py"
Cohesion: 0.11
Nodes (12): _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main(), Prepared, _run_one() (+4 more)

### Community 42 - "test_cost_layer.py"
Cohesion: 0.16
Nodes (27): Item, _finish(), process_item(), _seed_usage(), test_a_blocked_extraction_records_no_cost_row(), test_budget_allows_a_fresh_daily_budget(), test_cache_hit_still_serves_under_a_budget_block(), test_cache_hits_do_not_consume_rate_budget() (+19 more)

### Community 43 - "rate_limit.py"
Cohesion: 0.24
Nodes (3): RateLimitError, enforce_rate_limit(), FixedWindowRateLimiter

### Community 44 - "Backend + ML build progress"
Cohesion: 0.14
Nodes (12): Backend + ML build progress, Decisions and constraints, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 11 implementation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification (+4 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.12
Nodes (23): Filters, LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), ServerStrip(), Verdict, VERDICT_DOT (+15 more)

### Community 46 - "test_foundation.py"
Cohesion: 0.39
Nodes (4): _migrate(), _migration_config(), test_migration_preserves_legacy_item_fields(), test_readiness_checks_schema_and_storage()

### Community 47 - "security.py"
Cohesion: 0.23
Nodes (7): _b64(), hash_password(), password_hash_needs_upgrade(), _unb64(), verify_password(), authenticate(), test_hash_password_round_trips()

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 49 - "PipelineContext"
Cohesion: 0.21
Nodes (4): BackgroundJobRunner, JobRunner, PipelineContext, Milestone 8 verification (2026-10-13)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "core/config.py"
Cohesion: 0.35
Nodes (4): get_settings(), make_database_url(), run_migrations_offline(), run_migrations_online()

### Community 53 - "conftest.py"
Cohesion: 0.26
Nodes (6): make_settings(), migrated_settings(), migration_config(), _live_settings(), test_live_extraction_returns_validated_metadata(), test_live_upload_reaches_ready()

### Community 54 - "train.py"
Cohesion: 0.11
Nodes (6): assert_labels_match_taxonomy(), build_model(), evaluate(), evaluate_holdout(), main(), parse_args()

### Community 55 - "test_auth_api.py"
Cohesion: 0.13
Nodes (19): create_database_engine(), create_session_factory(), register(), test_api_key_still_authenticates_without_a_session(), test_auth_status_reports_registration_availability(), test_duplicate_email_is_rejected(), test_expired_session_is_refused_and_cleaned_up(), test_first_account_claims_pre_auth_items() (+11 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 57 - "LLMUsage"
Cohesion: 0.26
Nodes (7): LLMUsage, BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), _budget_deferral(), test_yesterday_spend_does_not_count_towards_today()

### Community 58 - "SklearnSvcClassifier"
Cohesion: 0.08
Nodes (10): Classifier, Prediction, ClassifierLoadError, ClassifierStatus, SklearnSvcClassifier, UnavailableClassifier, test_abstains_on_ambiguous_text_and_returns_no_labels(), test_loads_and_predicts_from_the_configured_path() (+2 more)

### Community 59 - "LocalDiskStorage"
Cohesion: 0.29
Nodes (3): LocalDiskStorage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 60 - "readme.md"
Cohesion: 0.17
Nodes (11): Accounts and authentication, Configuration, Cost and provider data handling, Current taxonomy and evaluation, How a screenshot moves through the system, Known limitations, Local data, deletion and retention, Local setup on Windows (+3 more)

### Community 61 - "json"
Cohesion: 0.27
Nodes (5): test_legacy_taxonomy_has_eight_unique_labels(), test_realistic_eval_is_not_the_legacy_taxonomy(), test_taxonomy_rejects_duplicate_labels(), test_taxonomy_rejects_missing_version(), load_taxonomy()

### Community 62 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, api-types, build, check, dev, lint, preview, typecheck

### Community 63 - "dropdown-menu.tsx"
Cohesion: 0.19
Nodes (7): AccountMenu(), DropdownMenu(), DropdownMenuContent(), DropdownMenuItem(), DropdownMenuLabel(), DropdownMenuSeparator(), DropdownMenuTrigger()

### Community 64 - "create_app"
Cohesion: 0.12
Nodes (8): create_app(), lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task(), test_app_startup_requeues_stale_processing_item(), test_recovery_resets_only_stale_processing_and_returns_pending_ids(), 6. Classifier (`services/classification/` + `ml/src/curated_ml`)

### Community 65 - "CacheIdentity"
Cohesion: 0.17
Nodes (10): AnalysisCache, cache_key(), lookup(), store(), CacheIdentity, _read_cache(), _write_cache(), test_cache_key_covers_every_version() (+2 more)

### Community 66 - "package.json"
Cohesion: 0.07
Nodes (27): devDependencies, openapi-typescript, oxlint, @types/node, @types/react, @types/react-dom, typescript, vite (+19 more)

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "useAuth.tsx"
Cohesion: 0.12
Nodes (18): request(), UNAUTHORIZED_EVENT, Account, auth, AuthStatus, accountKey, AuthContext, AuthContextValue (+10 more)

### Community 70 - "sqlalchemy"
Cohesion: 0.17
Nodes (8): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade(), upgrade(), upgrade()

### Community 71 - "get_current_owner"
Cohesion: 0.17
Nodes (7): Accounts and sessions, Curated Space backend, Local commands, Milestone 9 API security and retention, get_current_owner(), get_current_user(), AuthenticationError

### Community 72 - "list_items_route"
Cohesion: 0.16
Nodes (6): list_items_route(), AcceptedItem, _as_utc(), ImageInfo, ItemListResponse, ItemResponse

### Community 73 - "metrics.py"
Cohesion: 0.16
Nodes (12): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), test_percentiles_are_deterministic(), ClassScore, CostMetrics, LabelObservation (+4 more)

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 76 - "dependencies"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, cmdk, cn, lucide-react, next-themes, radix-ui, react (+6 more)

### Community 78 - "errors.py"
Cohesion: 0.10
Nodes (15): AnimatedImageError, AppError, ErrorBody, ErrorResponse, ExtractionUnavailableError, PayloadTooLargeError, TooManyPixelsError, UnsupportedMediaTypeError (+7 more)

### Community 79 - "Settings"
Cohesion: 0.27
Nodes (4): Settings, build_classifier(), test_build_classifier_falls_back_in_development(), test_build_classifier_refuses_in_production()

### Community 80 - "Curated Space frontend"
Cohesion: 0.29
Nodes (6): Curated Space frontend, Environment variables, Notes on behaviour, Project layout, Run it, Scripts

### Community 96 - "Eval harness"
Cohesion: 0.29
Nodes (6): Eval harness, Labeling a set, Layout, Running it, The synthetic set, What the report contains

### Community 97 - "test_intelligence.py"
Cohesion: 0.30
Nodes (7): _add_item(), FakeEmbeddingProvider, test_ask_returns_grounded_source(), test_ask_without_relevant_results_is_insufficient(), test_follow_up_history_reaches_answer_provider(), test_hybrid_search_and_owner_isolation(), test_langgraph_agent_uses_tool_and_returns_source()

### Community 98 - "FakeClassifier"
Cohesion: 0.16
Nodes (7): auth_settings(), classifier(), client(), extractor(), FakeClassifier, make_client(), factory()

### Community 99 - "EvalConfig"
Cohesion: 0.14
Nodes (4): cell_name(), EvalConfig, build_fake_extractor(), FakeExtractor

### Community 101 - "retrieval_evaluation.py"
Cohesion: 0.57
Nodes (6): evaluate_retrieval(), recall_at(), reciprocal_rank(), RetrievalMetrics, test_retrieval_metrics(), test_synthetic_retrieval_comparison()

### Community 102 - "joblib"
Cohesion: 0.25
Nodes (3): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main()

### Community 103 - "test_api_security.py"
Cohesion: 0.18
Nodes (6): ExtractionResult, FakeExtractor, test_app_body_limit_and_cors_allowlist(), test_other_owner_cannot_read_image_edit_delete_or_reanalyze(), test_skip_analysis_stores_owner_bound_deferred_item_without_provider_call(), test_upload_rate_limit_is_enforced_per_key_and_ip()

### Community 104 - "login"
Cohesion: 0.35
Nodes (6): clear_session_cookie(), login(), logout(), logout_all(), register(), set_session_cookie()

### Community 105 - "field.tsx"
Cohesion: 0.18
Nodes (5): Field(), FieldLabel(), FieldSeparator(), fieldVariants, Separator()

### Community 106 - "routes/items.py"
Cohesion: 0.24
Nodes (4): ConflictError, create_item(), list_items(), remove_item()

### Community 107 - "bootstrap_user.py"
Cohesion: 0.33
Nodes (7): main(), _read_password(), BadRequestError, create_user(), find_user(), _is_plausible_email(), normalize_email()

### Community 108 - "synthetic.py"
Cohesion: 0.27
Nodes (3): synthetic_set(), build_synthetic_set(), _render()

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 698 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ready()` connect `ready` to `Curated Space — Backend + ML Build Brief (for the coding agent)`, `get_current_owner`?**
  _High betweenness centrality (0.302) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_current_user()`) actually correct?**
  _`Settings` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ModelInput` be split into smaller, more focused modules?**
  _Cohesion score 0.13054187192118227 - nodes in this community are weakly interconnected._
- **Why does `Curated Space frontend` connect `Curated Space frontend` to `input-group.tsx`, `api.ts`?**
  _High betweenness centrality (0.296) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Item` (e.g. with `reindex()` and `_owned_item()`) actually correct?**
  _`Item` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._