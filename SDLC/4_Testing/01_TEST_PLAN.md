# FormFinance — Test Plan

**Version:** 1.0  
**Date:** January 2025  

---

## 1. Testing Strategy

### 1.1 Test Levels

| Level | Scope | Tools | Coverage |
|---|---|---|---|
| **Unit** | Individual functions/methods | pytest, Jest | ≥80% |
| **Integration** | Component interactions | pytest, supertest | ≥75% |
| **End-to-End** | Complete workflows | Playwright, Cypress | ≥60% |
| **Performance** | Response times, throughput | locust, k6 | Key paths |
| **Security** | Auth, data isolation | OWASP ZAP | Critical flows |

### 1.2 Test Coverage Targets

- **Overall:** ≥75% code coverage
- **Critical paths:** 100%
  - Settlement extraction
  - Deterministic verification
  - Decision synthesis
  - Audit logging

---

## 2. Unit Tests

### 2.1 Backend Unit Tests

**Location:** `services/api/tests/`

**Test Categories:**

#### Settlement Extraction
- Extract settlement from OCR text
- Parse amounts, dates, deductions
- Handle missing fields
- Handle malformed text

#### Deduction Classification
- Classify deduction types
- Set confidence scores
- Extract reference IDs and dates

#### Deterministic Verification
- Verify fee (0-5% of gross)
- Verify tax (known rates)
- Verify chargeback (has evidence)
- Verify adjustment (has reason)

#### Evidence Matching
- Match by date proximity
- Match by amount
- Match by reference number
- Compute confidence

#### Audit Trail
- Log extraction events
- Log verification results
- Log agent investigation
- Log final decision

**Run Tests:**
```bash
cd services/api
uv run pytest tests/ -v
uv run pytest tests/ --cov=formwise_api --cov-report=html
```

### 2.2 Frontend Unit Tests

**Location:** `apps/web/tests/`

**Test Categories:**

#### Components
- SettlementProcessor (upload, progress, results)
- DocumentUpload (file validation)
- SettlementResults (display verification)

#### Utilities
- API client functions
- Auth context (demo mode + Firebase)
- Format utilities (currency, dates)

#### Hooks
- useAuth
- useSettlement
- useBatchDemo

**Run Tests:**
```bash
cd apps/web
npm run test
npm run test -- --coverage
```

---

## 3. Integration Tests

### 3.1 API Integration Tests

**Workflow:**
1. Upload document
2. Complete upload (trigger OCR)
3. Wait for OCR completion
4. Process settlement
5. Verify results

**Test:**
```python
@pytest.mark.asyncio
async def test_complete_settlement_workflow(client, db):
    # Step 1-4
    # Assertions
    assert response.status_code == 200
    assert result["decision"]["decision"] in ["approve", "flag", "escalate"]
    assert len(result["auditTrail"]) >= 4
```

### 3.2 Batch Processing Integration

**Test:**
- Process 50+ settlements
- Verify metrics accuracy
- Check exception handling
- Verify audit trail for each

---

## 4. End-to-End Tests

### 4.1 Frontend E2E

**Scenario 1: Upload and Process**
1. Navigate to upload page
2. Select PDF file
3. Click upload
4. Wait for completion
5. Verify extracted data displayed
6. Click process
7. Verify decision displayed
8. Check audit trail

**Scenario 2: Batch Demo**
1. Click "Batch Demo" button
2. Wait for processing
3. Verify metrics displayed
4. Check result table

**Tools:**
```bash
# Playwright (recommended for Next.js)
npx playwright test

# OR Cypress
npx cypress run
```

---

## 5. Performance Tests

### 5.1 Load Testing

**Tool:** k6 or locust

**Scenarios:**
- Concurrent settlement uploads (10 users)
- Batch processing (1,000 settlements)
- API endpoint stress test (100 req/s)

**Metrics:**
- Response time (p50, p95, p99)
- Error rate
- Throughput

**Target:** <100ms p95 for single settlement

### 5.2 Benchmark Metrics

```bash
uv run python run_benchmark.py
```

**Expected Output:**
```
Total Records:               50
Processed:                   50
Extraction Success Rate:     100.0%
Verification Rate:           93.3%
Processing Duration:         ~2.5s
Throughput:                  ~20 records/sec
```

---

## 6. Security Tests

### 6.1 Authentication

- ✅ Demo mode works without credentials
- ✅ Firebase auth verified correctly
- ✅ Invalid tokens rejected (401)
- ✅ Missing auth header rejected (401)

### 6.2 Authorization

- ✅ User can only access own settlements
- ✅ Cross-user access blocked (403)
- ✅ User cannot modify other user's audit trail

### 6.3 API Security

- ✅ No SQL injection possible (Pydantic validation)
- ✅ No path traversal (document ID validation)
- ✅ CORS allows only configured origins
- ✅ Sensitive headers not exposed

---

## 7. Regression Tests

### 7.1 Critical Paths

Run on every commit:

- Settlement extraction (known OCR text)
- Deterministic verification (known rules)
- Decision synthesis (known results)
- Batch processing (50-record demo)

### 7.2 Test Data

Keep stable test fixtures:
```
tests/fixtures/
├── settlement_ocr.txt          # Sample OCR
├── settlement.json             # Expected parsed result
├── deductions.json             # Expected deductions
└── decisions.json              # Expected decisions
```

---

## 8. Test Execution

### 8.1 Local Testing

```bash
# Backend
cd services/api
uv run pytest tests/ -v

# Frontend
cd apps/web
npm run test

# E2E (if implemented)
npm run test:e2e

# Benchmark
uv run python run_benchmark.py
```

### 8.2 CI/CD Testing (GitHub Actions)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run backend tests
        run: |
          cd services/api
          uv sync
          uv run pytest tests/ --cov
      
      - name: Run frontend tests
        run: |
          cd apps/web
          npm install
          npm run test
```

---

## 9. Test Results Reporting

### 9.1 Coverage Report

```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=formwise_api --cov-report=html
open htmlcov/index.html
```

### 9.2 Test Report

```bash
# JUnit format for CI
uv run pytest tests/ --junit-xml=test-results.xml
```

---

## 10. Known Issues & Workarounds

| Issue | Status | Workaround |
|---|---|---|
| OCR on handwritten text | Known limitation | Use typed/printed PDFs |
| Large PDF processing (>50MB) | Not tested | Implement chunking |
| Non-Latin character OCR | Performance varies | Specify language in PaddleOCR |

---

**Status:** Active  
**Last Updated:** January 6, 2025
