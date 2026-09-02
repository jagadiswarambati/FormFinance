# FormWise AI Closed-Beta Release Gate

This checklist must be completed against the exact immutable release revision. A failed or unverified item blocks closed-beta deployment until an authorized owner records an exception outside this repository.

## Required confirmations

- [ ] **Security baseline:** strict CORS, security headers, correlation IDs, stable safe errors, and PII-safe structured logs are enabled.
- [ ] **Privacy controls:** Privacy Engine gating, SAFE-only AI context, response-safe privacy dashboard, and prompt-injection controls are verified.
- [ ] **Retention:** quota selection, immediate revocation, durable purge queue, retry handling, audit events, and deletion verification are verified.
- [ ] **Rendering:** Field Map v1 validation, deterministic native-widget dereferencing, renderer isolation, validation, and stale-publication safety are verified.
- [ ] **Download:** authenticated ownership check and shared artifact access are verified.
- [ ] **Accessibility:** keyboard navigation, focus management, semantic controls, alerts/statuses, dialog behavior, labels, and contrast checks are complete for implemented UI surfaces.
- [ ] **Observability:** `/health`, `/ready`, dependency health, worker heartbeat, queue depth, timeout/retry, and dead-letter signals are observed in the target environment.
- [ ] **Testing:** unit, security, synthetic golden, storage/OCR/render/retention, emulator, and closed-beta E2E suites are run or explicitly marked unavailable with an approved release decision.
- [ ] **Readiness:** production configuration, secrets, region, provider, backup/retention, monitoring, rollback, and runbook ownership are confirmed.

## Approval record

| Role              | Name | Date | Approval/reference |
| ----------------- | ---- | ---- | ------------------ |
| Product owner     |      |      |                    |
| Engineering owner |      |      |                    |
| Security owner    |      |      |                    |
| Privacy owner     |      |      |                    |
| Operations owner  |      |      |                    |
