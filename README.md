# FormFinance — AI Finance Controller for Settlement Reconciliation

**Razorpay AI Buildathon 2026 — Track 04: AI Finance Controller**

FormFinance turns a raw settlement PDF into a defensible, auditable decision
(`APPROVED` / `FLAGGED` / `ESCALATED` / `FAILED`) with no human step in
between — real OCR, real deterministic verification, real evidence
matching, and a real AI agent for the cases that deterministic rules alone
can't resolve.

---

## 1. Problem

Finance teams reconciling payment-gateway settlements today do it largely
by hand: open the settlement PDF, open the fee schedule, open the evidence
documents, manually check whether every deduction matches something
documented, and decide whether to approve, dispute, or escalate. This is
slow, inconsistent between reviewers, and produces no reusable audit trail
of *why* a settlement was approved or flagged.

## 2. Solution

FormFinance automates that reconciliation loop end-to-end:

```
Settlement PDF
   → Upload (existing FormWise document infrastructure)
   → PaddleOCR
   → Settlement & deduction extraction
   → Deterministic verification against the settlement's own numbers
   → Evidence matching against supporting documents (OCR'd the same way)
   → AI finance agent investigates only the cases deterministic rules
     couldn't resolve
   → Final decision: APPROVED / FLAGGED / ESCALATED / FAILED
   → Immutable audit trail (FinanceAuditEvent records)
   → Batch metrics across a settlement run
   → Frontend: upload, live status, decision, evidence, audit trail
```

Every decision is explainable: it's backed by the deterministic checks that
ran, the evidence that was or wasn't found, and — where used — the AI
agent's own reasoning, all recorded as audit events rather than produced
and thrown away.

## 3. Razorpay Track 04 alignment

Track 04 (AI Finance Controller) asks for an agentic system that can take
over a finance-operations task that currently requires a human in the
loop and produce a decision a finance team can trust. FormFinance targets
**settlement reconciliation** specifically: it doesn't just extract text
from a PDF, it closes the loop — deterministic verification first (cheap,
explainable, no hallucination risk), and an AI agent second, invoked only
for the residual cases that genuinely need judgment. That ordering (rules
before AI, AI as an escalation path rather than the primary decision-maker)
is deliberate: it keeps the system's most common outcomes fully explainable
and reserves the AI agent's non-determinism for the minority of cases where
it earns its keep.

## 4. Architecture

```
apps/web/                   Next.js 15 frontend (App Router)
services/api/                FastAPI backend — documents, OCR jobs, settlements,
                              batch processing, audit, privacy
services/worker/              Background worker — polls the OCR job queue,
                              runs PaddleOCR, writes results back to Firestore
packages/document-core/       Shared document/privacy/rendering models
                              (Python + TS), reused from the FormWise base
infra/                        Deployment/infra notes
docker-compose.yml             api + web + worker (+ optional ollama for the AI agent)
```

The frontend never talks to OCR or the AI provider directly — everything
goes through the FastAPI backend, which owns Firestore, local document
storage, the OCR job queue, and the settlement pipeline.

## 5. End-to-end workflow

1. **Upload** — the frontend requests a signed upload target
   (`POST /documents/upload-intents`), PUTs the PDF bytes directly
   (`PUT /documents/{id}/upload`), then confirms completion
   (`POST /documents/{id}/complete`).
2. **OCR** — the frontend enqueues an OCR job (`POST /documents/{id}/ocr`)
   and polls status (`GET /documents/{id}/ocr`) while the **worker**
   process picks the job off the Firestore queue and runs it through
   **PaddleOCR** (`PPStructureV3`) — not a stub, not a placeholder.
3. **Settlement extraction** — once OCR text is available, the pipeline
   extracts settlement-level fields (gross/net amount, currency,
   settlement date) and itemized deductions from the OCR'd text.
4. **Deterministic verification** — each deduction is checked against the
   settlement's own stated totals (does gross − deductions = net? do the
   deduction line items reconcile?) with no AI involved at this stage.
5. **Evidence matching** — supporting documents (fee schedules, dispute
   letters, etc.) are OCR'd the same way and checked for whether they
   substantiate the deductions found in the settlement.
6. **AI fallback** — only for deductions the deterministic + evidence
   steps couldn't resolve, a finance investigation agent is invoked to
   reason over the remaining ambiguity. If no AI provider is configured
   (e.g. Ollama isn't running), this step degrades gracefully to
   "unresolved" rather than crashing or fabricating a resolution.
7. **Decision** — `APPROVED`, `FLAGGED`, `ESCALATED`, or `FAILED`, derived
   from the combination of the above, not from the AI agent alone.
8. **Audit trail** — every stage writes a `FinanceAuditEvent`, giving a
   replayable record of what happened and why.
9. **Frontend result** — the settlement processor screen renders the real
   API response: decision, deductions, evidence matches, and audit events.

## 6. AI / agent role

The AI agent (`SettlementFinanceAgent`) is deliberately **not** the primary
decision-maker. It is invoked only when deterministic verification and
evidence matching leave a deduction unresolved, and its output is one input
to the final decision rather than the decision itself. The AI provider is
pluggable (`services/api/src/formwise_api/ai_provider/`); the reference
configuration uses **Ollama** running locally (`docker-compose.yml`, under
the `ai` profile). If the provider is unreachable or unconfigured, the
pipeline logs an audit event and falls back to a deterministic-only
outcome — it never silently fabricates an AI opinion.

## 7. OCR

OCR is real **PaddleOCR** (`PPStructureV3`), run inside the `worker`
service (`services/worker/src/formwise_worker/ocr/paddle.py`), not a
mock or manual transcription. The worker polls a Firestore-backed job
queue (`services/worker/src/formwise_worker/queue.py`) — it is a
separate long-running process and must be running for OCR to complete;
`docker-compose.yml` starts it by default (no special profile required).

## 8. Verification / evidence matching

- **Deterministic verification** (`settlements/deterministic_verifier.py`,
  `settlements/verification_service.py`) checks the settlement's own
  arithmetic and deduction structure with no AI involved — fast,
  reproducible, and the first line of defense against bad decisions.
- **Evidence matching** (`settlements/evidence_matcher.py`) checks
  deductions against separately-uploaded, separately-OCR'd evidence
  documents (fee schedules, correspondence, etc.), so a "the fee
  schedule says X" claim isn't taken from the settlement PDF alone.

## 9. Batch processing and metrics

`BatchSettlementProcessor` runs the full pipeline (extraction →
verification → evidence → AI fallback → decision → audit) across a set of
settlements and aggregates a `BatchMetrics` report: totals processed,
approval/flag/escalation counts, deduction verification stats, evidence
match rate, extraction success rate, exception rate, and AI agent
investigation/success/failure counts. Two endpoints expose this:

- `GET /settlements/batch/demo-run` — runs the backend's built-in
  synthetic demo dataset end-to-end through the real pipeline.
- `POST /settlements/batch/process` — runs the same pipeline against
  settlement specs supplied in the request body.

The frontend's **Dashboard** and **Batch Results** pages call
`GET /settlements/batch/demo-run` live and render whatever the pipeline
actually produces — there are no hardcoded metric values in either page.

## 10. Demo authentication

The backend requires a Firebase ID token on every authenticated request
(`services/api/src/formwise_api/dependencies/authentication.py`) by
default. For demos and local development without a real Firebase
project, an explicit, narrowly-scoped bypass exists:

- Set `DEMO_AUTH_ENABLED=true` on the **backend** and
  `NEXT_PUBLIC_DEMO_AUTH_ENABLED=true` on the **frontend** (baked in at
  Next.js build time).
- In this mode the frontend sends an `X-Demo-User-ID` header instead of a
  Firebase bearer token; the backend accepts it **only** when
  `DEMO_AUTH_ENABLED=true` **and** no real bearer token is present — a
  real Firebase token always takes priority if one is sent.
- `DEMO_AUTH_ENABLED=true` is **structurally rejected** if
  `FORMWISE_ENV=production` (`Settings.validate_security_configuration`
  raises on startup), so this path cannot accidentally ship live.
- If real `NEXT_PUBLIC_FIREBASE_*` values are configured instead, the
  frontend uses genuine Firebase `signInWithPopup` / `onAuthStateChanged`
  and demo mode is not used.

Everything downstream of authentication (documents, OCR jobs, settlements,
audit events) is scoped by `identity.uid`, which works identically whether
that uid came from a real Firebase token or the demo header — it's used
purely as a Firestore partition key, never passed to `firebase_admin`
itself.

## 11. Setup

```bash
git clone <this repository>
cd FormFinance

# Create a .env at the repo root — none is committed, none should be.
cat >> .env << 'EOF'
DEMO_AUTH_ENABLED=true
NEXT_PUBLIC_DEMO_AUTH_ENABLED=true
EOF
```

If you have a real Firebase project instead, set
`FIREBASE_PROJECT_ID`/`FIREBASE_SERVICE_ACCOUNT_JSON` (backend) and
`NEXT_PUBLIC_FIREBASE_*` (frontend) instead of the two lines above.

## 12. Running locally

```bash
docker compose up --build
```

This starts `api` (FastAPI, port 8000), `web` (Next.js, port 3000), and
`worker` (PaddleOCR job processor) by default. Add
`--profile ai` to also start `ollama` for the AI finance agent step —
without it, the pipeline still runs and produces decisions, just without
the AI-fallback step for unresolved deductions.

Open `http://localhost:3000`, click **Login** or **Sign Up** (demo mode
authenticates immediately, no Google account needed), go to
**Settlements**, upload a settlement PDF, and watch it move through OCR,
extraction, verification, evidence matching, and decisioning. Check
**Dashboard** or **Batch Results** for a live run of the demo benchmark.

## 13. API endpoints (all under `/api/v1`, auth required unless noted)

| Method | Path | Purpose |
|---|---|---|
| POST | `/documents/upload-intents` | Request a signed upload target |
| PUT | `/documents/{id}/upload` | Upload the raw file bytes |
| POST | `/documents/{id}/complete` | Confirm upload completion |
| GET | `/documents` | List the caller's documents |
| POST | `/documents/{id}/ocr` | Enqueue an OCR job |
| GET | `/documents/{id}/ocr` | Poll OCR status/result |
| POST | `/settlements` | Create a settlement record |
| GET | `/settlements/{id}` | Get a settlement |
| GET | `/settlements` | List the caller's settlements |
| POST | `/settlements/{id}/extract` | Extract deductions from OCR text |
| POST | `/settlements/{id}/verify` | Run verification on a settlement |
| POST | `/settlements/process-document` | Full pipeline: OCR'd document → decision |
| GET | `/settlements/{id}/details` | Full settlement detail + audit events |
| POST | `/settlements/batch/process` | Run the pipeline over supplied specs |
| GET | `/settlements/batch/demo-run` | Run the pipeline over the built-in demo dataset |
| GET | `/me` | Current authenticated identity |
| GET | `/health` | Liveness (no auth) |
| GET | `/ready` | Readiness, checks dependencies (no auth) |

## 14. Limitations / current demo dataset size

- The built-in demo/benchmark dataset
  (`services/api/src/formwise_api/settlements/demo_data.py`) contains
  **10** synthetic settlements, not 50 — this is the accurate current
  size; treat any "50-record benchmark" reference elsewhere as aspirational
  rather than what ships today.
- `BatchMetricsResponse` reports the rates the batch processor computes
  (`evidence_match_rate`, `exception_rate`, `extraction_success_rate`,
  etc.) but does not itself re-derive or sanity-check them — they're only
  as good as `BatchMetrics`'s own bookkeeping.
- The AI agent step requires a running Ollama instance
  (`docker compose --profile ai up`); without it the pipeline still
  produces decisions, just without AI-assisted resolution of ambiguous
  deductions.
- Demo authentication (`DEMO_AUTH_ENABLED`) is explicitly a demo-only
  mechanism, gated off in production by config validation — it is not a
  general-purpose auth bypass.
- Real Firebase sign-in is wired against the SDK but has not been
  exercised against a live Firebase project during development of this
  fix; if you configure real Firebase credentials, test the sign-in flow
  before relying on it for a live demo.

## 15. Tech stack

- **Frontend:** Next.js 15 (App Router), React, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Pydantic v2, Firestore (via `firebase_admin`)
- **OCR:** PaddleOCR (`PPStructureV3`)
- **AI agent:** Ollama (pluggable provider interface)
- **Worker:** Python, polling a Firestore-backed job queue
- **Auth:** Firebase Authentication, with an explicit demo-mode bypass
- **Infra:** Docker Compose (api / web / worker / optional ollama)
