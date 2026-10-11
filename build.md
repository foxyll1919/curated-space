# Curated Space — Backend + ML Build Brief (for the coding agent)

Audience: the coding agent working in this repo. Author's role: senior GenAI engineer giving direction; you write the code.
Scope: `backend/` and `ml/` only. **Do not touch any frontend.** Date of this brief: 2026-10-11. **Revision 2 (council-reviewed):** milestones reordered so a working demo exists early; privacy, blocked-response handling, pixel-based hashing and acceptance targets added.

Read first: `readme.md`, `AGENTS.md`, `backend/AGENTS.md`. Where this brief and the README disagree, **this brief wins**, and you must list each disagreement in your first PR description.

---

## 0. Product in one paragraph

A user saves a **screenshot**. The backend validates and sanitizes the image, asks Gemini for a title, short description and tags (cheaply), classifies it locally with the scikit-learn model in `ml/model/`, stores everything, and serves it back through search/list APIs. Every stage must be measurable, replaceable and safe against hostile input.

## 1. Decisions already made (do not re-litigate)

1. **Screenshot-first.** Input is an image. The old link-bookmark taxonomy (labeling guide v1, 162 URL rows) is a frozen side asset, not the product spec.
2. **DistilBERT is dead.** Serving model = `ml/model/curated_space_classifier.pkl` (TF-IDF + LinearSVC). Delete `backend/ml_service.py` and `backend/test_ml.py`; drop `torch` and `transformers` from requirements. Move `ml/benchmark.py` and `ml/eval_realistic.py` to `ml/legacy/` with a README note (do not delete).
3. **The taxonomy is not final.** The current artifact predicts 8 legacy labels (Design, Ideas, Inspiration, References, Research, Resources, Technology, Tutorials). A two-facet screenshot taxonomy (Intent x Domain, "v2") is being designed by the owner. Therefore:
   - Never hard-code label strings in application code. Load them from the artifact's model card (section 6).
   - Treat the legacy 8-label classifier as a **placeholder** (`taxonomy_version = "legacy-8"`), wired in so the pipeline runs end to end.
   - Persist predictions as a `labels` JSON object (`{"category": "Tutorials"}` today, `{"intent": ..., "domain": ...}` later) so v2 needs no schema change.
4. **The 800-row `curated_space_dataset.csv` is synthetic and templated** (a cue phrase like "cheat sheet" decides the label; topic words barely matter) and its labels contain inconsistencies. Its accuracy says nothing about real screenshots. Use it only to exercise the training/serving code path. **Never report its test accuracy as model quality.**
5. **No LangChain/LangGraph for this flow.** It is a linear extract -> classify pipeline. Frameworks that add no capability here are noise. "Modern" means the practices in this brief (typed structured outputs, provider interface, caching, cost telemetry, evals, observability, idempotent jobs), not a bigger dependency list. Revisit an agent framework only when a real multi-step/tool workflow exists (for example "ask questions across my saved screenshots").

## 2. Checks to run BEFORE writing features (report results in the first PR)

1. `python --version`; `pip freeze` for the current venv; record the **scikit-learn version** (pickle artifacts are version-sensitive).
2. In a throwaway script: `joblib.load` the `.pkl`, print `type(model)`, `model.classes_`, the TF-IDF vocabulary size, and the scikit-learn version it was trained with if discoverable. Confirm the 8 labels match `ml/dataset/curated_space_dataset.csv`.
3. Run `python ml/train.py` from the repo root on a **copy**; confirm it reproduces (do not overwrite the committed artifact yet).
4. **Verify the Gemini model id.** Run `client.models.list()` with the real key and confirm the chosen model supports image input and JSON schema output. Current state as I found it (verify, do not trust blindly):
   - Stable on the docs I read: `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`.
   - The existing code uses `gemini-3.8-flash`, which appears in a *short-term availability* list (retired 45 days after a replacement ships). Do not build on it.
   - The Gemini 2.5 family is scheduled to shut down **2026-10-16**. Do not use it.
5. Secrets audit: search the working tree and git history for API keys, `.env` files, and committed `curated_space.db` / `backend/uploads/*`. Add `.gitignore` entries for `*.db`, `backend/uploads/`, `venv/`, `.env*`, `graphify-out/cache/`. If anything sensitive is in history, **stop and tell the owner**; do not rewrite history yourself.
6. Check the dependency list against `import` statements. Known gaps: `scikit-learn`, `joblib`, `pandas`, `Pillow`, `pydantic-settings`, `alembic` are missing; `torch`/`transformers` are dead weight.

## 3. Target layout

```
backend/
  pyproject.toml            # uv-managed, pinned via lockfile; ruff, pyright/mypy, pytest config
  alembic.ini, migrations/
  app/
    main.py                 # app factory + lifespan (load classifier once, recover stuck jobs)
    core/ config.py logging.py security.py errors.py
    api/ deps.py routes/{items.py,health.py,usage.py}
    db/ session.py models.py
    schemas/                # Pydantic request/response models (the public contract)
    services/
      image_firewall.py
      storage.py            # opaque keys; local-disk impl behind an interface
      extraction/ base.py gemini.py schema.py prompts.py
      classification/ base.py sklearn_svc.py
      pipeline.py           # orchestrates stages, owns the status state machine
      cache.py  usage.py  jobs.py
  tests/
ml/
  src/curated_ml/ text.py taxonomy.py model_card.py   # shared by training AND serving
  train.py  predict.py  evals/  model/  dataset/  legacy/
```

`curated_ml` must be installable (`pip install -e ml`) and imported by both `ml/train.py` and the backend. **One `build_text(title, description, tags)` function, used by both training and serving, no exceptions.** (Today three different text formats exist across `train.py`, `predict.py`, `ml_service.py`.)

Tooling: Python 3.12+ if the environment allows, `uv`, `ruff` (lint + format), a type checker in CI, `pytest`, `pre-commit`. SQLAlchemy **2.0 typed style** (`Mapped[...]`), Pydantic v2, `pydantic-settings`. Look up current versions and pin them.

## 4. Data model (replace the current `Item`)

Table `items` (UUID PK; generate in app, store as string):

| Column | Notes |
|---|---|
| `owner_id` | nullable now, always filtered in queries; single static owner until auth grows |
| `status` | `pending` -> `processing` -> `ready` / `failed` / `deferred` (budget hit) |
| `image_key` | opaque storage key, never a path or URL |
| `content_sha256` (hash of normalized pixels, see section 5), `mime`, `width`, `height`, `bytes` | the rest describe the **sanitized** stored image |
| `title`, `description` | nullable until ready |
| `tags` | JSON array of strings (not a comma string) |
| `ocr_text` | nullable; only filled when the optional text-extraction flag is on (section 7); included in FTS |
| `labels` | JSON object (see decision 3) |
| `classifier_score`, `abstained` | decision margin, NOT "confidence" (LinearSVC has no probabilities) |
| `taxonomy_version`, `classifier_version`, `extractor_model`, `prompt_version` | provenance |
| `error_code` | short enum, never raw provider text |
| `user_corrected` | bool; edited items are future ground-truth training/eval data |
| `created_at`, `updated_at`, `analyzed_at` | UTC, timezone-aware |

Also: `analysis_cache` (key = `sha256 + model + prompt_version + schema_version`, value = validated JSON), `llm_usage` (item_id, model, prompt/output/thinking tokens, latency_ms, status, est_cost_usd, created_at), and an FTS5 virtual table over title/description/tags for search.

Use **Alembic** from the first commit. The existing `curated_space.db` is dev data: write a migration that carries over `id`, `image_url` -> `image_key`, and the nullable text fields; or document a clean reset. Ask the owner which if unsure. `Base.metadata.create_all()` must not run in production code. SQLite: enable WAL and `foreign_keys=ON`; resolve the DB path from settings, not the working directory.

## 5. Image firewall (`services/image_firewall.py`)

Runs before anything is persisted or sent to a model. Pure function: `bytes -> SanitizedImage | FirewallError`. Requirements:

1. **Bounded read.** Stream the upload in chunks and abort at `MAX_UPLOAD_BYTES` (default 8 MB). Reject early on an oversized `Content-Length`. Never `await file.read()` unbounded.
2. **Trust nothing the client says.** Ignore filename and `Content-Type` for decisions; the client filename is never used in any path or key.
3. **Decode to verify.** Pillow: `Image.open` + `verify()`, then reopen to load. Allow only PNG, JPEG, WebP by *decoded* format. Reject animated/multi-frame, truncated, and zero-size images.
4. **Pixel and dimension limits.** Set `Image.MAX_IMAGE_PIXELS` explicitly, catch `DecompressionBombError`, enforce max edge (default 8000 px) and max pixels.
5. **Normalize.** `ImageOps.exif_transpose`, convert to RGB/RGBA as needed, **drop all metadata** (EXIF, ICC, text chunks), re-encode to a safe format (WebP or PNG; pick one and keep it deterministic).
6. **Produce two outputs:** the sanitized image to store, and a **model-input** copy downscaled to max edge ~1280 px.
7. **Hash the decoded, normalized pixel buffer** (mode + size + raw pixel bytes, SHA-256), not the re-encoded file, for dedupe and cache keys. Hashing encoded bytes would silently invalidate every cache entry whenever Pillow or the encoder is upgraded. (Perceptual hashing for near-duplicates is a later option, not now.)
8. Stable error codes: `too_large`, `unsupported_type`, `corrupt_image`, `too_many_pixels`, `animated`. Map them to 413/415/422 without leaking internals.

Test with crafted files: a pixel-bomb PNG, a `.jpg` that is really HTML, a polyglot, a truncated JPEG, an animated GIF/WebP, a 0-byte file, an EXIF-GPS photo (assert metadata is gone).

Serving images: only via `GET /api/v1/items/{id}/image` with an ownership check, fixed `Content-Type` from stored `mime`, `X-Content-Type-Options: nosniff`, `Content-Disposition: inline` with a generated name, and no filesystem paths in any response.

## 6. Classifier (`services/classification/` + `ml/src/curated_ml`)

- Load the artifact **once** in the FastAPI `lifespan`, from `settings.CLASSIFIER_ARTIFACT`. Define `Classifier` protocol: `predict(text) -> Prediction(labels: dict[str,str], score: float, abstained: bool, model_version: str, taxonomy_version: str)`.
- **Model card sidecar** `curated_space_classifier.card.json` written by `train.py`: scikit-learn version, label list, taxonomy version, training-data SHA-256 and row count, metrics (macro-F1, per-class precision/recall), created_at, `build_text` version. On load, compare scikit-learn versions: refuse to start in production mode on mismatch, warn in dev.
- **Abstain rule:** use the margin between the top-1 and top-2 decision scores and store the threshold in the card. **For the legacy-8 artifact, a threshold tuned on the synthetic validation split is meaningless**, so use a fixed conservative default from settings and record `threshold_source: "default-unvalidated"` in the card; derive it from validation only once a human-labeled holdout exists. If abstained, `labels` is empty and the UI shows "uncategorized". Do not rename decision scores "confidence" anywhere (API field is `score`). Calibration (`CalibratedClassifierCV`) is a later upgrade.
- `train.py` hardening: fail on missing or unknown labels, assert the expected label set from a taxonomy file, write the card, and print macro-F1 + per-class report. Keep a **separate human-labeled holdout** that is never used for tuning (it does not exist yet; create the folder and loader, leave the data to the owner).
- `pickle`/`joblib` artifacts execute code on load: only load from the configured path, never from user input, never from the network.

## 7. Gemini extraction (`services/extraction/`)

Interface: `MetadataExtractor.extract(image: ModelInput) -> ExtractedMetadata`. The Gemini implementation sits behind it so the provider is swappable and fakeable in tests.

**Library:** the official `google-genai` SDK. Construct the client **lazily** (on first use, from settings); importing the module must never need a key or the network.

**Structured output, not string parsing.** Define a Pydantic model:

```
ExtractedMetadata:
  title: str        (1..80 chars)
  description: str  (1..280 chars)
  tags: list[str]   (max 8; each 2..30 chars)
```

Pass it as `response_schema` with `response_mime_type="application/json"`, then validate again with Pydantic and apply post-rules: lowercase/trim tags, collapse whitespace, strip control characters and any markup, dedupe, cap lengths, drop empties. Delete the code-fence-stripping `json.loads` hack.

**Cost controls (all configurable, all measured):**

1. **Cheapest adequate model.** Default `GEMINI_MODEL=gemini-3.5-flash-lite` (verify per section 2 and against the current Gemini API pricing page; I saw third-party pricing for 3.1-flash-lite of about $0.25 in / $1.50 out per million tokens, which you must confirm). Model id lives in config only. Compare 3.5-flash-lite vs 3.1-flash-lite vs 3.5-flash in the eval harness before locking the default.
2. **`media_resolution`.** For Gemini 3 models image tokens are set by this parameter, roughly 280 (low) / 560 (medium) / 1120 (high) per image. Default to MEDIUM for screenshots (small UI text), benchmark LOW/MEDIUM/HIGH, and expose it as a setting. Honest note: downscaling the image mainly saves upload bytes and latency; do not claim it cuts tokens. Check the SDK docs for whether per-part `media_resolution` is available on the API version you use; the global generation config setting is the fallback.
3. **Minimize thinking.** Set `thinking_level="minimal"` (Flash family; on Gemini 3 do not also pass `thinking_budget`, that errors). **Verify the chosen model, flash-lite included, actually accepts `minimal`**; if not, use the lowest level it accepts and record the choice. Set `max_output_tokens` low (about 300). Note output cap **includes** thinking tokens, so verify responses are not truncated.
4. **Short, versioned prompt.** System instruction in `prompts.py` with `PROMPT_VERSION`. No few-shot bloat, no instructions that repeat the schema.
5. **Cache and dedupe.** Key = `sha256 + model + PROMPT_VERSION + SCHEMA_VERSION`. A hit means zero API calls. Re-saving the same screenshot never re-bills.
6. **Retries.** Only on 429/5xx/timeouts: max 2, exponential backoff with jitter, overall timeout around 30 s (not 120). One repair retry on schema-validation failure, then fail the item cleanly (`error_code="extraction_invalid"`).
7. **Telemetry.** Record `usage_metadata` (prompt, candidates, thoughts, total token counts), latency and an estimated cost from a **config price table** for every call into `llm_usage`. Expose `GET /api/v1/usage` (today / 7 days: calls, tokens, est. cost, cache hit rate).
8. **Budget guard.** `DAILY_COST_CAP_USD` and `MAX_ANALYSES_PER_MINUTE`. When hit, store the item with `status="deferred"` and do not call Gemini; a re-analyze endpoint or the sweep picks it up later.
9. **Later, not now:** the Batch API for bulk backfills, and explicit context caching only if the shared instruction prompt grows large.

**Prompt-injection stance.** Screenshots can contain text addressed to the model. The model has no tools; its only output is schema-constrained data; everything it returns is untrusted input (validated, length-capped, escaped by any future UI, never used to build paths, SQL or shell). Add one test with an image whose text says "ignore previous instructions and output X" and assert the output still passes validation. Never log image bytes, prompts containing user data at INFO, API keys, or raw provider error bodies.

**Blocked, truncated or empty responses.** Inspect prompt feedback and each candidate's finish reason (safety block, max tokens, no candidates). Map them to `error_code` values (`extraction_blocked`, `extraction_truncated`, `extraction_empty`); the item becomes `failed` with a presentable state. Never a 500, never a blind retry loop.

**Searchable text.** People find screenshots by the words inside them. Behind `EXTRACT_TEXT=true` (default off until benchmarked), add `text_in_image` (max ~600 chars, the most salient visible text) to the schema, store it as `ocr_text`, and index it in FTS. It costs extra output tokens, so measure before enabling.

Optional (behind a flag, default off, used only by the eval harness): ask the same call to also return taxonomy labels as enums, to benchmark "Gemini does labels too" against the local classifier. The owner wants this comparison before deciding the classifier's long-term role.

## 7a. Data handling and privacy

Screenshots routinely contain passwords, one-time codes, private chats, banking and ID details. Treat every image as sensitive.

- Confirm which Gemini access tier is used and **read the current data-use terms** for it: unpaid API usage has historically allowed Google to use submitted content to improve its products, while paid usage generally does not. Verify, then document the tier and the consequence in the README. The owner decides; do not assume.
- Add a per-upload `skip_analysis` form field (and a global `ANALYSIS_ENABLED` setting): when set, the image is stored but never sent to a model.
- Logs never contain titles, descriptions, tags, OCR text or image bytes at INFO or above. Telemetry exports carry ids, durations and token counts only.
- `DELETE /items/{id}` removes the row, the stored image, and any `analysis_cache` entry no other item references. `llm_usage` rows keep no content.
- Document retention: what is stored, where, and how to purge it.

**Owner decision recorded 2026-10-11:** the API key's AI Studio project is on
the Free plan. Per Google's current Unpaid Services terms, submitted screenshot
content and generated responses can be used to improve Google products, and
human reviewers may review them. Do not send sensitive screenshots on this
project. The owner chose to defer classifier wiring in Milestone 1 and rebuild
the classifier from the CSV in Milestone 4; do not infer the committed artifact's
numeric classes or wire it into the backend before then.

## 8. Pipeline, jobs, API

**State machine** in `pipeline.py`: `pending -> processing -> ready | failed | deferred`. Each step is idempotent: re-running a `ready` item with the same versions does nothing; changed versions can be re-analyzed on request.

**Async processing.** `POST /api/v1/items` validates and stores the image, inserts the row as `pending`, and returns **202** with the item id immediately. Analysis runs through a `JobRunner` interface. Initial implementation: FastAPI `BackgroundTasks` with a bounded semaphore. On startup, a sweep resets items stuck in `processing` (older than N minutes) back to `pending` and re-queues them. Keep the interface narrow so swapping in a durable queue (Redis + arq) later changes one file. Blocking SDK/SQLAlchemy calls must not run on the event loop (use the async client or a threadpool; pick one and stay consistent).

**Endpoints** (versioned under `/api/v1`):

| Method | Path | Purpose |
|---|---|---|
| POST | `/items` | multipart `file`; returns 202 `{id, status}` |
| GET | `/items/{id}` | item + status (clients poll; SSE can come later) |
| GET | `/items` | cursor pagination, `status`, `label` filters, `q` (FTS5 search) |
| PATCH | `/items/{id}` | user edits title/tags/labels; sets `user_corrected=true` |
| DELETE | `/items/{id}` | removes row and stored image |
| POST | `/items/{id}/reanalyze` | respects cache and budget |
| GET | `/items/{id}/image` | authorized image bytes |
| GET | `/health`, `/ready` | liveness; readiness checks DB, classifier loaded, storage writable |
| GET | `/usage` | cost/token summary |

Response models are Pydantic schemas; never return ORM objects or storage keys. Use one error envelope `{error: {code, message, request_id}}`.

## 9. API-level firewall

- **Auth:** a static API key via header, compared with `hmac.compare_digest`, loaded from settings; return 401 without hints. Every query filters by `owner_id`.
- **Rate limits** per key and per IP on upload and reanalyze (a maintained library such as `slowapi`, or a small in-process limiter behind an interface), plus a concurrency cap on analyses.
- **CORS** allowlist from settings (no `*`). Security headers middleware (`nosniff`, `frame-options`, a strict referrer policy). Request-ID middleware and structured JSON logging with redaction.
- Request body size limit also enforced at the app layer (the reverse proxy limit will be documented, not assumed).
- Generic error responses; full detail only in server logs.

## 10. Observability

Structured logs (`structlog` or stdlib JSON) with `request_id`, `item_id`, stage and duration. Add OpenTelemetry tracing hooks around: firewall, cache lookup, Gemini call, classify, DB write. A console exporter is enough now; the point is the spans exist. Keep a `/usage` summary so cost is visible during development.

## 11. Evaluation (this is what separates a project from a demo)

Create `ml/evals/` with a CLI: `python -m evals.run --set <csv-or-folder> --config <name>`. It must report, as a JSON file and a printed table: per-facet accuracy and macro-F1, per-class precision/recall, abstain rate, p50/p95 latency, **tokens per item and estimated $ per item**, and cache hit rate. Configs to compare (all via settings, no code edits): model id x `media_resolution` x thinking level; local classifier vs Gemini-enum labels. Use fakes for CI and a real-key run on demand.

Inputs the owner will supply (do not fabricate any of them): a pilot set of 40-60 real screenshots, then a frozen ~150-image labeled set under the v2 labeling guide. Build the loader and metric code now against a tiny synthetic fixture; keep the real data out of git unless the owner says otherwise.

## 12. Tests

`pytest`; Gemini and storage faked behind their interfaces; temp SQLite per test; `TestClient` with dependency overrides. Required coverage: firewall cases (section 5), schema validation and tag sanitizing, cache hit/miss and version invalidation, budget guard, retry policy (429 then success; schema failure then repair), pipeline idempotency and the stuck-job sweep, auth/ownership (user A cannot read user B's item), pagination, and one `@pytest.mark.live` Gemini test skipped without a key. Replace the print-based `test_pipeline.py`, `test_gemini.py` with real tests.

## 13. Milestones (one PR each, in this order)

The order is deliberate: a working end-to-end demo first, measurement before hardening, hardening before polish.

1. **Hygiene + checks:** section 2 results, `.gitignore`, move legacy ML scripts, remove DistilBERT files, new dependency set, tooling, CI config. *Done when:* clean install from lockfile, `pytest` and `ruff` pass.
2. **Skeleton + config + DB:** settings, app factory, logging, typed models, Alembic migration, health endpoints. *Done when:* `/ready` reflects real dependencies.
3. **Thin vertical slice (first demo):** minimal firewall (bounded read, Pillow decode and re-encode, pixel limits, UUID names), lazy Gemini extractor with structured output and usage logging, `POST /items`, `GET /items/{id}`, `GET /items`. No auth, no classifier, no rate limits yet. *Done when:* the demo in section 13a passes with the fake provider and with a real key.
4. **Classifier adapter:** `curated_ml` package, shared `build_text`, model card, retrain-to-card, startup load, abstain logic (legacy-8 placeholder).
5. **Cost layer:** pixel-hash cache, retries, budget guard, `media_resolution` and thinking settings, `/usage`, blocked-response handling.
6. **Eval harness + first benchmark report.** Use it to choose the model, `media_resolution` and whether the local classifier earns its place before building more around either.
7. **Full firewall matrix + storage + authorized image endpoint.**
8. **Jobs and API features:** 202 flow with background processing, stuck-job sweep, PATCH corrections, FTS search, reanalyze, delete.
9. **API firewall + privacy:** auth, rate limits, CORS, security headers, `skip_analysis`, retention behavior.
10. **Docs:** rewrite the README around the screenshot pipeline (diagram, run instructions in PowerShell, config table, cost notes, known limitations).

## 13a. Demo acceptance and targets

**Demo (after milestone 3):** start the server, then
`curl -F "file=@backend/test_image.jpg" http://localhost:8000/api/v1/items` returns 202 with an id; polling `GET /api/v1/items/{id}` reaches `ready` with a title, description and tags. The same flow must pass in CI against the fake provider.

**Starting targets** (hypotheses to confirm or revise with the milestone 6 benchmark, not facts): under ~1,000 input tokens and ~300 output tokens per item at medium resolution; estimated cost under $0.002 per item at current verified prices; p95 end-to-end under 8 seconds; re-saving an identical screenshot makes 0 API calls; every crafted-bad fixture is rejected by the firewall.

## 14. Rules for you, the agent

- Small PRs, one milestone each. Explain *why* in every PR description, not just what changed.
- Do not invent facts about Gemini model names, prices, or SDK parameters: verify against current official docs and say what you verified and when.
- Never commit secrets, databases, uploads, or model outputs containing user data.
- If something here is ambiguous or contradicts what you see in the code, stop and ask the owner rather than guessing; list open questions at the end of each PR.
- No new heavy dependencies without a one-line justification. No frontend work.
- The dev machine is Windows (PowerShell): use `pathlib`, avoid POSIX-only APIs, and give commands in PowerShell form in docs.
- Do not delete user data or rewrite git history without explicit approval.
