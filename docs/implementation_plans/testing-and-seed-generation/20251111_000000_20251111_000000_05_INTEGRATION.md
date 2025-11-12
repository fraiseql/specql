# Integration Plan: Testing Infrastructure + Existing Teams

**Status**: Planning Phase
**Timeline**: Week 6 (Integration) + Week 7 (Polish)
**Priority**: Critical - Ties everything together

---

## 🎯 Mission

**Integrate Team T (Testing) with existing Teams A-E to create seamless test/seed generation pipeline.**

End result: `specql generate contact.yaml --with-tests --with-seed` produces:
- Schema + functions SQL
- Test metadata SQL
- Seed data SQL (100 records)
- pgTAP tests (50+ test cases)
- Pytest integration tests (10+ tests)
- Property-based tests

---

## 🔗 Integration Points

```
┌──────────────────────────────────────────────────────────────┐
│  User: specql generate contact.yaml --with-tests --with-seed │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│  Team E: CLI Orchestrator (EXTENDED)                          │
│  - Parse flags: --with-tests, --with-seed                     │
│  - Coordinate all teams                                       │
└──┬────────┬─────────┬──────────┬──────────┬───────────┬───────┘
   │        │         │          │          │           │
   │        │         │          │          │           │
   ▼        ▼         ▼          ▼          ▼           ▼
┌──────┐┌──────┐┌──────────┐┌─────────┐┌─────────┐┌──────────┐
│Team A││Team B││ Team C   ││ Team D  ││ Team T  ││ Output   │
│Parse ││Schema││ Actions  ││FraiseQL ││ Testing ││Combiner  │
└──┬───┘└──┬───┘└────┬─────┘└────┬────┘└────┬────┘└────┬─────┘
   │       │         │           │          │          │
   │       │         │           │          │          │
   └───────┴─────────┴───────────┴──────────┴──────────┘
                         │
                         ▼
            ┌────────────────────────────┐
            │  Generated Output Files:   │
            │  - migrations/001_*.sql    │
            │  - seed/001_*.sql          │
            │  - tests/pgtap/001_*.sql   │
            │  - tests/pytest/test_*.py  │
            └────────────────────────────┘
```

---

## 📦 Integration 1: Team E (CLI) Extensions

**File**: `src/cli/generate.py` (EXTENDED)

### New CLI Flags

```python
@click.command()
@click.argument('specql_file', type=click.Path(exists=True))
@click.option('--with-tests', is_flag=True, help='Generate test suites (pgTAP + Pytest)')
@click.option('--with-seed', is_flag=True, help='Generate seed data')
@click.option('--seed-count', default=10, help='Number of seed records')
@click.option('--seed-scenarios', default='0', help='Comma-separated scenario codes')
@click.option('--output-dir', default='generated/', help='Output directory')
@click.option('--validate-db', type=str, help='Database URL for validation')
def generate(
    specql_file: str,
    with_tests: bool,
    with_seed: bool,
    seed_count: int,
    seed_scenarios: str,
    output_dir: str,
    validate_db: str
):
    """
    Generate SQL schema, functions, tests, and seed data from SpecQL YAML

    Examples:
        specql generate contact.yaml
        specql generate contact.yaml --with-tests --with-seed
        specql generate contact.yaml --with-seed --seed-count=100 --seed-scenarios=0,1000,2000
    """
    click.echo(f"Generating from {specql_file}...")

    # Team A: Parse YAML → AST
    entity = parse_specql(specql_file)
    click.echo(f"✓ Parsed entity: {entity.name}")

    # Team B: Generate schema
    schema_sql = generate_schema(entity)
    click.echo(f"✓ Generated schema ({len(schema_sql)} lines)")

    # Team C: Generate actions
    action_sql = generate_actions(entity)
    click.echo(f"✓ Generated {len(entity.actions)} actions")

    # Team D: Generate FraiseQL metadata
    fraiseql_sql = generate_fraiseql_metadata(entity)
    click.echo(f"✓ Generated FraiseQL metadata")

    # Combine SQL
    migration_sql = combine_sql(schema_sql, action_sql, fraiseql_sql)
    migration_path = write_migration(migration_sql, output_dir)
    click.echo(f"✓ Wrote migration: {migration_path}")

    # NEW: Team T - Testing Infrastructure
    if with_tests or with_seed:
        click.echo("\\nGenerating testing infrastructure...")

        # Team T-Meta: Generate test metadata
        test_metadata_sql = generate_test_metadata(entity)
        metadata_path = write_file(test_metadata_sql, f"{output_dir}/test_metadata/{entity.name}_metadata.sql")
        click.echo(f"✓ Generated test metadata: {metadata_path}")

        # Team T-Seed: Generate seed data
        if with_seed:
            scenarios = [int(s.strip()) for s in seed_scenarios.split(',')]
            for scenario in scenarios:
                seed_sql = generate_seed_data(
                    entity,
                    scenario=scenario,
                    count=seed_count,
                    db_url=validate_db  # For FK/group leader resolution
                )
                seed_path = write_file(
                    seed_sql,
                    f"{output_dir}/seed/{entity.name}_scenario_{scenario}.sql"
                )
                click.echo(f"✓ Generated seed (scenario {scenario}): {seed_path}")

        # Team T-Test: Generate test suites
        if with_tests:
            # pgTAP tests
            pgtap_sql = generate_pgtap_tests(entity)
            pgtap_path = write_file(pgtap_sql, f"{output_dir}/tests/pgtap/{entity.name}_test.sql")
            click.echo(f"✓ Generated pgTAP tests: {pgtap_path}")

            # Pytest tests
            pytest_code = generate_pytest_tests(entity)
            pytest_path = write_file(pytest_code, f"{output_dir}/tests/pytest/test_{entity.name.lower()}.py")
            click.echo(f"✓ Generated Pytest tests: {pytest_path}")

            # Property tests
            property_code = generate_property_tests(entity)
            property_path = write_file(property_code, f"{output_dir}/tests/property/test_{entity.name.lower()}_properties.py")
            click.echo(f"✓ Generated property tests: {property_path}")

    # Optional: Validate against database
    if validate_db:
        click.echo("\\nValidating against database...")
        validate_generated_sql(migration_sql, validate_db)
        click.echo("✓ SQL validation passed")

    click.echo(f"\\n✅ Generation complete!")
    click.echo(f"   Migration: {migration_path}")
    if with_seed:
        click.echo(f"   Seed data: {len(scenarios)} scenario(s)")
    if with_tests:
        click.echo(f"   Tests: pgTAP + Pytest + Property")
```

### New Helper Functions

```python
def generate_test_metadata(entity: Entity) -> str:
    """Generate test metadata SQL (Team T-Meta)"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    gen = TestMetadataGenerator()

    # Derive table code from entity (simple: hash entity name)
    table_code = derive_table_code(entity)

    sql_parts = []
    sql_parts.append(gen.generate_entity_config(entity, table_code))

    for field in entity.fields.values():
        sql_parts.append(gen.generate_field_mapping(entity_config_id=1, field=field))

    # Auto-generate default scenarios
    sql_parts.append(gen.generate_default_scenarios(entity))

    return '\\n\\n'.join(sql_parts)


def generate_seed_data(
    entity: Entity,
    scenario: int,
    count: int,
    db_url: str = None
) -> str:
    """Generate seed data SQL (Team T-Seed)"""
    from src.testing.seed.seed_generator import EntitySeedGenerator
    from src.testing.seed.sql_generator import SeedSQLGenerator

    # Load metadata
    entity_config = load_entity_config(entity.name)  # From test_metadata if DB available
    field_mappings = load_field_mappings(entity.name)

    # Connect to DB for FK resolution (if URL provided)
    db_conn = connect_db(db_url) if db_url else None

    # Generate entities
    seed_gen = EntitySeedGenerator(entity_config, field_mappings, db_conn)
    entities = seed_gen.generate_batch(count=count, scenario=scenario)

    # Convert to SQL
    sql_gen = SeedSQLGenerator(entity_config)
    return sql_gen.generate_file(entities, scenario=scenario)


def generate_pgtap_tests(entity: Entity) -> str:
    """Generate pgTAP tests (Team T-Test)"""
    from src.testing.pgtap.pgtap_generator import PgTAPGenerator

    gen = PgTAPGenerator()

    tests = []
    tests.append(gen.generate_structure_tests(entity))
    tests.append(gen.generate_crud_tests(entity))
    tests.append(gen.generate_action_tests(entity))
    tests.append(gen.generate_constraint_tests(entity))

    return '\\n\\n'.join(tests)


def generate_pytest_tests(entity: Entity) -> str:
    """Generate Pytest integration tests (Team T-Test)"""
    from src.testing.pytest.pytest_generator import PytestGenerator

    gen = PytestGenerator()
    return gen.generate_integration_tests(entity)


def generate_property_tests(entity: Entity) -> str:
    """Generate Hypothesis property tests (Team T-Prop)"""
    from src.testing.property.property_generator import PropertyTestGenerator

    gen = PropertyTestGenerator()
    return gen.generate_all_properties(entity)
```

---

## 📦 Integration 2: Metadata from Existing Teams

### Team A → Team T-Meta

**Data Flow**: `Entity` AST → Test metadata

```python
# src/testing/metadata/metadata_generator.py

def from_entity_ast(entity: Entity) -> Dict[str, Any]:
    """Extract test metadata from Entity AST"""

    return {
        'entity_name': entity.name,
        'schema_name': entity.schema,
        'table_name': f'tb_{entity.name.lower()}',
        'table_code': derive_table_code(entity),
        'entity_code': derive_entity_code(entity.name),
        'is_tenant_scoped': entity.schema not in ['catalog', 'core'],
        'enable_dedup_tests': has_unique_constraints(entity),
        'field_mappings': [
            {
                'field_name': field.name,
                'field_type': field.type_name,
                'postgres_type': field.postgres_type,
                'generator_type': infer_generator_type(field),
                'nullable': field.nullable,
                # ... more metadata
            }
            for field in entity.fields.values()
        ],
        'actions': entity.actions
    }
```

### Team B → Team T-Meta

**Data Flow**: Table codes for UUID encoding

```python
# Team B already assigns table codes during schema generation
# Team T-Meta reads these codes

def get_table_code_from_schema_generator(entity: Entity) -> int:
    """Get table code assigned by Team B"""
    from src.generators.schema.naming_conventions import derive_table_number

    return derive_table_number(entity.schema, entity.name)
```

### Team C → Team T-Meta

**Data Flow**: Function numbers for UUID encoding

```python
# Team C assigns function numbers during action compilation
# Team T-Meta uses these for mutation test UUIDs

def get_function_number(action_name: str) -> int:
    """Get function number assigned by Team C"""
    from src.generators.actions.function_scaffolding import get_function_metadata

    metadata = get_function_metadata(action_name)
    return metadata['function_number']
```

---

## 📦 Integration 3: Database Fixtures for Testing

**File**: `tests/conftest.py` (EXTENDED)

```python
import pytest
import psycopg
from pathlib import Path

@pytest.fixture(scope="session")
def test_db_connection():
    """PostgreSQL connection for integration tests"""
    conn = psycopg.connect(
        "postgresql://test:test@localhost:5433/specql_test"
    )
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def test_db_schema(test_db_connection):
    """Initialize test database with schemas"""
    with test_db_connection.cursor() as cur:
        # Create test_metadata schema
        cur.execute(open('migrations/test_metadata_schema.sql').read())

        # Create app schema (mutation_result type, etc.)
        cur.execute(open('generated/app_schema.sql').read())

    test_db_connection.commit()
    yield test_db_connection


@pytest.fixture
def clean_db(test_db_schema):
    """Clean database before each test"""
    conn = test_db_schema

    with conn.cursor() as cur:
        # Truncate all test tables
        cur.execute("""
            SELECT table_schema || '.' || table_name
            FROM information_schema.tables
            WHERE table_schema IN ('crm', 'projects', 'catalog')
              AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"TRUNCATE TABLE {table} CASCADE")

    conn.commit()
    yield conn
    conn.rollback()


@pytest.fixture
def entity_config_fixture():
    """Fixture for test metadata entity config"""
    return {
        'entity_name': 'Contact',
        'schema_name': 'crm',
        'table_name': 'tb_contact',
        'table_code': 123210,
        'entity_code': 'CON',
        'base_uuid_prefix': '012321',
        'default_tenant_id': '22222222-2222-2222-2222-222222222222',
        'default_user_id': '01232022-0000-0000-0000-000000000001',
        'is_tenant_scoped': True
    }
```

---

## 📦 Integration 4: Docker Compose for Test Database

**File**: `docker-compose.yml` (NEW)

```yaml
version: '3.8'

services:
  test-db:
    image: postgres:16
    container_name: specql_test_db
    environment:
      POSTGRES_DB: specql_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    volumes:
      - test_db_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5

  # pgTAP for database testing
  pgtap:
    image: postgres:16
    depends_on:
      test-db:
        condition: service_healthy
    volumes:
      - ./tests/pgtap:/tests
    command: >
      sh -c "
        apt-get update &&
        apt-get install -y postgresql-16-pgtap &&
        pg_prove -h test-db -U test -d specql_test /tests/*.sql
      "

volumes:
  test_db_data:
```

**Usage**:
```bash
# Start test database
docker-compose up -d test-db

# Run pgTAP tests
docker-compose run pgtap

# Run pytest tests
uv run pytest tests/integration/ --db-url=postgresql://test:test@localhost:5433/specql_test
```

---

## 📦 Integration 5: Makefile Commands

**File**: `Makefile` (EXTENDED)

```makefile
# Existing targets
test:
    uv run pytest tests/unit/ -v

# NEW: Testing infrastructure targets
test-meta:
    uv run pytest tests/unit/testing/test_metadata_*.py -v

test-seed:
    uv run pytest tests/unit/testing/test_*seed*.py -v

test-pgtap-gen:
    uv run pytest tests/unit/testing/test_pgtap_generator.py -v

test-pytest-gen:
    uv run pytest tests/unit/testing/test_pytest_generator.py -v

# Integration tests (require Docker)
test-integration:
    docker-compose up -d test-db
    uv run pytest tests/integration/testing/ -v --db-url=postgresql://test:test@localhost:5433/specql_test

# Run generated pgTAP tests
test-pgtap:
    docker-compose run pgtap

# Generate everything for Contact example
generate-example:
    uv run python -m src.cli.generate entities/examples/contact_lightweight.yaml \\
        --with-tests --with-seed --seed-count=100 --output-dir=generated/

# Full test suite
test-all: test test-meta test-seed test-pgtap-gen test-integration test-pgtap
    @echo "✅ All tests passed!"
```

---

## 📊 Success Criteria

### Week 6 Integration
- ✅ CLI `--with-tests` flag working
- ✅ CLI `--with-seed` flag working
- ✅ All teams coordinated by Team E
- ✅ Docker Compose test database
- ✅ End-to-end: YAML → SQL + Tests + Seed
- ✅ Contact example fully generated
- ✅ All generated tests pass

### Week 7 Polish
- ✅ Documentation updated
- ✅ Example gallery (Contact, Task, Manufacturer)
- ✅ Performance optimization (< 5s for full generation)
- ✅ Error handling and validation
- ✅ CI/CD integration guide

---

## 📝 Complete Example Workflow

```bash
# 1. Start test database
docker-compose up -d test-db

# 2. Generate everything from SpecQL
specql generate entities/contact.yaml \\
    --with-tests \\
    --with-seed \\
    --seed-count=100 \\
    --seed-scenarios=0,1000,2000 \\
    --output-dir=generated/ \\
    --validate-db=postgresql://test:test@localhost:5433/specql_test

# Output:
# ✓ Parsed entity: Contact
# ✓ Generated schema (247 lines)
# ✓ Generated 3 actions
# ✓ Generated FraiseQL metadata
# ✓ Wrote migration: generated/migrations/001_contact.sql
#
# Generating testing infrastructure...
# ✓ Generated test metadata: generated/test_metadata/Contact_metadata.sql
# ✓ Generated seed (scenario 0): generated/seed/Contact_scenario_0.sql
# ✓ Generated seed (scenario 1000): generated/seed/Contact_scenario_1000.sql
# ✓ Generated seed (scenario 2000): generated/seed/Contact_scenario_2000.sql
# ✓ Generated pgTAP tests: generated/tests/pgtap/Contact_test.sql
# ✓ Generated Pytest tests: generated/tests/pytest/test_contact.py
# ✓ Generated property tests: generated/tests/property/test_contact_properties.py
#
# Validating against database...
# ✓ SQL validation passed
#
# ✅ Generation complete!
#    Migration: generated/migrations/001_contact.sql (1847 lines)
#    Seed data: 3 scenario(s), 300 total records
#    Tests: pgTAP (52 tests) + Pytest (12 tests) + Property (5 properties)

# 3. Apply to database
psql postgresql://test:test@localhost:5433/specql_test < generated/migrations/001_contact.sql
psql postgresql://test:test@localhost:5433/specql_test < generated/test_metadata/Contact_metadata.sql
psql postgresql://test:test@localhost:5433/specql_test < generated/seed/Contact_scenario_0.sql

# 4. Run tests
docker-compose run pgtap  # Run pgTAP tests
uv run pytest generated/tests/pytest/  # Run Pytest tests

# Output:
# pgTAP: 52/52 tests passed
# Pytest: 12/12 tests passed
# ✅ All tests passed!
```

---

## 🎯 Final Deliverables

### Code
- `src/testing/` - Complete testing infrastructure (1500+ lines)
- `tests/unit/testing/` - 50+ unit tests
- `tests/integration/testing/` - 15+ integration tests

### SQL
- `migrations/test_metadata_schema.sql` - Test metadata schema
- `migrations/test_metadata_functions.sql` - Query API functions

### Documentation
- Implementation plans (this directory)
- User guide for test/seed generation
- API reference for testing utilities

### Examples
- Contact entity: Full generation showcase
- Task entity: Complex relationships
- Manufacturer entity: Advanced features

---

## 🚀 Beyond Week 7: Future Enhancements

### Short Term (Week 8-10)
- Performance benchmarking suite
- Visual test reports
- GraphQL query test generation
- Mutation testing (test the tests)

### Medium Term (Month 2-3)
- AI-powered test case suggestions
- Snapshot testing for SQL
- Visual regression testing
- Load testing framework

### Long Term (Beyond)
- Production data anonymization for seed
- ML-based realistic data generation
- Continuous test optimization
- Integration with monitoring/observability

---

**🎉 With this integration complete, SpecQL achieves true 150x code leverage: Business logic → Production code → Comprehensive tests → Realistic seed data, all from 20 lines of YAML!**
