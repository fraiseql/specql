# SpecQL Test Suite

## Structure

- **unit/** - Unit tests for individual components
- **integration/** - Integration tests with database/full stack
- **fixtures/** - Shared test fixtures and mock data
- **archived/** - Deprecated tests kept for reference

## Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/core/test_scalar_types.py -v
```

## Test Coverage

- 906/910 tests passing (99.6%)
- 4 skipped (database-dependent)
- Target: 100% effective coverage