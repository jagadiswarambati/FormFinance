FormFinance

AI Finance Controller for Settlement Verification & Reconciliation

FormFinance is an AI-assisted finance operations system built for the Razorpay AI Buildathon — Track 04: AI Finance Controller.

It extends the existing FormWise document-processing infrastructure into a finance-controller workflow that automates settlement verification, deduction analysis, evidence matching, exception investigation, final decisioning, and auditability.

Core Workflow

Settlement PDF
      ↓
FormWise Document Upload
      ↓
PaddleOCR
      ↓
OCR Storage
      ↓
Settlement Extraction
      ↓
Deduction Analysis
      ↓
Deterministic Verification
      ↓
Evidence Matching
      ↓
Finance Investigation
      ↓
Final Decision
      ↓
Audit Trail + Metrics

The objective is to close a finance-operations loop instead of simply extracting information from documents.

What FormFinance Does

FormFinance processes settlement documents and determines whether each settlement should be:

APPROVED — settlement passes the configured verification checks

FLAGGED — an exception has been detected and requires review

ESCALATED — the case requires deeper investigation

FAILED — required information could not be extracted or processed

Every decision is intended to remain explainable through the underlying verification results, evidence checks, reasons, and audit events.

Key Features

1. Real PDF → OCR Pipeline

FormFinance reuses the existing FormWise document infrastructure instead of creating a separate document-processing system.

PDF
 ↓
FormWise Upload
 ↓
PaddleOCR
 ↓
OCR Result Storage
 ↓
Settlement Processing

The settlement-processing pipeline reads the actual stored OCR result.

It does not generate placeholder OCR text when OCR is unavailable.

2. Settlement Extraction

The settlement extraction layer converts OCR text into structured settlement data.

It can process:

Settlement ID

Settlement/reference number

Settlement date

Gross amount

Deductions

Deduction type

Deduction amount

Deduction reason

Net payout

Currency

Extraction confidence

3. Deterministic Financial Verification

Financial verification is performed through deterministic rules so that calculations and core financial checks remain predictable and reproducible.

Checks include:

Arithmetic validation

Gross amount validation

Deduction validation

Net payout validation

Required-field validation

Confidence checks

Reference validation

Deduction-type validation

Settlement consistency checks

4. Evidence Matching

Settlement deductions can be checked against supporting OCR documents.

Evidence matching evaluates:

Amount

Date

Reference / transaction ID

Results distinguish between:

Evidence found and matched

Evidence found but mismatched

Evidence not found

Evidence with missing required fields

5. Finance Investigation

Unresolved cases can be investigated using finance-specific verification and evidence tools.

The finance investigation layer can perform operations such as:

Comparing amounts

Verifying references

Checking deduction types

Searching available evidence

The implementation should be described accurately as AI-assisted / agentic finance investigation backed by deterministic finance tools, rather than claiming autonomous behavior beyond what is actually implemented.

6. Final Decision

Verification and investigation results feed into a final settlement decision.

Possible outcomes:

APPROVED
FLAGGED
ESCALATED
FAILED

The UI exposes the decision together with:

Confidence

Reasons

Verification results

Evidence results

Processing status

Audit events

7. Audit Trail

Important finance operations generate audit events for later review, including processing, extraction, verification, evidence evaluation, investigation, decision, and failure events.

50-Record Batch Benchmark

FormFinance includes a deterministic synthetic benchmark representing a batch of 50 settlement records.

Result

Records

Approved

20

Flagged

12

Escalated

13

Extraction Failed

5

Total

50

The benchmark contains positive cases, exceptions, escalations, and extraction failures.

It is designed to demonstrate finance-controller throughput and exception handling.

Benchmark Metrics

The batch-processing layer tracks:

Total records

Processed records

Extraction success

Approved records

Flagged records

Escalated records

Failed records

Evidence checks

Evidence match rate

Exception rate

Metrics should be derived from processing results rather than hard-coded in the frontend.

Synthetic Settlement Documents

Deterministic synthetic PDF fixtures are included for testing the settlement workflow.

Location:

services/api/tests/fixtures/settlements/

Scenarios include:

Valid settlement

Matching evidence

Evidence mismatch

Missing evidence

Deduction mismatch

Escalation scenarios

Multiple deductions

These documents are for development, testing, and demonstration only. No real customer financial data is required.

Architecture

                         ┌──────────────────────┐
                         │   Settlement PDF      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ FormWise Upload      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ PaddleOCR            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ OCR Result Storage   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Settlement Extraction│
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Deduction + Financial Checks │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Evidence Matching    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Finance Investigation│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Final Decision       │
                         │ APPROVED / FLAGGED   │
                         │ ESCALATED / FAILED   │
                         └──────────┬───────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
                ┌──────────────┐          ┌──────────────┐
                │ Audit Trail  │          │ Metrics/UI   │
                └──────────────┘          └──────────────┘

Repository Structure

FormFinance/
│
├── apps/
│   └── web/
│       └── src/
│           ├── app/
│           │   └── app/
│           │       └── settlements/
│           ├── components/
│           │   └── SettlementProcessor.jsx
│           └── services/
│               ├── documents/
│               └── settlements/
│
├── services/
│   ├── api/
│   │   ├── src/
│   │   │   └── formwise_api/
│   │   │       ├── settlements/
│   │   │       │   ├── models.py
│   │   │       │   ├── repository.py
│   │   │       │   ├── service.py
│   │   │       │   ├── extraction_service.py
│   │   │       │   ├── document_extractor.py
│   │   │       │   ├── deterministic_verifier.py
│   │   │       │   ├── verification_service.py
│   │   │       │   ├── evidence_matcher.py
│   │   │       │   ├── finance_agent.py
│   │   │       │   ├── batch_processor.py
│   │   │       │   ├── demo_data.py
│   │   │       │   ├── processing.py
│   │   │       │   └── router.py
│   │   │       ├── verification/
│   │   │       ├── evidence/
│   │   │       ├── audit/
│   │   │       └── ai_provider/
│   │   ├── tests/
│   │   │   ├── fixtures/
│   │   │   │   └── settlements/
│   │   │   └── settlement tests
│   │   └── storage/
│   │
│   └── worker/
│       └── src/
│           └── formwise_worker/
│               └── OCR infrastructure
│
└── packages/
    └── document-core/

Frontend

FormFinance extends the existing FormWise UI.

The intended user flow is:

Upload Settlement PDF
        ↓
Document Processing
        ↓
OCR Processing
        ↓
Settlement Extraction
        ↓
Verification
        ↓
Evidence Matching
        ↓
Finance Investigation
        ↓
Final Decision
        ↓
Finance Controller Dashboard

The frontend displays:

Settlement ID

Reference

Gross amount

Total deductions

Net amount

Verification result

Evidence result

Final decision

Confidence

Reasons

Processing status

Audit events

Individual deductions

Evidence details include:

Evidence found / not found

Amount match

Date match

Reference match

Overall evidence result

API

The settlement controller exposes endpoints including:

POST /v1/settlements
GET  /v1/settlements
GET  /v1/settlements/{id}
POST /v1/settlements/{id}/extract
POST /v1/settlements/{id}/verify

Document upload and OCR continue to use the existing FormWise infrastructure.

Firestore Data Model

Finance-specific collections include:

settlements
settlementDeductions
verificationResults
settlementDecisions
evidenceLinks
financeAuditEvents

The exact schema is defined by the corresponding models and repository implementations.

Testing

The project includes tests covering:

Settlement models and foundation

Settlement extraction

Deterministic verification

Evidence matching

Finance investigation

Document processing

OCR-backed processing

PDF fixtures

Batch processing

Synthetic benchmark data

Run the API tests:

cd services/api
uv run pytest -q

Focused settlement tests:

uv run pytest tests/test_settlements_foundation.py -v

PDF fixture tests:

uv run pytest tests/test_settlement_pdf_fixtures.py -v

Real PaddleOCR Test

The heavyweight model-backed PaddleOCR test is optional.

Enable it with:

FORMWISE_RUN_REAL_PADDLEOCR=1

Then run the relevant OCR/PDF test suite.

The normal test suite remains lightweight while the production architecture continues to use the existing PaddleOCR infrastructure.

Quick Start

1. Clone

git clone https://github.com/jagadiswarambati/FormFinance.git
cd FormFinance

2. Install Existing Dependencies

Use the existing FormWise setup and package-management workflow.

FormFinance is designed to reuse the existing FormWise stack rather than introduce a separate application stack.

3. Start FormWise Services

Start the API, worker, frontend, and required infrastructure according to the existing FormWise project instructions.

4. Open the Settlement Controller

Navigate to the settlement/finance-controller section of the FormWise frontend.

5. Upload a Synthetic Settlement PDF

Use a fixture from:

services/api/tests/fixtures/settlements/

Expected flow:

Upload
→ OCR
→ Process
→ Extract
→ Verify
→ Evidence
→ Decision

Demo Scenarios

Scenario 1 — Approved Settlement

Use a settlement with valid financial values and matching evidence.

Settlement
    ↓
OCR
    ↓
Extraction
    ↓
Verification PASS
    ↓
Evidence MATCH
    ↓
APPROVED

Show:

Gross amount

Deductions

Net amount

Evidence match

Final decision

Audit trail

Scenario 2 — Exception Settlement

Use a settlement containing an evidence or financial mismatch.

Settlement
    ↓
OCR
    ↓
Extraction
    ↓
Verification / Evidence Exception
    ↓
Investigation
    ↓
FLAGGED or ESCALATED

Show:

Mismatched field

Verification result

Evidence result

Investigation reason

Final decision

Audit event

This demonstrates that the controller does not simply approve every document.

Design Principles

Reuse Existing Infrastructure

FormFinance extends FormWise rather than building a separate OCR/document platform.

Deterministic Financial Controls

Financial calculations and core verification rules remain deterministic and reproducible.

Evidence-Based Decisions

Supporting evidence is checked whenever it is available.

Explainable Exceptions

Finance users should be able to understand why a settlement was flagged or escalated.

Failure Transparency

If OCR, extraction, evidence matching, or verification cannot complete, the system exposes the failure instead of fabricating a successful result.

Separation of Concerns

Document processing, extraction, verification, evidence matching, investigation, persistence, and UI responsibilities are separated into focused components.

Buildathon Alignment

Razorpay AI Buildathon — Track 04: AI Finance Controller

FormFinance targets a finance-operations workflow centered on settlement verification and reconciliation.

The core loop is:

Settlement
    ↓
Verification
    ↓
Exception Detection
    ↓
Evidence Investigation
    ↓
Finance Decision
    ↓
Audit

The 50-record synthetic benchmark provides measurable batch processing with successful cases and exceptions.

The system demonstrates:

Automated finance processing

Deterministic financial controls

Evidence-based exception handling

AI-assisted finance investigation

Explainable decisions

Auditability

Batch-level metrics

Current Implementation Status

The project contains the major backend and frontend building blocks for the settlement-controller workflow.

Implemented areas include:

Settlement models

Settlement persistence

Settlement extraction

Deduction extraction

Deterministic verification

Evidence matching

OCR-backed document processing

Finance investigation logic

Audit events

Batch processing

50-record synthetic benchmark

Synthetic settlement PDFs

OCR-backed evidence fixtures

Settlement API

Settlement frontend integration

Settlement controller interface

Processing metrics

Before submission, run the complete relevant test suite and perform the real browser-based demo flow.

Limitations

FormFinance is a buildathon prototype, not a production financial reconciliation platform.

Important limitations:

Synthetic data is used for benchmark and demo scenarios.

OCR quality depends on the underlying document and OCR pipeline.

Evidence matching depends on available evidence documents and extracted fields.

AI investigation is backed by explicit finance tools and deterministic logic; claims of fully autonomous LLM behavior should only be made if a live LLM/tool-calling path is actually enabled.

Production deployment would require additional security, monitoring, permissions, scalability, reliability, and financial-system integrations.

Data and Security

Do not commit:

.env
credentials
service-account files
runtime storage
customer financial documents
generated secrets

Synthetic fixtures belong under:

services/api/tests/fixtures/settlements/

Runtime storage should remain ignored by Git.

Development Commands

Run API tests:

cd services/api
uv run pytest -q

Validate Git whitespace:

git diff --check

Run the dedicated 50-record benchmark using the benchmark test included in the settlement test suite.

Project Goal

The goal of FormFinance is not merely to extract settlement information.

The goal is to build a finance controller that can:

READ
  ↓
UNDERSTAND
  ↓
VERIFY
  ↓
COMPARE WITH EVIDENCE
  ↓
INVESTIGATE EXCEPTIONS
  ↓
DECIDE
  ↓
EXPLAIN
  ↓
AUDIT

This turns document processing into an actionable finance-operations workflow.

Summary

FormFinance = FormWise + AI-assisted Finance Control

It combines:

Existing FormWise document infrastructure

PaddleOCR

Settlement extraction

Deduction analysis

Deterministic financial verification

Evidence matching

Finance investigation

Final decisioning

Audit trails

Batch processing

50-record synthetic benchmarking

Finance-controller UI

Central workflow:

PDF
→ OCR
→ Settlement
→ Deductions
→ Verification
→ Evidence
→ Investigation
→ Decision
→ Audit
→ Metrics

Repository

GitHub: https://github.com/jagadiswarambati/FormFinance

Project: FormFinance
Buildathon: Razorpay AI Buildathon 2026
Track: Track 04 — AI Finance Controller

Final Demo Checklist

Before submission:

Frontend starts successfully

Backend starts successfully

Worker/OCR service starts successfully

Settlement PDF uploads successfully

Real OCR processing completes

Stored OCR is consumed by settlement processing

Settlement fields are extracted

Deductions are persisted

Verification runs successfully

Evidence matching works

Approved case produces APPROVED

Exception case produces FLAGGED/ESCALATED

Reasons are visible

Audit events are visible

Batch benchmark runs

50-record metrics are available

No runtime storage is committed

No secrets are committed

git diff --check passes

Relevant tests pass

FormFinance

From settlement document to finance decision.