# Graph Report - curated-space-main  (2026-11-26)

## Corpus Check
- 254 files · ~729,265 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 57 file(s) not represented in the graph (top: .csv 24, (none) 16, .pkl 6)

## Summary
- 1829 nodes · 4662 edges · 96 communities (66 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 360 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8832a059`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.ts
- routes/auth.py
- Curated Space — Backend + ML Build Brief (for the coding agent)
- react
- RequestSecurityMiddleware
- Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?
- pipeline.py
- README.md
- datasets.py
- curated-ml
- ItemDetailDialog.tsx
- routes/items.py
- link_clerk
- test_classification.py
- services/auth.py
- schemas/items.py
- dataset.py
- _DecisionModel
- Human-labeled holdout
- intelligence.py
- model_card.py
- ExtractedMetadata
- App.tsx
- cn
- runner.py
- LibraryPage.tsx
- NotFoundPage.tsx
- GeminiExtractor
- make_image
- test_evals.py
- routes/usage.py
- package.json
- ready
- report.py
- SettingsPage.tsx
- run.py
- test_cost_layer.py
- EvalConfig
- Backend + ML build progress
- LibraryControls.tsx
- budget.py
- security.py
- compilerOptions
- Item
- Milestone 6 verification
- components.json
- sqlalchemy
- test_intelligence.py
- rate_limit.py
- test_auth_api.py
- compilerOptions
- devDependencies
- Prediction
- LocalDiskStorage
- readme.md
- scripts
- user_for_token
- create_app
- CacheIdentity
- dependencies
- vercel.json
- select.tsx
- useAuth.tsx
- json
- deps.py
- vite.config.ts
- .oxlintrc.json
- tsconfig.json
- Curated Space backend
- GeminiEmbeddingProvider
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
- Settings

## God Nodes (most connected - your core abstractions)
1. `make_image()` - 67 edges
2. `Settings` - 62 edges
3. `Item` - 62 edges
4. `create_app()` - 51 edges
5. `GeminiExtractor` - 42 edges
6. `react` - 41 edges
7. `process_item()` - 40 edges
8. `ExtractedMetadata` - 39 edges
9. `sanitize_image()` - 36 edges
10. `ModelInput` - 33 edges

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

## Communities (96 total, 30 thin omitted)

### Community 0 - "api.ts"
Cohesion: 0.07
Nodes (32): Generated types, ServerStrip(), Verdict, VERDICT_DOT, VERDICT_TEXT, verdictOf(), itemKeys, mapItemsInCache() (+24 more)

### Community 1 - "routes/auth.py"
Cohesion: 0.16
Nodes (11): auth_status(), me(), User, _as_utc(), AuthStatusResponse, LoginRequest, RegisterRequest, SessionResponse (+3 more)

### Community 2 - "Curated Space — Backend + ML Build Brief (for the coding agent)"
Cohesion: 0.12
Nodes (16): 0. Product in one paragraph, 10. Observability, 11. Evaluation (this is what separates a project from a demo), 12. Tests, 13. Milestones (one PR each, in this order), 14. Rules for you, the agent, 1. Decisions already made (do not re-litigate), 2. Checks to run BEFORE writing features (report results in the first PR) (+8 more)

### Community 3 - "react"
Cohesion: 0.13
Nodes (10): InputGroup(), InputGroupAddon(), inputGroupAddonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), InputGroupTextarea(), Input() (+2 more)

### Community 5 - "Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does create_item() connect the upload route to the FastAPI routes and database item entity?, Source Nodes

### Community 6 - "pipeline.py"
Cohesion: 0.09
Nodes (21): AnalysisCache, Base, ItemEmbedding, LLMUsage, utcnow(), lookup(), store(), TokenUsage (+13 more)

### Community 8 - "datasets.py"
Cohesion: 0.22
Nodes (6): test_holdout_is_absent_so_no_quality_claim(), test_holdout_loader_reads_a_supplied_file(), test_labeled_csv_rejects_a_missing_column(), file_sha256(), load_holdout(), load_labeled_csv()

### Community 10 - "ItemDetailDialog.tsx"
Cohesion: 0.10
Nodes (35): EditForm(), Field(), ItemDetailBody(), ItemDetailDialog(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent() (+27 more)

### Community 11 - "routes/items.py"
Cohesion: 0.09
Nodes (13): get_job_runner(), delete_item(), get_item(), get_item_image(), list_items_route(), _owned_item(), patch_item(), reanalyze_item() (+5 more)

### Community 12 - "link_clerk"
Cohesion: 0.23
Nodes (9): clear_session_cookie(), link_clerk(), login(), logout(), logout_all(), register(), set_session_cookie(), create_session() (+1 more)

### Community 13 - "test_classification.py"
Cohesion: 0.10
Nodes (25): build_classifier(), ClassifierLoadError, SklearnSvcClassifier, test_abstains_on_ambiguous_text_and_returns_no_labels(), test_build_classifier_falls_back_in_development(), test_build_classifier_refuses_in_production(), test_build_text_accepts_comma_string_and_missing_fields(), test_build_text_is_deterministic_and_versioned() (+17 more)

### Community 14 - "services/auth.py"
Cohesion: 0.14
Nodes (13): main(), _read_password(), AppError, BadRequestError, ConflictError, _claim_legacy_items(), create_user(), find_user() (+5 more)

### Community 20 - "schemas/items.py"
Cohesion: 0.15
Nodes (6): AcceptedItem, _as_utc(), ImageInfo, ItemListResponse, ItemPatch, ItemResponse

### Community 22 - "dataset.py"
Cohesion: 0.09
Nodes (16): synthetic_set(), test_folder_without_a_label_file_is_refused(), test_label_template_leaves_the_label_column_blank(), test_label_template_refuses_to_overwrite_existing_labels(), test_loader_rejects_a_gold_label_outside_the_taxonomy(), test_loader_rejects_a_row_pointing_at_a_missing_file(), test_unlabeled_rows_still_load(), EvalItem (+8 more)

### Community 24 - "Human-labeled holdout"
Cohesion: 0.40
Nodes (4): Expected format, Human-labeled holdout, Size, What becomes possible once this exists

### Community 25 - "intelligence.py"
Cohesion: 0.07
Nodes (27): get_embedding_provider(), agent(), AgentResponse, ask(), AskRequest, AskResponse, _history_text(), reindex() (+19 more)

### Community 26 - "model_card.py"
Cohesion: 0.14
Nodes (6): test_normalize_tags_drops_empties(), test_raw_dataset_text_uses_the_serving_layout(), test_serving_and_training_agree_on_the_tags_token(), ClassMetrics, build_text_from_raw(), normalize_tags()

### Community 27 - "ExtractedMetadata"
Cohesion: 0.17
Nodes (11): build_labeled_schema(), _clean_text(), ExtractedMetadata, sanitize_metadata(), test_rejects_oversized_title(), test_rejects_short_tag(), test_rejects_too_many_tags(), test_sanitize_drops_tags_that_normalize_to_nothing() (+3 more)

### Community 28 - "App.tsx"
Cohesion: 0.09
Nodes (25): App(), AuthSync(), queryClient, RedirectIfSignedIn(), router, AccountMenu(), AppShell(), NAV (+17 more)

### Community 29 - "cn"
Cohesion: 0.09
Nodes (23): Field(), FieldLabel(), FieldSeparator(), fieldVariants, Separator(), Switch(), ToggleGroupContext, ToggleGroupItem() (+15 more)

### Community 30 - "runner.py"
Cohesion: 0.09
Nodes (23): test_accuracy_denominator_excludes_unlabeled_rows(), test_accuracy_is_none_when_nothing_is_labeled(), test_an_abstention_is_scored_as_a_miss_not_a_hit(), test_per_class_precision_and_recall(), test_percentiles_are_deterministic(), agreement(), ClassScore, CostMetrics (+15 more)

### Community 31 - "LibraryPage.tsx"
Cohesion: 0.10
Nodes (32): ItemCard, ItemCardInner(), MASONRY_CAPTION_PX, MasonryItem(), MasonryItemProps, CardFooter(), InfiniteScrollSentinel(), PendingCard() (+24 more)

### Community 32 - "NotFoundPage.tsx"
Cohesion: 0.49
Nodes (8): Empty(), EmptyContent(), EmptyDescription(), EmptyHeader(), EmptyMedia(), emptyMediaVariants, EmptyTitle(), NotFoundPage()

### Community 33 - "GeminiExtractor"
Cohesion: 0.09
Nodes (4): ExtractionUnavailableError, ExtractionResult, GeminiExtractor, test_labeled_extractor_reads_and_validates_the_provider_label()

### Community 34 - "make_image"
Cohesion: 0.07
Nodes (62): AnimatedImageError, ErrorBody, ErrorResponse, PayloadTooLargeError, TooManyPixelsError, UnprocessableImageError, UnsupportedMediaTypeError, _downscale() (+54 more)

### Community 35 - "test_evals.py"
Cohesion: 0.06
Nodes (34): estimate_cost_usd(), load_pricing_table(), validate_labels(), DictCache, _Parsed, _prepare(), __init__(), _run() (+26 more)

### Community 36 - "routes/usage.py"
Cohesion: 0.21
Nodes (4): get_usage(), UsageResponse, UsageWindow, UsageBucket

### Community 37 - "package.json"
Cohesion: 0.15
Nodes (12): name, private, type, version, cmdk, openapi-typescript, oxlint, tailwindcss (+4 more)

### Community 38 - "ready"
Cohesion: 0.17
Nodes (11): _auth_status(), _classifier_status(), _database_status(), health(), HealthResponse, ready(), ReadyResponse, _storage_status() (+3 more)

### Community 39 - "report.py"
Cohesion: 0.20
Nodes (8): summarize(), _agreement_section(), _cache_section(), _fmt(), per_class_table(), _provider_label_section(), render_table(), write_report()

### Community 40 - "SettingsPage.tsx"
Cohesion: 0.11
Nodes (26): Alert(), AlertDescription(), AlertTitle(), alertVariants, ScrollArea(), ScrollBar(), Skeleton(), ChatMessage (+18 more)

### Community 41 - "run.py"
Cohesion: 0.11
Nodes (12): _bootstrap(), build_parser(), _default_report_path(), has_key(), _InMemoryCache, main(), Prepared, _run_one() (+4 more)

### Community 42 - "test_cost_layer.py"
Cohesion: 0.13
Nodes (19): ExtractionError, ModelInput, _CountingExtractor, _good_response(), _rate_limited(), _response(), _server_error(), test_400_is_not_retried() (+11 more)

### Community 43 - "EvalConfig"
Cohesion: 0.18
Nodes (3): cell_name(), EvalConfig, build_fake_extractor()

### Community 44 - "Backend + ML build progress"
Cohesion: 0.15
Nodes (11): Backend + ML build progress, Known gaps in the cost layer, Milestone 10 documentation (2026-10-13), Milestone 11 implementation (2026-10-13), Milestone 2 verification, Milestone 3 verification, Milestone 4 verification, Milestone 7 verification (2026-10-13) (+3 more)

### Community 45 - "LibraryControls.tsx"
Cohesion: 0.19
Nodes (15): Filters, LabelFilter(), LibraryControls(), LibraryControlsProps, StatusFilter(), Command(), CommandEmpty(), CommandGroup() (+7 more)

### Community 46 - "budget.py"
Cohesion: 0.29
Nodes (6): BudgetDecision, _count_calls(), evaluate_budget(), _sum_cost(), test_budget_allows_a_fresh_daily_budget(), test_yesterday_spend_does_not_count_towards_today()

### Community 47 - "security.py"
Cohesion: 0.18
Nodes (11): _b64(), dummy_password_hash(), hash_password(), new_session_token(), password_hash_needs_upgrade(), _unb64(), verify_password(), authenticate() (+3 more)

### Community 48 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, jsx, lib, module (+16 more)

### Community 49 - "Item"
Cohesion: 0.11
Nodes (30): Item, BackgroundJobRunner, _budget_deferral(), _finish(), PipelineContext, process_item(), _seed_usage(), test_cache_hit_still_serves_under_a_budget_block() (+22 more)

### Community 50 - "Milestone 6 verification"
Cohesion: 0.33
Nodes (6): Gemini enum labels vs the local classifier, 60 screenshots, Live benchmark, 100 owner screenshots (`sample ss/`), `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`, Milestone 6 verification, The retry path is now confirmed live, What Milestone 6 could not settle

### Community 51 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "sqlalchemy"
Cohesion: 0.15
Nodes (7): get_settings(), make_database_url(), run_migrations_offline(), run_migrations_online(), upgrade(), upgrade(), upgrade()

### Community 53 - "test_intelligence.py"
Cohesion: 0.30
Nodes (7): _add_item(), FakeEmbeddingProvider, test_ask_returns_grounded_source(), test_ask_without_relevant_results_is_insufficient(), test_follow_up_history_reaches_answer_provider(), test_hybrid_search_and_owner_isolation(), test_langgraph_agent_uses_tool_and_returns_source()

### Community 55 - "test_auth_api.py"
Cohesion: 0.16
Nodes (16): Session, register(), test_api_key_still_authenticates_without_a_session(), test_auth_status_reports_registration_availability(), test_duplicate_email_is_rejected(), test_expired_session_is_refused_and_cleaned_up(), test_first_registration_is_allowed_and_normalizes_the_email(), test_login_sets_an_httponly_cookie_and_me_reads_it() (+8 more)

### Community 56 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, erasableSyntaxOnly, lib, module, moduleDetection, noEmit (+11 more)

### Community 57 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, openapi-typescript, oxlint, @types/node, @types/react, @types/react-dom, typescript, vite (+1 more)

### Community 58 - "Prediction"
Cohesion: 0.13
Nodes (3): Prediction, ClassifierStatus, UnavailableClassifier

### Community 60 - "readme.md"
Cohesion: 0.07
Nodes (26): Curated Space frontend, Environment variables, How sign-in works, Notes on behaviour, Project layout, Run it, Scripts, The production equivalent (+18 more)

### Community 61 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, api-types, build, check, dev, lint, preview, typecheck

### Community 62 - "user_for_token"
Cohesion: 0.40
Nodes (3): hash_session_token(), revoke_session(), user_for_token()

### Community 64 - "create_app"
Cohesion: 0.07
Nodes (20): create_database_engine(), create_session_factory(), get_session(), create_app(), lifespan(), purge_expired_items(), recover_interrupted_items(), retain_task() (+12 more)

### Community 65 - "CacheIdentity"
Cohesion: 0.11
Nodes (8): cache_key(), CacheIdentity, create_item(), list_items(), _read_cache(), _write_cache(), test_cache_key_covers_every_version(), FakeExtractor

### Community 66 - "dependencies"
Cohesion: 0.13
Nodes (15): dependencies, class-variance-authority, @clerk/react, cmdk, cn, lucide-react, next-themes, radix-ui (+7 more)

### Community 68 - "select.tsx"
Cohesion: 0.22
Nodes (3): SelectContent(), SelectScrollDownButton(), SelectScrollUpButton()

### Community 69 - "useAuth.tsx"
Cohesion: 0.12
Nodes (19): AuthProvider(), request(), UNAUTHORIZED_EVENT, Account, auth, AuthStatus, accountKey, AuthContext (+11 more)

### Community 70 - "json"
Cohesion: 0.11
Nodes (14): ModelPrice, PricingTable, _create_items_table(), _create_supporting_tables(), downgrade(), _legacy_key(), _tags(), upgrade() (+6 more)

### Community 71 - "deps.py"
Cohesion: 0.12
Nodes (12): clerk_subject_from_request(), get_classifier(), get_current_owner(), get_current_user(), get_extractor(), get_pipeline_context(), get_settings_dep(), get_storage() (+4 more)

### Community 72 - "vite.config.ts"
Cohesion: 0.40
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 74 - ".oxlintrc.json"
Cohesion: 0.29
Nodes (6): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 75 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 77 - "Curated Space backend"
Cohesion: 0.25
Nodes (6): Backend and ML build brief, graphify, Accounts and sessions, Curated Space backend, Local commands, Milestone 9 API security and retention

### Community 100 - "app/main.py"
Cohesion: 0.08
Nodes (4): configure_logging(), JsonFormatter, Storage, storage_key()

### Community 101 - "evaluate_retrieval.py"
Cohesion: 0.15
Nodes (17): evaluate(), _fts_query(), main(), _rank_keyword(), _read_items(), _read_labels(), evaluate_retrieval(), recall_at() (+9 more)

### Community 102 - "train.py"
Cohesion: 0.09
Nodes (8): test_retired_artifact_has_numeric_classes(), test_shipped_artifact_classes_are_label_strings(), assert_labels_match_taxonomy(), build_model(), evaluate(), evaluate_holdout(), main(), parse_args()

### Community 103 - "Settings"
Cohesion: 0.08
Nodes (16): Settings, auth_settings(), classifier(), client(), extractor(), FakeClassifier, FakeExtractor, make_client() (+8 more)

## Knowledge Gaps
- **9 isolated node(s):** `curated-space-backend`, `tailwindcss`, `@types/node`, `@types/react`, `@types/react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 714 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ready()` connect `ready` to `Curated Space — Backend + ML Build Brief (for the coding agent)`, `routes/items.py`, `Curated Space backend`?**
  _High betweenness centrality (0.319) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `Settings` (e.g. with `clerk_subject_from_request()` and `get_current_owner()`) actually correct?**
  _`Settings` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `curated-space-backend`, `tailwindcss`, `@types/node` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.06612685560053981 - nodes in this community are weakly interconnected._
- **Why does `Curated Space frontend` connect `readme.md` to `api.ts`?**
  _High betweenness centrality (0.310) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `Item` (e.g. with `reindex()` and `_owned_item()`) actually correct?**
  _`Item` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Should `Curated Space — Backend + ML Build Brief (for the coding agent)` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._