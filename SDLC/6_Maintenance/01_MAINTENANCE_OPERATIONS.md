# FormFinance — Maintenance & Operations Guide

**Version:** 1.0  
**Date:** January 2025  

---

## 1. System Monitoring

### 1.1 Key Metrics to Monitor

**API Performance:**
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Throughput (requests/sec)
- Database query time

**Settlement Processing:**
- Extraction success rate
- Verification completion rate
- Agent investigation success rate
- Processing time per settlement

**Infrastructure:**
- CPU usage
- Memory usage
- Disk usage
- Network I/O

**System Health:**
- Service uptime
- Health check status
- Database connectivity
- External API availability (Anthropic)

### 1.2 Monitoring Setup

**Option 1: Cloud Monitoring (GCP)**
```bash
# Enable Cloud Monitoring
gcloud monitoring dashboards create \
  --config-from-file=dashboards/formwise-monitoring.json
```

**Option 2: Datadog**
```yaml
# datadog-agent.yaml
apiVersion: v1
kind: Pod
metadata:
  name: datadog-agent
spec:
  containers:
  - name: agent
    image: datadog/agent:latest
    env:
    - name: DD_API_KEY
      valueFrom:
        secretKeyRef:
          name: datadog-secrets
          key: api-key
```

**Option 3: Prometheus + Grafana**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'formwise-api'
    static_configs:
      - targets: ['localhost:8000']
```

### 1.3 Alerting

**Alert Rules (Examples):**

| Alert | Condition | Action |
|---|---|---|
| High Error Rate | >5% of requests fail | Page on-call engineer |
| High Latency | p95 > 1000ms | Investigate, scale if needed |
| Settlement Extraction Fails | <90% success rate | Alert team, check OCR service |
| Agent Investigation Fails | <80% success rate | Check LLM API, review logs |
| Disk Full | >90% used | Trigger cleanup job |
| Service Down | Health check fails | Auto-restart, page on-call |

---

## 2. Logging & Log Analysis

### 2.1 Log Levels

```python
# Backend logging configuration
import logging

logging.basicConfig(level=logging.INFO)

# Usage
logger = logging.getLogger(__name__)
logger.debug("Detailed debug info")        # Development only
logger.info("Settlement processing started")  # Important events
logger.warning("Low confidence extraction")   # Non-critical issues
logger.error("Settlement processing failed", exc_info=True)  # Errors
logger.critical("System failure")           # Critical issues
```

### 2.2 Log Aggregation

**Centralized Logging Stack:**
```
Apps (API, Worker)
  ↓ (stdout/stderr)
  ↓
Log Collector (Fluent Bit, Logstash)
  ↓
Log Storage (Cloud Logging, Elasticsearch)
  ↓
Analysis & Alerting (logs dashboard, alerts)
```

### 2.3 Important Log Queries

```bash
# Find all errors in last hour
gcloud logging read "severity=ERROR" --limit=100 --format=json

# Find settlement processing failures
gcloud logging read "settlement_id=settlement_001" --format=json

# Find agent investigation results
gcloud logging read "agent_investigation" --format=json

# Count errors by endpoint
gcloud logging read "httpRequest.requestUrl" --limit=1000 --format=json | jq '.[]|.httpRequest.requestUrl' | sort | uniq -c
```

---

## 3. Database Maintenance

### 3.1 Firestore Maintenance

**Index Optimization:**
```bash
# View current indexes
gcloud firestore indexes list

# Delete unused indexes
gcloud firestore indexes delete INDEX_ID
```

**Data Cleanup:**
```python
# Delete old audit records (>90 days)
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta

db = firestore.client()
cutoff_date = datetime.utcnow() - timedelta(days=90)

# Query old records
query = db.collection('audit_events').where('timestamp', '<', cutoff_date)
docs = query.stream()

# Delete in batches
batch = db.batch()
for doc in docs:
    batch.delete(doc.reference)
batch.commit()
```

### 3.2 Local Storage Cleanup

```bash
# Remove old OCR files (>30 days)
find storage/ocr -type f -mtime +30 -delete

# Remove old upload artifacts
find storage/uploads -type f -mtime +30 -delete

# Archive audit logs
tar -czf audits-2025-01.tar.gz storage/audits/
rm -rf storage/audits/*.json
```

---

## 4. Backup Management

### 4.1 Backup Schedule

| Target | Frequency | Retention | Tool |
|---|---|---|---|
| Firestore | Hourly | 30 days | Firestore Backup |
| Uploaded PDFs | Daily | 90 days | Cloud Storage |
| OCR Text | Daily | 30 days | Cloud Storage |
| Audit Trail | Continuous | 1 year | Cloud Logging |

### 4.2 Backup Verification

```bash
# Verify Firestore backup integrity
gsutil ls -r gs://formwise-backups/firestore/

# Verify file backups
gsutil ls -r gs://formwise-backups/uploads/

# Test restore procedure (on staging)
gcloud firestore restore \
  --backup=projects/PROJECT_ID/locations/us-central1/backups/BACKUP_ID
```

---

## 5. Incident Response

### 5.1 Incident Categories

| Severity | Impact | Response Time | Example |
|---|---|---|---|
| P1 (Critical) | Service down, data loss | <15 min | Database corrupted, API crashed |
| P2 (High) | Features broken, major degradation | <1 hour | Settlement processing fails |
| P3 (Medium) | Partial feature degradation | <4 hours | Slow response, occasional failures |
| P4 (Low) | Minor issues, workarounds exist | <24 hours | UI bug, typo in message |

### 5.2 Incident Response Workflow

```
1. DETECT: Alert fires, on-call engineer paged
2. RESPOND: Engineer joins incident channel, starts investigation
3. ASSESS: Determine severity, impact scope, affected users
4. MITIGATE: Stop the bleeding (rollback, feature flag, etc.)
5. INVESTIGATE: Root cause analysis
6. FIX: Develop and test fix
7. DEPLOY: Roll out fix to production
8. VERIFY: Confirm resolution
9. DOCUMENT: Write post-mortem, action items
10. FOLLOW-UP: Complete action items, prevent recurrence
```

### 5.3 Common Issues & Resolutions

**Issue: High Settlement Processing Latency**
```bash
# Check API logs
docker logs formwise-api-1 | grep "processing_time"

# Profile slow queries
gcloud firestore profile --all-collections

# Scale up if needed
kubectl scale deployment formwise-api --replicas=5
```

**Issue: OCR Extraction Fails**
```bash
# Restart worker
docker-compose restart worker

# Check worker logs
docker logs formwise-worker-1

# Check disk space (OCR needs space)
df -h storage/

# Verify PaddleOCR installation
docker exec formwise-worker-1 python -c "import paddleocr; print('OK')"
```

**Issue: Agent Investigation Timeout**
```bash
# Check LLM API availability
curl -s https://api.anthropic.com/status

# Increase timeout
# In finance_agent.py: timeout = 30 (seconds)

# Check API usage/quota
# In Anthropic dashboard
```

---

## 6. Performance Tuning

### 6.1 Query Optimization

**Firestore Queries:**
```python
# Good: Use indexes
query = db.collection('settlements')\
  .where('owner_uid', '==', user_id)\
  .where('created_at', '>=', start_date)\
  .order_by('created_at', direction=firestore.Query.DESCENDING)\
  .limit(20)

# Bad: Fetch all then filter
all_docs = db.collection('settlements').stream()
filtered = [d for d in all_docs if d.get('owner_uid') == user_id]
```

**Create Composite Index (if needed):**
```bash
gcloud firestore indexes composite create \
  --collection=settlements \
  --field-config field-path=owner_uid,order=asc \
  --field-config field-path=created_at,order=desc
```

### 6.2 Caching Strategy

**Cache Layers:**
1. Application-level cache (Redis)
2. CDN cache (for static assets)
3. Database result cache
4. Query result cache

**Example (Python):**
```python
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def get_verification_rules():
    """Cache verification rules (expensive to compute)."""
    return compute_rules()

# Or with TTL
cache = {}
cache_ttl = 3600  # 1 hour

def get_settlement_cached(settlement_id):
    if settlement_id in cache and time.time() - cache[settlement_id]['time'] < cache_ttl:
        return cache[settlement_id]['value']
    
    result = db.collection('settlements').document(settlement_id).get()
    cache[settlement_id] = {'value': result, 'time': time.time()}
    return result
```

### 6.3 Database Optimization

**Indexes:**
```
Recommended indexes:
- settlements(owner_uid, created_at)
- audit_events(settlement_id, timestamp)
- verification_results(deduction_id, status)
```

**Partitioning:**
- Partition by owner_uid (for multi-tenant)
- Partition by created_at (for time-series)

---

## 7. Security Maintenance

### 7.1 Security Patches

**Regular Updates:**
- Python packages: `pip list --outdated`
- Node packages: `npm outdated`
- Docker base images: Monthly

**Update Procedure:**
```bash
# 1. Test in dev
pip install --upgrade fastapi

# 2. Run tests
pytest tests/ -v

# 3. Test in staging
docker-compose up -d  # Staging environment

# 4. Deploy to production
docker-compose build
docker-compose push
kubectl set image deployment/formwise-api api=formwise-api:v1.0.1
```

### 7.2 Secret Rotation

**API Key Rotation (quarterly):**
```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -base64 32)

# 2. Update in Secret Manager
gcloud secrets versions add anthropic-api-key --data-file=<(echo -n "$NEW_KEY")

# 3. Update services
kubectl restart deployment formwise-api

# 4. Test
curl -H "Authorization: Bearer $NEW_KEY" http://api/test

# 5. Revoke old key (after verification)
```

### 7.3 Audit Trail Review

```bash
# Weekly security audit log review
gcloud logging read "protoPayload.resourceName=~\"documents|settlements\"" \
  --limit=1000 \
  --format=json \
  --order-by-time \
  desc | jq '.[] | {timestamp, principalEmail, resourceName, methodName, status}'
```

---

## 8. Disaster Recovery

### 8.1 Disaster Recovery Plan

**RTO/RPO Targets:**
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 1 hour

**Recovery Procedures:**

**Scenario: Data Corruption**
```bash
# 1. Detect: Verify data integrity check fails
python scripts/verify_firestore.py

# 2. Respond: Failover to read-only mode
# Update env: MAINTENANCE_MODE=true

# 3. Restore: Restore from latest good backup
gcloud firestore restore \
  --backup=projects/PROJECT_ID/locations/us-central1/backups/BACKUP_ID

# 4. Verify: Run data verification
python scripts/verify_firestore.py

# 5. Resume: Resume normal operations
# Update env: MAINTENANCE_MODE=false
```

**Scenario: Service Outage**
```bash
# 1. Detect: Health check fails
curl http://api:8000/api/v1/health  # Returns 503

# 2. Respond: Trigger failover
kubectl set image deployment/formwise-api api=formwise-api:v1.0.0  # Previous version

# 3. Investigate: Check logs
docker logs formwise-api-1 | tail -100

# 4. Fix: Deploy fix or wait for service recovery
# ...

# 5. Verify: All health checks pass
```

---

## 9. Maintenance Windows

### 9.1 Scheduled Maintenance

**Weekly Maintenance Windows (Sundays 2-4am UTC):**
- Database optimization
- Log cleanup
- Backup verification
- Security patches

**Notification:**
```
Status Page Update:
"We'll be performing scheduled maintenance on Sunday 2-4am UTC.
Service may be intermittently unavailable. We apologize for the inconvenience."
```

### 9.2 Maintenance Mode

```python
# In API routes
from fastapi import HTTPException

@app.get("/api/v1/health")
def health():
    if os.getenv('MAINTENANCE_MODE') == 'true':
        raise HTTPException(status_code=503, detail="Under maintenance")
    return {"status": "ok"}
```

**Enable maintenance mode:**
```bash
docker-compose set env MAINTENANCE_MODE=true
# ... perform maintenance ...
docker-compose set env MAINTENANCE_MODE=false
```

---

## 10. Documentation & Runbooks

### 10.1 Runbook Checklist

- [ ] Common Issues & Resolutions
- [ ] Incident Response Procedures
- [ ] Escalation Contacts
- [ ] Deployment Rollback
- [ ] Database Recovery
- [ ] Performance Tuning
- [ ] Log Analysis
- [ ] Alert Threshold Tuning

### 10.2 Team Communication

**Slack Channels:**
- `#formwise-incidents`: Real-time incident updates
- `#formwise-deploy`: Deployment notifications
- `#formwise-alerts`: Automated alert notifications
- `#formwise-maintenance`: Maintenance notifications

**On-Call Rotation:**
- Weekly on-call engineer (covers business hours)
- 24/7 on-call for P1 incidents
- Escalation path: On-call → Tech Lead → Manager

---

## 11. Regular Maintenance Tasks

### 11.1 Daily Tasks

- [ ] Review error logs
- [ ] Check system health dashboard
- [ ] Verify backups completed
- [ ] Monitor key metrics (error rate, latency)

### 11.2 Weekly Tasks

- [ ] Run data integrity checks
- [ ] Review and respond to non-urgent issues
- [ ] Optimize slow queries
- [ ] Update documentation
- [ ] Security patch review

### 11.3 Monthly Tasks

- [ ] Full backup verification (restore to staging)
- [ ] Disaster recovery drill
- [ ] Capacity planning review
- [ ] Performance analysis
- [ ] Security audit
- [ ] Cost optimization review

### 11.4 Quarterly Tasks

- [ ] Major version updates
- [ ] Security penetration testing
- [ ] Architecture review
- [ ] Dependency updates
- [ ] Secret rotation

---

**Status:** Active  
**Last Updated:** January 6, 2025
