# Graph Report - curated-space  (2026-10-13)

## Corpus Check
- 178 files · ~136,752 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 48 file(s) not represented in the graph (top: .csv 20, (none) 16, .pkl 6)

## Summary
- 1668 nodes · 4225 edges · 96 communities (66 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 328 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3c486c19`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_cost_layer.py
- routes/auth.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- make_image
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- api.ts
- README.md
- train.py
- curated-ml
- ItemDetailDialog.tsx
- routes/items.py
- dataset.py
- model_card.py
- services/auth.py
- ExtractedMetadata
- _DecisionModel
- Human-labeled holdout
- services/usage.py
- test_classification.py
- PipelineContext
- build_text
- react
- runner.py
- useAuth.tsx
- App.tsx
- GeminiExtractor
- curated_evals/__init__.py
- test_evals.py
- routes/usage.py
- pipeline.py
- ready
- report.py
- UsagePage.tsx
- run.py
- Item
- create_app
- Backend + ML build progress
- LibraryControls.tsx
- security.py
- Eval harness
- compilerOptions
- CacheIdentity
- Milestone 6 verification
- components.json
- app/main.py
- Settings
- test_auth_api.py
- compilerOptions
- json
- UnavailableClassifier
- LocalDiskStorage
- readme.md
- UploadSurface.tsx
- package.json
- dropdown-menu.tsx
- FakeClassifier
- env.py
- dependencies
- Curated Space frontend
- select.tsx
- create_database_engine
- sqlalchemy
- NotFoundPage.tsx
- joblib
- .oxlintrc.json
- tsconfig.json
- errors.py
- Curated Space backend
- Classifier
- FakeExtractor
- api-types.ts
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
1. `make_image()` - 65 edges
2. `Settings` - 57 edges
3. `Item` - 52 edges
4. `create_app()` - 46 edges
5. `GeminiExtractor` - 42 edges
6. `process_item()` - 40 edges
7. `ExtractedMetadata` - 38 edges
8. `react` - 38 edges
9. `sanitize_image()` - 36 edges
10. `Button()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `Milestone 5 verification` --references--> `ready()`  [INFERRED]
  PROGRESS.md → backend/app/api/routes/health.py
- `API` --references--> `ready()`  [INFERRED]
  readme.md → backend/app/api/routes/health.py
- `Milestone 7 verification (2026-10-13)` --references--> `read_bounded()`  [INFERRED]
  PROGRESS.md → backend/app/services/image_firewall.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py

## Import Cycles
- None detected.

## Communities (96 total, 30 thin omitted)

### Community 0 - "test_cost_layer.py"
Cohesion: 0.15
Nodes (18): ExtractionError, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response(), _server_error(), test_400_is_not_retried() (+10 more)

### Community 1 - "routes/auth.py"
Cohesion: 0.12
Nodes (16): auth_status(), clear_session_cookie(), login(), logout(), logout_all(), me(), register(), set_session_cookie() (+8 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (16): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+8 more)

### Community 3 - "make_image"
Cohesion: 0.07
Nodes (63): AnimatedImageError, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale(), _encode(), _normalized() (+55 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "api.ts"
Cohesion: 0.07
Nodes (49): Generated types, ItemCard, ItemCardInner(), MASONRY_CAPTION_PX, MasonryItem(), MasonryItemProps, CardFooter(), InfiniteScrollSentinel() (+41 more)

### Community 8 - "train.py"
Cohesion: 0.12
Nodes (12): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv(), assert_labels_match_taxonomy(), build_model() (+4 more)

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.09
Nodes (37): EditForm(), Field(), ItemDetailBody(), ItemDetailDialog(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent() (+29 more)

### Community 11 - "routes/items.py"
Cohesion: 0.05
Nodes (26): get_classifier(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), delete_item(), get_item() (+18 more)

### Community 12 - "dataset.py"
Cohesion: 0.08
Nodes (17): synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load(), EvalItem (+9 more)

### Community 13 - "model_card.py"
Cohesion: 0.24
Nodes (9): test_development_warns_instead_of_refusing(), test_model_card_roundtrips(), test_production_refuses_a_sklearn_version_mismatch(), test_shipped_card_records_unvalidated_threshold(), card_path_for(), ClassMetrics, ModelCard, read_model_card() (+1 more)

### Community 14 - "services/auth.py"
Cohesion: 0.13
Nodes (19): Accounts and sessions, main(), _read_password(), hash_session_token(), new_session_token(), Base, Session, User (+11 more)

### Community 22 - "ExtractedMetadata"
Cohesion: 0.11
Nodes (13): ExtractionResult, MetadataExtractor, _clean_text(), ExtractedMetadata, sanitize_metadata(), validate_labels(), test_rejects_oversized_title(), test_rejects_short_tag() (+5 more)

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "services/usage.py"
Cohesion: 0.12
Nodes (11): estimate_cost_usd(), load_pricing_table(), ModelPrice, PricingTable, estimate_cost_usd(), _unknown_cost_models(), test_default_model_is_priced(), test_every_benchmarked_model_is_priced() (+3 more)

### Community 26 - "test_classification.py"
Cohesion: 0.14
Nodes (13): build_classifier(), Prediction, ClassifierLoadError, SklearnSvcClassifier, test_abstains_on_ambiguous_text_and_returns_no_labels(), test_build_classifier_falls_back_in_development(), test_build_classifier_refuses_in_production(), test_loads_and_predicts_from_the_configured_path() (+5 more)

### Community 27 - "PipelineContext"
Cohesion: 0.21
Nodes (3): BackgroundJobRunner, PipelineContext, Milestone 8 verification (2026-10-13)

### Community 28 - "build_text"
Cohesion: 0.17
Nodes (9): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), normalize_tags() (+1 more)

### Community 29 - "react"
Cohesion: 0.08
Nodes (25): Badge(), badgeVariants, buttonVariants, Field(), FieldLabel(), FieldSeparator(), fieldVariants, inputGroupAddonVariants (+17 more)

### Community 30 - "runner.py"
Cohesion: 0.13
Nodes (10): EvalConfig, agreement(), _error_code(), ItemRecord, PreparedInput, run_config(), _run_item(), RunCache (+2 more)

### Community 31 - "useAuth.tsx"
Cohesion: 0.12
Nodes (19): AuthProvider(), request(), UNAUTHORIZED_EVENT, Account, auth, AuthStatus, accountKey, AuthContext (+11 more)

### Community 32 - "App.tsx"
Cohesion: 0.13
Nodes (16): How sign-in works, The production equivalent, App(), queryClient, RedirectIfSignedIn(), RequireAccount(), router, Toaster() (+8 more)

### Community 33 - "GeminiExtractor"
Cohesion: 0.11
Nodes (4): ExtractionUnavailableError, GeminiExtractor, build_labeled_schema(), test_labeled_extractor_reads_and_validates_the_provider_label()

### Community 34 - "curated_evals/__init__.py"
Cohesion: 0.14
Nodes (13): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), ClassScore, CostMetrics, LabelMetrics, LabelObservation (+5 more)

### Community 35 - "test_evals.py"
Cohesion: 0.07
Nodes (28): DictCache, _Parsed, _prepare(), __init__(), _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call() (+20 more)

### Community 36 - "routes/usage.py"
Cohesion: 0.17
Nodes (5): get_usage(), UsageResponse, UsageWindow, usage_windows(), UsageBucket

### Community 37 - "pipeline.py"
Cohesion: 0.11
Nodes (17): LLMUsage, BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), TokenUsage, _apply_classification(), _budget_deferral() (+9 more)

### Community 38 - "ready"
Cohesion: 0.16
Nodes (9): _auth_status(), _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status() (+1 more)

### Community 39 - "report.py"
Cohesion: 0.26
Nodes (7): _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "UsagePage.tsx"
Cohesion: 0.17
Nodes (16): AppShell(), NAV, currentTheme(), Theme, ThemeToggle(), toggle(), Alert(), AlertDescription() (+8 more)

### Community 41 - "run.py"
Cohesion: 0.08
Nodes (13): _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main(), Prepared, _run_one() (+5 more)

### Community 42 - "Item"
Cohesion: 0.17
Nodes (26): Item, _finish(), process_item(), _seed_usage(), test_a_blocked_extraction_records_no_cost_row(), test_cache_hit_still_serves_under_a_budget_block(), test_cache_hits_do_not_consume_rate_budget(), test_cache_miss_when_versions_change() (+18 more)

### Community 43 - "create_app"
Cohesion: 0.14
Nodes (6): create_app(), lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task(), test_app_body_limit_and_cors_allowlist()

### Community 44 - "Backend + ML build progress"
Cohesion: 0.15
Nodes (11): Backend + ML build progress, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 11 implementation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone 5 verification (+3 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.14
Nodes (21): Filters, LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), ServerStrip(), Verdict, VERDICT_DOT (+13 more)

### Community 46 - "security.py"
Cohesion: 0.15
Nodes (7): get_current_owner(), get_current_user(), _b64(), hash_password(), _unb64(), verify_password(), test_hash_password_round_trips()

### Community 47 - "Eval harness"
Cohesion: 0.29
Nodes (6): Eval harness, Labeling a set, Layout, Running it, The synthetic set, What the report contains

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 49 - "CacheIdentity"
Cohesion: 0.14
Nodes (10): AnalysisCache, cache_key(), lookup(), store(), CacheIdentity, _read_cache(), _write_cache(), test_cache_key_covers_every_version() (+2 more)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "app/main.py"
Cohesion: 0.10
Nodes (3): RequestSecurityMiddleware, utcnow(), get_session()

### Community 53 - "Settings"
Cohesion: 0.11
Nodes (14): Settings, auth_settings(), classifier(), client(), extractor(), FakeExtractor, make_client(), factory() (+6 more)

### Community 55 - "test_auth_api.py"
Cohesion: 0.17
Nodes (16): register(), test_api_key_still_authenticates_without_a_session(), test_auth_status_reports_registration_availability(), test_duplicate_email_is_rejected(), test_expired_session_is_refused_and_cleaned_up(), test_first_registration_is_allowed_and_normalizes_the_email(), test_login_sets_an_httponly_cookie_and_me_reads_it(), test_logout_all_revokes_every_session() (+8 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 57 - "json"
Cohesion: 0.21
Nodes (6): test_legacy_taxonomy_has_eight_unique_labels(), test_realistic_eval_is_not_the_legacy_taxonomy(), test_taxonomy_rejects_duplicate_labels(), test_taxonomy_rejects_missing_version(), load_taxonomy(), Taxonomy

### Community 59 - "LocalDiskStorage"
Cohesion: 0.29
Nodes (3): LocalDiskStorage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 60 - "readme.md"
Cohesion: 0.15
Nodes (12): Accounts and authentication, API, Configuration, Cost and provider data handling, Current taxonomy and evaluation, How a screenshot moves through the system, Known limitations, Local data, deletion and retention (+4 more)

### Community 61 - "UploadSurface.tsx"
Cohesion: 0.26
Nodes (11): Switch(), JOB_TEXT, looksLikeImage(), readFiles(), UploadSurface(), onDrop(), onPaste(), UploadSurfaceProps (+3 more)

### Community 62 - "package.json"
Cohesion: 0.11
Nodes (18): name, private, type, version, cmdk, lucide-react, next-themes, openapi-typescript (+10 more)

### Community 63 - "dropdown-menu.tsx"
Cohesion: 0.19
Nodes (7): AccountMenu(), DropdownMenu(), DropdownMenuContent(), DropdownMenuItem(), DropdownMenuLabel(), DropdownMenuSeparator(), DropdownMenuTrigger()

### Community 64 - "FakeClassifier"
Cohesion: 0.17
Nodes (5): FakeClassifier, _migrate(), _migration_config(), test_migration_preserves_legacy_item_fields(), test_readiness_checks_schema_and_storage()

### Community 65 - "env.py"
Cohesion: 0.20
Nodes (6): get_settings(), configure_logging(), JsonFormatter, make_database_url(), run_migrations_offline(), run_migrations_online()

### Community 66 - "dependencies"
Cohesion: 0.06
Nodes (31): dependencies, class-variance-authority, cmdk, cn, lucide-react, next-themes, radix-ui, react (+23 more)

### Community 67 - "Curated Space frontend"
Cohesion: 0.29
Nodes (6): Curated Space frontend, Environment variables, Notes on behaviour, Project layout, Run it, Scripts

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "create_database_engine"
Cohesion: 0.29
Nodes (5): create_database_engine(), create_session_factory(), test_first_account_claims_pre_auth_items(), test_app_startup_requeues_stale_processing_item(), test_recovery_resets_only_stale_processing_and_returns_pending_ids()

### Community 70 - "sqlalchemy"
Cohesion: 0.16
Nodes (7): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade(), upgrade()

### Community 71 - "NotFoundPage.tsx"
Cohesion: 0.49
Nodes (8): Empty(), EmptyContent(), EmptyDescription(), EmptyHeader(), EmptyMedia(), emptyMediaVariants, EmptyTitle(), NotFoundPage()

### Community 72 - "joblib"
Cohesion: 0.25
Nodes (3): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main()

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 76 - "errors.py"
Cohesion: 0.13
Nodes (8): AppError, AuthenticationError, BadRequestError, ConflictError, ErrorBody, ErrorResponse, RateLimitError, FixedWindowRateLimiter

### Community 77 - "Curated Space backend"
Cohesion: 0.29
Nodes (5): Backend and ML build brief, graphify, Curated Space backend, Local commands, Milestone 9 API security and retention

### Community 78 - "Classifier"
Cohesion: 0.33
Nodes (3): Classifier, 6. Classifier (`services/classification/` + `ml/src/curated_ml`), Milestone status

### Community 80 - "api-types.ts"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 655 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ready()` connect `ready` to `Curated Space — Backend + ML Build Brief (for the coding agent)`, `Backend + ML build progress`, `Curated Space backend`, `app/main.py`, `readme.md`?**
  _High betweenness centrality (0.304) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_current_user()`) actually correct?**
  _`Settings` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_cost_layer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14516129032258066 - nodes in this community are weakly interconnected._
- **Why does `Curated Space frontend` connect `Curated Space frontend` to `App.tsx`, `api.ts`?**
  _High betweenness centrality (0.296) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `Item` (e.g. with `_owned_item()` and `ItemResponse`) actually correct?**
  _`Item` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Should `routes/auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12010796221322537 - nodes in this community are weakly interconnected._