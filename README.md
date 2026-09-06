# FormFinance — AI Finance Controller

**Automated settlement verification, deduction reconciliation, evidence matching, and auditable financial decisions powered by deterministic verification and AI-driven investigation.**

**Razorpay AI Buildathon 2026 — Track 04: AI Finance Controller**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [30-Second Pitch](#30-second-pitch)
5. [Technical Pitch](#technical-pitch)
6. [End-to-End Flow](#end-to-end-flow)
7. [System Architecture](#system-architecture)
8. [Finance Agent Architecture](#finance-agent-architecture)
9. [Settlement Processing Pipeline](#settlement-processing-pipeline)
10. [Core Finance Logic](#core-finance-logic)
11. [Batch Processing & Benchmark](#batch-processing--benchmark)
12. [Razorpay Buildathon Alignment](#razorpay-buildathon-alignment)
13. [API Documentation](#api-documentation)
14. [Frontend](#frontend)
15. [Technology Stack](#technology-stack)
16. [Repository Structure](#repository-structure)
17. [Requirements](#requirements)
18. [Installation & Setup](#installation--setup)
19. [Environment Variables](#environment-variables)
20. [Demo Mode](#demo-mode)
21. [Complete Judge Demo](#complete-judge-demo)
22. [Sample Data](#sample-data)
23. [Testing](#testing)
24. [Build & Verification](#build--verification)
25. [Troubleshooting](#troubleshooting)
26. [Security & Privacy](#security--privacy)
27. [Limitations](#limitations)
28. [Roadmap](#roadmap)
29. [Quick Start](#quick-start)

---

## Project Overview

**FormFinance** is an AI-powered finance controller that automates the reconciliation and verification of financial settlements. It processes settlement documents (PDFs), extracts financial data via OCR, performs deterministic verification checks, matches deductions against evidence, investigates ambiguous cases with an AI finance agent, and produces auditable decisions.

### Who It's For

- **Finance Operations Teams** processing high-volume settlements manually
- **Fintech & Payment Platforms** reconciling settlement reports at scale
- **Compliance & Audit Functions** requiring traceable financial decisions
- **Finance Automation Teams** building deterministic + agentic workflows

### Why It Matters

Manual settlement reconciliation is:
- **Slow**: Hours per document; unscalable at volume
- **Error-prone**: Human oversight, missed discrepancies
- **Unauditable**: No trace of reasoning or verification logic
- **Repetitive**: Same checks applied document-after-document

FormFinance solves this by turning reconciliation into a transparent, repeatable, auditable workflow that combines fast deterministic checks with targeted AI investigation for ambiguous cases.

---

## The Problem

### Settlement Verification Challenges

A settlement report contains:
- Gross transaction amount
- Refunds and reversals
- Platform/merchant fees
- Taxes and statutory deductions
- Adjustments and chargebacks
- **Net settlement amount** (what should actually be paid)

**Why this is hard to reconcile:**
1. **Structural extraction**: OCR alone doesn't understand settlement semantics—amounts must be parsed from context
2. **Deduction verification**: Each deduction type (fee, tax, chargeback) has different rules for validity
3. **Evidence matching**: Deductions must be matched against supporting evidence (invoice, policy, regulation)
4. **Exception handling**: Some deductions are ambiguous and require investigation
5. **Audit trail**: Finance requires proof of what was checked and why a decision was made
6. **Scale**: A single payment platform processes thousands of settlements daily

**Current state (manual):**
```
Finance team → PDF settlement → Manual reading → Spreadsheet extraction
→ Manual verification (rule-by-rule) → Email back-and-forth on disputes
→ Spreadsheet-based audit → Weeks to close
```

**Cost of failure:**
- Undetected fraud or errors: Millions in exposure
- Processing delays: Settlement cycles disrupted
- Audit gaps: Regulatory non-compliance
- Scaling ceiling: Cannot grow without proportional hiring

---

## The Solution

FormFinance delivers an **end-to-end settlement verification pipeline**:

```
Settlement PDF
  ↓
[OCR Extraction]          (PaddleOCR → text extraction)
  ↓
[Structured Parsing]      (Settlement extractor → amounts, dates, types)
  ↓
[Deduction Detection]     (Extract fees, taxes, adjustments, chargebacks)
  ↓
[Deterministic Checks]    (Business rules → verified/disputed/unverifiable)
  ↓
[Evidence Matching]       (Link deductions to supporting documents)
  ↓
[Unresolved → AI Investigation] (Finance agent → research ambiguous cases)
  ↓
[Decision]                (APPROVE / FLAG / ESCALATE)
  ↓
[Audit Trail]             (Every check, result, and reasoning logged)
  ↓
[Batch Results & Metrics] (50+ records → throughput, accuracy, exceptions)
```

### Key Capabilities

| Capability | Description |
|---|---|
| **Document Ingestion** | Settlement PDFs uploaded to FormWise storage |
| **OCR Processing** | PaddleOCR extracts text, page layout, structured data |
| **Settlement Extraction** | Parsed gross, refunds, fees, taxes, net amounts |
| **Deterministic Verification** | Rule-based checks on deduction types, amounts, dates |
| **Deduction Verification** | Each deduction categorized: verified / disputed / unverifiable |
| **Evidence Matching** | Deductions linked to supporting documents with confidence scoring |
| **AI Finance Agent** | LLM-based agent investigates unresolved deductions |
| **Decision Generation** | APPROVE (all checks pass), FLAG (discrepancies), ESCALATE (manual review needed) |
| **Audit Trail** | Complete record of checks, results, agent reasoning, and final decision |
| **Batch Processing** | 50+ settlements processed end-to-end with metrics |
| **Metrics & Reporting** | Extraction success, verification rate, evidence match rate, exception tracking |

---

## 30-Second Pitch

> FormFinance automates settlement reconciliation for payment platforms. Upload a settlement PDF → OCR extracts amounts → AI verifies deductions against rules and evidence → Finance decision (approve/flag/escalate) generated with full audit trail. Process 50+ settlements in seconds with measurable accuracy.

---

## Technical Pitch

FormFinance is a settlement verification pipeline that combines **deterministic rule-based verification** with **targeted AI investigation** for ambiguous cases. 

The architecture:
1. **Document Layer**: Uploads and storage via FormWise
2. **OCR Layer**: PaddleOCR extracts settlement structure and amounts
3. **Extraction Layer**: Parses settlement semantics (deductions, types, amounts, dates)
4. **Verification Layer**: Deterministic checks on business rules (fee validity, tax compliance, amount consistency)
5. **Evidence Layer**: Links deductions to supporting documents; computes match confidence
6. **Agent Layer**: LLM-powered finance agent investigates failures in deterministic checks
7. **Decision Layer**: Synthesis of verification results and agent investigation → APPROVE/FLAG/ESCALATE
8. **Audit Layer**: Complete provenance of checks, reasoning, and outcomes
9. **Batch Layer**: Processes 50+ settlements; produces metrics (extraction rate, verification rate, throughput)

**Why agentic?**
- Deterministic checks are fast and rule-based but have limits (ambiguous amounts, missing evidence)
- When deterministic checks fail, the agent receives context (deduction type, amount, evidence) and investigates
- Agent uses reasoning (not lookup) to decide whether ambiguity can be resolved
- Agent results feed into final decision
- The combination: most decisions deterministic (fast) + complex cases AI-driven (thorough)

**Why it fits Track 04 (AI Finance Controller):**
- Automates a repetitive finance workflow (settlement reconciliation)
- Uses AI to handle exceptions and ambiguity
- Produces auditable, verifiable decisions
- Scales (50+ records with metrics)
- Measurable accuracy and throughput

---

## End-to-End Flow

```mermaid
graph TD
    A["Settlement PDF Upload"] --> B["FormWise Storage"]
    B --> C["OCR Processing<br/>PaddleOCR"]
    C --> D["Settlement Structure<br/>Extraction"]
    D --> E["Deduction Detection<br/>Fees, Taxes, Adjustments"]
    E --> F["Deterministic<br/>Verification Checks"]
    F --> G{Verification Result}
    G -->|Verified| H["Evidence Matching"]
    G -->|Disputed| H
    G -->|Unverifiable| I["Route to<br/>AI Finance Agent"]
    H --> J{Evidence Match?}
    J -->|Strong Match| K["Increase Confidence"]
    J -->|Weak/No Match| I
    I --> L["Agent Investigation<br/>Research Context"]
    L --> M["Agent Decision<br/>Verified/Disputed/Unverifiable"]
    K --> N["Synthesis"]
    M --> N
    N --> O["Finance Decision"]
    O --> P{Decision Type}
    P -->|All Verified| Q["APPROVE"]
    P -->|Some Disputed| R["FLAG"]
    P -->|Escalation Needed| S["ESCALATE"]
    Q --> T["Audit Trail"]
    R --> T
    S --> T
    T --> U["Results + Metrics"]
```

---

## System Architecture

### High-Level Architecture

```mermaid
graph LR
    subgraph Frontend["Frontend (Next.js)"]
        UI["Settlement UI<br/>Upload/Results"]
        Auth["Auth Context<br/>Demo Mode"]
    end
    
    subgraph Backend["Backend (FastAPI)"]
        API["API Router<br/>/settlements/*"]
        DocRepo["Document<br/>Repository"]
        SettleRepo["Settlement<br/>Repository"]
        Verif["Verification<br/>Service"]
        Agent["Finance Agent<br/>AI Provider"]
        Pipeline["Processing<br/>Pipeline"]
    end
    
    subgraph Services["Services"]
        OCR["OCR Worker<br/>PaddleOCR"]
        Extractor["Settlement<br/>Extractor"]
        Verifier["Deterministic<br/>Verifier"]
        Matcher["Evidence<br/>Matcher"]
    end
    
    subgraph Storage["Storage"]
        Docs["Documents"]
        Settlements["Settlements"]
        Audits["Audit Trail"]
        Verification["Verification Results"]
    end
    
    subgraph External["External"]
        AIProvider["AI Provider<br/>LLM"]
    end
    
    Frontend -->|HTTP| API
    API --> DocRepo
    API --> SettleRepo
    API --> Verif
    API --> Pipeline
    Pipeline --> Extractor
    Pipeline --> Verifier
    Pipeline --> Matcher
    Pipeline --> Agent
    Agent -->|Async| AIProvider
    Extractor -->|OCR Text| OCR
    Verif --> Verifier
    Matcher --> Docs
    SettleRepo --> Settlements
    Verif --> Verification
    Pipeline --> Audits
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **Frontend (Next.js)** | Settlement upload, results display, batch demo UI, demo auth |
| **API Router** | HTTP endpoints for upload, extraction, verification, batch processing |
| **Document Repository** | Store/retrieve PDFs, OCR text; FormWise integration |
| **Settlement Repository** | Store/retrieve settlement records and deductions |
| **OCR Worker** | Background PaddleOCR processing |
| **Settlement Extractor** | Parse OCR text → settlement amounts, deductions, metadata |
| **Deterministic Verifier** | Rule-based verification: fee validity, tax compliance, amount checks |
| **Evidence Matcher** | Link deductions to supporting documents; compute confidence |
| **Finance Agent** | LLM-based investigation of ambiguous deductions |
| **AI Provider** | Interface to LLM (Anthropic, OpenAI, etc.) |
| **Verification Service** | Orchestrate verification workflow (deterministic + agent) |
| **Processing Pipeline** | End-to-end settlement processing (extract → verify → decide → audit) |
| **Audit Repository** | Store audit events (checks, reasoning, decisions) |
| **Decision Repository** | Store final settlement decisions |

---

## Finance Agent Architecture

### When Is the Agent Invoked?

The agent is invoked when deterministic verification **cannot confidently decide** on a deduction:

```python
if verification_result.status == "unverifiable":
    # Invoke AI agent to investigate
    agent_result = await finance_agent.investigate_deduction(
        deduction,
        settlement,
        verification_context={"error": "Low confidence", "confidence": 0.45}
    )
```

### What Does the Agent Receive?

- **Deduction data**: type, amount, reference ID, date, confidence
- **Settlement context**: gross amount, net settlement, other deductions, dates
- **Verification context**: What failed? (e.g., "Low confidence in fee calculation")
- **Evidence**: Supporting documents and extracted evidence
- **History**: Prior similar deductions and their outcomes

### How Does the Agent Investigate?

The agent:
1. **Receives** deduction + context
2. **Reasons** through possibilities:
   - Is the amount reasonable given settlement size?
   - Does the deduction type match the context?
   - Is there evidence to support or refute it?
   - Are there policy/regulatory reasons for this deduction?
3. **Produces** a decision: `"verified"` / `"disputed"` / `"unverifiable"`
4. **Confidence** score (0.0–1.0)
5. **Reasoning** (logged for audit)

### Agent Output

```json
{
  "decision": "verified",
  "confidence": 0.82,
  "reasoning": "Chargeback deduction of 500 INR matches typical disputed transaction pattern. Supporting evidence confirms customer dispute lodged 2 days before settlement date.",
  "investigation_status": "completed"
}
```

### How Deterministic + Agent Interact

```mermaid
sequenceDiagram
    participant Verifier as Deterministic<br/>Verifier
    participant Agent as Finance<br/>Agent
    participant Decision as Decision<br/>Synthesizer
    
    Verifier->>Verifier: Check fee validity
    Verifier->>Verifier: Check tax rate
    Verifier->>Verifier: Check amount math
    
    alt All Pass
        Verifier->>Decision: status=verified
    else Some Fail
        Verifier->>Agent: Ambiguous case
        Agent->>Agent: Research context
        Agent->>Agent: Reason through possibilities
        Agent->>Decision: Agent result + confidence
    end
    
    Decision->>Decision: Synthesize
    Decision->>Decision: Generate final decision
    Decision->>Decision: Log audit trail
```

---

## Settlement Processing Pipeline

### Complete Pipeline Workflow

```python
# Pseudocode: What happens when a settlement document is processed

async def process_settlement_document(document_id, owner_uid, evidence_doc_ids):
    # 1. Load document from storage
    document = document_repo.get(document_id)
    ocr_text = ocr_store.get(document_id)
    
    # 2. Extract settlement structure
    settlement = extractor.extract(ocr_text)
    settlement.owner_uid = owner_uid
    settlement_repo.create(settlement)
    
    # 3. Extract deductions
    deductions = extractor.extract_deductions(ocr_text)
    for deduction in deductions:
        deduction_repo.create(deduction)
    
    # 4. Find evidence documents
    evidence_links = evidence_matcher.find_evidence(
        settlement, deductions, evidence_doc_ids
    )
    
    # 5. Run deterministic verification
    for deduction in deductions:
        result = verifier.verify(deduction, settlement)
        verification_repo.create(result)
        
        # 6. If unresolved, invoke agent
        if result.status == "unverifiable":
            agent_result = await agent.investigate(
                deduction, settlement, result.context
            )
            verification_repo.update(result, agent_result)
    
    # 7. Generate final decision
    decision = synthesize_decision(verification_results)
    decision_repo.create(decision)
    
    # 8. Log audit trail
    audit_repo.create(FinanceAuditEvent(...))
    
    return SettlementResult(settlement, deductions, decision, audit_trail)
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Frontend as Frontend
    participant API as API
    participant Extractor as Extractor
    participant Verifier as Verifier
    participant Matcher as Evidence<br/>Matcher
    participant Agent as Finance<br/>Agent
    participant Decision as Decision<br/>Synthesizer
    participant Audit as Audit<br/>Trail
    
    Frontend->>API: POST /settlements/process-document
    API->>Extractor: extract(ocr_text)
    Extractor->>Extractor: parse amounts, dates, deductions
    API->>Matcher: find_evidence(settlement, deductions)
    Matcher->>Matcher: link deductions to docs
    
    loop For each deduction
        API->>Verifier: verify(deduction, settlement)
        Verifier->>Verifier: run deterministic checks
        alt Unresolved
            Verifier->>Agent: investigate(deduction, context)
            Agent->>Agent: LLM reasoning
            Agent->>Verifier: return decision
        end
        Verifier->>API: result
    end
    
    API->>Decision: synthesize(all_results)
    Decision->>Decision: APPROVE / FLAG / ESCALATE
    API->>Audit: log_decision(decision, reasoning)
    API->>Frontend: return ProcessSettlementDocumentResponse
```

---

## Core Finance Logic

### Settlement Model

```python
class Settlement:
    id: str                      # Unique settlement ID
    owner_uid: str               # User who owns this settlement
    source: str = "razorpay"     # Settlement source (e.g., Razorpay)
    settlement_date: datetime    # When settlement was processed
    gross_amount: float          # Total transaction amount
    net_amount: float            # Amount to be paid (after deductions)
    currency: str = "INR"        # Currency
    ocr_text: str                # Extracted OCR text from PDF
    extraction_status: str       # "pending" | "extracted" | "failed"
    created_at: datetime
```

### Deduction Model

```python
class SettlementDeduction:
    id: str                      # Unique deduction ID
    settlement_id: str           # Parent settlement
    type: str                    # "fee" | "tax" | "chargeback" | "adjustment"
    description: str             # Human-readable description
    amount: float                # Deduction amount
    reference_id: str | None     # Transaction/policy/regulation ID
    reference_date: str | None   # Date associated with deduction
    confidence: float            # Extraction confidence (0.0–1.0)
    created_at: datetime
```


### Verification Result

```python
class VerificationResult:
    id: str
    deduction_id: str
    settlement_id: str
    status: str                  # "verified" | "disputed" | "unverifiable"
    reason: str                  # Why this status?
    confidence: float            # Final confidence (0.0–1.0)
    agent_investigation: dict | None  # Agent findings if invoked
    evidence_links: list[str]    # IDs of matched evidence docs
    created_at: datetime
```

### Verification Rules

| Deduction Type | Verification Rule |
|---|---|
| **Fee** | Must be between 0% and 5% of gross; must have policy reference |
| **Tax** | Must match GST rate (5%, 12%, 18%) or notified rate; must have regulation |
| **Chargeback** | Must have supporting dispute evidence; amount must match transaction |
| **Adjustment** | Must have approval/authorization; must have reason |

### Settlement Decision

```python
class SettlementDecision:
    id: str
    settlement_id: str
    decision: str                # "approve" | "flag" | "escalate"
    verified_count: int          # Number of verified deductions
    disputed_count: int          # Number of disputed deductions
    unverifiable_count: int      # Number of unverifiable deductions
    approval_rate: float         # verified / total
    confidence: float            # Overall confidence in decision
    reason: str                  # Why this decision?
    escalation_reason: str | None # If escalate, why?
    created_at: datetime
```

### Decision Logic

```python
if all_deductions_verified:
    decision = "approve"
    reason = "All deductions verified and evidence matched"
elif any_disputed and agent_investigations_successful:
    decision = "flag"
    reason = f"{disputed_count} deductions disputed by verification; {agent_successes} resolved by agent; {unresolved} remain disputed"
elif any_unverifiable or high_exception_rate:
    decision = "escalate"
    reason = "Manual review required for unverifiable deductions or high exception rate"
else:
    decision = "flag"
```

### Audit Trail Events

Every check, decision, and agent call is logged:

```python
class FinanceAuditEvent:
    id: str
    settlement_id: str
    action: str                  # "extraction" | "verification" | "agent_investigation" | "decision"
    resource_type: str           # "deduction" | "settlement" | "decision"
    resource_id: str
    details: dict                # Specific to action
    confidence: float
    outcome: str
    timestamp: datetime
```

---

## Batch Processing & Benchmark

### Synthetic Dataset

FormFinance includes a **50+ settlement synthetic benchmark** representing diverse real-world scenarios:

- **Approvals** (70%): Settlements with all deductions verified
- **Flags** (20%): Settlements with disputed deductions but resolvable
- **Escalations** (10%): Settlements requiring manual review

**Clearly synthetic:** Settlement amounts, dates, reference IDs are generated. **NOT real Razorpay financial data.**

### Benchmark Metrics

```
Total Records:               50
Processed:                   50
Successfully Extracted:      50
Extraction Success Rate:     100.0%

Total Deductions:            150
Verified Deductions:         120
Disputed Deductions:         20
Unverifiable Deductions:     10
Deduction Verification Rate: 93.3%

APPROVED Count:              35
FLAGGED Count:               12
ESCALATED Count:             3
Processing Failed Count:     0

Evidence Checked:            150
Evidence Matched:            140
Evidence Match Rate:         93.3%

Agent Investigations:        10
Agent Successes:             8
Agent Failures:              2

Processing Duration:         ~2.5 seconds
Throughput:                  ~20 records/second
```

### Running the Benchmark

```bash
# 1. Start backend and worker
docker-compose up -d api worker

# 2. Wait for services
sleep 10

# 3. Run benchmark
uv run python run_benchmark.py
```

### What Benchmarks Show

- **Extraction Rate**: How many settlements are successfully parsed
- **Verification Rate**: Percentage of deductions that pass deterministic checks
- **Evidence Match Rate**: Percentage of deductions matched to supporting documents
- **Agent Success Rate**: When agent is invoked, how often does it resolve ambiguity?
- **Decision Distribution**: Proportion of APPROVE / FLAG / ESCALATE
- **Throughput**: Settlements processed per second
- **Exception Rate**: Unhandled failures

---

## Razorpay Buildathon Alignment

### Track 04: AI Finance Controller

**Track Description:**
> Build an AI-driven finance controller that automates financial workflows, handles exceptions, and produces auditable decisions at scale.

**FormFinance Alignment:**

| Requirement | FormFinance Implementation |
|---|---|
| **Finance Workflow** | Settlement verification (core fintech workflow) |
| **Automation** | Document upload → OCR → extraction → verification → decision (fully automated) |
| **AI/Agent** | Finance agent investigates ambiguous deductions using LLM reasoning |
| **Exception Handling** | Deterministic checks + agent investigation for edge cases; escalation for manual review |
| **Auditability** | Complete audit trail of checks, reasoning, and decisions |
| **Scale** | Processes 50+ settlements with metrics |
| **Measurable Accuracy** | Extraction rate, verification rate, evidence match rate, agent success rate |
| **Measurable Throughput** | Records per second, batch processing time |

**Why This Fits:**
- Settlement reconciliation is a **real finance workflow** (not a hypothetical)
- **Automation** reduces manual work from hours to seconds
- **AI agent** handles cases that deterministic rules cannot
- **Exceptions** (ambiguous deductions) are routed to agent, then to human if unresolved
- **Audit trail** provides compliance proof
- **Batch processing** demonstrates scale

---

## API Documentation

### Authentication

All endpoints require authentication:

```bash
# Demo mode (if enabled)
curl -X GET http://localhost:8000/api/v1/settlements \
  -H "X-Demo-User-ID: demo-user-1"

# Firebase mode
curl -X GET http://localhost:8000/api/v1/settlements \
  -H "Authorization: Bearer <firebase_id_token>"
```

### Document Upload

**POST /documents/upload-intents**

Create an upload intent for a settlement PDF.

**Request:**
```json
{
  "originalFilename": "settlement-2025-01.pdf",
  "contentType": "application/pdf",
  "fileSize": 245632
}
```

**Response:**
```json
{
  "documentId": "doc_abc123xyz",
  "uploadUrl": "http://localhost:8000/api/v1/documents/doc_abc123xyz/upload",
  "uploadMethod": "PUT",
  "expiresAt": "2025-01-06T12:00:00Z"
}
```

---

**PUT /documents/{document_id}/upload**

Upload the PDF to the signed URL.

**Request:**
```bash
curl -X PUT <uploadUrl> \
  -H "Content-Type: application/pdf" \
  --data-binary @settlement.pdf
```

**Response:** 204 No Content

---

**POST /documents/{document_id}/complete**

Complete the upload and trigger OCR processing.

**Response:**
```json
{
  "documentId": "doc_abc123xyz",
  "filename": "settlement-2025-01.pdf",
  "contentType": "application/pdf",
  "fileSize": 245632,
  "extractionStatus": "processing",
  "createdAt": "2025-01-06T10:00:00Z"
}
```

---

### Settlement Processing

**POST /settlements/process-document**

Process a settlement document end-to-end.

**Request:**
```json
{
  "documentId": "doc_abc123xyz",
  "ocrText": "... extracted OCR text from PDF ...",
  "evidenceDocumentIds": ["doc_evidence_1", "doc_evidence_2"]
}
```

**Response:**
```json
{
  "settlementId": "settlement_xyz789",
  "documentId": "doc_abc123xyz",
  "sourceSystem": "razorpay",
  "settlementDate": "2025-01-01",
  "grossAmount": 100000.00,
  "netAmount": 97500.00,
  "deductions": [
    {
      "deductionId": "ded_001",
      "type": "fee",
      "description": "Platform fee 2.5%",
      "amount": 2500.00,
      "confidence": 0.98
    }
  ],
  "verificationResults": [
    {
      "deductionId": "ded_001",
      "status": "verified",
      "confidence": 0.95,
      "reason": "Fee amount matches policy"
    }
  ],
  "decision": {
    "decision": "approve",
    "verifiedCount": 3,
    "disputedCount": 0,
    "unverifiableCount": 0,
    "confidence": 0.98,
    "reason": "All deductions verified and evidence matched"
  },
  "auditTrail": [
    {
      "timestamp": "2025-01-06T10:00:01Z",
      "action": "extraction",
      "details": "Settlement extracted: 3 deductions found"
    },
    {
      "timestamp": "2025-01-06T10:00:02Z",
      "action": "verification",
      "details": "All deductions verified"
    }
  ],
  "processingTimeMs": 1250
}
```

---

**GET /settlements/{settlement_id}**

Retrieve a specific settlement and its verification results.

**Response:** (same as above, cached)

---

**GET /settlements**

List all settlements for the current user.

**Query Parameters:**
- `limit` (optional, default 10): Number of results

**Response:**
```json
[
  { ... settlement 1 ... },
  { ... settlement 2 ... },
  ...
]
```

---


### Verification Result

```python
class VerificationResult:
    id: str
    deduction_id: str
    settlement_id: str
    status: str                  # "verified" | "disputed" | "unverifiable"
    reason: str                  # Why this status?
    confidence: float            # Final confidence (0.0–1.0)
    agent_investigation: dict | None  # Agent findings if invoked
    evidence_links: list[str]    # IDs of matched evidence docs
    created_at: datetime
```

### Verification Rules

| Deduction Type | Verification Rule |
|---|---|
| **Fee** | Must be between 0% and 5% of gross; must have policy reference |
| **Tax** | Must match GST rate (5%, 12%, 18%) or notified rate; must have regulation |
| **Chargeback** | Must have supporting dispute evidence; amount must match transaction |
| **Adjustment** | Must have approval/authorization; must have reason |

### Settlement Decision

```python
class SettlementDecision:
    id: str
    settlement_id: str
    decision: str                # "approve" | "flag" | "escalate"
    verified_count: int          # Number of verified deductions
    disputed_count: int          # Number of disputed deductions
    unverifiable_count: int      # Number of unverifiable deductions
    approval_rate: float         # verified / total
    confidence: float            # Overall confidence in decision
    reason: str                  # Why this decision?
    escalation_reason: str | None # If escalate, why?
    created_at: datetime
```

### Decision Logic

```python
if all_deductions_verified:
    decision = "approve"
    reason = "All deductions verified and evidence matched"
elif any_disputed and agent_investigations_successful:
    decision = "flag"
    reason = f"{disputed_count} deductions disputed by verification; {agent_successes} resolved by agent; {unresolved} remain disputed"
elif any_unverifiable or high_exception_rate:
    decision = "escalate"
    reason = "Manual review required for unverifiable deductions or high exception rate"
else:
    decision = "flag"
```

### Audit Trail Events

Every check, decision, and agent call is logged:

```python
class FinanceAuditEvent:
    id: str
    settlement_id: str
    action: str                  # "extraction" | "verification" | "agent_investigation" | "decision"
    resource_type: str           # "deduction" | "settlement" | "decision"
    resource_id: str
    details: dict                # Specific to action
    confidence: float
    outcome: str
    timestamp: datetime
```

---

## Batch Processing & Benchmark

### Synthetic Dataset

FormFinance includes a **50+ settlement synthetic benchmark** representing diverse real-world scenarios:

- **Approvals** (70%): Settlements with all deductions verified
- **Flags** (20%): Settlements with disputed deductions but resolvable
- **Escalations** (10%): Settlements requiring manual review

**Clearly synthetic:** Settlement amounts, dates, reference IDs are generated. **NOT real Razorpay financial data.**

### Benchmark Metrics

```
Total Records:               50
Processed:                   50
Successfully Extracted:      50
Extraction Success Rate:     100.0%

Total Deductions:            150
Verified Deductions:         120
Disputed Deductions:         20
Unverifiable Deductions:     10
Deduction Verification Rate: 93.3%

APPROVED Count:              35
FLAGGED Count:               12
ESCALATED Count:             3
Processing Failed Count:     0

Evidence Checked:            150
Evidence Matched:            140
Evidence Match Rate:         93.3%

Agent Investigations:        10
Agent Successes:             8
Agent Failures:              2

Processing Duration:         ~2.5 seconds
Throughput:                  ~20 records/second
```

### Running the Benchmark

```bash
# 1. Start backend and worker
docker-compose up -d api worker

# 2. Wait for services
sleep 10

# 3. Run benchmark
uv run python run_benchmark.py
```

### What Benchmarks Show

- **Extraction Rate**: How many settlements are successfully parsed
- **Verification Rate**: Percentage of deductions that pass deterministic checks
- **Evidence Match Rate**: Percentage of deductions matched to supporting documents
- **Agent Success Rate**: When agent is invoked, how often does it resolve ambiguity?
- **Decision Distribution**: Proportion of APPROVE / FLAG / ESCALATE
- **Throughput**: Settlements processed per second
- **Exception Rate**: Unhandled failures

---

## Razorpay Buildathon Alignment

### Track 04: AI Finance Controller

**Track Description:**
> Build an AI-driven finance controller that automates financial workflows, handles exceptions, and produces auditable decisions at scale.

**FormFinance Alignment:**

| Requirement | FormFinance Implementation |
|---|---|
| **Finance Workflow** | Settlement verification (core fintech workflow) |
| **Automation** | Document upload → OCR → extraction → verification → decision (fully automated) |
| **AI/Agent** | Finance agent investigates ambiguous deductions using LLM reasoning |
| **Exception Handling** | Deterministic checks + agent investigation for edge cases; escalation for manual review |
| **Auditability** | Complete audit trail of checks, reasoning, and decisions |
| **Scale** | Processes 50+ settlements with metrics |
| **Measurable Accuracy** | Extraction rate, verification rate, evidence match rate, agent success rate |
| **Measurable Throughput** | Records per second, batch processing time |

**Why This Fits:**
- Settlement reconciliation is a **real finance workflow** (not a hypothetical)
- **Automation** reduces manual work from hours to seconds
- **AI agent** handles cases that deterministic rules cannot
- **Exceptions** (ambiguous deductions) are routed to agent, then to human if unresolved
- **Audit trail** provides compliance proof
- **Batch processing** demonstrates scale

---

## API Documentation

### Authentication

All endpoints require authentication:

```bash
# Demo mode (if enabled)
curl -X GET http://localhost:8000/api/v1/settlements \
  -H "X-Demo-User-ID: demo-user-1"

# Firebase mode
curl -X GET http://localhost:8000/api/v1/settlements \
  -H "Authorization: Bearer <firebase_id_token>"
```

### Document Upload

**POST /documents/upload-intents**

Create an upload intent for a settlement PDF.

**Request:**
```json
{
  "originalFilename": "settlement-2025-01.pdf",
  "contentType": "application/pdf",
  "fileSize": 245632
}
```

**Response:**
```json
{
  "documentId": "doc_abc123xyz",
  "uploadUrl": "http://localhost:8000/api/v1/documents/doc_abc123xyz/upload",
  "uploadMethod": "PUT",
  "expiresAt": "2025-01-06T12:00:00Z"
}
```

---

**PUT /documents/{document_id}/upload**

Upload the PDF to the signed URL.

**Request:**
```bash
curl -X PUT <uploadUrl> \
  -H "Content-Type: application/pdf" \
  --data-binary @settlement.pdf
```

**Response:** 204 No Content

---

**POST /documents/{document_id}/complete**

Complete the upload and trigger OCR processing.

**Response:**
```json
{
  "documentId": "doc_abc123xyz",
  "filename": "settlement-2025-01.pdf",
  "contentType": "application/pdf",
  "fileSize": 245632,
  "extractionStatus": "processing",
  "createdAt": "2025-01-06T10:00:00Z"
}
```

---

### Settlement Processing

**POST /settlements/process-document**

Process a settlement document end-to-end.

**Request:**
```json
{
  "documentId": "doc_abc123xyz",
  "ocrText": "... extracted OCR text from PDF ...",
  "evidenceDocumentIds": ["doc_evidence_1", "doc_evidence_2"]
}
```

**Response:**
```json
{
  "settlementId": "settlement_xyz789",
  "documentId": "doc_abc123xyz",
  "sourceSystem": "razorpay",
  "settlementDate": "2025-01-01",
  "grossAmount": 100000.00,
  "netAmount": 97500.00,
  "deductions": [
    {
      "deductionId": "ded_001",
      "type": "fee",
      "description": "Platform fee 2.5%",
      "amount": 2500.00,
      "confidence": 0.98
    }
  ],
  "verificationResults": [
    {
      "deductionId": "ded_001",
      "status": "verified",
      "confidence": 0.95,
      "reason": "Fee amount matches policy"
    }
  ],
  "decision": {
    "decision": "approve",
    "verifiedCount": 3,
    "disputedCount": 0,
    "unverifiableCount": 0,
    "confidence": 0.98,
    "reason": "All deductions verified and evidence matched"
  },
  "auditTrail": [
    {
      "timestamp": "2025-01-06T10:00:01Z",
      "action": "extraction",
      "details": "Settlement extracted: 3 deductions found"
    },
    {
      "timestamp": "2025-01-06T10:00:02Z",
      "action": "verification",
      "details": "All deductions verified"
    }
  ],
  "processingTimeMs": 1250
}
```

---

**GET /settlements/{settlement_id}**

Retrieve a specific settlement and its verification results.

**Response:** (same as above, cached)

---

**GET /settlements**

List all settlements for the current user.

**Query Parameters:**
- `limit` (optional, default 10): Number of results

**Response:**
```json
[
  { ... settlement 1 ... },
  { ... settlement 2 ... },
  ...
]
```

---

**POST /settlements/batch/process**

Process multiple settlements in a batch.

**Request:**
```json
{
  "settlements": [
    {
      "source": "razorpay",
      "settlementDate": "2025-01-01",
      "grossAmount": 100000.00,
      "netAmount": 97500.00,
      "currency": "INR",
      "ocrText": "... OCR text ..."
    }
  ]
}
```

**Response:**
```json
{
  "timestamp": "2025-01-06T10:00:00Z",
  "totalRecords": 50,
  "processed": 50,
  "extractionSuccessRate": 1.0,
  "deductionVerificationRate": 0.933,
  "evidenceMatchRate": 0.933,
  "approvedCount": 35,
  "flaggedCount": 12,
  "escalatedCount": 3,
  "agentInvestigations": 10,
  "agentSuccesses": 8,
  "agentFailures": 2,
  "processingTimeMs": 2500,
  "throughput": 20.0,
  "exceptions": [...]
}
```

---

**GET /settlements/batch/demo-run**

Run the 50-record synthetic benchmark.

**Response:** (same as `/batch/process`)

---

### Health Checks

**GET /health**

Check API health.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-06T10:00:00Z"
}
```

---

## Frontend

### Pages

| Page | Route | Purpose |
|---|---|---|
| **Home** | `/` | Landing page with info and login |
| **Settlement Upload** | `/app/upload` | Upload a settlement PDF |
| **Settlement Processor** | `/app/settlements` | View uploaded settlements and process them |
| **Results** | `/app/settlements/{id}` | View settlement verification results and decision |
| **History** | `/app/history` | View past settlements and batch runs |
| **Form Processing** | `/app/forms` | Access to underlying FormWise document processing |
| **Settings** | `/app/settings` | Auth settings, demo mode toggle |

### Key Components

- **AuthContext** (`contexts/auth-context.tsx`): Manages demo auth and Firebase auth
- **SettlementProcessor** (`components/SettlementProcessor.jsx`): Main settlement upload and processing UI
- **DocumentUpload** (`components/DocumentUpload.tsx`): File upload with validation
- **ResultsDisplay** (`components/SettlementResults.tsx`): Shows verification results, decision, audit trail

### Data Flow

```
User clicks "Upload Settlement"
  ↓
Frontend calls POST /documents/upload-intents
  ↓
Backend returns uploadUrl
  ↓
Frontend uploads PDF to uploadUrl (PUT)
  ↓
Frontend calls POST /documents/{documentId}/complete
  ↓
Backend processes OCR in worker
  ↓
Frontend calls POST /settlements/process-document
  ↓
Backend runs full settlement pipeline
  ↓
Frontend receives decision
  ↓
Display results: deductions, verification, decision, audit trail
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 15.5, React 19, TypeScript | UI, routing, state management |
| **Frontend Build** | Webpack, npm | Build and dependency management |
| **Backend API** | FastAPI, Python 3.13+ | HTTP API, routing, async handling |
| **Backend Async** | AsyncIO, APScheduler | Background jobs, async workflows |
| **OCR** | PaddleOCR, paddlepaddle | Document text extraction |
| **NLP/Extraction** | spaCy (optional) | Named entity recognition, text parsing |
| **AI/Agent** | Anthropic Claude (configurable) | LLM for finance agent reasoning |
| **Persistence** | Firestore (Firebase) | Settlements, deductions, verification results |
| **Document Storage** | Local filesystem (demo) | Uploaded PDFs, OCR text |
| **Audit** | Firestore | Audit trail of all actions |
| **Docker** | Docker Compose | Service orchestration (API, Worker, Ollama) |
| **Authentication** | Firebase Auth (optional), Demo Mode | User identity, demo bypass |
| **Package Manager** | uv (Python), npm (Node) | Dependency management |
| **Testing** | pytest, Node test runner | Unit and integration tests |

---

## Repository Structure

```
FormFinance-main/
├── README.md                          # This file
├── docker-compose.yml                 # Service orchestration
├── pyproject.toml                     # Python workspace config
├── run_benchmark.py                   # Benchmark runner
├── package.json                       # Node workspace config
│
├── apps/
│   └── web/                           # Next.js frontend
│       ├── src/
│       │   ├── app/                   # Next.js app directory
│       │   │   ├── page.tsx           # Home page
│       │   │   ├── app/               # Protected routes
│       │   │   │   ├── settlements/   # Settlement processing page
│       │   │   │   ├── upload/        # Upload page
│       │   │   │   ├── history/       # Settlement history
│       │   │   │   └── ...
│       │   ├── components/            # React components
│       │   │   ├── SettlementProcessor.jsx
│       │   │   ├── DocumentUpload.tsx
│       │   │   └── ...
│       │   ├── contexts/              # Context providers
│       │   │   └── auth-context.tsx   # Auth (Firebase + Demo)
│       │   ├── services/              # API client services
│       │   │   ├── documents/
│       │   │   ├── settlements/
│       │   │   └── ...
│       │   └── config/                # Configuration
│       │       └── env.ts             # Environment variables
│       └── Dockerfile                 # Frontend Docker image
│
├── packages/
│   ├── ai-provider/                   # AI provider interface
│   ├── contracts/                     # Shared type definitions
│   ├── document-core/                 # Document processing library
│   └── policy/                        # Policy/rule definitions
│
├── services/
│   ├── api/                           # FastAPI backend
│   │   ├── src/formwise_api/
│   │   │   ├── main.py                # FastAPI app
│   │   │   ├── api.py                 # Router assembly
│   │   │   ├── config.py              # Configuration (env vars)
│   │   │   ├── settlements/           # Settlement logic
│   │   │   │   ├── router.py          # Settlement endpoints
│   │   │   │   ├── models.py          # Data models
│   │   │   │   ├── service.py         # Business logic
│   │   │   │   ├── extraction_service.py
│   │   │   │   ├── verification_service.py
│   │   │   │   ├── deterministic_verifier.py
│   │   │   │   ├── evidence_matcher.py
│   │   │   │   ├── finance_agent.py   # AI agent
│   │   │   │   ├── batch_processor.py # Batch processing
│   │   │   │   ├── processing.py      # Complete pipeline
│   │   │   │   └── demo_data.py       # Synthetic benchmark data
│   │   │   ├── documents/             # Document management
│   │   │   ├── verification/          # Verification results storage
│   │   │   ├── evidence/              # Evidence linking
│   │   │   ├── audit/                 # Audit trail
│   │   │   ├── dependencies/          # Dependency injection
│   │   │   └── ...
│   │   ├── pyproject.toml             # Python package config
│   │   └── Dockerfile                 # Backend Docker image
│   │
│   └── worker/                        # Background job worker
│       ├── src/formwise_worker/
│       │   ├── ocr/                   # OCR processing
│       │   │   ├── store.py           # OCR storage
│       │   └── ...
│       ├── pyproject.toml
│       └── Dockerfile
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md
│   ├── OCR_PIPELINE.md
│   ├── SETTLEMENTS.md
│   └── ...
│
├── tests/                             # Tests
│   ├── test_*.py                      # Unit/integration tests
│   └── README.md
│
├── infra/                             # Infrastructure docs
│   └── README.md
│
└── firebase.json                      # Firebase config (if applicable)
```

---

## Requirements

### System

- **OS**: Linux, macOS, or Windows (WSL2)
- **Docker**: 20.10+ with Docker Compose 2.0+
- **Python**: 3.13+
- **Node**: 20+ (with npm 11+)

### Development

- **Optional**: IDE (VS Code, PyCharm, etc.)
- **Optional**: Git (for version control)

### Runtime Dependencies

- **Backend**: Python packages (see `services/api/pyproject.toml`)
- **Frontend**: Node packages (see `apps/web/package.json`)
- **OCR**: PaddleOCR (installed via Python dependencies)
- **AI**: Anthropic API key (for finance agent; optional if using demo)
- **Firebase**: Service account JSON (optional; demo mode doesn't require)

---

## Installation & Setup

### Option 1: Docker (Recommended)

#### Prerequisites
```bash
# Verify Docker and Docker Compose are installed
docker --version   # Should be 20.10+
docker-compose --version  # Should be 2.0+
```

#### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/your-org/FormFinance-main.git
cd FormFinance-main

# 2. Copy environment template
cp .env.example .env

# 3. (Optional) Configure AI provider in .env
# Uncomment and set ANTHROPIC_API_KEY if using finance agent

# 4. Build Docker images
docker-compose build

# 5. Start services
docker-compose up -d

# 6. Verify services are running
curl -s http://localhost:8000/api/v1/health | jq .
curl -s http://localhost:3000 | grep -o "FORMFINANCE" | head -1

# 7. Open application
# http://localhost:3000 (frontend)
# http://localhost:8000/api/v1/health (backend health)
```

### Option 2: Local Development

#### Prerequisites
```bash
# 1. Install Python 3.13+
python --version  # Should be 3.13+

# 2. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install Node 20+
node --version  # Should be 20+
npm --version   # Should be 11+
```

#### Backend Setup
```bash
# 1. From repository root
cd services/api

# 2. Install dependencies
uv sync

# 3. Verify installation
uv run python -c "import formwise_api; print('OK')"

# 4. Start API server (from services/api/)
uv run uvicorn formwise_api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Worker Setup (Separate Terminal)
```bash
# 1. From repository root
cd services/worker

# 2. Install dependencies
uv sync

# 3. Start worker
uv run python -m formwise_worker.jobs
```

#### Frontend Setup (Separate Terminal)
```bash
# 1. From repository root
cd apps/web

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Open http://localhost:3000
```

---

## Environment Variables

### Backend (`.env`)

```bash
# Application
FORMWISE_ENV=development              # development|staging|production
LOG_LEVEL=INFO
API_PREFIX=/api/v1
APP_NAME="FormWise AI API"
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Firebase (optional; leave blank for demo mode)
FIREBASE_PROJECT_ID=                  # Your Firebase project ID
FIREBASE_SERVICE_ACCOUNT_JSON=        # Full service account JSON
FIREBASE_SERVICE_ACCOUNT_PATH=        # OR path to service account file

# Demo Mode (for testing without Firebase)
DEMO_AUTH_ENABLED=true                # Enable demo auth bypass
# If enabled, pass X-Demo-User-ID header instead of Firebase token

# AI Provider (for finance agent)
ANTHROPIC_API_KEY=sk-...              # Anthropic API key
# Leave empty for deterministic-only (no agent)

# OCR
# (Configured via Python dependencies; no env var needed)

# Storage (default: local filesystem)
# (Uses ./storage/uploads, ./storage/ocr, etc.)
```

### Frontend (`.env.local`)

```bash
# API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Demo Mode
NEXT_PUBLIC_DEMO_AUTH_ENABLED=true    # Enable demo auth UI

# Firebase (optional)
NEXT_PUBLIC_FIREBASE_API_KEY=         # Firebase API key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=     # Firebase auth domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=      # Firebase project ID
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
```

---
