# Graph Report - curated-space-main  (2026-11-26)

## Corpus Check
- 254 files · ~729,215 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 57 file(s) not represented in the graph (top: .csv 24, (none) 16, .pkl 6)

## Summary
- 1813 nodes · 4616 edges · 93 communities (62 shown, 31 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 350 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8832a059`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- load_pricing_table
- routes/auth.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- RequestSecurityMiddleware
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- pipeline.py
- README.md
- UploadSurface.tsx
- curated-ml
- ItemDetailDialog.tsx
- upload_item
- LabeledSet
- test_classification.py
- services/auth.py
- pathlib
- dataset.py
- ._validate
- Human-labeled holdout
- intelligence.py
- build_text
- ExtractedMetadata
- App.tsx
- react
- runner.py
- api.ts
- NotFoundPage.tsx
- GeminiExtractor
- make_image
- test_evals.py
- services/usage.py
- package.json
- ready
- report.py
- SettingsPage.tsx
- run.py
- test_cost_layer.py
- get_current_owner
- Backend + ML build progress
- LibraryControls.tsx
- LLMUsage
- joblib
- compilerOptions
- Item
- Milestone 6 verification
- components.json
- Settings
- UnavailableEmbeddingProvider
- errors.py
- test_auth_api.py
- compilerOptions
- devDependencies
- Prediction
- LocalDiskStorage
- readme.md
- scripts
- dropdown-menu.tsx
- app/main.py
- FakeExtractor
- dependencies
- vercel.json
- select.tsx
- useAuth.tsx
- json
- routes/items.py
- .oxlintrc.json
- tsconfig.json
- AGENTS.md
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
- evaluate_retrieval.py
- train.py
- conftest.py

## God Nodes (most connected - your core abstractions)
1. `make_image()` - 65 edges
2. `Settings` - 60 edges
3. `Item` - 60 edges
4. `create_app()` - 47 edges
5. `GeminiExtractor` - 42 edges
6. `react` - 42 edges
7. `process_item()` - 40 edges
8. `ExtractedMetadata` - 39 edges
9. `sanitize_image()` - 36 edges
10. `Button()` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Milestone 7 verification (2026-10-13)` --references--> `read_bounded()`  [INFERRED]
  PROGRESS.md → backend/app/services/image_firewall.py
- `Decisions and constraints` --references--> `build_text()`  [INFERRED]
  PROGRESS.md → ml/src/curated_ml/text.py
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py

## Import Cycles
- None detected.

## Communities (93 total, 31 thin omitted)

### Community 0 - "load_pricing_table"
Cohesion: 0.13
Nodes (10): estimate_cost_usd(), load_pricing_table(), ModelPrice, PricingTable, test_default_model_is_priced(), test_every_benchmarked_model_is_priced(), test_known_price_arithmetic(), test_price_table_records_provenance() (+2 more)

### Community 1 - "routes/auth.py"
Cohesion: 0.12
Nodes (16): auth_status(), clear_session_cookie(), login(), logout(), logout_all(), me(), register(), set_session_cookie() (+8 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (15): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+7 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "pipeline.py"
Cohesion: 0.07
Nodes (17): lookup(), store(), BackgroundJobRunner, _apply_classification(), _budget_deferral(), _complete(), create_item(), _embed_item() (+9 more)

### Community 8 - "UploadSurface.tsx"
Cohesion: 0.17
Nodes (16): Switch(), JOB_TEXT, looksLikeImage(), readFiles(), UploadSurface(), onDrop(), onPaste(), UploadSurfaceProps (+8 more)

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.10
Nodes (35): EditForm(), Field(), ItemDetailBody(), ItemDetailDialog(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent() (+27 more)

### Community 11 - "upload_item"
Cohesion: 0.06
Nodes (17): delete_item(), get_item(), get_item_image(), list_items_route(), _owned_item(), patch_item(), reanalyze_item(), upload_item() (+9 more)

### Community 12 - "LabeledSet"
Cohesion: 0.16
Nodes (3): EvalItem, LabeledSet, summarize()

### Community 13 - "test_classification.py"
Cohesion: 0.17
Nodes (16): SklearnSvcClassifier, test_abstains_on_ambiguous_text_and_returns_no_labels(), test_development_warns_instead_of_refusing(), test_loads_and_predicts_from_the_configured_path(), test_missing_artifact_raises(), test_missing_card_raises(), test_model_card_path_sits_next_to_the_artifact(), test_model_card_roundtrips() (+8 more)

### Community 14 - "services/auth.py"
Cohesion: 0.10
Nodes (23): main(), _read_password(), _b64(), dummy_password_hash(), hash_password(), hash_session_token(), new_session_token(), password_hash_needs_upgrade() (+15 more)

### Community 22 - "dataset.py"
Cohesion: 0.10
Nodes (17): test_legacy_taxonomy_has_eight_unique_labels(), synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load() (+9 more)

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "intelligence.py"
Cohesion: 0.07
Nodes (33): get_embedding_provider(), agent(), AgentResponse, ask(), AskRequest, AskResponse, _history_text(), reindex() (+25 more)

### Community 26 - "build_text"
Cohesion: 0.19
Nodes (8): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), normalize_tags()

### Community 27 - "ExtractedMetadata"
Cohesion: 0.09
Nodes (17): ExtractionResult, TokenUsage, build_labeled_schema(), _clean_text(), ExtractedMetadata, sanitize_metadata(), validate_labels(), test_labeled_schema_enum_is_built_from_the_taxonomy() (+9 more)

### Community 28 - "App.tsx"
Cohesion: 0.11
Nodes (26): How sign-in works, The production equivalent, App(), queryClient, RedirectIfSignedIn(), RequireAccount(), router, AppShell() (+18 more)

### Community 29 - "react"
Cohesion: 0.08
Nodes (21): buttonVariants, Field(), FieldLabel(), FieldSeparator(), fieldVariants, InputGroupAddon(), inputGroupAddonVariants, InputGroupButton() (+13 more)

### Community 30 - "runner.py"
Cohesion: 0.09
Nodes (23): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), test_percentiles_are_deterministic(), agreement(), ClassScore, CostMetrics (+15 more)

### Community 31 - "api.ts"
Cohesion: 0.06
Nodes (48): ItemCard, ItemCardInner(), MASONRY_CAPTION_PX, MasonryItem(), MasonryItemProps, CardFooter(), InfiniteScrollSentinel(), PendingCard() (+40 more)

### Community 32 - "NotFoundPage.tsx"
Cohesion: 0.49
Nodes (8): Empty(), EmptyContent(), EmptyDescription(), EmptyHeader(), EmptyMedia(), emptyMediaVariants, EmptyTitle(), NotFoundPage()

### Community 33 - "GeminiExtractor"
Cohesion: 0.07
Nodes (7): ExtractionError, ExtractionUnavailableError, GeminiExtractor, test_a_blocked_extraction_records_no_cost_row(), test_extractor_cache_identity_tracks_the_label_flag(), test_labeled_extractor_reads_and_validates_the_provider_label(), test_blocked_and_truncated_responses_map_to_error_codes()

### Community 34 - "make_image"
Cohesion: 0.07
Nodes (60): AnimatedImageError, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale(), _encode(), _normalized() (+52 more)

### Community 35 - "test_evals.py"
Cohesion: 0.09
Nodes (22): DictCache, _Parsed, _prepare(), __init__(), _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call() (+14 more)

### Community 36 - "services/usage.py"
Cohesion: 0.11
Nodes (11): get_usage(), UsageResponse, UsageWindow, estimate_cost_usd(), summarize_usage(), _unknown_cost_models(), usage_windows(), UsageBucket (+3 more)

### Community 37 - "package.json"
Cohesion: 0.08
Nodes (24): name, private, type, version, ServerStrip(), Verdict, VERDICT_DOT, VERDICT_TEXT (+16 more)

### Community 38 - "ready"
Cohesion: 0.17
Nodes (11): _auth_status(), _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status() (+3 more)

### Community 39 - "report.py"
Cohesion: 0.26
Nodes (7): _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "SettingsPage.tsx"
Cohesion: 0.12
Nodes (25): Alert(), AlertDescription(), AlertTitle(), alertVariants, ScrollArea(), ScrollBar(), Skeleton(), ChatMessage (+17 more)

### Community 41 - "run.py"
Cohesion: 0.08
Nodes (15): _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main(), Prepared, _run_one() (+7 more)

### Community 42 - "test_cost_layer.py"
Cohesion: 0.13
Nodes (21): AnalysisCache, cache_key(), CacheIdentity, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response() (+13 more)

### Community 43 - "get_current_owner"
Cohesion: 0.17
Nodes (6): Accounts and sessions, Curated Space backend, Local commands, Milestone 9 API security and retention, get_current_owner(), get_current_user()

### Community 44 - "Backend + ML build progress"
Cohesion: 0.15
Nodes (11): Backend + ML build progress, Decisions and constraints, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 11 implementation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification (+3 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.17
Nodes (17): Filters, LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), Command(), CommandEmpty(), CommandGroup() (+9 more)

### Community 46 - "LLMUsage"
Cohesion: 0.29
Nodes (7): LLMUsage, BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), test_budget_allows_a_fresh_daily_budget(), test_yesterday_spend_does_not_count_towards_today()

### Community 47 - "joblib"
Cohesion: 0.25
Nodes (3): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main()

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 49 - "Item"
Cohesion: 0.19
Nodes (24): Item, process_item(), _seed_usage(), test_cache_hit_still_serves_under_a_budget_block(), test_cache_hits_do_not_consume_rate_budget(), test_cache_miss_when_versions_change(), test_daily_cap_defers_the_item(), test_disabled_cache_always_calls_the_provider() (+16 more)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "Settings"
Cohesion: 0.12
Nodes (7): get_settings(), Settings, get_session(), make_database_url(), GeminiEmbeddingProvider, run_migrations_offline(), run_migrations_online()

### Community 54 - "errors.py"
Cohesion: 0.14
Nodes (9): AppError, AuthenticationError, BadRequestError, ConflictError, ErrorBody, ErrorResponse, RateLimitError, list_items() (+1 more)

### Community 55 - "test_auth_api.py"
Cohesion: 0.11
Nodes (24): verify_password(), create_database_engine(), create_session_factory(), register(), test_api_key_still_authenticates_without_a_session(), test_auth_status_reports_registration_availability(), test_dummy_password_hash_is_well_formed_but_never_matches(), test_duplicate_email_is_rejected() (+16 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 57 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, openapi-typescript, oxlint, @types/node, @types/react, @types/react-dom, typescript, vite (+1 more)

### Community 58 - "Prediction"
Cohesion: 0.10
Nodes (9): build_classifier(), Classifier, Prediction, ClassifierLoadError, ClassifierStatus, UnavailableClassifier, test_build_classifier_falls_back_in_development(), test_build_classifier_refuses_in_production() (+1 more)

### Community 59 - "LocalDiskStorage"
Cohesion: 0.29
Nodes (3): LocalDiskStorage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 60 - "readme.md"
Cohesion: 0.07
Nodes (25): Curated Space frontend, Environment variables, Generated types, Notes on behaviour, Project layout, Run it, Scripts, normalizeItem() (+17 more)

### Community 61 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, api-types, build, check, dev, lint, preview, typecheck

### Community 63 - "dropdown-menu.tsx"
Cohesion: 0.19
Nodes (7): AccountMenu(), DropdownMenu(), DropdownMenuContent(), DropdownMenuItem(), DropdownMenuLabel(), DropdownMenuSeparator(), DropdownMenuTrigger()

### Community 64 - "app/main.py"
Cohesion: 0.06
Nodes (10): configure_logging(), JsonFormatter, create_app(), lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task(), test_app_body_limit_and_cors_allowlist() (+2 more)

### Community 65 - "FakeExtractor"
Cohesion: 0.33
Nodes (3): FakeExtractor, test_skip_analysis_stores_owner_bound_deferred_item_without_provider_call(), test_upload_rate_limit_is_enforced_per_key_and_ip()

### Community 66 - "dependencies"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, cmdk, cn, lucide-react, next-themes, radix-ui, react (+6 more)

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "useAuth.tsx"
Cohesion: 0.12
Nodes (19): AuthProvider(), request(), UNAUTHORIZED_EVENT, Account, auth, AuthStatus, accountKey, AuthContext (+11 more)

### Community 70 - "json"
Cohesion: 0.29
Nodes (8): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade(), test_taxonomy_rejects_duplicate_labels(), test_taxonomy_rejects_missing_version()

### Community 71 - "routes/items.py"
Cohesion: 0.13
Nodes (10): get_classifier(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), utcnow(), cosine_similarity() (+2 more)

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 101 - "evaluate_retrieval.py"
Cohesion: 0.20
Nodes (14): evaluate(), _fts_query(), main(), _rank_keyword(), _read_items(), _read_labels(), evaluate_retrieval(), recall_at() (+6 more)

### Community 102 - "train.py"
Cohesion: 0.08
Nodes (12): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv(), assert_labels_match_taxonomy(), build_model() (+4 more)

### Community 103 - "conftest.py"
Cohesion: 0.05
Nodes (21): upgrade(), upgrade(), upgrade(), downgrade(), auth_settings(), classifier(), client(), extractor() (+13 more)

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 703 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ready()` connect `ready` to `upload_item`, `Curated Space — Backend + ML Build Brief (for the coding agent)`, `get_current_owner`?**
  _High betweenness centrality (0.309) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_current_user()`) actually correct?**
  _`Settings` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load_pricing_table` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._
- **Why does `Curated Space frontend` connect `readme.md` to `App.tsx`?**
  _High betweenness centrality (0.308) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Item` (e.g. with `reindex()` and `_owned_item()`) actually correct?**
  _`Item` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Should `routes/auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1214574898785425 - nodes in this community are weakly interconnected._