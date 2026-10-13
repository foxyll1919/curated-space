# Backend + ML build progress

Last updated: 2026-10-13
Scope: backend and ML by default. The sign-in work below is the one documented
exception: it was requested explicitly and also touches `frontend/`.

## Milestone status

| # | Milestone | Status | Notes |
|---|---|---|---|
| 1 | Hygiene + checks | Done | Added secret/data/cache ignores, archived DistilBERT comparison scripts, removed the stale adapter, added `uv.lock`, pytest, Ruff, mypy and CI. Fresh locked sync, one pytest, Ruff and mypy passed. |
| 2 | Skeleton + config + DB | Done | Added settings, JSON logging, app factory/lifespan, typed SQLAlchemy models, Alembic and health/readiness routes. Migration preserved the six existing item rows. |
| 3 | Thin vertical slice | Done | Added the image firewall, local storage with opaque keys, the versioned Gemini extractor behind a swappable interface, `POST/GET /api/v1/items`, cost telemetry and fake-provider tests. See "Milestone 3 verification" below. |
| 4 | Classifier adapter | Done | Added installable `curated_ml` (shared `build_text`, taxonomy loader, model card, dataset/holdout loaders), a hardened `train.py`, the versioned `legacy-8` taxonomy file, and a backend `Classifier` adapter with a model card, version guard and abstention. See "Milestone 4 verification" below. |
| 5 | Cost layer | Done | Added the pixel-hash `analysis_cache`, a bounded retry + one-repair policy, `GET /api/v1/usage`, and the daily-cap / per-minute budget guard that stores blocked items as `deferred`. See "Milestone 5 verification" below. |
| 6 | Eval harness + benchmark | Done (harness, partial benchmark) | Added `ml/evals/` with a CLI, metrics, a config matrix, a fake provider, a generated CI fixture, a checked-in Gemini price table with provenance, and a flag-gated Gemini enum-label arm. Ran the model and `media_resolution` sweeps live against 100 owner-supplied screenshots. **Quality is still unmeasured: the set has no gold labels.** See "Milestone 6 verification" and "What Milestone 6 could not settle". |
| 7 | Full firewall + storage | Done | Added stable pixel-limit errors, the bounded upload-size precheck, sanitized image retrieval with ownership visibility checks and security headers, and adversarial firewall/API coverage. Offline backend suite and focused static checks passed. |
| 8 | Jobs + API features | Done | Added bounded in-process background jobs, startup recovery, the 202 upload/reanalyze flow, correction and delete APIs, FTS5 search/filtering, and idempotent processing claims. See "Milestone 8 verification" below. |
| 9 | API firewall + privacy | Done | Static-key auth and owner scoping, rate limits, CORS/security headers, `skip_analysis`, and configurable retention. See Milestone 9 implementation below. |
| 10 | Docs | Done | Rewrote README around the implemented screenshot pipeline, PowerShell operations, configuration, privacy, costs and limitations. See Milestone 10 documentation below. |
| 11 | Accounts, sessions and sign-in (owner request, outside `build.md`) | Done | Added `users`/`sessions`, PBKDF2 password hashing, session-cookie auth, the `/auth` routes, per-account ownership, a login rate limit, and a guarded sign-in page in the frontend. See Milestone 11 below. |

## Decisions and constraints

- The API key's AI Studio project is on the Free plan. Do not send sensitive or
  private screenshots to Gemini using this project. See the data-use note in
  `readme.md` and section 7a in `build.md`. **Owner decision 2026-10-11 (M6):**
  the 100 images in `sample ss/` were sent to that Free project with explicit
  owner approval, for the benchmark only. That was a decision about *those*
  images, not a reversal of the general rule.
- `POST /api/v1/items` stores a sanitized image and pending item, returns **202**,
  and schedules the idempotent `process_item(item_id)` through the background
  job runner. The job moves the item to ready, failed or deferred; provider
  failures do not become upload-response 500s.
- Classifier serving landed in Milestone 4 as the `legacy-8` **placeholder**, loaded
  from `ml/model/curated_space_classifier_v2.pkl` plus its `.card.json` sidecar.
  The retired `curated_space_classifier.pkl` is **still on disk and unserved**: its
  `classes_` are the numeric ids `0..7` with an unrecoverable mapping, and a test
  asserts this so the hazard stays documented. Delete it whenever you like;
  nothing imports it.
- The rebuilt artifact scores **macro-F1 1.0000** on the synthetic split. That is
  the point, not a triumph: the dataset is templated and a cue phrase decides the
  label. The card records `split: "synthetic"` and
  `threshold_source: "default-unvalidated"`. Do not quote this number as accuracy.
- `ml/dataset/realistic_eval.csv` uses a **different label set** (`Career`,
  `Other`, `Personal`, `Programming`, `Study`) and `title/description/tags` columns
  rather than `text`. It is not interchangeable with the training set or the
  holdout, and a test asserts that.
- Training and serving now both build features through `curated_ml.build_text`. An
  earlier pass trained on the raw CSV `text` column while serving produced a
  3-line format; that token mismatch is fixed and now has its own test.
- Existing SQLite data was migrated, not reset. The six existing item IDs and
  their generated upload filenames were retained; legacy category/tags are
  converted to JSON when present. User image bytes were not read by the migration.
- Gemini prices now come from `backend/app/core/gemini_pricing.json`, verified
  against <https://aistudio.google.com/docs/pricing> on 2026-10-11. The
  `gemini_*_price_usd_per_mtok` settings are gone. `gemini-3.5-flash` and
  `gemini-3.7-flash` exist as model ids but have **no section on the pricing
  page**, so they are deliberately absent from the table and cannot be priced.
  A model missing from the table reports `null` cost, never `$0.00`, and
  `GET /api/v1/usage` lists such models in `unknown_cost_models`.
- `sample ss/` is **gitignored**. It holds real personal screenshots, and
  `build.md` says to keep real eval data out of the repo.
- **Correction to an earlier entry:** the claim that this workspace has no `.git`
  directory was wrong. There is one, with a single `First Commit` and a long
  uncommitted working tree, so the Milestone 3 deletions are recoverable and the
  secret audit question is answerable here.

## Milestone 2 verification

- `pytest`: 2 passed. Tests use temporary SQLite databases and cover readiness,
  forward migration and downgrade preservation.
- `ruff check .`: passed.
- `mypy app main.py`: passed.
- `alembic check`: no schema drift detected.
- Local SQLite migration: applied at head; six item rows preserved and
  `PRAGMA integrity_check` returned `ok`.
- Pytest emits a Starlette deprecation warning about its current `httpx`
  TestClient integration; it does not fail the checks.

## Milestone 3 verification

- `pytest`: 48 passed (46 offline + 2 `@pytest.mark.live`). 15 firewall cases,
  schema/tag post-rules, blocked/truncated/empty mapping, pipeline idempotency,
  ownership filtering, cursor pagination and prompt-injection resistance.
- `ruff check .`: passed. `mypy app main.py`: passed (27 files).
- `alembic check`: no schema drift.
- **Live run 2026-10-11** against `gemini-3.5-flash-lite`, `media_resolution=MEDIUM`,
  `thinking_level=minimal`, using the committed non-sensitive fixture
  `backend/tests/fixtures/test_image.jpg`: 597 prompt tokens, 97 output tokens,
  0 thinking tokens, ~9.5 s, estimated $0.000295. Prompt/output tokens and cost
  are inside the section 13a starting targets; the single-sample latency is
  above the 8 s p95 target and is a hypothesis to re-measure in Milestone 6.
- Model ids re-verified live against `models.list()` on 2026-10-11:
  `gemini-3.5-flash`, `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` all
  support `generateContent`. `gemini-2.5-*` is still listed but is scheduled for
  shutdown on 2026-10-16 and is not used.
- Removed `backend/gemini_service.py`, `backend/test_gemini.py` and
  `backend/test_pipeline.py` (the last imported the already-deleted
  `ml_service`, so it was broken). `backend/test_image.jpg` moved to
  `backend/tests/fixtures/test_image.jpg` and is still used by the demo and the
  live test. `backend/main.py` now re-exports `app` for `uvicorn main:app`.

## Milestone 4 verification

- `pytest`: 82 passed (80 offline + 2 `@pytest.mark.live`).
- `ruff check . ../ml`: passed. `ruff format --check`: passed.
  `mypy app main.py`: passed (30 files).
- `uv lock --check` and `uv sync --locked`: clean. `curated_ml` is installed as an
  editable path dependency, so `ml/train.py` and the backend share one copy.
- `alembic check`: no schema drift. Milestone 4 is code and config only; the
  schema already had every column it needed.
- Rebuilt artifact: `macro-F1 1.0000` on the synthetic split, 8/8 labels,
  `classes_` are label strings, card records scikit-learn 1.9.1, the training
  data SHA-256 and `threshold_source: "default-unvalidated"`.
- Adapter verified against the real artifact: loads, predicts `Tutorials` for the
  React/JWT example with a 1.2227 margin, and **abstains** (margin 0.09 < 0.5)
  on out-of-distribution text.
- Version guard verified both ways: a mismatched `sklearn_version` refuses startup
  in production and only warns in development. A numeric-classes artifact is
  refused with an explicit message rather than an inferred mapping.

## Milestone 5 verification

- `pytest`: 109 passed (107 offline + 2 `@pytest.mark.live`). 29 new cases in
  `tests/test_cost_layer.py`.
- `ruff check .`: passed. `ruff format --check`: passed. `mypy app main.py`:
  passed (34 files). `alembic check`: no schema drift; M5 needed no migration
  because `analysis_cache` and `llm_usage` already existed from Milestone 2.
- **Cache.** Key is `sha256(normalized pixels) | model | prompt_version |
  schema_version`, built from `CacheIdentity` on the extractor before any call.
  Verified a second identical item reaches `ready` with **zero** provider calls
  and records a `cache_hit` row; changing any one of the three versions
  invalidates the entry; `ANALYSIS_CACHE_ENABLED=false` forces a call; a cache
  row that fails re-validation degrades to a miss rather than failing the item.
  Cached values are re-validated on read, so a corrupt or hand-edited row cannot
  reach an item.
- **Retries.** 429, 5xx and transport timeouts retry (default 2) with exponential
  backoff plus jitter; a 400 is **not** retried. The overall deadline
  (`gemini_total_timeout_ms`, default 30 s) is enforced before every sleep, so a
  backoff never starts without budget for it. Schema-validation failure gets
  exactly one repair retry, then `extraction_invalid`.
- **Budget.** `DAILY_COST_CAP_USD` (default 1.00) and `MAX_ANALYSES_PER_MINUTE`
  (default 30); `0` disables each check. A blocked item is stored as
  `status: "deferred"` with `error_code` `budget_exceeded` or `rate_limited`, is
  never dropped, and makes no provider call. Cache hits bypass the guard because
  they cost nothing. Yesterday's spend does not count against today.
- **Usage.** `GET /api/v1/usage` reports `today` and `last_7_days`: calls,
  provider calls, cache hits, failed calls, prompt/output/thinking tokens,
  estimated cost and cache hit rate. It is derived from `llm_usage` and exposes
  counts only.
- No live Gemini run this milestone. The retry and repair paths are covered
  against stubbed transports; a real 429/timeout is the one behaviour a fake
  cannot confirm, and M6 should observe it.

## Milestone 6 verification

- `pytest`: 145 passed (143 offline + 2 `@pytest.mark.live`). 36 new cases in
  `tests/test_evals.py`.
- `ruff check . ../ml` and `ruff format --check`: passed.
  `mypy app main.py`: passed (35 files). `alembic check`: no schema drift; M6
  needed no migration. `uv lock --check` and `uv sync --locked`: clean.
- CI gained an `eval-harness` job that builds the generated set and runs the
  matrix with `--fake`, then asserts the report is marked `synthetic`, that the
  cache hit, and that nothing failed. The workflow path filters now include
  `ml/**`, since `curated_evals` is installed into the backend environment.
- **Pricing verified 2026-10-11** against <https://aistudio.google.com/docs/pricing>,
  Standard tier, Paid tier, USD per 1M tokens:
  `gemini-3.5-flash-lite` $0.30 in / $2.50 out, `gemini-3.1-flash-lite` $0.25 /
  $1.50, `gemini-3.8-flash` and `gemini-3.6-flash` $0.75 / $3.75 until
  2026-12-31 then $1.50 / $7.50. Google's output figure is explicitly
  "including thinking tokens", so the previous code was charging thinking tokens
  a second time at a third invented rate.
- **Model ids re-verified live** against `models.list()` on 2026-10-12. All three
  benchmarked models exist. `gemini-3.5-flash` and `gemini-3.7-flash` also exist
  but have **no pricing section**, which is why they are not in the table and not
  in the matrix.

### Live benchmark, 100 owner screenshots (`sample ss/`)

Sent to the Free-tier project with explicit owner approval. Reports are in
`ml/evals/reports/` (gitignored; regenerate with the commands below).

| config | n | p50 | p95 | tokens/item | $/item | fails |
|---|---|---|---|---|---|---|
| `gemini-3.5-flash-lite` MEDIUM minimal | 100 | 3,816 ms | 7,256 ms | 688 | $0.00041 | 0 |
| `gemini-3.1-flash-lite` MEDIUM minimal | 100 | 5,416 ms | 8,824 ms | 706 | $0.00031 | 1 |
| `gemini-3.8-flash` MEDIUM minimal | 100 | n/a | n/a | n/a | n/a | **100** |

`gemini-3.8-flash` returned `extraction_provider_error` on every item. The
underlying HTTP error is `429 RESOURCE_EXHAUSTED`, "Quota exceeded for
`generate_content_free_tier_requests`, limit: 20, model: gemini-3.8-flash". The
Free tier allows 20 requests/day for that model and the quota was already spent.
This is a quota fact about the account, not a defect in the code, and it is
recorded as `null` rather than as a slow or bad model.

### `media_resolution` sweep, 40 screenshots, `gemini-3.5-flash-lite`

| resolution | p50 | p95 | tokens/item | $/item | fails |
|---|---|---|---|---|---|
| LOW | 2,639 ms | 5,812 ms | 423 | $0.00033 | 6 (2 `extraction_empty`, 4 provider) |
| MEDIUM | 2,950 ms | 5,632 ms | 686 | $0.00040 | 1 (provider) |
| HIGH | 2,665 ms | 5,117 ms | 1,240 | $0.00057 | 3 (provider) |

HIGH roughly doubles prompt tokens and costs ~41% more than MEDIUM while showing
no latency benefit, which is consistent with the brief's warning that
`media_resolution` mainly moves image tokens, not speed. LOW is cheapest and
fastest but produced more failures, including the only `extraction_empty` in the
sweep. **Recommendation: stay on MEDIUM.** The failure counts are small enough
that the LOW result is suggestive, not decisive.

### Gemini enum labels vs the local classifier, 60 screenshots

With `GEMINI_RETURN_LABELS=true`, the same call returns a taxonomy label alongside
the metadata. On 60 items:

- **Agreement between Gemini and the local classifier: 0.25 over n=20.**
- The local classifier **abstained on 34 of 60 (57%)** and used only 4 of the 8
  taxonomy labels (`Tutorials`, `Research`, `Design`, `References`).
- Gemini used 7 of 8 labels and spread across all of them
  (`References` 14, `Inspiration` 13, `Resources` 12, `Research` 7,
  `Tutorials` 4, `Technology` 3, `Design` 1).

The `n=20` is the 60 minus the 34 abstentions: an abstention is counted as
"no opinion", not as agreement. **This is the strongest evidence so far that the
`legacy-8` classifier does not earn its place on real screenshots** - it declines
to answer the majority of them and covers half the taxonomy. Agreement is not
accuracy: it shows the two systems mostly disagree, not which one is right.

### The retry path is now confirmed live

M5 recorded that a real 429 or timeout was the one behaviour a fake could not
confirm. The `gemini-3.8-flash` run produced exactly that: real HTTP 429s,
retried twice with jittered backoff inside the overall deadline, then
`extraction_provider_error` on the item rather than a 500. That path is verified
against the provider, not just a stubbed transport.

### What Milestone 6 could not settle

**Quality is unmeasured.** The 100 screenshots have no gold labels, so every
accuracy and macro-F1 figure above is `n/a` by design, and the harness refuses to
print a number over an empty denominator. Nothing in this milestone says whether
the extracted titles, descriptions and tags are any good. To settle it, fill in
the `category` column in `sample ss/labels.csv` (already written, filenames
filled, gold columns blank) and re-run; accuracy, macro-F1 and per-class
precision/recall appear immediately.

Consequences, stated plainly:

- **The model default is unchanged.** `gemini-3.5-flash-lite` is the cheapest
  *reliable* option measured, not the best one; only a quality sweep can pick the
  best one. 3.1-flash-lite is ~23% cheaper per item but ~40% slower at p50.
- **The 8-second p95 target is met on the full set** (7,256 ms) and missed by
  3.1-flash-lite (8,824 ms). Single-run latencies on the owner's connection are
  not a stable distribution; treat this as provisional.
- **The "< $0.002 per item" target is met with ~5x headroom** by every config that
  completed.
- **Whether the local classifier stays** is now answerable on cost and coverage
  grounds alone: it abstains on the majority of real screenshots. Its quality is
  still unknown, but it is not currently doing useful work on this set.

## Known gaps in the cost layer

- A request that fails *after* the provider generated tokens (blocked late, a
  truncated body, a retry that succeeded only on attempt 3) leaves no
  `llm_usage` row, because the error path has no `usage_metadata`. Our cost
  estimate is therefore a floor, not the bill. M6 did not reconcile against
  provider-side usage; there is no reconciliation code, only the caveat.
- The retry counter is not exposed on `llm_usage`, so a run that needed three
  attempts is indistinguishable from one that needed one. M6 made this concrete:
  the `gemini-3.8-flash` run failed 100/100 after exhausting its retries, and
  there is no column that records "this took 3 attempts". That is worth a column
  now.
- The guard reads `llm_usage` on every analysis. That is two cheap indexed
  counts and fine for SQLite at this scale; a multi-process deployment would
  want a shared counter, which lands with the durable queue in M8.

## Open questions for the owner

- **Labels are the blocker.** Nothing about quality can be decided until
  `sample ss/labels.csv` has a `category` column. That is the single highest-value
  thing you can do next; it needs no code and about twenty minutes.
- Free-tier quotas are tight and per-model. `gemini-3.8-flash` allows 20
  requests/day on this project. Do you want to upgrade to the Paid tier before
  benchmarking the newer Flash models properly, or stay on the Free plan and
  benchmark only what its quota allows?
- Latency on the full set came in under the 8 s p95 target at MEDIUM (7,256 ms),
  so the earlier single-sample 9.5 s reading was noise. Should the default stay
  `MEDIUM`, given HIGH buys nothing and LOW failed more?
- Storage format is PNG for determinism, but that makes the model-input payload
  large (~1.0 MB for a 1080x1920 screenshot). Lossless WebP would cut it
  substantially. Still worth switching in M7 once quality is measurable?
- `ml/model/curated_space_classifier.pkl` (the retired numeric-classes artifact)
  is dead weight on disk. There *is* a `.git` here with one commit, so deleting it
  is now recoverable. Want me to remove it?
- `ml/holdout/holdout.csv` is still yours to label. Until it exists the card
  records an unvalidated abstention threshold and no accuracy claim is possible.
- The `legacy-8` classifier abstains on ~57% of your real screenshots. Do you
  want it kept as a cost baseline that mostly abstains, or should M7/M8 stop
  serving it and revisit with a real taxonomy?

## Milestone 7 verification (2026-10-13)

- Added `GET /api/v1/items/{id}/image`. It looks up the item before reading its
  blob, returns 404 for missing or owner-bound items under the current
  unauthenticated API boundary, uses the stored MIME type, and emits a
  generated UUID filename plus `X-Content-Type-Options: nosniff`. M9 will add
  authenticated ownership identity.
- The upload route now rejects a known oversized multipart part before copying
  it into the application buffer; `read_bounded` remains the hard limit.
- Pixel-count, edge-limit, and Pillow decompression-bomb rejections now use the
  stable `too_many_pixels` code instead of collapsing into `corrupt_image`.
- Firewall tests cover decoded formats, malformed and truncated files, animated
  formats, upload/pixel/edge limits, stable `too_many_pixels` errors, metadata
  removal including GPS EXIF, trailing polyglot payload removal, downscaling,
  and normalized-pixel hash stability.
- API tests verify retrieval returns the sanitized PNG with the generated inline
  filename and `nosniff` header, and returns 404 for missing and owner-bound
  items before exposing storage bytes.
- `uv run pytest -m "not live"`: **150 passed, 2 live tests deselected**.
  One existing Starlette `TestClient` deprecation warning remains.
- Ruff lint and format checks passed on the five changed Python files. `mypy
  app main.py` passed (35 source files).

## Milestone 8 verification (2026-10-13)

- `POST /api/v1/items` now persists the sanitized image and pending row, returns
  `202 {id, status: "pending"}`, and schedules the existing `process_item` via
  FastAPI `BackgroundTasks`. `BackgroundJobRunner` uses a bounded semaphore;
  its interface is isolated in `services/jobs.py` for a later durable queue.
- Startup resets `processing` items older than `STUCK_JOB_TIMEOUT_MINUTES` to
  `pending` and requeues all pending items. It skips the sweep before the first
  migration so health/readiness remain available. Processing claims are atomic,
  so duplicate jobs do not analyze the same row concurrently.
- Added Alembic revision `0002_milestone_8_fts` with an FTS5 index and insert,
  update, and delete triggers. `GET /items` now filters by status, any label
  value, and AND-matched title/description/tags text.
- Added `PATCH /items/{id}` for sanitized title/tags/labels corrections and the
  `user_corrected` marker; `POST /items/{id}/reanalyze` queues an item through
  the same cache- and budget-aware pipeline; `DELETE /items/{id}` removes its
  image and row, preserves shared cache entries, removes unreferenced cache
  entries, and leaves usage rows without item links.
- `pytest -m "not live"`: **157 passed, 2 live tests deselected**. Ruff lint and
  formatting passed for `app`, `main.py`, `migrations`, and `tests`.
- `mypy app main.py` passed (36 source files). One existing Starlette
  `TestClient` deprecation warning remains.

## Milestone 9 implementation (2026-10-13)

- Protected all item and usage routes with `X-API-Key`, using
  `hmac.compare_digest`; one configured owner identity is assigned to new
  items. Item reads and writes scope their SQL query by both item id and owner.
  Public health and readiness routes remain available; readiness reports a
  missing API key as `api_auth: unconfigured`.
- Added upload and reanalyze fixed-window rate limits keyed by API-key digest
  and client IP, plus app-level bounded request-body handling. Limits are
  process-local and need shared storage before running multiple API workers.
- Added configured CORS origins (wildcards rejected), request IDs in responses
  and structured logs, generic error envelopes, and `nosniff`, `DENY` frame,
  and `no-referrer` headers.
- Upload field `skip_analysis` and global `ANALYSIS_ENABLED=false` store an
  item as deferred without queueing model analysis. `ITEM_RETENTION_DAYS=0`
  disables automatic expiry; positive values purge old item blobs and rows at
  startup. The owner migration assigns existing ownerless items to
  `legacy-owner`.
- Added API tests for missing keys, cross-owner access across item operations,
  skipped analysis, per-key/IP upload limiting, app body limits, CORS, and
  retention deletion. SQLite timestamps are normalized to UTC before retention
  comparisons.
- `uv run pytest -m "not live"`: **163 passed, 2 live tests deselected**. Ruff
  lint, Ruff format check, and `mypy app main.py` passed. One existing
  Starlette `TestClient` deprecation warning remains.

## Milestone 10 documentation (2026-10-13)

- Rewrote `readme.md` to describe the implemented screenshot-to-search pipeline,
  including its image firewall, background processing, cache, Gemini extractor
  and legacy classifier, with a Mermaid flow diagram.
- Added PowerShell setup and upload/poll examples, the current API route table,
  environment configuration and defaults, local storage/deletion/retention
  behavior, test/evaluation commands, costs, privacy terms and limitations.
- Checked the default model's paid price against Google's official pricing page
  and checked unpaid/paid data-use terms on 2026-10-13. The project tier is
  still recorded as Free based on its last owner confirmation on 2026-10-11;
  the README calls out that date rather than presenting it as a live account
  check.

## Milestone 11 implementation (2026-10-13)

Requested directly by the owner as frontend work, which uild.md section 14
excludes; the brief is otherwise unchanged. Static-key auth stays as an
alternative credential, so no documented curl flow breaks.

- Added Alembic revision  004_user_sessions: a users table with a unique
  lowercase email and a sessions table holding only the SHA-256 digest of a
  token, its owner and its expiry. items.owner_id needed no change; a user
  hands out its uuid as the owner id.
- Passwords use PBKDF2-HMAC-SHA256 from the standard library in
  pp/core/security.py with a per-account salt and the iteration count encoded
  in the hash. No new dependency was added.
- pp/services/auth.py and pp/api/routes/auth.py add /auth/status,
  /auth/register, /auth/login, /auth/me, /auth/logout and
  /auth/logout-all. The token is delivered only as an httpOnly, SameSite=Lax
  cookie; registration is open for the first account and afterwards needs
  AUTH_ALLOW_REGISTRATION or python -m app.cli.bootstrap_user.
- get_current_owner accepts the session cookie or the static key, preferring the
  cookie, so every existing owner-scoped query and test keeps working.
  get_current_user has no key fallback, which is why /auth/me refuses a key
  caller. Readiness now reports pi_auth and session_auth separately and is
  ready when either path is configured.
- The first account adopts rows still owned by API_KEY_OWNER_ID, so a library
  saved through the key before accounts existed is not orphaned. Login and
  register pass through the fixed-window limiter keyed on credential or IP.
  Expired sessions are purged at startup, and startup skips that when the schema
  has not been migrated yet.
- Frontend: lib/auth.ts calls the account routes, hooks/useAuth.tsx holds the
  session, RequireAccount in App.tsx gates the shell, LoginPage.tsx signs in
  or creates the first account, and AccountMenu.tsx signs out or signs out
  everywhere. A 401 anywhere in lib/api.ts fires a window event that returns
  the reader to the sign-in page. The Vite proxy no longer injects
  X-API-Key: it would answer as one owner and skip per-account ownership.
- uv run pytest -m "not live": **182 passed, 2 live tests deselected**. Ruff
  lint, Ruff format check and mypy app main.py passed. Frontend
  
pm run check passed. One existing Starlette TestClient deprecation warning
  remains.