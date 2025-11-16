# Test Generation - Quick Reference

## Generate Tests

```bash
# All tests (pgTAP + pytest)
specql generate-tests entities/contact.yaml

# pgTAP only (database unit tests)
specql generate-tests entities/*.yaml --type pgtap -o tests/db/

# pytest only (integration tests)
specql generate-tests entities/*.yaml --type pytest -o tests/integration/

# Preview what would be generated
specql generate-tests entities/contact.yaml --preview

# Verbose output
specql generate-tests entities/*.yaml --verbose

# Overwrite existing files
specql generate-tests entities/contact.yaml --overwrite
```

## Reverse Engineer Tests

```bash
# Parse pgTAP tests
specql reverse-tests tests/test_contact.sql --preview

# Coverage analysis
specql reverse-tests tests/*.sql --analyze-coverage

# Gap analysis
specql reverse-tests tests/ --analyze-gaps --entity=Contact

# Convert to TestSpec YAML
specql reverse-tests tests/*.py --entity=Contact --output-dir=specs/ --format=yaml

# Multiple test files
specql reverse-tests tests/test_*.sql tests/test_*_integration.py
```

## Run Tests

```bash
# pgTAP tests (PostgreSQL unit tests)
pg_prove -d dbname tests/test_*.sql

# pytest tests (Python integration)
pytest tests/test_*_integration.py -v

# Run all tests together
pg_prove -d dbname tests/test_*.sql && pytest tests/test_*_integration.py -v
```

## What Gets Generated

| Entity Elements | pgTAP Tests | pytest Tests | Total |
|----------------|-------------|--------------|-------|
| 5 fields | 10-15 | - | 10-15 |
| Basic CRUD | 12-18 | 8-12 | 20-30 |
| 2 actions | 8-12 | 4-6 | 12-18 |
| Edge cases | 5-8 | 3-5 | 8-13 |
| **Total** | **35-53** | **15-23** | **50-76** |

## Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--type` | Test framework | `--type pgtap` |
| `--output-dir, -o` | Output location | `-o tests/` |
| `--preview` | Dry run | `--preview` |
| `--verbose, -v` | Detailed output | `-v` |
| `--overwrite` | Replace existing | `--overwrite` |
| `--entity` | Specify entity | `--entity=Contact` |
| `--format` | Output format | `--format=yaml` |

## Quick Examples

### Generate Tests for New Entity
```bash
# Generate all tests
specql generate-tests entities/user.yaml

# Check what was created
ls -la tests/
# test_user_structure.sql
# test_user_crud.sql
# test_user_actions.sql
# test_user_integration.py
```

### Analyze Existing Test Coverage
```bash
# Quick coverage check
specql reverse-tests tests/ --analyze-coverage --preview

# Detailed gap analysis
specql reverse-tests tests/ --analyze-gaps --entity=Contact --output-dir reports/
```

### CI/CD Integration
```bash
# Generate tests in CI
specql generate-tests entities/*.yaml --overwrite --verbose

# Run test suite
pg_prove -d $DATABASE_URL tests/test_*.sql
pytest tests/test_*_integration.py -v
```

## File Structure

```
tests/
├── db/                    # pgTAP tests
│   ├── test_contact_structure.sql
│   ├── test_contact_crud.sql
│   └── test_contact_actions.sql
└── integration/           # pytest tests
    └── test_contact_integration.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pgTAP extension not found` | `CREATE EXTENSION IF NOT EXISTS pgtap;` |
| `Table does not exist` | Run database migrations first |
| `Permission denied` | Grant schema permissions |
| Tests fail | Check entity definition syntax |
| Wrong test count | Verify entity has actions/fields |

## Links

- [Full Test Generation Guide](../02_guides/TEST_GENERATION.md)
- [Test Reverse Engineering Guide](../02_guides/TEST_REVERSE_ENGINEERING.md)
- [Working Examples](../06_examples/simple_contact/generated_tests/)
- [CI/CD Integration Guide](../02_guides/CI_CD_INTEGRATION.md)

---

**SpecQL Test Generation**: From entity YAML to comprehensive test suites in seconds.