# Privacy Engine

Milestone 5 adds a deterministic policy gate between OCR and every future AI provider. It does not add an AI call.

## Workflow

```text
Immutable upload → PaddleOCR artifact → privacy scan → policy report
                                                     ├─ BLOCK → manual-only
                                                     ├─ ASK_USER → protected-processing consent
                                                     └─ REDACT/ALLOW → protected text ready
```

The scanner detects configured government, financial, personal, and medical identifier patterns. A finding has an internal category, confidence, matched span, and action. Matched values and positions are never put in Firestore, logs, API responses, or the UI.

Policy actions are `ALLOW`, `REDACT`, `ASK_USER`, and `BLOCK`. `ASK_USER` is consent to continue only with already protected text; it never permits the original OCR artifact or a raw detected value to reach an AI provider. `BLOCK` makes the document manual-only.

## Stored metadata

`documents/{documentId}` receives `privacyStatus`, `privacyCompletedAt`, `privacyPolicyVersion`, `piiCategories`, `redactedTextStorageKey`, and `consentDecision`. The separate `privacy_reports/{documentId}` document stores only aggregate category/count/action results. Protected OCR text is written to the local development privacy store; the original upload and original OCR artifact remain unchanged.

## API

- `POST /api/v1/documents/{documentId}/privacy/scan` scans a completed OCR artifact.
- `GET /api/v1/documents/{documentId}/privacy` returns the owner-authorized report.
- `POST /api/v1/documents/{documentId}/privacy/consent` records `continue_with_redaction`, `continue_protected`, or `cancel` for an `ASK_USER` report.

All routes require a verified Firebase bearer token and enforce document ownership.
