# FormFinance — Development Guidelines

**Version:** 1.0  
**Date:** January 2025  

---

## 1. Development Environment Setup

### 1.1 Prerequisites

```bash
# Python 3.13+
python --version

# Node 20+
node --version
npm --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### 1.2 Backend Setup

```bash
# Clone repository
git clone <repo_url>
cd FormFinance-main

# Install Python dependencies
cd services/api
uv sync

# Run backend
uv run uvicorn formwise_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 1.3 Frontend Setup

```bash
# From repo root
cd apps/web

# Install dependencies
npm install

# Run dev server
npm run dev

# Visit http://localhost:3000
```

### 1.4 Worker Setup

```bash
# From repo root
cd services/worker

# Install dependencies
uv sync

# Run worker (separate terminal)
uv run python -m formwise_worker.jobs
```

---

## 2. Code Style & Standards

### 2.1 Python (Backend)

**Style Guide:** PEP 8  
**Formatter:** Black (auto-format)  
**Linter:** Pylint  
**Type Checker:** mypy  

```bash
# Format code
black services/api/src/

# Run linter
pylint services/api/src/formwise_api/

# Type check
mypy services/api/src/formwise_api/

# All together
make lint
```

**Code Style Rules:**
- Max line length: 100 characters
- Use type hints on all functions
- Docstrings on all classes and public functions
- Use async/await for I/O operations
- Use dependency injection (FastAPI Depends)

**Example:**
```python
from typing import Optional
from fastapi import HTTPException, status

async def get_settlement(
    settlement_id: str,
    owner_uid: str,
    settlement_repo: SettlementRepository = Depends(get_settlement_repository),
) -> Settlement:
    """
    Retrieve a settlement by ID.
    
    Args:
        settlement_id: Unique settlement identifier
        owner_uid: Owner user ID (for authorization)
        settlement_repo: Settlement repository (injected)
    
    Returns:
        Settlement object
    
    Raises:
        HTTPException: If settlement not found or unauthorized
    """
    settlement = settlement_repo.get(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.owner_uid != owner_uid:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return settlement
```

### 2.2 TypeScript (Frontend)

**Style Guide:** ESLint + Prettier  
**Formatter:** Prettier (auto-format)  
**Linter:** ESLint  

```bash
# Format code
npm run format

# Run linter
npm run lint

# Type check
npm run typecheck
```

**Code Style Rules:**
- Max line length: 100 characters
- Use strict TypeScript (`strict: true`)
- Use functional components + hooks
- Use named exports
- Avoid `any` type

**Example:**
```typescript
import React, { useState, FC } from 'react';

interface SettlementProps {
  settlementId: string;
  onProcessed?: (result: SettlementResult) => void;
}

const SettlementProcessor: FC<SettlementProps> = ({ settlementId, onProcessed }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (): Promise<void> => {
    try {
      setLoading(true);
      const result = await processSettlement(settlementId);
      onProcessed?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleProcess} disabled={loading}>
      {loading ? 'Processing...' : 'Process Settlement'}
    </button>
  );
};

export default SettlementProcessor;
```

---

## 3. Git Workflow

### 3.1 Branch Naming

**Format:** `<type>/<description>`

**Types:**
- `feature/` — New feature
- `fix/` — Bug fix
- `docs/` — Documentation
- `refactor/` — Code refactoring
- `test/` — Test improvements

**Examples:**
```
feature/settlement-extraction
fix/evidence-matching-bug
docs/api-documentation
refactor/verification-service
test/batch-processing-tests
```

### 3.2 Commit Messages

**Format:** Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
```
feat(settlements): add deterministic verification rules

- Implement fee validation (0-5% of gross)
- Implement tax rate validation (5%, 12%, 18%)
- Add audit logging for each rule

Closes #123

---

fix(evidence): handle missing reference IDs

Previously, missing reference IDs caused verification to fail.
Now we gracefully handle missing IDs and continue processing.

---

docs(api): update settlement endpoints documentation
```

### 3.3 Pull Request Process

1. **Create branch** from `main`
2. **Make changes** (small, focused commits)
3. **Push to remote**
4. **Open PR** with description
5. **Code review** (1+ approvals required)
6. **CI/CD checks** pass (lint, test, build)
7. **Merge** to main

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## 4. Testing Requirements

### 4.1 Unit Tests

**Location:** `services/api/tests/`

**Example:**
```python
import pytest
from formwise_api.settlements.deterministic_verifier import DeterministicVerifier

@pytest.fixture
def verifier():
    return DeterministicVerifier()

def test_fee_verification_valid(verifier):
    """Test fee verification with valid fee (2.5% of gross)."""
    deduction = SettlementDeduction(
        id="ded_001",
        type="fee",
        amount=2500,
        description="Platform fee 2.5%",
        confidence=0.95
    )
    settlement = Settlement(
        id="settlement_001",
        gross_amount=100000,
        net_amount=97500
    )
    
    result = verifier.verify(deduction, settlement)
    
    assert result.status == "verified"
    assert result.confidence >= 0.90

def test_fee_verification_invalid(verifier):
    """Test fee verification with invalid fee (10% exceeds max)."""
    deduction = SettlementDeduction(
        type="fee",
        amount=10000,  # 10% of gross
        confidence=0.95
    )
    settlement = Settlement(gross_amount=100000)
    
    result = verifier.verify(deduction, settlement)
    
    assert result.status == "disputed"
```

### 4.2 Integration Tests

**Location:** `services/api/tests/integration/`

**Example:**
```python
@pytest.mark.asyncio
async def test_settlement_processing_pipeline(client, db):
    """Test end-to-end settlement processing."""
    # 1. Upload document
    response = client.post("/api/v1/documents/upload-intents", json={
        "originalFilename": "settlement.pdf",
        "contentType": "application/pdf",
        "fileSize": 1024
    })
    document_id = response.json()["documentId"]
    
    # 2. Complete upload
    client.post(f"/api/v1/documents/{document_id}/complete")
    
    # 3. Process settlement
    ocr_text = "... settlement OCR text ..."
    response = client.post("/api/v1/settlements/process-document", json={
        "documentId": document_id,
        "ocrText": ocr_text,
        "evidenceDocumentIds": []
    })
    
    result = response.json()
    assert result["decision"]["decision"] in ["approve", "flag", "escalate"]
    assert len(result["auditTrail"]) > 0
```

### 4.3 Running Tests

```bash
# All tests
cd services/api
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_settlement_extraction.py -v

# With coverage
uv run pytest tests/ --cov=formwise_api --cov-report=html

# Watch mode (requires pytest-watch)
uv run ptw tests/
```

---

## 5. Logging & Debugging

### 5.1 Logging Configuration

**Backend (Python):**
```python
import logging

logger = logging.getLogger(__name__)

# Usage
logger.info(f"Processing settlement {settlement_id}")
logger.warning(f"Low confidence extraction: {confidence}")
logger.error(f"Settlement processing failed: {error}", exc_info=True)
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: Confirmation that things are working
- `WARNING`: Something unexpected but non-critical
- `ERROR`: Serious problem; feature not working
- `CRITICAL`: Very serious; system may fail

### 5.2 Docker Logs

```bash
# View logs for all services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# With timestamps
docker-compose logs -f --timestamps
```

### 5.3 Debugging

**Backend:**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()
```

**Frontend:**
```typescript
// Browser DevTools Console
console.log("Debug info:", variable);
debugger;  // Breakpoint
```

---

## 6. Performance Profiling

### 6.1 Backend Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code to profile
result = settlement_processor.process(settlement)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10
```

### 6.2 Timing Measurements

```python
import time

start = time.time()
# Code to measure
elapsed = time.time() - start
logger.info(f"Settlement processing took {elapsed:.3f}s")
```

---

## 7. Database Migrations (Firestore)

### 7.1 Schema Evolution

When modifying Firestore collections:

1. **Document the change** in `docs/DATABASE_CHANGES.md`
2. **Create migration script** if needed
3. **Test on dev Firestore**
4. **Apply to production** with backup
5. **Update code** to handle both old and new schema

**Example Migration:**
```python
def migrate_add_confidence_field():
    """Add confidence field to existing verification results."""
    db = firestore.client()
    results = db.collection('verification_results').stream()
    
    batch = db.batch()
    for doc in results:
        if 'confidence' not in doc.to_dict():
            batch.update(doc.reference, {'confidence': 0.75})
    
    batch.commit()
```

---

## 8. Configuration Management

### 8.1 Environment Variables

**Backend (.env):**
```bash
FORMWISE_ENV=development
DEMO_AUTH_ENABLED=true
LOG_LEVEL=DEBUG
CORS_ALLOWED_ORIGINS=http://localhost:3000
API_PREFIX=/api/v1
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEMO_AUTH_ENABLED=true
```

### 8.2 Loading Configuration

**Python:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    formwise_env: str = "development"
    demo_auth_enabled: bool = False
    
    class Config:
        env_file = ".env"
```

**TypeScript:**
```typescript
// Environment variables must start with NEXT_PUBLIC_ to be available in browser
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
```

---

## 9. Documentation

### 9.1 Code Documentation

**Docstring Format (Python):**
```python
def verify_settlement(settlement_id: str) -> SettlementDecision:
    """
    Verify all deductions in a settlement.
    
    Runs deterministic checks on each deduction. For unverifiable
    deductions, invokes AI agent investigation if configured.
    
    Args:
        settlement_id: Unique settlement identifier
    
    Returns:
        SettlementDecision with APPROVE/FLAG/ESCALATE outcome
    
    Raises:
        SettlementNotFoundError: If settlement doesn't exist
        VerificationError: If verification fails
    
    Example:
        >>> decision = verify_settlement("settlement_001")
        >>> print(decision.decision)
        "approve"
    """
```

**JSDoc Format (TypeScript):**
```typescript
/**
 * Process a settlement document end-to-end.
 * 
 * @param documentId - The uploaded document ID
 * @param ocrText - Extracted OCR text from document
 * @returns Promise resolving to settlement result
 * @throws SettlementProcessingError if processing fails
 * 
 * @example
 * const result = await processSettlement("doc_123", "OCR text...");
 * console.log(result.decision);
 */
async function processSettlement(
  documentId: string,
  ocrText: string
): Promise<SettlementResult> { ... }
```

### 9.2 API Documentation

**Use inline comments:**
```python
@router.post(
    "/process-document",
    response_model=ProcessSettlementDocumentResponse,
    tags=["settlements"]
)
async def process_settlement_document(
    payload: ProcessSettlementDocumentRequest,
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
) -> ProcessSettlementDocumentResponse:
    """
    Process a settlement document end-to-end.
    
    Complete workflow:
    1. Load settlement document (FormWise)
    2. Extract OCR text
    3. Parse settlement structure
    4. Find/link evidence documents
    5. Run verification (deterministic + AI)
    6. Generate decision
    7. Log audit trail
    
    Returns: Settlement with decision and audit trail
    """
```

---

## 10. Release Checklist

Before releasing a version:

- [ ] All tests passing (unit + integration + E2E)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with new features/fixes
- [ ] Version bumped (semantic versioning)
- [ ] Docker images built successfully
- [ ] Demo mode tested end-to-end
- [ ] Performance benchmarks acceptable
- [ ] No new security vulnerabilities
- [ ] Release notes prepared

---

## 11. Common Development Tasks

### 11.1 Add New Deduction Type

1. **Update verification rules:**
   ```python
   # deterministic_verifier.py
   if deduction.type == "new_type":
       return self._verify_new_type(deduction, settlement)
   ```

2. **Add test:**
   ```python
   def test_verify_new_type():
       deduction = SettlementDeduction(type="new_type", ...)
       result = verifier.verify(deduction, settlement)
       assert result.status == "verified"
   ```

3. **Update documentation**

### 11.2 Change Settlement Extraction Logic

1. **Update extraction service:**
   ```python
   # extraction_service.py
   def extract(self, ocr_text: str) -> Settlement:
       # ... new extraction logic
   ```

2. **Add test with sample OCR text:**
   ```python
   def test_extract_settlement():
       ocr_text = "... sample OCR ..."
       settlement = extractor.extract(ocr_text)
       assert settlement.gross_amount == 100000
   ```

3. **Test against benchmark data**

### 11.3 Modify API Endpoint

1. **Update models:**
   ```python
   class ProcessSettlementDocumentRequest(BaseModel):
       document_id: str
       ocr_text: str
       new_field: Optional[str] = None  # New field
   ```

2. **Update handler:**
   ```python
   async def process_settlement_document(payload: ProcessSettlementDocumentRequest):
       # Use payload.new_field
   ```

3. **Update frontend:**
   ```typescript
   interface ProcessSettlementRequest {
     documentId: string;
     ocrText: string;
     newField?: string;
   }
   ```

4. **Update tests and documentation**

---

**Status:** Active  
**Last Updated:** January 6, 2025
