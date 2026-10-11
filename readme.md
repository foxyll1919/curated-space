# Curated Space

Curated Space is a screenshot-first personal knowledge library. Save a screenshot and get a concise title, description, tags, and two organizing facets: **Intent** (why the item may be useful) and **Domain** (what it concerns). The current work is focused on the ML and backend vertical slice; frontend and share-sheet experiences come later.

## Product goals

- Make saving a screenshot quick and reliable.
- Organize saved items consistently with the v1 Intent × Domain taxonomy.
- Keep AI calls measurable and cost-aware.
- Evaluate the product on screenshot inputs, not only text or URLs.
- Keep a local classifier as an evaluated baseline/challenger, not an assumed production dependency.

## Taxonomy and data

The current v1 labeling guide defines **7 Intent values × 7 Domain values**. The exact enum names and tie-break rules must come from that guide; this repository does not currently contain it, so this README intentionally does not recreate or guess those values. Keep the guide as the source of truth, version it, and use the same version in the prompt, response validator, API, evaluation script, and stored records.

The pasted project review describes a frozen set of **162 hand-labeled URL rows**. Those rows are useful for an initial text/category comparison, but they are not a screenshot benchmark: URL-derived examples do not measure the complete screenshot → Gemini metadata → facets path. Keep the 162 rows frozen as evaluation data. Do not tune the taxonomy or prompt against them after reporting results. Build a separate, human-labeled screenshot set (initial target: 30–50 varied images) before making screenshot pipeline quality claims.

The checked-in `ml/dataset/curated_space_dataset.csv` is an older 800-row, single-label dataset with labels `Design`, `Ideas`, `Inspiration`, `References`, `Research`, `Resources`, `Technology`, and `Tutorials`. It does not represent v1 Intent × Domain labels and should not be silently mixed with the new taxonomy or used to claim v1 classifier quality.

## Recommended AI pipeline

```text
Screenshot upload
       |
       v
Small image firewall
  byte/pixel limits -> decode allowlisted raster -> strip metadata
  -> safe re-encode -> generated UUID name
       |
       v
Gemini (one request for extraction + facets)
  normalized image -> schema-constrained JSON
  title + concise description + bounded tags
  intent: one value from v1 enum
  domain: one value from v1 enum
       |
       v
Validate and persist
  validate fields and taxonomy -> save image + metadata + versions
  -> return saved item and processing result
       |
       +---- optional offline/challenger evaluation:
             Gemini-extracted text -> local TF-IDF + LinearSVC baseline
             compare on suitable labeled data before serving it
```

For the first product slice, Gemini should produce Intent and Domain alongside title, description, and tags in the same structured response. That avoids a second AI call and gives us a simple end-to-end behavior to measure. Keep the local TF-IDF + LinearSVC model as an optional portfolio and cost/latency baseline. Promote it to the serving path only if it has enough v1-labeled training examples and an honest evaluation shows acceptable facet quality and a meaningful cost or latency advantage over Gemini.

## Recommended build order

1. **Benchmark Gemini on the frozen 162-row set.** Add a small reproducible script that asks for enum-constrained Intent and Domain, validates the response, and reports per-facet accuracy, macro-F1, and confusion tables. Record model ID, prompt/schema/taxonomy versions, and cache results by input plus those versions. Do not tune the guide against this frozen set. The v1 guide and the 162-row data file are not present in this checkout yet; bring those in before implementing or running this benchmark.
2. **Build one thin vertical slice.** Implement upload → minimal image firewall → lazily configured Gemini call with schema validation → persist metadata and taxonomy/model/prompt versions → return the saved item. Keep failure states clear and avoid saving unusable or unvalidated model output as complete metadata.
3. **Create a screenshot evaluation set.** Label an initial 30–50 varied screenshots and run the full image-to-facets path. Report per-facet metrics and review errors before claiming the URL benchmark predicts screenshot behavior.
4. **Evaluate the local classifier as a challenger.** Do not retrain it on the old labels and call that v1. If retaining the SVC, gather enough reviewed examples in the new taxonomy, and make its training inputs match the actual serving text (Gemini-generated title, description, and tags). Compare both systems on the same suitable fixed examples. With only 162 rows split across 49 possible facet cells, the set is too small to serve as a 49-cell training set and should remain evaluation-only.
5. **Harden for multiple users and production.** Add authentication/ownership, protected image retrieval, durable background processing if needed, migrations, object storage, stronger rate/spend limits, retention controls, and deployment observability before opening the service to public use. These are important production requirements, but they do not need to block a private single-user vertical slice.

## Current implementation

The repository is rebuilding its original prototype around the milestone plan:

- `backend/` now has an app factory, `/api/v1/health` and `/api/v1/ready`, settings, typed SQLAlchemy models, Alembic migrations, an image firewall, local disk storage with opaque keys, a versioned Gemini extractor behind a swappable interface, and `POST/GET /api/v1/items`. The former prototype `/api/items` routes have been removed during the data-model migration.
- `POST /api/v1/items` validates the upload, stores a sanitized PNG under a generated key, runs `process_item` inline and returns **201** with the item. The analysis is `status: ready` with a title, description and tags, or `status: failed` with an `error_code`; a provider failure is never a 500 and never exposes provider text. Milestone 8 flips this to **202 + `pending`** with background processing; the pipeline function itself is already idempotent and standalone.
- `backend/app/services/extraction/` sends an image to Gemini with a versioned prompt and a Pydantic `response_schema`, re-validates and sanitizes the response, and maps blocked/truncated/empty responses to stable error codes. The client is created lazily, so importing the module needs neither a key nor the network. It records token counts, latency and an estimated cost in `llm_usage` for every call.
- `ml/model/curated_space_classifier.pkl` is an older scikit-learn TF-IDF + LinearSVC single-label model trained by `ml/train.py`. It is not wired into `backend/app/main.py` and does not represent the v1 two-facet taxonomy.

The stale DistilBERT adapter and its backend smoke test have been removed. The old comparison scripts are archived in `ml/legacy/`. Classifier serving is deferred until Milestone 4; rebuild from the CSV there and do not infer labels from the committed artifact's numeric class ids.

## Cost, quality, and reliability

- Use one Gemini call to return all required fields and both facets. Request only concise fields and set an explicit output-token limit.
- Resize and re-encode screenshots before sending them. Choose dimensions and quality using the screenshot evaluation set so small text remains legible while reducing image payload.
- Use the official `google-genai` SDK behind a small service boundary. Configure the model by environment/configuration, create the client lazily, set a timeout, and validate a strict schema. A multi-agent or general-purpose agent framework is unnecessary for this linear workflow.
- Cache completed extraction by a cryptographic hash of normalized image bytes plus model, prompt, schema, and taxonomy versions. Never use a client filename as an identity or cache key.
- Track model ID, prompt/schema/taxonomy versions, latency, token usage, and failures. Redact secrets, prompts, and image contents from logs. Add bounded retries and rate/concurrency controls when integrating the call.
- Gemini's structured values are still untrusted input. Enforce enum membership, string length limits, a bounded tag count, and normalized text before persistence. Treat user feedback/corrections as explicit data; do not silently change the frozen evaluation labels.
- LinearSVC decision scores are not probabilities. If a local model is retained, do not expose scores as confidence without calibration and evaluation on separate labeled data.

## Gemini data handling status (2026-10-11)

The API key's AI Studio project is currently on the **Free** plan. Under Google's
current Gemini API Additional Terms, content submitted through Unpaid Services
(including screenshot images and model responses) may be used to improve and
develop Google products and machine-learning technologies; human reviewers may
review inputs and outputs for that purpose. Do not send screenshots containing
passwords, one-time codes, private conversations, financial details, IDs, or
other sensitive or personal information using this Free project. Keep screenshot
analysis disabled for sensitive content. Recheck the project's Plan and the
terms before changing this decision. Google's abuse-monitoring policy separately
describes 55-day retention of prompts, contextual information, and outputs for
policy enforcement.

The API currently stores uploaded image files under `backend/uploads/` and item
metadata in `backend/curated_space.db`; local deletion/retention controls are not
implemented yet. The API has no `skip_analysis` control yet; that is scheduled
for the API privacy milestone. Until it exists, treat any call to the Gemini
service as an explicit external disclosure and do not use it with sensitive
images. See the [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms),
[abuse monitoring policy](https://ai.google.dev/gemini-api/docs/usage-policies),
and [billing plan guide](https://ai.google.dev/gemini-api/docs/billing).

## Minimal image/API firewall for the first slice

Before any uploaded bytes are persisted or sent to Gemini:

- Enforce a small maximum request and image byte size.
- Allow only intended raster formats and verify the decoded format; do not trust the filename or multipart MIME type.
- Decode with a maintained image library, enforce width/height/pixel limits, reject malformed or decompression-bomb inputs, strip metadata, and re-encode to a safe format.
- Generate a UUID-based storage name and keep the file private. Never join a user-supplied filename to a filesystem path or return local filesystem paths in API responses.
- Set provider timeouts and handle provider failures without returning raw exception details, keys, or internal paths to callers.

For a private prototype, the essential slice is this image firewall plus the authenticated-to-provider secret boundary (secret in environment/secret manager) and validated model output. Authentication for end users can follow before adding multiple users or public access. Before public deployment, enforce authorization and per-user ownership on every item and image route, along with HTTPS, scoped CORS, rate/spend limits, retention/deletion behavior, and database migrations. `Base.metadata.create_all()` does not migrate existing SQLite tables; the current SQLite URL is process-working-directory-relative.

## Repository map

```text
backend/
  app/                    FastAPI factory, settings, health routes and DB layer
    core/                 config, structured logging, error envelope
    db/                   SQLAlchemy models and engine/session setup
    api/                  dependencies and versioned routes
    schemas/              Pydantic request/response contracts
    services/             image firewall, storage, extraction, usage, pipeline
  main.py                 Compatibility import for `uvicorn main:app`
  pyproject.toml          Backend dependencies and developer tooling
  uv.lock                 Locked backend dependency graph
  alembic.ini             Migration configuration
  migrations/             Versioned SQLite schema and legacy-data migration
  tests/                  Pytest checks, fixtures and a live-marked Gemini test
ml/
  dataset/                Legacy single-label training/evaluation CSVs
  model/                  Legacy TF-IDF + LinearSVC artifact
  train.py                Train the old single-label classifier
  predict.py              Local prediction example
  legacy/                 Archived DistilBERT comparison scripts
```

## Local development

Run backend commands from `backend/` because SQLite currently uses a CWD-relative path. Use the checked-in lockfile to create a reproducible environment.

```powershell
cd backend
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

The old `backend/gemini_service.py` and its print-based `test_gemini.py` / `test_pipeline.py` scripts have been removed; `app/services/extraction/` replaces them and is covered by pytest with a fake provider. The non-sensitive demo image lives at `backend/tests/fixtures/test_image.jpg`.

The Gemini enum benchmark cannot run until the v1 label guide and frozen 162-row data are available here.

Verified on 2026-10-11 against `gemini-3.5-flash-lite` with `media_resolution=MEDIUM` and `thinking_level=minimal`: 597 prompt tokens, 97 output tokens and an estimated $0.000295 per item. The price table in settings is a placeholder carried from the build brief and has **not** been checked against Google's current pricing page, so treat the cost figure as an estimate.
