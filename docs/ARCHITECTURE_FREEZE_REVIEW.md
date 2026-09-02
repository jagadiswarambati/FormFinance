# FormWise AI — Final Architecture Review and Freeze

**Date:** 2026-07-21  
**Decision:** **APPROVED WITH MINOR CHANGES**  
**Scope:** Version 1 architecture only; no application code is authorised by this document.

## Executive conclusion

The architecture is sound for a privacy-first closed beta. It has the right core decisions: a modular monolith, asynchronous document processing, policy-enforced data handling, direct private uploads, a provider-neutral AI boundary, and rendering that preserves source documents rather than recreating them.

It should not be expanded before implementation. The changes below are corrective, not feature additions. Once incorporated, this is the frozen V1 architecture. Future changes require an ADR and do not reopen the V1 design by default.

## Required corrections before implementation

### 1. Correct the privacy claim around OCR

A scanned or pre-filled form can contain sensitive information. OCR must inspect document content before field labels can be classified. Therefore, FormWise must never claim that sensitive content is not processed by OCR. The correct promise is:

- Uploaded documents are processed only in FormWise-controlled document workers.
- Sensitive **answer values are never sent to the LLM, asked in chat, persisted as answers, or inserted into the output by FormWise.**
- The LLM receives only policy-approved, sanitized text/schema after document analysis.
- Documents that appear already populated with sensitive values are quarantined from LLM use; processing continues only through the restricted document pipeline or ends in manual-only guidance.

The Privacy Dashboard must separately show **Document/OCR processing** and **LLM processing**. It must not use “AI processed” as an imprecise umbrella statement.

### 2. Make V1 retention deterministic

“Five conversations” means five retained conversations per user. On creating a sixth completed or active conversation, the oldest retained conversation is immediately access-revoked and queued for cascading purge. A scheduled worker retries the purge until source files, OCR artifacts, answers, outputs, and indexes are gone. Backup expiry must be disclosed separately.

Keep an explicit `retentionStatus` and purge audit event; do not depend on Firestore client-side deletion or a best-effort browser call.

### 3. Rename and merge document-intelligence concerns

Do not create a separate, vague “Form Knowledge Engine” in V1. It risks becoming an undefined RAG/product-knowledge subsystem. Freeze a single **Form Understanding Pipeline** containing:

1. PDF native-widget/text extraction;
2. OCR/layout analysis only when needed;
3. field/section candidate mapping;
4. confidence scoring; and
5. handoff to the Privacy Engine for classification.

It may use the AI Provider only with sanitized material. A future knowledge base for common forms is a distinct Version 2 proposal, not an implied part of this pipeline.

### 4. Keep the provider abstraction; defer cloud-provider implementations

The `AIProvider` interface is justified because it isolates a security-critical boundary. In V1, implement and enable only `OllamaProvider`. Gemini and Groq remain configuration entries and contract fixtures, not working SDK integrations. This meets provider independence without creating credentials, data-flow, test, operational, or compliance overhead for unused services.

There is no automatic provider fallback. Selecting a cloud provider is a future security and product decision, not an environment-variable-only operational change; configuration merely selects an already approved provider.

### 5. Make review exceptional, not a required step for every field

After upload, show a simple processing state, then begin the guided flow automatically. Interrupt only for low-confidence fields, unsupported documents, or user-requested corrections. Show a compact “Review detected fields” affordance rather than a mandatory form-builder screen. Sensitive/restricted fields appear in the preview as manual-only from the start.

## Architecture assessment

| Question                             | Review finding                                                                                                       | Frozen decision                                                                                                                                  |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Is the overall architecture correct? | Yes for a closed beta; modular monolith and workers are proportionate.                                               | Keep it.                                                                                                                                         |
| Can workflow be simpler?             | Mandatory review would cause friction.                                                                               | Auto-start safe conversation; exception-based review only.                                                                                       |
| Is there unnecessary complexity?     | Microservices, RAG, provider SDKs, and a separate knowledge engine are premature.                                    | Exclude them from V1.                                                                                                                            |
| 50 users                             | Architecture is comfortably sufficient.                                                                              | One API deployment, worker, durable queue, private storage.                                                                                      |
| 500 users                            | Still sufficient with worker replicas, queue limits, and monitoring.                                                 | Scale workers horizontally; retain modular monolith.                                                                                             |
| 5,000 users                          | Compute and document workload—not API routes—become the bottleneck.                                                  | GPU/OCR worker pools, queue partitioning, load tests, evaluate Firestore access/cost.                                                            |
| 50,000 users                         | Provider, storage, operations, and audit/query needs require a platform review.                                      | Split workers/services only from measured bottlenecks; move transactional/audit workloads to Postgres if Firestore query/cost limits justify it. |
| Missing modules                      | Quota/retention orchestration and explicit malware/quarantine status need first-class ownership.                     | Add as responsibilities within Document Lifecycle, not new product features.                                                                     |
| Unnecessary modules                  | “Form Knowledge Engine” is ambiguous.                                                                                | Merge into Form Understanding Pipeline.                                                                                                          |
| Clear separation                     | Good after merge: documents understand; policy permits; conversation sequences; provider generates; renderer writes. | Enforce import/dependency boundaries.                                                                                                            |
| OCR pipeline                         | Native PDF extraction first, then layout-aware OCR is correct.                                                       | Keep; sandbox and quarantine inputs.                                                                                                             |
| Guided Assistant                     | A model should never choose a sensitive question or advancement rule.                                                | Deterministic state machine selects field; model only phrases approved question/explanation.                                                     |
| PDF rendering                        | Correct for fillable/static PDFs; fidelity cannot be guaranteed for every scan.                                      | Render preview, coordinate tolerance tests, manual-only/unsupported outcome when alignment is unsafe.                                            |
| Firebase V1                          | Firebase Auth, Firestore metadata, and Firebase Storage are appropriate at 50–500 users.                             | Keep for V1; server-side access only.                                                                                                            |
| Firestore later                      | It is not automatically a problem.                                                                                   | Reassess at 5,000 users or earlier if transactional quotas, audit analytics, query patterns, or cost become limiting.                            |
| Firebase Storage                     | Sufficient for V1 private originals/outputs.                                                                         | Private bucket, short-lived signed URLs, scanning/quarantine, lifecycle deletion.                                                                |
| API/repository maintainability       | Good if contracts and domain boundaries remain enforced.                                                             | Keep API versioning and domain-first repository structure.                                                                                       |

## Frozen V1 responsibility boundaries

| Module                      | Owns                                                                             | Must not own                                 |
| --------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------- |
| Document Lifecycle          | upload intent, validation, scan/quarantine, storage, jobs, retention/purge       | privacy classification, chat, model calls    |
| Form Understanding Pipeline | extraction, OCR, layout, field candidates/confidence                             | soliciting values, privacy permissions       |
| Privacy Engine              | classification, policy decisions, redaction, outbound data gate, audit decisions | OCR, conversation wording, file rendering    |
| Guided Assistant Engine     | state machine, approved safe-field order, user-facing flow                       | classification decisions, provider SDK calls |
| AI Provider                 | model request/response translation and health                                    | field selection, policy exemptions, storage  |
| Validation Engine           | value type/format validation for policy-approved fields                          | classification escalation bypass             |
| PDF Rendering               | approved-field placement and manual markers                                      | accepting or generating protected values     |
| Privacy Dashboard           | read-only explanation/projection of policy/audit outcomes                        | client-side policy computation               |

## Customer journey freeze

1. Sign in with Google; see a short, factual privacy promise and supported-format limits.
2. Upload a form. Show progress and explain that FormWise detects fields before asking questions.
3. If supported and confident, enter a conversational safe-field flow immediately. If not, give one clear action: review a few fields or download a manual-completion original.
4. Surface a persistent “Privacy details” control, not a separate onboarding tour. It shows what the document worker and LLM did separately.
5. Show the rendered preview with safe fields complete and protected fields visibly manual-only. Permit correction of safe fields before download.
6. Download through a short-lived link; clearly state the five-conversation limit and deletion control.

Avoid dashboard clutter, a required field-mapping editor, LLM disclaimers on every message, or generic “magic AI” claims. Explain limitations only where they affect the user’s next decision.

## Privacy review outcomes

| Stage                 | Primary risk                                          | Frozen control                                                                                                            |
| --------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Login                 | unnecessary identity/profile collection               | Google sign-in only; retain minimum Firebase identity data.                                                               |
| Upload                | malicious/pre-filled sensitive documents, URL leakage | private direct upload, real-type checks, scan/quarantine, short expiry, worker sandbox.                                   |
| OCR                   | document content includes sensitive values            | no third-party OCR in V1; controlled workers; OCR artifacts encrypted and short-lived; no LLM handoff before policy gate. |
| Field detection       | false-negative classification                         | fail closed on ambiguity; locale aliases/patterns; review fixtures and release gate.                                      |
| Conversation          | user enters protected data voluntarily                | input scanning/redaction before logs/storage; do not echo; explain manual completion.                                     |
| Provider/model        | prompt injection or unwanted cloud transfer           | uploaded text treated as data; structured outputs; tools off; Ollama only; no automatic fallback.                         |
| Rendering             | protected data inserted or leaked in preview          | renderer accepts only policy-approved field/value pairs; manual markers only otherwise.                                   |
| Storage/history       | stale files or derived content remain                 | five-conversation cascade purge, storage lifecycle, access revoke first, purge audit.                                     |
| Settings/dashboard    | accidental exposure in summaries                      | no answer values/raw OCR/pattern details; server-built, owner-authorized projections.                                     |
| Logging/observability | PII in errors/traces/session replay                   | central redaction, log allowlist, Sentry scrubber, replay disabled on sensitive pages.                                    |

## Three-month, one-developer plan

Build only the vertical slice necessary for a safe closed beta:

1. Google auth, private upload, document limits, quarantine, native-PDF-first extraction, then OCR fallback.
2. Deterministic field map/classification with English first; UI strings and safe explanations in Hindi/Telugu only after the privacy test corpus covers each language.
3. Guided safe-field chat, preview/render, deletion/quota, and Privacy Dashboard.
4. Test fixtures, audit trail, security checks, and closed-beta operations.

Defer portal integrations, reusable profile data, teams, mobile/offline mode, general knowledge/RAG, rich analytics, cloud-provider adapters, handwriting guarantees, and broad “any form” marketing. These exclusions increase the chance of a safe and useful first release.

## Freeze conditions

The architecture is frozen with the five corrections above. Before any production launch—not before local implementation—confirm the target processing region, public privacy notice wording, document retention/backup period, and supported document limits. These are operational and legal launch settings, not reasons to redesign the software architecture.

No further architectural redesign is required for V1. Implementation may now proceed against this SDD and freeze review.
