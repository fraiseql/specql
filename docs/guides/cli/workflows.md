# Workflows - Common Development Patterns

This guide covers common SpecQL development workflows, from initial setup to production deployment. Learn efficient patterns for using the CLI in different scenarios.

## 🎯 What You'll Learn

- Development workflow patterns
- CI/CD pipeline integration
- Multi-environment deployments
- Troubleshooting workflows
- Team collaboration patterns
- Production maintenance workflows

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity specifications created](../getting-started/first-entity.md)
- Understanding of CLI commands

## 💡 Workflow Overview

### Development Cycle

```mermaid
graph LR
    A[Edit YAML] --> B[Validate]
    B --> C[Generate Schema]
    C --> D[Apply to DB]
    D --> E[Generate Tests]
    E --> F[Run Tests]
    F --> G[Check Coverage]
    G --> H{Changes Needed?}
    H -->|Yes| A
    H -->|No| I[Commit & Deploy]
```

### Workflow Categories

| Workflow | Purpose | Frequency |
|----------|---------|-----------|
| **Development** | Local coding and testing | Daily |
| **CI/CD** | Automated testing and deployment | Per commit |
| **Deployment** | Environment promotion | Per release |
| **Maintenance** | Production monitoring and updates | Weekly |
| **Troubleshooting** | Issue investigation and fixes | As needed |

## 🚀 Development Workflows

### Basic Development Cycle

```bash
# 1. Create/edit entity
vim entities/user.yaml

# 2. Validate YAML
specql validate entities/user.yaml

# 3. Generate schema
specql generate schema entities/user.yaml

# 4. Apply to local database
psql $DATABASE_URL -f db/schema/10_tables/user.sql

# 5. Generate tests
specql generate tests entities/user.yaml

# 6. Run tests
specql test run entities/user.yaml

# 7. Check coverage
specql test coverage entities/user.yaml

# 8. Commit changes
git add .
git commit -m "Add user entity with state machine"
```

### Iterative Development

```bash
# Quick validation during editing
specql validate entities/user.yaml

# Fast test cycle (skip generation if no schema changes)
specql test run --type pgtap entities/user.yaml

# Full cycle when schema changes
specql generate schema entities/user.yaml
specql generate tests entities/user.yaml
specql test run entities/user.yaml
```

### Multi-Entity Development

```bash
# Work on related entities together
specql validate entities/user.yaml entities/company.yaml entities/contact.yaml

# Generate all schemas
specql generate schema entities/user.yaml entities/company.yaml entities/contact.yaml

# Run tests for all
specql test run entities/user.yaml entities/company.yaml entities/contact.yaml

# Check cross-entity coverage
specql test coverage entities/user.yaml entities/company.yaml entities/contact.yaml
```

## 🔄 CI/CD Workflows

### GitHub Actions Pipeline

```yaml
# .github/workflows/specql.yml
name: SpecQL Pipeline

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install specql
      - run: specql validate entities/**/*.yaml

  test:
    needs: validate
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install specql pytest psycopg2-binary

      - name: Setup database
        run: |
          specql generate schema entities/**/*.yaml
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/**/*.sql

      - name: Generate tests
        run: specql generate tests entities/**/*.yaml

      - name: Run pgTAP tests
        run: specql test run --type pgtap entities/**/*.yaml

      - name: Run pytest tests
        run: |
          specql test run --type pytest entities/**/*.yaml --cov --cov-report xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Parallel Testing Workflow

```yaml
# .github/workflows/parallel-tests.yml
name: Parallel Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [1, 2, 3, 4]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install specql pytest psycopg2-binary

      # Setup database (same for all jobs)
      - name: Setup database
        run: |
          specql generate schema entities/**/*.yaml
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/**/*.sql
          specql generate tests entities/**/*.yaml

      # Split tests across jobs
      - name: Run tests
        run: |
          entities=$(ls entities/*.yaml | sed -n "${{ matrix.test-group }}~4p")
          specql test run $entities --parallel
```

### Performance Monitoring

```yaml
# .github/workflows/performance.yml
name: Performance Monitoring

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install specql

      - name: Setup performance environment
        run: |
          specql generate schema entities/**/*.yaml
          ./scripts/load_performance_data.sh

      - name: Run performance tests
        run: |
          specql test run --type performance entities/**/*.yaml \
            --baseline performance-baseline.json \
            --report performance-report.html

      - name: Check regressions
        run: |
          python scripts/check_performance_regression.py \
            --baseline performance-baseline.json \
            --current performance-results.json

      - name: Update baseline
        if: github.ref == 'refs/heads/main'
        run: |
          cp performance-results.json performance-baseline.json
          git add performance-baseline.json
          git commit -m "Update performance baseline"
          git push

      - name: Alert on issues
        if: failure()
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Performance regression detected!"}' \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 🚢 Deployment Workflows

### Environment Promotion

```bash
# Local development
export SPECQL_ENV=local
specql generate schema entities/**/*.yaml
psql $LOCAL_DB -f db/schema/**/*.sql

# Staging deployment
export SPECQL_ENV=staging
specql generate schema entities/**/*.yaml
psql $STAGING_DB -f db/schema/**/*.sql

# Production deployment
export SPECQL_ENV=production
specql generate schema entities/**/*.yaml
psql $PRODUCTION_DB -f db/schema/**/*.sql
```

### Blue-Green Deployment

```bash
# Generate schema for new version
specql generate schema entities/**/*.yaml --env production-v2

# Apply to blue environment
psql $BLUE_DB -f db/schema/**/*.sql

# Run tests against blue
specql test run entities/**/*.yaml --database-url $BLUE_DB

# Switch traffic to blue
kubectl set image deployment/myapp myapp=blue-image

# Keep green as rollback option
# (green still has old schema)
```

### Database Migration

```bash
# 1. Backup production database
pg_dump $PRODUCTION_DB > backup_$(date +%Y%m%d).sql

# 2. Generate new schema
specql generate schema entities/**/*.yaml --env production-new

# 3. Test migration on staging
psql $STAGING_DB -f db/schema/**/*.sql
specql test run entities/**/*.yaml --database-url $STAGING_DB

# 4. Apply migration with downtime
# Option A: Scheduled maintenance window
psql $PRODUCTION_DB -f db/schema/**/*.sql

# Option B: Rolling migration (if backward compatible)
# Apply schema changes first
psql $PRODUCTION_DB -f db/schema/00_foundation/*.sql
# Then update application
kubectl rollout restart deployment/myapp
# Then apply remaining schema
psql $PRODUCTION_DB -f db/schema/10_tables/*.sql
```

## 🔧 Maintenance Workflows

### Schema Synchronization

```bash
# Check if database matches YAML
specql diff entities/user.yaml --compare db/schema/10_tables/user.sql

# Regenerate if out of sync
specql generate schema entities/user.yaml --force

# Apply changes
psql $DATABASE_URL -f db/schema/10_tables/user.sql
```

### Test Suite Maintenance

```bash
# Regenerate all tests
specql generate tests entities/**/*.yaml --force

# Run full test suite
specql test run entities/**/*.yaml

# Update test baselines
specql test run --type performance entities/**/*.yaml --update-baseline

# Clean old test data
specql test clean entities/**/*.yaml
```

### Performance Monitoring

```bash
# Run performance tests
specql test run --type performance entities/**/*.yaml

# Check for regressions
specql test run --type performance entities/**/*.yaml --baseline baseline.json

# Profile slow operations
specql test profile entities/user.yaml --operation user_activate

# Generate performance report
specql test run --type performance entities/**/*.yaml --report monthly-report.html
```

## 🐛 Troubleshooting Workflows

### Test Failure Investigation

```bash
# 1. Run tests with verbose output
specql test run entities/user.yaml --verbose

# 2. Check test data setup
psql $DATABASE_URL -c "SELECT * FROM user LIMIT 5;"

# 3. Run specific failing test
specql test run entities/user.yaml --filter "*failing_test*"

# 4. Check database logs
tail -f /var/log/postgresql/postgresql.log

# 5. Debug manually
psql $DATABASE_URL -f tests/pgtap/user_test.sql
```

### Schema Issues

```bash
# 1. Validate YAML
specql validate entities/user.yaml --verbose

# 2. Check generated SQL
cat db/schema/10_tables/user.sql

# 3. Test SQL syntax
psql $DATABASE_URL -f db/schema/10_tables/user.sql --dry-run

# 4. Check database state
psql $DATABASE_URL -c "\d user"

# 5. Compare with expected
specql diff entities/user.yaml --compare db/schema/10_tables/user.sql
```

### Performance Issues

```bash
# 1. Run performance tests
specql test run --type performance entities/user.yaml

# 2. Profile slow operations
specql test profile entities/user.yaml --operation user_activate

# 3. Check query plans
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM user WHERE status = 'active';"

# 4. Check indexes
psql $DATABASE_URL -c "SELECT * FROM pg_indexes WHERE tablename = 'user';"

# 5. Monitor system resources
top
iostat -x 1
```

### Environment Issues

```bash
# 1. Check SpecQL version
specql --version

# 2. Verify database connection
psql $DATABASE_URL -c "SELECT version();"

# 3. Check environment variables
env | grep -E "(DATABASE|SPECQL)"

# 4. Test basic functionality
specql validate --help

# 5. Check file permissions
ls -la entities/
ls -la db/schema/
```

## 👥 Team Collaboration Workflows

### Code Review Workflow

```bash
# Reviewer workflow
# 1. Checkout PR branch
git checkout feature/new-entity

# 2. Validate changes
specql validate entities/new_entity.yaml

# 3. Review generated code
cat db/schema/10_tables/new_entity.sql

# 4. Run tests
specql test run entities/new_entity.yaml

# 5. Check coverage
specql test coverage entities/new_entity.yaml

# 6. Review performance impact
specql test run --type performance entities/new_entity.yaml
```

### Pair Programming

```bash
# Driver: Edit YAML
vim entities/user.yaml

# Navigator: Validate in real-time
watch -n 2 specql validate entities/user.yaml

# Driver: Generate schema
specql generate schema entities/user.yaml

# Navigator: Review generated SQL
cat db/schema/10_tables/user.sql

# Both: Run tests together
specql test run entities/user.yaml
```

### Knowledge Sharing

```bash
# Document patterns
specql docs entities/user.yaml --output docs/entities/user.md

# Share test results
specql test coverage entities/user.yaml --format html --output coverage.html

# Create examples
specql generate tests entities/user.yaml --include-examples

# Export configuration
specql check-codes entities/**/*.yaml --export team_entity_codes.csv
```

## 🔄 Advanced Workflows

### Multi-Repository Setup

```bash
# Core entities in main repo
cd specql-core
specql generate schema entities/**/*.yaml

# Domain-specific entities in separate repos
cd ../specql-crm
specql generate schema entities/crm/**/*.yaml

# Shared foundation
cd ../specql-shared
specql generate schema --foundation-only entities/shared/**/*.yaml
```

### Microservices Architecture

```bash
# Service A: User management
cd services/user-service
specql generate schema entities/user.yaml entities/auth.yaml
specql generate tests entities/user.yaml entities/auth.yaml

# Service B: Order management
cd ../order-service
specql generate schema entities/order.yaml entities/payment.yaml
specql generate tests entities/order.yaml entities/payment.yaml

# Shared entities
cd ../shared-entities
specql generate schema entities/audit.yaml entities/common.yaml
```

### Multi-Environment Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]

    environment: ${{ matrix.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup SpecQL
        run: |
          pip install specql
          export SPECQL_ENV=${{ matrix.environment }}

      - name: Generate environment schema
        run: specql generate schema entities/**/*.yaml

      - name: Deploy to ${{ matrix.environment }}
        run: |
          # Environment-specific deployment
          if [ "${{ matrix.environment }}" = "staging" ]; then
            ./scripts/deploy_staging.sh
          else
            ./scripts/deploy_production.sh
          fi

      - name: Run smoke tests
        run: |
          specql test run entities/**/*.yaml \
            --database-url ${{ secrets.${{ matrix.environment }}_DATABASE_URL }}
```

## 📊 Workflow Analytics

### Development Metrics

```bash
# Track development velocity
specql analytics development --period 30d

# Example output:
Development Metrics (Last 30 Days)
=================================

Commits: 45
Entities Modified: 12
Tests Generated: 2340
Test Executions: 5670
Coverage: 94.2%
Performance Regressions: 0
Schema Changes: 8
```

### Team Productivity

```bash
# Team collaboration metrics
specql analytics team --period 7d

# Example output:
Team Productivity (Last 7 Days)
==============================

Active Developers: 5
Entities Created: 3
Tests Added: 450
Code Reviews: 12
Deployments: 7
Incidents: 0
```

### Quality Trends

```bash
# Quality metrics over time
specql analytics quality --period 90d

# Example output:
Quality Trends (Last 90 Days)
============================

Test Success Rate: 📈 98.5% → 99.2%
Coverage: 📈 92.1% → 94.2%
Performance: ➡️ Stable (no regressions)
Validation Errors: 📉 15 → 3 per week
```

## 🎯 Best Practices

### Development
- **Validate early** - Check YAML as you write
- **Test frequently** - Run tests after every change
- **Use version control** - Commit validated YAML
- **Document changes** - Explain schema modifications

### CI/CD
- **Parallel execution** - Split tests across multiple jobs
- **Fail fast** - Stop pipeline on critical failures
- **Comprehensive coverage** - Test all environments
- **Monitor performance** - Track metrics over time

### Deployment
- **Environment parity** - Keep environments similar
- **Rollback plans** - Prepare for deployment failures
- **Gradual rollouts** - Use feature flags and canary deployments
- **Monitoring** - Watch for issues post-deployment

### Maintenance
- **Regular updates** - Keep dependencies current
- **Performance monitoring** - Track system health
- **Backup strategies** - Regular database backups
- **Documentation** - Keep runbooks updated

## 🆘 Common Workflow Issues

### "Pipeline is slow"
```bash
# Optimize CI/CD
# - Use parallel jobs
# - Cache dependencies
# - Run tests incrementally
# - Use faster test runners

# Example optimization
- name: Cache SpecQL
  uses: actions/cache@v3
  with:
    path: ~/.cache/specql
    key: specql-${{ hashFiles('entities/**/*.yaml') }}
```

### "Environment drift"
```bash
# Prevent environment differences
# - Use infrastructure as code
# - Automate deployments
# - Test in staging first
# - Monitor environment parity

# Check environment consistency
specql diff entities/user.yaml --compare staging_schema.sql
specql diff entities/user.yaml --compare production_schema.sql
```

### "Test flakes"
```bash
# Stabilize tests
# - Use fixed test data
# - Isolate test execution
# - Avoid timing dependencies
# - Mock external services

# Debug flaky tests
specql test run entities/user.yaml --verbose --repeat 3
```

### "Deployment failures"
```bash
# Improve deployment reliability
# - Test deployments in staging
# - Use blue-green deployments
# - Implement health checks
# - Prepare rollback procedures

# Deployment checklist
- [ ] Schema validated
- [ ] Tests passing
- [ ] Performance tested
- [ ] Rollback plan ready
- [ ] Monitoring configured
```

## 📊 Workflow Metrics

### Development Efficiency
- **Validation time**: <5 seconds per entity
- **Test execution**: <2 minutes for typical suite
- **Schema generation**: <10 seconds for typical project
- **CI/CD pipeline**: <5 minutes total

### Quality Assurance
- **Test coverage**: >95% of generated code
- **Validation success**: >99% of commits
- **Performance stability**: <5% variance
- **Deployment success**: >99% of deployments

### Team Productivity
- **Development velocity**: 10-15 entities per week
- **Test automation**: 100% of code paths tested
- **Documentation coverage**: 100% of entities documented
- **Knowledge sharing**: Weekly team reviews

## 🎉 Summary

SpecQL workflows provide:
- ✅ **Streamlined development** - Fast iteration cycles
- ✅ **Automated CI/CD** - Reliable testing and deployment
- ✅ **Multi-environment support** - Consistent deployments
- ✅ **Team collaboration** - Shared patterns and practices
- ✅ **Production maintenance** - Monitoring and optimization
- ✅ **Troubleshooting efficiency** - Fast issue resolution

## 🚀 What's Next?

- **[Generate Commands](generate.md)** - Schema and test generation
- **[Validate Commands](validate.md)** - YAML validation and checking
- **[Test Commands](test.md)** - Running and managing tests
- **[Performance Commands](performance.md)** - Benchmarking and optimization

**Ready to master SpecQL workflows? Let's build something amazing! 🚀**