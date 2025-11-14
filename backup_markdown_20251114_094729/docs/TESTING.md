# Testing Guide

## Running Tests

### Quick Start
```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest tests/unit/core/test_parser.py -v
```

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests (~80% of suite)
│   ├── core/          # Parser tests
│   ├── generators/    # Generator tests
│   ├── cli/           # CLI tests
│   └── registry/      # Registry tests
├── integration/       # Slower, integration tests (~20% of suite)
│   ├── test_e2e_generation.py
│   └── test_database_integration.py
└── conftest.py        # Shared fixtures
```

### Test Categories

Run specific test categories using markers:

```bash
# Unit tests only (fast)
pytest -m unit -v

# Integration tests (slower, may need database)
pytest -m integration -v

# Parser-specific tests
pytest -m parser -v
```

### Writing Tests

Follow the project's TDD methodology:

1. **RED**: Write failing test
2. **GREEN**: Minimal implementation to pass
3. **REFACTOR**: Clean up code
4. **QA**: Verify quality

Example:
```python
import pytest

@pytest.mark.unit
@pytest.mark.parser
def test_parse_entity_with_email_field():
    """
    Given: YAML with entity containing email field
    When: Parsing the entity
    Then: AST contains email field with correct type
    """
    yaml_content = """
    entity: Contact
    fields:
      email: text
    """
    parser = SpecQLParser()
    result = parser.parse(yaml_content)

    assert result.fields[0].name == "email"
    assert result.fields[0].type == "text"
```

### Continuous Integration

All tests run automatically on:
- Every push to `main`
- Every pull request
- Nightly builds

View test results: [GitHub Actions](https://github.com/fraiseql/specql/actions)

### Test Coverage

We maintain >95% test coverage. View detailed coverage:

```bash
# Generate HTML coverage report
make coverage

# Open in browser
open htmlcov/index.html
```

### Troubleshooting

**Tests fail on import:**
```bash
# Ensure all dependencies installed
uv sync

# Ensure package installed in development mode
uv pip install -e .
```

**Slow test runs:**
```bash
# Show 10 slowest tests
pytest --durations=10

# Run only fast unit tests
pytest -m unit
```

**Flaky tests:**
```bash
# Run test 10 times to identify flakiness
pytest tests/unit/test_example.py --count=10
```