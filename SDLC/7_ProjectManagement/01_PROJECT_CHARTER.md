# FormFinance Project Charter

**Project Name:** FormFinance — AI Finance Controller  
**Version:** 1.0  
**Date:** January 6, 2025  
**Status:** Active  

---

## 1. Project Overview

**Objective:** Develop an automated settlement verification and reconciliation system powered by OCR, deterministic rules, and AI-driven investigation.

**Business Case:** Manual settlement reconciliation consumes 40+ hours per 1,000 settlements. FormFinance automates this workflow, reducing processing time from hours to seconds while maintaining auditability and accuracy.

**Target Launch:** Razorpay AI Buildathon 2026 (January 2025)

**Track:** AI Finance Controller (Track 04)

---

## 2. Project Scope

### In Scope
- Settlement document ingestion (PDF uploads)
- OCR extraction via PaddleOCR
- Settlement structure parsing (amounts, dates, deductions)
- Deterministic verification (rule-based checks)
- Evidence matching (deduction ↔ document linking)
- AI finance agent (LLM-based investigation for ambiguous cases)
- Final decision generation (APPROVE / FLAG / ESCALATE)
- Audit trail logging
- Batch processing (50+ settlements)
- Frontend UI (upload, results, history, batch demo)
- Backend API (REST endpoints)

### Out of Scope
- Real-time Razorpay settlement API integration
- Production-grade database (Firestore setup deferred to Phase 2)
- Multi-tenancy support (single user/org for MVP)
- Machine learning model training
- Regulatory reporting exports
- Multi-level approval workflows

---

## 3. Success Criteria

| Criterion | Target | Status |
|---|---|---|
| Settlement extraction accuracy | ≥95% | In Progress |
| Deduction verification rate | ≥90% | In Progress |
| Evidence match rate | ≥85% | In Progress |
| End-to-end processing time | <100ms per settlement | In Progress |
| Batch throughput | ≥15 settlements/sec | In Progress |
| Decision accuracy (APPROVE/FLAG/ESCALATE) | ≥92% | In Progress |
| Agent investigation success (when unresolved) | ≥80% | In Progress |
| Code coverage | ≥75% | In Progress |
| Demo readiness (no credentials needed) | 100% | Complete ✅ |

---

## 4. Stakeholders

| Role | Name | Responsibility |
|---|---|---|
| **Project Manager** | [Your Name] | Overall project delivery |
| **Tech Lead** | [Your Name] | Architecture, decisions |
| **Frontend Lead** | [Your Name] | Next.js/React implementation |
| **Backend Lead** | [Your Name] | FastAPI/Python implementation |
| **QA Lead** | [Your Name] | Testing, validation |
| **Razorpay Contact** | [Buildathon Organizer] | Track requirements, judging |

---

## 5. Key Deliverables

1. ✅ **README.md** — Comprehensive project documentation
2. ✅ **Frontend (Next.js)** — Settlement UI, upload, results
3. ✅ **Backend API (FastAPI)** — REST endpoints, business logic
4. ✅ **OCR Worker** — PaddleOCR processing
5. ✅ **Finance Agent** — LLM-based investigation
6. ✅ **Docker Setup** — docker-compose orchestration
7. ✅ **Test Suite** — Unit, integration, end-to-end tests
8. ✅ **Deployment Guide** — Setup and running instructions
9. ✅ **Demo Data** — 50-record synthetic benchmark

---

## 6. Timeline

| Phase | Duration | Dates | Status |
|---|---|---|---|
| **Requirements & Design** | 2 days | Jan 1-2 | ✅ Complete |
| **Core Development** | 5 days | Jan 3-7 | ✅ Complete |
| **Integration & Testing** | 3 days | Jan 8-10 | ✅ Complete |
| **Demo & Refinement** | 2 days | Jan 11-12 | 🔄 In Progress |
| **Submission** | 1 day | Jan 13 | ⏳ Ready |

---

## 7. Budget & Resources

**Development Team:** 2-3 engineers  
**Timeline:** 2-week sprint  
**Infrastructure:** Docker, local storage (demo)  
**External Services:** Anthropic API (optional for agent)  

**Cost Estimate:**
- Development: ~80 hours @ $100/hr = $8,000
- Infrastructure: ~$500 (dev/demo only)
- **Total:** ~$8,500

---

## 8. Risk Management

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| OCR accuracy on varied PDFs | High | Medium | Test with diverse settlement formats; fallback to manual review |
| LLM latency for agent investigation | Medium | Low | Implement caching; timeout handling |
| Firebase setup delays | Medium | Low | Use demo auth for MVP; defer to Phase 2 |
| Batch processing performance | Medium | Medium | Optimize extraction/verification; profile early |

---

## 9. Assumptions

1. Razorpay provides clear settlement document format/samples
2. AI provider (Anthropic) API is available and stable
3. No real Razorpay integration required for MVP (synthetic data acceptable)
4. Demo mode sufficient for hackathon judging (no production auth needed)
5. Docker environment available for deployment

---

## 10. Constraints

- **Timeline:** Must complete by Razorpay AI Buildathon deadline (Jan 13, 2025)
- **Technology Stack:** Locked to Next.js, FastAPI, PaddleOCR, Anthropic
- **Data:** Only synthetic/demo data (no real financial records)
- **Scale:** MVP tested with 50+ settlements (not production-scale)

---

## 11. Approvals

| Stakeholder | Signature | Date |
|---|---|---|
| Project Manager | _________________ | _________ |
| Tech Lead | _________________ | _________ |
| Product Owner | _________________ | _________ |

---

**Project Status:** 🟢 On Track  
**Last Updated:** January 6, 2025  
**Next Review:** January 10, 2025
