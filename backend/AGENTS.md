# Curated Space backend

Read [`../AGENTS.md`](../AGENTS.md) and [`../build.md`](../build.md) before
backend or ML implementation. `build.md` is the authoritative milestone plan;
implement one milestone at a time and do not touch frontend files.

The app currently has a FastAPI application factory, versioned health/readiness
routes, an Alembic-managed SQLite schema, an image firewall, local disk storage
with opaque keys, a versioned Gemini metadata extractor behind a swappable
`MetadataExtractor` interface, and `POST/GET /api/v1/items`.

`POST /api/v1/items` validates and stores the image, then runs `process_item`
inline and returns **201** with the item (`status: ready`, or `status: failed`
with an `error_code`; a provider failure is never a 500). Milestone 8 flips the
route to **202 + `pending`** and schedules that same idempotent
`services/pipeline.py:process_item` in the background. Do not add a second code
path for the 202 behaviour.

The serving classifier is intentionally deferred
until Milestone 4; rebuild it from `ml/dataset/curated_space_dataset.csv` then,
and do not interpret the committed artifact's numeric class ids in the meantime.

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

Demo the vertical slice:

```powershell
curl.exe -F "file=@tests/fixtures/test_image.jpg" http://localhost:8000/api/v1/items
```

Settings resolve SQLite and storage paths from the backend configuration. Run
Alembic before starting the app; production startup never creates tables. Tests
must use temporary databases and storage. Never log API keys, screenshot bytes,
or user-provided metadata.

`backend/pytest` needs a writable `--basetemp` on this machine; the default
`%TEMP%\pytest-of-*` root is not accessible.
