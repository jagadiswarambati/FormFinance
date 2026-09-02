# Closed-Beta Deployment and Monitoring Checklist

## Production configuration

- [ ] Production Firebase project, service account, and web origins are isolated from development and staging.
- [ ] All secrets are supplied by the deployment secret manager; none are embedded in images, frontend variables, logs, or source control.
- [ ] Strict CORS origin list, security headers, HSTS, and production worker-heartbeat readiness are configured.
- [ ] API and worker share the configured rendered-artifact volume only as required by the LocalRenderArtifactStore contract.
- [ ] Upload, quarantine, OCR, privacy, and render storage paths are distinct and access-controlled.
- [ ] Enabled provider is explicitly configured; disabled providers remain unavailable.
- [ ] Worker concurrency, timeout, retry-backoff, heartbeat, and coordinate-confidence settings have approved values.
- [ ] Deployment region, legal privacy wording, backup retention, and restore owner are recorded in the release approval.

## Closed-beta deployment

- [ ] Build immutable web, API, and worker images from the approved revision.
- [ ] Apply migrations/configuration using the approved deployment process only.
- [ ] Start API and worker services; verify `/api/v1/health` and `/api/v1/ready`.
- [ ] Confirm worker heartbeat, queue-depth metrics, and safe dead-letter reporting.
- [ ] Run the synthetic upload → OCR → privacy → understanding → rendering → download → deletion smoke flow in the isolated beta environment.
- [ ] Confirm the five-conversation retention statement and deletion-queued wording are visible.

## Monitoring checklist

- [ ] Monitor API readiness, Firestore, storage, provider, queue, and worker-heartbeat dependency status.
- [ ] Monitor queue depth, timeout counts, retry counts, and dead-letter rates using response-safe metadata only.
- [ ] Review quarantine release/block status and OCR regression signals using synthetic fixtures.
- [ ] Review retention backlog and purge completion verification.
- [ ] Escalate any suspected privacy boundary, authorization, or artifact-access failure through the security incident runbook.

## Rollback procedure

1. Stop rollout and retain the currently deployed immutable image references.
2. Restore the last approved API, worker, and web images together if compatibility requires it.
3. Do not roll back by modifying stored Field Maps, assignments, render records, privacy artifacts, or retention records.
4. Validate `/health`, `/ready`, worker heartbeat, queue claims, and synthetic smoke flow after rollback.
5. Open an incident record with safe identifiers and determine whether queued work should resume under the restored release.

## Release approval checklist

- [ ] Product owner approves closed-beta scope and supported document limits.
- [ ] Security owner approves threat model, security baseline, and incident procedure.
- [ ] Privacy owner approves privacy wording, region, retention, backup policy, and deletion verification.
- [ ] Engineering owner approves build, tests, readiness, rollback, and observability checks.
- [ ] Operations owner confirms alert ownership and runbook access.
