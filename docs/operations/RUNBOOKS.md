# Closed-Beta Operational Runbooks

All runbooks use PII-safe logs, request IDs, worker health records, queue depth, and stable error codes. Never place document content, OCR output, assignment values, prompts, responses, artifact paths, service-account material, or tokens in tickets or logs.

## Worker failure recovery

1. Check `/api/v1/ready`, worker-heartbeat freshness, queue depth, and dead-letter metadata.
2. Verify the worker has the production configuration and can reach Firestore, configured storage, and its enabled provider.
3. Restart only the affected worker instance through the deployment platform; do not alter queued document payloads.
4. Confirm a fresh heartbeat and that queued jobs resume. Inspect terminal jobs by identifier and error code only.
5. Escalate repeated terminal failures to the incident owner; preserve audit metadata.

## Queue backlog recovery

1. Identify the affected queue (OCR, rendering, or retention) from queue-depth metrics.
2. Check dependency readiness and dead-letter rates before increasing configured worker concurrency.
3. Increase capacity only within the configured concurrency/memory limit and monitor timeout rates.
4. Do not bypass quarantine, privacy, validation, or retention ordering to clear a backlog.
5. Return capacity to the approved baseline after the queue remains stable.

## Firestore outage

1. Mark the service unavailable through deployment incident controls; `/ready` should return not ready.
2. Do not manually recreate job, retention, or audit records from logs.
3. Wait for the provider to recover, validate authenticated read/write access with a non-content health check, then restart affected workers.
4. Confirm queued work is claimed once and reconcile terminal failures through identifiers and status only.

## Storage outage

1. Stop accepting uploads if quarantine or upload storage is unavailable.
2. Do not move, copy, or manually reconstruct artifacts while storage health is failing.
3. Restore shared API/worker access to the configured storage location.
4. Verify storage using a synthetic artifact, then resume queues. Requeue only retryable identifier-only jobs.

## AI provider outage

1. Confirm provider health in `/ready` and provider-safe operational logs.
2. Keep the configured provider selection unchanged; never enable cloud fallback or send raw data elsewhere.
3. Allow configured retries/backoff to operate, then move exhausted jobs to dead-letter handling.
4. Communicate delayed safe-chat availability; direct users to manual review when necessary.

## Malware and quarantine procedure

1. Treat unverified and blocked uploads as quarantined. Do not manually release them into processing storage.
2. Review only scanner status/error metadata and the document identifier.
3. A clean scanner result is required before release to OCR. Scanner unavailability fails closed.
4. For a suspected malicious upload, retain only response-safe incident metadata and follow the security incident procedure.

## OCR degradation and regression procedure

1. Compare synthetic corpus outcomes to the approved golden baseline; do not use customer documents as test fixtures.
2. Check OCR timeout, confidence, failure, and queue metrics without reading protected text in logs.
3. Pause affected processing or route it to manual-only handling if regression is material.
4. Do not alter OCR provider selection or privacy policy without an approved release.

## Retention backlog recovery

1. Confirm access revocation has occurred before any purge retry.
2. Inspect queued/failed retention jobs by ID, retry count, and safe error code.
3. Restore the failed dependency, then allow configured retry backoff or requeue through the approved operator process.
4. Mark completion only after all required purge scopes are verified. Never claim physical deletion from a queued state.

## Suspected security incident

1. Preserve timestamps, request IDs, status codes, and safe error codes; do not collect raw content into incident records.
2. Restrict access using deployment and identity controls, then assess affected service boundaries.
3. Validate token, storage, worker, and provider configuration. Rotate credentials through the secret manager if exposure is suspected.
4. Notify the designated security and privacy owners according to the approved incident policy.
5. Record remediation and release any recovery only after a security review.

## Data deletion verification

1. Verify the conversation is revoked and the retention job exists.
2. Verify required purge scopes completed: uploads, OCR, structured projections, assignments, messages, renders/artifacts, privacy summaries, and privacy audit events.
3. Record only completion status, timestamps, retry count, and safe audit event metadata.
4. Apply the backup-retention policy separately; do not report immediate physical backup deletion.
