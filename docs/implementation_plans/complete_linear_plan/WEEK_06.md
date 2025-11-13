# Week 06: Infrastructure Migration

**Objective**: Document infrastructure and convert to universal format

## Day 1-2: Infrastructure Inventory

```bash
cd ../printoptim_migration

# Document current infrastructure
cat > infrastructure/CURRENT_INFRA.md << 'EOF'
# PrintOptim Current Infrastructure

## Compute
- Type: Hetzner bare metal servers
- Count: 3 (1 API, 1 worker, 1 database)
- Specs: CX31 (2 vCPU, 8GB RAM)

## Database
- PostgreSQL 15
- Storage: 100GB SSD
- Backups: Daily automated

## Networking
- Load balancer: Hetzner Load Balancer
- SSL: Let's Encrypt
- Domain: api.printoptim.com

## Monitoring
- Logs: journald → Loki
- Metrics: node_exporter → Prometheus
- Alerting: Alertmanager
EOF
```

## Day 3-4: Reverse Engineer to Universal Format

```bash
cd /home/lionel/code/specql

# Reverse engineer existing infrastructure scripts
uv run specql infrastructure reverse \
  ../printoptim_migration/infrastructure/hetzner_setup.sh \
  --output ../printoptim_migration/infrastructure/universal_infra.yaml \
  --provider hetzner

# Or create manually from inventory
cat > ../printoptim_migration/infrastructure/universal_infra.yaml << 'EOF'
service: printoptim_api
provider: hetzner
region: eu-central

compute:
  api_server:
    type: cx31
    count: 1
  worker_server:
    type: cx31
    count: 1

database:
  type: postgresql
  version: 15
  storage: 100GB
  backups:
    frequency: daily
    retention: 30

networking:
  load_balancer:
    enabled: true
    type: lb11
  ssl:
    provider: letsencrypt
    auto_renew: true
  domain: api.printoptim.com

observability:
  logs:
    provider: loki
    retention: 30d
  metrics:
    provider: prometheus
    retention: 90d
  alerting:
    provider: alertmanager
EOF
```

## Day 5: Generate Infrastructure Code

```bash
# Generate Terraform for Hetzner
uv run specql infrastructure convert \
  ../printoptim_migration/infrastructure/universal_infra.yaml \
  terraform-hetzner \
  --output ../printoptim_migration/infrastructure/terraform/

# Generate Kubernetes manifests (if migrating to K8s)
uv run specql infrastructure convert \
  ../printoptim_migration/infrastructure/universal_infra.yaml \
  kubernetes \
  --output ../printoptim_migration/infrastructure/k8s/
```

## Deliverables

- ✅ Current infrastructure documented
- ✅ Universal infrastructure YAML
- ✅ Terraform/K8s manifests generated
- ✅ Infrastructure migration plan