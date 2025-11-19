# Week 1: Database Integration
**Duration**: 5 days | **Tests**: 8 | **Priority**: 🔴 HIGH

## 🎯 What You'll Build

By the end of this week, you'll have:
- ✅ Docker setup for PostgreSQL test database
- ✅ 6 database roundtrip tests passing (CREATE, UPDATE, validation)
- ✅ 2 Confiture integration tests passing (migrations)
- ✅ CI/CD pipeline configured for database tests

**Why this matters**: Database tests prove our generated SQL actually works in PostgreSQL!

---

## 📋 Tests to Unskip

### File 1: `tests/integration/actions/test_database_roundtrip.py` (6 tests)

These tests generate SQL and run it in PostgreSQL:

1. `test_create_contact_action_database_execution` - Test INSERT works
2. `test_validation_error_database_execution` - Test validation fails correctly
3. `test_trinity_resolution_database_execution` - Test UUID → INTEGER conversion
4. `test_update_action_database_execution` - Test UPDATE works
5. `test_soft_delete_database_execution` - Test soft delete (deleted_at)
6. `test_custom_action_database_execution` - Test custom action logic

### File 2: `tests/integration/test_confiture_integration.py` (2 tests)

These test integration with Confiture (our migration tool):

7. `test_confiture_migrate_up_and_down` - Test migrations work
8. `test_confiture_fallback_when_unavailable` - Test fallback if Confiture missing

---

## 📅 Day-by-Day Plan

### Day 1: Docker Setup (Infrastructure) 🐳

**Goal**: Get PostgreSQL running in Docker for tests

#### Step 1: Create Docker Compose File

Create `docker-compose.test.yml` in project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: specql_test_db
    environment:
      POSTGRES_DB: specql_test
      POSTGRES_USER: specql_test
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"  # Use 5433 to avoid conflicts
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
      - ./tests/fixtures/schema:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U specql_test"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_test_data:
```

**What this does**:
- Runs PostgreSQL 16 in Docker
- Uses port 5433 (so it doesn't conflict with your local PostgreSQL)
- Creates database `specql_test`
- Automatically runs SQL files from `tests/fixtures/schema/` on startup

#### Step 2: Create Database Initialization Script

Create `tests/fixtures/schema/00_init.sql`:

```sql
-- Initialize test database with required extensions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create base schemas
CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS core;

-- Create app.mutation_result type (required for all actions)
CREATE TYPE app.mutation_result AS (
    success BOOLEAN,
    error_code TEXT,
    error_message TEXT,
    object_data JSONB,
    _meta JSONB
);

-- Test tenant for multi-tenant tests
CREATE SCHEMA IF NOT EXISTS management;
CREATE TABLE IF NOT EXISTS management.tb_tenant (
    pk_tenant INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID DEFAULT uuid_generate_v4(),
    identifier TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Insert test tenant
INSERT INTO management.tb_tenant (identifier)
VALUES ('test-tenant')
ON CONFLICT (identifier) DO NOTHING;
```

**What this does**:
- Installs PostgreSQL extensions we need
- Creates framework schemas (common, app, core)
- Creates the `mutation_result` type (required for actions)
- Sets up test tenant for multi-tenant tests

#### Step 3: Start PostgreSQL

```bash
# Start database
docker-compose -f docker-compose.test.yml up -d

# Check it's running
docker-compose -f docker-compose.test.yml ps

# View logs
docker-compose -f docker-compose.test.yml logs postgres

# Test connection
psql -h localhost -p 5433 -U specql_test -d specql_test
# Password: test_password
```

#### Step 4: Set Environment Variables

Add to your `.envrc` (or export manually):

```bash
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433
export TEST_DB_NAME=specql_test
export TEST_DB_USER=specql_test
export TEST_DB_PASSWORD=test_password
```

Load environment:
```bash
# If using direnv
direnv allow

# Or export manually
source .envrc
```

#### Step 5: Verify Database Tests Can Connect

Run one test to verify connection:

```bash
# This will FAIL but should connect to database
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_create_contact_action_database_execution -v

# You should see database connection message in output
```

#### ✅ Day 1 Success Criteria

- [ ] Docker Compose file created
- [ ] PostgreSQL running on port 5433
- [ ] Database initialization script created
- [ ] Environment variables set
- [ ] Tests can connect to database (even if they fail)

**Deliverable**: PostgreSQL running and accessible ✅

---

### Day 2: First Database Test Passing 🟢

**Goal**: Make `test_create_contact_action_database_execution` pass

#### Step 1: Understand the Test

Read the test in `tests/integration/actions/test_database_roundtrip.py`:

```python
def test_create_contact_action_database_execution(test_db, isolated_schema):
    """
    Test that generated action SQL actually executes in PostgreSQL
    and creates records correctly
    """
    # 1. Create Contact entity
    # 2. Generate schema (tables, functions)
    # 3. Execute SQL in PostgreSQL
    # 4. Call action function
    # 5. Verify record created
```

**What it's testing**:
- Our generated DDL (CREATE TABLE) works
- Our generated PL/pgSQL function works
- The function inserts data correctly
- Trinity pattern (pk, id, identifier) works

#### Step 2: Run the Test to See What Fails

```bash
# Temporarily remove the @pytest.mark.skip decorator
cd tests/integration/actions/
# Edit test_database_roundtrip.py: comment out the skip markers

# Run test
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_create_contact_action_database_execution -v -s
```

**Expected failures** (these are normal!):
- "Table doesn't exist" → Need to run schema generation
- "Function doesn't exist" → Need to run action generation
- "Type doesn't exist" → Missing composite types

#### Step 3: Fix Schema Generation Order

The test likely fails because generated SQL isn't in the right order. Update `src/generators/schema_orchestrator.py`:

```python
def generate_complete_schema(self, entity: Entity) -> str:
    """Generate complete schema in correct order"""
    parts = []

    # 1. Create schemas FIRST
    if entity.schema not in ['common', 'app', 'core']:
        parts.append(f"CREATE SCHEMA IF NOT EXISTS {entity.schema};")

    # 2. Create composite types (if any)
    type_generator = CompositeTypeGenerator(self.schema_registry)
    composite_types = type_generator.generate_types(entity)
    if composite_types:
        parts.append(composite_types)

    # 3. Create tables
    table_generator = TableGenerator(self.schema_registry)
    table_ddl = table_generator.generate(entity)
    parts.append(table_ddl)

    # 4. Create indexes
    index_ddl = table_generator.generate_indexes(entity)
    if index_ddl:
        parts.append(index_ddl)

    # 5. Create Trinity helper functions
    trinity_generator = TrinityHelperGenerator(self.schema_registry)
    trinity_ddl = trinity_generator.generate(entity)
    parts.append(trinity_ddl)

    # 6. Create action functions
    action_generator = ActionOrchestrator(self.schema_registry)
    for action in entity.actions:
        action_ddl = action_generator.generate_action(entity, action)
        parts.append(action_ddl)

    return "\n\n".join(parts)
```

**Why this order matters**:
1. Schemas must exist before creating objects in them
2. Types must exist before tables use them
3. Tables must exist before functions reference them
4. Helper functions must exist before actions call them

#### Step 4: Fix Test Fixture (Isolated Schema)

The test uses `isolated_schema` fixture to avoid conflicts. Verify it works:

```python
# In tests/conftest.py
@pytest.fixture
def isolated_schema(test_db_connection):
    """
    Create unique schema per test for DDL isolation
    """
    import uuid
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    # Create schema
    with test_db_connection.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {schema_name}")
    test_db_connection.commit()

    yield schema_name

    # Cleanup
    try:
        with test_db_connection.cursor() as cur:
            cur.execute(f"DROP SCHEMA {schema_name} CASCADE")
        test_db_connection.commit()
    except Exception:
        test_db_connection.rollback()
```

**What this does**:
- Creates unique schema for each test (test_a1b2c3d4)
- Prevents tests from interfering with each other
- Cleans up after test finishes

#### Step 5: Update Test to Use Isolated Schema

The test needs to replace schema names in generated SQL:

```python
def test_create_contact_action_database_execution(test_db, isolated_schema):
    # Generate entity
    entity = create_simple_contact_entity()

    # Generate complete DDL
    orchestrator = SchemaOrchestrator()
    ddl = orchestrator.generate_complete_schema(entity)

    # Replace schema name with isolated schema
    ddl = ddl.replace("CREATE SCHEMA IF NOT EXISTS crm;", f"CREATE SCHEMA IF NOT EXISTS {isolated_schema};")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")

    # Execute DDL
    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Call action function
    result = execute_query(
        test_db,
        f"SELECT * FROM {isolated_schema}.create_contact($1, $2, $3)",
        TEST_TENANT_ID, TEST_USER_ID, '{"email": "test@example.com", "status": "lead"}'
    )

    # Verify success
    assert result['success'] == True
    assert result['object_data']['email'] == 'test@example.com'
```

#### Step 6: Run Test Again

```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_create_contact_action_database_execution -v
```

**Debug tips if it still fails**:

```bash
# Save generated SQL to file
python -c "
from src.generators.schema_orchestrator import SchemaOrchestrator
from tests.integration.actions.test_database_roundtrip import create_simple_contact_entity

entity = create_simple_contact_entity()
orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)
print(ddl)
" > /tmp/generated.sql

# Try running SQL manually
psql -h localhost -p 5433 -U specql_test -d specql_test < /tmp/generated.sql

# Check for errors
```

#### ✅ Day 2 Success Criteria

- [ ] First test passes: `test_create_contact_action_database_execution`
- [ ] Schema generation order fixed
- [ ] Isolated schema fixture working
- [ ] Can create records via action functions

**Deliverable**: First database test passing ✅

---

### Day 3: All Roundtrip Tests Passing 🟢

**Goal**: Make all 6 database roundtrip tests pass

#### Step 1: Remove All Skip Markers

Edit `tests/integration/actions/test_database_roundtrip.py`:

```python
# Comment out or remove this line:
# pytestmark = pytest.mark.skip(reason="Requires actual database connection")
```

#### Step 2: Fix Validation Test

Run validation test:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_validation_error_database_execution -v
```

This test verifies validation errors are returned correctly:

```python
def test_validation_error_database_execution(test_db, isolated_schema):
    """Test that validation errors are returned with correct error code"""
    # Setup: Create Contact entity with email validation
    # Execute: Call action with missing email
    # Verify: Returns success=false, error_code='missing_email'
```

**Common issue**: Error codes don't match

Fix in `src/generators/actions/step_compilers/validate_step.py`:

```python
def compile_validate_step(self, step: ActionStep) -> str:
    """Generate validation check with error return"""
    return f"""
    -- Validate: {step.expression}
    IF NOT ({step.expression}) THEN
        RETURN ROW(
            false,                           -- success
            '{step.error}',                  -- error_code (from YAML)
            'Validation failed: {step.error}',  -- error_message
            NULL::JSONB,                     -- object_data
            NULL::JSONB                      -- _meta
        )::app.mutation_result;
    END IF;
    """
```

#### Step 3: Fix Trinity Resolution Test

Run Trinity test:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_trinity_resolution_database_execution -v
```

This tests UUID → INTEGER conversion:

```python
def test_trinity_resolution_database_execution(test_db, isolated_schema):
    """
    Test Trinity resolution: accept UUID, convert to INTEGER internally

    User passes: company_id = '550e8400-e29b-41d4-a716-446655440000' (UUID)
    Action converts: fk_company = company_pk('550e...') = 123 (INTEGER)
    """
```

**Common issue**: Trinity helper functions not generated

Fix in `src/generators/trinity_helper_generator.py`:

```python
def generate(self, entity: Entity) -> str:
    """Generate Trinity helper functions"""
    schema = entity.schema
    table = f"tb_{entity.name.lower()}"

    return f"""
    -- Trinity helper: Get pk_* from id (UUID)
    CREATE OR REPLACE FUNCTION {schema}.{entity.name.lower()}_pk(p_id UUID)
    RETURNS INTEGER AS $$
    BEGIN
        RETURN (
            SELECT pk_{entity.name.lower()}
            FROM {schema}.{table}
            WHERE id = p_id AND deleted_at IS NULL
        );
    END;
    $$ LANGUAGE plpgsql STABLE;

    -- Trinity helper: Get id (UUID) from pk_*
    CREATE OR REPLACE FUNCTION {schema}.{entity.name.lower()}_id(p_pk INTEGER)
    RETURNS UUID AS $$
    BEGIN
        RETURN (
            SELECT id
            FROM {schema}.{table}
            WHERE pk_{entity.name.lower()} = p_pk AND deleted_at IS NULL
        );
    END;
    $$ LANGUAGE plpgsql STABLE;

    -- Trinity helper: Get identifier from id (UUID)
    CREATE OR REPLACE FUNCTION {schema}.{entity.name.lower()}_identifier(p_id UUID)
    RETURNS TEXT AS $$
    BEGIN
        RETURN (
            SELECT identifier
            FROM {schema}.{table}
            WHERE id = p_id AND deleted_at IS NULL
        );
    END;
    $$ LANGUAGE plpgsql STABLE;
    """
```

#### Step 4: Fix Update Test

Run update test:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_update_action_database_execution -v
```

**Common issue**: `updated_at` not set correctly

Fix in `src/generators/actions/step_compilers/update_step.py`:

```python
def compile_update_step(self, step: ActionStep, context: ActionContext) -> str:
    """Generate UPDATE statement with audit fields"""
    set_clauses = []

    # Add user-specified fields
    for field, value in step.fields.items():
        set_clauses.append(f"{field} = {self._compile_value(value)}")

    # ALWAYS update audit fields
    set_clauses.append("updated_at = NOW()")
    set_clauses.append(f"updated_by = {context.user_id_param}")

    return f"""
    UPDATE {step.entity.schema}.tb_{step.entity.name.lower()}
    SET {', '.join(set_clauses)}
    WHERE id = {context.entity_id_param}
      AND deleted_at IS NULL;
    """
```

#### Step 5: Fix Soft Delete Test

Run soft delete test:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_soft_delete_database_execution -v
```

**What soft delete means**: Set `deleted_at` instead of actual DELETE

```python
# In SpecQL YAML:
- name: delete_contact
  steps:
    - update: Contact SET deleted_at = NOW()

# Generated SQL:
UPDATE crm.tb_contact
SET deleted_at = NOW(),
    updated_at = NOW(),
    updated_by = p_user_id
WHERE id = p_entity_id;
```

Verify this generates correctly in update step compiler.

#### Step 6: Fix Custom Action Test

Run custom action test:
```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py::test_custom_action_database_execution -v
```

This tests multi-step actions:
- Validate
- Update
- Return complete object

#### Step 7: Run All 6 Tests Together

```bash
uv run pytest tests/integration/actions/test_database_roundtrip.py -v
```

**Expected output**:
```
test_create_contact_action_database_execution PASSED
test_validation_error_database_execution PASSED
test_trinity_resolution_database_execution PASSED
test_update_action_database_execution PASSED
test_soft_delete_database_execution PASSED
test_custom_action_database_execution PASSED

========================= 6 passed in 2.34s =========================
```

#### ✅ Day 3 Success Criteria

- [ ] All 6 database roundtrip tests passing
- [ ] Validation errors work correctly
- [ ] Trinity resolution works (UUID → INTEGER)
- [ ] UPDATE sets audit fields
- [ ] Soft delete works
- [ ] Custom actions work

**Deliverable**: 6 database tests passing ✅

---

### Day 4: Confiture Integration Tests 🔗

**Goal**: Make 2 Confiture integration tests pass

#### Step 1: Understand Confiture

Confiture is our migration tool that:
- Organizes SQL migrations in folders
- Runs migrations up/down
- Tracks migration state

Directory structure:
```
migrations/
  00_schemas/
    10_create_crm_schema.sql
  10_types/
    10_create_composite_types.sql
  20_tables/
    10_create_contact_table.sql
  30_functions/
    10_create_contact_actions.sql
```

#### Step 2: Install/Verify Confiture

```bash
# Check if confiture is available
which confiture

# If not installed, install it
# (Add installation instructions based on your setup)

# Verify it works
confiture --version
```

#### Step 3: Understand the Tests

Read `tests/integration/test_confiture_integration.py`:

```python
def test_confiture_migrate_up_and_down(test_db):
    """
    Test that SpecQL-generated SQL works with Confiture migrations
    """
    # 1. Generate SQL for entity
    # 2. Write to Confiture migration folders
    # 3. Run confiture migrate up
    # 4. Verify tables created
    # 5. Run confiture migrate down
    # 6. Verify tables dropped

def test_confiture_fallback_when_unavailable(test_db):
    """
    Test graceful fallback when Confiture not available
    """
    # If confiture not installed, should still work
    # Should apply SQL directly without migration tracking
```

#### Step 4: Remove Skip Markers

Edit `tests/integration/test_confiture_integration.py`:

```python
# Comment out:
# @pytest.mark.skip(reason="Requires actual database connection")
```

#### Step 5: Implement Confiture Integration

Create `src/cli/confiture_integration.py`:

```python
import subprocess
from pathlib import Path
from typing import Optional

class ConfigureIntegration:
    """Integration with Confiture migration tool"""

    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir

    def is_available(self) -> bool:
        """Check if confiture command is available"""
        try:
            result = subprocess.run(
                ['confiture', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def write_migration(self, sql: str, category: str, name: str) -> Path:
        """
        Write SQL to appropriate Confiture migration folder

        Args:
            sql: The SQL DDL to write
            category: One of: schemas, types, tables, functions
            name: Migration name (e.g., "create_contact_table")

        Returns:
            Path to created migration file
        """
        # Map category to Confiture folder
        folder_map = {
            'schemas': '00_schemas',
            'types': '10_types',
            'tables': '20_tables',
            'functions': '30_functions',
        }

        folder = self.migrations_dir / folder_map[category]
        folder.mkdir(parents=True, exist_ok=True)

        # Find next migration number
        existing = list(folder.glob('*.sql'))
        next_num = (len(existing) + 1) * 10

        # Write migration
        filename = f"{next_num:02d}_{name}.sql"
        filepath = folder / filename
        filepath.write_text(sql)

        return filepath

    def migrate_up(self, connection_string: str) -> bool:
        """Run confiture migrate up"""
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                ['confiture', 'migrate', 'up', '--connection', connection_string],
                cwd=self.migrations_dir,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False

    def migrate_down(self, connection_string: str, steps: int = 1) -> bool:
        """Run confiture migrate down"""
        if not self.is_available():
            return False

        try:
            result = subprocess.run(
                ['confiture', 'migrate', 'down', '--steps', str(steps), '--connection', connection_string],
                cwd=self.migrations_dir,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
```

#### Step 6: Update Tests to Use Integration

Update the test to use our integration class:

```python
def test_confiture_migrate_up_and_down(test_db, tmp_path):
    """Test Confiture migration workflow"""
    # Setup
    migrations_dir = tmp_path / "migrations"
    integration = ConfigureIntegration(migrations_dir)

    # Skip if Confiture not available
    if not integration.is_available():
        pytest.skip("Confiture not installed")

    # Generate entity
    entity = create_simple_contact_entity()
    orchestrator = SchemaOrchestrator()

    # Write migrations
    schema_ddl = f"CREATE SCHEMA IF NOT EXISTS {entity.schema};"
    integration.write_migration(schema_ddl, 'schemas', 'create_crm_schema')

    table_ddl = orchestrator.generate_table_ddl(entity)
    integration.write_migration(table_ddl, 'tables', 'create_contact_table')

    # Migrate up
    connection_string = "postgresql://specql_test:test_password@localhost:5433/specql_test"
    success = integration.migrate_up(connection_string)
    assert success, "Migration up failed"

    # Verify table exists
    result = test_db.execute("SELECT * FROM information_schema.tables WHERE table_name = 'tb_contact'")
    assert result is not None

    # Migrate down
    success = integration.migrate_down(connection_string, steps=2)
    assert success, "Migration down failed"

    # Verify table dropped
    result = test_db.execute("SELECT * FROM information_schema.tables WHERE table_name = 'tb_contact'")
    assert result is None
```

#### Step 7: Implement Fallback Test

```python
def test_confiture_fallback_when_unavailable(test_db):
    """Test that we can apply SQL directly if Confiture unavailable"""
    # Generate SQL
    entity = create_simple_contact_entity()
    orchestrator = SchemaOrchestrator()
    ddl = orchestrator.generate_complete_schema(entity)

    # Apply directly (fallback when Confiture not available)
    test_db.execute(ddl)
    test_db.commit()

    # Verify it worked
    result = test_db.execute(
        "SELECT * FROM information_schema.tables WHERE table_name = 'tb_contact'"
    )
    assert result is not None
```

#### Step 8: Run Confiture Tests

```bash
uv run pytest tests/integration/test_confiture_integration.py -v
```

#### ✅ Day 4 Success Criteria

- [ ] 2 Confiture integration tests passing
- [ ] Confiture integration class implemented
- [ ] Migration writing works
- [ ] Migrate up/down works
- [ ] Fallback works when Confiture unavailable

**Deliverable**: 2 Confiture tests passing ✅

---

### Day 5: Polish & QA ✨

**Goal**: Refactor, document, and verify everything works

#### Step 1: Refactor Database Test Helpers

Create `tests/utils/db_test_helpers.py`:

```python
"""Helper utilities for database tests"""

from typing import Any, Dict, Optional
import psycopg

def execute_ddl(db_connection: psycopg.Connection, ddl: str) -> None:
    """Execute DDL and commit"""
    cursor = db_connection.cursor()
    cursor.execute(ddl)
    db_connection.commit()

def execute_query(db_connection: psycopg.Connection,
                 query: str,
                 *params) -> Optional[Dict[str, Any]]:
    """Execute query and return first result as dict"""
    cursor = db_connection.cursor()
    cursor.execute(query, params)

    if cursor.description is None:
        return None

    columns = [desc[0] for desc in cursor.description]
    result = cursor.fetchone()

    if result:
        return dict(zip(columns, result))
    return None

def table_exists(db_connection: psycopg.Connection,
                schema: str,
                table: str) -> bool:
    """Check if table exists"""
    result = execute_query(
        db_connection,
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        schema, table
    )
    return result is not None

def function_exists(db_connection: psycopg.Connection,
                   schema: str,
                   function: str) -> bool:
    """Check if function exists"""
    result = execute_query(
        db_connection,
        """
        SELECT 1 FROM information_schema.routines
        WHERE routine_schema = %s AND routine_name = %s
        """,
        schema, function
    )
    return result is not None
```

Refactor tests to use these helpers.

#### Step 2: Add Database Test Documentation

Create `tests/integration/actions/README.md`:

```markdown
# Database Integration Tests

These tests verify that SpecQL-generated SQL actually works in PostgreSQL.

## Setup

1. Start PostgreSQL:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. Set environment variables:
   ```bash
   export TEST_DB_HOST=localhost
   export TEST_DB_PORT=5433
   export TEST_DB_NAME=specql_test
   export TEST_DB_USER=specql_test
   export TEST_DB_PASSWORD=test_password
   ```

3. Run tests:
   ```bash
   uv run pytest tests/integration/actions/ -v
   ```

## Test Files

- `test_database_roundtrip.py` - Core CRUD operations (6 tests)
- `test_confiture_integration.py` - Migration tool integration (2 tests)

## Debugging

View generated SQL:
```bash
python -c "
from src.generators.schema_orchestrator import SchemaOrchestrator
# ... generate and print SQL
" > /tmp/debug.sql

psql -h localhost -p 5433 -U specql_test -d specql_test < /tmp/debug.sql
```
```

#### Step 3: Configure CI/CD for Database Tests

Create `.github/workflows/database-tests.yml`:

```yaml
name: Database Integration Tests

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
        image: postgres:16-alpine
        env:
          POSTGRES_DB: specql_test
          POSTGRES_USER: specql_test
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run database tests
        env:
          TEST_DB_HOST: localhost
          TEST_DB_PORT: 5432
          TEST_DB_NAME: specql_test
          TEST_DB_USER: specql_test
          TEST_DB_PASSWORD: test_password
        run: |
          uv run pytest tests/integration/ -v --tb=short
```

#### Step 4: Run Full Test Suite

```bash
# Run ALL tests (including database)
uv run pytest -v --tb=short

# Should see:
# - 1409 tests passing (1401 + 8 new database tests)
# - 96 tests skipped (104 - 8 completed)
```

#### Step 5: Update Documentation

Update main `README.md`:

```markdown
## Running Tests

### Quick tests (no database required):
```bash
uv run pytest -m "not database"
```

### Full tests (with database):
```bash
# Start PostgreSQL
docker-compose -f docker-compose.test.yml up -d

# Set environment
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433
export TEST_DB_NAME=specql_test
export TEST_DB_USER=specql_test
export TEST_DB_PASSWORD=test_password

# Run all tests
uv run pytest -v
```
```

#### Step 6: Create Handoff Document

Create `docs/post_beta_plan/week1_handoff.md`:

```markdown
# Week 1 Completion: Database Integration ✅

## What Was Completed

- ✅ Docker setup for PostgreSQL testing
- ✅ 6 database roundtrip tests passing
- ✅ 2 Confiture integration tests passing
- ✅ CI/CD pipeline configured

## Files Created/Modified

### Created:
- `docker-compose.test.yml` - PostgreSQL test database
- `tests/fixtures/schema/00_init.sql` - Database initialization
- `tests/utils/db_test_helpers.py` - Test helper functions
- `src/cli/confiture_integration.py` - Confiture integration
- `.github/workflows/database-tests.yml` - CI/CD pipeline
- `tests/integration/actions/README.md` - Documentation

### Modified:
- `tests/integration/actions/test_database_roundtrip.py` - Removed skip markers
- `tests/integration/test_confiture_integration.py` - Removed skip markers
- `src/generators/schema_orchestrator.py` - Fixed DDL order
- `src/generators/actions/step_compilers/*.py` - Fixed audit fields

## How to Run

```bash
# Start database
docker-compose -f docker-compose.test.yml up -d

# Run tests
uv run pytest tests/integration/ -v
```

## Next Steps

Ready for **Week 2: Rich Type Comments** (13 tests)
```

#### ✅ Day 5 Success Criteria

- [ ] Code refactored and cleaned up
- [ ] Helper functions extracted
- [ ] Documentation complete
- [ ] CI/CD pipeline working
- [ ] All 8 tests passing consistently
- [ ] Ready for Week 2

**Deliverable**: Clean, documented, tested database integration ✅

---

## 🎉 Week 1 Complete!

### What You Accomplished

✅ **8 database tests passing**
- 6 roundtrip tests (CREATE, UPDATE, validation, Trinity)
- 2 Confiture integration tests

✅ **Infrastructure in place**
- Docker Compose setup
- Database initialization
- CI/CD pipeline

✅ **Team B & C improvements**
- Fixed schema generation order
- Fixed action generation
- Fixed audit field handling

### Progress Tracking

```bash
# Before Week 1: 1401 passed, 104 skipped
# After Week 1:  1409 passed, 96 skipped
# Progress:      +8 tests (7.7% of skipped tests complete)
```

### What's Next

**👉 [Week 2: Rich Type Comments](./week2_rich_type_comments.md)** (13 tests)

Week 2 focuses on generating descriptive PostgreSQL COMMENT statements for rich types, enabling better GraphQL schema documentation through FraiseQL autodiscovery.

---

## 💡 Tips & Troubleshooting

### Common Issues

**Issue**: Tests hang or timeout
```bash
# Check database is running
docker-compose -f docker-compose.test.yml ps

# Check connection
psql -h localhost -p 5433 -U specql_test -d specql_test -c "SELECT 1"
```

**Issue**: Permission denied errors
```bash
# Reset database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

**Issue**: Tests pass individually but fail together
```bash
# Run with verbose output to see conflicts
uv run pytest tests/integration/actions/ -v -s

# Check isolated_schema fixture is working
```

### Debugging SQL

Save generated SQL to file:
```python
from src.generators.schema_orchestrator import SchemaOrchestrator

entity = create_simple_contact_entity()
orchestrator = SchemaOrchestrator()
ddl = orchestrator.generate_complete_schema(entity)

with open('/tmp/debug.sql', 'w') as f:
    f.write(ddl)

print("SQL saved to /tmp/debug.sql")
```

Run manually:
```bash
psql -h localhost -p 5433 -U specql_test -d specql_test < /tmp/debug.sql
```

### Getting Help

1. Read the test - it shows exactly what should work
2. Check similar working code
3. Run SQL manually to debug
4. Check PostgreSQL logs: `docker-compose logs postgres`

---

**Great work completing Week 1! 🎉**
