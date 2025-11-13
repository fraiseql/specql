# Getting Started with CI/CD Pipelines

This guide will walk you through your first SpecQL CI/CD pipeline, from installation to deployment. By the end, you'll have a working pipeline that builds, tests, and deploys your application across multiple platforms.

## 🎯 What You'll Learn

- Create your first universal CI/CD pipeline
- Generate platform-specific configurations
- Use the pattern library for rapid development
- Set up automated testing and deployment
- Convert existing pipelines to universal format

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- Git
- Docker (optional, for containerized builds)

### Install SpecQL
```bash
# Install SpecQL with CI/CD features
pip install specql

# Verify installation
specql --version

# Check CI/CD commands are available
specql cicd --help
```

### Sample Project
We'll use a simple Python FastAPI application for this tutorial. Create a new project:

```bash
# Create project directory
mkdir fastapi-tutorial
cd fastapi-tutorial

# Initialize Git repository
git init

# Create basic FastAPI app
mkdir -p src/myapp
```

Create `src/myapp/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="My FastAPI App")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Create `pyproject.toml`:
```toml
[project]
name = "my-fastapi-app"
version = "0.1.0"
description = "A simple FastAPI application"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "httpx>=0.24.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0"
]
```

Create `tests/test_main.py`:
```python
from fastapi.testclient import TestClient
from src.myapp.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

## 🚀 Tutorial 1: Generate Your First Pipeline

### Step 1: Auto-Generate Pipeline from Project

SpecQL can analyze your project structure and generate an appropriate pipeline:

```bash
# Auto-generate pipeline based on project structure
specql cicd generate-cicd --auto --language python --framework fastapi --output pipeline.yaml
```

This creates a `pipeline.yaml` file with a complete CI/CD pipeline tailored to your FastAPI project.

### Step 2: Review Generated Pipeline

Let's examine what was generated:

```yaml
pipeline: fastapi_app
description: "FastAPI application with automated testing and deployment"
language: python
framework: fastapi

triggers:
  - type: push
    branches: [main, develop]
  - type: pull_request
    branches: [main]

stages:
  - name: test
    jobs:
      - name: lint
        runtime:
          language: python
          version: "3.11"
        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies
            command: "uv pip install -e .[dev]"
          - type: lint
            command: "uv run ruff check src/"
          - type: run
            name: "Type checking"
            command: "uv run mypy src/"

      - name: unit_tests
        runtime:
          language: python
          version: "3.11"
        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies
          - type: run_tests
            command: "uv run pytest tests/ --cov=src"

  - name: build
    jobs:
      - name: docker_build
        steps:
          - type: checkout
          - type: build
            name: "Build Docker image"
            command: "docker build -t my-fastapi-app:${{ git.sha }} ."
          - type: run
            name: "Push to registry"
            command: "docker push my-fastapi-app:${{ git.sha }}"

  - name: deploy
    environment: staging
    jobs:
      - name: deploy_staging
        steps:
          - type: deploy
            command: "kubectl set image deployment/myapp myapp=my-fastapi-app:${{ git.sha }}"
```

### Step 3: Generate Platform-Specific Configs

Convert your universal pipeline to GitHub Actions:

```bash
# Generate GitHub Actions workflow
specql cicd convert-cicd pipeline.yaml github-actions --output .github/workflows/ci.yml
```

This creates `.github/workflows/ci.yml` with the equivalent GitHub Actions workflow.

## 🧪 Tutorial 2: Test Your Pipeline Locally

### Step 1: Validate Pipeline Syntax

```bash
# Validate your universal pipeline
specql cicd validate-pipeline pipeline.yaml

# Should output: ✅ Pipeline validation successful
```

### Step 2: Test Conversion Quality

```bash
# Test the generated GitHub Actions workflow
specql cicd convert-cicd pipeline.yaml github-actions --validate

# Generate with verbose output to see conversion details
specql cicd convert-cicd pipeline.yaml github-actions --verbose
```

### Step 3: Preview Generated Output

```bash
# Preview GitHub Actions without writing files
specql cicd convert-cicd pipeline.yaml github-actions

# The generated YAML will be displayed in your terminal
```

## 📚 Tutorial 3: Use the Pattern Library

### Step 1: Explore Available Patterns

```bash
# List all available CI/CD patterns
specql cicd search-pipeline --list

# Search for FastAPI-related patterns
specql cicd search-pipeline "fastapi"

# Get detailed information about a pattern
specql cicd search-pipeline --show python_fastapi_backend
```

### Step 2: Generate from Pattern

Instead of auto-generation, use a proven pattern:

```bash
# Generate from the FastAPI backend pattern
specql cicd generate-cicd --from-pattern python_fastapi_backend --output pattern-pipeline.yaml
```

### Step 3: Customize the Pattern

Modify the generated pipeline for your specific needs:

```bash
# Customize database and deployment settings
specql cicd generate-cicd --from-pattern python_fastapi_backend \
  --customize '{"database": "postgresql", "deployment": "kubernetes", "monitoring": "prometheus"}' \
  --output custom-pipeline.yaml
```

## 🔄 Tutorial 4: Convert Existing Pipelines

### Step 1: Find an Existing Pipeline

If you have an existing CI/CD pipeline, you can convert it to universal format. Let's create a sample GitHub Actions workflow to demonstrate:

Create `.github/workflows/existing-ci.yml`:
```yaml
name: Existing CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: ruff check src/
      - run: pytest tests/
```

### Step 2: Reverse Engineer to Universal Format

```bash
# Convert existing GitHub Actions to universal pipeline
specql cicd reverse-cicd .github/workflows/existing-ci.yml --output reversed-pipeline.yaml
```

### Step 3: Compare Original and Reversed

```bash
# View the reversed universal pipeline
cat reversed-pipeline.yaml

# It should contain the equivalent universal representation
```

### Step 4: Generate for Multiple Platforms

```bash
# Generate GitLab CI from the reversed pipeline
specql cicd convert-cicd reversed-pipeline.yaml gitlab-ci --output .gitlab-ci.yml

# Generate CircleCI config
specql cicd convert-cicd reversed-pipeline.yaml circleci --output .circleci/config.yml

# Generate all platforms at once
specql cicd convert-cicd reversed-pipeline.yaml all --output ./cicd-platforms/
```

## 🚀 Tutorial 5: Advanced Pipeline Features

### Step 1: Add Matrix Builds

Edit your `pipeline.yaml` to include matrix testing:

```yaml
stages:
  - name: test
    jobs:
      - name: matrix_test
        runtime:
          language: python
        matrix:
          python: ["3.10", "3.11", "3.12"]
          os: [ubuntu-latest, macos-latest]
        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies
          - type: run_tests
```

### Step 2: Add Services (Databases)

Add database integration testing:

```yaml
stages:
  - name: test
    jobs:
      - name: integration_tests
        runtime:
          language: python
          version: "3.11"
        services:
          - name: postgres
            version: "15"
            environment:
              POSTGRES_PASSWORD: test
            ports: [5432]
        steps:
          - type: checkout
          - type: setup_runtime
          - type: install_dependencies
          - type: run
            name: "Run database migrations"
            command: "python manage.py migrate"
          - type: run_tests
            command: "pytest tests/integration/"
```

### Step 3: Add Deployment Approvals

Add manual approval for production deployments:

```yaml
stages:
  - name: deploy
    environment: production
    approval_required: true
    jobs:
      - name: deploy_production
        steps:
          - type: deploy
            command: "kubectl apply -f k8s/production/"
          - type: run
            name: "Health check"
            command: "curl -f https://api.example.com/health"
```

### Step 4: Add Caching

Optimize build times with caching:

```yaml
pipeline: optimized_app
cache_paths:
  - ~/.cache/pip
  - .venv
  - node_modules

stages:
  - name: test
    jobs:
      - name: test_with_cache
        steps:
          - type: checkout
          - type: cache_restore
            with:
              key: pip-${{ hashFiles('pyproject.toml') }}
          - type: setup_runtime
          - type: install_dependencies
          - type: cache_save
            with:
              key: pip-${{ hashFiles('pyproject.toml') }}
          - type: run_tests
```

## 📊 Tutorial 6: Performance Benchmarking

### Step 1: Benchmark Your Pipeline

```bash
# Run performance benchmark
specql cicd benchmark execution pipeline.yaml --iterations 3

# Benchmark resource usage
specql cicd benchmark resources pipeline.yaml

# Compare performance across platforms
specql cicd benchmark compare pipeline.yaml --platforms github-actions,gitlab-ci
```

### Step 2: Analyze Results

The benchmark will show:
- Execution time for each stage
- Resource usage (CPU, memory)
- Reliability metrics
- Cost estimates across platforms

### Step 3: Optimize Based on Results

```bash
# Get optimization suggestions
specql cicd recommend-pipeline pipeline.yaml --optimize

# Apply automatic optimizations
specql cicd optimize-pipeline pipeline.yaml --caching --parallelization --output optimized-pipeline.yaml
```

## 🤖 Tutorial 7: AI-Powered Recommendations

### Step 1: Get Pipeline Recommendations

```bash
# Get AI recommendations for your project
specql cicd recommend-pipeline --language python --framework fastapi --database postgres

# Analyze existing pipeline for improvements
specql cicd recommend-pipeline pipeline.yaml --analyze
```

### Step 2: Security Recommendations

```bash
# Get security-focused recommendations
specql cicd recommend-pipeline pipeline.yaml --security

# Add security scanning to your pipeline
specql cicd optimize-pipeline pipeline.yaml --security --output secure-pipeline.yaml
```

## 🎯 Tutorial 8: Complete Workflow

### Step 1: Set Up Complete CI/CD

Create a comprehensive pipeline for your FastAPI app:

```bash
# 1. Generate initial pipeline
specql cicd generate-cicd --auto --language python --framework fastapi --output complete-pipeline.yaml

# 2. Add customizations
specql cicd generate-cicd --from-pattern python_fastapi_backend \
  --customize '{
    "database": "postgresql",
    "cache": "redis",
    "monitoring": "prometheus",
    "deployment": "kubernetes"
  }' \
  --output complete-pipeline.yaml

# 3. Generate for your preferred platform
specql cicd convert-cicd complete-pipeline.yaml github-actions --output .github/workflows/ci.yml

# 4. Validate everything works
specql cicd validate-pipeline complete-pipeline.yaml
specql cicd convert-cicd complete-pipeline.yaml github-actions --validate
```

### Step 2: Commit and Push

```bash
# Add generated files to Git
git add .
git commit -m "Add CI/CD pipeline with SpecQL"

# Push to trigger the pipeline
git push origin main
```

### Step 3: Monitor Your Pipeline

Watch your pipeline run on GitHub Actions and see:
- ✅ Code checkout and setup
- ✅ Dependency installation
- ✅ Linting and type checking
- ✅ Unit and integration tests
- ✅ Docker build and push
- ✅ Deployment to staging

## 🐛 Troubleshooting

### Common Issues

#### "Command not found"
```bash
# Ensure SpecQL is installed
pip install specql

# Check PATH
which specql

# Use python module if needed
python -m src.cli.main cicd --help
```

#### "Pipeline validation failed"
```bash
# Get detailed validation errors
specql cicd validate-pipeline pipeline.yaml --verbose

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('pipeline.yaml'))"
```

#### "Conversion failed"
```bash
# Try with verbose output
specql cicd convert-cicd pipeline.yaml github-actions --verbose

# Check if target platform is supported
specql cicd convert-cicd --help
```

#### "Pattern not found"
```bash
# List available patterns
specql cicd search-pipeline --list

# Search with broader terms
specql cicd search-pipeline "python"
```

### Getting Help

```bash
# General CI/CD help
specql cicd --help

# Command-specific help
specql cicd convert-cicd --help
specql cicd generate-cicd --help

# Check SpecQL version
specql --version
```

## 🎉 Next Steps

Now that you have a working CI/CD pipeline, you can:

1. **Explore Advanced Features**:
   - Add more complex testing strategies
   - Implement blue-green deployments
   - Set up automated rollbacks

2. **Customize Further**:
   - Add custom steps and scripts
   - Integrate with your specific tools
   - Create organization-wide patterns

3. **Scale Up**:
   - Convert pipelines for multiple projects
   - Set up monorepo configurations
   - Implement pipeline composition

4. **Learn More**:
   - [CI/CD Features Overview](../features/cicd-features.md)
   - [Platform Conversion Guide](../guides/cicd-platform-conversion-guide.md)
   - [Pattern Library Guide](../patterns/cicd/README.md)

## 📚 Additional Resources

- [Universal Pipeline Specification](../cicd_research/UNIVERSAL_PIPELINE_SPEC.md)
- [CLI Commands Reference](../reference/cli_commands.md)
- [Best Practices Guide](../guides/best_practices.md)

Congratulations! You've successfully created your first SpecQL CI/CD pipeline. Your application now has automated testing, building, and deployment across multiple platforms.