"""Tests for Kubernetes → Universal Infrastructure parser"""

import pytest
from src.infrastructure.parsers.kubernetes_parser import KubernetesParser
from src.infrastructure.universal_infra_schema import *


class TestKubernetesParser:
    """Test parsing Kubernetes manifests to universal format"""

    @pytest.fixture
    def parser(self):
        return KubernetesParser()

    def test_parse_deployment_with_service(self, parser):
        """Test parsing basic Deployment + Service"""
        k8s_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: default
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
"""

        # Act
        infra = parser.parse(k8s_content)

        # Assert
        assert infra.name == "web-app"
        assert infra.provider == CloudProvider.KUBERNETES

        # Container config
        assert infra.container is not None
        assert infra.container.image == "nginx:1.21"
        assert infra.container.port == 80
        assert infra.container.cpu_request == 0.1
        assert infra.container.memory_request == "128Mi"
        assert infra.container.cpu_limit == 0.2
        assert infra.container.memory_limit == "256Mi"
        assert infra.container.health_check_path == "/health"

        # Compute config (from replicas)
        assert infra.compute is not None
        assert infra.compute.instances == 3

        # Load balancer
        assert infra.load_balancer is not None
        assert infra.load_balancer.enabled == True
        assert infra.load_balancer.type == "network"  # LoadBalancer service

    def test_parse_stateful_set_with_pvc(self, parser):
        """Test parsing StatefulSet with PersistentVolumeClaim"""
        k8s_content = """
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-db
spec:
  replicas: 1
  serviceName: postgres
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
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: admin
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
    name: postgres-storage
    labels:
      app: postgres
    annotations:
      volume.beta.kubernetes.io/storage-class: "fast-ssd"
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
"""

        # Act
        infra = parser.parse(k8s_content)

        # Assert
        assert infra.name == "postgres-db"
        assert infra.provider == CloudProvider.KUBERNETES

        # Database config
        assert infra.database is not None
        assert infra.database.type == DatabaseType.POSTGRESQL
        assert infra.database.version == "15"

        # Container config
        assert infra.container is not None
        assert infra.container.image == "postgres:15"
        assert infra.container.port == 5432

        # Storage
        assert len(infra.volumes) == 1
        assert infra.volumes[0].size == "50Gi"
        assert infra.volumes[0].mount_path == "/var/lib/postgresql/data"

    def test_parse_ingress_with_tls(self, parser):
        """Test parsing Ingress with TLS configuration"""
        k8s_content = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 80
"""

        # Act
        infra = parser.parse(k8s_content)

        # Assert
        assert infra.name == "web-ingress"
        assert infra.provider == CloudProvider.KUBERNETES

        # Load balancer with HTTPS
        assert infra.load_balancer is not None
        assert infra.load_balancer.enabled == True
        assert infra.load_balancer.https == True
        assert infra.load_balancer.certificate_domain == "api.example.com"

    def test_parse_configmap_and_secret(self, parser):
        """Test parsing ConfigMap and Secret resources"""
        k8s_content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  LOG_LEVEL: INFO
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  DATABASE_URL: cG9zdGdyZXM6Ly91c2VyOnBhc3NAZGI6NTQzMi9teWRi
  API_KEY: bXlhcGlrZXk=
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: web
        image: myapp:latest
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
"""

        # Act
        infra = parser.parse(k8s_content)

        # Assert
        assert infra.name == "web-app"
        assert infra.provider == CloudProvider.KUBERNETES

        # Environment variables
        assert infra.container is not None
        assert "APP_ENV" in infra.container.environment
        assert infra.container.environment["APP_ENV"] == "production"

        # Secrets
        assert "DATABASE_URL" in infra.container.secrets
        assert "API_KEY" in infra.container.secrets