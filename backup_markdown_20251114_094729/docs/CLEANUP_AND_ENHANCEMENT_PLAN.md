# Test Suite Cleanup & Enhancement Implementation Plan

**Project**: SpecQL Code Generator
**Current Status**: 845/882 tests passing (95.8%)
**Goal**: 100% passing tests with cleanup of deprecated features
**Estimated Time**: 4-6 hours
**Priority**: MEDIUM (post-production enhancement)

---

## Executive Summary

This plan addresses the 37 skipped tests by:
1. **Implementing safe_slug feature** (8 tests) - 1.5-2 hours
2. **Unifying PostgreSQL database setup** (24 tests) - 2-3 hours
3. **Removing backward compatibility tests** (5 tests) - 30 minutes

**Result**: ~100% test pass rate (up to 874/882 tests passing)

---

## Phase 1: Implement Safe Slug Feature

**Priority**: MEDIUM
**Estimated Time**: 1.5-2 hours
**Tests to Fix**: 8 tests in `tests/unit/schema/test_safe_slug.py`
**Files to Create/Modify**: 2 files

### Problem Description

The `safe_slug` feature generates URL-safe identifiers from arbitrary text input. It's used for creating clean, consistent identifiers from user input.

**Use Cases**:
- Entity names: "My Company" → "my_company"
- Field names: "First Name" → "first_name"
- Identifiers: "ACME Corp (NYC)" → "acme_corp_nyc"

**Tests Expecting**:
```python
# tests/unit/schema/test_safe_slug.py
def test_normal_text():
    assert safe_slug("Hello World") == "hello_world"

def test_unicode_unaccent():
    assert safe_slug("Café résumé") == "cafe_resume"

def test_special_characters():
    assert safe_slug("Hello@World!#$") == "hello_world"

def test_empty_string():
    assert safe_slug("", fallback="default") == "default"
```

### Implementation Steps

#### Step 1.1: Create safe_slug Module (30 minutes)

**File**: `src/utils/safe_slug.py` (create new file)

```python
"""
Safe Slug Generator
Converts arbitrary text to URL-safe identifiers
"""

import re
import unicodedata
from typing import Optional


def safe_slug(
    text: Optional[str],
    separator: str = "_",
    fallback: str = "untitled",
    max_length: Optional[int] = None,
) -> str:
    """
    Convert text to a safe slug (URL-safe identifier)

    Args:
        text: Input text to convert
        separator: Character to use as word separator (default: "_")
        fallback: Text to use if result is empty (default: "untitled")
        max_length: Maximum length of result (default: None = unlimited)

    Returns:
        Safe slug string

    Examples:
        >>> safe_slug("Hello World")
        'hello_world'
        >>> safe_slug("Café résumé")
        'cafe_resume'
        >>> safe_slug("Special!@#$Characters")
        'special_characters'
        >>> safe_slug("", fallback="default")
        'default'
        >>> safe_slug("123 Numbers", fallback="n")
        'n_123_numbers'
    """
    # Handle None or empty string
    if not text or not text.strip():
        return fallback

    # Convert to string (in case it's not)
    text = str(text)

    # Normalize Unicode characters (NFD = decompose accents)
    # Example: "é" → "e" + accent mark
    text = unicodedata.normalize('NFD', text)

    # Remove accent marks (category Mn = Mark, nonspacing)
    # This converts "é" → "e", "ñ" → "n", etc.
    text = ''.join(
        char for char in text
        if unicodedata.category(char) != 'Mn'
    )

    # Convert to lowercase
    text = text.lower()

    # Replace sequences of non-alphanumeric characters with separator
    # Pattern: \W+ matches one or more non-word characters
    text = re.sub(r'\W+', separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Handle case where result is empty or starts with digit
    if not text or text[0].isdigit():
        # Prefix with fallback if starts with digit
        if text and text[0].isdigit():
            text = f"{fallback}{separator}{text}"
        else:
            text = fallback

    # Truncate to max_length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip(separator)

    return text


def safe_identifier(text: Optional[str], fallback: str = "field") -> str:
    """
    Create a safe Python/PostgreSQL identifier from text

    Wrapper around safe_slug with identifier-specific defaults.
    Ensures result is a valid Python/PostgreSQL identifier.

    Args:
        text: Input text
        fallback: Fallback if text is empty (default: "field")

    Returns:
        Valid identifier string

    Examples:
        >>> safe_identifier("First Name")
        'first_name'
        >>> safe_identifier("123-ID")
        'field_123_id'
    """
    slug = safe_slug(text, separator="_", fallback=fallback)

    # Ensure it doesn't start with a number (invalid identifier)
    if slug[0].isdigit():
        slug = f"{fallback}_{slug}"

    return slug


def safe_table_name(entity_name: str, prefix: str = "tb") -> str:
    """
    Create a safe table name from entity name

    Args:
        entity_name: Entity name (e.g., "Contact", "TaskItem")
        prefix: Table prefix (default: "tb")

    Returns:
        Table name with prefix (e.g., "tb_contact", "tb_task_item")

    Examples:
        >>> safe_table_name("Contact")
        'tb_contact'
        >>> safe_table_name("TaskItem")
        'tb_task_item'
    """
    slug = safe_slug(entity_name, fallback="entity")
    return f"{prefix}_{slug}"
```

#### Step 1.2: Update Test File (15 minutes)

**File**: `tests/unit/schema/test_safe_slug.py`

**Remove skip marker**:
```python
# OLD:
pytestmark = pytest.mark.skip(reason="safe_slug feature not yet implemented")

# NEW:
# (remove the line entirely)
```

**Update imports**:
```python
import pytest
from src.utils.safe_slug import safe_slug, safe_identifier, safe_table_name
```

#### Step 1.3: Run Tests and Fix Issues (30 minutes)

```bash
# Run safe_slug tests
uv run pytest tests/unit/schema/test_safe_slug.py -v

# Expected: 8/8 passing
```

**Common Issues to Debug**:
1. **Unicode handling**: Ensure `unicodedata.normalize()` works correctly
2. **Edge cases**: Empty strings, all special characters, all digits
3. **Separator handling**: Multiple consecutive separators should become one

**Fix any test failures** by adjusting the implementation.

#### Step 1.4: Add Additional Tests (15 minutes)

**Enhance test coverage** in `tests/unit/schema/test_safe_slug.py`:

```python
def test_consecutive_separators():
    """Test: Multiple spaces/special chars become single separator"""
    assert safe_slug("Hello    World!!!") == "hello_world"

def test_mixed_case():
    """Test: Mixed case converts to lowercase"""
    assert safe_slug("CamelCaseText") == "camelcasetext"

def test_max_length():
    """Test: Truncation to max_length"""
    assert safe_slug("very_long_text_here", max_length=10) == "very_long"

def test_custom_separator():
    """Test: Custom separator character"""
    assert safe_slug("Hello World", separator="-") == "hello-world"

def test_safe_identifier_function():
    """Test: safe_identifier ensures valid Python identifier"""
    assert safe_identifier("123-field") == "field_123_field"

def test_safe_table_name_function():
    """Test: safe_table_name adds prefix"""
    assert safe_table_name("Contact") == "tb_contact"
```

#### Step 1.5: Integration with Schema Generator (15 minutes)

**Optional Enhancement**: Use safe_slug in schema generation

**File**: `src/generators/table_generator.py`

```python
from src.utils.safe_slug import safe_slug, safe_table_name

# In table name generation:
# OLD:
table_name = f"tb_{entity.name.lower()}"

# NEW:
table_name = safe_table_name(entity.name)
```

**Benefits**:
- Handles entity names with special characters
- More robust identifier generation
- Consistent naming across codebase

### Success Criteria

- ✅ `src/utils/safe_slug.py` created with full implementation
- ✅ All 8 tests in `test_safe_slug.py` passing
- ✅ Additional edge case tests added
- ✅ No regressions in schema generation tests

**Verification**:
```bash
uv run pytest tests/unit/schema/test_safe_slug.py -v
# Expected: 8/8 passing (or more with additional tests)

uv run pytest tests/unit/schema/ -v
# Expected: All schema tests still passing
```

---

## Phase 2: Unify PostgreSQL Database Setup

**Priority**: HIGH (for CI/CD)
**Estimated Time**: 2-3 hours
**Tests to Fix**: 24 tests requiring PostgreSQL
**Files to Modify**: 4-5 files

### Problem Description

Currently there are **two separate PostgreSQL database setups**:

1. **Working database**: `specql_test` (3 tests passing)
   - User: Current user (peer authentication)
   - Database: `specql_test`
   - Tests: `tests/pytest/test_contact_integration.py`
   - Status: ✅ Working

2. **Skipped database**: `test_specql` (24 tests skipped)
   - User: `postgres` with password
   - Database: `test_specql`
   - Tests: Various integration tests
   - Status: ⚠️ Skipped

**Goal**: Unify into a single database setup so all tests can run.

### Implementation Steps

#### Step 2.1: Decide on Database Configuration (15 minutes)

**Recommendation**: Use flexible configuration that works for both local and CI/CD

**Configuration Strategy**:
```python
# Database settings (from environment or defaults)
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("TEST_DB_PORT", "5432")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "specql_test")
TEST_DB_USER = os.getenv("TEST_DB_USER", os.getenv("USER"))
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "")
```

**Benefits**:
- Local: Use peer authentication (no password needed)
- CI/CD: Set environment variables for postgres user
- Flexible: Works in both environments

#### Step 2.2: Create Unified Database Fixture (45 minutes)

**File**: `tests/conftest.py` (update existing or create new)

```python
"""
Global pytest fixtures for all tests
"""

import os
import pytest
import psycopg
from pathlib import Path


def get_db_config():
    """Get database configuration from environment or defaults"""
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": int(os.getenv("TEST_DB_PORT", "5432")),
        "dbname": os.getenv("TEST_DB_NAME", "specql_test"),
        "user": os.getenv("TEST_DB_USER", os.getenv("USER")),
        "password": os.getenv("TEST_DB_PASSWORD", ""),
    }


@pytest.fixture(scope="session")
def db_config():
    """Database configuration"""
    return get_db_config()


@pytest.fixture(scope="session")
def test_db_connection(db_config):
    """
    Session-scoped PostgreSQL connection for integration tests

    Environment variables (optional):
    - TEST_DB_HOST: Database host (default: localhost)
    - TEST_DB_PORT: Database port (default: 5432)
    - TEST_DB_NAME: Database name (default: specql_test)
    - TEST_DB_USER: Database user (default: current user)
    - TEST_DB_PASSWORD: Database password (default: empty)

    To skip database tests:
        pytest -m "not database"
    """
    try:
        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]

        if db_config['password']:
            conn_parts.append(f"password={db_config['password']}")

        conn_string = " ".join(conn_parts)

        # Connect with autocommit=False for transaction control
        conn = psycopg.connect(conn_string, autocommit=False)

        # Verify connection
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\n✅ Database connected: {version[:70]}...")

        # Install extensions if needed
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            conn.commit()
            print("✅ PostgreSQL extensions installed (pg_trgm, postgis)")
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Could not install extensions: {e}")
            print("   (Some tests may be skipped)")

        yield conn

        # Cleanup
        conn.close()

    except psycopg.OperationalError as e:
        pytest.skip(
            f"PostgreSQL database not available: {e}\n\n"
            f"To run database tests:\n"
            f"  1. Create database: createdb {db_config['dbname']}\n"
            f"  2. Load schema: psql {db_config['dbname']} < tests/schema/setup.sql\n"
            f"  3. Or set ENABLE_DB_TESTS=0 to skip\n\n"
            f"Connection attempted:\n"
            f"  Host: {db_config['host']}\n"
            f"  Database: {db_config['dbname']}\n"
            f"  User: {db_config['user']}\n"
        )


@pytest.fixture
def test_db(test_db_connection):
    """
    Function-scoped database fixture with transaction rollback

    Each test gets a fresh transaction that's rolled back after the test.
    This ensures test isolation without needing to delete data.
    """
    # Start a transaction
    test_db_connection.rollback()  # Ensure clean state

    yield test_db_connection

    # Rollback transaction to clean up
    test_db_connection.rollback()
```

#### Step 2.3: Update All Database Test Files (1 hour)

**Files to Update**:
1. `tests/integration/schema/test_rich_types_postgres.py`
2. `tests/integration/fraiseql/test_rich_type_autodiscovery.py`
3. `tests/integration/fraiseql/test_mutation_annotations_e2e.py`
4. `tests/integration/test_composite_hierarchical_e2e.py`
5. `tests/pytest/test_contact_integration.py`

**Changes for Each File**:

**1. Remove local fixture, use global one**:

```python
# OLD (in each file):
@pytest.fixture
def test_db():
    """PostgreSQL test database connection"""
    try:
        conn = psycopg.connect(
            host="localhost",
            dbname="test_specql",  # ← Hardcoded
            user="postgres",       # ← Hardcoded
            password="postgres"    # ← Hardcoded
        )
        yield conn
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL not available")

# NEW (remove fixture, use global one from conftest.py):
# (no local fixture needed - will use the one from conftest.py)
```

**2. Update test signatures**:

```python
# OLD:
def test_email_constraint_validates_format(test_db):
    # test_db is local fixture
    ...

# NEW:
def test_email_constraint_validates_format(test_db):
    # test_db is global fixture from conftest.py
    # No changes needed to signature - pytest will inject it
    ...
```

**3. Handle extension requirements**:

```python
# For tests requiring pg_trgm or postgis:
def test_url_pattern_matching_with_gin_index(test_db):
    """Test: URL pattern matching with GIN index"""
    try:
        # This test requires pg_trgm extension
        with test_db.cursor() as cur:
            # Test code...
    except psycopg.errors.UndefinedObject as e:
        if "pg_trgm" in str(e):
            pytest.skip("Test requires pg_trgm extension")
        raise
```

**Example: Update test_rich_types_postgres.py**:

```python
"""
PostgreSQL Integration Tests for Rich Types
Tests that generated SQL actually works in PostgreSQL database
"""

import pytest
import psycopg
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition

# Mark all tests as requiring database
pytestmark = pytest.mark.database


def create_contact_entity_with_email():
    """Helper: Create test entity with email field"""
    return Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
        },
    )


def test_email_constraint_validates_format(test_db, schema_registry):
    """Test: Email CHECK constraint validates format in PostgreSQL"""
    # Create entity and generate DDL
    entity = create_contact_entity_with_email()
    generator = TableGenerator(schema_registry)
    ddl = generator.generate_table_ddl(entity)

    # Create table in database
    with test_db.cursor() as cur:
        # Clean up if exists
        cur.execute("DROP TABLE IF EXISTS crm.tb_contact CASCADE")
        cur.execute("DROP SCHEMA IF EXISTS crm CASCADE")
        cur.execute("CREATE SCHEMA crm")

        # Execute DDL
        cur.execute(ddl)

        # Test valid email - should succeed
        cur.execute(
            "INSERT INTO crm.tb_contact (id, name, email) VALUES (%s, %s, %s)",
            ("550e8400-e29b-41d4-a716-446655440000", "John Doe", "john@example.com")
        )

        # Test invalid email - should fail
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO crm.tb_contact (id, name, email) VALUES (%s, %s, %s)",
                ("550e8400-e29b-41d4-a716-446655440001", "Jane Doe", "not-an-email")
            )

    test_db.rollback()  # Clean up


def test_url_pattern_matching_with_gin_index(test_db, schema_registry):
    """Test: URL pattern matching with GIN index (requires pg_trgm)"""
    try:
        entity = create_contact_entity_with_url()
        generator = TableGenerator(schema_registry)
        ddl = generator.generate_table_ddl(entity)

        with test_db.cursor() as cur:
            # Setup
            cur.execute("DROP TABLE IF EXISTS crm.tb_contact CASCADE")
            cur.execute("DROP SCHEMA IF EXISTS crm CASCADE")
            cur.execute("CREATE SCHEMA crm")
            cur.execute(ddl)

            # Test GIN index works
            cur.execute(
                "SELECT * FROM pg_indexes WHERE tablename = 'tb_contact' AND indexdef LIKE '%gin%'"
            )
            indexes = cur.fetchall()
            assert len(indexes) > 0, "GIN index not created"

    except psycopg.errors.UndefinedObject as e:
        if "pg_trgm" in str(e):
            pytest.skip("Test requires pg_trgm extension - install with: CREATE EXTENSION pg_trgm;")
        raise

    test_db.rollback()
```

#### Step 2.4: Create Database Setup Script (30 minutes)

**File**: `tests/schema/setup.sql` (create new)

```sql
-- ============================================================================
-- Test Database Setup Script
-- Run this to initialize the test database with required schemas and types
-- ============================================================================

-- Drop existing schemas (clean slate)
DROP SCHEMA IF EXISTS app CASCADE;
DROP SCHEMA IF EXISTS crm CASCADE;
DROP SCHEMA IF EXISTS common CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;
DROP SCHEMA IF EXISTS pm CASCADE;
DROP SCHEMA IF EXISTS catalog CASCADE;

-- Create schemas
CREATE SCHEMA app;
CREATE SCHEMA crm;
CREATE SCHEMA common;
CREATE SCHEMA core;
CREATE SCHEMA pm;
CREATE SCHEMA catalog;

-- Install extensions (optional - skip if not available)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create app.mutation_result type
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    _meta JSONB
);

COMMENT ON TYPE app.mutation_result IS
'Standard return type for all mutations.

@fraiseql:type
name: MutationResult
description: Result of a mutation operation';

-- Create input types (will be generated by tests as needed)
-- These are just placeholders for tests that need them

-- Create Company table (for FK testing)
CREATE TABLE crm.tb_company (
    pk_company INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    identifier TEXT,
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMP DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_company_tenant ON crm.tb_company(tenant_id);

-- Trinity helper functions
CREATE OR REPLACE FUNCTION crm.company_pk(company_identifier TEXT, p_tenant_id UUID)
RETURNS INTEGER AS $$
    SELECT pk_company
    FROM crm.tb_company
    WHERE identifier = company_identifier
      AND tenant_id = p_tenant_id
      AND deleted_at IS NULL;
$$ LANGUAGE SQL STABLE;

-- Audit logging function
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    auth_tenant_id UUID,
    auth_user_id UUID,
    entity_name TEXT,
    entity_id UUID,
    operation TEXT,
    status TEXT,
    updated_fields TEXT[],
    message TEXT,
    object_data JSONB,
    extra JSONB,
    error_details JSONB DEFAULT NULL
) RETURNS app.mutation_result AS $$
DECLARE
    result app.mutation_result;
BEGIN
    -- Build result
    result.id := entity_id;
    result.updated_fields := updated_fields;
    result.status := status;
    result.message := message;
    result.object_data := object_data;
    result._meta := COALESCE(extra, '{}'::JSONB);

    -- In production, this would log to audit table
    -- For tests, just return the result

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (if using postgres user)
GRANT ALL ON SCHEMA app TO PUBLIC;
GRANT ALL ON SCHEMA crm TO PUBLIC;
GRANT ALL ON SCHEMA common TO PUBLIC;
GRANT ALL ON SCHEMA core TO PUBLIC;
GRANT ALL ON SCHEMA pm TO PUBLIC;
GRANT ALL ON SCHEMA catalog TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA app TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA crm TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA crm TO PUBLIC;
```

**Load script**:
```bash
# Create database if needed
createdb specql_test

# Load setup script
psql specql_test < tests/schema/setup.sql

# Verify
psql specql_test -c "\dn"  # List schemas
psql specql_test -c "\dT app.*"  # List types
```

#### Step 2.5: Update pytest.ini / pyproject.toml (15 minutes)

**File**: `pyproject.toml`

**Add database marker**:
```toml
[tool.pytest.ini_options]
markers = [
    "database: marks tests as requiring PostgreSQL database (deselect with '-m \"not database\"')",
    "slow: marks tests as slow running",
]
```

**Mark tests requiring database**:

```python
# In each database test file, add at top:
pytestmark = pytest.mark.database
```

#### Step 2.6: Update README with Database Setup (15 minutes)

**File**: `README.md`

**Add section**:
```markdown
## Running Tests

### Full Test Suite

```bash
# Run all tests (including database tests)
uv run pytest

# Run without database tests
uv run pytest -m "not database"
```

### Database Tests

Database integration tests require PostgreSQL:

```bash
# 1. Create test database
createdb specql_test

# 2. Load schema
psql specql_test < tests/schema/setup.sql

# 3. Run database tests
uv run pytest -m database -v
```

**Environment Variables**:

```bash
# Optional: Configure database connection
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5432
export TEST_DB_NAME=specql_test
export TEST_DB_USER=$USER
export TEST_DB_PASSWORD=

# Run tests
uv run pytest
```

**CI/CD Setup**:

```yaml
# GitHub Actions example
- name: Setup PostgreSQL
  run: |
    sudo apt-get install postgresql postgresql-contrib
    sudo -u postgres createdb specql_test
    sudo -u postgres psql specql_test < tests/schema/setup.sql

- name: Run Tests
  env:
    TEST_DB_HOST: localhost
    TEST_DB_NAME: specql_test
    TEST_DB_USER: postgres
    TEST_DB_PASSWORD: postgres
  run: uv run pytest
```
```

#### Step 2.7: Test the Changes (30 minutes)

```bash
# 1. Create/verify database
createdb specql_test
psql specql_test < tests/schema/setup.sql

# 2. Run previously skipped tests
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v

# 3. Run all database tests
uv run pytest -m database -v

# 4. Verify no regressions
uv run pytest

# 5. Test skip behavior (without database)
dropdb specql_test
uv run pytest -m database -v
# Should skip gracefully with helpful message
```

### Success Criteria

- ✅ Single unified database fixture (`test_db_connection` in `conftest.py`)
- ✅ All 24 PostgreSQL tests running (not skipped)
- ✅ Tests pass when database is available
- ✅ Tests skip gracefully when database is not available
- ✅ No regressions in existing tests
- ✅ Documentation updated

**Expected Result**:
```bash
uv run pytest -v

# With database:
======================= 869 passed, 13 skipped in ~35s =======================
# (13 skipped = safe_slug deprecated tests + under-development features)

# Without database:
======================= 845 passed, 37 skipped in ~30s =======================
# (37 skipped = 24 database + 13 other)
```

---

## Phase 3: Remove Backward Compatibility Tests

**Priority**: LOW (cleanup)
**Estimated Time**: 30 minutes
**Tests to Remove**: 5 tests
**Files to Modify/Delete**: 3 files

### Problem Description

These tests verify deprecated features that are no longer relevant:
- Underscore separator for hierarchical identifiers (old format)
- Strip tenant prefix feature (not implemented)

**Tests to Remove**:
1. `tests/integration/test_backward_compatibility.py` (2 tests)
2. `tests/unit/actions/test_identifier_hierarchical_dot.py` (2 tests)
3. `tests/unit/actions/test_strip_tenant_prefix.py` (2 tests)

### Implementation Steps

#### Step 3.1: Review Tests Before Removal (10 minutes)

**Verify these are truly deprecated**:

```bash
# Check if code references these features
grep -r "underscore.*separator" src/
grep -r "strip_tenant_prefix" src/
grep -r "hierarchical.*dot" src/

# If no references found in src/, safe to remove tests
```

#### Step 3.2: Remove Test Files (5 minutes)

```bash
# Remove deprecated test files
rm tests/integration/test_backward_compatibility.py
rm tests/unit/actions/test_identifier_hierarchical_dot.py
rm tests/unit/actions/test_strip_tenant_prefix.py

# Or move to archive (safer option)
mkdir -p tests/archived/
git mv tests/integration/test_backward_compatibility.py tests/archived/
git mv tests/unit/actions/test_identifier_hierarchical_dot.py tests/archived/
git mv tests/unit/actions/test_strip_tenant_prefix.py tests/archived/
```

#### Step 3.3: Update Documentation (10 minutes)

**File**: `docs/DEPRECATED_FEATURES.md` (create new)

```markdown
# Deprecated Features

This document tracks features that have been deprecated and removed.

## Hierarchical Identifier Underscore Separator

**Deprecated**: 2024-Q4
**Removed**: 2025-11-09
**Reason**: Dot separator is more readable and standard

**Old Format**:
```
tenant_ACME_location_NYC
```

**New Format**:
```
tenant.ACME.location.NYC
```

**Migration**: No migration needed - new entities use dot separator by default.

## Strip Tenant Prefix

**Status**: Never implemented
**Removed**: 2025-11-09
**Reason**: Feature was planned but never needed

**Original Idea**: Strip redundant tenant prefixes from composite identifiers
**Decision**: Not needed - identifiers work fine with tenant prefix

## Test Files Archived

The following test files have been moved to `tests/archived/`:
- `test_backward_compatibility.py` - Underscore separator tests
- `test_identifier_hierarchical_dot.py` - Hierarchical dot separator tests
- `test_strip_tenant_prefix.py` - Strip tenant prefix tests

These can be permanently deleted after 6 months (2025-05-09).
```

#### Step 3.4: Verify No Regressions (5 minutes)

```bash
# Run full test suite
uv run pytest

# Should see:
# - 5 fewer tests (removed tests)
# - All remaining tests passing
# - No import errors or missing fixtures

# Verify count
uv run pytest --collect-only -q | tail -1
# Should show ~877 tests (882 - 5 deprecated = 877)
```

### Success Criteria

- ✅ 5 deprecated test files removed or archived
- ✅ Documentation updated explaining what was removed
- ✅ No regressions in remaining tests
- ✅ No broken imports or references

**Expected Result**:
```bash
# After Phase 1 (safe_slug) + Phase 2 (database) + Phase 3 (cleanup):
uv run pytest -v

======================= 869 passed, 8 skipped in ~35s =======================
# 869 passed = 845 (original) + 8 (safe_slug) + 24 (database) - 5 (removed) - 3 (truly deprecated)
# 8 skipped = features legitimately under development
```

---

## Complete Execution Order

### Recommended Order

1. **Phase 3: Remove Backward Compatibility** (30 min) - Easiest, reduces noise
2. **Phase 1: Implement Safe Slug** (1.5-2 hours) - Independent feature
3. **Phase 2: Unify Database Setup** (2-3 hours) - Most complex, highest value

**Total Time**: 4-6 hours
**Result**: ~99% test pass rate (869/877 tests)

### Alternative Order (If Time Constrained)

**Just do Phase 1 and 3**:
- Phase 3: Remove deprecated tests (30 min)
- Phase 1: Implement safe_slug (2 hours)
- Skip Phase 2 (database unification) for now

**Result**: 853/877 tests passing (97.3%)
- Still excellent for production
- Database tests remain optional

---

## Testing Strategy

### After Each Phase

```bash
# Phase 1: Safe slug
uv run pytest tests/unit/schema/test_safe_slug.py -v
uv run pytest tests/unit/schema/ -v  # Verify no regressions

# Phase 2: Database unification
createdb specql_test
psql specql_test < tests/schema/setup.sql
uv run pytest -m database -v
uv run pytest  # Full suite

# Phase 3: Cleanup
uv run pytest  # Verify no import errors
```

### Final Verification

```bash
# Full test suite with database
createdb specql_test
psql specql_test < tests/schema/setup.sql
uv run pytest -v

# Expected: 869 passed, 8 skipped

# Without database (for CI without PostgreSQL)
uv run pytest -m "not database" -v

# Expected: 845 passed, 32 skipped
```

---

## CI/CD Integration

### GitHub Actions Example

**File**: `.github/workflows/test.yml` (create if doesn't exist)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: specql_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Setup PostgreSQL
        env:
          PGPASSWORD: postgres
        run: |
          psql -h localhost -U postgres -d specql_test < tests/schema/setup.sql

      - name: Run tests
        env:
          TEST_DB_HOST: localhost
          TEST_DB_NAME: specql_test
          TEST_DB_USER: postgres
          TEST_DB_PASSWORD: postgres
        run: uv run pytest -v

      - name: Upload coverage
        if: success()
        run: |
          uv run pytest --cov=src --cov-report=xml
          # Upload to codecov or similar
```

---

## Rollback Plan

If any phase causes issues:

### Phase 1 Rollback (Safe Slug)

```bash
# Remove implementation
rm src/utils/safe_slug.py

# Re-skip tests
# Add back to test_safe_slug.py:
pytestmark = pytest.mark.skip(reason="safe_slug feature not yet implemented")
```

### Phase 2 Rollback (Database)

```bash
# Revert conftest.py changes
git checkout HEAD -- tests/conftest.py

# Restore local fixtures in test files
git checkout HEAD -- tests/integration/schema/test_rich_types_postgres.py
# (repeat for other files)
```

### Phase 3 Rollback (Cleanup)

```bash
# Restore archived tests
git checkout HEAD -- tests/integration/test_backward_compatibility.py
git checkout HEAD -- tests/unit/actions/test_identifier_hierarchical_dot.py
git checkout HEAD -- tests/unit/actions/test_strip_tenant_prefix.py
```

---

## Success Metrics

### Minimum Success (Phases 1 + 3 only)

- ✅ 853/877 tests passing (97.3%)
- ✅ Safe slug implemented
- ✅ Deprecated tests removed
- ✅ 24 database tests remain skipped (acceptable)

### Full Success (All Phases)

- ✅ 869/877 tests passing (99.1%)
- ✅ Safe slug implemented and tested
- ✅ Database tests unified and running
- ✅ Deprecated tests removed
- ✅ CI/CD integration documented
- ✅ Only 8 tests skipped (legitimately under development)

---

## Documentation Updates

After completion, update:

1. **README.md**: Database setup instructions
2. **GETTING_STARTED.md**: Test running instructions
3. **CLAUDE.md**: Update test status to ~99% passing
4. **DEPRECATED_FEATURES.md**: Document removed features
5. **docs/SKIPPED_TESTS_SUMMARY.md**: Update with new skip count

---

## Timeline

### Fast Track (4 hours)

- Phase 3 (cleanup): 30 min
- Phase 1 (safe_slug): 1.5 hours
- Phase 2 (database): 2 hours

### Thorough Track (6 hours)

- Phase 3 (cleanup): 30 min
- Phase 1 (safe_slug): 2 hours
- Phase 2 (database): 3 hours
- Documentation: 30 min

---

## Conclusion

This plan will bring the test suite to **~99% pass rate** (869/877 tests) by:

1. ✅ Implementing the safe_slug utility feature (8 tests)
2. ✅ Unifying PostgreSQL database setup (24 tests)
3. ✅ Removing deprecated backward compatibility tests (-5 tests)

**Final Result**: Production-ready test suite with comprehensive coverage and minimal skipped tests.

**Recommendation**: Execute all three phases for maximum test coverage and clean codebase.
