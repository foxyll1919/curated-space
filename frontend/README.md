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

`backend/.env` needs a `GEMINI_API_KEY` to analyze screenshots. See the
repository `readme.md`.

**2. Frontend**:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The app is at http://localhost:5173 and proxies `/api` to
http://localhost:8000. Open it and create your account on the sign-in page; the
first account registers the library's owner and adopts any screenshots that were
saved before accounts existed.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `BACKEND_URL` | no | Where the backend listens. Defaults to `http://localhost:8000`. |

There is no credential in `frontend/.env` any more. Authentication is a session
cookie the backend sets, and the browser sends it by itself.

## How sign-in works

The sign-in page posts an email and password to `/api/v1/auth/login`. The backend
answers with an `httpOnly`, `SameSite=Lax` cookie and nothing else; the token is
never in a response body, so no script in this bundle can read it.

From then on the app asks `GET /api/v1/auth/me` once and keeps the answer in
TanStack Query. `RequireAccount` in `src/App.tsx` renders nothing while that
request is in flight, redirects to `/login` when it comes back 401, and returns
the reader to the page they wanted afterwards.

When any request anywhere in the app comes back 401, `src/lib/api.ts` fires a
window event that the auth provider listens for. That is how an expired or
revoked session lands back on the sign-in page instead of an empty grid.

Accounts:

- The **first** account may always be created, so a fresh install is usable.
- Later accounts need `AUTH_ALLOW_REGISTRATION=true` in `backend/.env`, or the
  `bootstrap-user` CLI. The sign-in page hides the switch when it is closed.
- Passwords are PBKDF2-HMAC-SHA256 hashed in the backend with a per-account
  salt. Nothing hashes on this side.
- `Sign out everywhere` in the account menu revokes every session, which is the
  one you want on a shared machine.

`vite.config.ts` still proxies `/api`, but it adds no headers:

```ts
const proxy = {
  '/api': { target, changeOrigin: true },
}
```

That is deliberate. When the proxy injected an `X-API-Key`, every request would
answer as the same configured owner and per-account ownership checks would never
be exercised. `npm run preview` uses the same proxy.

### The production equivalent

A production deployment needs the same same-origin guarantee from a real reverse
proxy rather than from Vite:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    client_max_body_size 8m;
}
```

Serve `dist/` as static files and route unknown paths to `index.html`, because
the router uses real paths (`/login`, `/usage`, `/item/{id}`). Serve the app over
HTTPS and set `AUTH_COOKIE_SECURE=true` in `backend/.env`, or the session cookie
will travel in plaintext.

`backend/.env`'s `API_KEY` still works for scripts and `curl`:

```powershell
curl.exe -H "X-API-Key: $env:API_KEY" http://localhost:8000/api/v1/items
```

That key maps to one owner id, which is not an account: `/api/v1/auth/me` has no
answer for it. Use the sign-in page for the UI.

## Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Dev server with the same-origin `/api` proxy. |
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
    api.ts          typed client; the only module that calls fetch for items
    api-types.ts    generated from openapi.json, do not edit
    auth.ts         account calls; the session cookie is the credential
    auth-context.ts the auth context object and useAuth, no components
    errors.ts       ApiError and the error-envelope parser
    failures.ts     error_code to human copy
    ratio.ts        screenshot aspect ratio for the masonry
  hooks/
    useAuth.tsx     the AuthProvider: session state and sign-in mutations
    useItems.ts     list, detail, polling, patch, delete
    useUpload.ts    validation and the client-side upload queue
    useDebounce.ts
  components/
    ui/             shadcn/ui, copied in by the CLI
    AccountMenu.tsx the signed-in account, sign out, sign out everywhere
    *               feature components
  pages/
    LibraryPage.tsx ItemPage.tsx UsagePage.tsx LoginPage.tsx NotFoundPage.tsx
```

## Notes on behaviour

**Sign in.** One page for both signing in and creating the first account. It
shows "create account" until `GET /auth/status` reports that an account exists,
and hides the switch when registration is closed. Passwords are never stored,
compared or confirmed on this side: the confirmation field only catches a typo
before a request is made. Failed attempts get one message, because the backend
does not reveal whether an address exists.

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