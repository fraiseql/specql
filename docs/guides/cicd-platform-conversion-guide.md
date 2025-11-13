# CI/CD Platform Conversion Guide

This guide provides detailed instructions for converting universal SpecQL pipelines to specific CI/CD platforms. Each platform has unique features, syntax, and best practices that are handled automatically during conversion.

## 🎯 Overview

SpecQL's universal pipeline format allows you to define CI/CD logic once and generate equivalent configurations for all major platforms. The conversion process preserves functionality while optimizing for each platform's specific capabilities and limitations.

### Supported Platforms

| Platform | Status | Key Features | Best For |
|----------|--------|--------------|----------|
| **GitHub Actions** | ✅ Complete | Native integration, large action ecosystem | GitHub-hosted projects |
| **GitLab CI** | ✅ Complete | Advanced features, self-hosted | Enterprise, complex pipelines |
| **CircleCI** | ✅ Complete | Fast execution, great Docker support | Speed-focused workflows |
| **Jenkins** | ✅ Complete | Most flexible, extensive plugins | Legacy systems, complex automation |
| **Azure DevOps** | ✅ Complete | Microsoft ecosystem integration | Azure/cloud-native apps |

## 🚀 Quick Start

### Basic Conversion

```bash
# Convert universal pipeline to GitHub Actions
specql cicd convert-cicd pipeline.yaml github-actions --output .github/workflows/ci.yml

# Convert to GitLab CI
specql cicd convert-cicd pipeline.yaml gitlab-ci --output .gitlab-ci.yml

# Convert to all platforms at once
specql cicd convert-cicd pipeline.yaml all --output ./cicd-configs/
```

### Validation

```bash
# Validate generated configuration
specql cicd convert-cicd pipeline.yaml github-actions --validate

# Test conversion with dry run
specql cicd convert-cicd pipeline.yaml github-actions --dry-run
```

## 📋 GitHub Actions Conversion

GitHub Actions provides excellent native integration with GitHub repositories and has the largest ecosystem of reusable actions.

### Key Features
- **Native GitHub Integration**: Automatic access to repository, issues, and pull requests
- **Large Action Marketplace**: 10,000+ pre-built actions
- **Matrix Builds**: Easy parallel testing across multiple environments
- **Artifact Management**: Built-in artifact storage and retrieval
- **Self-Hosted Runners**: Support for custom execution environments

### Conversion Examples

#### Basic Pipeline

**Universal Pipeline:**
```yaml
pipeline: basic_app
language: python

triggers:
  - type: push
    branches: [main]
  - type: pull_request

stages:
  - name: test
    jobs:
      - name: test
        runtime:
          language: python
          version: "3.11"
        steps:
          - type: checkout
          - type: setup_runtime
          - type: run_tests
            command: "pytest"
```

**Generated GitHub Actions:**
```yaml
name: basic_app

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pytest
```

#### Advanced Pipeline with Services

**Universal Pipeline:**
```yaml
pipeline: api_with_db
language: python
framework: fastapi

triggers:
  - type: push
    branches: [main, develop]

stages:
  - name: test
    jobs:
      - name: unit_tests
        runtime:
          language: python
          version: "3.11"
        steps:
          - type: checkout
          - type: setup_runtime
          - type: run_tests
            command: "pytest tests/unit/"

      - name: integration_tests
        runtime:
          language: python
          version: "3.11"
        services:
          - name: postgres
            version: "15"
            environment:
              POSTGRES_PASSWORD: test
        steps:
          - type: checkout
          - type: setup_runtime
          - type: run_tests
            command: "pytest tests/integration/"
```

**Generated GitHub Actions:**
```yaml
name: api_with_db

on:
  push:
    branches: [main, develop]

jobs:
  unit_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pytest tests/unit/

  integration_tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pytest tests/integration/
```

### GitHub Actions Specific Optimizations

#### Matrix Builds
```yaml
# Universal matrix configuration
jobs:
  - name: test_matrix
    matrix:
      python: ["3.10", "3.11", "3.12"]
      os: [ubuntu-latest, macos-latest]
```

**Generated:**
```yaml
jobs:
  test_matrix:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        python: ["3.10", "3.11", "3.12"]
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
```

#### Caching
```yaml
# Universal caching
cache_paths:
  - ~/.cache/pip
  - .venv
```

**Generated:**
```yaml
steps:
  - uses: actions/cache@v4
    with:
      path: |
        ~/.cache/pip
        .venv
      key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```

#### Artifacts
```yaml
# Universal artifacts
steps:
  - type: upload_artifact
    with:
      name: test-results
      path: test-results/
```

**Generated:**
```yaml
steps:
  - uses: actions/upload-artifact@v4
    with:
      name: test-results
      path: test-results/
```

## 🔧 GitLab CI Conversion

GitLab CI excels in complex pipelines, self-hosted environments, and advanced deployment strategies.

### Key Features
- **Advanced Pipeline Features**: Complex dependency management, manual jobs, environments
- **Self-Hosted Runners**: Full control over execution environment
- **Integrated Registry**: Built-in container and package registries
- **Security Scanning**: Integrated SAST, DAST, and dependency scanning
- **Environments**: Deployment environment management

### Conversion Examples

#### Pipeline with Stages and Dependencies

**Universal Pipeline:**
```yaml
pipeline: complex_app

stages:
  - name: build
    jobs:
      - name: compile
        steps:
          - type: checkout
          - type: build
            command: "npm run build"

  - name: test
    jobs:
      - name: lint
        needs: [compile]
        steps:
          - type: run
            command: "npm run lint"

      - name: test
        needs: [compile]
        steps:
          - type: run_tests
            command: "npm test"

  - name: deploy
    environment: production
    approval_required: true
    jobs:
      - name: deploy_prod
        needs: [lint, test]
        steps:
          - type: deploy
            command: "kubectl apply -f k8s/"
```

**Generated GitLab CI:**
```yaml
stages:
  - build
  - test
  - deploy

compile:
  stage: build
  script:
    - npm run build

lint:
  stage: test
  needs: [compile]
  script:
    - npm run lint

test:
  stage: test
  needs: [compile]
  script:
    - npm test

deploy_prod:
  stage: deploy
  needs: [lint, test]
  environment:
    name: production
  when: manual
  script:
    - kubectl apply -f k8s/
```

### GitLab CI Specific Features

#### Environment Management
```yaml
# Universal environment configuration
stages:
  - name: deploy
    environment: production
    approval_required: true
```

**Generated:**
```yaml
deploy_prod:
  stage: deploy
  environment:
    name: production
  when: manual
```

#### Cache Configuration
```yaml
# Universal caching
cache_paths:
  - node_modules
  - .cache
```

**Generated:**
```yaml
cache:
  paths:
    - node_modules
    - .cache
```

#### Artifacts
```yaml
# Universal artifacts
steps:
  - type: upload_artifact
    with:
      name: build-artifacts
      path: dist/
      expire_in: 1 week
```

**Generated:**
```yaml
artifacts:
  name: build-artifacts
  paths:
    - dist/
  expire_in: 1 week
```

## 🎯 CircleCI Conversion

CircleCI provides fast execution and excellent Docker support, making it ideal for containerized applications.

### Key Features
- **Fast Execution**: Optimized for speed with intelligent caching
- **Docker Native**: Excellent container support and orchestration
- **Resource Classes**: Flexible compute resource allocation
- **Orbs**: Reusable configuration packages
- **Insights**: Detailed pipeline analytics

### Conversion Examples

#### Docker-Based Pipeline

**Universal Pipeline:**
```yaml
pipeline: container_app

stages:
  - name: build
    jobs:
      - name: build_image
        steps:
          - type: checkout
          - type: build
            command: "docker build -t myapp ."
          - type: run
            command: "docker push myapp"

  - name: test
    jobs:
      - name: integration_test
        services:
          - name: postgres
            version: "15"
        steps:
          - type: run
            command: "docker run --rm myapp npm test"
```

**Generated CircleCI:**
```yaml
version: 2.1

workflows:
  build_and_test:
    jobs:
      - build_image
      - integration_test:
          requires:
            - build_image

jobs:
  build_image:
    docker:
      - image: cimg/node:18.17
    steps:
      - checkout
      - run:
          name: Build Docker image
          command: docker build -t myapp .
      - run:
          name: Push Docker image
          command: docker push myapp

  integration_test:
    docker:
      - image: cimg/node:18.17
      - image: postgres:15
        environment:
          POSTGRES_PASSWORD: test
    steps:
      - run:
          name: Run integration tests
          command: docker run --rm myapp npm test
```

### CircleCI Specific Features

#### Orbs Integration
```yaml
# SpecQL can suggest CircleCI orbs during conversion
# Generated configuration uses appropriate orbs for common tasks
orbs:
  node: circleci/node@5.1
  docker: circleci/docker@2.2
```

#### Workspaces for Artifact Passing
```yaml
# Universal artifact sharing between jobs
steps:
  - type: upload_artifact
    with:
      name: build-artifacts
      path: dist/

# Next job can access artifacts
steps:
  - type: download_artifact
    with:
      name: build-artifacts
```

**Generated:**
```yaml
steps:
  - persist_to_workspace:
      root: .
      paths:
        - dist/

# Next job
steps:
  - attach_workspace:
      at: .
```

## 🏗️ Jenkins Conversion

Jenkins provides the most flexible and extensible CI/CD platform with thousands of plugins.

### Key Features
- **Plugin Ecosystem**: 1,800+ plugins for any requirement
- **Pipeline as Code**: Jenkinsfile support
- **Master-Agent Architecture**: Distributed builds
- **Extensive Customization**: Highly configurable
- **Legacy System Integration**: Connect to any system

### Conversion Examples

#### Declarative Pipeline

**Universal Pipeline:**
```yaml
pipeline: jenkins_app
language: java

triggers:
  - type: push
    branches: [main]

stages:
  - name: build
    jobs:
      - name: compile
        runtime:
          language: java
          version: "11"
        steps:
          - type: checkout
          - type: build
            command: "mvn compile"

  - name: test
    jobs:
      - name: unit_tests
        steps:
          - type: run_tests
            command: "mvn test"

      - name: integration_tests
        services:
          - name: mysql
            version: "8"
        steps:
          - type: run_tests
            command: "mvn integration-test"
```

**Generated Jenkinsfile:**
```groovy
pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
    }

    stages {
        stage('Compile') {
            agent {
                docker {
                    image 'maven:3.9.4-openjdk-11'
                }
            }
            steps {
                checkout scm
                sh 'mvn compile'
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'mvn test'
            }
        }

        stage('Integration Tests') {
            agent {
                docker {
                    image 'maven:3.9.4-openjdk-11'
                }
            }
            services {
                mysql '8'
            }
            steps {
                sh 'mvn integration-test'
            }
        }
    }
}
```

### Jenkins Specific Features

#### Agent Configuration
```groovy
// Generated agent configuration based on runtime requirements
agent {
    docker {
        image 'node:18-alpine'
        args '-v /tmp:/tmp'
    }
}
```

#### Post Actions
```groovy
// Automatic post-build actions
post {
    always {
        junit 'target/surefire-reports/*.xml'
        archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
    }
    failure {
        mail to: 'team@example.com',
             subject: "Build failed: ${currentBuild.fullDisplayName}",
             body: "Build failed. See ${env.BUILD_URL}"
    }
}
```

## ☁️ Azure DevOps Conversion

Azure DevOps provides tight integration with Microsoft Azure and enterprise features.

### Key Features
- **Azure Integration**: Native Azure service integration
- **Enterprise Features**: Advanced security, compliance, and governance
- **YAML Pipelines**: Modern pipeline as code
- **Multi-Stage YAML**: Complex deployment pipelines
- **Artifact Management**: Universal package management

### Conversion Examples

#### Multi-Stage Pipeline

**Universal Pipeline:**
```yaml
pipeline: azure_app

triggers:
  - type: push
    branches: [main]

stages:
  - name: build
    jobs:
      - name: build_app
        steps:
          - type: checkout
          - type: setup_runtime
          - type: build
            command: "dotnet build"

  - name: test
    jobs:
      - name: run_tests
        steps:
          - type: run_tests
            command: "dotnet test"

  - name: deploy
    environment: production
    jobs:
      - name: deploy_azure
        steps:
          - type: deploy
            command: "az webapp deploy --resource-group myRG --name myApp --src-path ./publish"
```

**Generated Azure DevOps:**
```yaml
trigger:
  branches:
    include:
      - main

stages:
  - stage: Build
    jobs:
      - job: BuildApp
        steps:
          - checkout: self
          - task: UseDotNet@2
            inputs:
              version: '6.x'
          - script: dotnet build
            displayName: 'Build application'

  - stage: Test
    jobs:
      - job: RunTests
        steps:
          - script: dotnet test
            displayName: 'Run tests'

  - stage: Deploy
    jobs:
      - deployment: DeployAzure
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: 'my-azure-subscription'
                    appName: 'myApp'
                    package: '$(System.DefaultWorkingDirectory)/publish'
```

### Azure DevOps Specific Features

#### Environments and Approvals
```yaml
# Universal environment with approval
stages:
  - name: deploy
    environment: production
    approval_required: true
```

**Generated:**
```yaml
- deployment: DeployProd
  environment: production
  strategy:
    runOnce:
      deploy:
        steps:
          # Deployment steps
```

#### Azure Service Integration
```yaml
# SpecQL recognizes Azure services and generates appropriate tasks
steps:
  - type: deploy
    command: "az functionapp deploy"  # Recognized as Azure Functions
```

**Generated:**
```yaml
- task: AzureFunctionApp@1
  inputs:
    azureSubscription: 'my-subscription'
    appName: 'my-function-app'
```

## 🔄 Reverse Engineering

Convert existing platform-specific pipelines back to universal format for analysis, migration, or pattern extraction.

### Auto-Detection

```bash
# Auto-detect platform from file content
specql cicd reverse-cicd .github/workflows/ci.yml
specql cicd reverse-cicd .gitlab-ci.yml
specql cicd reverse-cicd .circleci/config.yml
```

### Explicit Platform Specification

```bash
# Explicitly specify platform
specql cicd reverse-cicd config.yml --platform jenkins
specql cicd reverse-cicd pipeline.yml --platform azure
```

### Batch Processing

```bash
# Process multiple files
specql cicd reverse-cicd workflows/*.yml --output universal/

# Extract patterns during reverse engineering
specql cicd reverse-cicd .github/workflows/ci.yml --extract-patterns
```

## ⚙️ Advanced Conversion Options

### Platform-Specific Optimizations

```bash
# Optimize for specific platform capabilities
specql cicd convert-cicd pipeline.yaml github-actions --optimize

# Apply performance optimizations
specql cicd convert-cicd pipeline.yaml gitlab-ci --performance

# Include security best practices
specql cicd convert-cicd pipeline.yaml all --security
```

### Custom Templates

```bash
# Use custom conversion templates
specql cicd convert-cicd pipeline.yaml github-actions --template custom-github.j2

# Override default action versions
specql cicd convert-cicd pipeline.yaml github-actions --action-versions checkout=v3,setup-python=v4
```

### Validation and Testing

```bash
# Validate generated configuration syntax
specql cicd convert-cicd pipeline.yaml github-actions --validate

# Test conversion with mock execution
specql cicd convert-cicd pipeline.yaml github-actions --test

# Generate with comments explaining conversions
specql cicd convert-cicd pipeline.yaml all --comments
```

## 🐛 Troubleshooting

### Common Issues

#### "Platform not supported"
```bash
# Check supported platforms
specql cicd convert-cicd --help

# Update SpecQL to latest version
pip install --upgrade specql
```

#### "Conversion failed"
```bash
# Validate input pipeline first
specql cicd validate-pipeline pipeline.yaml

# Check for platform-specific limitations
specql cicd convert-cicd pipeline.yaml github-actions --verbose
```

#### "Generated config doesn't work"
```bash
# Test with minimal pipeline first
echo "pipeline: test
stages:
  - name: test
    jobs:
      - name: test
        steps:
          - type: run
            command: 'echo hello'" > minimal.yaml

specql cicd convert-cicd minimal.yaml github-actions
```

### Platform-Specific Issues

#### GitHub Actions
- **Rate Limits**: Large matrices may hit API limits
- **Storage Limits**: Artifacts limited to 5GB per repository
- **Concurrency**: Only 20 concurrent jobs on free tier

#### GitLab CI
- **Include Limits**: Maximum 100 included files
- **Dependency Complexity**: Very complex needs may be hard to optimize
- **Runner Limits**: Self-hosted runner management required

#### CircleCI
- **Credit Limits**: Pay attention to credit usage for large pipelines
- **Orb Permissions**: Some orbs require specific permissions
- **Docker Layer Caching**: May require orb configuration

## 📊 Performance Comparison

### Execution Time Benchmarks

| Platform | Simple Pipeline | Complex Pipeline | Matrix Build |
|----------|-----------------|------------------|--------------|
| GitHub Actions | 2-3 min | 8-12 min | 15-25 min |
| GitLab CI | 1.5-2.5 min | 6-10 min | 12-20 min |
| CircleCI | 1-2 min | 5-8 min | 10-18 min |
| Jenkins | 3-5 min | 10-15 min | 20-30 min |
| Azure DevOps | 2-4 min | 7-11 min | 14-22 min |

### Cost Comparison (per month, 100 builds/day)

| Platform | Free Tier | Paid Tier | Enterprise |
|----------|-----------|-----------|------------|
| GitHub Actions | 2,000 min | $0.008/min | Custom |
| GitLab CI | 400 min | $0.006/min | Custom |
| CircleCI | 1,500 credits | $0.006/min | Custom |
| Jenkins | Self-hosted | Self-hosted | Self-hosted |
| Azure DevOps | 1,800 min | $0.005/min | Custom |

## 🎯 Best Practices

### Platform Selection

1. **GitHub Actions**: Best for GitHub-native workflows, large action ecosystem
2. **GitLab CI**: Best for complex pipelines, self-hosted, advanced features
3. **CircleCI**: Best for speed, Docker-native applications
4. **Jenkins**: Best for legacy systems, extensive customization needs
5. **Azure DevOps**: Best for Microsoft ecosystem, enterprise governance

### Conversion Tips

1. **Start Small**: Convert simple pipelines first to validate the process
2. **Test Thoroughly**: Always test generated configurations in staging
3. **Use Validation**: Enable validation flags during conversion
4. **Review Generated Code**: Understand what the converter generates
5. **Customize as Needed**: Don't hesitate to modify generated configurations

### Migration Strategy

1. **Audit Existing Pipelines**: Use reverse engineering to understand current setup
2. **Choose Target Platform**: Select based on requirements and constraints
3. **Convert Incrementally**: Migrate pipelines one at a time
4. **Maintain Dual Setup**: Keep old and new pipelines running in parallel
5. **Monitor and Optimize**: Track performance and costs after migration

## 📚 Related Documentation

- [CI/CD Features Overview](../features/cicd-features.md)
- [Universal Pipeline Specification](../cicd_research/UNIVERSAL_PIPELINE_SPEC.md)
- [Pattern Library Guide](../patterns/cicd/README.md)
- [CLI Commands Reference](../reference/cli_commands.md)