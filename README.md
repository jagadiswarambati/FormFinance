Update the existing README.md of the FormFinance repository to a professional, production-quality README suitable for the Razorpay AI Buildathon 2026 submission.

IMPORTANT:
- First inspect the existing README.md and repository structure.
- Do NOT invent features that do not exist in the code.
- Preserve technically accurate details from the existing implementation.
- The README should describe the CURRENT working project, not future plans.
- Do not rewrite application code.
- Only modify README.md unless a tiny documentation-related correction is absolutely necessary.
- Make the README polished enough that a hackathon judge, engineer, or recruiter can understand the project in 2–3 minutes.

==================================================
PROJECT
==================================================

Name:
FormFinance

Position it as:

AI Finance Controller for automated settlement verification, reconciliation, evidence matching, exception investigation, and auditable financial decisions.

Built for:
Razorpay AI Buildathon 2026
Track 04 — AI Finance Controller

==================================================
CORE PROBLEM
==================================================

Explain the real finance-operations problem:

Settlement reports contain payments, refunds, platform fees, taxes, adjustments, and net settlement amounts.

Traditional reconciliation requires finance teams to:
- extract information from settlement documents
- verify amounts and deductions
- match deductions against evidence
- investigate discrepancies
- decide whether a settlement can be approved
- escalate unresolved cases
- maintain an audit trail

At scale, this becomes repetitive, slow, and difficult to audit.

FormFinance addresses this by turning settlement reconciliation into an automated finance-control workflow.

==================================================
SOLUTION
==================================================

Clearly explain the end-to-end workflow:

Settlement PDF/document
→ FormWise document upload
→ OCR/PaddleOCR
→ structured settlement extraction
→ deterministic verification
→ deduction verification
→ evidence matching
→ AI/agent investigation for unresolved cases
→ APPROVE / FLAG / ESCALATE
→ audit trail
→ batch metrics

Emphasize:

OCR is only the extraction layer.

The actual product value is the finance-control loop that uses extracted information, verification, evidence, investigation, and decision-making.

==================================================
KEY CAPABILITIES
==================================================

Document Processing
- Settlement document upload
- Existing FormWise document infrastructure
- OCR/PaddleOCR processing

Settlement Intelligence
- Settlement metadata extraction
- Gross amount
- Refunds
- Platform fees
- Taxes
- Adjustments
- Net settlement

Verification
- Settlement verification
- Deduction verification
- Evidence matching
- Verified / disputed / unverifiable outcomes

AI Finance Controller
- Investigates unresolved cases
- Uses available evidence/context
- Produces a finance decision
- Supports APPROVE / FLAG / ESCALATE outcomes

Auditability
- Records processing and decision events
- Makes the decision flow traceable

Batch Processing
- Synthetic 50-record benchmark/demo
- Settlement outcome metrics
- Extraction metrics
- Deduction verification metrics
- Evidence match rate
- Exception rate
- Agent investigation metrics

==================================================
ARCHITECTURE
==================================================

Include a clean Mermaid architecture diagram.

Use a diagram similar to:

flowchart TD
    A[Settlement PDF / Document] --> B[FormWise Document Upload]
    B --> C[OCR / PaddleOCR]
    C --> D[Settlement Extraction]
    D --> E[Verification Engine]
    E --> F[Evidence Matching]
    F --> G[Finance Agent Investigation]
    G --> H{Decision}
    H -->|Verified| I[APPROVE]
    H -->|Exception| J[FLAG]
    H -->|Unresolved| K[ESCALATE]
    I --> L[Audit Trail]
    J --> L
    K --> L
    L --> M[Batch Metrics / Finance Dashboard]

Only include components that actually correspond to the current implementation.

==================================================
TECHNICAL ARCHITECTURE
==================================================

Inspect package files and source code and document the actual stack.

Where supported by the repository, describe:

Frontend:
- Next.js
- React
- TypeScript

Backend:
- Python
- FastAPI

OCR:
- PaddleOCR / existing FormWise OCR pipeline

Infrastructure:
- Docker
- Docker Compose

Authentication:
- Firebase authentication support
- Demo authentication mode

Do NOT claim technologies that are not actually present.

==================================================
API
==================================================

Document the important existing endpoints.

At minimum inspect and document the actual implementation of:

POST /api/v1/settlements/process-document

GET /api/v1/settlements/batch/demo-run

Also document the settlement/document endpoints that actually exist in the code.

For each important endpoint give:
- purpose
- HTTP method
- short description

Do not invent request/response fields. Inspect the actual schemas before documenting them.

==================================================
DEMO WORKFLOW
==================================================

Add a "Demo Flow" section explaining exactly how someone can demonstrate the project:

1. Start the application.
2. Open the FormFinance frontend.
3. Authenticate using supported demo mode if configured.
4. Open settlement processing.
5. Select/upload a settlement document.
6. Run processing.
7. Show extracted settlement data.
8. Show verification.
9. Show evidence matching.
10. Show agent investigation when applicable.
11. Show final APPROVE / FLAG / ESCALATE decision.
12. Show audit events.
13. Run/show the 50-record benchmark.

Only describe steps that work in the current application.

==================================================
SYNTHETIC DEMO DATA
==================================================

Document that the project uses synthetic/demo financial data.

Include an example settlement:

Settlement ID:
setl_TEST_20260905_001

Merchant:
Demo Commerce Pvt Ltd

Settlement Date:
05-Sep-2026

UTR:
FORMTESTUTR260905001

Gross Payment Credits:
225,000.00

Refund:
10,000.00

Platform Fees:
6,525.00

Tax on Fees:
1,174.50

Adjustment:
500.00

Net Settlement:
207,800.50

3 payments
1 refund
1 adjustment

Clearly state:

"This is synthetic test data created for demonstration and does not represent a real Razorpay settlement."

==================================================
BATCH BENCHMARK
==================================================

Explain the 50-record synthetic benchmark.

Document the actual metrics exposed by the implementation, including where applicable:

- total settlements
- extraction success
- approved
- flagged
- escalated
- failed
- verified deductions
- disputed deductions
- unverifiable deductions
- settlement approval rate
- deduction verification rate
- evidence match rate
- exception rate
- extraction success rate
- agent investigations
- agent investigation successes/failures

IMPORTANT:
Do not put fake percentages or fake benchmark results in the README.

If actual benchmark numbers are available in the repository, document them accurately.
Otherwise describe the metrics without inventing values.

==================================================
PROJECT STRUCTURE
==================================================

Inspect the repository and create a concise project structure section.

Something like:

apps/
  web/
services/
  api/
  worker/
...

But only include directories that actually exist.

Briefly explain the responsibility of important directories.

==================================================
LOCAL DEVELOPMENT
==================================================

Create accurate setup instructions based on the repository.

Include:

Prerequisites
- Node.js version if defined
- Python version if defined
- Docker Desktop if required
- any other actual dependency

Installation

Environment configuration

Demo authentication configuration

Running locally

Running with Docker Compose

Building the frontend

Running backend tests

Running the benchmark

Do NOT invent commands.

Inspect:
- package.json
- workspace configuration
- Dockerfiles
- docker-compose.yml
- pyproject.toml / requirements files
- existing documentation
before writing commands.

==================================================
ENVIRONMENT VARIABLES
==================================================

Create a clean environment variable section.

Inspect .env.example and actual code.

Document only safe variable names and descriptions.

NEVER put:
- API keys
- Firebase secrets
- credentials
- tokens
- private keys
- actual .env contents

Explain that `.env` should not be committed.

==================================================
SECURITY / DEMO MODE
==================================================

Explain that the repository supports demo authentication for local/demo use.

Make it clear that demo authentication is intended for demonstration/development and is not equivalent to production authentication.

Do not expose secrets.

==================================================
DESIGN PRINCIPLES
==================================================

Add a concise section explaining the important design principles:

1. Evidence-backed decisions
2. Deterministic verification before agent reasoning
3. Human-readable exceptions
4. Auditable decisions
5. Batch-level measurement
6. Reuse of FormWise document/OCR infrastructure
7. Production authentication path remains separate from demo mode

Only claim these where supported by the code.

==================================================
WHY THIS FITS AI FINANCE CONTROLLER
==================================================

Add a strong section explaining why FormFinance fits Track 04.

Focus on:

- finance workflow automation
- settlement reconciliation
- exception detection
- evidence-based verification
- agent investigation
- operational decisions
- measurable batch performance
- auditability

Avoid generic statements like "AI makes finance better."

Make the connection to the finance-operations loop explicit:

DETECT
→ VERIFY
→ INVESTIGATE
→ DECIDE
→ RECORD

==================================================
LIMITATIONS / DEMO SCOPE
==================================================

Add an honest section.

State that:
- demo settlement data is synthetic
- this is a buildathon prototype
- benchmark data is synthetic
- production deployment would require production-grade data integrations, authentication, authorization, observability, and operational controls where applicable

Do not undersell the project, but do not claim production readiness that isn't implemented.

==================================================
ROADMAP
==================================================

Only include a small "Future Enhancements" section.

Do NOT make it look like missing core functionality.

Possible future work should be clearly labeled as future and should not be presented as already implemented.

==================================================
SCREENSHOTS
==================================================

If the repository already contains screenshots/assets, inspect them and reference them appropriately.

If there are no screenshots, do not invent image paths.

Leave a clean placeholder section only if useful.

==================================================
README STYLE
==================================================

Use professional GitHub README formatting.

Recommended structure:

# FormFinance

Short one-line description.

Badges only if they can be verified.

> Problem statement

## Overview

## Why FormFinance

## How It Works

## Architecture

## Key Capabilities

## AI Finance Controller

## Verification & Evidence

## Decisions

## Auditability

## 50-Record Benchmark

## API

## Tech Stack

## Project Structure

## Getting Started

## Environment Configuration

## Demo Workflow

## Synthetic Demo Data

## Design Principles

## Track 04 Alignment

## Limitations & Demo Scope

## Future Enhancements

## License

Only include License if an actual license exists in the repository. Do not invent one.

==================================================
QUALITY BAR
==================================================

The final README should feel like:

- serious engineering project
- finance/fintech product
- AI-agent system
- hackathon submission
- understandable by judges
- understandable by developers
- technically honest

Avoid:
- excessive emojis
- marketing fluff
- fake metrics
- fake integrations
- unsupported claims
- giant walls of text
- vague "AI-powered" statements
- saying something is implemented when it is only planned

Use diagrams, tables, concise bullets, and code blocks where useful.

Before finishing:
1. Inspect the repository.
2. Rewrite README.md.
3. Check every technical claim against the actual code/configuration.
4. Make sure commands are valid.
5. Make sure no secrets are included.
6. Show me the final README.md content or a concise summary of what you changed.
7. Do not modify application functionality.