# Backend + ML build progress

Last updated: 2026-10-11  
Scope: backend and ML only; frontend is out of scope.

## Milestone status

| # | Milestone | Status | Notes |
|---|---|---|---|
| 1 | Hygiene + checks | Done | Added secret/data/cache ignores, archived DistilBERT comparison scripts, removed the stale adapter, added `uv.lock`, pytest, Ruff, mypy and CI. Fresh locked sync, one pytest, Ruff and mypy passed. |
| 2 | Skeleton + config + DB | Done | Added settings, JSON logging, app factory/lifespan, typed SQLAlchemy models, Alembic and health/readiness routes. Migration preserved the six existing item rows. |
| 3 | Thin vertical slice | Done | Added the image firewall, local storage with opaque keys, the versioned Gemini extractor behind a swappable interface, `POST/GET /api/v1/items`, cost telemetry and fake-provider tests. See "Milestone 3 verification" below. |
| 4 | Classifier adapter | Planned | Owner chose to defer the committed artifact and rebuild from the CSV. Add shared `build_text`, model card and serving adapter; treat the synthetic labels as a code-path fixture, not quality evidence. |
| 5 | Cost layer | Planned | Pixel-hash cache, bounded retry policy, usage telemetry, budget guard and blocked/truncated/empty response mapping. |
| 6 | Eval harness + benchmark | Planned | Compare candidate Gemini models/settings and local classifier using synthetic CI fixtures first; real screenshot set is owner-supplied and must not be fabricated. |
| 7 | Full firewall + storage | Planned | Complete adversarial image validation, normalized storage, and authorized image retrieval. |
| 8 | Jobs + API features | Planned | **Flip `POST /items` to 202 + `pending` and schedule the existing `process_item` in the background**, recovery sweep, corrections, FTS, reanalysis and deletion. |
| 9 | API firewall + privacy | Planned | Auth/ownership, rate limits, CORS/security headers, `skip_analysis`, and retention behavior. |
| 10 | Docs | Planned | Rewrite README around the implemented screenshot pipeline and verified operating instructions. |

## Decisions and constraints

- The API key's AI Studio project is on the Free plan. Do not send sensitive or
  private screenshots to Gemini using this project. See the data-use note in
  `readme.md` and section 7a in `build.md`.
- `POST /api/v1/items` runs analysis **inline** and returns **201** with the item
  (`status: ready`, or `status: failed` with an `error_code`). A provider failure
  is never a 500. The brief's `curl` demo asserting **202** belongs to Milestone 8,
  which introduces the background job and flips the route to 202 + `pending`. The
  work itself is already a standalone idempotent `process_item(item_id)`, so M8
  only changes the route, not the pipeline.
- Classifier serving is deferred to Milestone 4. The committed artifact's
  numeric class IDs do not match the CSV's category strings; do not guess their
  mapping or overwrite the artifact before the planned rebuild.
- Existing SQLite data was migrated, not reset. The six existing item IDs and
  their generated upload filenames were retained; legacy category/tags are
  converted to JSON when present. User image bytes were not read by the migration.
- There is no `.git` directory in this workspace, so Git tracking/history and
  commit-level secret audits cannot be verified here. For the same reason the
  Milestone 3 deletions below are **not** recoverable from history.
- `Settings.gemini_input_price_usd_per_mtok` / `output` / `thinking` are
  placeholders carried from the brief, **not verified** against Google's pricing
  page. Recorded cost estimates are estimates, not a bill. Milestone 6 replaces
  them with a checked-in table that records when it was verified.

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

## Open questions for the owner

- Latency: 9.5 s on one sample versus the 8 s p95 target. Should M6 benchmark
  `thinking_level`, `media_resolution` and the flash vs flash-lite choice against
  a real screenshot set before we tune anything?
- Storage format is PNG for determinism, but that makes the model-input payload
  large (~1.0 MB for a 1080x1920 screenshot). Lossless WebP would cut it
  substantially. Worth switching in M6/M7 once quality is measurable?
- The brief's section 2 step 4 pricing figures were never verified; do you want
  me to check the official Gemini pricing page before M6?

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
