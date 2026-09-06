# FormFinance — System Design Document

**Version:** 1.0  
**Date:** January 2025  
**Status:** Approved  

---

## 1. Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│                 ┌──────────────────────────────────┐             │
│                 │   Settlement Upload & Results    │             │
│                 │   Batch Demo Runner              │             │
│                 │   History & Audit Trail Display  │             │
│                 └──────────────────────────────────┘             │
└─────────────────────┬──────────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼──────────────────────────────────────────┐
│                    API Gateway (FastAPI)                        │
│            ┌──────────────────────────────────┐                 │
│            │   /documents/*                   │                 │
│            │   /settlements/*                 │                 │
│            │   /batch/*                       │                 │
│            └──────────────────────────────────┘                 │
└─────────────────────┬──────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────────┐
        │             │             │                  │
        │             │             │                  │
        ▼             ▼             ▼                  ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐    ┌─────────────┐
    │Document│  │Settlement│  │Verification  │AI Provider  │
    │Service │  │Service   │  │Service   │    │(Anthropic)  │
    └────────┘  └──────────┘  └──────────┘    └─────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
    ┌─────────────────▼──────────────────┐
    │   Storage Layer                    │
    │   ┌──────────────────────────────┐ │
    │   │ Firestore / Local Filesystem  │ │
    │   │ (documents, settlements,      │ │
    │   │  audits, verifications)       │ │
    │   └──────────────────────────────┘ │
    └────────────────────────────────────┘
        │
    ┌───▼─────────────────────┐
    │   Background Worker     │
    │   (OCR, Extraction)     │
    └───────────────────────┘
```

---

## 2. System Components

### 2.1 Frontend (Next.js)

**Responsibility:** User interface for document upload, settlement processing, results display

**Key Components:**
- `AuthContext`: Demo + Firebase authentication
- `SettlementProcessor`: Main upload & processing UI
- `DocumentUpload`: File picker and validation
- `SettlementResults`: Display verification results, decision, audit trail
- `BatchDemo`: 50-record benchmark runner
- `SettlementHistory`: Past settlements and batch runs

**Technologies:**
- Next.js 15.5
- React 19 with hooks
- TypeScript
- TailwindCSS
- Axios (HTTP client)
- React Query (state management)

**Folder Structure:**
```
apps/web/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx            # Home
│   │   ├── app/                # Protected routes
│   │   │   ├── settlements/
│   │   │   ├── upload/
│   │   │   ├── history/
│   │   │   └── settings/
│   ├── components/             # React components
│   ├── contexts/               # Auth context
│   ├── services/               # API clients
│   └── config/                 # Environment
```

### 2.2 Backend API (FastAPI)

**Responsibility:** Business logic, orchestration, data persistence

**Key Modules:**
- `documents`: Document upload, storage, OCR text retrieval
- `settlements`: Settlement CRUD, extraction, verification
- `verification`: Rule-based verification logic
- `evidence`: Evidence linking and matching
- `finance_agent`: LLM-based investigation
- `audit`: Audit trail logging
- `batch`: Batch processing orchestration

**Technologies:**
- FastAPI
- Pydantic (validation)
- SQLAlchemy / Firestore ORM
- AsyncIO
- pytest (testing)

**Folder Structure:**
```
services/api/src/formwise_api/
├── main.py                     # FastAPI app
├── api.py                      # Router assembly
├── config.py                   # Settings
├── dependencies/               # Dependency injection
├── documents/                  # Document routes & logic
├── settlements/                # Settlement routes & logic
│   ├── router.py
│   ├── models.py
│   ├── service.py
│   ├── extraction_service.py
│   ├── verification_service.py
│   ├── deterministic_verifier.py
│   ├── evidence_matcher.py
│   ├── finance_agent.py
│   ├── batch_processor.py
│   ├── processing.py           # Complete pipeline
│   └── demo_data.py            # 50-record benchmark
├── verification/               # Verification results storage
├── evidence/                   # Evidence linking
├── audit/                      # Audit trail
├── authentication/             # Auth logic
└── ai_provider/                # AI provider interface
```

### 2.3 OCR Worker

**Responsibility:** Background OCR processing using PaddleOCR

**Technologies:**
- Python 3.13+
- PaddleOCR
- paddlepaddle
- AsyncIO
- File storage

**Workflow:**
1. Watch for new documents
2. Extract text using PaddleOCR
3. Store OCR text in storage/ocr/{document_id}.txt
4. Update document status to "extracted"

### 2.4 Storage Layer

**Responsibility:** Persistent data storage

**Entities:**
- **Documents**: Uploaded PDFs, metadata, extraction status
- **Settlements**: Parsed settlement records
- **SettlementDeductions**: Individual deductions
- **VerificationResults**: Deterministic check outcomes
- **SettlementDecisions**: Final decisions (APPROVE/FLAG/ESCALATE)
- **EvidenceLinks**: Deduction ↔ evidence mapping
- **AuditEvents**: Complete action log

**Storage Options:**
- **MVP (Demo):** Local filesystem (`storage/uploads/`, `storage/ocr/`, etc.)
- **Production:** Firestore (collections)

**Schema:**
```python
# Document
{
  id: UUID
  owner_uid: str
  filename: str
  content_type: str
  file_size: int
  extraction_status: "pending" | "extracted" | "failed"
  created_at: datetime
}

# Settlement
{
  id: UUID
  document_id: UUID
  owner_uid: str
  source: str = "razorpay"
  settlement_date: datetime
  gross_amount: float
  net_amount: float
  currency: str
  ocr_text: str
  created_at: datetime
}

# SettlementDeduction
{
  id: UUID
  settlement_id: UUID
  type: str  # "fee" | "tax" | "chargeback" | "adjustment"
  description: str
  amount: float
  reference_id: str | None
  reference_date: str | None
  confidence: float  # 0.0-1.0
  created_at: datetime
}

# VerificationResult
{
  id: UUID
  deduction_id: UUID
  settlement_id: UUID
  status: str  # "verified" | "disputed" | "unverifiable"
  reason: str
  confidence: float  # 0.0-1.0
  agent_investigation: dict | None
  evidence_links: list[str]
  created_at: datetime
}

# SettlementDecision
{
  id: UUID
  settlement_id: UUID
  decision: str  # "approve" | "flag" | "escalate"
  verified_count: int
  disputed_count: int
  unverifiable_count: int
  approval_rate: float
  confidence: float
  reason: str
  created_at: datetime
}

# AuditEvent
{
  id: UUID
  settlement_id: UUID
  action: str  # "extraction" | "verification" | "agent_investigation" | "decision"
  resource_type: str  # "deduction" | "settlement" | "decision"
  resource_id: str
  details: dict
  outcome: str
  timestamp: datetime (UTC)
}
```

---

## 3. Data Flow Diagrams

### 3.1 Settlement Processing Pipeline

```
User Upload PDF
    ↓
Frontend: POST /documents/upload-intents
    ↓
Backend: Create document record, return uploadUrl
    ↓
Frontend: PUT {uploadUrl} (upload binary)
    ↓
Backend: Store file, call POST /documents/{id}/complete
    ↓
Worker: Trigger OCR processing
    ↓
Worker: Extract text, store in storage/ocr/{id}.txt
    ↓
Backend: Mark document as "extracted"
    ↓
Frontend: Call POST /settlements/process-document
    ↓
Backend Pipeline:
  1. Load document + OCR text
  2. Extract settlement structure
  3. Identify deductions
  4. Create deduction records
  5. Find evidence documents
  6. Link evidence to deductions
  ↓
For each deduction:
  7a. Run deterministic verification
  7b. If unverifiable, invoke AI agent
  ↓
  8. Synthesize decision (APPROVE/FLAG/ESCALATE)
  9. Log audit trail
  10. Return ProcessSettlementDocumentResponse
    ↓
Frontend: Display results
  - Extracted settlement
  - Deductions with status
  - Evidence matching
  - Agent findings
  - Final decision
  - Audit trail
```

### 3.2 Batch Processing Flow

```
User: POST /settlements/batch/process
  ├─ settlements: [
  │   { date, gross_amount, net_amount, ocr_text },
  │   ...
  │ ]
    ↓
Backend BatchProcessor:
  For each settlement in batch:
    1. Create settlement record
    2. Extract deductions
    3. Run verification
    4. Invoke agent (if needed)
    5. Generate decision
    6. Log audit
    ↓
    Collect metrics:
    - Total records
    - Processed count
    - Extraction success rate
    - Verification rate (verified/disputed/unverifiable)
    - Decision distribution (APPROVE/FLAG/ESCALATE)
    - Agent investigation results
    - Evidence match rate
    - Processing time
    - Throughput
    ↓
Return BatchMetricsResponse
  └─ metrics: { ... }
     results: [settlement_result, ...]
```

---

## 4. API Design

### 4.1 Authentication

**Header-based:**
```
# Demo mode
X-Demo-User-ID: demo-user-1

# Firebase mode
Authorization: Bearer <firebase_id_token>
```

### 4.2 Document Upload Endpoints

**POST /documents/upload-intents**
```json
Request:
{
  "originalFilename": "settlement-2025-01.pdf",
  "contentType": "application/pdf",
  "fileSize": 245632
}

Response:
{
  "documentId": "doc_abc123",
  "uploadUrl": "http://localhost:8000/api/v1/documents/doc_abc123/upload",
  "uploadMethod": "PUT",
  "expiresAt": "2025-01-06T12:00:00Z"
}
```

**PUT /documents/{documentId}/upload**
- Binary file upload (Content-Type: application/pdf)
- Response: 204 No Content

**POST /documents/{documentId}/complete**
- Trigger OCR processing
- Response: { documentId, filename, status: "processing" }

### 4.3 Settlement Processing

**POST /settlements/process-document**
```json
Request:
{
  "documentId": "doc_abc123",
  "ocrText": "... extracted text ...",
  "evidenceDocumentIds": ["doc_evidence_1", ...]
}

Response:
{
  "settlementId": "settlement_xyz",
  "documentId": "doc_abc123",
  "settlementDate": "2025-01-01",
  "grossAmount": 100000.00,
  "netAmount": 97500.00,
  "deductions": [
    {
      "deductionId": "ded_001",
      "type": "fee",
      "amount": 2500.00,
      "confidence": 0.98
    }
  ],
  "verificationResults": [
    {
      "deductionId": "ded_001",
      "status": "verified",
      "confidence": 0.95
    }
  ],
  "decision": {
    "decision": "approve",
    "confidence": 0.98,
    "reason": "All deductions verified"
  },
  "auditTrail": [
    {
      "timestamp": "2025-01-06T10:00:01Z",
      "action": "extraction",
      "details": "3 deductions found"
    },
    ...
  ]
}
```

**GET /settlements/{settlementId}**
- Retrieve cached settlement

**GET /settlements**
- List all settlements for user
- Query: ?limit=10&offset=0

### 4.4 Batch Processing

**POST /settlements/batch/process**
```json
Request:
{
  "settlements": [
    {
      "source": "razorpay",
      "settlementDate": "2025-01-01",
      "grossAmount": 100000,
      "netAmount": 97500,
      "ocrText": "..."
    },
    ...
  ]
}

Response:
{
  "timestamp": "2025-01-06T10:00:00Z",
  "totalRecords": 50,
  "processed": 50,
  "extractionSuccessRate": 1.0,
  "verificationRate": 0.93,
  "approvedCount": 35,
  "flaggedCount": 12,
  "escalatedCount": 3,
  "agentInvestigations": 10,
  "agentSuccesses": 8,
  "processingTimeMs": 2500,
  "throughput": 20.0
}
```

**GET /settlements/batch/demo-run**
- Run 50-record synthetic benchmark
- Response: Same as batch/process

---

## 5. Database Design

### 5.1 Firestore Collections (Production)

```
Collections:
├── documents/{document_id}
│   ├── id
│   ├── owner_uid
│   ├── filename
│   ├── extraction_status
│   ├── created_at
│   └── (subcollection) ocr_text
│
├── settlements/{settlement_id}
│   ├── id
│   ├── document_id
│   ├── owner_uid
│   ├── gross_amount
│   ├── net_amount
│   ├── created_at
│   └── (subcollection) deductions/{deduction_id}
│       ├── id
│       ├── type
│       ├── amount
│       ├── confidence
│       └── (subcollection) verification_result
│           ├── id
│           ├── status
│           ├── confidence
│           └── (subcollection) agent_findings
│
├── verification_results/{result_id}
│   ├── settlement_id
│   ├── deduction_id
│   ├── status
│   ├── confidence
│   └── agent_investigation
│
├── settlement_decisions/{decision_id}
│   ├── settlement_id
│   ├── decision
│   ├── confidence
│   └── reason
│
├── evidence_links/{link_id}
│   ├── deduction_id
│   ├── evidence_document_id
│   ├── confidence
│   └── match_type
│
└── audit_events/{event_id}
    ├── settlement_id
    ├── action
    ├── resource_type
    ├── resource_id
    ├── details
    ├── outcome
    └── timestamp
```

### 5.2 Local Filesystem Storage (MVP Demo)

```
storage/
├── uploads/
│   ├── {document_id}.pdf
│   └── {document_id}.metadata.json
├── ocr/
│   ├── {document_id}.txt
│   └── {document_id}.json (structured)
├── settlements/
│   └── {settlement_id}.json
├── audits/
│   └── {settlement_id}_audit.json
└── verifications/
    └── {settlement_id}_verification.json
```

---

## 6. Service Interfaces

### 6.1 DocumentService

```python
class DocumentService:
    def create_upload_intent(owner_uid: str, filename: str, size: int) -> UploadIntent
    def complete_upload(document_id: str, owner_uid: str) -> Document
    def get_document(document_id: str, owner_uid: str) -> Document
    def list_documents(owner_uid: str, limit: int) -> List[Document]
```

### 6.2 SettlementService

```python
class SettlementService:
    def create_settlement(settlement: Settlement) -> Settlement
    def get_settlement(settlement_id: str, owner_uid: str) -> Settlement
    def list_settlements(owner_uid: str, limit: int) -> List[Settlement]
```

### 6.3 ExtractionService

```python
class SettlementExtractionService:
    def extract(ocr_text: str) -> Settlement
    def extract_deductions(ocr_text: str) -> List[SettlementDeduction]
```

### 6.4 VerificationService

```python
class DeterministicVerifier:
    def verify(deduction: SettlementDeduction, settlement: Settlement) -> VerificationResult

class SettlementFinanceAgent:
    async def investigate_deduction(deduction, settlement, context) -> VerificationResult
```

### 6.5 BatchProcessor

```python
class BatchSettlementProcessor:
    def process_settlements(owner_uid: str, specs: List[SettlementSpec]) -> (BatchMetrics, List[Result])
```

---

## 7. Error Handling

### 7.1 Error Categories

**400 Bad Request**
- Invalid request format
- Missing required fields
- File too large

**401 Unauthorized**
- No authentication header
- Invalid credentials

**403 Forbidden**
- User does not own resource
- Access denied

**404 Not Found**
- Resource does not exist

**500 Internal Server Error**
- Unexpected exception
- OCR failure (retriable)
- Agent API failure (retriable)

### 7.2 Retry Strategy

**Retriable Errors:**
- 408 Request Timeout
- 429 Too Many Requests
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable

**Retry Policy:**
- Max 3 attempts
- Exponential backoff (1s, 2s, 4s)
- Timeout: 30s per attempt

---

## 8. Security Design

### 8.1 Authentication

**Demo Mode:**
```
Header: X-Demo-User-ID: demo-user-1
No validation; session-only
```

**Firebase Mode:**
```
Header: Authorization: Bearer <id_token>
Verify token signature via Firebase SDK
Extract uid from token claims
```

### 8.2 Authorization

**Data Isolation:**
- All queries filtered by owner_uid
- User can only access own documents/settlements

**No Cross-User Access:**
- GET /settlements/{id} returns 403 if owner_uid != current_user

### 8.3 Secrets Management

**Environment Variables:**
```bash
FIREBASE_SERVICE_ACCOUNT_JSON    # Never committed
ANTHROPIC_API_KEY                # Never committed
CORS_ALLOWED_ORIGINS             # Configurable per environment
```

**Demo Mode:**
- No secrets needed
- Safe for open-source

---

## 9. Testing Strategy

### 9.1 Test Levels

**Unit Tests:**
- Settlement extraction logic
- Deduction verification rules
- Evidence matching algorithm
- Agent response parsing

**Integration Tests:**
- Document upload → OCR → extraction
- Settlement processing pipeline
- Batch processing flow
- Audit trail logging

**End-to-End Tests:**
- Frontend upload → backend processing → results display
- Batch demo runner
- Demo auth flow

### 9.2 Test Coverage Targets

- Overall: ≥75%
- Critical paths: 100%
  - Settlement extraction
  - Deterministic verification
  - Decision synthesis

### 9.3 Test Data

**Fixtures:**
- Sample settlement PDFs
- Pre-extracted OCR text
- Synthetic deductions
- Evidence documents

**Benchmark:**
- 50-record demo dataset
- Diverse outcomes (APPROVE, FLAG, ESCALATE)
- Known expected metrics

---

## 10. Deployment Architecture

### 10.1 Development

```
docker-compose up -d
├── API (localhost:8000)
├── Frontend (localhost:3000)
├── Worker (background)
└── Ollama (optional, not used in MVP)
```

### 10.2 Volumes

```yaml
services:
  api:
    volumes:
      - upload-artifacts:/app/storage/uploads
      - ocr-artifacts:/app/storage/ocr
      - audits-artifacts:/app/storage/audits
  worker:
    volumes:
      - upload-artifacts:/app/storage/uploads
      - ocr-artifacts:/app/storage/ocr
```

---

## 11. Performance Considerations

### 11.1 Optimization Strategies

**Frontend:**
- Lazy load results (pagination)
- Client-side filtering/sorting
- Cache settlement results
- Async file upload

**Backend:**
- Parallel deduction processing (asyncio)
- Evidence matching indexed by date range
- Batch verification (bulk operations)
- Async OCR processing

**Storage:**
- Index settlements by owner_uid and created_at
- Index audit events by settlement_id
- Compress old audit records

### 11.2 Monitoring Points

- API response times (p50, p95, p99)
- OCR processing time
- Verification rule execution time
- Agent investigation latency
- Batch throughput (settlements/second)
- Error rate by endpoint

---

## 12. Design Decisions

| Decision | Rationale | Alternative |
|---|---|---|
| REST API (not GraphQL) | Simpler, faster to build | GraphQL (more complex) |
| Async FastAPI | Non-blocking I/O, better throughput | Sync Flask (lower performance) |
| PaddleOCR (not Tesseract) | Better accuracy, multilingual | Tesseract (lower accuracy) |
| Demo mode built-in | No credentials for MVP | Firebase-only (requires setup) |
| Firestore optional | Demo works with local filesystem | Firestore-only (harder to test) |
| Single async worker | Simpler deployment | Multiple workers (complex) |

---

**Status:** Approved  
**Last Updated:** January 6, 2025
