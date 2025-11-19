# Database Testing Guide

## Overview

SpecQL has **17 integration tests** that require a live PostgreSQL database to validate:
- Generated SQL execution
- Database roundtrip operations
- Trinity pattern resolution
- FraiseQL metadata queries
- Transaction handling

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start test database
make db-up

# Run all tests including database tests
make test-all

# Stop database when done
make db-down
```

**Database Details:**
- Container: `specql_test_db`
- Port: `5433` (avoids conflict with local PostgreSQL)
- Database: `test_specql`
- User: `postgres`
- Password: `postgres`

### Option 2: Manual Docker

```bash
# Start database
docker-compose -f docker-compose.test.yml up -d

# Run tests with environment variables
TEST_DB_HOST=localhost \
TEST_DB_PORT=5433 \
TEST_DB_NAME=test_specql \
TEST_DB_USER=postgres \
TEST_DB_PASSWORD=postgres \
uv run pytest tests/

# Stop database
docker-compose -f docker-compose.test.yml down
```

### Option 3: Local PostgreSQL

If you prefer using your local PostgreSQL installation:

```bash
# Create test database
createdb specql_test

# Run tests
TEST_DB_HOST=localhost \
TEST_DB_PORT=5432 \
TEST_DB_NAME=specql_test \
uv run pytest tests/
```

## Database Management Commands

```bash
make db-status     # Check if database is running
make db-up         # Start database
make db-down       # Stop and remove database
make db-restart    # Restart database
make db-logs       # View database logs
```

## Running Tests

### Without Database (Fast)
```bash
make test          # Unit tests only (skips 17 database tests)
```

### With Database (Complete)
```bash
make test-all      # All tests including database integration
```

### Specific Database Tests
```bash
# Database roundtrip tests
uv run pytest tests/integration/actions/test_database_roundtrip.py -v

# Metadata query tests
uv run pytest tests/integration/testing/test_metadata_query_api.py -v

# Confiture integration tests
uv run pytest tests/integration/test_confiture_integration.py -v
```

## Skipped Tests Behavior

When PostgreSQL is **not available**, these tests are automatically skipped:

- `tests/integration/actions/test_database_roundtrip.py` (6 tests)
- `tests/integration/testing/test_metadata_query_api.py` (7 tests)
- `tests/integration/test_confiture_integration.py` (2 tests)
- `tests/pytest/conftest.py` fixtures (2 tests)

**Total: 17 skipped tests**

The test suite detects database availability via `tests/conftest.py:test_db_connection` fixture and gracefully skips tests with clear messages.

## CI/CD Integration

For GitHub Actions or other CI systems, use Docker:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: test_specql
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - 5433:5432

steps:
  - name: Run all tests
    env:
      TEST_DB_HOST: localhost
      TEST_DB_PORT: 5433
      TEST_DB_NAME: test_specql
      TEST_DB_USER: postgres
      TEST_DB_PASSWORD: postgres
    run: uv run pytest tests/ -v
```

## Troubleshooting

### Database won't start
```bash
# Check if port 5433 is already in use
lsof -i :5433

# Or use different port in docker-compose.test.yml
```

### Connection refused errors
```bash
# Verify database is running
make db-status

# Check logs for errors
make db-logs

# Restart database
make db-restart
```

### Tests still skipping
```bash
# Verify environment variables are set
echo $TEST_DB_PORT  # Should be 5433

# Test connection manually
psql -h localhost -p 5433 -U postgres -d test_specql
```

## Test Isolation Strategy

**Transaction Rollback** (`test_db` fixture):
- Each test runs in a transaction
- Automatically rolled back after test
- Fast, no cleanup needed
- Used for data manipulation tests

**Isolated Schemas** (`isolated_schema` fixture):
- Creates unique schema per test (e.g., `test_a3f2b1c8`)
- For DDL operations that can't be rolled back
- Automatically dropped after test
- Used for schema generation tests

## Architecture

```
tests/conftest.py
├── test_db_connection (session-scoped)
│   └── Creates single connection for all tests
├── test_db (function-scoped)
│   └── Transaction per test, auto-rollback
└── isolated_schema (function-scoped)
    └── Unique schema per test, auto-cleanup
```

## Performance

- **Unit tests only**: ~2-5 seconds (1488 tests)
- **With database tests**: ~6-10 seconds (1505 tests)
- **Database startup**: ~3-5 seconds (one-time)

## Best Practices

1. **Local development**: Keep database running with `make db-up`
2. **CI/CD**: Always use Docker for consistency
3. **Fast iteration**: Use `make test` (skips DB) for quick feedback
4. **Before commit**: Run `make test-all` to ensure full coverage
5. **Cleanup**: Use `make db-down` to free resources when done
