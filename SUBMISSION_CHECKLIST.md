# FormFinance — Submission Checklist

Honest status as of packaging. Items marked **UNVERIFIED (network-blocked)**
mean the sandbox that prepared this submission has no outbound network
access, so the command was never actually run — you must run it yourself
before trusting it.

## Build

- [ ] `cd services/api && uv sync --dev` — **UNVERIFIED (network-blocked)**,
      `uv sync` fails with `403 Forbidden` fetching the Python interpreter
      in this sandbox.
- [ ] `cd apps/web && npm install && npm run build` — **UNVERIFIED
      (network-blocked)**, `npm install` fails with `403 Forbidden`
      against `registry.npmjs.org` in this sandbox.
- [x] `python3 -m py_compile` across every `.py` file in the repo —
      **PASSED**, 300+ files, 0 syntax errors. This proves the Python
      parses; it does not prove imports resolve or logic is correct.
- [x] Manual brace/paren-balance and cross-reference check on every edited
      `.ts`/`.tsx` file — **PASSED** by hand. Not a substitute for `tsc`.

## Tests

- [ ] `cd services/api && uv run pytest -q` — **UNVERIFIED
      (network-blocked)**. Includes two new test files added during this
      fix: `test_demo_authentication.py` (demo-auth header behavior) and
      `test_batch_metrics_response.py` (batch metrics field completeness).
- [ ] `cd services/worker && uv run pytest -q` — **UNVERIFIED
      (network-blocked)**.
- [ ] `cd apps/web && npm run test` — **UNVERIFIED (network-blocked)**.
      Note: no `*.test.*` files exist under `apps/web` yet, so this will
      report zero tests found rather than failing, once it can run.

## Environment

- [x] No `.env` file is committed in this repo (confirmed by direct
      search — none present).
- [ ] You must create `.env` at the repo root with either
      `DEMO_AUTH_ENABLED=true` + `NEXT_PUBLIC_DEMO_AUTH_ENABLED=true`, or
      a full set of `FIREBASE_*` / `NEXT_PUBLIC_FIREBASE_*` values, before
      running the demo. See `VERIFICATION.md` for the exact list.
- [x] `DEMO_AUTH_ENABLED=true` is structurally rejected if
      `FORMWISE_ENV=production` — verified by reading
      `Settings.validate_security_configuration` in
      `services/api/src/formwise_api/config.py`; not runtime-tested.

## Docker

- [x] `docker-compose.yml` starts `api`, `web`, and `worker` by default
      (verified by reading the compose file — `worker` has no `profiles`
      key, so it is not gated).
- [x] `ollama` (AI agent) is behind `profiles: [ai]` — use
      `docker compose --profile ai up` to include it.
- [ ] `docker compose up --build` actually succeeding — **UNVERIFIED
      (network-blocked)**; Docker itself is not available in this
      packaging sandbox either.

## End-to-end demo

- [x] Full call chain traced by reading code: upload → OCR enqueue → OCR
      poll → settlement processing → verification → evidence → AI
      fallback (if configured) → decision → audit → frontend render.
      Every request/response schema pairing was checked field-by-field
      between frontend and backend.
- [ ] Actually clicking through the flow in a browser — **NOT DONE**, no
      browser or running server available in this sandbox. Follow
      `VERIFICATION.md` section 6 to do this yourself.

## Frontend/backend connection

- [x] `firebaseUser` is no longer permanently `null` — real Firebase mode
      and demo mode both populate it (`apps/web/src/contexts/auth-context.tsx`).
- [x] Every API service module (`upload-api.ts`, `settlement-api.ts`,
      `auth-api.ts`, `assignment-api.ts`, `conversation-api.ts`,
      `batch-api.ts`) sends the correct header for the active auth mode
      via the shared `buildAuthHeaders()` helper.
- [x] Backend accepts the demo header only when `DEMO_AUTH_ENABLED=true`
      and only when no real bearer token is present
      (`services/api/src/formwise_api/dependencies/authentication.py`).
- [x] CORS allows the `X-Demo-User-ID` header
      (`services/api/src/formwise_api/config.py` →
      `cors_allowed_headers`, consumed by `CORSMiddleware` in `main.py`).

## Batch metrics

- [x] Dashboard (`apps/web/src/app/app/page.tsx`) and Batch Results
      (`apps/web/src/app/app/history/page.tsx`) call
      `GET /settlements/batch/demo-run` on load — no hardcoded metric
      values remain in either file (verified by grep for stray numeric
      literals in both files).
- [x] `BatchMetricsResponse` (`services/api/src/formwise_api/settlements/router.py`)
      now includes all fields `BatchMetrics.to_dict()` computes:
      `evidence_match_rate`, `exception_rate`, `extraction_success_rate`,
      `total_records`, `processed`, `successfully_extracted` — previously
      silently dropped by Pydantic's default `extra="ignore"` behavior.
- [ ] Running `docker compose up` and clicking through Dashboard/Batch
      Results to see real numbers render — **NOT DONE**, same
      no-browser/no-Docker limitation as above.

## No secrets committed

- [x] Searched the entire repo for `.env`, `.env.*`, `firebase-admin.json`,
      `serviceAccountKey.json`, `secrets/` — **none found**.
- [x] `.gitignore` already excludes all of the above plus `.venv/`,
      `__pycache__/`, `node_modules/`, `.next/`, `dist/`, `build/`,
      `/storage/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`.
- [x] `FormFinance-Submission.zip` was built with explicit `-x` excludes
      matching every pattern above, plus generated `__pycache__`/
      `*.egg-info` directories found in the working tree; verified after
      zipping that zero matching paths are present in the archive.

## Git status

- [ ] **No `.git` directory exists in this repository as extracted** —
      confirmed by direct check. Git history could not be preserved in
      `FormFinance-Submission.zip` because there is none to preserve. If
      you have the original git history elsewhere (e.g. your own clone or
      GitHub repo), use that as your submission source and treat this zip
      as a content snapshot only, not a replacement for your git history.
