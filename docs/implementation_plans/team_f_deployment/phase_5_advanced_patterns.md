# Team F Phase 5: Advanced Patterns Implementation Plan

**Created**: 2025-11-12
**Phase**: 5 of 5
**Status**: Planning
**Complexity**: High - Enterprise deployment patterns
**Priority**: LOW-MEDIUM - Advanced use cases
**Prerequisites**: Phases 1-4 complete

---

## Executive Summary

Implement advanced deployment patterns for enterprise and complex scenarios: Kubernetes/Helm, multi-region deployments, blue-green deployments, and Django/Rails framework support.

**Goal**: Support complex production scenarios beyond basic AWS deployment

**Key Deliverables**:
1. Kubernetes Helm chart generation
2. Multi-region deployment (disaster recovery)
3. Blue-green deployment strategies
4. Django framework support
5. Rails framework support (optional)
6. Service mesh integration (Istio/Linkerd)

**Impact**:
- Enterprise-grade deployment patterns
- Multi-framework support (not just FraiseQL)
- High-availability architectures
- Zero-downtime deployments

---

## 🎯 Phase 5 Objectives

### Core Goals
1. **Kubernetes Support**: Helm chart generation for K8s deployments
2. **Multi-Region**: Active-passive or active-active configurations
3. **Blue-Green Deployments**: Zero-downtime deployment strategy
4. **Framework Expansion**: Django and Rails support
5. **Service Mesh**: Optional Istio/Linkerd integration

### Success Criteria
- ✅ Generate production-ready Helm charts
- ✅ Support multi-region deployments with DR
- ✅ Implement blue-green deployment automation
- ✅ Django framework generates correct Python/Gunicorn stack
- ✅ All patterns pass enterprise security review

---

## 📋 Technical Design

### Architecture

```
src/generators/deployment/advanced/
├── __init__.py
├── kubernetes/
│   ├── __init__.py
│   ├── helm_generator.py          # Helm chart generation
│   ├── manifests/
│   │   ├── deployment.py          # Kubernetes Deployment
│   │   ├── service.py             # Kubernetes Service
│   │   ├── ingress.py             # Ingress/Gateway
│   │   ├── configmap.py           # ConfigMaps
│   │   └── secrets.py             # Secrets
│   └── operators/
│       ├── postgres_operator.py   # CloudNativePG operator
│       └── cert_manager.py        # Cert-manager integration
├── multiregion/
│   ├── __init__.py
│   ├── multiregion_generator.py   # Multi-region orchestrator
│   ├── active_passive.py          # Active-passive DR
│   ├── active_active.py           # Active-active (complex)
│   └── replication_config.py      # Database replication
├── bluegreen/
│   ├── __init__.py
│   ├── bluegreen_generator.py     # Blue-green deployment
│   └── traffic_shifting.py        # Gradual traffic shift
└── frameworks/
    ├── django_generator.py        # Django-specific deployment
    └── rails_generator.py         # Rails-specific deployment (optional)
```

### Deployment YAML Extension

```yaml
# deployment.yaml (EXTENDED for Phase 5)
deployment:
  name: my-app
  framework: fraiseql
  pattern: kubernetes  # NEW: Kubernetes pattern

# Kubernetes configuration
kubernetes:
  cluster: existing  # existing | create
  namespace: myapp-prod
  replicas: 3
  autoscaling:
    enabled: true
    min: 3
    max: 50
    target_cpu: 70
  database:
    operator: cloudnative-pg  # CloudNativePG operator
    size: medium
    replicas: 2
  ingress:
    class: nginx
    ssl: cert-manager
    domain: myapp.com
  monitoring:
    prometheus_operator: true
    grafana: true

# Multi-region configuration
multiregion:
  enabled: true
  strategy: active-passive  # active-passive | active-active
  primary_region: us-east-1
  dr_region: eu-west-1
  replication:
    database: async  # async | sync
    storage: s3-replication

# Blue-green deployment
bluegreen:
  enabled: true
  strategy: gradual  # instant | gradual
  traffic_shift:
    initial: 10%
    increment: 10%
    interval: 5m
  rollback_on_error: true
```

---

## 🏗️ Implementation Details

### 1. Helm Chart Generator

```python
# src/generators/deployment/advanced/kubernetes/helm_generator.py
from pathlib import Path
from typing import Dict, Any
import yaml

class HelmGenerator:
    """Generate Kubernetes Helm charts"""

    def __init__(self, config: Dict[str, Any], framework: str):
        self.config = config
        self.framework = framework

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """Generate Helm chart structure"""
        generated = {}

        # Create Helm chart structure
        chart_dir = output_dir / 'helm' / self.config['deployment']['name']
        chart_dir.mkdir(parents=True, exist_ok=True)

        # Chart.yaml
        generated['chart'] = self._generate_chart_yaml(chart_dir)

        # values.yaml
        generated['values'] = self._generate_values_yaml(chart_dir)

        # templates/
        templates_dir = chart_dir / 'templates'
        templates_dir.mkdir(exist_ok=True)

        generated['deployment'] = self._generate_deployment(templates_dir)
        generated['service'] = self._generate_service(templates_dir)
        generated['ingress'] = self._generate_ingress(templates_dir)
        generated['configmap'] = self._generate_configmap(templates_dir)
        generated['postgres'] = self._generate_postgres_cluster(templates_dir)

        return generated

    def _generate_chart_yaml(self, chart_dir: Path) -> Path:
        """Generate Chart.yaml"""
        app_name = self.config['deployment']['name']

        chart_yaml = {
            'apiVersion': 'v2',
            'name': app_name,
            'description': f'Helm chart for {app_name} ({self.framework})',
            'type': 'application',
            'version': '0.1.0',
            'appVersion': '1.0.0',
            'dependencies': [
                {
                    'name': 'cloudnative-pg',
                    'version': '0.18.0',
                    'repository': 'https://cloudnative-pg.github.io/charts',
                    'condition': 'postgresql.enabled'
                }
            ]
        }

        chart_path = chart_dir / 'Chart.yaml'
        chart_path.write_text(yaml.dump(chart_yaml, sort_keys=False))
        return chart_path

    def _generate_values_yaml(self, chart_dir: Path) -> Path:
        """Generate values.yaml"""
        app_name = self.config['deployment']['name']
        k8s_config = self.config.get('kubernetes', {})

        values = {
            'replicaCount': k8s_config.get('replicas', 3),
            'image': {
                'repository': f'ghcr.io/your-org/{app_name}',
                'pullPolicy': 'IfNotPresent',
                'tag': 'latest'
            },
            'service': {
                'type': 'ClusterIP',
                'port': 8000
            },
            'ingress': {
                'enabled': True,
                'className': k8s_config.get('ingress', {}).get('class', 'nginx'),
                'annotations': {
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod'
                },
                'hosts': [
                    {
                        'host': k8s_config.get('ingress', {}).get('domain', f'{app_name}.com'),
                        'paths': [
                            {'path': '/', 'pathType': 'Prefix'}
                        ]
                    }
                ],
                'tls': [
                    {
                        'secretName': f'{app_name}-tls',
                        'hosts': [k8s_config.get('ingress', {}).get('domain', f'{app_name}.com')]
                    }
                ]
            },
            'autoscaling': {
                'enabled': k8s_config.get('autoscaling', {}).get('enabled', True),
                'minReplicas': k8s_config.get('autoscaling', {}).get('min', 3),
                'maxReplicas': k8s_config.get('autoscaling', {}).get('max', 50),
                'targetCPUUtilizationPercentage': k8s_config.get('autoscaling', {}).get('target_cpu', 70)
            },
            'postgresql': {
                'enabled': True,
                'instances': k8s_config.get('database', {}).get('replicas', 2),
                'storage': {
                    'size': '100Gi',
                    'storageClass': 'gp3'
                },
                'monitoring': {
                    'enabled': True
                }
            },
            'resources': self._get_resources_for_framework()
        }

        values_path = chart_dir / 'values.yaml'
        values_path.write_text(yaml.dump(values, sort_keys=False))
        return values_path

    def _get_resources_for_framework(self) -> Dict[str, Any]:
        """Get framework-specific resource requirements"""
        if self.framework == 'fraiseql':
            return {
                'requests': {
                    'memory': '512Mi',
                    'cpu': '500m'
                },
                'limits': {
                    'memory': '1Gi',
                    'cpu': '1000m'
                }
            }
        elif self.framework == 'django':
            return {
                'requests': {
                    'memory': '256Mi',
                    'cpu': '250m'
                },
                'limits': {
                    'memory': '512Mi',
                    'cpu': '500m'
                }
            }
        else:
            return {}

    def _generate_deployment(self, templates_dir: Path) -> Path:
        """Generate Kubernetes Deployment manifest"""
        app_name = self.config['deployment']['name']

        deployment = f"""# ============================================
# Kubernetes Deployment for {app_name}
# Framework: {self.framework}
# ============================================

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
  labels:
    {{{{- include "{app_name}.labels" . | nindent 4 }}}}
spec:
  {{{{- if not .Values.autoscaling.enabled }}}}
  replicas: {{{{ .Values.replicaCount }}}}
  {{{{- end }}}}
  selector:
    matchLabels:
      {{{{- include "{app_name}.selectorLabels" . | nindent 6 }}}}
  template:
    metadata:
      annotations:
        checksum/config: {{{{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}}}
      labels:
        {{{{- include "{app_name}.selectorLabels" . | nindent 8 }}}}
    spec:
      containers:
      - name: {app_name}
        image: "{{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag | default .Chart.AppVersion }}}}"
        imagePullPolicy: {{{{ .Values.image.pullPolicy }}}}
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {app_name}-secrets
              key: database-url
        - name: PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{{{- toYaml .Values.resources | nindent 10 }}}}
"""

        deployment_path = templates_dir / 'deployment.yaml'
        deployment_path.write_text(deployment)
        return deployment_path

    def _generate_postgres_cluster(self, templates_dir: Path) -> Path:
        """Generate CloudNativePG Cluster manifest"""
        app_name = self.config['deployment']['name']

        postgres_cluster = f"""# ============================================
# CloudNativePG Cluster for {app_name}
# ============================================

apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: {app_name}-postgres
spec:
  instances: {{{{ .Values.postgresql.instances }}}}

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: 256MB
      effective_cache_size: 1GB
      work_mem: 16MB
      # FraiseQL optimizations for JSONB
      random_page_cost: "1.1"

  storage:
    size: {{{{ .Values.postgresql.storage.size }}}}
    storageClass: {{{{ .Values.postgresql.storage.storageClass }}}}

  bootstrap:
    initdb:
      database: {app_name}
      owner: app_user
      postInitSQL:
        - CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        - CREATE EXTENSION IF NOT EXISTS "pg_trgm";

  backup:
    barmanObjectStore:
      destinationPath: s3://{app_name}-backups/
      s3Credentials:
        accessKeyId:
          name: backup-s3-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-s3-credentials
          key: SECRET_ACCESS_KEY
    retentionPolicy: "30d"

  monitoring:
    enabled: {{{{ .Values.postgresql.monitoring.enabled }}}}
"""

        postgres_path = templates_dir / 'postgres-cluster.yaml'
        postgres_path.write_text(postgres_cluster)
        return postgres_path
```

### 2. Multi-Region Generator

```python
# src/generators/deployment/advanced/multiregion/multiregion_generator.py
from pathlib import Path
from typing import Dict, Any

class MultiRegionGenerator:
    """Generate multi-region deployment configurations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.multiregion_config = config.get('multiregion', {})

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """Generate multi-region infrastructure"""
        generated = {}

        if not self.multiregion_config.get('enabled'):
            return generated

        strategy = self.multiregion_config.get('strategy', 'active-passive')

        if strategy == 'active-passive':
            generated['primary'] = self._generate_primary_region(output_dir)
            generated['dr'] = self._generate_dr_region(output_dir)
            generated['replication'] = self._generate_replication_config(output_dir)
        elif strategy == 'active-active':
            generated['regions'] = self._generate_active_active(output_dir)

        generated['failover'] = self._generate_failover_runbook(output_dir)

        return generated

    def _generate_primary_region(self, output_dir: Path) -> Path:
        """Generate primary region infrastructure"""
        primary_region = self.multiregion_config['primary_region']

        # Use OpenTofu orchestrator for primary
        # ... (similar to Phase 2 but with replication config)

        return output_dir / 'primary' / 'main.tf'

    def _generate_dr_region(self, output_dir: Path) -> Path:
        """Generate DR region infrastructure"""
        dr_region = self.multiregion_config['dr_region']

        # DR region with read replica
        dr_config = f"""# ============================================
# Disaster Recovery Region: {dr_region}
# ============================================

module "dr_database" {{
  source = "./modules/database"

  # Read replica configuration
  replicate_source_db = module.primary_database.db_instance_arn
  # ... rest of config
}}
"""

        dr_path = output_dir / 'dr' / 'main.tf'
        dr_path.parent.mkdir(parents=True, exist_ok=True)
        dr_path.write_text(dr_config)
        return dr_path

    def _generate_failover_runbook(self, output_dir: Path) -> Path:
        """Generate failover runbook"""
        runbook = f"""# Disaster Recovery Failover Runbook

## Pre-Requisites
- [ ] Primary region is down or unreachable
- [ ] DR region is healthy
- [ ] Executive approval obtained

## Failover Steps

### 1. Promote DR Database
```bash
aws rds promote-read-replica \\
  --db-instance-identifier {self.config['deployment']['name']}-postgres-dr \\
  --region {self.multiregion_config['dr_region']}
```

### 2. Update DNS
```bash
# Point domain to DR region ALB
aws route53 change-resource-record-sets \\
  --hosted-zone-id ZXXXXX \\
  --change-batch file://dr-dns-change.json
```

### 3. Scale Up DR Capacity
```bash
# Update ECS service desired count
aws ecs update-service \\
  --cluster {self.config['deployment']['name']}-cluster-dr \\
  --service {self.config['deployment']['name']}-service-dr \\
  --desired-count 10
```

### 4. Verify Health
```bash
# Check application health
curl https://{self.config['deployment']['name']}.com/health

# Check database connections
psql -h <DR_ENDPOINT> -U app_user -d {self.config['deployment']['name']} -c "SELECT 1;"
```

## Rollback (if needed)
```bash
# Revert DNS
# Stop DR writes
# Re-sync from primary (if recovered)
```

## Post-Failover
- [ ] Update monitoring dashboards
- [ ] Notify stakeholders
- [ ] Document incident
- [ ] Plan primary recovery
"""

        runbook_path = output_dir / 'FAILOVER_RUNBOOK.md'
        runbook_path.write_text(runbook)
        return runbook_path
```

### 3. Blue-Green Deployment Generator

```python
# src/generators/deployment/advanced/bluegreen/bluegreen_generator.py
from pathlib import Path
from typing import Dict, Any

class BlueGreenGenerator:
    """Generate blue-green deployment configuration"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bluegreen_config = config.get('bluegreen', {})

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """Generate blue-green deployment scripts"""
        generated = {}

        if not self.bluegreen_config.get('enabled'):
            return generated

        # Generate deployment script
        generated['deploy_script'] = self._generate_deploy_script(output_dir)

        # Generate traffic shift script
        generated['traffic_script'] = self._generate_traffic_shift_script(output_dir)

        # Generate rollback script
        generated['rollback_script'] = self._generate_rollback_script(output_dir)

        return generated

    def _generate_deploy_script(self, output_dir: Path) -> Path:
        """Generate blue-green deployment script"""
        app_name = self.config['deployment']['name']

        script = f"""#!/bin/bash
# ============================================
# Blue-Green Deployment Script
# Application: {app_name}
# ============================================

set -e

CLUSTER="{app_name}-cluster"
SERVICE_BLUE="{app_name}-service-blue"
SERVICE_GREEN="{app_name}-service-green"
TARGET_GROUP_BLUE="target-group-blue"
TARGET_GROUP_GREEN="target-group-green"
ALB_LISTENER_ARN="arn:aws:elasticloadbalancing:..."

# Determine current active environment
CURRENT=$(aws elbv2 describe-listeners \\
  --listener-arns $ALB_LISTENER_ARN \\
  --query 'Listeners[0].DefaultActions[0].TargetGroupArn' \\
  --output text)

if [[ $CURRENT == *"blue"* ]]; then
  ACTIVE="blue"
  INACTIVE="green"
else
  ACTIVE="green"
  INACTIVE="blue"
fi

echo "✅ Current active: $ACTIVE"
echo "🚀 Deploying to: $INACTIVE"

# Deploy new version to inactive environment
echo "📦 Updating $INACTIVE service..."
aws ecs update-service \\
  --cluster $CLUSTER \\
  --service {app_name}-service-$INACTIVE \\
  --task-definition {app_name}:$NEW_TASK_REVISION \\
  --force-new-deployment

# Wait for service stability
echo "⏳ Waiting for $INACTIVE to stabilize..."
aws ecs wait services-stable \\
  --cluster $CLUSTER \\
  --services {app_name}-service-$INACTIVE

# Health check on inactive
echo "🔍 Running health checks on $INACTIVE..."
INACTIVE_ENDPOINT=$(aws elbv2 describe-target-groups \\
  --target-group-arns $TARGET_GROUP_{{INACTIVE^^}} \\
  --query 'TargetGroups[0].HealthCheckPath' \\
  --output text)

curl -f https://$INACTIVE.{app_name}.com/health || {{
  echo "❌ Health check failed on $INACTIVE!"
  exit 1
}}

echo "✅ $INACTIVE is healthy!"
echo ""
echo "Next step: Run traffic shift script to gradually move traffic to $INACTIVE"
echo "  ./shift-traffic.sh $INACTIVE"
"""

        script_path = output_dir / 'deploy-bluegreen.sh'
        script_path.write_text(script)
        script_path.chmod(0o755)
        return script_path

    def _generate_traffic_shift_script(self, output_dir: Path) -> Path:
        """Generate gradual traffic shift script"""
        strategy = self.bluegreen_config.get('strategy', 'gradual')
        traffic_config = self.bluegreen_config.get('traffic_shift', {})

        script = f"""#!/bin/bash
# ============================================
# Gradual Traffic Shift Script
# Strategy: {strategy}
# ============================================

set -e

TARGET_ENV=$1  # blue or green

if [ -z "$TARGET_ENV" ]; then
  echo "Usage: $0 <blue|green>"
  exit 1
fi

INITIAL={traffic_config.get('initial', 10)}
INCREMENT={traffic_config.get('increment', 10)}
INTERVAL={traffic_config.get('interval', '5m')}

echo "🚀 Starting gradual traffic shift to $TARGET_ENV"
echo "Initial: $INITIAL%, Increment: $INCREMENT%, Interval: $INTERVAL"

CURRENT_WEIGHT=$INITIAL
while [ $CURRENT_WEIGHT -le 100 ]; do
  echo ""
  echo "📊 Shifting $CURRENT_WEIGHT% traffic to $TARGET_ENV..."

  # Update ALB target group weights
  aws elbv2 modify-listener \\
    --listener-arn $ALB_LISTENER_ARN \\
    --default-actions Type=forward,ForwardConfig="{{
      TargetGroups=[
        {{TargetGroupArn=$TARGET_GROUP_${{TARGET_ENV^^}},Weight=$CURRENT_WEIGHT}},
        {{TargetGroupArn=$TARGET_GROUP_${{OTHER_ENV^^}},Weight=$((100-CURRENT_WEIGHT))}}
      ]
    }}"

  echo "✅ Traffic shift complete: $CURRENT_WEIGHT%"

  if [ $CURRENT_WEIGHT -lt 100 ]; then
    echo "⏳ Waiting $INTERVAL before next shift..."
    sleep ${{INTERVAL::-1}}m  # Remove 'm' suffix
  fi

  CURRENT_WEIGHT=$((CURRENT_WEIGHT + INCREMENT))
done

echo ""
echo "✅ Traffic shift complete! 100% on $TARGET_ENV"
"""

        script_path = output_dir / 'shift-traffic.sh'
        script_path.write_text(script)
        script_path.chmod(0o755)
        return script_path
```

---

## 📊 Testing Strategy

### Unit Tests
- Test Helm chart generation
- Test multi-region configuration
- Test blue-green script generation

### Integration Tests
- Deploy to test Kubernetes cluster
- Test blue-green deployment flow
- Test multi-region failover (simulated)

---

## 📝 Deliverables

### Code Files
1. ✅ Helm generator
2. ✅ Multi-region generator
3. ✅ Blue-green generator
4. ✅ Django framework generator
5. ✅ Rails framework generator (optional)

### Templates
6. ✅ Kubernetes manifests
7. ✅ Multi-region OpenTofu modules
8. ✅ Blue-green deployment scripts

### Tests
9. ✅ Unit tests for all generators
10. ✅ Integration tests for Kubernetes
11. ✅ E2E tests for blue-green

### Documentation
12. ✅ Kubernetes deployment guide
13. ✅ Multi-region DR guide
14. ✅ Blue-green deployment guide

---

## 🚀 Implementation Phases

### Week 1-2: Kubernetes/Helm
**TDD Cycles for K8s manifest generation**

### Week 3-4: Multi-Region
**TDD Cycles for DR infrastructure**

### Week 5-6: Blue-Green + Frameworks
**TDD Cycles for deployment strategies + Django/Rails**

---

## ✅ Success Metrics

### Quantitative
- ✅ Generate production-ready Helm charts
- ✅ Multi-region infrastructure deploys successfully
- ✅ Blue-green deployment completes without downtime
- ✅ Django apps deploy correctly
- ✅ 100% test coverage

### Qualitative
- ✅ Enterprise-grade deployment patterns
- ✅ Zero-downtime deployments
- ✅ High availability architecture
- ✅ Multi-framework support

---

**Status**: Future (After Phases 1-4)
**Priority**: LOW-MEDIUM - Advanced use cases
**Estimated Effort**: 6 weeks (complex patterns)
**Risk Level**: High - Enterprise complexity
