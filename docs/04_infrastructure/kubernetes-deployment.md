# Kubernetes Deployment Guide

> **Deploy SpecQL backends to any Kubernetes cluster with auto-generated manifests and Helm charts**

## Overview

SpecQL generates production-ready Kubernetes manifests and Helm charts. Define your requirements in YAML, get complete Kubernetes resources with best practices, observability, and GitOps workflows built-in.

**Think of it as**: Kubernetes expertise codified—from YAML to production-grade K8s resources automatically.

---

## Quick Start

### 1. Define Deployment

```yaml
# deployment.yaml
deployment:
  name: crm-backend
  cloud: kubernetes
  namespace: production
  environment: production

compute:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2
      memory: 4Gi
  auto_scale:
    enabled: true
    min: 3
    max: 10
    cpu_target: 70
    memory_target: 80

container:
  image: myregistry.io/crm-backend
  tag: v1.2.3
  port: 8080
  environment:
    ENV: production
  secrets:
    DATABASE_URL: ${SECRET_DB_URL}

database:
  type: postgresql
  version: "15"
  storage: 100Gi
  storage_class: fast-ssd
  replicas: 3  # Primary + 2 replicas

network:
  ingress:
    enabled: true
    class: nginx
    host: api.example.com
    tls:
      enabled: true
      secret_name: api-tls-cert

monitoring:
  prometheus: true
  grafana: true
  jaeger: true  # Distributed tracing
```

### 2. Generate Kubernetes Manifests

```bash
# Generate Kubernetes YAML
specql deploy deployment.yaml --cloud kubernetes --output k8s/

# Output structure
k8s/
├── namespace.yaml           # Namespace definition
├── deployment.yaml          # Application deployment
├── service.yaml             # ClusterIP service
├── ingress.yaml             # Ingress (HTTPS)
├── hpa.yaml                 # Horizontal Pod Autoscaler
├── configmap.yaml           # Configuration
├── secret.yaml              # Secrets (sealed)
├── statefulset.yaml         # PostgreSQL StatefulSet
├── pvc.yaml                 # Persistent Volume Claims
├── servicemonitor.yaml      # Prometheus monitoring
└── networkpolicy.yaml       # Network policies
```

### 3. Generate Helm Chart

```bash
# Generate Helm chart
specql deploy deployment.yaml --cloud kubernetes --format helm --output helm-chart/

# Output structure
helm-chart/
├── Chart.yaml               # Chart metadata
├── values.yaml              # Default values
├── values-prod.yaml         # Production values
├── values-staging.yaml      # Staging values
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── statefulset.yaml
    └── NOTES.txt
```

### 4. Deploy to Kubernetes

```bash
# Apply manifests directly
kubectl apply -f k8s/

# Or install Helm chart
helm install crm-backend helm-chart/ \
  --namespace production \
  --create-namespace \
  --values helm-chart/values-prod.yaml

# Check deployment
kubectl get pods -n production
kubectl get ingress -n production
```

---

## Deployment Patterns

### Pattern 1: Stateless Microservice

**Best for**: REST APIs, web services, stateless applications

```yaml
import:
  - patterns/infrastructure/k8s_stateless_microservice.yaml

deployment:
  name: api-service
  namespace: production

compute:
  replicas: 5
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1
      memory: 2Gi

  auto_scale:
    enabled: true
    min: 5
    max: 50
    cpu_target: 60
    memory_target: 75

  rolling_update:
    max_surge: 25%
    max_unavailable: 0  # Zero-downtime deployments

health_checks:
  liveness_probe:
    path: /health
    initial_delay: 30
    period: 10
  readiness_probe:
    path: /ready
    initial_delay: 5
    period: 5
```

**Generated Kubernetes Resources**:

**Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: production
  labels:
    app: api-service
    version: v1.2.3
spec:
  replicas: 5
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: api
          image: myregistry.io/crm-backend:v1.2.3
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            - name: ENV
              value: production
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: database-url
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: api-service
                topologyKey: kubernetes.io/hostname
```

**Horizontal Pod Autoscaler (HPA)**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 5
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

---

### Pattern 2: Stateful PostgreSQL Database

**Best for**: PostgreSQL databases, stateful services

```yaml
import:
  - patterns/infrastructure/k8s_postgresql_statefulset.yaml

database:
  name: crm-db
  namespace: production
  version: "15"
  replicas: 3  # 1 primary + 2 read replicas

  storage:
    size: 100Gi
    storage_class: fast-ssd  # Provider-specific (gp3, pd-ssd, etc.)

  resources:
    requests:
      cpu: 1
      memory: 4Gi
    limits:
      cpu: 4
      memory: 16Gi

  backup:
    enabled: true
    schedule: "0 2 * * *"  # 2 AM daily
    retention: 7  # days
    storage_class: standard  # Cheaper for backups
```

**Generated StatefulSet**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: crm-db
  namespace: production
spec:
  serviceName: crm-db
  replicas: 3
  selector:
    matchLabels:
      app: crm-db
  template:
    metadata:
      labels:
        app: crm-db
    spec:
      containers:
        - name: postgresql
          image: postgres:15-alpine
          ports:
            - name: postgresql
              containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: appdb
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: crm-db-secret
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: crm-db-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
            - name: config
              mountPath: /etc/postgresql
          resources:
            requests:
              cpu: 1
              memory: 4Gi
            limits:
              cpu: 4
              memory: 16Gi
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U $POSTGRES_USER
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U $POSTGRES_USER
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: config
          configMap:
            name: crm-db-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
```

**PostgreSQL Replication** (Primary + Replicas):
```yaml
# Primary Service (read-write)
apiVersion: v1
kind: Service
metadata:
  name: crm-db-primary
  namespace: production
spec:
  selector:
    app: crm-db
    role: primary
  ports:
    - port: 5432
      targetPort: 5432

---
# Replica Service (read-only)
apiVersion: v1
kind: Service
metadata:
  name: crm-db-replica
  namespace: production
spec:
  selector:
    app: crm-db
    role: replica
  ports:
    - port: 5432
      targetPort: 5432
```

---

### Pattern 3: Service Mesh with Istio

**Best for**: Microservices with service-to-service communication

```yaml
import:
  - patterns/infrastructure/k8s_istio_service_mesh.yaml

service_mesh:
  type: istio
  version: "1.19"
  features:
    - mTLS  # Mutual TLS between services
    - traffic_management
    - observability
    - security_policies

traffic:
  canary:
    enabled: true
    versions:
      stable: v1.2.3
      canary: v1.3.0
    weight:
      stable: 90
      canary: 10

  circuit_breaker:
    max_connections: 100
    max_requests_per_connection: 10
    consecutive_errors: 5
    interval: 30s
    base_ejection_time: 30s
```

**Generated Istio Resources**:

**Virtual Service** (traffic routing):
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-service
  namespace: production
spec:
  hosts:
    - api-service
    - api.example.com
  gateways:
    - api-gateway
  http:
    # Canary deployment (10% to v1.3.0)
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: api-service
            subset: canary
          weight: 100
    - route:
        - destination:
            host: api-service
            subset: stable
          weight: 90
        - destination:
            host: api-service
            subset: canary
          weight: 10
```

**Destination Rule** (load balancing, circuit breaker):
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-service
  namespace: production
spec:
  host: api-service
  trafficPolicy:
    loadBalancer:
      simple: LEAST_REQUEST
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 40
  subsets:
    - name: stable
      labels:
        version: v1.2.3
    - name: canary
      labels:
        version: v1.3.0
```

**Gateway** (Ingress):
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: api-gateway
  namespace: production
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: api-tls-cert
      hosts:
        - api.example.com
```

**mTLS Policy** (secure service-to-service):
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Require mTLS for all services
```

---

### Pattern 4: GitOps with ArgoCD/Flux

**Best for**: Continuous deployment, declarative infrastructure

```yaml
import:
  - patterns/infrastructure/k8s_gitops_argocd.yaml

gitops:
  tool: argocd  # or flux
  repo: https://github.com/myorg/k8s-manifests
  branch: main
  path: apps/crm-backend
  sync_policy:
    automated: true
    prune: true  # Delete resources not in Git
    self_heal: true  # Auto-fix drift

environments:
  - name: staging
    branch: staging
    namespace: staging
    values: values-staging.yaml

  - name: production
    branch: main
    namespace: production
    values: values-prod.yaml
    manual_sync: true  # Require approval
```

**Generated ArgoCD Application**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: crm-backend-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/k8s-manifests
    targetRevision: main
    path: apps/crm-backend
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## Kubernetes Best Practices

### Resource Requests & Limits

**Why?** Ensures proper scheduling and prevents resource starvation.

```yaml
resources:
  requests:  # Minimum guaranteed
    cpu: 500m      # 0.5 CPU cores
    memory: 1Gi    # 1 gigabyte RAM
  limits:    # Maximum allowed
    cpu: 2         # 2 CPU cores
    memory: 4Gi    # 4 gigabytes RAM
```

**Best Practices**:
- ✅ Always set requests (for scheduling)
- ✅ Set limits to prevent runaway processes
- ✅ requests ≤ limits
- ✅ Monitor actual usage and adjust

### Health Checks

**Liveness Probe** (restart if unhealthy):
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30  # Wait for app startup
  periodSeconds: 10        # Check every 10 seconds
  timeoutSeconds: 5
  failureThreshold: 3      # Restart after 3 failures
```

**Readiness Probe** (remove from load balancer if not ready):
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

**Startup Probe** (for slow-starting apps):
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 0
  periodSeconds: 10
  failureThreshold: 30  # Allow up to 300 seconds to start
```

### Pod Disruption Budgets

**Ensures high availability during voluntary disruptions** (node drains, upgrades):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-service-pdb
  namespace: production
spec:
  minAvailable: 2  # At least 2 pods must remain available
  selector:
    matchLabels:
      app: api-service
```

Or:
```yaml
spec:
  maxUnavailable: 1  # At most 1 pod can be unavailable
```

### Network Policies

**Restrict network traffic** (default deny):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-service-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow from ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    # Allow to database
    - to:
        - podSelector:
            matchLabels:
              app: crm-db
      ports:
        - protocol: TCP
          port: 5432
    # Allow DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

---

## Monitoring & Observability

### Prometheus & Grafana

**ServiceMonitor** (Prometheus Operator):
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-service
  namespace: production
  labels:
    app: api-service
spec:
  selector:
    matchLabels:
      app: api-service
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

**Grafana Dashboard** (auto-generated):
- Pod CPU/Memory usage
- Request rate (RPS)
- Error rate
- Response time (p50, p95, p99)
- Pod count over time

### Distributed Tracing (Jaeger/Tempo)

**Inject sidecar**:
```yaml
# Automatic with Istio
apiVersion: v1
kind: Pod
metadata:
  annotations:
    sidecar.istio.io/inject: "true"
```

**Manual instrumentation** (OpenTelemetry):
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="jaeger-collector:4317"))
)
trace.set_tracer_provider(tracer_provider)
```

### Logging (EFK Stack)

**Elasticsearch, Fluent Bit, Kibana**:

```yaml
# Fluent Bit DaemonSet (auto-collects logs)
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    spec:
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:latest
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
```

---

## Storage Classes

**Performance tiers**:

| Provider | Storage Class | Type | IOPS | Use Case | Cost |
|----------|---------------|------|------|----------|------|
| **AWS** | gp3 | SSD | 3,000-16,000 | General purpose | $$ |
| **AWS** | io2 | SSD | 64,000+ | High-performance DB | $$$$ |
| **GCP** | pd-standard | HDD | Baseline | Archives | $ |
| **GCP** | pd-ssd | SSD | High | Databases | $$$ |
| **Azure** | managed-premium | SSD | High | Production | $$$ |

**Example**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "10000"
  throughput: "500"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

---

## Secrets Management

### Sealed Secrets

**Encrypt secrets in Git**:

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
echo -n 'super-secret-password' | kubectl create secret generic db-password \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

# Commit sealed-secret.yaml to Git (safe!)
```

### External Secrets Operator

**Pull secrets from external vaults**:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager  # or vault, gcp, azure
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: crm-backend-db-password
```

---

## Cost Optimization

### Cluster Autoscaler

**Auto-scale nodes** based on pod demand:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: ClusterAutoscaler
metadata:
  name: cluster-autoscaler
spec:
  scaleDown:
    enabled: true
    delayAfterAdd: 10m
    delayAfterDelete: 10s
    delayAfterFailure: 3m
    unneededTime: 10m
  scaleUp:
    maxNodeProvisionTime: 15m
```

### Vertical Pod Autoscaler (VPA)

**Right-size resource requests**:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-service-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  updatePolicy:
    updateMode: "Auto"  # Automatically apply recommendations
```

### Spot/Preemptible Nodes

**70-90% cost savings**:

**AWS (Spot)**:
```yaml
apiVersion: karpenter.sh/v1alpha5
kind: Provisioner
metadata:
  name: spot-nodes
spec:
  requirements:
    - key: karpenter.sh/capacity-type
      operator: In
      values: ["spot"]
  limits:
    resources:
      cpu: 1000
```

**GCP (Preemptible)**:
```bash
gcloud container node-pools create spot-pool \
  --cluster=my-cluster \
  --preemptible \
  --num-nodes=5 \
  --enable-autoscaling \
  --min-nodes=0 \
  --max-nodes=20
```

---

## Next Steps

- [AWS EKS Guide](aws-deployment.md#eks) - Amazon Elastic Kubernetes Service
- [GCP GKE Guide](gcp-deployment.md#gke) - Google Kubernetes Engine
- [Azure AKS Guide](azure-deployment.md#aks) - Azure Kubernetes Service
- [Cost Optimization](cost-optimization.md) - Multi-cloud cost comparison

---

**Kubernetes deployment with SpecQL means cloud-native infrastructure without the complexity. From YAML to production-grade K8s resources with best practices, observability, and GitOps built-in.**

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete Kubernetes deployment guide (manifests, Helm, Istio, monitoring, best practices)
