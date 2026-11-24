# Graph Report - curated-space-main  (2026-11-25)

## Corpus Check
- 205 files · ~255,532 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 56 file(s) not represented in the graph (top: .csv 24, (none) 16, .pkl 6)

## Summary
- 1799 nodes · 4593 edges · 91 communities (59 shown, 32 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 350 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- UploadSurface.tsx
- routes/auth.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- UnavailableEmbeddingProvider
- RequestSecurityMiddleware
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- services/usage.py
- README.md
- datasets.py
- curated-ml
- ItemDetailDialog.tsx
- routes/items.py
- LabeledSet
- model_card.py
- services/auth.py
- dataset.py
- _DecisionModel
- Human-labeled holdout
- intelligence.py
- build_text
- ExtractedMetadata
- App.tsx
- react
- runner.py
- LibraryPage.tsx
- NotFoundPage.tsx
- GeminiExtractor
- pytest
- test_evals.py
- summarize_usage
- load_pricing_table
- ready
- report.py
- SettingsPage.tsx
- run.py
- test_cost_layer.py
- Backend + ML build progress
- LibraryControls.tsx
- security.py
- compilerOptions
- pipeline.py
- Milestone 6 verification
- components.json
- core/config.py
- test_auth_api.py
- compilerOptions
- SklearnSvcClassifier
- LocalDiskStorage
- readme.md
- test_classification.py
- dropdown-menu.tsx
- purge_expired_items
- CacheIdentity
- package.json
- vercel.json
- select.tsx
- api.ts
- sqlalchemy
- get_current_owner
- .oxlintrc.json
- tsconfig.json
- AGENTS.md
- Settings
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
- app/main.py
- evaluate_retrieval.py
- train.py
- create_app
- DictCache

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
- `13a. Demo acceptance and targets` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `4. Data model (replace the current `Item`)` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py
- `8. Pipeline, jobs, API` --references--> `ready()`  [INFERRED]
  build.md → backend/app/api/routes/health.py

## Import Cycles
- None detected.

## Communities (91 total, 32 thin omitted)

### Community 0 - "UploadSurface.tsx"
Cohesion: 0.16
Nodes (17): Switch(), JOB_TEXT, looksLikeImage(), readFiles(), UploadSurface(), onDrop(), onPaste(), UploadSurfaceProps (+9 more)

### Community 1 - "routes/auth.py"
Cohesion: 0.12
Nodes (16): auth_status(), clear_session_cookie(), login(), logout(), logout_all(), me(), register(), set_session_cookie() (+8 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (15): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+7 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "services/usage.py"
Cohesion: 0.17
Nodes (7): estimate_cost_usd(), TokenUsage, estimate_cost_usd(), record_cache_hit(), record_usage(), test_estimate_cost_uses_the_price_table(), test_unpriced_model_is_reported_rather_than_silently_free()

### Community 8 - "datasets.py"
Cohesion: 0.22
Nodes (6): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv()

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.09
Nodes (39): EditForm(), Field(), ItemDetailBody(), ItemDetailDialog(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent() (+31 more)

### Community 11 - "routes/items.py"
Cohesion: 0.06
Nodes (26): get_classifier(), get_extractor(), get_job_runner(), get_pipeline_context(), get_settings_dep(), get_storage(), delete_item(), get_item() (+18 more)

### Community 12 - "LabeledSet"
Cohesion: 0.16
Nodes (3): EvalItem, LabeledSet, summarize()

### Community 13 - "model_card.py"
Cohesion: 0.18
Nodes (11): test_abstains_on_ambiguous_text_and_returns_no_labels(), test_development_warns_instead_of_refusing(), test_model_card_path_sits_next_to_the_artifact(), test_model_card_roundtrips(), test_production_refuses_a_sklearn_version_mismatch(), test_shipped_card_records_unvalidated_threshold(), card_path_for(), ClassMetrics (+3 more)

### Community 14 - "services/auth.py"
Cohesion: 0.11
Nodes (19): main(), _read_password(), AppError, BadRequestError, ConflictError, Base, Session, User (+11 more)

### Community 22 - "dataset.py"
Cohesion: 0.08
Nodes (17): synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load(), EvalSetError (+9 more)

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "intelligence.py"
Cohesion: 0.07
Nodes (35): get_embedding_provider(), agent(), AgentResponse, ask(), AskRequest, AskResponse, _history_text(), reindex() (+27 more)

### Community 26 - "build_text"
Cohesion: 0.24
Nodes (7): test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), build_text(), build_text_from_raw(), Decisions and constraints

### Community 27 - "ExtractedMetadata"
Cohesion: 0.12
Nodes (14): ExtractionResult, MetadataExtractor, build_labeled_schema(), _clean_text(), ExtractedMetadata, sanitize_metadata(), test_labeled_schema_enum_is_built_from_the_taxonomy(), test_rejects_oversized_title() (+6 more)

### Community 28 - "App.tsx"
Cohesion: 0.11
Nodes (24): App(), queryClient, RedirectIfSignedIn(), RequireAccount(), router, AppShell(), currentTheme(), Theme (+16 more)

### Community 29 - "react"
Cohesion: 0.08
Nodes (15): Field(), FieldLabel(), FieldSeparator(), fieldVariants, ScrollArea(), ScrollBar(), Separator(), ToggleGroupContext (+7 more)

### Community 30 - "runner.py"
Cohesion: 0.09
Nodes (23): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), test_percentiles_are_deterministic(), agreement(), ClassScore, CostMetrics (+15 more)

### Community 31 - "LibraryPage.tsx"
Cohesion: 0.13
Nodes (26): ItemCard, ItemCardInner(), Filters, MASONRY_CAPTION_PX, MasonryItem(), MasonryItemProps, CardFooter(), InfiniteScrollSentinel() (+18 more)

### Community 32 - "NotFoundPage.tsx"
Cohesion: 0.49
Nodes (8): Empty(), EmptyContent(), EmptyDescription(), EmptyHeader(), EmptyMedia(), emptyMediaVariants, EmptyTitle(), NotFoundPage()

### Community 33 - "GeminiExtractor"
Cohesion: 0.09
Nodes (6): ExtractionUnavailableError, GeminiExtractor, _Parsed, test_extractor_cache_identity_tracks_the_label_flag(), test_label_reading_is_off_unless_asked_for(), test_labeled_extractor_reads_and_validates_the_provider_label()

### Community 34 - "pytest"
Cohesion: 0.08
Nodes (43): AnimatedImageError, ErrorBody, ErrorResponse, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale() (+35 more)

### Community 35 - "test_evals.py"
Cohesion: 0.08
Nodes (23): validate_labels(), _run(), StubClassifier, test_a_failing_item_is_a_data_point_not_a_crash(), test_a_second_pass_over_the_same_pixels_makes_no_provider_call(), test_cache_identity_includes_everything_that_changes_the_answer(), test_labeled_and_unlabeled_schemas_have_different_cache_versions(), test_provider_label_and_classifier_label_agreement_is_reported() (+15 more)

### Community 36 - "summarize_usage"
Cohesion: 0.15
Nodes (7): get_usage(), UsageResponse, UsageWindow, summarize_usage(), _unknown_cost_models(), usage_windows(), UsageBucket

### Community 37 - "load_pricing_table"
Cohesion: 0.25
Nodes (6): load_pricing_table(), ModelPrice, PricingTable, test_default_model_is_priced(), test_every_benchmarked_model_is_priced(), test_price_table_records_provenance()

### Community 38 - "ready"
Cohesion: 0.17
Nodes (11): _auth_status(), _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status() (+3 more)

### Community 39 - "report.py"
Cohesion: 0.26
Nodes (7): _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "SettingsPage.tsx"
Cohesion: 0.17
Nodes (17): Alert(), AlertDescription(), AlertTitle(), alertVariants, Skeleton(), Textarea(), AskResponse, UsageWindow (+9 more)

### Community 41 - "run.py"
Cohesion: 0.10
Nodes (14): _prepare(), __init__(), _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main() (+6 more)

### Community 42 - "test_cost_layer.py"
Cohesion: 0.05
Nodes (81): ExtractionError, Item, LLMUsage, BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), ModelInput (+73 more)

### Community 44 - "Backend + ML build progress"
Cohesion: 0.15
Nodes (11): Backend + ML build progress, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 11 implementation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone 7 verification (2026-10-13) (+3 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.10
Nodes (29): LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), ServerStrip(), Verdict, VERDICT_DOT, VERDICT_TEXT (+21 more)

### Community 47 - "security.py"
Cohesion: 0.16
Nodes (12): _b64(), dummy_password_hash(), hash_password(), hash_session_token(), new_session_token(), password_hash_needs_upgrade(), _unb64(), verify_password() (+4 more)

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 49 - "pipeline.py"
Cohesion: 0.09
Nodes (9): Classifier, BackgroundJobRunner, _apply_classification(), _budget_deferral(), _complete(), PipelineContext, _read_cache(), Storage (+1 more)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "core/config.py"
Cohesion: 0.18
Nodes (5): get_settings(), get_session(), make_database_url(), run_migrations_offline(), run_migrations_online()

### Community 55 - "test_auth_api.py"
Cohesion: 0.12
Nodes (20): create_database_engine(), create_session_factory(), register(), test_api_key_still_authenticates_without_a_session(), test_auth_status_reports_registration_availability(), test_duplicate_email_is_rejected(), test_expired_session_is_refused_and_cleaned_up(), test_first_account_claims_pre_auth_items() (+12 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 58 - "SklearnSvcClassifier"
Cohesion: 0.09
Nodes (7): Prediction, ClassifierStatus, SklearnSvcClassifier, UnavailableClassifier, FakeClassifier, test_loads_and_predicts_from_the_configured_path(), test_score_is_a_margin_not_a_probability()

### Community 59 - "LocalDiskStorage"
Cohesion: 0.29
Nodes (3): LocalDiskStorage, storage_key(), test_retention_purges_old_rows_and_blobs_but_keeps_recent_items()

### Community 60 - "readme.md"
Cohesion: 0.07
Nodes (26): Curated Space frontend, Environment variables, Generated types, How sign-in works, Notes on behaviour, Project layout, Run it, Scripts (+18 more)

### Community 61 - "test_classification.py"
Cohesion: 0.16
Nodes (12): build_classifier(), ClassifierLoadError, test_build_classifier_falls_back_in_development(), test_build_classifier_refuses_in_production(), test_legacy_taxonomy_has_eight_unique_labels(), test_missing_artifact_raises(), test_missing_card_raises(), test_normalize_tags_drops_empties() (+4 more)

### Community 63 - "dropdown-menu.tsx"
Cohesion: 0.16
Nodes (9): AccountMenu(), NAV, DropdownMenu(), DropdownMenuContent(), DropdownMenuItem(), DropdownMenuLabel(), DropdownMenuSeparator(), DropdownMenuTrigger() (+1 more)

### Community 64 - "purge_expired_items"
Cohesion: 0.20
Nodes (5): lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task(), 6. Classifier (`services/classification/` + `ml/src/curated_ml`)

### Community 65 - "CacheIdentity"
Cohesion: 0.12
Nodes (8): AnalysisCache, cache_key(), lookup(), store(), CacheIdentity, _write_cache(), test_cache_key_covers_every_version(), FakeExtractor

### Community 66 - "package.json"
Cohesion: 0.04
Nodes (46): dependencies, class-variance-authority, cmdk, cn, lucide-react, next-themes, radix-ui, react (+38 more)

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "api.ts"
Cohesion: 0.06
Nodes (39): AuthProvider(), AcceptedItem, AskSource, FILTERABLE_STATUSES, Health, ImageInfo, isItemStatus(), ITEM_STATUSES (+31 more)

### Community 70 - "sqlalchemy"
Cohesion: 0.14
Nodes (8): _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade(), upgrade(), upgrade()

### Community 71 - "get_current_owner"
Cohesion: 0.17
Nodes (7): Accounts and sessions, Curated Space backend, Local commands, Milestone 9 API security and retention, get_current_owner(), get_current_user(), AuthenticationError

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 100 - "app/main.py"
Cohesion: 0.10
Nodes (4): RateLimitError, configure_logging(), JsonFormatter, FixedWindowRateLimiter

### Community 101 - "evaluate_retrieval.py"
Cohesion: 0.20
Nodes (14): evaluate(), _fts_query(), main(), _rank_keyword(), _read_items(), _read_labels(), evaluate_retrieval(), recall_at() (+6 more)

### Community 102 - "train.py"
Cohesion: 0.13
Nodes (9): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), main(), assert_labels_match_taxonomy(), build_model(), evaluate(), evaluate_holdout(), main() (+1 more)

### Community 103 - "create_app"
Cohesion: 0.09
Nodes (16): create_app(), auth_settings(), classifier(), client(), extractor(), FakeExtractor, make_client(), factory() (+8 more)

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 699 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ready()` connect `ready` to `Curated Space — Backend + ML Build Brief (for the coding agent)`, `routes/items.py`, `get_current_owner`?**
  _High betweenness centrality (0.292) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Settings` (e.g. with `get_current_owner()` and `get_current_user()`) actually correct?**
  _`Settings` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `routes/auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11666666666666667 - nodes in this community are weakly interconnected._
- **Why does `API` connect `ready` to `readme.md`?**
  _High betweenness centrality (0.288) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Item` (e.g. with `reindex()` and `_owned_item()`) actually correct?**
  _`Item` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._