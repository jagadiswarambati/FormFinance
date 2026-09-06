# FormFinance — Requirements Specification Document

**Version:** 1.0  
**Date:** January 2025  
**Status:** Approved  

---

## 1. Executive Summary

FormFinance is an AI-powered settlement verification system that automates reconciliation of financial settlements. This document defines functional, non-functional, and technical requirements for the MVP (Minimum Viable Product) submission to Razorpay AI Buildathon 2026, Track 04.

---

## 2. Functional Requirements

### FR1: Document Upload & Storage

**FR1.1** System shall accept PDF settlement documents ≤10 MB  
**FR1.2** Uploaded documents shall be stored in FormWise document repository  
**FR1.3** Documents shall be associated with authenticated user (owner_uid)  
**FR1.4** OCR processing shall be triggered automatically upon upload completion  
**FR1.5** OCR text shall be stored separately and linked to document  

### FR2: OCR & Text Extraction

**FR2.1** System shall use PaddleOCR to extract text from PDF settlement documents  
**FR2.2** OCR text shall include structured extraction (amounts, dates, account numbers)  
**FR2.3** OCR confidence scores shall be tracked and returned to user  
**FR2.4** Failed OCR processing shall be retried with degraded settings  
**FR2.5** OCR processing shall timeout after 30 seconds  

### FR3: Settlement Extraction

**FR3.1** System shall parse settlement structure from OCR text:
- Settlement date
- Gross transaction amount
- Refunds and reversals
- Platform/merchant fees
- Taxes and statutory deductions
- Adjustments and chargebacks
- Net settlement amount

**FR3.2** Extracted settlement shall be validated against schema  
**FR3.3** Extraction confidence scores (0.0-1.0) shall be computed per field  
**FR3.4** Failed extractions shall be logged with reason and context  

### FR4: Deduction Detection & Classification

**FR4.1** System shall identify all deductions in settlement  
**FR4.2** Each deduction shall be classified by type:
- Platform/merchant fee
- Tax (GST, income tax, etc.)
- Chargeback or dispute reversal
- Adjustment or correction

**FR4.3** Each deduction shall include:
- Amount
- Description/reason
- Reference ID (if present)
- Reference date (if present)
- Extraction confidence

**FR4.4** Deductions with confidence <0.70 shall be marked for investigation  

### FR5: Deterministic Verification

**FR5.1** System shall apply rule-based verification to each deduction:

**Fee Verification:**
- Amount must be 0-5% of gross amount
- Must reference fee schedule or policy
- Confidence must be ≥0.75

**Tax Verification:**
- Must match known tax rate (5%, 12%, 18% for GST, or notified rate)
- Must reference tax regulation
- Confidence must be ≥0.80

**Chargeback Verification:**
- Must have supporting dispute evidence
- Amount must match original transaction
- Confidence must be ≥0.75

**Adjustment Verification:**
- Must have authorization/approval reference
- Must include reason for adjustment
- Confidence must be ≥0.70

**FR5.2** Verification result shall include status:
- `verified` (rule passed)
- `disputed` (rule failed but amount reasonable)
- `unverifiable` (insufficient evidence; route to agent)

**FR5.3** Verification shall be deterministic (same input → same output)  
**FR5.4** Verification logic shall be auditable (all checks logged)  

### FR6: Evidence Matching

**FR6.1** System shall link deductions to supporting evidence documents:
- Invoices
- Tax certificates
- Regulatory notices
- Dispute records

**FR6.2** Evidence matching shall compute confidence (0.0-1.0):
- Date proximity to deduction date
- Amount match
- Reference number match
- Document type relevance

**FR6.3** Matched evidence shall be included in results  
**FR6.4** Unmatched deductions shall be escalated to verification/agent  

### FR7: AI Finance Agent (Conditional)

**FR7.1** When a deduction is unverifiable deterministically, system shall invoke AI agent (if configured)  
**FR7.2** Agent shall receive:
- Deduction details (type, amount, date, reference)
- Settlement context (gross, net, other deductions)
- Verification failure reason
- Available evidence documents
- Policy/regulation context

**FR7.3** Agent shall reason through:
- Is the amount reasonable given settlement size?
- Does the deduction type match the context?
- Is there supporting evidence?
- Are there regulatory/policy reasons?

**FR7.4** Agent shall return decision:
- `verified` (agent investigation successful)
- `disputed` (agent found inconsistency)
- `unverifiable` (agent cannot resolve)
- Confidence score (0.0-1.0)
- Reasoning (for audit trail)

**FR7.5** If ANTHROPIC_API_KEY not configured, agent investigation shall be skipped; mark as `unverifiable`  

### FR8: Settlement Decision

**FR8.1** System shall synthesize verification results into decision:

**APPROVE:**
- All deductions verified AND evidence matched
- No disputed or unverifiable deductions
- Overall confidence ≥0.90

**FLAG:**
- Some deductions verified, some disputed
- Agent investigations resolved most cases
- Remaining disputed deductions <20% of total
- Requires manual review

**ESCALATE:**
- Unverifiable deductions present
- Agent investigation failed or skipped
- High exception rate or processing errors
- Requires manual review

**FR8.2** Decision shall include:
- Decision type (APPROVE / FLAG / ESCALATE)
- Reasoning
- Confidence score
- Recommendation for manual action (if FLAG or ESCALATE)

### FR9: Audit Trail

**FR9.1** Every action shall be logged:
- Extraction event (settlement parsed, deductions found)
- Verification event (rule applied, result)
- Evidence matching event (document linked, confidence)
- Agent investigation event (invoked, reasoning, result)
- Decision event (final decision, reason)

**FR9.2** Audit event shall include:
- Timestamp (UTC)
- Action type
- Resource (settlement/deduction/decision)
- Details (structured data)
- Outcome/result
- User/system that triggered action

**FR9.3** Audit trail shall be immutable (append-only)  
**FR9.4** Audit trail shall be queryable by settlement ID  

### FR10: Batch Processing

**FR10.1** System shall support batch processing of multiple settlements  
**FR10.2** Batch request shall include list of settlement specs:
- Source system
- Settlement date
- Gross/net amounts
- Currency
- OCR text (if pre-extracted)

**FR10.3** System shall process each settlement end-to-end  
**FR10.4** Batch shall return metrics:
- Total records
- Processed count
- Extraction success rate
- Verification rate (verified/disputed/unverifiable breakdown)
- Decision distribution (APPROVE/FLAG/ESCALATE counts)
- Agent investigation results
- Evidence match rate
- Processing time
- Throughput (records/second)

**FR10.5** Batch errors shall be caught and reported (not blocking entire batch)  

### FR11: Demo Mode

**FR11.1** System shall support demo authentication (no Firebase required)  
**FR11.2** Demo mode enabled via `DEMO_AUTH_ENABLED=true` (backend) and `NEXT_PUBLIC_DEMO_AUTH_ENABLED=true` (frontend)  
**FR11.3** In demo mode, request header `X-Demo-User-ID` shall be accepted as user identity  
**FR11.4** Demo mode shall provide full functionality (upload, processing, batch, results)  
**FR11.5** Demo mode shall be clearly labeled (UI and logs)  

### FR12: Frontend UI

**FR12.1** Landing page with project info and login/demo button  
**FR12.2** Settlement upload page:
- File picker
- Upload progress
- Extracted data preview

**FR12.3** Settlement processor page:
- List of uploaded settlements
- Process button per settlement
- Results display (deductions, verification, decision, audit trail)

**FR12.4** Batch demo page:
- "Run 50-Record Benchmark" button
- Real-time progress
- Results and metrics table

**FR12.5** History page:
- List of processed settlements
- Filters (date range, decision type)
- Export option

**FR12.6** Settings page:
- Auth status display
- Demo mode indicator

---

## 3. Non-Functional Requirements

### NFR1: Performance

**NFR1.1** Settlement extraction: <2 seconds per document  
**NFR1.2** Deterministic verification: <100ms per deduction  
**NFR1.3** Evidence matching: <500ms per settlement  
**NFR1.4** Agent investigation: <5 seconds per deduction (with LLM latency)  
**NFR1.5** End-to-end processing: <10 seconds per settlement  
**NFR1.6** Batch processing throughput: ≥10 settlements/second  

### NFR2: Scalability

**NFR2.1** System shall handle batch processing of 50+ settlements without degradation  
**NFR2.2** Storage shall support 10,000+ documents (MVP scope)  
**NFR2.3** API shall support concurrent requests (async processing)  

### NFR3: Reliability

**NFR3.1** OCR failures shall not block document ingestion (mark for manual review)  
**NFR3.2** Agent API failures shall not block verification (mark unresolvable)  
**NFR3.3** All errors shall be caught, logged, and reported to user  
**NFR3.4** System availability target: 99.5% (uptime) during MVP phase  

### NFR4: Security

**NFR4.1** All API endpoints shall require authentication  
**NFR4.2** Uploaded documents shall only be accessible by owner  
**NFR4.3** OCR text and extracted data shall follow same access control  
**NFR4.4** Demo mode credentials shall not be stored (session-only)  
**NFR4.5** All data in transit shall use HTTPS (production)  
**NFR4.6** Sensitive configuration (API keys) shall use environment variables  

### NFR5: Auditability

**NFR5.1** All financial decisions shall have complete audit trail  
**NFR5.2** Audit trail shall include reasoning for each decision  
**NFR5.3** Audit trail shall not be modifiable after creation  
**NFR5.4** Users shall be able to export audit trail as PDF/JSON  

### NFR6: Maintainability

**NFR6.1** Code shall follow Python PEP 8 (backend) and ESLint (frontend)  
**NFR6.2** All public functions/components shall have docstrings  
**NFR6.3** Commit messages shall follow conventional commit format  
**NFR6.4** Pull requests shall require code review before merge  

### NFR7: Testability

**NFR7.1** Unit test coverage: ≥75%  
**NFR7.2** Critical paths (extraction, verification, decision): 100% coverage  
**NFR7.3** Integration tests for API endpoints  
**NFR7.4** End-to-end tests for settlement processing pipeline  

### NFR8: Usability

**NFR8.1** UI shall be responsive (mobile, tablet, desktop)  
**NFR8.2** Error messages shall be clear and actionable  
**NFR8.3** Processing status shall be visible (progress indicators)  
**NFR8.4** Results shall be readable and exportable  

---

## 4. Technical Requirements

### TR1: Architecture

**TR1.1** Frontend: Next.js 15.5 with React 19, TypeScript  
**TR1.2** Backend: FastAPI (Python 3.13+)  
**TR1.3** OCR: PaddleOCR  
**TR1.4** AI: Anthropic Claude API (configurable)  
**TR1.5** Storage: Firestore (preferred) or local filesystem (demo)  
**TR1.6** Authentication: Firebase Auth (optional) or demo mode  
**TR1.7** Deployment: Docker Compose  

### TR2: API Design

**TR2.1** REST API only (no GraphQL)  
**TR2.2** API prefix: `/api/v1`  
**TR2.3** Response format: JSON with camelCase keys  
**TR2.4** Error responses: `{ "detail": "error message" }`  
**TR2.5** Pagination: `limit` and `offset` query parameters  

### TR3: Database Schema

**TR3.1** Collections/tables:
- documents (uploaded PDFs)
- settlements (parsed settlement records)
- settlement_deductions (extracted deductions)
- verification_results (deterministic check results)
- settlement_decisions (final decisions)
- evidence_links (deduction ↔ evidence mapping)
- audit_events (complete action log)

**TR3.2** All records shall include:
- Unique ID (UUID)
- Created timestamp (UTC)
- Owner UID (authenticated user)

### TR4: Dependencies

**Backend:**
- FastAPI, Uvicorn
- Pydantic, Pydantic Settings
- PaddleOCR, paddlepaddle
- firebase-admin
- anthropic (or openai)
- pytest, pytest-asyncio

**Frontend:**
- Next.js, React, TypeScript
- TailwindCSS
- React Hook Form
- Axios or Fetch

### TR5: Environment Configuration

**Backend:**
- FORMWISE_ENV (development|staging|production)
- DEMO_AUTH_ENABLED (true|false)
- FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT_*
- ANTHROPIC_API_KEY
- CORS_ALLOWED_ORIGINS
- LOG_LEVEL

**Frontend:**
- NEXT_PUBLIC_API_BASE_URL
- NEXT_PUBLIC_DEMO_AUTH_ENABLED
- NEXT_PUBLIC_FIREBASE_* (API key, auth domain, project ID, etc.)

---

## 5. Acceptance Criteria

| Requirement | Acceptance Criteria | Status |
|---|---|---|
| FR1: Document Upload | Accept PDF, store in repository, trigger OCR | ✅ |
| FR2: OCR | Extract text with confidence scores | ✅ |
| FR3: Settlement Extraction | Parse all 7 fields (gross, net, fees, taxes, etc.) | ✅ |
| FR4: Deduction Classification | Identify and classify all deduction types | ✅ |
| FR5: Deterministic Verification | Apply rules, produce VERIFY/DISPUTE/UNVERIFIABLE | ✅ |
| FR6: Evidence Matching | Link deductions to documents with confidence | ✅ |
| FR7: AI Finance Agent | Investigate unverifiable deductions, return decision | ✅ |
| FR8: Settlement Decision | Synthesize results into APPROVE/FLAG/ESCALATE | ✅ |
| FR9: Audit Trail | Log all actions with timestamps and outcomes | ✅ |
| FR10: Batch Processing | Process 50+ settlements with metrics | ✅ |
| FR11: Demo Mode | Work without Firebase/API keys | ✅ |
| FR12: Frontend UI | Upload, process, view results, run batch demo | ✅ |
| NFR1: Performance | <10 seconds per settlement, ≥10 settlements/sec | 🔄 |
| NFR4: Security | Auth required, data isolation, env secrets | ✅ |
| NFR5: Auditability | Complete trail with reasoning | ✅ |
| NFR7: Testability | 75%+ coverage | 🔄 |

---

## 6. Assumptions

1. Razorpay provides settlement document samples
2. PDF format is standard (text-based, not scanned images)
3. Settlement structure follows common fintech patterns
4. Anthropic API is available (optional for agent)
5. No real Razorpay API integration required (synthetic data acceptable)

---

## 7. Constraints

- **Timeline:** Complete by January 13, 2025
- **Data:** Only synthetic settlement records
- **Scale:** MVP tested with 50+ settlements
- **Deployment:** Docker Compose only (no Kubernetes)
- **Authentication:** Demo mode sufficient (no production auth)

---

## 8. Glossary

| Term | Definition |
|---|---|
| **Settlement** | Financial payment from payment platform to merchant |
| **Deduction** | Fee, tax, chargeback, or adjustment subtracted from gross |
| **Verification** | Rule-based check on deduction validity |
| **Evidence** | Supporting document (invoice, tax cert, policy) |
| **Agent Investigation** | LLM-based reasoning for ambiguous deductions |
| **Decision** | Final outcome (APPROVE / FLAG / ESCALATE) |
| **Audit Trail** | Complete log of all actions and reasoning |

---

## 9. Sign-Off

| Role | Approval | Date |
|---|---|---|
| Product Manager | _________________ | _________ |
| Tech Lead | _________________ | _________ |
| QA Lead | _________________ | _________ |

---

**Status:** Approved  
**Version:** 1.0  
**Last Updated:** January 6, 2025
