# Team T-Test: Test Suite Generation (pgTAP + Pytest)

**Status**: Planning Phase
**Timeline**: Week 4 (5 days)
**Priority**: High - Enables automated validation
**Team Size**: 1-2 developers
**Dependencies**: Team T-Meta, Team T-Seed complete

---

## 🎯 Mission

**Auto-generate comprehensive test suites (pgTAP + Pytest) from SpecQL definitions and test metadata.**

Generate tests for:
- CRUD operations (create, update, delete)
- Custom actions (qualify_lead, etc.)
- Constraint violations (unique, FK, check)
- Deduplication scenarios
- Multi-tenant isolation

---

## 📋 Test Coverage Matrix

| Test Type | Tool | What We Test | Example |
|-----------|------|--------------|---------|
| **Schema Structure** | pgTAP | Tables, columns, constraints exist | `has_table('crm', 'tb_contact')` |
| **CRUD Functions** | pgTAP | app.create/update/delete work | `app.create_contact(...)` succeeds |
| **Custom Actions** | pgTAP | Business logic functions | `crm.qualify_lead(...)` updates status |
| **Constraints** | pgTAP | Unique, FK, CHECK enforced | Duplicate email fails |
| **Integration** | Pytest | End-to-end Python client | Full create → read → update flow |
| **GraphQL** | Pytest | FraiseQL queries/mutations | 🔄 Future |

---

## 🏗️ Architecture

```
Test Metadata (Team T-Meta)
    ↓
pgTAP Generator → .sql test files
    ├─ Structure tests
    ├─ CRUD tests
    ├─ Action tests
    └─ Constraint tests
    ↓
Pytest Generator → .py test files
    ├─ Integration tests
    ├─ Multi-step workflows
    └─ Performance tests
    ↓
Output:
    tests/pgtap/contact_test.sql
    tests/pytest/test_contact.py
```

---

## 📦 Component 1: pgTAP Test Generator

**File**: `src/testing/pgtap/pgtap_generator.py`

### Structure Test Template

```python
def generate_structure_tests(entity_config: Dict) -> str:
    """Generate schema structure validation tests"""
    entity = entity_config['entity_name']
    schema = entity_config['schema_name']
    table = entity_config['table_name']

    return f"""
-- Structure Tests for {entity}
BEGIN;
SELECT plan(10);

-- Table exists
SELECT has_table(
    '{schema}'::name,
    '{table}'::name,
    '{entity} table should exist'
);

-- Trinity pattern columns
SELECT has_column('{schema}', '{table}', 'pk_{entity.lower()}', 'Has INTEGER PK');
SELECT has_column('{schema}', '{table}', 'id', 'Has UUID id');
SELECT has_column('{schema}', '{table}', 'identifier', 'Has TEXT identifier');

-- Audit columns
SELECT has_column('{schema}', '{table}', 'created_at', 'Has created_at');
SELECT has_column('{schema}', '{table}', 'updated_at', 'Has updated_at');
SELECT has_column('{schema}', '{table}', 'deleted_at', 'Has deleted_at for soft delete');

-- Primary key constraint
SELECT col_is_pk('{schema}', '{table}', 'pk_{entity.lower()}', 'pk_{entity.lower()} is primary key');

-- UUID unique constraint
SELECT col_is_unique('{schema}', '{table}', 'id', 'id is unique');

SELECT * FROM finish();
ROLLBACK;
"""
```

### CRUD Test Template

```python
def generate_crud_tests(entity_config: Dict, field_mappings: List[Dict]) -> str:
    """Generate CRUD operation tests"""
    entity = entity_config['entity_name']
    schema = entity_config['schema_name']

    # Build sample input JSON from field mappings
    input_fields = {}
    for field in field_mappings:
        if field['generator_type'] in ('random', 'fixed'):
            if field['field_type'] == 'email':
                input_fields[field['field_name']] = 'test@example.com'
            elif field['field_type'].startswith('enum('):
                values = field['enum_values'] or field['field_type'][5:-1].split(',')
                input_fields[field['field_name']] = values[0].strip()
            # ... handle other types

    input_json = json.dumps(input_fields)

    return f"""
-- CRUD Tests for {entity}
BEGIN;
SELECT plan(15);

-- Test: CREATE succeeds
PREPARE create_test AS
    SELECT app.create_{entity.lower()}(
        '{entity_config['default_tenant_id']}'::UUID,
        '{entity_config['default_user_id']}'::UUID,
        '{input_json}'::JSONB
    );

SELECT lives_ok(
    'create_test',
    'create_{entity.lower()} should execute without error'
);

-- Test: CREATE returns success
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    v_result := app.create_{entity.lower()}(
        '{entity_config['default_tenant_id']}'::UUID,
        '{entity_config['default_user_id']}'::UUID,
        '{input_json}'::JSONB
    );

    PERFORM ok(
        v_result.status = 'success',
        'CREATE should return success status'
    );

    PERFORM ok(
        v_result.object_data IS NOT NULL,
        'CREATE should return object_data'
    );

    PERFORM ok(
        (v_result.object_data->>'id') IS NOT NULL,
        'object_data should contain id'
    );
END $$;

-- Test: Record exists in database
DO $$
DECLARE
    v_result app.mutation_result;
    v_id UUID;
    v_count INTEGER;
BEGIN
    v_result := app.create_{entity.lower()}(
        '{entity_config['default_tenant_id']}'::UUID,
        '{entity_config['default_user_id']}'::UUID,
        '{input_json}'::JSONB
    );
    v_id := (v_result.object_data->>'id')::UUID;

    SELECT COUNT(*) INTO v_count
    FROM {schema}.{entity_config['table_name']}
    WHERE id = v_id;

    PERFORM is(v_count, 1, 'Record should exist in table');
END $$;

SELECT * FROM finish();
ROLLBACK;
"""
```

### Constraint Violation Test Template

```python
def generate_constraint_tests(entity_config: Dict, scenarios: List[Dict]) -> str:
    """Generate constraint violation tests from scenarios"""
    tests = []

    for scenario in scenarios:
        if scenario['scenario_type'] == 'constraint_violation':
            test = f"""
-- Constraint Test: {scenario['scenario_name']}
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- First insert (should succeed)
    v_result := app.create_{entity_config['entity_name'].lower()}(
        '{entity_config['default_tenant_id']}'::UUID,
        '{entity_config['default_user_id']}'::UUID,
        '{json.dumps(scenario['input_overrides'])}'::JSONB
    );

    PERFORM ok(
        v_result.status = 'success',
        'First insert should succeed'
    );

    -- Duplicate insert (should fail)
    v_result := app.create_{entity_config['entity_name'].lower()}(
        '{entity_config['default_tenant_id']}'::UUID,
        '{entity_config['default_user_id']}'::UUID,
        '{json.dumps(scenario['input_overrides'])}'::JSONB
    );

    PERFORM like(
        v_result.status,
        'failed:%',
        '{scenario['scenario_name']} should fail with error'
    );

    PERFORM like(
        v_result.message,
        '%{scenario.get('expected_error_code', 'duplicate')}%',
        'Error message should mention constraint violation'
    );
END $$;
"""
            tests.append(test)

    return '\n\n'.join(tests)
```

### Custom Action Test Template

```python
def generate_action_tests(entity_config: Dict, actions: List[Dict], scenarios: List[Dict]) -> str:
    """Generate tests for custom actions"""
    tests = []

    for action in actions:
        action_name = action['name']
        schema = entity_config['schema_name']

        # Find scenarios for this action
        action_scenarios = [s for s in scenarios if s.get('target_action') == action_name]

        for scenario in action_scenarios:
            test = f"""
-- Action Test: {action_name} - {scenario['scenario_name']}
BEGIN;
SELECT plan(5);

{scenario.get('setup_sql', '')}

-- Execute action
DO $$
DECLARE
    v_contact_id UUID := '01232122-0000-0000-2000-000000000001';
    v_result app.mutation_result;
BEGIN
    v_result := {schema}.{action_name}(
        v_contact_id,
        '{entity_config['default_user_id']}'::UUID
    );

    -- Verify expected result
    PERFORM {"ok" if scenario['expected_result'] == 'success' else "isnt"}(
        v_result.status,
        'success',
        '{action_name} should {"succeed" if scenario['expected_result'] == 'success' else "fail"}'
    );

    -- Verify updated_fields
    PERFORM ok(
        array_length(v_result.updated_fields, 1) > 0,
        'updated_fields should not be empty'
    );

    -- Verify object_data
    PERFORM ok(
        v_result.object_data IS NOT NULL,
        'object_data should contain result'
    );
END $$;

SELECT * FROM finish();
ROLLBACK;
"""
            tests.append(test)

    return '\n\n'.join(tests)
```

---

## 📦 Component 2: Pytest Integration Test Generator

**File**: `src/testing/pytest/pytest_generator.py`

### Integration Test Template

```python
def generate_pytest_integration_tests(entity_config: Dict, actions: List[Dict]) -> str:
    """Generate pytest integration tests"""
    entity = entity_config['entity_name']
    schema = entity_config['schema_name']

    return f'''
"""Integration tests for {entity} entity"""

import pytest
from uuid import UUID
import psycopg

class Test{entity}Integration:
    """Integration tests for {entity} CRUD and actions"""

    @pytest.fixture
    def clean_db(self, test_db_connection):
        """Clean {entity} table before test"""
        with test_db_connection.cursor() as cur:
            cur.execute("DELETE FROM {schema}.{entity_config['table_name']}")
        test_db_connection.commit()
        yield test_db_connection

    def test_create_{entity.lower()}_happy_path(self, clean_db):
        """Test creating {entity} via app.create function"""
        tenant_id = UUID("{entity_config['default_tenant_id']}")
        user_id = UUID("{entity_config['default_user_id']}")

        with clean_db.cursor() as cur:
            cur.execute(
                """
                SELECT app.create_{entity.lower()}(
                    %s::UUID,
                    %s::UUID,
                    %s::JSONB
                )
                """,
                (tenant_id, user_id, {{"email": "test@example.com", "status": "lead"}})
            )
            result = cur.fetchone()[0]

        assert result['status'] == 'success'
        assert result['object_data']['id'] is not None
        assert result['object_data']['email'] == 'test@example.com'

    def test_create_duplicate_{entity.lower()}_fails(self, clean_db):
        """Test duplicate {entity} fails with proper error"""
        tenant_id = UUID("{entity_config['default_tenant_id']}")
        user_id = UUID("{entity_config['default_user_id']}")
        input_data = {{"email": "duplicate@example.com", "status": "lead"}}

        with clean_db.cursor() as cur:
            # First insert
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success'

            # Duplicate insert
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result2 = cur.fetchone()[0]

        assert result2['status'].startswith('failed:')
        assert 'duplicate' in result2['message'].lower()

{"".join([self._generate_action_test(action, entity_config) for action in actions])}
'''

    def _generate_action_test(self, action: Dict, entity_config: Dict) -> str:
        """Generate test for custom action"""
        action_name = action['name']
        entity = entity_config['entity_name']

        return f'''
    def test_{action_name}(self, clean_db):
        """Test {action_name} action"""
        tenant_id = UUID("{entity_config['default_tenant_id']}")
        user_id = UUID("{entity_config['default_user_id']}")

        with clean_db.cursor() as cur:
            # Setup: Create {entity} with appropriate status
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, {{"email": "qualify@example.com", "status": "lead"}})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Execute action
            cur.execute(
                "SELECT {entity_config['schema_name']}.{action_name}(%s, %s)",
                (contact_id, user_id)
            )
            action_result = cur.fetchone()[0]

        assert action_result['status'] == 'success'
        assert action_result['object_data']['status'] == 'qualified'
'''
```

---

## 🧪 Testing Strategy

### Self-Testing Tests
```python
# tests/unit/testing/test_pgtap_generator.py

def test_generate_structure_tests():
    """pgTAP generator should create structure tests"""
    gen = PgTAPGenerator()
    entity_config = {...}

    sql = gen.generate_structure_tests(entity_config)

    assert "has_table" in sql
    assert "has_column" in sql
    assert "col_is_pk" in sql

def test_generate_crud_tests():
    """pgTAP generator should create CRUD tests"""
    gen = PgTAPGenerator()
    entity_config = {...}

    sql = gen.generate_crud_tests(entity_config, [])

    assert "app.create_contact" in sql
    assert "lives_ok" in sql
```

---

## 📊 Success Criteria

### Week 4 Completion
- ✅ pgTAP generator for structure tests
- ✅ pgTAP generator for CRUD tests
- ✅ pgTAP generator for action tests
- ✅ pgTAP generator for constraint tests
- ✅ Pytest generator for integration tests
- ✅ Generated tests run successfully
- ✅ Contact entity has 50+ auto-generated test cases
- ✅ 10+ unit tests for generators
- ✅ All generated tests pass

---

## 📝 Example Output

**File**: `tests/pgtap/contact_test.sql`

```sql
-- Auto-generated tests for Contact entity
-- Generated: 2025-11-08T15:00:00

-- Structure Tests
BEGIN;
SELECT plan(10);
SELECT has_table('crm', 'tb_contact', 'Contact table exists');
SELECT has_column('crm', 'tb_contact', 'pk_contact', 'Has INTEGER PK');
-- ... 8 more structure tests
SELECT * FROM finish();
ROLLBACK;

-- CRUD Tests
BEGIN;
SELECT plan(15);
-- Test CREATE
DO $$
DECLARE v_result app.mutation_result;
BEGIN
    v_result := app.create_contact(...);
    PERFORM ok(v_result.status = 'success', 'CREATE succeeds');
END $$;
-- ... 14 more CRUD tests
SELECT * FROM finish();
ROLLBACK;

-- Constraint Tests
BEGIN;
SELECT plan(5);
-- Test duplicate email
-- ... constraint tests
SELECT * FROM finish();
ROLLBACK;

-- Action Tests
BEGIN;
SELECT plan(10);
-- Test qualify_lead action
-- ... action tests
SELECT * FROM finish();
ROLLBACK;
```

---

**Next**: [Team T-Prop: Property-Based Testing](04_TEAM_T_PROP.md)
