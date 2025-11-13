# Week 07: Integration Testing & Validation

**Objective**: Comprehensive testing of entire migration

## Day 1-2: Schema Testing

```bash
# Run full test suite against new schema
cd ../printoptim_migration
confiture build --env test

# Run application tests
pytest tests/ -v --cov=. --cov-report=html

# Generate test coverage report
open htmlcov/index.html
```

## Day 3: Data Integrity Testing

```bash
# Run data validation queries
psql printoptim_specql_test < db/migrations/validation/001_validate_migration.sql

# Check row counts match
psql printoptim_production_old -c "
SELECT
    'contact' as table_name,
    COUNT(*) as count
FROM contact
UNION ALL
SELECT 'company', COUNT(*) FROM company;
"

psql printoptim_specql_test -c "
SELECT
    'contact' as table_name,
    COUNT(*) as count
FROM crm.tb_contact
UNION ALL
SELECT 'company', COUNT(*) FROM crm.tb_company;
"
```

## Day 4: Performance Testing

```bash
# Run performance benchmarks
uv run python scripts/migration/performance_benchmark.py \
  --old-db printoptim_production_old \
  --new-db printoptim_specql_test \
  --queries tests/queries/benchmark_queries.sql

# Generate performance report
# Target: New schema performs within 10% of original
```

## Day 5: Security Audit

```bash
# Check for security issues
uv run python scripts/migration/security_audit.py \
  ../printoptim_migration/reverse_engineering/specql_output/ \
  > reverse_engineering/assessments/SECURITY_AUDIT.md

# Verify:
# - No SQL injection vulnerabilities
# - Proper RLS policies
# - Audit fields present
# - Sensitive data encrypted
```

## Deliverables

- ✅ Full test suite passing (>95% coverage)
- ✅ Data integrity validated
- ✅ Performance acceptable (±10%)
- ✅ Security audit clean