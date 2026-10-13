# Curated Space

Curated Space is a screenshot-first personal knowledge library. Its backend validates and stores screenshots, extracts concise metadata, and lets the owner search and manage saved items. This repository contains the backend and ML work, plus the web frontend in [`frontend/`](frontend/README.md). There is no share-sheet client yet.

## Running the frontend

The frontend is a Vite app in `frontend/`. Start the backend on port 8000, then:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

It serves http://localhost:5173 and proxies `/api` to the backend. Open it and
create your account on the sign-in page: the backend sets an `httpOnly` session
cookie, so there is no key in the frontend environment and nothing for a browser
extension to read. See [`frontend/README.md`](frontend/README.md) for the sign-in
flow, the environment variables, the production reverse-proxy equivalent, and
the rest.

## Accounts and authentication

Accounts live in the same SQLite database as the items. A password is hashed
with PBKDF2-HMAC-SHA256 and a per-account salt (`app/core/security.py`); the
iteration count travels inside the hash, so it can be raised later without
invalidating existing rows. Signing in issues a random 32-byte token whose
SHA-256 digest is the only thing stored, delivered as an `httpOnly`,
`SameSite=Lax` cookie.

The first account may always be created, so a fresh install has a way in. It also
adopts the items saved through the API key before accounts existed, so an
existing library does not disappear on the first sign-in. Every later account
needs `AUTH_ALLOW_REGISTRATION=true` or the CLI:

```powershell
cd backend
uv run python -m app.cli.bootstrap-user you@example.com
```

Item and usage routes accept two credentials: a session cookie, whose user id
becomes the item owner, and the static `API_KEY` header, which keeps working for
scripts and `curl` and maps to `API_KEY_OWNER_ID`. Every item query is scoped by
owner, so one account cannot read or delete another's screenshots. Failed sign-in
attempts answer identically whether or not the address exists, and login and
registration are rate limited per client IP.

## How a screenshot moves through the system

~~~mermaid
flowchart LR
    A[Browser with a session cookie] --> B[FastAPI request limits and ownership]
    B --> C[Image firewall]
    C --> D[Sanitized PNG stored locally]
    D --> E[Pending item in SQLite]
    E --> F[Background job]
    F --> G{Pixel and version cache}
    G -->|hit| K[Validated or cached metadata]
    G -->|miss| H[Budget guard]
    H --> I[Gemini structured extraction]
    I --> K
    K --> L[Local legacy classifier]
    L --> J
    J --> M[Search, item, image and usage APIs]
~~~

The image firewall enforces byte, pixel and edge limits, decodes supported raster images, strips metadata, and re-encodes the image as PNG. It does not trust the submitted filename or MIME type. The stored image uses an opaque generated key.

The job first checks the extraction cache, keyed by normalized image pixels and the model, prompt and schema versions. A cache hit avoids a Gemini call. On a miss, the budget guard can defer analysis; otherwise Gemini returns schema-validated title, description and tags. The local TF-IDF + LinearSVC classifier annotates the result with a legacy category when it is available. The classifier is a placeholder and does not block an item from reaching a usable state.

Uploads return HTTP 202 with an item ID and a pending status. Poll the item endpoint until it becomes ready, failed or deferred. A skipped or globally disabled analysis is stored as deferred and does not enter the analysis queue.

## Current taxonomy and evaluation

The metadata extractor returns title, description and tags by default. The local classifier can attach a single category from the legacy eight-label taxonomy: Design, Ideas, Inspiration, References, Research, Resources, Technology and Tutorials. Gemini label output is an opt-in benchmark setting, not the default product behavior.

The planned screenshot Intent × Domain taxonomy is not finalized in this checkout. Its labeling guide and frozen screenshot gold labels are not present. The older 800-row category dataset is synthetic and templated; its training split is not evidence of screenshot quality. The real screenshot evaluation set has no completed gold labels, so accuracy and macro-F1 are unavailable. Do not treat synthetic metrics or unlabeled benchmark runs as model quality.

The evaluation harness runs the shipping firewall, extractor and classifier. It can use a fake provider without a key, reports `n/a` when gold labels are absent, reports unknown model prices as null, and omits extracted titles, descriptions and tags from reports. See [ml/evals/README.md](ml/evals/README.md).

## Local setup on Windows

Run the following in PowerShell from the repository root. Use a non-sensitive demo image. The configured Gemini project has been recorded as Free tier; do not send sensitive screenshots to it.

~~~powershell
cd backend
if (Test-Path .env) { throw "backend/.env already exists; add these settings without replacing the file." }
$apiKey = python -c "import secrets; print(secrets.token_urlsafe(32))"
$geminiSecret = Read-Host "Gemini API key" -AsSecureString
$geminiKey = [System.Net.NetworkCredential]::new("", $geminiSecret).Password
@"
API_KEY=$apiKey
GEMINI_API_KEY=$geminiKey
"@ | Set-Content -LiteralPath .env -Encoding ascii

uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
~~~

Keep the Gemini key and API key in an ignored local environment file or a secret manager for repeat use. Never commit them. If `backend/.env` already exists, add or update these settings without replacing its other contents. `API_KEY` is optional once accounts exist; with neither an account nor a key configured, item and usage endpoints answer 401. `/api/v1/health` and `/api/v1/ready` remain public for probes, and readiness reports `api_auth` and `session_auth` separately.

In a second PowerShell window, also from `backend/`, load the API key from the ignored environment file, then upload the bundled demo image and poll its status. The `curl` examples use the key because a shell has no browser cookie jar; the web app signs in instead.

~~~powershell
$credentials = Get-Content .env -Raw | ConvertFrom-StringData
$env:API_KEY = $credentials.API_KEY
$accepted = curl.exe -sS -H "X-API-Key: $env:API_KEY" -F "file=@tests/fixtures/test_image.jpg" http://localhost:8000/api/v1/items | ConvertFrom-Json
$accepted
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $item = curl.exe -sS -H "X-API-Key: $env:API_KEY" "http://localhost:8000/api/v1/items/$($accepted.id)" | ConvertFrom-Json
    if ($item.status -notin @("pending", "processing")) { break }
    Start-Sleep -Seconds 1
}
$item
~~~

The accepted response is `202` with an ID and `pending` status. The item response contains the current state and, after successful extraction, the metadata. If Gemini is unavailable or the request fails, inspect the item's `error_code`.

To save a screenshot without sending it for analysis, include the form field `skip_analysis=true`. The sanitized image and item are still stored locally:

~~~powershell
curl.exe -sS -H "X-API-Key: $env:API_KEY" -F "skip_analysis=true" -F "file=@tests/fixtures/test_image.jpg" http://localhost:8000/api/v1/items
~~~

Set `ANALYSIS_ENABLED=false` to disable analysis for all uploads. This global setting also prevents the reanalyze endpoint from queueing a model call.

## API

All paths below are under `/api/v1`. Item and usage routes accept either the session cookie from `/auth/login` or the service key in the `X-API-Key` header. Every item lookup is scoped to the owner behind that credential. An item owned by another identity is returned as not found.

| Method | Path | Purpose |
|---|---|---|
| GET | `/auth/status` | Public: whether registration is open and how many accounts exist |
| POST | `/auth/register` | Create an account and sign in; open for the first account, or when `AUTH_ALLOW_REGISTRATION` is set |
| POST | `/auth/login` | Exchange email and password for a session cookie |
| GET | `/auth/me` | The signed-in account, or 401; an API-key caller has no account |
| POST | `/auth/logout` | Revoke this session and clear the cookie |
| POST | `/auth/logout-all` | Revoke every session for the account |
| POST | `/items` | Upload a screenshot; optional `skip_analysis`; returns 202 |
| GET | `/items/{id}` | Read item status and metadata |
| GET | `/items` | List and search; supports `status`, `label`, `q`, `limit` and `cursor` |
| GET | `/items/{id}/image` | Retrieve the sanitized image |
| PATCH | `/items/{id}` | Correct title, tags or labels |
| POST | `/items/{id}/reanalyze` | Queue analysis again, subject to cache and budget |
| DELETE | `/items/{id}` | Delete the item image and row |
| GET | `/usage` | Read token, call, cache and estimated-cost summaries |
| GET | `/health` | Public liveness probe |
| GET | `/ready` | Public component report; database, storage and at least one credential path determine the ready status |

Item states are `pending`, `processing`, `ready`, `failed` and `deferred`. Errors use a generic envelope with a stable code and request ID. Full item metadata and image bytes are never returned in error messages.

List search AND-matches terms against title, description and tags. `label` matches any stored label value. The API returns pagination cursors; it does not expose local storage paths or storage keys.

## Configuration

Settings can be supplied as environment variables or in `backend/.env`. Environment names are case-insensitive. Defaults below are from the current backend settings.

| Variable | Default | Purpose |
|---|---:|---|
| `API_KEY` | unset | Optional shared key for item and usage routes; the browser uses a session cookie instead |
| `API_KEY_OWNER_ID` | `legacy-owner` | Stable owner ID associated with the single configured key; keep it stable after migration |
| `AUTH_ALLOW_REGISTRATION` | `false` | Allow account creation beyond the first one |
| `AUTH_SESSION_TTL_DAYS` | 30 | Session cookie lifetime |
| `AUTH_COOKIE_NAME` | `cs_session` | Session cookie name |
| `AUTH_COOKIE_SECURE` | `false` | Mark the cookie `Secure`; set true when serving over HTTPS |
| `AUTH_PASSWORD_MIN_LENGTH` | 10 | Minimum password length |
| `PASSWORD_HASH_ITERATIONS` | 600000 | PBKDF2-HMAC-SHA256 iterations for new password hashes |
| `LOGIN_RATE_LIMIT` | 10 per window | Sign-in and registration attempts allowed per client IP |
| `GEMINI_API_KEY` | unset | Gemini Developer API key; extraction is unavailable without it |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Extraction model |
| `GEMINI_MEDIA_RESOLUTION` | `MEDIUM` | Image resolution sent to Gemini |
| `GEMINI_THINKING_LEVEL` | `minimal` | Gemini thinking setting |
| `ANALYSIS_ENABLED` | `true` | Global analysis switch |
| `ANALYSIS_CACHE_ENABLED` | `true` | Cache successful extraction by image and version identity |
| `MAX_UPLOAD_BYTES` | 8 MiB | Maximum uploaded image part |
| `MAX_REQUEST_BODY_BYTES` | 8 MiB + 64 KiB | Maximum complete HTTP request body |
| `MAX_IMAGE_EDGE` | 8000 pixels | Maximum decoded width or height |
| `MAX_IMAGE_PIXELS` | 40,000,000 | Maximum decoded pixel count |
| `MODEL_INPUT_MAX_EDGE` | 1280 pixels | Longest edge used to resize the image sent to Gemini |
| `UPLOAD_RATE_LIMIT` | 10 per window | Upload requests allowed per API key and IP |
| `REANALYZE_RATE_LIMIT` | 5 per window | Reanalyze requests allowed per API key and IP |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Fixed rate-limit window |
| `ALLOWED_ORIGINS` | `[]` | JSON array of explicit CORS origins; `*` is rejected |
| `MAX_CONCURRENT_ANALYSES` | 2 | In-process concurrent analysis limit |
| `STUCK_JOB_TIMEOUT_MINUTES` | 15 | Age after which a processing item is reset on startup |
| `DAILY_COST_CAP_USD` | 1.00 | Estimated daily provider-cost guard; zero disables it |
| `MAX_ANALYSES_PER_MINUTE` | 30 | Provider analysis guard; zero disables it |
| `ITEM_RETENTION_DAYS` | 0 | Zero keeps items until deletion; positive values purge older items at startup |
| `DATABASE_PATH` | `backend/curated_space.db` | SQLite database path |
| `STORAGE_PATH` | `backend/uploads` | Local sanitized-image directory |
| `GEMINI_TIMEOUT_MS` | 30,000 | Timeout for one provider request |
| `GEMINI_MAX_OUTPUT_TOKENS` | 300 | Maximum generated output tokens |
| `GEMINI_TOTAL_TIMEOUT_MS` | 30,000 | Overall timeout across retries |
| `GEMINI_MAX_RETRIES` | 2 | Bounded transport retries |
| `GEMINI_MAX_SCHEMA_REPAIRS` | 1 | Schema repair attempts |
| `GEMINI_RETURN_LABELS` | `false` | Benchmark-only Gemini taxonomy output; off by default |

`ALLOWED_ORIGINS` is a JSON array, for example `["http://localhost:5173"]`. CORS credentials are disabled. Upload and reanalyze limits are in-process, so multiple API workers do not share counts.

## Cost and provider data handling

The default model is `gemini-3.5-flash-lite`. Checked against Google's pricing page on 2026-10-13, its Standard paid rates are $0.30 per million input tokens and $2.50 per million output tokens; output pricing includes thinking tokens. The complete checked-in table at `backend/app/core/gemini_pricing.json` was last verified on 2026-10-11. The API project is recorded as Free tier, where eligible model usage is free within its quotas. The app's cost estimate and budget guard use paid-rate equivalents, so they remain useful for comparing usage but do not represent Free-tier charges. Estimates vary with the image and response. Unknown models are reported as unknown rather than free. A local cache hit makes no provider call. A provider failure that omits usage metadata can make the local estimate lower than the eventual provider bill.

The Gemini project used by this prototype was last recorded as Free tier on 2026-10-11. Google's current Gemini API terms say that content and responses submitted through unpaid services may be used to improve Google products and that human reviewers may review inputs and outputs. Do not send sensitive, confidential or personal screenshots through an unpaid project. A `skip_analysis` upload is still stored by this backend but is not sent to Gemini. Check the project's billing tier and Google's terms before changing this policy. Paid services have different data-use terms; confirm the specific project and applicable terms before relying on them.

Official references: [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), [billing tiers](https://ai.google.dev/gemini-api/docs/billing), [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms).

## Local data, deletion and retention

By default, sanitized screenshots are stored as files under `backend/uploads/`. Item metadata, extraction cache entries and token/cost usage records are stored in `backend/curated_space.db`. These paths are configurable. Keep both private and include them in local backup and deletion practices.

`DELETE /api/v1/items/{id}` removes that item's image and database row. A cache entry is removed when no other item refers to it. Usage rows remain for aggregate cost history with their item link cleared. `ITEM_RETENTION_DAYS=0` disables automatic expiry. A positive value removes old item rows and image files when the service starts. Retention is based on item creation age, so set it deliberately and back up data before enabling it.

## Tests and evaluation

From `backend/`, run the non-live suite and static checks:

~~~powershell
uv run pytest -m "not live" --basetemp .pytest-tmp
uv run ruff check app main.py migrations tests
uv run ruff format --check app main.py migrations tests
uv run mypy app main.py
~~~

The live Gemini test requires `GEMINI_API_KEY` and is excluded from the command above. Use only a non-sensitive screenshot with a project whose data-use tier you have confirmed.

To run the synthetic evaluation without a key, from `ml/`:

~~~powershell
uv run --project ..\backend python -m evals.run --set evals\sets\synthetic --taxonomy taxonomy\legacy-8.json --config "gemini-3.5-flash-lite|medium|minimal" --fake --provider-labels
~~~

Synthetic sets exercise the code path, not screenshot quality. For useful accuracy or macro-F1, label a separate screenshot set and keep its gold labels out of training.

## Known limitations

- Accounts are email plus password with no password reset by email, no second factor, and no roles. Sessions are revoked by signing out, signing out everywhere, or expiry; there is no rotation or reuse detection.
- The static `API_KEY` remains an alternative credential for scripts and maps to one owner id that is not an account.
- Background jobs use FastAPI in-process tasks. Startup recovery handles interrupted work, but there is no durable distributed queue.
- Rate limits are process-local and reset when the service restarts. They are not shared between workers.
- Storage and database defaults are local disk and SQLite; production object storage, database operations, HTTPS termination and secret management are deployment responsibilities.
- The screenshot Intent × Domain guide and labeled screenshot evaluation set are absent. The serving classifier is the legacy eight-category placeholder; its score is a LinearSVC decision margin, not a probability or confidence.
- The cost report is an estimate from recorded token usage, not a provider invoice. Failed provider calls without usage metadata may be undercounted.
- There is no frontend or mobile share-sheet integration in this repository.

## Repository map

~~~text
backend/
  app/                  FastAPI application, routes, settings and services
  migrations/           Alembic schema and data migrations
  tests/                Offline tests and live-marked provider test
  pyproject.toml         Backend dependencies and tools
  uv.lock                Locked backend environment
ml/
  src/curated_ml/        Shared classifier, taxonomy and data utilities
  model/                 Legacy-8 model and model card
  taxonomy/              Current taxonomy files
  evals/                 Evaluation harness and synthetic set
  train.py               Train the placeholder classifier
  legacy/                Archived experiments
build.md                 Authoritative architecture and milestone brief
PROGRESS.md              Implemented work and evaluation notes
