# Curated Space frontend

The screenshot library UI. React + Vite + TypeScript, Tailwind v4, shadcn/ui on
Radix, TanStack Query for server state, React Router for routing.

It talks to the backend at `backend/` in this repository. Nothing here modifies
the backend.

## Run it

Two processes. Start the backend first, because the frontend proxies to it and
reads its readiness report.

**1. Backend** (from the repository root):

```powershell
cd backend
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000
```

`backend/.env` needs a `GEMINI_API_KEY` to analyze screenshots and an `API_KEY`
to serve them. See the repository `readme.md`.

**2. Frontend**:

```powershell
cd frontend
npm install
Copy-Item .env.example .env   # then paste your API_KEY in
npm run dev
```

The app is at http://localhost:5173 and proxies `/api` to
http://localhost:8000.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `API_KEY` | yes | Shared key sent as `X-API-Key`. Must match `API_KEY` in `backend/.env`. |
| `BACKEND_URL` | no | Where the backend listens. Defaults to `http://localhost:8000`. |

Both live in `frontend/.env`, which is git-ignored. Copy `.env.example` to get
started.

**`API_KEY` must not be named `VITE_*`.** Vite exposes `VITE_`-prefixed
variables to client code through `import.meta.env`, which would put the key in
the JavaScript bundle. The proxy reads it with `loadEnv` instead, on the Node
side only, so it never reaches the browser.

## How the key proxy works

`vite.config.ts` registers a dev-server proxy for `/api`:

```ts
const env = loadEnv(mode, process.cwd(), '')
const apiKey = env.API_KEY ?? ''

const proxy = {
  '/api': {
    target: env.BACKEND_URL ?? 'http://localhost:8000',
    changeOrigin: true,
    configure(proxyServer) {
      proxyServer.on('proxyReq', (proxyReq) => {
        if (apiKey) proxyReq.setHeader('X-API-Key', apiKey)
      })
    },
  },
}
```

The browser only ever makes same-origin requests to `/api/v1/...`. The dev
server adds the header on the way out. Two consequences worth knowing:

- The key is not in the bundle, the browser network tab, or local storage.
- `<img src="/api/v1/items/{id}/image">` works with no extra work, because the
  image request goes through the same proxy and picks up the same header.

`npm run preview` uses the same proxy, so a production build can be checked
locally with the key in place.

### The production equivalent

A production deployment needs the same guarantee from a real reverse proxy
rather than from Vite. Anything that can add a request header on the way to the
backend works; nginx, for example:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-API-Key "<the same API_KEY>";
    proxy_set_header Host $host;
    client_max_body_size 8m;
}
```

Serve `dist/` as static files and route unknown paths to `index.html`, because
the router uses real paths (`/usage`, `/item/{id}`).

Note that the header has to be set by the proxy rather than forwarded from the
browser, and the key must not be readable by anyone who can load the app. This
is a single-user personal library behind one shared key, which is what the
backend's `X-API-Key` model assumes.

## Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Dev server with the key-injecting proxy. |
| `npm run build` | Type-check and build to `dist/`. |
| `npm run typecheck` | `tsc --noEmit`. |
| `npm run lint` | oxlint. |
| `npm run check` | All three. |
| `npm run preview` | Serve the build, still through the proxy. |
| `npm run api-types` | Regenerate `src/lib/api-types.ts` from the running backend's `openapi.json`. |

## Generated types

`src/lib/api-types.ts` is produced by `openapi-typescript` from the backend's
own OpenAPI document. Regenerate it whenever the API changes:

```powershell
npm run api-types
```

The backend must be running for that to work. Two things the generated contract
does not cover, both handled in `src/lib/api.ts`:

- The error envelope (`{ "error": { "code", "message", "request_id" } }`) is not
  declared in the OpenAPI document. It is typed in `src/lib/errors.ts` by hand,
  and `X-Request-Id` from the response headers is used as a fallback.
- `status`, `tags` and `labels` are not marked required, so `normalizeItem`
  fills them in once, in the API layer. Components never defend against a
  missing array.

## Project layout

```
src/
  lib/
    api.ts          typed client; the only module that calls fetch
    api-types.ts    generated from openapi.json, do not edit
    errors.ts       ApiError and the error-envelope parser
    failures.ts     error_code to human copy
    ratio.ts        screenshot aspect ratio for the masonry
  hooks/
    useItems.ts     list, detail, polling, patch, delete
    useUpload.ts    validation and the client-side upload queue
    useDebounce.ts
  components/
    ui/             shadcn/ui, copied in by the CLI
    *               feature components
  pages/
    LibraryPage.tsx ItemPage.tsx UsagePage.tsx NotFoundPage.tsx
```

## Notes on behaviour

**Upload.** Images only, 8 MB max, checked in the browser before anything is
sent. Files upload two at a time; the backend allows 10 per minute, so a burst
becomes an orderly queue instead of a wall of 429s. A 429 waits out the server's
fixed window and tries again rather than failing the upload.

**"Don't analyze".** Sends `skip_analysis=true`. The image is stored on your own
machine and sent to no AI provider; the item lands as `deferred` and can be
analyzed later from its detail view. The configured provider project is on a
Free tier where submitted content may be reviewed, so the toggle is on the main
page with an explanation rather than hidden in a menu.

**Polling.** A newly accepted upload appears in the grid immediately in a
pending state and polls `GET /items/{id}` from 800ms up to a 4s cap. After a
minute it stops and offers a refresh rather than spinning forever. Polling is
cancelled on unmount.

**Scores.** `classifier_score` is a classifier margin, not a probability. It is
never displayed, and never as a percentage or a confidence. Legacy category
labels are shown as plain chips, and no taxonomy is hardcoded anywhere in the
client: the label filter is built from whatever the API returns.

**Search.** Bound to `q`, debounced 300ms, and mirrored into the URL query
string, so a search can be shared or survived by a reload. Terms are AND-matched
by the backend.

**Thumbnails.** Cards render at the screenshot's own proportions, computed from
the `image.width` and `image.height` the API returns, and the image is
letterboxed inside. Nothing is cropped or stretched, so text in a screenshot is
always readable.