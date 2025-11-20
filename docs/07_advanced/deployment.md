# Deployment Guide

> **Production deployment for SpecQL applications—from staging to scale**

## Overview

Production-ready deployment requires:
- ✅ **Database setup** - PostgreSQL with replication
- ✅ **Application deployment** - Docker + Kubernetes/ECS
- ✅ **Load balancing** - Distribute traffic
- ✅ **SSL/TLS** - Secure connections
- ✅ **Monitoring** - Observability stack
- ✅ **Backup & Recovery** - Data protection
- ✅ **CI/CD** - Automated deployments

**Goal**: 99.9% uptime, zero-downtime deployments

---

## Quick Start (Docker Compose)

### Development/Staging

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./generated/schema:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  app:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@postgres:5432/myapp
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    ports:
      - "5000:5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres-data:
  redis-data:
```

**Deploy**:
```bash
docker-compose up -d
```

---

## Production Deployment (Kubernetes)

### PostgreSQL StatefulSet

```yaml
# postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3  # Primary + 2 replicas
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        ports:
        - containerPort: 5432
          name: postgres
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - app_user
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - app_user
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: init-scripts
        configMap:
          name: postgres-init
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None  # Headless service for StatefulSet
```

---

### Application Deployment

```yaml
# app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: specql-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: specql-app
  template:
    metadata:
      labels:
        app: specql-app
    spec:
      containers:
      - name: app
        image: myregistry/specql-app:v1.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: redis-url
        - name: NODE_ENV
          value: production
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: specql-app
spec:
  selector:
    app: specql-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: specql-app-external
spec:
  selector:
    app: specql-app
  ports:
  - protocol: TCP
    port: 443
    targetPort: 5000
  type: LoadBalancer
```

---

### Ingress (SSL/TLS)

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: specql-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.myapp.com
    secretName: specql-tls
  rules:
  - host: api.myapp.com
    http:
      paths:
      - path: /graphql
        pathType: Prefix
        backend:
          service:
            name: specql-app
            port:
              number: 80
```

---

## Zero-Downtime Deployments

### Rolling Update Strategy

```yaml
# app-deployment.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Max extra pods during update
      maxUnavailable: 0  # Always keep all pods running
  minReadySeconds: 10    # Wait 10s before considering pod ready
```

**Deploy new version**:
```bash
kubectl set image deployment/specql-app app=myregistry/specql-app:v1.1.0
kubectl rollout status deployment/specql-app
```

**Rollback if needed**:
```bash
kubectl rollout undo deployment/specql-app
```

---

### Blue-Green Deployment

**Create blue deployment** (current):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: specql-app-blue
  labels:
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: specql-app
      version: blue
  # ... rest of deployment
```

**Create green deployment** (new):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: specql-app-green
  labels:
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: specql-app
      version: green
  # ... rest of deployment
```

**Switch traffic**:
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: specql-app
spec:
  selector:
    app: specql-app
    version: green  # Switch from blue to green
  ports:
  - port: 80
    targetPort: 5000
```

---

## Database Migrations

### Migration Strategy

**File**: `migrations/001_initial_schema.sql`
```sql
-- Auto-generated from SpecQL
-- Date: 2025-01-15

BEGIN;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS crm;
CREATE SCHEMA IF NOT EXISTS app;

-- Create tables
\i generated/schema/00_framework/app_schema.sql
\i generated/schema/10_tables/company.sql
\i generated/schema/10_tables/contact.sql

-- Create functions
\i generated/functions/qualify_lead.sql

COMMIT;
```

---

### Automated Migrations (Flyway)

**Install Flyway**:
```bash
docker pull flyway/flyway
```

**Directory structure**:
```
migrations/
├── V001__initial_schema.sql
├── V002__add_orders_table.sql
├── V003__add_qualify_lead_action.sql
└── R__refresh_materialized_views.sql  # Repeatable
```

**Run migrations**:
```bash
flyway -url=jdbc:postgresql://localhost:5432/myapp \
       -user=app_user \
       -password=secret \
       -locations=filesystem:./migrations \
       migrate
```

**Kubernetes CronJob** for repeatable migrations:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: refresh-materialized-views
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: flyway
            image: flyway/flyway
            command:
            - flyway
            - -url=jdbc:postgresql://postgres:5432/myapp
            - -user=app_user
            - -password=$(DB_PASSWORD)
            - -locations=filesystem:/migrations
            - migrate
            volumeMounts:
            - name: migrations
              mountPath: /migrations
          volumes:
          - name: migrations
            configMap:
              name: migrations
          restartPolicy: OnFailure
```

---

## Backup & Recovery

### Automated Backups (pg_dump)

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Create backup
pg_dump -h localhost -U app_user myapp | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://myapp-backups/

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Kubernetes CronJob**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U app_user myapp | \
              gzip | \
              aws s3 cp - s3://myapp-backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: secret-access-key
          restartPolicy: OnFailure
```

---

### Point-in-Time Recovery (PITR)

**Enable WAL archiving**:
```sql
-- postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/wal_archive/%f && cp %p /mnt/wal_archive/%f'
max_wal_senders = 3
wal_keep_size = 1GB
```

**Restore to specific time**:
```bash
# Stop PostgreSQL
pg_ctl stop

# Restore base backup
gunzip -c backup_20250115.sql.gz | psql -U app_user myapp

# Create recovery.conf
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_time = '2025-01-15 14:30:00'
EOF

# Start PostgreSQL (will recover to specified time)
pg_ctl start
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run tests
        run: |
          pip install -e .
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t myregistry/specql-app:${{ github.sha }} .
          docker tag myregistry/specql-app:${{ github.sha }} myregistry/specql-app:latest

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push myregistry/specql-app:${{ github.sha }}
          docker push myregistry/specql-app:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG }}" > kubeconfig.yaml
          export KUBECONFIG=kubeconfig.yaml

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/specql-app app=myregistry/specql-app:${{ github.sha }}
          kubectl rollout status deployment/specql-app

      - name: Run migrations
        run: |
          kubectl run flyway-migrate \
            --image=flyway/flyway \
            --restart=Never \
            --command -- flyway migrate
```

---

## Cloud Platforms

### AWS (ECS + RDS)

```yaml
# ecs-task-definition.json
{
  "family": "specql-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "myregistry/specql-app:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/specql-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deploy**:
```bash
aws ecs update-service \
  --cluster specql-cluster \
  --service specql-app \
  --task-definition specql-app:latest \
  --force-new-deployment
```

---

### Google Cloud (GKE + Cloud SQL)

```bash
# Create GKE cluster
gcloud container clusters create specql-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Create Cloud SQL instance
gcloud sql instances create specql-db \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-2 \
  --region=us-central1

# Deploy application
kubectl apply -f k8s/
```

---

## Monitoring in Production

### Key Metrics

**Set up monitoring** (see [Monitoring Guide](monitoring.md)):
- Application metrics (latency, errors, throughput)
- Database metrics (connections, slow queries)
- Infrastructure metrics (CPU, memory, disk)
- Business metrics (signups, conversions)

**Alerting thresholds**:
```yaml
# prometheus-alerts.yml
- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) > 0.05
  for: 5m
  severity: critical

- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_duration_seconds_bucket[5m])) > 1
  for: 10m
  severity: warning

- alert: DatabaseConnectionsHigh
  expr: pg_stat_activity_count > 80
  for: 5m
  severity: warning
```

---

## Best Practices

### ✅ DO

1. **Use health checks** (liveness and readiness)
2. **Implement rolling updates** for zero downtime
3. **Automate migrations** (Flyway, Liquibase)
4. **Backup daily** with point-in-time recovery
5. **Monitor everything** (metrics, logs, traces)
6. **Use secrets management** (not environment variables in code)
7. **Test deployments** in staging first
8. **Document runbooks** for common issues

---

### ❌ DON'T

1. **Don't skip backups**
2. **Don't deploy directly to production** (use staging)
3. **Don't hardcode secrets**
4. **Don't ignore health checks**
5. **Don't skip migrations** (data and schema must be in sync)
6. **Don't deploy without monitoring**

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Staging deployment successful
- [ ] Migrations tested
- [ ] Backup created
- [ ] Monitoring configured
- [ ] Alerts tested
- [ ] Rollback plan documented

### Post-Deployment

- [ ] Health checks passing
- [ ] Metrics stable (error rate, latency)
- [ ] No elevated alerts
- [ ] Database migrations applied
- [ ] Smoke tests passed
- [ ] Documentation updated

---

## Next Steps

### Learn More

- **[Monitoring Guide](monitoring.md)** - Production observability
- **[Security Hardening](security-hardening.md)** - Production security
- **[Performance Tuning](performance-tuning.md)** - Optimize for scale

### Tools

- **Kubernetes** - Container orchestration
- **Docker** - Containerization
- **Flyway** - Database migrations
- **Terraform** - Infrastructure as code
- **ArgoCD** - GitOps deployments

---

## Summary

You've learned:
- ✅ Docker Compose for development
- ✅ Kubernetes deployment
- ✅ Zero-downtime strategies
- ✅ Database migrations
- ✅ Backup and recovery
- ✅ CI/CD pipelines
- ✅ Cloud platform deployments

**Key Takeaway**: Production deployment requires automation—automate testing, migrations, deployments, and monitoring.

**Next**: Manage schema changes with [Migrations Guide](migrations.md) →

---

**Deploy with confidence—automation and monitoring are non-negotiable.**
