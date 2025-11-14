# Week 05: CI/CD Pipeline Migration

**Objective**: Convert GitHub Actions to universal format and regenerate with SpecQL integration

## Day 1-2: Reverse Engineer Existing CI/CD

```bash
cd /home/lionel/code/specql

# Reverse engineer GitHub Actions workflows
uv run specql cicd reverse \
  ../printoptim_migration/.github/workflows/test.yml \
  --output ../printoptim_migration/cicd/universal_test.yaml \
  --platform github-actions

uv run specql cicd reverse \
  ../printoptim_migration/.github/workflows/deploy.yml \
  --output ../printoptim_migration/cicd/universal_deploy.yaml \
  --platform github-actions
```

## Day 3-4: Enhance with SpecQL Integration

```yaml
# cicd/universal_test_enhanced.yaml
pipeline: printoptim_test
language: python
framework: fastapi
database: postgresql

stages:
  validate:
    - name: specql_validation
      command: specql validate entities/**/*.yaml
      fail_fast: true

  test:
    - name: unit_tests
      command: pytest tests/unit/ -v
    - name: integration_tests
      command: pytest tests/integration/ -v
      requires:
        - database: postgresql
    - name: schema_generation_test
      command: specql generate entities/**/*.yaml --dry-run

  build:
    - name: generate_schema
      command: specql generate entities/**/*.yaml --output db/0_schema/
    - name: build_database
      command: confiture build --env test
```

## Day 5: Generate New Workflows

```bash
# Generate GitHub Actions with SpecQL integration
uv run specql cicd convert \
  ../printoptim_migration/cicd/universal_test_enhanced.yaml \
  github-actions \
  --output ../printoptim_migration/.github/workflows/specql_test.yml

uv run specql cicd convert \
  ../printoptim_migration/cicd/universal_deploy.yaml \
  github-actions \
  --output ../printoptim_migration/.github/workflows/specql_deploy.yml
```

## Deliverables

- ✅ Universal CI/CD YAML for PrintOptim
- ✅ Enhanced pipelines with SpecQL validation
- ✅ New GitHub Actions workflows
- ✅ CI/CD migration documentation