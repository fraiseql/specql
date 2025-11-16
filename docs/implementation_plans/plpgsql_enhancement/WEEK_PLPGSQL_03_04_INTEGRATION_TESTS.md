# Week PL/pgSQL 3-4: Integration Test Suite

**Date**: TBD
**Duration**: 2 weeks (80 hours)
**Status**: 📅 Planned
**Objective**: Create comprehensive integration test suite for PL/pgSQL generation

**Prerequisites**:
- Week 1-2 complete (PLpgSQLParser working)
- Understanding of SpecQL code generation
- Sample PostgreSQL schemas for testing

**Output**:
- 20+ integration tests
- Sample project with 5+ entities
- Test coverage > 90%
- CI/CD integration

---

## 🎯 Executive Summary

This 2-week sprint creates a **systematic integration test suite** for PL/pgSQL generation, following the proven patterns from Java (Week 12) and Rust (Week 16) implementations.

### Why This Matters

Currently, PL/pgSQL has **scattered integration tests** without systematic coverage:
- Java: 50+ integration tests, 95% coverage, systematic approach
- Rust: 50+ integration tests, 95% coverage, systematic approach
- **PL/pgSQL**: ~15 scattered tests, no systematic suite

This creates **validation gaps** that could impact production migrations like Reference Application.

### Key Objectives

1. **Basic Integration**: SpecQL YAML → PostgreSQL DDL
2. **Multi-Entity Tests**: Related entities with foreign keys
3. **Action Compilation**: SpecQL actions → PL/pgSQL functions
4. **Advanced Features**: Composite types, hierarchical entities, views
5. **Real-World Validation**: Test with production-like schemas

---

## 📅 Week 3: Basic & Multi-Entity Integration Tests

### Day 1: Test Infrastructure Setup (8 hours)

**Objective**: Create test infrastructure and sample project

#### Morning (4 hours): Sample Project Creation

**Step 1.1: Create sample entity definitions** (2 hours)

```bash
cd /home/lionel/code/specql

# Create sample project structure
mkdir -p tests/integration/plpgsql/sample_project/entities
mkdir -p tests/integration/plpgsql/sample_project/expected_sql
mkdir -p tests/integration/plpgsql/sample_project/fixtures
```

Create `tests/integration/plpgsql/sample_project/entities/contact.yaml`:

```yaml
# Sample Contact entity
entity: Contact
schema: crm
description: Customer contact information

fields:
  email: text!
  first_name: text
  last_name: text
  phone: text
  company: ref(Company)!
  status:
    type: enum
    values: [lead, qualified, customer, inactive]
    default: lead

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: not_a_lead
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

Create `tests/integration/plpgsql/sample_project/entities/company.yaml`:

```yaml
entity: Company
schema: crm
description: Company/organization

fields:
  name: text!
  website: text
  industry:
    type: enum
    values: [technology, finance, healthcare, retail, other]
  employee_count: integer
```

Create `tests/integration/plpgsql/sample_project/entities/order.yaml`:

```yaml
entity: Order
schema: sales
description: Customer order

fields:
  contact: ref(Contact)!
  order_number: text!
  total_amount: decimal!
  status:
    type: enum
    values: [pending, processing, shipped, delivered, cancelled]
    default: pending
  shipped_at: datetime
  notes: text

actions:
  - name: ship_order
    steps:
      - validate: status = 'processing'
        error: not_ready_to_ship
      - update: Order SET status = 'shipped', shipped_at = NOW()
      - notify: contact.email("Your order has shipped")
```

Create `tests/integration/plpgsql/sample_project/entities/order_item.yaml`:

```yaml
entity: OrderItem
schema: sales
description: Line item in an order

fields:
  order: ref(Order)!
  product: ref(Product)!
  quantity: integer! = 1
  unit_price: decimal!
  subtotal: decimal!
```

Create `tests/integration/plpgsql/sample_project/entities/product.yaml`:

```yaml
entity: Product
schema: catalog
description: Product catalog

fields:
  name: text!
  description: text
  sku: text!
  price: decimal!
  category: ref(Category)
  in_stock: boolean = true
  stock_quantity: integer = 0
```

**Step 1.2: Generate expected SQL** (2 hours)

```bash
cd /home/lionel/code/specql

# Generate SQL from sample entities
uv run specql generate \
  tests/integration/plpgsql/sample_project/entities/*.yaml \
  --output-dir tests/integration/plpgsql/sample_project/expected_sql \
  --hierarchical \
  --include-trinity \
  --verbose

# This creates:
# - Schema DDL for each entity
# - Function definitions for actions
# - Indexes, constraints, etc.
```

#### Afternoon (4 hours): Test Framework Setup

**Step 1.3: Create test configuration** (1 hour)

Create `tests/integration/plpgsql/conftest.py`:

```python
"""Pytest configuration for PL/pgSQL integration tests"""
import pytest
import psycopg2
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(scope="session")
def test_db_connection():
    """Create test database connection"""
    # Use pytest-postgresql for test database
    # Or connect to existing test instance
    conn = psycopg2.connect(
        dbname="specql_test",
        user="postgres",
        host="localhost",
        port=5432
    )
    yield conn
    conn.close()


@pytest.fixture
def clean_database(test_db_connection):
    """Clean database before each test"""
    with test_db_connection.cursor() as cur:
        # Drop all schemas except system schemas
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        """)
        schemas = [row[0] for row in cur.fetchall()]

        for schema in schemas:
            cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")

        test_db_connection.commit()

    yield test_db_connection


@pytest.fixture
def sample_project_dir():
    """Path to sample project"""
    return Path(__file__).parent / "sample_project"


@pytest.fixture
def temp_output_dir():
    """Temporary directory for generated SQL"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def schema_generator():
    """SpecQL schema generator"""
    from src.generators.schema.schema_generator import SchemaGenerator
    return SchemaGenerator()


@pytest.fixture
def function_generator():
    """SpecQL function generator"""
    from src.generators.function_generator import FunctionGenerator
    from src.core.schema_registry import SchemaRegistry

    registry = SchemaRegistry()
    return FunctionGenerator(registry)
```

**Step 1.4: Create test utilities** (2 hours)

Create `tests/integration/plpgsql/test_utils.py`:

```python
"""Utilities for PL/pgSQL integration tests"""
from pathlib import Path
from typing import List, Dict, Any
import psycopg2
from src.core.specql_parser import SpecQLParser
from src.cli.generate import convert_entity_definition_to_entity


def load_entity_from_yaml(yaml_path: Path):
    """Load entity from YAML file"""
    parser = SpecQLParser()
    yaml_content = yaml_path.read_text()
    entity_def = parser.parse(yaml_content)
    entity = convert_entity_definition_to_entity(entity_def)
    return entity


def execute_sql_file(conn, sql_file: Path):
    """Execute SQL file"""
    sql_content = sql_file.read_text()

    with conn.cursor() as cur:
        cur.execute(sql_content)
        conn.commit()


def execute_sql(conn, sql: str):
    """Execute SQL statement"""
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def table_exists(conn, schema: str, table_name: str) -> bool:
    """Check if table exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            )
        """, (schema, table_name))
        return cur.fetchone()[0]


def function_exists(conn, schema: str, function_name: str) -> bool:
    """Check if function exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.routines
                WHERE routine_schema = %s
                AND routine_name = %s
                AND routine_type = 'FUNCTION'
            )
        """, (schema, function_name))
        return cur.fetchone()[0]


def get_table_columns(conn, schema: str, table_name: str) -> List[Dict[str, Any]]:
    """Get table column definitions"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))

        columns = []
        for row in cur.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3]
            })

        return columns


def get_foreign_keys(conn, schema: str, table_name: str) -> List[Dict[str, Any]]:
    """Get foreign key constraints"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s
            AND tc.table_name = %s
        """, (schema, table_name))

        fks = []
        for row in cur.fetchall():
            fks.append({
                'column': row[0],
                'references_schema': row[1],
                'references_table': row[2],
                'references_column': row[3]
            })

        return fks


def assert_schemas_equivalent(conn, schema1: str, table1: str, schema2: str, table2: str):
    """Assert two schemas are functionally equivalent"""
    cols1 = get_table_columns(conn, schema1, table1)
    cols2 = get_table_columns(conn, schema2, table2)

    # Compare column count
    assert len(cols1) == len(cols2), f"Column count mismatch: {len(cols1)} vs {len(cols2)}"

    # Compare each column
    cols1_by_name = {c['name']: c for c in cols1}
    cols2_by_name = {c['name']: c for c in cols2}

    for col_name in cols1_by_name:
        assert col_name in cols2_by_name, f"Column {col_name} missing in second schema"

        col1 = cols1_by_name[col_name]
        col2 = cols2_by_name[col_name]

        # Compare types (allowing for type aliases)
        assert_types_equivalent(col1['type'], col2['type'])
```

**Step 1.5: Create first integration test** (1 hour)

Create `tests/integration/plpgsql/test_integration_basic.py`:

```python
"""Basic integration tests for PL/pgSQL generation"""
import pytest
from pathlib import Path
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    table_exists,
    function_exists,
    get_table_columns
)


class TestBasicIntegration:
    """Test basic PL/pgSQL generation"""

    def test_generate_simple_entity_schema(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test generating schema for simple entity"""
        # Load Contact entity
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        # Generate DDL
        ddl = schema_generator.generate_table(entity)

        # Execute DDL
        execute_sql(clean_database, ddl)

        # Verify table exists
        assert table_exists(clean_database, "crm", "tb_contact")

        # Verify Trinity pattern fields
        columns = get_table_columns(clean_database, "crm", "tb_contact")
        column_names = [c['name'] for c in columns]

        assert "pk_contact" in column_names
        assert "id" in column_names
        assert "identifier" in column_names

        # Verify business fields
        assert "email" in column_names
        assert "first_name" in column_names
        assert "last_name" in column_names
        assert "phone" in column_names
        assert "fk_company" in column_names
        assert "status" in column_names

        # Verify audit fields
        assert "created_at" in column_names
        assert "updated_at" in column_names
        assert "deleted_at" in column_names

    def test_generate_entity_with_action(
        self,
        clean_database,
        schema_generator,
        function_generator,
        sample_project_dir
    ):
        """Test generating entity with action function"""
        # Load Contact entity
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        # Generate and execute schema
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Generate and execute functions
        functions_sql = function_generator.generate_action_functions(entity)
        execute_sql(clean_database, functions_sql)

        # Verify action function exists
        assert function_exists(clean_database, "crm", "qualify_lead")
        assert function_exists(clean_database, "app", "qualify_lead")

    def test_generate_enum_type(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test generating enum type"""
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        # Generate DDL
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Verify enum type exists
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_type
                    WHERE typname = 'contact_status'
                )
            """)
            assert cur.fetchone()[0], "Enum type 'contact_status' should exist"
```

**Day 1 Deliverables**:
- ✅ Sample project with 5 entities created
- ✅ Test infrastructure set up
- ✅ Test utilities implemented
- ✅ First 3 integration tests passing

---

### Day 2-3: Multi-Entity Integration Tests (16 hours)

**Objective**: Test complex scenarios with multiple related entities

#### Day 2 Morning (4 hours): Foreign Key Tests

**Step 2.1: Create foreign key integration tests** (4 hours)

Create `tests/integration/plpgsql/test_multi_entity_integration.py`:

```python
"""Multi-entity integration tests"""
import pytest
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    table_exists,
    get_foreign_keys
)


class TestMultiEntityIntegration:
    """Test multiple related entities"""

    def test_generate_entities_with_relationships(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test generating related entities"""
        # Load entities in dependency order
        company_yaml = sample_project_dir / "entities" / "company.yaml"
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"

        company_entity = load_entity_from_yaml(company_yaml)
        contact_entity = load_entity_from_yaml(contact_yaml)

        # Generate and execute DDL in order
        company_ddl = schema_generator.generate_table(company_entity)
        execute_sql(clean_database, company_ddl)

        contact_ddl = schema_generator.generate_table(contact_entity)
        execute_sql(clean_database, contact_ddl)

        # Verify both tables exist
        assert table_exists(clean_database, "crm", "tb_company")
        assert table_exists(clean_database, "crm", "tb_contact")

        # Verify foreign key relationship
        fks = get_foreign_keys(clean_database, "crm", "tb_contact")

        company_fk = next(
            (fk for fk in fks if fk['column'] == 'fk_company'),
            None
        )

        assert company_fk is not None, "Foreign key fk_company should exist"
        assert company_fk['references_table'] == 'tb_company'
        assert company_fk['references_column'] == 'pk_company'

    def test_generate_order_with_multiple_references(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test entity with multiple foreign keys"""
        # Generate all dependencies first
        entities_order = [
            "company.yaml",
            "contact.yaml",
            "category.yaml",
            "product.yaml",
            "order.yaml",
        ]

        for entity_file in entities_order:
            entity_yaml = sample_project_dir / "entities" / entity_file
            if entity_yaml.exists():
                entity = load_entity_from_yaml(entity_yaml)
                ddl = schema_generator.generate_table(entity)
                execute_sql(clean_database, ddl)

        # Verify Order table has multiple foreign keys
        fks = get_foreign_keys(clean_database, "sales", "tb_order")

        # Should have foreign key to Contact
        contact_fk = next(
            (fk for fk in fks if 'contact' in fk['column'].lower()),
            None
        )
        assert contact_fk is not None

    def test_generate_junction_table(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test junction table (OrderItem)"""
        # Generate dependencies
        for entity_file in ["product.yaml", "order.yaml", "order_item.yaml"]:
            entity_yaml = sample_project_dir / "entities" / entity_file
            if entity_yaml.exists():
                entity = load_entity_from_yaml(entity_yaml)
                ddl = schema_generator.generate_table(entity)
                execute_sql(clean_database, ddl)

        # Verify OrderItem has two foreign keys
        fks = get_foreign_keys(clean_database, "sales", "tb_order_item")

        assert len(fks) >= 2, "OrderItem should have at least 2 foreign keys"

        # Should reference Order and Product
        fk_columns = [fk['column'] for fk in fks]
        assert any('order' in col.lower() for col in fk_columns)
        assert any('product' in col.lower() for col in fk_columns)
```

#### Day 2 Afternoon (4 hours): Cross-Schema Tests

**Step 2.2: Test entities across multiple schemas** (4 hours)

Continue in `test_multi_entity_integration.py`:

```python
class TestCrossSchemaIntegration:
    """Test entities across different schemas"""

    def test_cross_schema_foreign_keys(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test foreign keys across schemas"""
        # Company in crm schema
        company_yaml = sample_project_dir / "entities" / "company.yaml"
        company_entity = load_entity_from_yaml(company_yaml)
        company_ddl = schema_generator.generate_table(company_entity)
        execute_sql(clean_database, company_ddl)

        # Contact in crm schema (references Company)
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        contact_entity = load_entity_from_yaml(contact_yaml)
        contact_ddl = schema_generator.generate_table(contact_entity)
        execute_sql(clean_database, contact_ddl)

        # Order in sales schema (references Contact from crm)
        order_yaml = sample_project_dir / "entities" / "order.yaml"
        order_entity = load_entity_from_yaml(order_yaml)
        order_ddl = schema_generator.generate_table(order_entity)
        execute_sql(clean_database, order_ddl)

        # Verify cross-schema foreign key
        fks = get_foreign_keys(clean_database, "sales", "tb_order")

        contact_fk = next(
            (fk for fk in fks if 'contact' in fk['column'].lower()),
            None
        )

        assert contact_fk is not None
        assert contact_fk['references_schema'] == 'crm'
        assert contact_fk['references_table'] == 'tb_contact'

    def test_schema_creation_order_independence(
        self,
        clean_database,
        schema_generator,
        sample_project_dir
    ):
        """Test that schema generation handles dependencies"""
        # Try generating in "wrong" order (Order before Contact)
        # Should still work because of deferred constraints

        order_yaml = sample_project_dir / "entities" / "order.yaml"
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"

        order_entity = load_entity_from_yaml(order_yaml)
        contact_entity = load_entity_from_yaml(contact_yaml)

        # Generate Order first (will have deferred FK)
        order_ddl = schema_generator.generate_table(order_entity)

        # Generate Contact second
        contact_ddl = schema_generator.generate_table(contact_entity)

        # Execute both (Order's FK will be validated after Contact exists)
        execute_sql(clean_database, order_ddl)
        execute_sql(clean_database, contact_ddl)

        # Both tables should exist
        assert table_exists(clean_database, "sales", "tb_order")
        assert table_exists(clean_database, "crm", "tb_contact")
```

#### Day 3: Action Compilation Tests (8 hours)

**Objective**: Test SpecQL action → PL/pgSQL function compilation

**Step 2.3: Create action compilation tests** (8 hours)

Create `tests/integration/plpgsql/test_action_compilation.py`:

```python
"""Action compilation integration tests"""
import pytest
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    function_exists
)


class TestActionCompilation:
    """Test SpecQL actions → PL/pgSQL functions"""

    def test_compile_simple_action(
        self,
        clean_database,
        schema_generator,
        function_generator,
        sample_project_dir
    ):
        """Test compiling simple action with validate + update"""
        # Setup: Create Contact table
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Generate action functions
        functions_sql = function_generator.generate_action_functions(entity)
        execute_sql(clean_database, functions_sql)

        # Verify qualify_lead function exists
        assert function_exists(clean_database, "app", "qualify_lead")
        assert function_exists(clean_database, "core", "qualify_lead")

    def test_action_validation_step(
        self,
        clean_database,
        schema_generator,
        function_generator,
        sample_project_dir
    ):
        """Test that validation step works correctly"""
        # Setup
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        functions_sql = function_generator.generate_action_functions(entity)
        execute_sql(clean_database, functions_sql)

        # Insert test contact with status 'lead'
        with clean_database.cursor() as cur:
            cur.execute("""
                INSERT INTO crm.tb_contact (email, first_name, status, fk_company)
                VALUES ('test@example.com', 'John', 'lead', NULL)
                RETURNING pk_contact
            """)
            pk_contact = cur.fetchone()[0]
            clean_database.commit()

        # Call qualify_lead - should succeed
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT app.qualify_lead(%s::INTEGER, '{}'::JSONB)
            """, (pk_contact,))

            result = cur.fetchone()[0]
            clean_database.commit()

        # Verify status changed
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT status FROM crm.tb_contact WHERE pk_contact = %s
            """, (pk_contact,))
            status = cur.fetchone()[0]

        assert status == 'qualified'

    def test_action_validation_failure(
        self,
        clean_database,
        schema_generator,
        function_generator,
        sample_project_dir
    ):
        """Test that validation failure raises error"""
        # Setup
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        functions_sql = function_generator.generate_action_functions(entity)
        execute_sql(clean_database, functions_sql)

        # Insert contact with status 'customer' (not 'lead')
        with clean_database.cursor() as cur:
            cur.execute("""
                INSERT INTO crm.tb_contact (email, first_name, status, fk_company)
                VALUES ('test@example.com', 'John', 'customer', NULL)
                RETURNING pk_contact
            """)
            pk_contact = cur.fetchone()[0]
            clean_database.commit()

        # Call qualify_lead - should fail with validation error
        with pytest.raises(Exception) as exc_info:
            with clean_database.cursor() as cur:
                cur.execute("""
                    SELECT app.qualify_lead(%s::INTEGER, '{}'::JSONB)
                """, (pk_contact,))
                clean_database.commit()

        # Verify error message contains 'not_a_lead'
        assert 'not_a_lead' in str(exc_info.value)

    def test_action_with_notify_step(
        self,
        clean_database,
        schema_generator,
        function_generator,
        sample_project_dir
    ):
        """Test action with notify step"""
        # Setup
        contact_yaml = sample_project_dir / "entities" / "contact.yaml"
        entity = load_entity_from_yaml(contact_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        functions_sql = function_generator.generate_action_functions(entity)
        execute_sql(clean_database, functions_sql)

        # The notify step should be compiled
        # Verify function contains notification logic
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT routine_definition
                FROM information_schema.routines
                WHERE routine_schema = 'core'
                AND routine_name = 'qualify_lead'
            """)
            function_body = cur.fetchone()[0]

        # Should contain email notification logic
        assert 'email' in function_body.lower() or 'notify' in function_body.lower()
```

**Day 2-3 Deliverables**:
- ✅ 10+ multi-entity integration tests
- ✅ Foreign key relationship tests
- ✅ Cross-schema tests
- ✅ Action compilation tests
- ✅ Validation step tests

---

### Day 4-5: Advanced Features & Edge Cases (16 hours)

**Objective**: Test advanced SpecQL features

#### Day 4: Composite Types & Hierarchical Entities (8 hours)

**Step 3.1: Test composite types** (4 hours)

Create `tests/integration/plpgsql/test_composite_types.py`:

```python
"""Composite type integration tests"""
import pytest
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    table_exists
)


class TestCompositeTypes:
    """Test composite type generation"""

    def test_generate_entity_with_rich_type(
        self,
        clean_database,
        schema_generator,
        sample_project_dir,
        tmp_path
    ):
        """Test entity with composite/rich type field"""
        # Create test entity with address composite type
        entity_yaml = tmp_path / "location.yaml"
        entity_yaml.write_text("""
entity: Location
schema: catalog

fields:
  name: text!
  address:
    type: composite
    fields:
      street: text!
      city: text!
      state: text!
      zip_code: text!
      country: text = 'USA'
  coordinates:
    type: composite
    fields:
      latitude: decimal!
      longitude: decimal!
        """)

        entity = load_entity_from_yaml(entity_yaml)

        # Generate DDL
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Verify composite types created
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_type
                    WHERE typname = 'address'
                )
            """)
            assert cur.fetchone()[0], "Composite type 'address' should exist"

        # Verify table uses composite type
        assert table_exists(clean_database, "catalog", "tb_location")
```

**Step 3.2: Test hierarchical entities** (4 hours)

Create `tests/integration/plpgsql/test_hierarchical_entities.py`:

```python
"""Hierarchical entity integration tests"""
import pytest
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    table_exists,
    get_foreign_keys
)


class TestHierarchicalEntities:
    """Test self-referential entities"""

    def test_generate_hierarchical_entity(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entity with parent reference"""
        # Create hierarchical entity
        entity_yaml = tmp_path / "category.yaml"
        entity_yaml.write_text("""
entity: Category
schema: catalog
hierarchical: true

fields:
  name: text!
  description: text
  parent: ref(Category)
  level: integer
        """)

        entity = load_entity_from_yaml(entity_yaml)

        # Generate DDL
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Verify table exists
        assert table_exists(clean_database, "catalog", "tb_category")

        # Verify self-referential foreign key
        fks = get_foreign_keys(clean_database, "catalog", "tb_category")

        parent_fk = next(
            (fk for fk in fks if 'parent' in fk['column'].lower()),
            None
        )

        assert parent_fk is not None
        assert parent_fk['references_table'] == 'tb_category'

    def test_hierarchical_helper_functions(
        self,
        clean_database,
        schema_generator,
        function_generator,
        tmp_path
    ):
        """Test hierarchical helper functions generated"""
        entity_yaml = tmp_path / "category.yaml"
        entity_yaml.write_text("""
entity: Category
schema: catalog
hierarchical: true

fields:
  name: text!
  parent: ref(Category)
        """)

        entity = load_entity_from_yaml(entity_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        # Generate helper functions
        from src.generators.trinity_helper_generator import TrinityHelperGenerator
        helper_gen = TrinityHelperGenerator()
        helpers_sql = helper_gen.generate_all_helpers(entity)
        execute_sql(clean_database, helpers_sql)

        # Verify hierarchical functions exist
        with clean_database.cursor() as cur:
            cur.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'catalog'
                AND routine_type = 'FUNCTION'
                AND routine_name LIKE '%category%'
            """)
            functions = [row[0] for row in cur.fetchall()]

        # Should have ancestors/descendants functions
        assert any('ancestor' in fn for fn in functions)
```

#### Day 5: Edge Cases & Error Handling (8 hours)

**Step 3.3: Test edge cases** (8 hours)

Create `tests/integration/plpgsql/test_edge_cases.py`:

```python
"""Edge case integration tests"""
import pytest
from tests.integration.plpgsql.test_utils import (
    load_entity_from_yaml,
    execute_sql,
    table_exists
)


class TestEdgeCases:
    """Test edge cases and unusual scenarios"""

    def test_entity_with_no_business_fields(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entity with only Trinity fields"""
        entity_yaml = tmp_path / "minimal.yaml"
        entity_yaml.write_text("""
entity: Minimal
schema: test

fields: {}
        """)

        entity = load_entity_from_yaml(entity_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

        assert table_exists(clean_database, "test", "tb_minimal")

    def test_entity_with_very_long_name(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entity with long name (PostgreSQL limits)"""
        entity_yaml = tmp_path / "long.yaml"
        entity_yaml.write_text("""
entity: VeryLongEntityNameThatMightCauseIssues
schema: test

fields:
  field_with_extremely_long_name_that_might_exceed_limits: text
        """)

        entity = load_entity_from_yaml(entity_yaml)

        # Should generate valid DDL (with name truncation if needed)
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

    def test_entity_with_reserved_keywords(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entity using PostgreSQL reserved keywords"""
        entity_yaml = tmp_path / "keywords.yaml"
        entity_yaml.write_text("""
entity: Select
schema: test

fields:
  table: text
  where: text
  order: integer
        """)

        entity = load_entity_from_yaml(entity_yaml)

        # Should quote reserved keywords
        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

    def test_entity_with_unicode_characters(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entity with Unicode in descriptions"""
        entity_yaml = tmp_path / "unicode.yaml"
        entity_yaml.write_text("""
entity: Product
schema: test
description: Product catalog with émojis 🎉 and ñoñ-ASCII

fields:
  name: text!
  description_français: text
        """)

        entity = load_entity_from_yaml(entity_yaml)

        ddl = schema_generator.generate_table(entity)
        execute_sql(clean_database, ddl)

    def test_circular_references(
        self,
        clean_database,
        schema_generator,
        tmp_path
    ):
        """Test entities with circular references"""
        # User references Team, Team references User (as owner)
        user_yaml = tmp_path / "user.yaml"
        user_yaml.write_text("""
entity: User
schema: test

fields:
  name: text!
  team: ref(Team)
        """)

        team_yaml = tmp_path / "team.yaml"
        team_yaml.write_text("""
entity: Team
schema: test

fields:
  name: text!
  owner: ref(User)
        """)

        user_entity = load_entity_from_yaml(user_yaml)
        team_entity = load_entity_from_yaml(team_yaml)

        # Generate both DDLs
        user_ddl = schema_generator.generate_table(user_entity)
        team_ddl = schema_generator.generate_table(team_entity)

        # Should handle circular references with deferred constraints
        execute_sql(clean_database, user_ddl)
        execute_sql(clean_database, team_ddl)

        assert table_exists(clean_database, "test", "tb_user")
        assert table_exists(clean_database, "test", "tb_team")
```

**Week 3 Deliverables**:
- ✅ 20+ integration tests passing
- ✅ Multi-entity relationship tests
- ✅ Action compilation tests
- ✅ Composite type tests
- ✅ Hierarchical entity tests
- ✅ Edge case tests
- ✅ Test coverage > 85%

---

## 📅 Week 4: Performance, Real-World & CI/CD

### Day 1-2: Real-World Schema Testing (16 hours)

**Objective**: Test with production-like schemas

(Continued in next section...)

**Week 4 Deliverables**:
- ✅ Real-world schema tests
- ✅ Performance benchmarks
- ✅ CI/CD integration
- ✅ Test coverage > 90%

---

## ✅ Success Criteria (Week 3-4 Complete)

### Must Have
- [x] 20+ integration tests passing
- [x] Multi-entity relationships tested
- [x] Foreign key constraints verified
- [x] Action compilation validated
- [x] Composite types working
- [x] Hierarchical entities working
- [x] Edge cases covered
- [x] Test coverage > 90%
- [x] CI/CD integrated

### Nice to Have
- [ ] Performance regression tests
- [ ] Visual test reports
- [ ] Mutation testing
- [ ] Chaos engineering tests

---

**Status**: 📅 Planned
**Risk Level**: Low (testing existing functionality)
**Estimated Effort**: 80 hours (2 weeks)
**Prerequisites**: Week 1-2 complete (Parser working)
**Confidence**: Very High (proven testing patterns)

---

*Last Updated*: 2025-11-14
*Author*: SpecQL Team
*Junior Developer Friendly*: Yes ✨

Comprehensive integration testing following Java/Rust patterns!
