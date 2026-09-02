# Development Setup

Prerequisites: Node.js 24, npm 11, Python 3.13, and Docker Desktop (optional).

1. Copy `.env.example` to `.env` and fill only the values needed for the environment.
2. Run `npm install`, then `npm run lint`, `npm run typecheck`, and `npm run build`.
3. Install [uv](https://docs.astral.sh/uv/) and run `uv sync` from the repository root. The root uv workspace installs the API, worker, and shared `formwise-document-core` package together. Start the API with `cd services/api` then `uv run uvicorn formwise_api.main:app --app-dir src --reload`; start the worker with `cd services/worker` then `uv run python -m formwise_worker.main`.
4. For containers: run `docker compose --profile ai up --build`. Docker Compose supplies the container-only Ollama address automatically; direct API/worker runs use `OLLAMA_BASE_URL=http://localhost:11434`.

The API routes in this milestone are `GET /api/v1/health` and authenticated `GET /api/v1/me`.

## Frontend Firebase Configuration

1. In Firebase Console, open your project and go to **Project settings → General → Your apps**. Create a Web App if one does not already exist.
2. Copy the values from its Firebase Web SDK configuration object into `apps/web/.env.local`, replacing only the `YOUR_FIREBASE_*` placeholders:
   - `apiKey` → `NEXT_PUBLIC_FIREBASE_API_KEY`
   - `authDomain` → `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
   - `projectId` → `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
   - `messagingSenderId` → `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
   - `appId` → `NEXT_PUBLIC_FIREBASE_APP_ID`
3. Firebase Storage does not need to be enabled. `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` is optional Firebase Web SDK metadata and is not used by FormWise AI local development.
4. Stop and restart `npm run dev` after changing `.env.local`, because Next.js reads `NEXT_PUBLIC_*` values at startup/build time.
5. Set `NEXT_PUBLIC_API_BASE_URL` to the FastAPI versioned base URL (for local development, `http://localhost:8000/api/v1`). After Firebase signs in, the auth context sends its Firebase SDK ID token to `GET /me` and uses the verified backend profile as its authenticated state.

## Backend Firebase setup

1. Create separate Firebase projects for development, staging, and production.
2. Enable **Authentication → Sign-in method → Google** and configure the OAuth consent screen.
3. Add the local and deployed web origins under **Authentication → Settings → Authorized domains**.
4. Create a Web App and copy its public configuration into the `NEXT_PUBLIC_FIREBASE_*` variables.
5. Create a service account for the API with Firebase Authentication token verification and Firestore access. Store its JSON only in `FIREBASE_SERVICE_ACCOUNT_JSON` through local secrets or the deployment secret manager.
6. Create a Firestore database in Native mode. The application creates `users/{uid}` only after a verified first login.

Never place the service-account JSON in a `NEXT_PUBLIC_*` variable or commit it to the repository.

## Local Filesystem Storage

Local development selects the existing `LocalStorageAdapter` directly through API dependency wiring. Firebase Storage is not initialized or called. Keep the following shared paths for the API and worker, relative to the repository root when running processes directly:

- `storage/uploads`
- `storage/quarantine`
- `storage/ocr`
- `storage/privacy`
- `storage/renders`

Uploads are written to quarantine first. The worker releases clean files to uploads and writes OCR artifacts locally; the API writes protected privacy artifacts locally. Rendering, download streaming, and retention use the same local paths. Docker Compose mounts named local volumes at the corresponding container paths for both API and worker.
