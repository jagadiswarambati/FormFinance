# FormFinance — Deployment Guide

**Version:** 1.0  
**Date:** January 2025  

---

## 1. Deployment Environments

### 1.1 Development

**Purpose:** Local development and testing  
**Infrastructure:** Developer laptop/workstation  
**Data:** Synthetic test data  
**Authentication:** Demo mode  
**API Keys:** Optional (development only)

### 1.2 Staging

**Purpose:** Pre-production testing, integration, performance validation  
**Infrastructure:** Cloud VM or Docker host  
**Data:** Synthetic data + production-like volumes  
**Authentication:** Firebase (optional) + Demo mode  
**Monitoring:** Basic logging

### 1.3 Production

**Purpose:** Live system for end users  
**Infrastructure:** Kubernetes or managed container service  
**Data:** Real financial records (encrypted)  
**Authentication:** Firebase + OAuth2  
**Monitoring:** Comprehensive logging, alerting, tracing

---

## 2. Docker Deployment

### 2.1 Prerequisites

```bash
# Verify Docker and Docker Compose
docker --version  # 20.10+
docker-compose --version  # 2.0+

# Clone repository
git clone <repo_url>
cd FormFinance-main
```

### 2.2 Local Development (Docker Compose)

```bash
# 1. Create .env file
cp .env.example .env

# 2. (Optional) Configure AI provider
# Uncomment ANTHROPIC_API_KEY in .env

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Wait for initialization
sleep 10

# 6. Verify services
curl -s http://localhost:8000/api/v1/health | jq .
curl -s http://localhost:3000 | grep -o "FORMFINANCE"
```

### 2.3 docker-compose.yml Structure

```yaml
version: '3.8'

services:
  api:
    build: ./services/api
    ports:
      - "8000:8000"
    environment:
      - FORMWISE_ENV=development
      - DEMO_AUTH_ENABLED=true
      - LOG_LEVEL=INFO
    volumes:
      - upload-artifacts:/app/storage
    depends_on:
      - worker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
      - NEXT_PUBLIC_DEMO_AUTH_ENABLED=true
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 10s
      timeout: 5s
      retries: 3

  worker:
    build: ./services/worker
    environment:
      - FORMWISE_ENV=development
      - LOG_LEVEL=INFO
    volumes:
      - upload-artifacts:/app/storage

volumes:
  upload-artifacts:
```

### 2.4 Stopping Services

```bash
# Graceful shutdown
docker-compose down

# Remove volumes (delete data)
docker-compose down -v

# View logs before shutdown
docker-compose logs -f
```

---

## 3. Environment Configuration

### 3.1 Backend Environment Variables

**Required:**
```bash
FORMWISE_ENV=development              # development|staging|production
DEMO_AUTH_ENABLED=true                # Enable demo auth
```

**Optional (Firebase):**
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_JSON={}      # Full JSON
# OR
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
```

**Optional (AI):**
```bash
ANTHROPIC_API_KEY=sk-...              # Anthropic API key
```

**Optional (Logging):**
```bash
LOG_LEVEL=INFO                        # DEBUG|INFO|WARNING|ERROR|CRITICAL
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### 3.2 Frontend Environment Variables

**Required:**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEMO_AUTH_ENABLED=true
```

**Optional (Firebase):**
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
```

### 3.3 Environment File Location

**Backend:** `services/api/.env` or `~/.env`  
**Frontend:** `apps/web/.env.local`

**Load Priority:**
1. Environment variables (highest priority)
2. .env file
3. .env.local file
4. Defaults in code

---

## 4. Production Deployment

### 4.1 Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Version bumped (semantic versioning)
- [ ] Docker images built and tagged
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Monitoring/alerting configured
- [ ] Rollback plan documented

### 4.2 Docker Image Tagging

```bash
# Build with version tag
docker build -t formwise-api:v1.0.0 ./services/api
docker build -t formwise-web:v1.0.0 ./apps/web

# Also tag as latest
docker tag formwise-api:v1.0.0 formwise-api:latest
docker tag formwise-web:v1.0.0 formwise-web:latest

# Push to registry (e.g., Docker Hub)
docker push formwise-api:v1.0.0
docker push formwise-web:v1.0.0
```

### 4.3 Production Docker Compose

```yaml
version: '3.8'

services:
  api:
    image: formwise-api:v1.0.0
    ports:
      - "8000:8000"
    environment:
      - FORMWISE_ENV=production
      - DEMO_AUTH_ENABLED=false
      - LOG_LEVEL=WARNING
      - FIREBASE_SERVICE_ACCOUNT_PATH=/secrets/firebase.json
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - /data/uploads:/app/storage/uploads
      - /secrets:/secrets:ro
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  web:
    image: formwise-web:v1.0.0
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1
      - NEXT_PUBLIC_DEMO_AUTH_ENABLED=false
      - NEXT_PUBLIC_FIREBASE_API_KEY=${FIREBASE_API_KEY}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  worker:
    image: formwise-worker:v1.0.0
    environment:
      - FORMWISE_ENV=production
      - LOG_LEVEL=WARNING
    volumes:
      - /data/uploads:/app/storage
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4.4 Kubernetes Deployment (Optional)

**Deployment Manifest (api-deployment.yaml):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: formwise-api
  labels:
    app: formwise-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: formwise-api
  template:
    metadata:
      labels:
        app: formwise-api
    spec:
      containers:
      - name: api
        image: formwise-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: FORMWISE_ENV
          value: "production"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: formwise-secrets
              key: anthropic-key
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: storage
          mountPath: /app/storage
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: formwise-storage
```

---

## 5. Database Migration

### 5.1 Firestore Setup (Production)

```bash
# 1. Create Firestore project in GCP
# 2. Download service account JSON
# 3. Set environment variable
export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json

# 4. Run migration (if needed)
uv run python scripts/firestore_migrate.py
```

### 5.2 Data Migration from Local Storage to Firestore

```python
# services/api/scripts/firestore_migrate.py
import firebase_admin
from firebase_admin import firestore, credentials
import json
from pathlib import Path

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Migrate documents
for doc_file in Path('storage/uploads').glob('*.metadata.json'):
    with open(doc_file) as f:
        doc_data = json.load(f)
    db.collection('documents').document(doc_data['id']).set(doc_data)

print("Migration complete!")
```

---

## 6. Monitoring & Health Checks

### 6.1 Health Check Endpoints

**API Health:**
```bash
curl http://localhost:8000/api/v1/health
# Response: { "status": "ok", "timestamp": "..." }
```

**Frontend Health:**
```bash
curl http://localhost:3000
# Response: HTML with "FORMFINANCE" title
```

### 6.2 Docker Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 6.3 Logging Configuration

**Backend (Python):**
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

**Log Aggregation:**
- Use CloudLogging (GCP), CloudWatch (AWS), or Datadog
- Configure log drain in docker-compose
- Set up alerting on error patterns

---

## 7. Secrets Management

### 7.1 Never Commit Secrets

**.gitignore:**
```
.env
.env.local
.env.*.local
serviceAccountKey.json
*.pem
*.key
```

### 7.2 Secret Storage Options

**Development:**
- Local .env file (not committed)
- Use demo mode (no secrets needed)

**Production:**
- Google Secret Manager (GCP)
- AWS Secrets Manager (AWS)
- HashiCorp Vault
- Kubernetes Secrets

**Example (GCP Secret Manager):**
```bash
# Store secret
gcloud secrets create anthropic-api-key --data-file=-

# Use in Cloud Run
gcloud run deploy formwise-api \
  --set-env-vars ANTHROPIC_API_KEY="projects/PROJECT_ID/secrets/anthropic-api-key/versions/latest"
```

---

## 8. Backup & Recovery

### 8.1 Data Backup Strategy

**What to Backup:**
- Firestore collections (documents, settlements, audits)
- Uploaded PDFs (storage/uploads/)
- OCR text (storage/ocr/)

**Backup Frequency:**
- Development: Not needed (synthetic data)
- Staging: Daily
- Production: Hourly

**Backup Tools:**
- Firestore Backup (automatic in GCP)
- Cloud Storage backup for files
- Database replication for high availability

### 8.2 Disaster Recovery

**RPO (Recovery Point Objective):** 1 hour  
**RTO (Recovery Time Objective):** 4 hours

**Procedure:**
1. Restore Firestore from backup
2. Restore files from Cloud Storage backup
3. Redeploy Docker containers
4. Verify health checks
5. Test critical paths
6. Monitor for anomalies

---

## 9. Rollback Procedure

### 9.1 Simple Rollback (Docker Compose)

```bash
# If deployment fails, rollback to previous version

# 1. Stop current containers
docker-compose down

# 2. Update docker-compose.yml to previous version
vim docker-compose.yml
# Change images back to previous tag

# 3. Start previous version
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/api/v1/health

# 5. Monitor logs
docker-compose logs -f
```

### 9.2 Database Rollback

**If migration causes issues:**

```bash
# 1. Restore from backup
gcloud firestore restore \
  --backup=projects/PROJECT_ID/locations/LOCATION/backups/BACKUP_ID

# 2. Verify data integrity
uv run python scripts/verify_firestore.py

# 3. Restart services
docker-compose restart
```

---

## 10. Performance Tuning

### 10.1 API Optimization

**Connection Pooling:**
```python
# Use connection pool for database
database = firestore.Client(
    credentials=credentials,
    pool_size=20
)
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_settlement_rules():
    # Cache deduction verification rules
    return VERIFICATION_RULES
```

### 10.2 Frontend Optimization

**Code Splitting:**
```typescript
// Next.js automatic code splitting
import dynamic from 'next/dynamic';

const SettlementResults = dynamic(() => import('./SettlementResults'), {
  loading: () => <Loading />,
});
```

**Image Optimization:**
```typescript
// Use Next.js Image component
import Image from 'next/image';

<Image src="/logo.png" alt="Logo" width={100} height={100} />
```

---

## 11. Scaling

### 11.1 Horizontal Scaling (Docker Swarm / Kubernetes)

**Docker Swarm:**
```bash
# Initialize swarm
docker swarm init

# Scale API service
docker service create --replicas 3 --name api formwise-api:v1.0.0
```

**Kubernetes:**
```yaml
# Replicas in deployment manifest
spec:
  replicas: 3
```

### 11.2 Vertical Scaling

**Increase resources in docker-compose:**
```yaml
services:
  api:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

---

## 12. Deployment Checklist

- [ ] Environment variables configured
- [ ] Secrets securely stored
- [ ] Docker images built and tagged
- [ ] docker-compose.yml updated
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Monitoring/alerting setup
- [ ] Backups scheduled
- [ ] Rollback plan documented
- [ ] Team trained on deployment
- [ ] Post-deployment tests passed
- [ ] Performance metrics acceptable

---

**Status:** Approved  
**Last Updated:** January 6, 2025
