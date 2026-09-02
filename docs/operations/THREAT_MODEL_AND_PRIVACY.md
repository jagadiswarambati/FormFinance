# Closed-Beta Threat Model and Privacy Wording

This operational document implements the frozen SDD’s closed-beta safety requirements. It does not replace the SDD or the deployment-specific legal privacy notice.

## Scope and assets

FormWise AI processes original uploads, OCR artifacts, protected text/layout, immutable structured documents, approved safe assignments, rendered artifacts, and response-safe lifecycle metadata. Original uploads and sensitive values are never AI inputs. The browser is untrusted; Firebase ID tokens are verified by the API; Firestore, local development storage, and workers are trusted service boundaries only after their configured credentials are validated.

## Threat model

| Threat                            | Boundary                 | Required control                                                                   | Release evidence                                     |
| --------------------------------- | ------------------------ | ---------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Account takeover or IDOR          | API authorization        | Firebase token verification and owner-scoped repository access                     | Authorization and IDOR tests pass                    |
| Malicious upload                  | Upload/quarantine        | Type/size validation, quarantine state, fail-closed scan gate                      | Quarantine workflow exercised with synthetic fixture |
| Sensitive data reaching AI        | Privacy gateway          | Classification, redaction/quarantine, SAFE-only structured context                 | Privacy/redaction and prompt-boundary tests pass     |
| Prompt injection in document text | AI boundary              | Uploaded text is untrusted data; structured output schema and no tools             | Prompt-injection test passes                         |
| Stale/incorrect rendering         | Rendering boundary       | Immutable Field Map v1, approved assignments only, deterministic widget references | Golden rendering corpus passes                       |
| Unauthorized artifact download    | Download API             | Authentication, ownership validation, completed-record requirement                 | Download authorization test passes                   |
| Excessive retention               | Retention worker         | Immediate access revocation, durable purge queue, completion verification          | Retention retry and deletion verification pass       |
| Service outage/backlog            | Worker/provider boundary | Configured timeouts, retry backoff, dead-letter records, readiness and heartbeats  | Readiness and runbook checks complete                |

## Product privacy wording

Use the following wording in closed-beta product and support communications only after legal approval for the deployment region:

> FormWise AI is designed to process forms with privacy controls. Sensitive and restricted values are excluded from AI processing. The AI receives only the protected structured information needed for a supported task. We show privacy-status information for processed conversations and revoke access before asynchronous deletion. FormWise AI retains no more than five conversations per user while they remain active.

Do not claim that a document is anonymous, that all possible sensitive data can be detected, or that deletion is physically immediate. State that supported document types and limits apply, processing may be delayed or unavailable during provider outages, and a deletion request revokes access before purge completion.

## Supported documents and limits

The closed beta supports PDF, PNG, JPG, and JPEG uploads up to 10 MB. Processing is limited to the documented supported fixture corpus and configured OCR/rendering capabilities. Password-protected, corrupt, unsupported, or ambiguous documents must fail safely or remain manual-only; they must not be silently transformed into another document type.

## Backup and retention policy

- Production backup location, region, encryption, retention period, restore owner, and deletion handling must be recorded in the release approval.
- Backups must be access-controlled and covered by the same incident process as production data.
- A purge request revokes access immediately. Backup expiration or deletion must follow the approved backup retention period; do not state that backup copies disappear immediately.
- The release approver must confirm that backup retention is compatible with the product privacy wording and applicable obligations.
