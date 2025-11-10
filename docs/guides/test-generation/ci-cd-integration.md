# CI/CD Integration - Automated Testing Pipelines

Learn how to integrate SpecQL's automatic test generation into your CI/CD pipelines. Set up automated testing for pgTAP, pytest, and performance tests across GitHub Actions, GitLab CI, and Jenkins.

## 🎯 What You'll Learn

- CI/CD integration for automatic test generation
- GitHub Actions, GitLab CI, and Jenkins examples
- Parallel test execution
- Test reporting and notifications
- Performance regression detection
- Multi-environment testing strategies

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity with patterns created](../getting-started/first-entity.md)
- CI/CD platform (GitHub Actions, GitLab CI, Jenkins)
- PostgreSQL database for testing

## 💡 CI/CD Testing Strategy

### Test Types in CI/CD

| Test Type | Speed | Coverage | When to Run |
|-----------|-------|----------|-------------|
| **pgTAP** | ⚡ Fast (seconds) | Database logic | Every commit |
| **pytest** | 🐌 Slower (minutes) | App integration | Every commit |
| **Performance** | 🐌 Slowest (minutes) | Benchmarks | Nightly/daily |

### Pipeline Stages

```mermaid
graph LR
    A[Code Push] --> B[Validate YAML]
    B --> C[Generate Schema]
    C --> D[Apply to Test DB]
    D --> E[Generate Tests]
    E --> F[Run pgTAP Tests]
    F --> G[Run pytest Tests]
    G --> H[Performance Tests]
    H --> I[Deploy]
```

## 🚀 GitHub Actions Integration

### Basic Test Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install specql pytest pytest-cov psycopg2-binary

      - name: Validate entities
        run: specql validate entities/*.yaml

      - name: Generate schema
        run: specql generate schema entities/*.yaml

      - name: Apply schema
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/10_tables/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/40_functions/*.sql

      - name: Generate tests
        run: specql generate tests entities/*.yaml

      - name: Run pgTAP tests
        run: specql test run --type pgtap entities/*.yaml

      - name: Run pytest tests
        run: |
          specql test run --type pytest entities/*.yaml \
            --cov --cov-report xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: pytest
```

### Parallel Test Execution

```yaml
# .github/workflows/parallel-tests.yml
name: Parallel Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [pgtap, pytest]
        entity-group: [1, 2, 3, 4]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install specql pytest psycopg2-binary

      # Setup database and schema (same as above)
      - name: Setup database
        run: |
          specql validate entities/*.yaml
          specql generate schema entities/*.yaml
          # Apply schema...

      - name: Generate tests
        run: specql generate tests entities/*.yaml

      - name: Run pgTAP tests
        if: matrix.test-type == 'pgtap'
        run: |
          # Split entities into groups
          entities=$(ls entities/*.yaml | sed -n "${{ matrix.entity-group }}~4p")
          specql test run --type pgtap $entities

      - name: Run pytest tests
        if: matrix.test-type == 'pytest'
        run: |
          entities=$(ls entities/*.yaml | sed -n "${{ matrix.entity-group }}~4p")
          specql test run --type pytest $entities --cov --cov-report xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: pytest-${{ matrix.entity-group }}
```

### Performance Testing Pipeline

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  performance:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install specql

      - name: Setup database with test data
        run: |
          specql generate schema entities/*.yaml
          # Apply schema and load performance test data
          ./scripts/load_performance_data.sh

      - name: Generate performance tests
        run: specql generate tests --type performance entities/*.yaml

      - name: Run performance tests
        run: |
          specql test run --type performance entities/*.yaml \
            --report performance-report.html \
            --baseline .github/performance-baseline.json

      - name: Check performance regression
        run: |
          python scripts/check_performance_regression.py \
            --baseline .github/performance-baseline.json \
            --current performance-results.json \
            --max-degradation 0.1

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance-report.html

      - name: Update baseline
        if: github.ref == 'refs/heads/main' && github.event_name == 'schedule'
        run: |
          cp performance-results.json .github/performance-baseline.json
          git add .github/performance-baseline.json
          git commit -m "Update performance baseline"
          git push

      - name: Alert on regression
        if: failure()
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Performance regression detected!"}' \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 🔄 GitLab CI Integration

### Basic Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - performance

variables:
  POSTGRES_DB: specql_test
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres

validate:
  stage: validate
  image: python:3.11
  services:
    - postgres:15
  script:
    - pip install specql
    - specql validate entities/*.yaml

test:pgtap:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  script:
    - pip install specql
    - specql generate schema entities/*.yaml
    - |
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/00_foundation/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/10_tables/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/40_functions/*.sql
    - specql generate tests entities/*.yaml
    - specql test run --type pgtap entities/*.yaml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week

test:pytest:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  script:
    - pip install specql pytest pytest-cov psycopg2-binary
    - specql generate schema entities/*.yaml
    - |
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/00_foundation/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/10_tables/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/40_functions/*.sql
    - specql generate tests entities/*.yaml
    - specql test run --type pytest entities/*.yaml --cov --cov-report xml --cov-report term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week

performance:
  stage: performance
  image: python:3.11
  services:
    - postgres:15
  script:
    - pip install specql
    - ./scripts/setup_performance_db.sh
    - specql generate tests --type performance entities/*.yaml
    - specql test run --type performance entities/*.yaml --report performance.html
    - python scripts/check_performance_regression.py
  artifacts:
    paths:
      - performance.html
    expire_in: 1 month
  only:
    - schedules  # Only run on scheduled pipelines
    - main
  when: manual  # Allow manual trigger
```

### Parallel Testing

```yaml
# .gitlab-ci.yml (parallel jobs)
.test_template: &test_template
  image: python:3.11
  services:
    - postgres:15
  before_script:
    - pip install specql pytest psycopg2-binary
    - specql generate schema entities/*.yaml
    - |
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/00_foundation/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/10_tables/*.sql
      psql -h postgres -U postgres -d $POSTGRES_DB -f db/schema/40_functions/*.sql
    - specql generate tests entities/*.yaml

test:pgtap:1/4:
  <<: *test_template
  script:
    - entities=$(ls entities/*.yaml | head -n 25)  # First 25%
    - specql test run --type pgtap $entities

test:pgtap:2/4:
  <<: *test_template
  script:
    - entities=$(ls entities/*.yaml | sed -n '26,50p')  # Next 25%
    - specql test run --type pgtap $entities

test:pgtap:3/4:
  <<: *test_template
  script:
    - entities=$(ls entities/*.yaml | sed -n '51,75p')  # Next 25%
    - specql test run --type pgtap $entities

test:pgtap:4/4:
  <<: *test_template
  script:
    - entities=$(ls entities/*.yaml | tail -n +76)  # Last 25%
    - specql test run --type pgtap $entities

test:pytest:1/4:
  <<: *test_template
  script:
    - entities=$(ls entities/*.yaml | head -n 25)
    - specql test run --type pytest $entities --cov --cov-report xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# Similar jobs for pytest 2/4, 3/4, 4/4...
```

## 🏗️ Jenkins Integration

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        DATABASE_URL = credentials('specql-db-url')
    }

    stages {
        stage('Validate') {
            steps {
                sh 'pip install specql'
                sh 'specql validate entities/*.yaml'
            }
        }

        stage('Setup Database') {
            steps {
                sh '''
                    # Create test database
                    createdb specql_test

                    # Generate and apply schema
                    specql generate schema entities/*.yaml
                    psql $DATABASE_URL -f db/schema/00_foundation/*.sql
                    psql $DATABASE_URL -f db/schema/10_tables/*.sql
                    psql $DATABASE_URL -f db/schema/40_functions/*.sql
                '''
            }
        }

        stage('Generate Tests') {
            steps {
                sh 'specql generate tests entities/*.yaml'
            }
        }

        stage('Test pgTAP') {
            steps {
                sh 'specql test run --type pgtap entities/*.yaml'
            }
            post {
                always {
                    sh 'specql test coverage entities/*.yaml --format html --output pgtap-coverage.html'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'pgtap-coverage.html',
                        reportName: 'pgTAP Coverage'
                    ])
                }
            }
        }

        stage('Test pytest') {
            steps {
                sh '''
                    pip install pytest pytest-cov psycopg2-binary
                    specql test run --type pytest entities/*.yaml --cov --cov-report xml
                '''
            }
            post {
                always {
                    cobertura([
                        autoUpdateHealth: false,
                        autoUpdateStability: false,
                        coberturaReportFile: 'coverage.xml',
                        conditionalCoverageTargets: '70, 0, 0',
                        failUnhealthy: false,
                        failUnstable: false,
                        lineCoverageTargets: '80, 0, 0',
                        maxNumberOfBuilds: 0,
                        methodCoverageTargets: '80, 0, 0',
                        onlyStable: false,
                        sourceEncoding: 'ASCII',
                        zoomCoverageChart: false
                    ])
                }
            }
        }

        stage('Performance Test') {
            when {
                anyOf {
                    triggeredBy 'TimerTrigger'  // Nightly builds
                    triggeredBy cause: 'UserIdCause'  // Manual trigger
                }
            }
            steps {
                sh '''
                    ./scripts/load_performance_data.sh
                    specql generate tests --type performance entities/*.yaml
                    specql test run --type performance entities/*.yaml --report performance.html
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'performance.html',
                        reportName: 'Performance Report'
                    ])
                }
                failure {
                    script {
                        // Send alert on performance regression
                        def message = "🚨 Performance regression detected in build ${env.BUILD_NUMBER}"
                        // Send to Slack, email, etc.
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'dropdb specql_test || true'  // Cleanup
        }
        failure {
            script {
                def message = "❌ Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
                // Send failure notification
            }
        }
    }
}
```

### Declarative Pipeline with Parallel

```groovy
// Jenkinsfile (parallel)
pipeline {
    agent any

    environment {
        DATABASE_URL = credentials('specql-db-url')
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    pip install specql pytest psycopg2-binary
                    specql validate entities/*.yaml
                    specql generate schema entities/*.yaml
                    createdb specql_test
                    # Apply schema...
                    specql generate tests entities/*.yaml
                '''
            }
        }

        stage('Parallel Tests') {
            parallel {
                stage('pgTAP Tests') {
                    steps {
                        script {
                            def entities = sh(script: 'ls entities/*.yaml', returnStdout: true).trim().split('\n')
                            def chunks = entities.collate(entities.size().intdiv(4) + 1)

                            def parallelStages = [:]
                            chunks.eachWithIndex { chunk, index ->
                                parallelStages["pgTAP-${index + 1}/${chunks.size()}"] = {
                                    sh "specql test run --type pgtap ${chunk.join(' ')}"
                                }
                            }

                            parallel parallelStages
                        }
                    }
                }

                stage('pytest Tests') {
                    steps {
                        script {
                            def entities = sh(script: 'ls entities/*.yaml', returnStdout: true).trim().split('\n')
                            def chunks = entities.collate(entities.size().intdiv(4) + 1)

                            def parallelStages = [:]
                            chunks.eachWithIndex { chunk, index ->
                                parallelStages["pytest-${index + 1}/${chunks.size()}"] = {
                                    sh "specql test run --type pytest ${chunk.join(' ')} --cov --cov-report xml"
                                }
                            }

                            parallel parallelStages
                        }
                    }
                }
            }
        }

        stage('Merge Coverage') {
            steps {
                sh '''
                    pip install coverage
                    coverage combine
                    coverage xml
                '''
            }
            post {
                always {
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
    }
}
```

## 📊 Test Reporting and Notifications

### Test Results Dashboard

```yaml
# .github/workflows/test-results.yml
name: Test Results Dashboard

on:
  workflow_run:
    workflows: ["Test Suite"]
    types: [completed]

jobs:
  dashboard:
    runs-on: ubuntu-latest

    steps:
      - name: Download test results
        uses: actions/download-artifact@v3
        with:
          name: test-results

      - name: Generate dashboard
        run: |
          python scripts/generate_test_dashboard.py \
            --results-dir ./test-results \
            --output dashboard.html

      - name: Upload dashboard
        uses: actions/upload-artifact@v3
        with:
          name: test-dashboard
          path: dashboard.html

      - name: Comment on PR
        if: github.event.workflow_run.event == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const dashboard = fs.readFileSync('dashboard.html', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🧪 Test Results Dashboard

${dashboard}

[View Full Report](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})`
            });
```

### Slack Notifications

```yaml
# .github/workflows/notifications.yml
name: Test Notifications

on:
  workflow_run:
    workflows: ["Test Suite", "Performance Tests"]
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest

    steps:
      - name: Get workflow conclusion
        id: conclusion
        run: |
          echo "result=${{ github.event.workflow_run.conclusion }}" >> $GITHUB_OUTPUT

      - name: Notify success
        if: steps.conclusion.outputs.result == 'success'
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{
              "text": "✅ Tests passed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*✅ All tests passed*\n\nWorkflow: ${{ github.event.workflow_run.name }}\nBranch: ${{ github.ref_name }}\nCommit: ${{ github.sha }}"
                  }
                }
              ]
            }' \
            ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Notify failure
        if: steps.conclusion.outputs.result == 'failure'
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{
              "text": "❌ Tests failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*❌ Tests failed*\n\nWorkflow: ${{ github.event.workflow_run.name }}\nBranch: ${{ github.ref_name }}\n\n[View Details](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"
                  }
                }
              ]
            }' \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Performance Regression Alerts

```python
# scripts/check_performance_regression.py
import json
import sys
import argparse
from typing import Dict, Any

def check_performance_regression(baseline_file: str, current_file: str, max_degradation: float) -> bool:
    """Check for performance regressions"""

    with open(baseline_file) as f:
        baseline = json.load(f)

    with open(current_file) as f:
        current = json.load(f)

    regressions = []

    for test_name in baseline.get('results', {}):
        if test_name in current.get('results', {}):
            baseline_mean = baseline['results'][test_name]['mean']
            current_mean = current['results'][test_name]['mean']

            degradation = (current_mean - baseline_mean) / baseline_mean

            if degradation > max_degradation:
                regressions.append({
                    'test': test_name,
                    'baseline': baseline_mean,
                    'current': current_mean,
                    'degradation': degradation
                })

    if regressions:
        print("🚨 Performance regressions detected:")
        for regression in regressions:
            print(".1%")
        return False

    print("✅ No performance regressions detected")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--current', required=True)
    parser.add_argument('--max-degradation', type=float, default=0.1)

    args = parser.parse_args()
    success = check_performance_regression(args.baseline, args.current, args.max_degradation)
    sys.exit(0 if success else 1)
```

## 🔧 Multi-Environment Testing

### Environment-Specific Configurations

```yaml
# .github/workflows/multi-env-tests.yml
name: Multi-Environment Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [development, staging, production]
        include:
          - environment: development
            database_url: postgresql://localhost:5432/specql_dev
            test_data_size: small
          - environment: staging
            database_url: ${{ secrets.STAGING_DATABASE_URL }}
            test_data_size: medium
          - environment: production
            database_url: ${{ secrets.PRODUCTION_DATABASE_URL }}
            test_data_size: large

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup environment
        run: |
          echo "DATABASE_URL=${{ matrix.database_url }}" >> $GITHUB_ENV
          echo "TEST_DATA_SIZE=${{ matrix.test_data_size }}" >> $GITHUB_ENV

      - name: Install dependencies
        run: pip install specql

      - name: Generate environment-specific tests
        run: |
          specql generate tests entities/*.yaml \
            --env ${{ matrix.environment }} \
            --test-data-size $TEST_DATA_SIZE

      - name: Run tests
        run: specql test run entities/*.yaml

      - name: Environment-specific assertions
        run: |
          if [ "${{ matrix.environment }}" = "production" ]; then
            # Stricter checks for production
            specql test run --type performance entities/*.yaml --strict
          fi
```

### Database Migration Testing

```yaml
# .github/workflows/migration-tests.yml
name: Migration Tests

on:
  push:
    paths:
      - 'db/migrations/**'

jobs:
  migration-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install specql

      # Test migration on clean database
      - name: Test migration from scratch
        run: |
          specql generate schema entities/*.yaml
          # Apply migrations in order
          for migration in db/migrations/*.sql; do
            psql postgresql://postgres:postgres@localhost:5432/postgres -f "$migration"
          done

      # Test migration on existing database
      - name: Test migration on existing data
        run: |
          # Setup base schema
          ./scripts/setup_base_schema.sh

          # Run migrations
          ./scripts/run_migrations.sh

          # Verify data integrity
          ./scripts/verify_data_integrity.sh

      - name: Generate tests on migrated schema
        run: specql generate tests entities/*.yaml

      - name: Run tests on migrated schema
        run: specql test run entities/*.yaml
```

## 📈 Advanced CI/CD Patterns

### Test Impact Analysis

```yaml
# .github/workflows/impact-analysis.yml
name: Test Impact Analysis

on: [pull_request]

jobs:
  impact-analysis:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Analyze changed files
        id: changed-files
        run: |
          # Get changed entity files
          changed_entities=$(git diff --name-only origin/main...HEAD | grep 'entities/.*\.yaml' || true)
          echo "changed_entities=$changed_entities" >> $GITHUB_OUTPUT

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install specql

      - name: Run targeted tests
        if: steps.changed-files.outputs.changed_entities != ''
        run: |
          for entity in ${{ steps.changed-files.outputs.changed_entities }}; do
            echo "Testing changed entity: $entity"
            specql validate "$entity"
            specql generate tests "$entity"
            specql test run "$entity"
          done

      - name: Run full test suite
        if: steps.changed-files.outputs.changed_entities == ''
        run: |
          echo "No entity changes detected, running full test suite"
          specql validate entities/*.yaml
          specql generate tests entities/*.yaml
          specql test run entities/*.yaml
```

### Test Result Caching

```yaml
# .github/workflows/cached-tests.yml
name: Cached Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache test dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Cache generated schema
        uses: actions/cache@v3
        id: schema-cache
        with:
          path: |
            db/schema/
            tests/
          key: ${{ runner.os }}-schema-${{ hashFiles('entities/*.yaml') }}

      - name: Install dependencies
        run: pip install specql pytest psycopg2-binary

      - name: Generate schema (if cache miss)
        if: steps.schema-cache.outputs.cache-hit != 'true'
        run: |
          specql validate entities/*.yaml
          specql generate schema entities/*.yaml
          specql generate tests entities/*.yaml

      - name: Setup test database
        run: |
          # Apply cached schema to fresh database
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/10_tables/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres \
            -f db/schema/40_functions/*.sql

      - name: Run tests
        run: |
          specql test run --type pgtap entities/*.yaml
          specql test run --type pytest entities/*.yaml --cov --cov-report xml
```

## 🎯 Best Practices

### Pipeline Design
- **Fast feedback**: Run critical tests first (pgTAP)
- **Parallel execution**: Split tests across multiple jobs
- **Incremental testing**: Only test changed components
- **Comprehensive coverage**: Full suite on main branch

### Test Data Management
- **Isolated databases**: Fresh database for each test run
- **Realistic data**: Use production-like test data
- **Data versioning**: Version test data with code
- **Cleanup**: Always clean up test data

### Monitoring and Alerting
- **Test metrics**: Track test execution time and failure rates
- **Performance baselines**: Monitor for performance regressions
- **Notifications**: Alert on failures and regressions
- **Dashboards**: Visual test result dashboards

### Security
- **Secret management**: Use platform secret stores
- **Database isolation**: Separate test databases
- **Access control**: Limit CI/CD system permissions
- **Audit logging**: Log all CI/CD activities

## 🆘 Troubleshooting

### "Tests pass locally but fail in CI"
```bash
# Check environment differences
# - PostgreSQL version
# - Python version
# - Database configuration
# - File permissions

# Debug with verbose output
specql test run entities/user.yaml --verbose

# Test with CI database locally
export DATABASE_URL="postgresql://localhost:5432/ci_test"
specql test run entities/user.yaml
```

### "Performance tests are flaky"
```bash
# Stabilize test environment
# - Use fixed test data sets
# - Control system load
# - Set appropriate timeouts
# - Use statistical analysis for results

# Check system resources
# - CPU usage during tests
# - Memory availability
# - Disk I/O performance
# - Network latency
```

### "Database connection issues"
```bash
# Verify database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check connection limits
psql $DATABASE_URL -c "SHOW max_connections;"

# Monitor connection pool
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Use connection pooling
# Configure PgBouncer or similar
```

### "Test timeouts"
```bash
# Increase timeout settings
specql test run entities/user.yaml --timeout 300

# Optimize slow tests
# - Add database indexes
# - Reduce test data size
# - Use faster assertions
# - Parallelize test execution

# Profile test execution
specql test profile entities/user.yaml
```

## 📊 Success Metrics

### Pipeline Efficiency
- **Test execution time**: <10 minutes for full suite
- **Time to feedback**: <5 minutes for critical tests
- **Parallel efficiency**: >80% CPU utilization
- **Cache hit rate**: >90% for unchanged code

### Test Quality
- **Test coverage**: >95% of generated code
- **Failure rate**: <1% in stable branches
- **Flaky test rate**: <0.1% of all tests
- **Performance regression detection**: >95% accuracy

### Business Impact
- **Deployment frequency**: Multiple deployments per day
- **Time to production**: <1 hour from commit to deploy
- **Defect escape rate**: <5% bugs reach production
- **Mean time to recovery**: <30 minutes for incidents

## 🎉 Summary

CI/CD integration provides:
- ✅ **Automated testing** - Tests run on every change
- ✅ **Fast feedback** - Immediate results for developers
- ✅ **Quality gates** - Prevent deployment of broken code
- ✅ **Performance monitoring** - Catch regressions early
- ✅ **Multi-environment testing** - Test across all environments
- ✅ **Parallel execution** - Faster test suites
- ✅ **Comprehensive reporting** - Visual dashboards and alerts

## 🚀 What's Next?

- **[Performance Testing](performance-tests.md)** - Advanced benchmarking
- **[Test Best Practices](../best-practices/testing.md)** - Testing strategies
- **[Monitoring](../best-practices/monitoring.md)** - Production monitoring
- **[Deployment Automation](../guides/deployment.md)** - Automated deployments

**Ready to automate your testing pipeline? Let's set up CI/CD! 🚀**