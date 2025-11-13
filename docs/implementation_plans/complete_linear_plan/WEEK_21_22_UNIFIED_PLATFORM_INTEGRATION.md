# Weeks 21-22: Unified Platform Integration & Semantic Intelligence

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: Integrate all three domains (Database, CI/CD, Infrastructure) with unified semantic search and LLM enhancement

**Prerequisites**: Weeks 18-20 complete (Universal Infrastructure)
**Output**: Single unified platform with cross-domain intelligence

---

## 🎯 Executive Summary

**The Vision**: One universal expression language for **all technical implementation**

```yaml
# Single project.specql.yaml defines EVERYTHING

project: my_saas_application
description: "SaaS platform for project management"

# ============================================================================
# DOMAIN 1: Database Schema (from Weeks 1-14)
# ============================================================================
database:
  schema_type: multi_tenant
  entities:
    - entity: Project
      fields:
        name: text!
        owner: ref(User)
        status: enum(active, archived)

    - entity: Task
      fields:
        title: text!
        project: ref(Project)
        assignee: ref(User)

  actions:
    - name: create_task
      steps:
        - validate: project.status = 'active'
        - insert: Task
        - notify: assignee

# ============================================================================
# DOMAIN 2: CI/CD Pipeline (from Weeks 15-17)
# ============================================================================
ci_cd:
  platform: github-actions
  language: python
  framework: fastapi

  stages:
    - name: test
      jobs: [lint, unit_tests, integration_tests]

    - name: deploy
      environment: production
      approval_required: true

# ============================================================================
# DOMAIN 3: Infrastructure (from Weeks 18-20)
# ============================================================================
infrastructure:
  provider: aws
  region: us-east-1

  compute:
    instances: 3
    auto_scale: true
    min: 2
    max: 10

  database:
    type: postgresql
    version: "15"
    storage: 100GB
    multi_az: true

  load_balancer:
    https: true
    domain: api.example.com

  observability:
    logging: true
    metrics: prometheus
    tracing: jaeger

# ============================================================================
# UNIFIED: One Command to Rule Them All
# ============================================================================
```

**One Command**:
```bash
specql deploy project.specql.yaml

# Generates:
# ✅ 5,000+ lines PostgreSQL (schema + actions)
# ✅ 500+ lines GitHub Actions workflows
# ✅ 2,000+ lines Terraform/Kubernetes
# ✅ Complete production deployment ready
```

### Success Criteria

- [ ] Single unified project specification
- [ ] Cross-domain semantic search (find similar projects across DB/CI/CD/Infra)
- [ ] LLM-powered recommendations spanning all domains
- [ ] Automatic dependency resolution (DB schema → migrations → CI/CD tests → infra deployment)
- [ ] Pattern library unified across all domains
- [ ] Single CLI for all operations
- [ ] Complete documentation

---

## Week 21: Unified Domain Integration

**Objective**: Integrate database, CI/CD, and infrastructure into single cohesive system

### Day 1: Unified Project Schema

**Morning Block (4 hours): Project Definition Schema**

#### 1. Design Unified Schema (2 hours)

**Unified Project Schema**: `src/unified/project_schema.py`

```python
"""
Unified Project Schema

Single source of truth for database, CI/CD, and infrastructure definitions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from src.core.specql_parser import Entity
from src.cicd.universal_pipeline_schema import UniversalPipeline
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


@dataclass
class UnifiedProject:
    """
    Complete project specification spanning all domains

    This is the single YAML that defines everything:
    - Database schema and business logic
    - CI/CD pipelines
    - Infrastructure
    """

    # Project metadata
    name: str
    description: str = ""
    version: str = "1.0.0"
    team: Optional[str] = None

    # ========================================================================
    # DOMAIN 1: Database Schema
    # ========================================================================
    database: Optional['DatabaseDefinition'] = None

    # ========================================================================
    # DOMAIN 2: CI/CD Pipeline
    # ========================================================================
    ci_cd: Optional[UniversalPipeline] = None

    # ========================================================================
    # DOMAIN 3: Infrastructure
    # ========================================================================
    infrastructure: Optional[UniversalInfrastructure] = None

    # ========================================================================
    # Cross-Domain Configuration
    # ========================================================================
    environments: List['Environment'] = field(default_factory=list)

    # Pattern metadata (for unified pattern library)
    pattern_id: Optional[str] = None
    category: str = "full_stack"  # full_stack, backend, frontend, data, ml
    tags: List[str] = field(default_factory=list)

    # Semantic search
    embedding: Optional[List[float]] = None

    # Estimated costs
    estimated_monthly_cost: Optional[float] = None


@dataclass
class DatabaseDefinition:
    """Database schema definition"""
    schema_type: str = "multi_tenant"  # framework, multi_tenant, shared
    entities: List[Entity] = field(default_factory=list)
    actions: List[Any] = field(default_factory=list)  # From action compiler

    # Database configuration
    migrations_path: str = "migrations/"
    seed_data_path: Optional[str] = None


@dataclass
class Environment:
    """Environment-specific configuration (dev, staging, prod)"""
    name: str  # development, staging, production
    database_url: Optional[str] = None
    ci_cd_overrides: Dict[str, Any] = field(default_factory=dict)
    infrastructure_overrides: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Cross-Domain Intelligence
# ============================================================================

@dataclass
class ProjectDependencies:
    """
    Automatically detected dependencies between domains

    Example:
    - Database entities → Create tables before running tests
    - Database actions → Generate integration tests in CI/CD
    - Database + compute → Right-size infrastructure based on schema
    """
    database_to_cicd: List[str] = field(default_factory=list)
    database_to_infra: List[str] = field(default_factory=list)
    cicd_to_infra: List[str] = field(default_factory=list)

    @staticmethod
    def analyze(project: UnifiedProject) -> 'ProjectDependencies':
        """
        Analyze project and detect cross-domain dependencies

        Returns:
            Detected dependencies with recommendations
        """
        deps = ProjectDependencies()

        # Database → CI/CD
        if project.database and project.ci_cd:
            deps.database_to_cicd.append(
                "Add migration tests to CI/CD pipeline"
            )
            deps.database_to_cicd.append(
                f"Test {len(project.database.entities)} entities in integration tests"
            )

        # Database → Infrastructure
        if project.database and project.infrastructure:
            # Estimate database size
            entity_count = len(project.database.entities)
            if entity_count > 20:
                deps.database_to_infra.append(
                    "Consider increasing database instance size (20+ entities)"
                )

        # CI/CD → Infrastructure
        if project.ci_cd and project.infrastructure:
            deps.cicd_to_infra.append(
                "Ensure deployment targets match infrastructure configuration"
            )

        return deps
```

**Unified YAML Format**: `docs/unified/UNIFIED_PROJECT_SPEC.md`

```yaml
# project.specql.yaml - Complete Project Definition

project: saas_project_manager
description: "SaaS platform for agile project management"
version: "2.0.0"
team: platform-engineering

# ============================================================================
# Database Schema (SpecQL)
# ============================================================================
database:
  schema_type: multi_tenant

  entities:
    - entity: Organization
      fields:
        name: text!
        plan: enum(free, pro, enterprise)!
        max_users: integer
        created_at: timestamp

    - entity: User
      fields:
        email: text!
        name: text!
        organization: ref(Organization)
        role: enum(admin, member, viewer)

    - entity: Project
      fields:
        name: text!
        description: text
        organization: ref(Organization)
        owner: ref(User)
        status: enum(planning, active, completed, archived)
        deadline: date

    - entity: Task
      fields:
        title: text!
        description: text
        project: ref(Project)
        assignee: ref(User)
        status: enum(todo, in_progress, review, done)
        priority: enum(low, medium, high, critical)
        due_date: date
        estimated_hours: integer

  actions:
    - name: create_task
      description: "Create new task and notify assignee"
      parameters:
        project_id: uuid
        title: text
        assignee_id: uuid
      steps:
        - validate: project.status IN ('planning', 'active')
        - insert: Task
        - update: Project SET updated_at = now()
        - notify: assignee
          message: "You've been assigned a new task: {task.title}"

    - name: complete_task
      parameters:
        task_id: uuid
      steps:
        - validate: task.status != 'done'
        - update: Task SET status = 'done', completed_at = now()
        - if: all_tasks_complete(task.project_id)
          then:
            - update: Project SET status = 'completed'
            - notify: project.owner

  migrations_path: "db/migrations/"

# ============================================================================
# CI/CD Pipeline
# ============================================================================
ci_cd:
  name: "Project Manager CI/CD"
  platform: github-actions
  language: python
  framework: fastapi

  triggers:
    - type: push
      branches: [main, develop]
    - type: pull_request

  stages:
    - name: test
      jobs:
        - name: lint
          steps:
            - {type: checkout}
            - {type: setup_runtime, with: {python-version: "3.11"}}
            - {type: install_dependencies, command: "uv pip install -e .[dev]"}
            - {type: lint, command: "uv run ruff check ."}
            - {type: run, name: "Type check", command: "uv run mypy src/"}

        - name: database_tests
          services:
            - {name: postgres, version: "15"}
          steps:
            - {type: checkout}
            - {type: setup_runtime}
            - {type: install_dependencies}
            - {type: run, name: "Run migrations", command: "specql migrate --apply"}
            - {type: run_tests, command: "pytest tests/database/"}

        - name: integration_tests
          needs: [database_tests]
          services:
            - {name: postgres, version: "15"}
            - {name: redis, version: "7"}
          steps:
            - {type: checkout}
            - {type: setup_runtime}
            - {type: install_dependencies}
            - {type: run, name: "Seed test data", command: "specql seed test"}
            - {type: run_tests, command: "pytest tests/integration/ --cov"}

    - name: build
      jobs:
        - name: docker_build
          needs: [lint, database_tests, integration_tests]
          steps:
            - {type: checkout}
            - {type: build, command: "docker build -t saas-pm:${{ git.sha }} ."}
            - {type: run, command: "docker push saas-pm:${{ git.sha }}"}

    - name: deploy
      environment: production
      approval_required: true
      jobs:
        - name: deploy_production
          if: github.ref == 'refs/heads/main'
          steps:
            - {type: checkout}
            - {type: run, name: "Run database migrations", command: "specql migrate --production"}
            - {type: deploy, command: "kubectl set image deployment/api api=saas-pm:${{ git.sha }}"}
            - {type: run, name: "Health check", command: "curl -f https://api.example.com/health"}

# ============================================================================
# Infrastructure
# ============================================================================
infrastructure:
  provider: aws
  region: us-east-1
  environment: production

  # Application Servers
  compute:
    instances: 5
    cpu: 2
    memory: 4GB
    auto_scale:
      enabled: true
      min: 3
      max: 20
      cpu_target: 70

  # Container
  container:
    image: saas-pm
    port: 8000
    environment:
      ENV: production
      LOG_LEVEL: INFO
    secrets:
      DATABASE_URL: ${secrets.database_url}
      REDIS_URL: ${secrets.redis_url}
      JWT_SECRET: ${secrets.jwt_secret}
    health_check:
      path: /health
      interval: 30
    resources:
      cpu_limit: 2
      memory_limit: 4GB

  # PostgreSQL Database
  database:
    type: postgresql
    version: "15"
    storage: 500GB
    instance_class: db.r6g.xlarge  # Memory-optimized for large datasets
    multi_az: true
    replicas: 2  # Read replicas

    backups:
      enabled: true
      retention_days: 30
      window: "03:00-04:00"

    performance:
      iops: 10000
      storage_type: io2  # High-performance SSD

  # Redis Cache
  additional_databases:
    - type: redis
      version: "7.0"
      instance_class: cache.r6g.large
      replicas: 2

  # Load Balancer
  load_balancer:
    enabled: true
    type: application
    https: true
    certificate_domain: api.example.com
    health_check:
      path: /health
      interval: 30
    sticky_sessions: true

  # CDN for static assets
  cdn:
    enabled: true
    origin_domain: api.example.com
    cache_ttl: 86400

  # Networking
  network:
    vpc_cidr: 10.0.0.0/16
    custom_domain: api.example.com

  # Observability
  observability:
    logging:
      enabled: true
      retention_days: 90
      level: INFO

    metrics:
      enabled: true
      provider: prometheus

    tracing:
      enabled: true
      provider: jaeger
      sample_rate: 0.2

    alerts:
      - name: high_cpu
        condition: "cpu > 80%"
        duration: 300
        channels: [pagerduty]

      - name: database_connections_exhausted
        condition: "db_connections > 90%"
        duration: 60
        channels: [pagerduty, slack]

      - name: high_error_rate
        condition: "error_rate > 1%"
        duration: 120
        channels: [slack]

  # Security
  security:
    secrets_provider: aws_secrets
    waf: true
    encryption_at_rest: true
    encryption_in_transit: true

  tags:
    Project: saas-project-manager
    Team: platform-engineering
    Environment: production

# ============================================================================
# Environment-Specific Overrides
# ============================================================================
environments:
  - name: development
    infrastructure:
      compute:
        instances: 1
        auto_scale: false
      database:
        storage: 20GB
        multi_az: false
        backups:
          retention_days: 1

  - name: staging
    infrastructure:
      compute:
        instances: 2
      database:
        storage: 100GB
        multi_az: false

  - name: production
    # Uses default infrastructure settings above

# ============================================================================
# Pattern Metadata
# ============================================================================
pattern:
  category: saas_application
  tags: [fastapi, postgresql, redis, aws, multi-tenant, project-management]
  estimated_monthly_cost: 2500  # USD

  best_practices:
    - "Multi-AZ database for high availability"
    - "Read replicas for query scaling"
    - "Auto-scaling based on CPU"
    - "Comprehensive monitoring and alerting"
    - "Automated backups with 30-day retention"
    - "WAF for security"
    - "CDN for static assets"
```

#### 2. Implement Unified Parser (2 hours)

**Parser**: `src/unified/project_parser.py`

```python
"""
Unified Project Parser

Parses complete project.specql.yaml into UnifiedProject.
"""

import yaml
from pathlib import Path
from src.unified.project_schema import UnifiedProject, DatabaseDefinition, Environment
from src.core.specql_parser import SpecQLParser
from src.cicd.parsers.parser_factory import ParserFactory as CICDParserFactory
from src.infrastructure.parsers.parser_factory import ParserFactory as InfraParserFactory


class UnifiedProjectParser:
    """Parse unified project YAML"""

    def __init__(self):
        self.specql_parser = SpecQLParser()

    def parse_file(self, file_path: Path) -> UnifiedProject:
        """Parse project.specql.yaml"""
        content = file_path.read_text()
        return self.parse(content)

    def parse(self, yaml_content: str) -> UnifiedProject:
        """Parse YAML content to UnifiedProject"""
        data = yaml.safe_load(yaml_content)

        return UnifiedProject(
            name=data["project"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            team=data.get("team"),
            database=self._parse_database(data.get("database")),
            ci_cd=self._parse_cicd(data.get("ci_cd")),
            infrastructure=self._parse_infrastructure(data.get("infrastructure")),
            environments=self._parse_environments(data.get("environments", [])),
            tags=data.get("pattern", {}).get("tags", []),
            estimated_monthly_cost=data.get("pattern", {}).get("estimated_monthly_cost")
        )

    def _parse_database(self, db_config: dict) -> DatabaseDefinition:
        """Parse database section"""
        if not db_config:
            return None

        # Parse entities using existing SpecQL parser
        entities = []
        for entity_config in db_config.get("entities", []):
            # Convert dict to YAML string for SpecQL parser
            entity_yaml = yaml.dump(entity_config)
            entity = self.specql_parser.parse(entity_yaml)
            entities.append(entity)

        return DatabaseDefinition(
            schema_type=db_config.get("schema_type", "multi_tenant"),
            entities=entities,
            actions=db_config.get("actions", []),
            migrations_path=db_config.get("migrations_path", "migrations/")
        )

    def _parse_cicd(self, cicd_config: dict) -> UniversalPipeline:
        """Parse CI/CD section"""
        if not cicd_config:
            return None

        # Convert to YAML and use existing CI/CD parser
        cicd_yaml = yaml.dump(cicd_config)
        # Parse using appropriate parser based on platform
        # (Implementation uses existing parsers)
        return None  # TODO: Implement

    def _parse_infrastructure(self, infra_config: dict) -> UniversalInfrastructure:
        """Parse infrastructure section"""
        if not infra_config:
            return None

        # Convert to universal infrastructure object
        # (Implementation uses existing infrastructure schema)
        return None  # TODO: Implement

    def _parse_environments(self, envs_config: list) -> List[Environment]:
        """Parse environment overrides"""
        return [
            Environment(
                name=env["name"],
                infrastructure_overrides=env.get("infrastructure", {})
            )
            for env in envs_config
        ]
```

---

**Afternoon Block (4 hours): Unified Code Generation**

#### 1. Unified Generator Orchestrator (4 hours)

**Orchestrator**: `src/unified/unified_generator.py`

```python
"""
Unified Generator Orchestrator

Coordinates generation across all three domains:
1. Database schema + actions
2. CI/CD pipelines
3. Infrastructure
"""

from pathlib import Path
from typing import List, Dict
from src.unified.project_schema import UnifiedProject, ProjectDependencies
from src.generators.schema.schema_orchestrator import SchemaOrchestrator
from src.cicd.generators.github_actions_generator import GitHubActionsGenerator
from src.infrastructure.generators.terraform_aws_generator import TerraformAWSGenerator


class UnifiedGenerator:
    """Generate all code from unified project definition"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

        # Domain-specific generators
        self.schema_gen = SchemaOrchestrator()
        self.cicd_gen = GitHubActionsGenerator()
        self.infra_gen = TerraformAWSGenerator()

    def generate_all(self, project: UnifiedProject) -> Dict[str, List[Path]]:
        """
        Generate everything from unified project

        Returns:
            Dict of generated files by domain
        """
        generated = {
            "database": [],
            "ci_cd": [],
            "infrastructure": [],
            "documentation": []
        }

        # Analyze dependencies first
        deps = ProjectDependencies.analyze(project)

        print(f"🎯 Generating project: {project.name}")
        print(f"📊 Detected {len(deps.database_to_cicd)} database→CI/CD dependencies")
        print(f"📊 Detected {len(deps.database_to_infra)} database→infra dependencies")

        # 1. Generate database schema
        if project.database:
            print("\n📁 Generating database schema...")
            db_files = self._generate_database(project)
            generated["database"] = db_files
            print(f"   ✅ Generated {len(db_files)} database files")

        # 2. Generate CI/CD pipeline
        if project.ci_cd:
            print("\n⚙️ Generating CI/CD pipeline...")
            cicd_files = self._generate_cicd(project)
            generated["ci_cd"] = cicd_files
            print(f"   ✅ Generated {len(cicd_files)} CI/CD files")

        # 3. Generate infrastructure
        if project.infrastructure:
            print("\n🏗️ Generating infrastructure...")
            infra_files = self._generate_infrastructure(project)
            generated["infrastructure"] = infra_files
            print(f"   ✅ Generated {len(infra_files)} infrastructure files")

        # 4. Generate documentation
        print("\n📚 Generating documentation...")
        doc_files = self._generate_documentation(project, deps)
        generated["documentation"] = doc_files
        print(f"   ✅ Generated {len(doc_files)} documentation files")

        # Summary
        total_files = sum(len(files) for files in generated.values())
        print(f"\n✨ Total: {total_files} files generated")

        return generated

    def _generate_database(self, project: UnifiedProject) -> List[Path]:
        """Generate database schema and migrations"""
        files = []

        # Generate schema for each entity
        for entity in project.database.entities:
            file_specs = self.schema_gen.generate_schema([entity])

            for spec in file_specs:
                file_path = self.output_dir / "database" / f"{spec.name}.sql"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(spec.content)
                files.append(file_path)

        return files

    def _generate_cicd(self, project: UnifiedProject) -> List[Path]:
        """Generate CI/CD pipeline"""
        workflow = self.cicd_gen.generate(project.ci_cd)

        workflow_path = self.output_dir / ".github" / "workflows" / "ci.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(workflow)

        return [workflow_path]

    def _generate_infrastructure(self, project: UnifiedProject) -> List[Path]:
        """Generate infrastructure code"""
        terraform = self.infra_gen.generate(project.infrastructure)

        tf_path = self.output_dir / "terraform" / "main.tf"
        tf_path.parent.mkdir(parents=True, exist_ok=True)
        tf_path.write_text(terraform)

        return [tf_path]

    def _generate_documentation(
        self,
        project: UnifiedProject,
        deps: ProjectDependencies
    ) -> List[Path]:
        """Generate comprehensive documentation"""

        readme = f"""# {project.name}

{project.description}

**Version**: {project.version}
**Team**: {project.team or 'N/A'}
**Estimated Monthly Cost**: ${project.estimated_monthly_cost or 'N/A'}

## 🎯 Project Overview

This project was generated with SpecQL from a single unified specification.

### Components

- **Database**: {len(project.database.entities) if project.database else 0} entities
- **CI/CD**: {len(project.ci_cd.stages) if project.ci_cd else 0} stages
- **Infrastructure**: {project.infrastructure.provider.value if project.infrastructure else 'N/A'}

### Dependencies

{self._format_dependencies(deps)}

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker
- Terraform (if deploying infrastructure)

### Setup

```bash
# Install dependencies
uv pip install -e .

# Run database migrations
specql migrate --apply

# Start development server
uvicorn app.main:app --reload
```

### Deployment

```bash
# Deploy everything
specql deploy project.specql.yaml --environment production

# Or deploy individually
specql deploy-database
specql deploy-infrastructure
```

## 📁 Project Structure

```
.
├── database/           # Generated database schema
├── .github/workflows/  # Generated CI/CD pipelines
├── terraform/          # Generated infrastructure
├── src/               # Application code
└── tests/             # Test suite
```

## 🔧 Configuration

See `project.specql.yaml` for complete configuration.

## 📊 Monitoring

- **Metrics**: Prometheus at metrics.{project.infrastructure.network.custom_domain if project.infrastructure else 'example.com'}
- **Logs**: CloudWatch/Loki
- **Tracing**: Jaeger

## 💰 Cost Estimation

Estimated monthly cost: **${project.estimated_monthly_cost or 'N/A'}**

Breakdown:
- Compute: ~${self._estimate_compute_cost(project)}
- Database: ~${self._estimate_database_cost(project)}
- Networking: ~${self._estimate_networking_cost(project)}
"""

        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)

        return [readme_path]

    def _format_dependencies(self, deps: ProjectDependencies) -> str:
        """Format dependencies for documentation"""
        lines = []

        if deps.database_to_cicd:
            lines.append("**Database → CI/CD**:")
            for dep in deps.database_to_cicd:
                lines.append(f"- {dep}")

        if deps.database_to_infra:
            lines.append("\n**Database → Infrastructure**:")
            for dep in deps.database_to_infra:
                lines.append(f"- {dep}")

        return "\n".join(lines) if lines else "No cross-domain dependencies detected."

    def _estimate_compute_cost(self, project: UnifiedProject) -> int:
        """Rough estimate of compute costs"""
        if not project.infrastructure or not project.infrastructure.compute:
            return 0

        # Rough AWS pricing
        instances = project.infrastructure.compute.instances
        return instances * 100  # ~$100/month per t3.medium

    def _estimate_database_cost(self, project: UnifiedProject) -> int:
        """Rough estimate of database costs"""
        if not project.infrastructure or not project.infrastructure.database:
            return 0

        # Rough RDS pricing
        return 200  # Base cost for db.t3.large

    def _estimate_networking_cost(self, project: UnifiedProject) -> int:
        """Rough estimate of networking costs"""
        if not project.infrastructure or not project.infrastructure.load_balancer:
            return 0

        return 50  # Base cost for ALB
```

---

**Day 1 Summary**:
- ✅ Unified project schema defined
- ✅ Single YAML format for all domains
- ✅ Unified parser implementation
- ✅ Unified generator orchestrator
- ✅ Cross-domain dependency analysis

---

### Day 2: Unified Pattern Library & Semantic Search

**Objective**: Create unified pattern library with semantic search across all domains

**Morning Block (4 hours): Unified Pattern Repository**

#### 1. Unified Pattern Schema (2 hours)

**Repository**: `src/unified/unified_pattern_repository.py`

```python
"""
Unified Pattern Repository

Stores patterns across all three domains with unified semantic search.
"""

from dataclasses import dataclass
from typing import List, Optional
from src.unified.project_schema import UnifiedProject


@dataclass
class UnifiedPattern:
    """Pattern spanning database, CI/CD, and infrastructure"""
    pattern_id: str
    name: str
    description: str
    category: str  # saas_app, microservices, data_platform, ml_platform

    # Complete project definition
    project: UnifiedProject

    # Metadata
    tags: List[str]
    use_cases: List[str]
    company_size: str  # startup, growth, enterprise

    # Quality metrics
    usage_count: int = 0
    success_rate: float = 1.0
    avg_deployment_time_minutes: int = 0

    # Cost
    estimated_monthly_cost: float = 0.0
    cost_breakdown: dict = None

    # Semantic search
    embedding: Optional[List[float]] = None

    # Similar patterns
    similar_patterns: List[str] = None


class UnifiedPatternRepository:
    """Repository for unified patterns with semantic search"""

    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self.patterns: Dict[str, UnifiedPattern] = {}

    def store_pattern(self, pattern: UnifiedPattern) -> None:
        """Store pattern with embedding"""
        # Generate embedding from pattern description + tags
        text = f"{pattern.name} {pattern.description} {' '.join(pattern.tags)}"
        pattern.embedding = self.embedding_service.generate_embedding(text)

        self.patterns[pattern.pattern_id] = pattern

    def search_similar(
        self,
        query: str,
        limit: int = 10,
        filters: dict = None
    ) -> List[UnifiedPattern]:
        """
        Semantic search across all patterns

        Args:
            query: Natural language query
            limit: Number of results
            filters: Optional filters (category, max_cost, etc.)

        Returns:
            List of similar patterns
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)

        # Find similar patterns
        results = []
        for pattern in self.patterns.values():
            if self._matches_filters(pattern, filters):
                similarity = self._cosine_similarity(
                    query_embedding,
                    pattern.embedding
                )
                results.append((pattern, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        return [pattern for pattern, _ in results[:limit]]

    def search_by_cost(
        self,
        max_monthly_cost: float
    ) -> List[UnifiedPattern]:
        """Find patterns within budget"""
        return [
            pattern for pattern in self.patterns.values()
            if pattern.estimated_monthly_cost <= max_monthly_cost
        ]

    def _matches_filters(self, pattern: UnifiedPattern, filters: dict) -> bool:
        """Check if pattern matches filters"""
        if not filters:
            return True

        if "category" in filters and pattern.category != filters["category"]:
            return False

        if "max_cost" in filters and pattern.estimated_monthly_cost > filters["max_cost"]:
            return False

        if "tags" in filters:
            if not any(tag in pattern.tags for tag in filters["tags"]):
                return False

        return True

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

---

#### 2. Populate Pattern Library (2 hours)

**Unified Patterns**: `patterns/unified/`

```yaml
# patterns/unified/saas_starter.yaml

pattern_id: "saas_starter_v1"
name: "SaaS Starter Template"
description: "Complete production-ready SaaS application with multi-tenancy, CI/CD, and AWS infrastructure"
category: saas_application
company_size: startup
estimated_monthly_cost: 800

use_cases:
  - "B2B SaaS application"
  - "Multi-tenant platform"
  - "API-first architecture"

tags: [saas, multi-tenant, fastapi, postgresql, aws, production-ready]

# Complete unified project definition
project:
  name: saas_starter
  description: "Starter template for SaaS applications"

  database:
    schema_type: multi_tenant
    entities:
      - entity: Organization
        fields:
          name: text!
          plan: enum(free, pro, enterprise)!

      - entity: User
        fields:
          email: text!
          name: text!
          organization: ref(Organization)

  ci_cd:
    language: python
    framework: fastapi
    stages:
      - {name: test, jobs: [lint, unit_tests]}
      - {name: deploy, environment: production}

  infrastructure:
    provider: aws
    compute:
      instances: 2
      auto_scale: true
    database:
      type: postgresql
      storage: 50GB

best_practices:
  - "Multi-tenant by default"
  - "Automated CI/CD pipeline"
  - "Auto-scaling infrastructure"
  - "Production-ready monitoring"

cost_breakdown:
  compute: 200
  database: 150
  networking: 100
  monitoring: 50
```

**More Patterns**:

```bash
patterns/unified/
├── saas_starter.yaml
├── microservices_platform.yaml
├── data_analytics_platform.yaml
├── ml_training_platform.yaml
├── ecommerce_platform.yaml
└── api_backend.yaml
```

---

**Afternoon Block (4 hours): LLM-Powered Pattern Recommendations**

#### 1. LLM Pattern Recommender (4 hours)

**Recommender**: `src/unified/llm_recommender.py`

```python
"""
LLM-Powered Pattern Recommender

Uses LLM to analyze project requirements and recommend patterns.
"""

from typing import List, Dict
from src.unified.unified_pattern_repository import UnifiedPattern, UnifiedPatternRepository


class LLMPatternRecommender:
    """Use LLM to recommend patterns based on requirements"""

    def __init__(
        self,
        pattern_repo: UnifiedPatternRepository,
        llm_client
    ):
        self.pattern_repo = pattern_repo
        self.llm_client = llm_client

    def recommend(
        self,
        requirements: str,
        budget: float = None,
        company_size: str = None
    ) -> List[UnifiedPattern]:
        """
        Get pattern recommendations from natural language requirements

        Args:
            requirements: Natural language project description
            budget: Optional monthly budget constraint
            company_size: startup, growth, enterprise

        Returns:
            Ranked list of pattern recommendations with explanations
        """
        # 1. Use semantic search to find candidate patterns
        candidates = self.pattern_repo.search_similar(
            requirements,
            limit=20,
            filters={
                "max_cost": budget,
                "company_size": company_size
            } if budget or company_size else None
        )

        # 2. Use LLM to rank and explain recommendations
        prompt = self._build_recommendation_prompt(requirements, candidates)
        response = self.llm_client.complete(prompt)

        # 3. Parse LLM response and return top patterns
        return self._parse_recommendations(response, candidates)

    def _build_recommendation_prompt(
        self,
        requirements: str,
        candidates: List[UnifiedPattern]
    ) -> str:
        """Build prompt for LLM ranking"""
        return f"""You are an expert software architect. Analyze these requirements and recommend the best patterns.

Requirements:
{requirements}

Available Patterns:
{self._format_candidates(candidates)}

For each pattern, provide:
1. Match score (0-10)
2. Reasoning
3. Potential modifications needed

Rank patterns by best fit."""

    def _format_candidates(self, candidates: List[UnifiedPattern]) -> str:
        """Format candidates for LLM prompt"""
        lines = []
        for i, pattern in enumerate(candidates, 1):
            lines.append(f"{i}. {pattern.name}")
            lines.append(f"   Description: {pattern.description}")
            lines.append(f"   Tags: {', '.join(pattern.tags)}")
            lines.append(f"   Cost: ${pattern.estimated_monthly_cost}/month")
            lines.append("")

        return "\n".join(lines)

    def _parse_recommendations(
        self,
        llm_response: str,
        candidates: List[UnifiedPattern]
    ) -> List[Dict]:
        """Parse LLM recommendations"""
        # Simple parsing (production would be more robust)
        recommendations = []
        # ... parse LLM response ...
        return recommendations
```

---

**Day 2 Summary**:
- ✅ Unified pattern repository with semantic search
- ✅ Pattern library with 10+ complete project templates
- ✅ LLM-powered pattern recommendations
- ✅ Cross-domain pattern matching

---

### Days 3-5: CLI Integration & Advanced Features

**Day 3**: Unified CLI Commands

```bash
# Single command deployment
specql deploy project.specql.yaml

# Interactive project creation
specql init --interactive

# Pattern search
specql search "saas application with postgresql"

# Cost estimation
specql estimate project.specql.yaml

# Compare patterns
specql compare pattern1 pattern2
```

**Day 4**: Advanced Cross-Domain Features

- Automatic dependency resolution
- Smart defaults based on project type
- Cost optimization suggestions
- Security best practices validation

**Day 5**: Documentation & Polish

- Complete user guide
- Video tutorials
- Migration guides
- API documentation

---

## Week 22: Production Readiness & Community Launch

### Day 1-2: Production Testing

- Load testing with large projects
- Multi-platform validation
- Error handling improvements
- Recovery mechanisms

### Day 3-4: Documentation & Examples

- Complete documentation site
- 20+ example projects
- Video walkthroughs
- Best practices guide

### Day 5: Community Launch

- Blog post
- GitHub release
- Social media announcement
- Community support setup

---

## Success Metrics

### Technical Metrics

- [ ] Single YAML defines database + CI/CD + infrastructure
- [ ] Pattern library with 50+ unified patterns
- [ ] Semantic search accuracy > 80%
- [ ] LLM recommendations relevant > 90%
- [ ] Cost estimation accurate within 15%
- [ ] Generation time < 5 seconds for medium projects
- [ ] Test coverage > 90%

### Business Metrics

- [ ] 100+ GitHub stars in first week
- [ ] 10+ community contributions
- [ ] 5+ production deployments
- [ ] Positive feedback from beta users
- [ ] Documentation complete and reviewed

### User Experience

- [ ] One command deployment works reliably
- [ ] Interactive mode user-friendly
- [ ] Error messages clear and actionable
- [ ] Documentation comprehensive
- [ ] Examples cover common use cases

---

## Conclusion

**Weeks 21-22** complete the vision of **universal expressivity** across all technical domains:

1. ✅ **Database** (Weeks 1-14): Schema, actions, Trinity pattern
2. ✅ **CI/CD** (Weeks 15-17): Universal pipelines, multi-platform
3. ✅ **Infrastructure** (Weeks 18-20): Cloud resources, multi-provider
4. ✅ **Unified** (Weeks 21-22): Single source of truth for everything

### The Result

**Before SpecQL**:
- 5,000+ lines PostgreSQL (manual)
- 500+ lines GitHub Actions (manual)
- 2,000+ lines Terraform (manual)
- 1,000+ lines documentation (manual)
- **Total: 8,500+ lines of manual technical work**

**With SpecQL**:
- 150 lines `project.specql.yaml` (business intent only)
- **1 command**: `specql deploy project.specql.yaml`
- **Result**: Complete production deployment

### Business Impact

**100x Developer Leverage**: Write 1% of the code, get 100% of the functionality

This is the culmination of the universal expression language vision:
- **One language** for all technical implementation
- **One pattern library** across all domains
- **One semantic search** that understands everything
- **One command** to deploy everything

---

**Status**: 🔴 Ready to Execute
**Priority**: Critical (completes universal expressivity vision)
**Expected Output**: Production-ready unified platform with complete documentation

**Next Steps**: Begin Week 12 (Trinity Pattern 100% Equivalence) to complete database foundation, then proceed to CI/CD and Infrastructure extensions.
