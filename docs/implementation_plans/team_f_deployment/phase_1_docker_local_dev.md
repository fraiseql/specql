# Team F Phase 1: Docker & Local Dev Implementation Plan

**Created**: 2025-11-12
**Phase**: 1 of 5
**Status**: Planning
**Complexity**: Medium - Foundation for deployment generation
**Priority**: HIGH - Enables local development for all users

---

## Executive Summary

Implement Team F's foundational Docker generation capabilities, enabling SpecQL to auto-generate production-ready Docker configurations from minimal YAML. This phase focuses on **local development and simple deployment scenarios**.

**Goal**: From `deployment.yaml` (15 lines) → Generate Docker stack (500+ lines)

**Key Deliverables**:
1. Framework-aware Docker generation (FraiseQL, Django, Rails)
2. docker-compose.yml for local dev + production
3. Multi-stage Dockerfiles with best practices
4. Caddy reverse proxy configuration
5. Environment management (.env templates)
6. Health checks and monitoring hooks

**Impact**:
- Users can deploy locally with one command
- Production-ready Docker setups without DevOps expertise
- Framework-specific optimizations (Rust builds for FraiseQL, etc.)

---

## 🎯 Phase 1 Objectives

### Core Goals
1. **Docker Generation System**: Create generator architecture for Team F
2. **Framework-Aware Templates**: FraiseQL, Django, Rails-specific Docker configs
3. **Local Development**: docker-compose.yml optimized for dev workflow
4. **Production-Ready**: Multi-stage builds, security hardening, health checks
5. **Pattern Library**: Reusable Docker patterns (hobby-project, small-saas)

### Success Criteria
- ✅ Generate complete Docker stack from `deployment.yaml`
- ✅ Support FraiseQL (Python 3.13 + Rust), Django (Python 3.12), Rails (Ruby 3.2)
- ✅ Local dev works with hot reload
- ✅ Production builds are optimized and secure
- ✅ All generated configs pass best practice checks (hadolint, docker-compose validate)

---

## 📋 Technical Design

### Architecture: Team F Structure

```
src/generators/deployment/
├── __init__.py
├── deployment_orchestrator.py     # Main orchestrator (like SchemaOrchestrator)
├── docker/
│   ├── __init__.py
│   ├── dockerfile_generator.py    # Multi-stage Dockerfile generation
│   ├── compose_generator.py       # docker-compose.yml generation
│   └── caddy_generator.py         # Caddyfile generation
├── patterns/
│   ├── __init__.py
│   ├── pattern_models.py          # Pattern definitions (hobby, small-saas, etc.)
│   └── pattern_loader.py          # Load pattern configurations
├── framework/
│   ├── __init__.py
│   ├── fraiseql_docker.py         # FraiseQL-specific Docker logic
│   ├── django_docker.py           # Django-specific Docker logic
│   └── rails_docker.py            # Rails-specific Docker logic
└── templates/
    ├── dockerfiles/
    │   ├── fraiseql.dockerfile.j2
    │   ├── django.dockerfile.j2
    │   └── rails.dockerfile.j2
    ├── compose/
    │   ├── base.compose.yaml.j2
    │   ├── fraiseql.compose.yaml.j2
    │   └── django.compose.yaml.j2
    └── caddy/
        └── Caddyfile.j2
```

### CLI Integration

```python
# src/cli/deploy.py (NEW)
import click
from src.generators.deployment.deployment_orchestrator import DeploymentOrchestrator

@click.group()
def deploy():
    """Generate deployment configurations"""
    pass

@deploy.command()
@click.argument('deployment_file', type=click.Path(exists=True))
@click.option('--framework', default='fraiseql', help='Target framework')
@click.option('--pattern', default='small-saas', help='Deployment pattern')
@click.option('--output-dir', default='generated/deployment', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Show what would be generated')
def generate(deployment_file, framework, pattern, output_dir, dry_run):
    """Generate Docker deployment configuration"""
    orchestrator = DeploymentOrchestrator(
        deployment_file=deployment_file,
        framework=framework,
        pattern=pattern,
        output_dir=output_dir
    )

    if dry_run:
        orchestrator.preview()
    else:
        orchestrator.generate()
        click.echo(f"✅ Generated deployment files in {output_dir}")
```

### Deployment YAML Schema

```yaml
# deployment.yaml
deployment:
  name: my-app
  framework: fraiseql  # fraiseql | django | rails
  pattern: hobby-project  # hobby-project | small-saas | production-saas

# Optional overrides
platform:
  domain: myapp.local  # Local development domain

database:
  engine: postgresql
  version: "16"

environment:
  dev:
    LOG_LEVEL: debug
    ENABLE_RELOAD: true
  production:
    LOG_LEVEL: info
    ENABLE_RELOAD: false
```

---

## 🏗️ Implementation Details

### 1. Deployment Orchestrator

```python
# src/generators/deployment/deployment_orchestrator.py
from pathlib import Path
from typing import Dict, Any
import yaml
from jinja2 import Environment, FileSystemLoader

from .patterns.pattern_loader import PatternLoader
from .docker.dockerfile_generator import DockerfileGenerator
from .docker.compose_generator import ComposeGenerator
from .docker.caddy_generator import CaddyGenerator

class DeploymentOrchestrator:
    """
    Orchestrates deployment configuration generation.
    Similar role to SchemaOrchestrator for database generation.
    """

    def __init__(
        self,
        deployment_file: str,
        framework: str,
        pattern: str,
        output_dir: str
    ):
        self.deployment_file = deployment_file
        self.framework = framework
        self.pattern = pattern
        self.output_dir = Path(output_dir)

        # Load deployment config
        with open(deployment_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load pattern defaults
        self.pattern_config = PatternLoader.load(pattern, framework)

        # Initialize generators
        self.dockerfile_gen = DockerfileGenerator(framework, self.pattern_config)
        self.compose_gen = ComposeGenerator(framework, self.pattern_config)
        self.caddy_gen = CaddyGenerator(self.pattern_config)

    def generate(self) -> Dict[str, Path]:
        """Generate all deployment files"""
        generated_files = {}

        # Create output directories
        (self.output_dir / 'docker').mkdir(parents=True, exist_ok=True)

        # Generate Dockerfile
        dockerfile_path = self.output_dir / 'Dockerfile'
        dockerfile_content = self.dockerfile_gen.generate(self.config)
        dockerfile_path.write_text(dockerfile_content)
        generated_files['dockerfile'] = dockerfile_path

        # Generate docker-compose.yml
        compose_path = self.output_dir / 'docker-compose.yml'
        compose_content = self.compose_gen.generate(self.config)
        compose_path.write_text(compose_content)
        generated_files['compose'] = compose_path

        # Generate docker-compose.dev.yml (development overrides)
        compose_dev_path = self.output_dir / 'docker-compose.dev.yml'
        compose_dev_content = self.compose_gen.generate_dev(self.config)
        compose_dev_path.write_text(compose_dev_content)
        generated_files['compose_dev'] = compose_dev_path

        # Generate Caddyfile
        caddy_path = self.output_dir / 'Caddyfile'
        caddy_content = self.caddy_gen.generate(self.config)
        caddy_path.write_text(caddy_content)
        generated_files['caddy'] = caddy_path

        # Generate .env.example
        env_path = self.output_dir / '.env.example'
        env_content = self._generate_env_template()
        env_path.write_text(env_content)
        generated_files['env'] = env_path

        # Generate .dockerignore
        dockerignore_path = self.output_dir / '.dockerignore'
        dockerignore_content = self._generate_dockerignore()
        dockerignore_path.write_text(dockerignore_content)
        generated_files['dockerignore'] = dockerignore_path

        # Generate README
        readme_path = self.output_dir / 'DEPLOYMENT_README.md'
        readme_content = self._generate_readme(generated_files)
        readme_path.write_text(readme_content)
        generated_files['readme'] = readme_path

        return generated_files

    def preview(self):
        """Preview what would be generated"""
        print("📦 Deployment Generation Preview")
        print(f"Framework: {self.framework}")
        print(f"Pattern: {self.pattern}")
        print(f"Output: {self.output_dir}")
        print("\nFiles to be generated:")
        print("  - Dockerfile (multi-stage build)")
        print("  - docker-compose.yml (production)")
        print("  - docker-compose.dev.yml (development)")
        print("  - Caddyfile (reverse proxy)")
        print("  - .env.example (environment variables)")
        print("  - .dockerignore")
        print("  - DEPLOYMENT_README.md")

    def _generate_env_template(self) -> str:
        """Generate .env.example with framework-specific variables"""
        template = f"""# {self.config['deployment']['name']} Environment Variables
# Copy to .env and fill in values

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/dbname
POSTGRES_USER=user
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB={self.config['deployment']['name']}

# Application
PYTHON_ENV=development
PORT=8000
LOG_LEVEL=debug

# Domain (for Caddy SSL)
DOMAIN=localhost

# Secret Keys (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')
SECRET_KEY=generate_me
JWT_SECRET=generate_me
"""

        if self.framework == 'fraiseql':
            template += """
# FraiseQL-specific
ENABLE_PLAYGROUND=true
ENABLE_INTROSPECTION=true
GRAPHQL_DEPTH_LIMIT=10
"""

        return template

    def _generate_dockerignore(self) -> str:
        """Generate .dockerignore"""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
dist/
*.egg-info/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# Docs
docs/
*.md

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""

    def _generate_readme(self, generated_files: Dict[str, Path]) -> str:
        """Generate deployment README"""
        return f"""# Deployment Guide: {self.config['deployment']['name']}

**Framework**: {self.framework}
**Pattern**: {self.pattern}
**Generated**: Auto-generated by SpecQL Team F

---

## Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
vim .env
```

### 2. Local Development
```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Application will be available at:
# - API: http://localhost:8000
# - GraphQL Playground: http://localhost:8000/playground
```

### 3. Production Deployment
```bash
# Build production images
docker compose build

# Start production stack
docker compose up -d

# View logs
docker compose logs -f
```

---

## Generated Files

{self._format_file_list(generated_files)}

---

## Architecture

**Services:**
- **postgres**: PostgreSQL 16 database
- **{self.framework}-server**: Application server
- **caddy**: Reverse proxy with auto-SSL

**Volumes:**
- `postgres_data`: Database persistence
- `caddy_data`: SSL certificates

---

## Health Checks

All services include health checks:
```bash
# Check service health
docker compose ps

# View health status
docker inspect <container_name> | jq '.[0].State.Health'
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Verify connection
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Application Errors
```bash
# View application logs
docker compose logs {self.framework}-server

# Enter container for debugging
docker compose exec {self.framework}-server bash
```

---

## Next Steps

1. Review generated configuration files
2. Customize .env for your environment
3. Add application code to ./app directory
4. Run database migrations
5. Deploy to production

For more information, see: https://github.com/fraiseql/specql
"""

    def _format_file_list(self, files: Dict[str, Path]) -> str:
        """Format file list for README"""
        lines = []
        for name, path in files.items():
            lines.append(f"- `{path.name}`: {self._describe_file(name)}")
        return "\n".join(lines)

    def _describe_file(self, file_type: str) -> str:
        """Describe what each file does"""
        descriptions = {
            'dockerfile': 'Multi-stage Docker build configuration',
            'compose': 'Production docker-compose configuration',
            'compose_dev': 'Development overrides (hot reload, debug)',
            'caddy': 'Reverse proxy with auto-SSL',
            'env': 'Environment variable template',
            'dockerignore': 'Files to exclude from Docker build',
            'readme': 'This file'
        }
        return descriptions.get(file_type, 'Configuration file')
```

### 2. Dockerfile Generator (FraiseQL)

```python
# src/generators/deployment/docker/dockerfile_generator.py
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

class DockerfileGenerator:
    """Generate framework-specific Dockerfiles"""

    def __init__(self, framework: str, pattern_config: Dict[str, Any]):
        self.framework = framework
        self.pattern_config = pattern_config
        self.template_env = Environment(
            loader=FileSystemLoader('src/generators/deployment/templates/dockerfiles')
        )

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate Dockerfile for framework"""
        template = self.template_env.get_template(f'{self.framework}.dockerfile.j2')

        context = {
            'app_name': config['deployment']['name'],
            'python_version': self.pattern_config['deployment']['version'],
            'framework': self.framework,
            'needs_rust': self.framework == 'fraiseql',
            'base_image': self.pattern_config['deployment']['docker_base'],
            'framework_package': self.pattern_config['deployment']['framework_package'],
        }

        return template.render(**context)
```

**Template: fraiseql.dockerfile.j2**

```jinja2
# ============================================
# AUTO-GENERATED BY SPECQL TEAM F
# Framework: FraiseQL (Python + Rust)
# Pattern: {{ pattern }}
# Generated: {{ timestamp }}
# ============================================

# ====================================
# Stage 1: Builder (Rust + Python)
# ====================================
FROM {{ base_image }} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for FraiseQL's maturin build)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && rustup default stable

ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /build

# Install uv for faster Python dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./
{% if needs_rust %}
COPY Cargo.toml Cargo.lock ./
COPY fraiseql_rs/ ./fraiseql_rs/
{% endif %}

# Install dependencies (including FraiseQL with Rust extensions)
RUN uv pip install --system --no-cache-dir {{ framework_package }}

# Copy application code
COPY ./app ./app
COPY ./migrations ./migrations

# ====================================
# Stage 2: Production Runtime
# ====================================
FROM {{ base_image }} AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/migrations && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python packages from builder (includes compiled Rust .so files)
COPY --from=builder /usr/local/lib/python{{ python_version }}/site-packages /usr/local/lib/python{{ python_version }}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder --chown=appuser:appuser /build/app ./app
COPY --from=builder --chown=appuser:appuser /build/migrations ./migrations

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHON_ENV=production \
    PATH="/home/appuser/.local/bin:$PATH"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose application port
EXPOSE 8000

# Run FraiseQL server
CMD ["fraiseql", "run", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Compose Generator

```python
# src/generators/deployment/docker/compose_generator.py
from typing import Dict, Any
import yaml

class ComposeGenerator:
    """Generate docker-compose.yml files"""

    def __init__(self, framework: str, pattern_config: Dict[str, Any]):
        self.framework = framework
        self.pattern_config = pattern_config

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate production docker-compose.yml"""
        compose_config = {
            'version': '3.9',
            'services': self._generate_services(config),
            'volumes': self._generate_volumes(),
            'networks': self._generate_networks()
        }

        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False)

    def generate_dev(self, config: Dict[str, Any]) -> str:
        """Generate development overrides"""
        dev_overrides = {
            'version': '3.9',
            'services': {
                f"{self.framework}-server": {
                    'command': self._get_dev_command(),
                    'volumes': [
                        './app:/app/app:ro',  # Hot reload
                    ],
                    'environment': {
                        'PYTHON_ENV': 'development',
                        'LOG_LEVEL': 'debug',
                        'ENABLE_RELOAD': 'true',
                        'ENABLE_PLAYGROUND': 'true',
                    }
                }
            }
        }

        return yaml.dump(dev_overrides, default_flow_style=False)

    def _generate_services(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate service definitions"""
        services = {}

        # PostgreSQL service
        services['postgres'] = {
            'image': 'postgres:16-alpine',
            'environment': {
                'POSTGRES_USER': '${POSTGRES_USER:-postgres}',
                'POSTGRES_PASSWORD': '${POSTGRES_PASSWORD}',
                'POSTGRES_DB': '${POSTGRES_DB}',
            },
            'volumes': [
                'postgres_data:/var/lib/postgresql/data',
                './migrations:/docker-entrypoint-initdb.d:ro'
            ],
            'healthcheck': {
                'test': ['CMD-SHELL', 'pg_isready -U ${POSTGRES_USER}'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            },
            'restart': 'unless-stopped'
        }

        # Application server
        services[f'{self.framework}-server'] = {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile',
                'target': 'production'
            },
            'depends_on': {
                'postgres': {'condition': 'service_healthy'}
            },
            'environment': {
                'DATABASE_URL': 'postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}',
                'PORT': '8000',
                'PYTHON_ENV': 'production',
                'SECRET_KEY': '${SECRET_KEY}',
            },
            'ports': ['8000:8000'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
                'interval': '30s',
                'timeout': '5s',
                'retries': 3,
                'start_period': '10s'
            },
            'restart': 'unless-stopped'
        }

        # Caddy reverse proxy
        services['caddy'] = {
            'image': 'caddy:2-alpine',
            'depends_on': [f'{self.framework}-server'],
            'ports': [
                '80:80',
                '443:443',
                '443:443/udp'  # HTTP/3
            ],
            'volumes': [
                './Caddyfile:/etc/caddy/Caddyfile:ro',
                'caddy_data:/data',
                'caddy_config:/config'
            ],
            'environment': {
                'DOMAIN': '${DOMAIN:-localhost}'
            },
            'restart': 'unless-stopped'
        }

        return services

    def _generate_volumes(self) -> Dict[str, Any]:
        """Generate volume definitions"""
        return {
            'postgres_data': None,
            'caddy_data': None,
            'caddy_config': None
        }

    def _generate_networks(self) -> Dict[str, Any]:
        """Generate network definitions"""
        return {
            'default': {
                'driver': 'bridge'
            }
        }

    def _get_dev_command(self) -> list:
        """Get development command with hot reload"""
        if self.framework == 'fraiseql':
            return ['fraiseql', 'run', '--host', '0.0.0.0', '--port', '8000', '--reload']
        elif self.framework == 'django':
            return ['python', 'manage.py', 'runserver', '0.0.0.0:8000']
        else:
            return ['rails', 'server', '-b', '0.0.0.0']
```

### 4. Caddy Generator

```python
# src/generators/deployment/docker/caddy_generator.py
from typing import Dict, Any

class CaddyGenerator:
    """Generate Caddyfile configuration"""

    def __init__(self, pattern_config: Dict[str, Any]):
        self.pattern_config = pattern_config

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate Caddyfile"""
        domain = config.get('platform', {}).get('domain', 'localhost')
        framework = config['deployment']['framework']

        return f"""# Auto-generated Caddyfile for {config['deployment']['name']}
# Framework: {framework}

{{$DOMAIN:{domain}}} {{
    # Reverse proxy to application server
    reverse_proxy {framework}-server:8000

    # Enable compression
    encode gzip zstd

    # Security headers
    header {{
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"

        # CORS for GraphQL (adjust for your needs)
        Access-Control-Allow-Origin "*"
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type, Authorization"
        Access-Control-Max-Age "86400"
    }}

    # Handle OPTIONS preflight
    @options {{
        method OPTIONS
    }}
    respond @options 204

    # Health check endpoint
    handle /health {{
        reverse_proxy {framework}-server:8000
    }}

    # GraphQL endpoint
    handle /graphql {{
        reverse_proxy {framework}-server:8000
    }}

    # GraphQL playground (disable in production)
    handle /playground {{
        reverse_proxy {framework}-server:8000
    }}

    # Metrics endpoint (restrict access in production)
    handle /metrics {{
        reverse_proxy {framework}-server:8000
    }}

    # Request logging
    log {{
        output stdout
        format json
        level INFO
    }}
}}
"""
```

---

## 📊 Testing Strategy

### Unit Tests

```python
# tests/unit/generators/deployment/test_deployment_orchestrator.py
import pytest
from pathlib import Path
from src.generators.deployment.deployment_orchestrator import DeploymentOrchestrator

def test_orchestrator_initialization(tmp_path):
    """Test orchestrator initializes correctly"""
    deployment_file = tmp_path / "deployment.yaml"
    deployment_file.write_text("""
deployment:
  name: test-app
  framework: fraiseql
  pattern: hobby-project
""")

    orchestrator = DeploymentOrchestrator(
        deployment_file=str(deployment_file),
        framework='fraiseql',
        pattern='hobby-project',
        output_dir=str(tmp_path / 'output')
    )

    assert orchestrator.framework == 'fraiseql'
    assert orchestrator.pattern == 'hobby-project'

def test_generate_creates_all_files(tmp_path):
    """Test that all expected files are generated"""
    deployment_file = tmp_path / "deployment.yaml"
    deployment_file.write_text("""
deployment:
  name: test-app
  framework: fraiseql
  pattern: hobby-project
""")

    output_dir = tmp_path / 'output'
    orchestrator = DeploymentOrchestrator(
        deployment_file=str(deployment_file),
        framework='fraiseql',
        pattern='hobby-project',
        output_dir=str(output_dir)
    )

    generated = orchestrator.generate()

    # Verify all files were generated
    assert 'dockerfile' in generated
    assert 'compose' in generated
    assert 'compose_dev' in generated
    assert 'caddy' in generated
    assert 'env' in generated

    # Verify files exist
    assert (output_dir / 'Dockerfile').exists()
    assert (output_dir / 'docker-compose.yml').exists()
    assert (output_dir / 'docker-compose.dev.yml').exists()

# tests/unit/generators/deployment/test_dockerfile_generator.py
def test_fraiseql_dockerfile_includes_rust():
    """FraiseQL Dockerfile should include Rust build stage"""
    generator = DockerfileGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    dockerfile = generator.generate({'deployment': {'name': 'test-app'}})

    assert 'rustup' in dockerfile
    assert 'maturin' in dockerfile or 'fraiseql' in dockerfile
    assert 'python:3.13' in dockerfile

def test_dockerfile_includes_health_check():
    """Dockerfile should include health check"""
    generator = DockerfileGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    dockerfile = generator.generate({'deployment': {'name': 'test-app'}})

    assert 'HEALTHCHECK' in dockerfile
    assert '/health' in dockerfile

def test_dockerfile_uses_non_root_user():
    """Dockerfile should use non-root user for security"""
    generator = DockerfileGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    dockerfile = generator.generate({'deployment': {'name': 'test-app'}})

    assert 'useradd' in dockerfile
    assert 'USER' in dockerfile
    assert 'root' not in dockerfile.split('USER')[1]  # After USER directive

# tests/unit/generators/deployment/test_compose_generator.py
def test_compose_has_all_services():
    """Compose should include postgres, app, and caddy"""
    generator = ComposeGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    compose = generator.generate({'deployment': {'name': 'test-app'}})

    assert 'postgres:' in compose
    assert 'fraiseql-server:' in compose
    assert 'caddy:' in compose

def test_compose_has_health_checks():
    """All services should have health checks"""
    generator = ComposeGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    compose_yaml = yaml.safe_load(
        generator.generate({'deployment': {'name': 'test-app'}})
    )

    assert 'healthcheck' in compose_yaml['services']['postgres']
    assert 'healthcheck' in compose_yaml['services']['fraiseql-server']

def test_dev_compose_enables_reload():
    """Dev compose should enable hot reload"""
    generator = ComposeGenerator('fraiseql', FRAISEQL_PATTERN_CONFIG)
    dev_yaml = yaml.safe_load(
        generator.generate_dev({'deployment': {'name': 'test-app'}})
    )

    service = dev_yaml['services']['fraiseql-server']
    assert '--reload' in ' '.join(service['command'])
    assert service['environment']['ENABLE_RELOAD'] == 'true'
```

### Integration Tests

```python
# tests/integration/deployment/test_docker_generation_e2e.py
def test_fraiseql_docker_stack_builds(tmp_path):
    """Test that generated Docker stack actually builds"""
    deployment_file = tmp_path / "deployment.yaml"
    deployment_file.write_text("""
deployment:
  name: test-app
  framework: fraiseql
  pattern: hobby-project
""")

    # Generate files
    orchestrator = DeploymentOrchestrator(
        deployment_file=str(deployment_file),
        framework='fraiseql',
        pattern='hobby-project',
        output_dir=str(tmp_path)
    )
    orchestrator.generate()

    # Create minimal app structure
    app_dir = tmp_path / 'app'
    app_dir.mkdir()
    (app_dir / 'main.py').write_text("""
from fraiseql.fastapi import create_fraiseql_app

app = create_fraiseql_app(
    database_url="postgresql://localhost/test",
    types=[],
    queries=[]
)

@app.get("/health")
async def health():
    return {"status": "healthy"}
""")

    # Try to build Docker image
    result = subprocess.run(
        ['docker', 'build', '-t', 'test-fraiseql', str(tmp_path)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Build failed: {result.stderr}"

def test_docker_compose_validates(tmp_path):
    """Test that generated docker-compose.yml is valid"""
    deployment_file = tmp_path / "deployment.yaml"
    deployment_file.write_text("""
deployment:
  name: test-app
  framework: fraiseql
  pattern: hobby-project
""")

    orchestrator = DeploymentOrchestrator(
        deployment_file=str(deployment_file),
        framework='fraiseql',
        pattern='hobby-project',
        output_dir=str(tmp_path)
    )
    orchestrator.generate()

    # Validate compose file
    result = subprocess.run(
        ['docker', 'compose', '-f', str(tmp_path / 'docker-compose.yml'), 'config'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )

    assert result.returncode == 0, f"Invalid compose file: {result.stderr}"
```

---

## 📝 Deliverables

### Code Files
1. ✅ `src/generators/deployment/deployment_orchestrator.py`
2. ✅ `src/generators/deployment/docker/dockerfile_generator.py`
3. ✅ `src/generators/deployment/docker/compose_generator.py`
4. ✅ `src/generators/deployment/docker/caddy_generator.py`
5. ✅ `src/generators/deployment/patterns/pattern_loader.py`
6. ✅ `src/generators/deployment/framework/fraiseql_docker.py`
7. ✅ `src/cli/deploy.py`

### Templates
8. ✅ `src/generators/deployment/templates/dockerfiles/fraiseql.dockerfile.j2`
9. ✅ `src/generators/deployment/templates/compose/base.compose.yaml.j2`
10. ✅ `src/generators/deployment/templates/caddy/Caddyfile.j2`

### Tests
11. ✅ `tests/unit/generators/deployment/test_deployment_orchestrator.py`
12. ✅ `tests/unit/generators/deployment/test_dockerfile_generator.py`
13. ✅ `tests/unit/generators/deployment/test_compose_generator.py`
14. ✅ `tests/integration/deployment/test_docker_generation_e2e.py`

### Documentation
15. ✅ `docs/guides/DEPLOYMENT_DOCKER.md` - Docker deployment guide
16. ✅ `docs/reference/TEAM_F_OVERVIEW.md` - Team F architecture
17. ✅ Auto-generated `DEPLOYMENT_README.md` (per project)

---

## 🚀 Implementation Phases

### Week 1: Foundation (Days 1-3)
**Goal**: Basic orchestrator + Dockerfile generation

**TDD Cycle 1: Orchestrator Init**
- 🔴 RED: Write test for orchestrator initialization
- 🟢 GREEN: Implement basic orchestrator class
- 🔧 REFACTOR: Add pattern loading
- ✅ QA: All tests pass

**TDD Cycle 2: Dockerfile Generation**
- 🔴 RED: Write test for FraiseQL Dockerfile generation
- 🟢 GREEN: Implement DockerfileGenerator with template
- 🔧 REFACTOR: Extract framework-specific logic
- ✅ QA: Dockerfile builds successfully

**TDD Cycle 3: Multi-stage Build**
- 🔴 RED: Write test for Rust build stage
- 🟢 GREEN: Add Rust toolchain to Dockerfile
- 🔧 REFACTOR: Optimize layer caching
- ✅ QA: Build time < 5 minutes

### Week 2: Compose + Caddy (Days 4-6)
**Goal**: docker-compose.yml + Caddyfile generation

**TDD Cycle 4: Compose Generation**
- 🔴 RED: Write test for compose service definitions
- 🟢 GREEN: Implement ComposeGenerator
- 🔧 REFACTOR: Add health checks and dependencies
- ✅ QA: docker-compose config validates

**TDD Cycle 5: Development Overrides**
- 🔴 RED: Write test for dev compose overrides
- 🟢 GREEN: Implement generate_dev()
- 🔧 REFACTOR: Add hot reload configuration
- ✅ QA: Dev mode works with code changes

**TDD Cycle 6: Caddy Configuration**
- 🔴 RED: Write test for Caddyfile generation
- 🟢 GREEN: Implement CaddyGenerator
- 🔧 REFACTOR: Add security headers and CORS
- ✅ QA: Caddy validates and serves traffic

### Week 3: Integration + Testing (Days 7-10)
**Goal**: End-to-end tests + CLI integration

**TDD Cycle 7: Full Stack Generation**
- 🔴 RED: Write E2E test for complete stack generation
- 🟢 GREEN: Wire all generators in orchestrator
- 🔧 REFACTOR: Add environment templates
- ✅ QA: Generated stack builds and runs

**TDD Cycle 8: CLI Integration**
- 🔴 RED: Write test for CLI commands
- 🟢 GREEN: Implement `specql deploy generate`
- 🔧 REFACTOR: Add rich progress output
- ✅ QA: CLI works end-to-end

**TDD Cycle 9: Docker Build Test**
- 🔴 RED: Write integration test that actually builds Docker
- 🟢 GREEN: Fix any build issues discovered
- 🔧 REFACTOR: Optimize Dockerfile for speed
- ✅ QA: Full build + test in CI/CD

### Week 4: Documentation + Polish (Days 11-12)
**Goal**: Documentation and user experience

- Write deployment guide
- Create example projects
- Add CLI help text
- Generate sample outputs
- Final QA and testing

---

## ✅ Success Metrics

### Quantitative
- ✅ Generate complete Docker stack from 15-line YAML
- ✅ Dockerfile builds successfully in < 5 minutes
- ✅ docker-compose validates with no errors
- ✅ All services pass health checks
- ✅ 100% test coverage for generators
- ✅ Local dev works with hot reload
- ✅ Production build is < 200MB (FraiseQL)

### Qualitative
- ✅ New users can deploy locally with one command
- ✅ Generated configs pass security best practices (hadolint, docker-bench)
- ✅ Documentation is clear and complete
- ✅ Framework-specific optimizations are applied (Rust for FraiseQL)
- ✅ Developer experience is smooth (good error messages, helpful README)

---

## 🔗 Dependencies

### Internal
- ✅ SpecQL parser (Team A) - For entity definitions
- ✅ Schema registry (Team B) - For database configuration
- ✅ Framework defaults system (Issue #9) - For framework-aware generation

### External
- **jinja2** - Template engine
- **pyyaml** - YAML parsing
- **docker** (runtime) - For building images
- **hadolint** (optional) - Dockerfile linting

### New Dependencies
```toml
# Add to pyproject.toml
dependencies = [
    # ... existing ...
    "jinja2>=3.1.0",
]

[project.optional-dependencies]
deployment = [
    "docker>=7.0.0",  # For Docker API (build testing)
]
```

---

## 🚧 Next Steps (After Phase 1)

### Phase 2: OpenTofu Modules
- Generate AWS infrastructure (RDS, ECS, ALB)
- Pattern: small-saas with AWS resources
- Infrastructure as code with best practices

### Phase 3: CI/CD Pipelines
- GitHub Actions workflows
- Automated deployment pipelines
- Database migration automation

### Phase 4: Observability Stack
- Prometheus configuration
- Grafana dashboards
- Structured logging setup

### Phase 5: Advanced Patterns
- Kubernetes Helm charts
- Multi-region deployments
- Blue-green deployment strategies

---

**Status**: Ready for Implementation
**Priority**: HIGH - Foundational capability for Team F
**Estimated Effort**: 3-4 weeks (phased TDD approach)
**Risk Level**: Medium - Docker complexity, framework-specific builds
