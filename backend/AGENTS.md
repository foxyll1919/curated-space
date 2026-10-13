# Curated Space backend

Read [`../AGENTS.md`](../AGENTS.md) and [`../build.md`](../build.md) before
backend or ML implementation. `build.md` is the authoritative milestone plan;
implement one milestone at a time and do not touch frontend files.

The app currently has a FastAPI application factory, versioned health/readiness
routes, an Alembic-managed SQLite schema, an image firewall, local disk storage
with opaque keys, a versioned Gemini metadata extractor behind a swappable
`MetadataExtractor` interface, the pixel-hash analysis cache, a budget guard and
`POST/GET /api/v1/items` plus `GET /api/v1/usage`.

Prices come from `app/core/gemini_pricing.json`, which records `verified_on` and
`source`. Do not reintroduce per-token price settings, and do not add a price
that was not read off the official page on the date the table records. A model
missing from the table has **unknown** cost: `estimate_cost_usd` returns `None`,
`llm_usage` stores 0.0 so one unknown price cannot fail an upload, and
`summarize_usage` names the models in `unknown_cost_models`. Returning `0.0` from
`estimate_cost_usd` instead would make an unpriced model look free and silently
understate the budget guard.

`GEMINI_RETURN_LABELS` makes the extractor request a taxonomy enum label in the
same call. It is a Milestone 6 benchmark affordance, off by default, and it
changes the response schema, so it also changes `schema_version` and therefore
the cache key. Never let the labeled and unlabeled schemas share a version.

The cache key is `sha256(normalized pixels) | model | prompt_version |
schema_version`, built from the extractor's `cache_identity` before any call.
`MetadataExtractor` therefore declares `cache_identity`; adding a provider means
implementing it, and the key must stay version-complete or the cache will serve
stale metadata under a key nothing else can find.

The budget guard (`services/budget.py`) reads `llm_usage` and stores a blocked
item as `status: "deferred"` with `error_code` `budget_exceeded` or
`rate_limited`. It is checked **after** the cache, because a cache hit costs
nothing and must not be blocked. Do not move it in front of the lookup.

`POST /api/v1/items` validates and stores the image, then runs `process_item`
inline and returns **201** with the item (`status: ready`, or `status: failed`
with an `error_code`; a provider failure is never a 500). Milestone 8 flips the
route to **202 + `pending`** and schedules that same idempotent
`services/pipeline.py:process_item` in the background. Do not add a second code
path for the 202 behaviour.

The serving classifier is the `legacy-8` **placeholder**, loaded once in the
lifespan from `settings.classifier_artifact` plus its `.card.json` sidecar. It
annotates items with `labels`, `classifier_score` and `abstained`; it never
blocks an item from reaching `ready`. Labels come from the taxonomy file, never
from hard-coded strings, so the v1 Intent x Domain guide is a data change.

`ml/model/curated_space_classifier.pkl` is the retired artifact whose `classes_`
are numeric ids. Nothing imports it. Do not serve it and do not try to infer its
mapping; `ml/model/curated_space_classifier_v2.pkl` is the one to retrain with
`python ml/train.py`.

The configured Gemini project is Free. Do not send sensitive screenshots to
that service. See the data-handling section in `../readme.md` and build brief
section 7a.

## Local commands

Use `uv` from this directory to sync the pinned lockfile and run checks:

```powershell
uv sync --locked
uv run alembic upgrade head
uv run pytest -m "not live"
uv run pytest -m live          # requires GEMINI_API_KEY
uv run ruff check .
uv run mypy app main.py
uv run uvicorn app.main:app --reload --port 8000
```

Run the eval harness from `ml/`, in the same environment:

```powershell
cd ml
uv run --project ..\backend python -m evals.run --list-configs
uv run --project ..\backend python -m evals.run --set evals\sets\synthetic --fake
```

Demo the vertical slice:

```powershell
curl.exe -F "file=@tests/fixtures/test_image.jpg" http://localhost:8000/api/v1/items
```

Retrain the classifier from the repository root:

```powershell
python ml/train.py
python ml/predict.py
```

## Milestone 9 API security and retention

`API_KEY` is optional once accounts exist: item and usage routes accept either a
session cookie or the key, and `get_current_owner` prefers the cookie. The key
maps to `API_KEY_OWNER_ID` (keep the default `legacy-owner` stable after
migration) and has no account behind it, so `/auth/me` refuses a key caller
rather than inventing one. Health and readiness remain public for probes.
Set `ALLOWED_ORIGINS` to an explicit JSON array of origins, never `*`. Upload and
reanalyze limits are process-local, so move the limiter behind shared storage
before scaling to multiple API workers. `ANALYSIS_ENABLED=false` or upload field
`skip_analysis=true` stores the item as deferred and never queues a model call.
`ITEM_RETENTION_DAYS=0` keeps items until explicitly deleted; positive values
purge old item rows and blobs at startup. The delete route also removes an
item's unshared analysis cache entry.

## Accounts and sessions

`users` and `sessions` arrive in Alembic revision `0004_user_sessions`. Passwords
are PBKDF2-HMAC-SHA256 from the standard library in `core/security.py`, with the
parameters encoded in the hash; **do not add a hashing dependency** without a
reason in the PR description. A session stores only the SHA-256 digest of a
random token, which reaches the browser as an httpOnly `SameSite=Lax` cookie and
never in a response body.

Registration is open for the first account only, so a fresh install has a way in;
`AUTH_ALLOW_REGISTRATION` or `app/cli/bootstrap_user.py` opens it further. The
first account adopts rows still owned by `API_KEY_OWNER_ID`, which is what keeps
a pre-account library visible. Every login and register call passes through
`enforce_rate_limit`, and `authenticate` answers identically for an unknown
address and a wrong password. Keep both properties if you touch that code.

Do not log passwords, session tokens, token digests or emails at INFO. A
`401` from any route means the session died, and the frontend relies on that to
return the reader to the sign-in page.

Settings resolve SQLite and storage paths from the backend configuration. Run
Alembic before starting the app; production startup never creates tables. Tests
must use temporary databases and storage. Never log API keys, screenshot bytes,
or user-provided metadata.

`backend/pytest` needs a writable `--basetemp` on this machine; the default
`%TEMP%\pytest-of-*` root is not accessible.
