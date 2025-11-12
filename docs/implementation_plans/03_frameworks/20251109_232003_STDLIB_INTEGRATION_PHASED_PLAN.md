# SpecQL stdlib Integration - Phased Implementation Plan

**Project**: printoptim_backend_poc
**Task**: Integrate 30 battle-tested entities from SpecQL stdlib v1.1.0
**Complexity**: Complex | **Phased TDD Approach**
**Document Created**: 2025-11-09

---

## Executive Summary

Integrate the SpecQL standard library (30 production-ready entities) into printoptim_backend_poc to demonstrate the framework's ability to generate production-quality code from real-world entity definitions. The stdlib showcases advanced FraiseQL features including rich scalar types (coordinates, email, phone, money, url), hierarchical entities, and complex business actions.

**Key Challenge**: The stdlib uses rich types that are already defined in `src/core/scalar_types.py` but may not be fully integrated across all generators (Team B: Schema, Team C: Actions, Team D: FraiseQL).

**Success Criteria**:
- All 30 stdlib entities generate valid PostgreSQL DDL
- Rich types correctly map to PostgreSQL types with validation constraints
- Spatial types (coordinates) generate proper GIST indexes
- Generated code matches PrintOptim production patterns
- Full test coverage for rich type handling

---

## Current State Analysis

### ✅ What's Already Implemented

1. **Rich Type Registry** (`src/core/scalar_types.py`):
   - 49 scalar types defined (email, phone, url, coordinates, money, etc.)
   - PostgreSQL type mappings complete
   - Validation patterns (regex) defined
   - Composite types defined (MoneyAmount, ContactInfo, etc.)

2. **Team A (Parser)**:
   - Should already parse stdlib YAML files
   - Needs validation for rich types

3. **Team B (Schema Generator)**:
   - Basic table generation works
   - Rich type handling may be incomplete

4. **Team C (Action Compiler)**:
   - Basic action compilation works
   - Rich type handling in expressions may be incomplete

5. **Team D (FraiseQL)**:
   - Metadata generation works
   - Rich type GraphQL scalar mapping may be incomplete

### ❌ What's Missing

1. **Rich Type Validation** in Parser (Team A)
2. **Rich Type PostgreSQL Generation** in Schema Generator (Team B):
   - CHECK constraints for validated types (email, phone, url)
   - GIST indexes for spatial types (coordinates)
   - Proper NUMERIC precision for money, percentage, etc.
3. **Rich Type Expression Handling** in Action Compiler (Team C)
4. **GraphQL Scalar Definitions** for FraiseQL (Team D)
5. **End-to-End Tests** with stdlib entities
6. **Migration Scripts** for stdlib deployment

---

## PHASE 1: Rich Type Foundation - Parser & Validation

**Objective**: Ensure Team A parser correctly validates all rich types used in stdlib entities

**Estimated Time**: 3-4 hours

### TDD Cycle 1.1: Parse stdlib entities with rich types

#### 🔴 RED: Write failing test for rich type parsing
**Test file**: `tests/unit/core/test_rich_type_parsing.py`

```python
def test_parse_contact_entity_with_email_phone_rich_types():
    """Contact entity uses email and phone rich types"""
    yaml_content = """
entity: Contact
schema: tenant
fields:
  email_address:
    type: email
    nullable: false
  mobile_phone:
    type: phone
"""
    result = parse_specql_yaml(yaml_content)

    # Should recognize 'email' and 'phone' as rich scalar types
    assert result.fields['email_address'].type_name == 'email'
    assert result.fields['email_address'].is_rich_type == True
    assert result.fields['mobile_phone'].type_name == 'phone'
```

**Expected failure**: `AttributeError: 'FieldDef' object has no attribute 'is_rich_type'`

#### 🟢 GREEN: Implement minimal rich type detection
**Files to modify**:
- `src/core/ast_models.py` - Add `is_rich_type` property to FieldDef
- `src/core/parser.py` - Detect rich types using `scalar_types.is_scalar_type()`

**Minimal implementation**:
```python
# In ast_models.py
from src.core.scalar_types import is_rich_type

@dataclass
class FieldDef:
    name: str
    type_name: str
    # ... existing fields ...

    @property
    def is_rich_type(self) -> bool:
        """Check if field uses a rich type (scalar or composite)"""
        return is_rich_type(self.type_name)
```

**Run test**: `uv run pytest tests/unit/core/test_rich_type_parsing.py::test_parse_contact_entity_with_email_phone_rich_types -v`

#### 🔧 REFACTOR: Clean up rich type detection
- Add comprehensive rich type validation
- Add helpful error messages for unknown types
- Follow existing parser patterns

**Run broader tests**: `uv run pytest tests/unit/core/ -v`

#### ✅ QA: Verify phase completion
```bash
# All parser tests pass
uv run pytest tests/unit/core/ -v

# Parse real stdlib entities
uv run python -c "
from src.core.parser import parse_specql_file
result = parse_specql_file('stdlib/crm/contact.yaml')
print(f'Parsed {result.entity_name} with {len(result.fields)} fields')
"
```

**Checklist**:
- [ ] All parser tests pass
- [ ] Real stdlib entities parse without errors
- [ ] Rich types correctly identified
- [ ] Clear error messages for invalid types

---

## PHASE 2: Rich Type PostgreSQL Generation (Team B)

**Objective**: Generate correct PostgreSQL DDL for all rich scalar types

**Estimated Time**: 6-8 hours

### TDD Cycle 2.1: Generate email type with validation

#### 🔴 RED: Write failing test for email validation
**Test file**: `tests/unit/generators/test_rich_type_schema_generation.py`

```python
def test_generate_email_field_with_check_constraint():
    """Email rich type should generate TEXT with email validation CHECK constraint"""
    field = FieldDef(
        name='email_address',
        type_name='email',
        nullable=False
    )

    sql = generate_field_ddl(field)

    # Should generate TEXT with email regex CHECK constraint
    assert 'email_address TEXT NOT NULL' in sql
    assert 'CHECK (' in sql
    assert '@' in sql  # Email regex pattern
```

**Expected failure**: `AssertionError: 'CHECK (' not in sql`

#### 🟢 GREEN: Implement email field generation
**Files to modify**:
- `src/generators/table_generator.py` - Use `scalar_types.get_scalar_type()` for rich types

**Minimal implementation**:
```python
from src.core.scalar_types import get_scalar_type, is_scalar_type

def generate_field_ddl(field: FieldDef) -> str:
    if is_scalar_type(field.type_name):
        scalar_def = get_scalar_type(field.type_name)

        # Get PostgreSQL type with precision
        pg_type = scalar_def.get_postgres_type_with_precision()

        # Build DDL
        parts = [f"{field.name} {pg_type}"]

        if not field.nullable:
            parts.append("NOT NULL")

        # Add validation constraint if defined
        if scalar_def.validation_pattern:
            parts.append(f"CHECK ({field.name} ~* '{scalar_def.validation_pattern}')")

        return ' '.join(parts)

    # ... existing logic for basic types ...
```

**Run test**: `uv run pytest tests/unit/generators/test_rich_type_schema_generation.py::test_generate_email_field_with_check_constraint -v`

#### 🔧 REFACTOR: Clean up and extend to all validated types
- Handle phone, url, slug, etc.
- Extract validation constraint generation to helper function
- Add tests for min_value, max_value constraints (money, percentage)

#### ✅ QA: Verify email and phone generation
```bash
uv run pytest tests/unit/generators/test_rich_type_schema_generation.py -v
```

**Checklist**:
- [ ] Email fields generate with regex validation
- [ ] Phone fields generate with E.164 validation
- [ ] URL fields generate with URL validation
- [ ] Code follows existing table generator patterns

---

### TDD Cycle 2.2: Generate coordinates type with GIST index

#### 🔴 RED: Write failing test for coordinates spatial index
**Test file**: `tests/unit/generators/test_rich_type_schema_generation.py`

```python
def test_generate_coordinates_field_with_gist_index():
    """Coordinates rich type should generate POINT type with GIST spatial index"""
    entity = EntityDef(
        entity_name='PublicAddress',
        schema='common',
        fields={
            'coordinates': FieldDef(
                name='coordinates',
                type_name='coordinates',
                nullable=True
            )
        }
    )

    sql = generate_table_ddl(entity)

    # Should generate POINT type
    assert 'coordinates POINT' in sql

    # Should generate GIST spatial index
    assert 'CREATE INDEX' in sql
    assert 'USING GIST (coordinates)' in sql
```

**Expected failure**: `AssertionError: 'USING GIST (coordinates)' not in sql`

#### 🟢 GREEN: Implement spatial index generation
**Files to modify**:
- `src/generators/index_generator.py` - Add spatial index detection

**Minimal implementation**:
```python
from src.core.scalar_types import get_scalar_type, PostgreSQLType

def generate_indexes(entity: EntityDef) -> List[str]:
    indexes = []

    # ... existing index logic ...

    # Add spatial indexes for POINT types
    for field_name, field in entity.fields.items():
        if is_scalar_type(field.type_name):
            scalar_def = get_scalar_type(field.type_name)
            if scalar_def.postgres_type == PostgreSQLType.POINT:
                index_name = f"idx_tb_{entity.entity_name.lower()}_{field_name}"
                indexes.append(
                    f"CREATE INDEX {index_name} ON {entity.schema}.tb_{entity.entity_name.lower()} "
                    f"USING GIST ({field_name});"
                )

    return indexes
```

**Run test**: `uv run pytest tests/unit/generators/test_rich_type_schema_generation.py::test_generate_coordinates_field_with_gist_index -v`

#### 🔧 REFACTOR: Clean up spatial index generation
- Extract to helper function
- Add configuration for spatial index types (GIST, BRIN, etc.)
- Handle nullable vs non-nullable spatial fields

#### ✅ QA: Verify spatial index generation
```bash
uv run pytest tests/unit/generators/ -k spatial -v
uv run pytest tests/unit/schema/ -v
```

**Checklist**:
- [ ] Coordinates fields generate POINT type
- [ ] GIST indexes created for spatial fields
- [ ] Index naming follows conventions
- [ ] All schema generator tests pass

---

### TDD Cycle 2.3: Generate money type with precision

#### 🔴 RED: Write failing test for money precision
**Test file**: `tests/unit/generators/test_rich_type_schema_generation.py`

```python
def test_generate_money_field_with_numeric_precision():
    """Money rich type should generate NUMERIC(19,4)"""
    field = FieldDef(
        name='amount',
        type_name='money',
        nullable=False
    )

    sql = generate_field_ddl(field)

    # Should generate NUMERIC with (19,4) precision
    assert 'amount NUMERIC(19,4) NOT NULL' in sql
```

**Expected failure**: `AssertionError: 'NUMERIC(19,4)' not in sql`

#### 🟢 GREEN: Implement precision handling
**Implementation**: Already handled by `get_postgres_type_with_precision()` in Cycle 2.1

**Run test**: `uv run pytest tests/unit/generators/test_rich_type_schema_generation.py::test_generate_money_field_with_numeric_precision -v`

#### 🔧 REFACTOR: Test all precision types
- Test percentage (5,2)
- Test latitude (10,8)
- Test longitude (11,8)
- Test exchangeRate (19,8)

#### ✅ QA: Verify all numeric precision types
```bash
uv run pytest tests/unit/generators/ -k precision -v
```

**Checklist**:
- [ ] Money generates NUMERIC(19,4)
- [ ] Percentage generates NUMERIC(5,2)
- [ ] All numeric types have correct precision
- [ ] Min/max constraints generated where defined

---

## PHASE 3: stdlib Entity End-to-End Tests

**Objective**: Verify complete DDL generation for real stdlib entities

**Estimated Time**: 4-6 hours

### TDD Cycle 3.1: Generate Contact entity (crm)

#### 🔴 RED: Write failing E2E test for Contact
**Test file**: `tests/integration/stdlib/test_stdlib_contact_generation.py`

```python
def test_generate_contact_entity_full_ddl():
    """Generate complete DDL for stdlib Contact entity"""
    entity = parse_specql_file('stdlib/crm/contact.yaml')

    ddl = generate_complete_schema(entity)

    # Verify table creation
    assert 'CREATE TABLE tenant.tb_contact' in ddl

    # Verify rich type fields
    assert 'email_address TEXT NOT NULL CHECK' in ddl  # Email validation
    assert 'office_phone TEXT CHECK' in ddl  # Phone validation
    assert 'mobile_phone TEXT CHECK' in ddl

    # Verify foreign keys
    assert 'REFERENCES tenant.tb_organization' in ddl
    assert 'REFERENCES common.tb_genre' in ddl

    # Verify Trinity pattern
    assert 'pk_contact INTEGER PRIMARY KEY' in ddl
    assert 'id UUID NOT NULL DEFAULT gen_random_uuid()' in ddl
    assert 'identifier TEXT NOT NULL' in ddl

    # Verify audit fields
    assert 'created_at TIMESTAMPTZ NOT NULL DEFAULT now()' in ddl
    assert 'updated_at TIMESTAMPTZ NOT NULL DEFAULT now()' in ddl
```

**Expected failure**: Email/phone CHECK constraints not generated

#### 🟢 GREEN: Ensure schema generator handles Contact
**Files to verify**:
- `src/generators/schema_orchestrator.py` - Orchestrate full generation
- `src/generators/table_generator.py` - Rich type handling from Phase 2

**Run test**: `uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py::test_generate_contact_entity_full_ddl -v`

#### 🔧 REFACTOR: Add validation helpers
- Extract DDL assertion helpers
- Add snapshot testing for generated SQL
- Verify against PrintOptim production schema

#### ✅ QA: Full Contact entity generation
```bash
# Run integration test
uv run pytest tests/integration/stdlib/test_stdlib_contact_generation.py -v

# Generate actual SQL file
uv run python -c "
from src.core.parser import parse_specql_file
from src.generators.schema_orchestrator import generate_complete_schema

entity = parse_specql_file('stdlib/crm/contact.yaml')
ddl = generate_complete_schema(entity)
print(ddl)
" > /tmp/contact_generated.sql

# Validate SQL syntax
psql -d postgres -f /tmp/contact_generated.sql --dry-run
```

**Checklist**:
- [ ] Contact entity generates complete DDL
- [ ] Email and phone validation constraints present
- [ ] Foreign keys correctly generated
- [ ] Trinity pattern applied
- [ ] SQL is syntactically valid

---

### TDD Cycle 3.2: Generate PublicAddress entity (geo)

#### 🔴 RED: Write failing E2E test for PublicAddress
**Test file**: `tests/integration/stdlib/test_stdlib_public_address_generation.py`

```python
def test_generate_public_address_with_coordinates():
    """Generate complete DDL for stdlib PublicAddress with spatial coordinates"""
    entity = parse_specql_file('stdlib/geo/public_address.yaml')

    ddl = generate_complete_schema(entity)

    # Verify POINT type for coordinates
    assert 'coordinates POINT' in ddl

    # Verify GIST spatial index
    assert 'CREATE INDEX idx_tb_publicaddress_coordinates' in ddl
    assert 'USING GIST (coordinates)' in ddl

    # Verify foreign keys to geo entities
    assert 'REFERENCES common.tb_country' in ddl
    assert 'REFERENCES common.tb_postalcode' in ddl
```

**Expected failure**: GIST index not generated

#### 🟢 GREEN: Ensure spatial index generation works
**Files to verify**:
- `src/generators/index_generator.py` - Spatial index logic from Phase 2.2

**Run test**: `uv run pytest tests/integration/stdlib/test_stdlib_public_address_generation.py::test_generate_public_address_with_coordinates -v`

#### 🔧 REFACTOR: Verify PostGIS compatibility
- Test on PostgreSQL with PostGIS extension
- Validate POINT vs GEOMETRY types
- Add comments explaining spatial choices

#### ✅ QA: Full PublicAddress generation
```bash
uv run pytest tests/integration/stdlib/test_stdlib_public_address_generation.py -v

# Test with PostGIS if available
createdb test_spatial
psql test_spatial -c "CREATE EXTENSION postgis;"
psql test_spatial -f /tmp/public_address_generated.sql
```

**Checklist**:
- [ ] PublicAddress generates with POINT type
- [ ] GIST index created
- [ ] Works with and without PostGIS
- [ ] Spatial queries functional

---

### TDD Cycle 3.3: Generate all 30 stdlib entities

#### 🔴 RED: Write parameterized test for all stdlib entities
**Test file**: `tests/integration/stdlib/test_stdlib_full_generation.py`

```python
import pytest
from pathlib import Path

STDLIB_ENTITIES = [
    'i18n/country.yaml',
    'i18n/currency.yaml',
    'crm/contact.yaml',
    'crm/organization.yaml',
    'geo/public_address.yaml',
    # ... all 30 entities
]

@pytest.mark.parametrize('entity_path', STDLIB_ENTITIES)
def test_generate_stdlib_entity(entity_path):
    """Generate DDL for all stdlib entities without errors"""
    entity = parse_specql_file(f'stdlib/{entity_path}')

    # Should not raise any exceptions
    ddl = generate_complete_schema(entity)

    # Should generate non-empty DDL
    assert len(ddl) > 100
    assert 'CREATE TABLE' in ddl
```

**Expected failure**: Some entities fail due to missing dependencies or edge cases

#### 🟢 GREEN: Fix failing entities one by one
**Approach**:
1. Run test to identify failing entities
2. Fix parser, generator, or entity definition
3. Repeat until all pass

**Run test**: `uv run pytest tests/integration/stdlib/test_stdlib_full_generation.py -v`

#### 🔧 REFACTOR: Add comprehensive validation
- Validate all foreign key references exist
- Check for circular dependencies
- Validate schema assignments (common vs tenant)

#### ✅ QA: All 30 entities generate successfully
```bash
# Generate all entities
uv run pytest tests/integration/stdlib/test_stdlib_full_generation.py -v

# Generate full stdlib schema
uv run python scripts/generate_stdlib_schema.py > db/schema/stdlib_full.sql

# Validate SQL syntax
psql -d test_db -f db/schema/stdlib_full.sql
```

**Checklist**:
- [ ] All 30 entities parse successfully
- [ ] All 30 entities generate valid DDL
- [ ] No missing dependencies
- [ ] Full schema deploys to PostgreSQL

---

## PHASE 4: Action Compilation with Rich Types (Team C)

**Objective**: Ensure action compiler handles rich type expressions correctly

**Estimated Time**: 4-6 hours

### TDD Cycle 4.1: Compile action with email validation

#### 🔴 RED: Write failing test for email validation in action
**Test file**: `tests/unit/actions/test_rich_type_action_compilation.py`

```python
def test_compile_action_with_email_validation():
    """Action with email field should compile correctly"""
    action = ActionDef(
        name='update_email',
        steps=[
            ValidateStep(
                condition="email_address ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'"
            ),
            UpdateStep(
                table='Contact',
                set_clause="email_address = new_email"
            )
        ]
    )

    sql = compile_action(action, entity)

    # Should compile email regex validation
    assert "~*" in sql  # Regex operator
```

**Expected failure**: Regex operator escaping issues

#### 🟢 GREEN: Ensure expression compiler handles regex
**Files to verify**:
- `src/generators/actions/expression_compiler.py` - Regex operator support

**Run test**: `uv run pytest tests/unit/actions/test_rich_type_action_compilation.py::test_compile_action_with_email_validation -v`

#### 🔧 REFACTOR: Add rich type helpers for actions
- Create helper functions for common validations
- Extract email/phone validation to reusable snippets

#### ✅ QA: Rich type action compilation
```bash
uv run pytest tests/unit/actions/ -k rich_type -v
```

**Checklist**:
- [ ] Email validation in actions compiles
- [ ] Phone validation in actions compiles
- [ ] Expression compiler handles regex operators
- [ ] All action tests pass

---

### TDD Cycle 4.2: Compile stdlib actions

#### 🔴 RED: Write test for Contact actions
**Test file**: `tests/integration/stdlib/test_stdlib_action_compilation.py`

```python
def test_compile_contact_change_email_action():
    """Compile Contact.change_email_address action"""
    entity = parse_specql_file('stdlib/crm/contact.yaml')

    # Assume action definition exists (or mock it)
    action = entity.actions['change_email_address']

    sql = compile_action(action, entity)

    # Should generate PL/pgSQL function
    assert 'CREATE OR REPLACE FUNCTION' in sql
    assert 'tenant.change_email_address' in sql
    assert 'RETURNS app.mutation_result' in sql
```

**Expected failure**: Actions in stdlib are placeholders (name-only)

#### 🟢 GREEN: Add action implementations to stdlib
**Files to modify**:
- `stdlib/crm/contact.yaml` - Add full action definitions with steps

**Example**:
```yaml
actions:
  - name: change_email_address
    description: "Update contact email address with validation"
    steps:
      - validate: email_address IS NOT NULL
      - validate: new_email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
      - update: Contact SET email_address = new_email WHERE pk_contact = contact_pk
```

**Run test**: `uv run pytest tests/integration/stdlib/test_stdlib_action_compilation.py::test_compile_contact_change_email_action -v`

#### 🔧 REFACTOR: Add business logic to stdlib actions
- Implement all actions in Contact
- Implement actions in PublicAddress (geocode, validate, etc.)
- Add comprehensive validation steps

#### ✅ QA: All stdlib actions compile
```bash
uv run pytest tests/integration/stdlib/test_stdlib_action_compilation.py -v

# Generate all action functions
uv run python scripts/generate_stdlib_actions.py > db/schema/stdlib_actions.sql
```

**Checklist**:
- [ ] All Contact actions have full implementations
- [ ] All PublicAddress actions compile
- [ ] Actions follow FraiseQL standard (mutation_result)
- [ ] Trinity resolution works correctly

---

## PHASE 5: FraiseQL Metadata for Rich Types (Team D)

**Objective**: Generate correct GraphQL scalar definitions for rich types

**Estimated Time**: 3-4 hours

### TDD Cycle 5.1: Generate GraphQL scalar for Email

#### 🔴 RED: Write failing test for Email scalar
**Test file**: `tests/unit/fraiseql/test_rich_type_graphql_scalars.py`

```python
def test_generate_email_graphql_scalar():
    """Email rich type should generate GraphQL Email scalar"""
    field = FieldDef(name='email_address', type_name='email')

    graphql_type = get_graphql_type(field)

    assert graphql_type == 'Email'  # FraiseQL scalar name
```

**Expected failure**: Returns 'String' instead of 'Email'

#### 🟢 GREEN: Implement GraphQL scalar mapping
**Files to modify**:
- `src/generators/fraiseql/type_mapper.py` - Map rich types to GraphQL scalars

**Minimal implementation**:
```python
from src.core.scalar_types import is_scalar_type, get_scalar_type

def get_graphql_type(field: FieldDef) -> str:
    if is_scalar_type(field.type_name):
        scalar_def = get_scalar_type(field.type_name)
        return scalar_def.fraiseql_scalar_name  # e.g., 'Email'

    # ... existing logic for basic types ...
```

**Run test**: `uv run pytest tests/unit/fraiseql/test_rich_type_graphql_scalars.py::test_generate_email_graphql_scalar -v`

#### 🔧 REFACTOR: Generate scalar type definitions
- Generate GraphQL scalar type definitions file
- Add validation logic for each scalar
- Document each scalar in GraphQL schema

#### ✅ QA: All rich type GraphQL scalars
```bash
uv run pytest tests/unit/fraiseql/ -k scalar -v

# Generate GraphQL scalar definitions
uv run python scripts/generate_graphql_scalars.py > frontend/graphql/scalars.graphql
```

**Checklist**:
- [ ] All rich types map to GraphQL scalars
- [ ] Scalar definitions generated
- [ ] FraiseQL annotations include scalar info
- [ ] Frontend can use custom scalars

---

### TDD Cycle 5.2: Generate mutation impacts with rich types

#### 🔴 RED: Write test for mutation impact with email
**Test file**: `tests/integration/fraiseql/test_rich_type_mutation_impacts.py`

```python
def test_generate_mutation_impact_with_email_field():
    """Mutation impact metadata should include Email scalar type"""
    action = ActionDef(name='update_email', ...)
    entity = EntityDef(name='Contact', fields={'email_address': email_field})

    impact = generate_mutation_impact(action, entity)

    # Impact should specify Email scalar
    assert impact['fields']['email_address']['type'] == 'Email'
```

**Expected failure**: Returns 'String' instead of 'Email'

#### 🟢 GREEN: Update mutation impact generator
**Files to modify**:
- `src/generators/frontend/mutation_impacts_generator.py` - Use GraphQL type mapper

**Run test**: `uv run pytest tests/integration/fraiseql/test_rich_type_mutation_impacts.py::test_generate_mutation_impact_with_email_field -v`

#### 🔧 REFACTOR: Complete mutation impact metadata
- Include validation rules in metadata
- Add example values from scalar type definitions
- Generate TypeScript types with custom scalars

#### ✅ QA: Full mutation impact generation
```bash
uv run pytest tests/integration/fraiseql/ -k impact -v

# Generate mutation impacts for stdlib
uv run python scripts/generate_stdlib_impacts.py > frontend/generated/stdlib_impacts.json
```

**Checklist**:
- [ ] Mutation impacts include rich type info
- [ ] TypeScript types use custom scalars
- [ ] Frontend receives validation metadata
- [ ] All FraiseQL tests pass

---

## PHASE 6: CLI Integration & Documentation

**Objective**: Enable CLI to generate stdlib entities and document usage

**Estimated Time**: 2-3 hours

### TDD Cycle 6.1: CLI generate command for stdlib

#### 🔴 RED: Write test for CLI stdlib generation
**Test file**: `tests/unit/cli/test_stdlib_generation.py`

```python
def test_cli_generate_stdlib_entity():
    """CLI should generate schema from stdlib entity"""
    result = run_cli(['generate', 'stdlib/crm/contact.yaml'])

    assert result.exit_code == 0
    assert 'Generated schema for Contact' in result.output
```

**Expected failure**: CLI doesn't recognize stdlib/ paths

#### 🟢 GREEN: Update CLI to support stdlib paths
**Files to modify**:
- `src/cli/generate.py` - Resolve stdlib/ paths

**Run test**: `uv run pytest tests/unit/cli/test_stdlib_generation.py::test_cli_generate_stdlib_entity -v`

#### 🔧 REFACTOR: Add stdlib-specific commands
- `specql generate-stdlib` - Generate all stdlib entities
- `specql validate-stdlib` - Validate all stdlib entities
- `specql list-stdlib` - List available stdlib entities

#### ✅ QA: CLI stdlib integration
```bash
# Test CLI commands
specql generate stdlib/crm/contact.yaml
specql generate-stdlib --category=crm
specql validate-stdlib
specql list-stdlib
```

**Checklist**:
- [ ] CLI generates stdlib entities
- [ ] Stdlib paths resolve correctly
- [ ] All CLI tests pass
- [ ] Help documentation updated

---

### TDD Cycle 6.2: Documentation and examples

#### 🔴 RED: Write test for generated documentation
**Test file**: `tests/unit/cli/test_stdlib_docs.py`

```python
def test_generate_stdlib_documentation():
    """CLI should generate markdown docs for stdlib"""
    result = run_cli(['docs', 'stdlib/crm/contact.yaml'])

    assert result.exit_code == 0
    assert '## Entity: Contact' in result.output
    assert '### Fields' in result.output
```

**Expected failure**: `docs` command doesn't exist or doesn't support stdlib

#### 🟢 GREEN: Implement docs generation
**Files to modify**:
- `src/cli/docs.py` - Add stdlib documentation support

#### 🔧 REFACTOR: Generate comprehensive docs
- Field type documentation with examples
- Action documentation with step-by-step logic
- Rich type usage examples

#### ✅ QA: Complete documentation
```bash
# Generate all stdlib docs
specql docs stdlib/ --output=docs/stdlib/

# Verify docs are complete and accurate
ls -la docs/stdlib/
```

**Checklist**:
- [ ] Documentation generated for all entities
- [ ] Rich type examples included
- [ ] Action logic documented
- [ ] README updated with stdlib usage

---

## PHASE 7: Migration & Deployment Scripts

**Objective**: Create deployment scripts for stdlib in production

**Estimated Time**: 2-3 hours

### TDD Cycle 7.1: Generate migration script

#### 🔴 RED: Write test for migration generation
**Test file**: `tests/unit/cli/test_stdlib_migration.py`

```python
def test_generate_stdlib_migration():
    """Generate PostgreSQL migration for stdlib"""
    result = run_cli(['generate-migration', 'stdlib/', '--output=migrations/'])

    assert result.exit_code == 0
    assert os.path.exists('migrations/002_stdlib.sql')
```

**Expected failure**: `generate-migration` command doesn't exist

#### 🟢 GREEN: Implement migration generator
**Files to create**:
- `src/cli/migrate.py` - Migration generation logic
- `scripts/generate_stdlib_migration.py` - Standalone script

**Migration script structure**:
```sql
-- Migration: 002_stdlib.sql
-- Description: SpecQL stdlib entities (30 entities)
-- Version: 1.1.0

BEGIN;

-- Framework schemas (if not exists)
CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS app;

-- Create entities in dependency order
\ir stdlib/i18n/country.sql
\ir stdlib/i18n/currency.sql
-- ... all 30 entities ...

COMMIT;
```

#### 🔧 REFACTOR: Add dependency resolution
- Automatically order entities by foreign key dependencies
- Detect circular dependencies
- Generate rollback scripts

#### ✅ QA: Migration deployment
```bash
# Generate migration
specql generate-migration stdlib/ --output=migrations/002_stdlib.sql

# Test migration
createdb test_stdlib
psql test_stdlib -f migrations/000_app_foundation.sql
psql test_stdlib -f migrations/002_stdlib.sql

# Verify all tables created
psql test_stdlib -c "\dt common.*"
psql test_stdlib -c "\dt tenant.*"
```

**Checklist**:
- [ ] Migration script generated
- [ ] Dependencies correctly ordered
- [ ] Migration deploys successfully
- [ ] Rollback script works

---

## PHASE 8: Performance & Production Readiness

**Objective**: Ensure stdlib generation is production-ready

**Estimated Time**: 3-4 hours

### TDD Cycle 8.1: Performance testing

#### 🔴 RED: Write performance test
**Test file**: `tests/performance/test_stdlib_generation_performance.py`

```python
def test_generate_all_stdlib_entities_performance():
    """Generate all 30 stdlib entities in under 5 seconds"""
    import time

    start = time.time()
    for entity_path in STDLIB_ENTITIES:
        entity = parse_specql_file(f'stdlib/{entity_path}')
        ddl = generate_complete_schema(entity)
    end = time.time()

    elapsed = end - start
    assert elapsed < 5.0, f"Generation took {elapsed:.2f}s (should be < 5s)"
```

**Expected failure**: Takes too long (> 5 seconds)

#### 🟢 GREEN: Optimize generation performance
**Optimizations**:
- Cache parsed entities
- Parallelize generation
- Optimize regex compilation

#### 🔧 REFACTOR: Add caching layer
- Cache scalar type lookups
- Cache parsed YAML
- Memoize expensive operations

#### ✅ QA: Performance benchmarks
```bash
# Run performance tests
uv run pytest tests/performance/ -v

# Profile generation
uv run python -m cProfile -o stdlib_gen.prof scripts/generate_stdlib_schema.py
python -m pstats stdlib_gen.prof
```

**Checklist**:
- [ ] All entities generate in < 5 seconds
- [ ] No performance regressions
- [ ] Memory usage acceptable
- [ ] Caching works correctly

---

### TDD Cycle 8.2: Production validation

#### 🔴 RED: Write production validation test
**Test file**: `tests/integration/test_stdlib_production_readiness.py`

```python
def test_stdlib_schema_matches_production():
    """Generated stdlib schema should match PrintOptim production patterns"""

    # Generate Contact entity
    contact_ddl = generate_entity_schema('stdlib/crm/contact.yaml')

    # Compare against known production schema
    production_contact = load_production_schema('contact')

    # Key patterns should match
    assert 'pk_contact INTEGER PRIMARY KEY' in contact_ddl
    assert 'email_address TEXT NOT NULL CHECK' in contact_ddl
    # ... more assertions ...
```

**Expected failure**: Generated schema differs from production

#### 🟢 GREEN: Align generated schema with production
**Adjustments**:
- Fix naming conventions
- Adjust constraint formats
- Match production index patterns

#### 🔧 REFACTOR: Add schema comparison tool
- Automated diff between generated and production
- Highlight breaking changes
- Generate migration paths

#### ✅ QA: Production deployment readiness
```bash
# Compare all entities
uv run python scripts/compare_with_production.py

# Generate production-ready schema
uv run python scripts/generate_stdlib_schema.py --production > db/schema/stdlib_production.sql

# Deploy to staging
psql staging_db -f db/schema/stdlib_production.sql
```

**Checklist**:
- [ ] Schema matches production patterns
- [ ] No breaking changes
- [ ] Staging deployment successful
- [ ] All validations pass

---

## Success Criteria Summary

### ✅ Phase Completion Checklist

- [ ] **Phase 1**: Parser validates all rich types used in stdlib
- [ ] **Phase 2**: Schema generator produces correct DDL for all rich types
- [ ] **Phase 3**: All 30 stdlib entities generate valid SQL
- [ ] **Phase 4**: Actions with rich types compile correctly
- [ ] **Phase 5**: FraiseQL metadata includes rich type info
- [ ] **Phase 6**: CLI supports stdlib generation and docs
- [ ] **Phase 7**: Migration scripts deploy successfully
- [ ] **Phase 8**: Performance and production validation pass

### 🎯 Final Deliverables

1. **Generated Code**:
   - `db/schema/stdlib_full.sql` - All 30 entities DDL
   - `db/schema/stdlib_actions.sql` - All action functions
   - `frontend/generated/stdlib_impacts.json` - Mutation metadata
   - `frontend/graphql/scalars.graphql` - GraphQL scalar definitions

2. **Tests**:
   - 100+ new tests for rich type handling
   - End-to-end tests for all 30 entities
   - Performance benchmarks

3. **Documentation**:
   - `docs/stdlib/README.md` - stdlib usage guide
   - `docs/stdlib/RICH_TYPES.md` - Rich type reference
   - Entity-specific docs for all 30 entities

4. **CLI Enhancements**:
   - `specql generate-stdlib` - Batch generation
   - `specql validate-stdlib` - Validation
   - `specql list-stdlib` - Entity browser

---

## Estimated Timeline

**Total Estimated Time**: 27-38 hours

| Phase | Description | Time |
|-------|-------------|------|
| 1 | Rich Type Parsing | 3-4h |
| 2 | PostgreSQL Generation | 6-8h |
| 3 | E2E Entity Tests | 4-6h |
| 4 | Action Compilation | 4-6h |
| 5 | FraiseQL Metadata | 3-4h |
| 6 | CLI & Documentation | 2-3h |
| 7 | Migration Scripts | 2-3h |
| 8 | Production Readiness | 3-4h |

**Recommended Schedule**: 4-5 days of focused development with TDD discipline

---

## Risk Mitigation

### Known Risks

1. **Rich Type Edge Cases**: Some stdlib entities may use rich types in unexpected ways
   - **Mitigation**: Comprehensive test coverage, validate against production

2. **Dependency Ordering**: 30 entities with complex foreign key relationships
   - **Mitigation**: Topological sort for dependency resolution, detect cycles early

3. **Performance**: Generating 30 entities with actions and metadata could be slow
   - **Mitigation**: Performance testing in Phase 8, optimize early if issues arise

4. **Production Alignment**: Generated schema must match PrintOptim production
   - **Mitigation**: Compare with production schemas, iterate until aligned

---

## Appendix: stdlib Entity Inventory

### Category: i18n (6 entities)
- Country (ISO 3166)
- Currency (ISO 4217)
- Language (ISO 639)
- Locale (BCP 47)
- Territory
- CurrencyFormat

### Category: geo (11 entities)
- PublicAddress ⭐ (coordinates rich type)
- Location ⭐ (coordinates rich type)
- Country
- AdministrativeUnit
- PostalCode
- StreetType
- AddressDatasource (url rich type)
- GeocodingResult
- Timezone
- Continent
- Region

### Category: crm (3 entities)
- Contact ⭐ (email, phone rich types)
- Organization ⭐ (hierarchical)
- Interaction

### Category: org (2 entities)
- OrganizationalUnit (hierarchical)
- Department

### Category: commerce (3 entities)
- Contract
- Order
- Price ⭐ (money rich type)

### Category: tech (2 entities)
- OperatingSystem
- Browser

### Category: time (1 entity)
- Calendar

### Category: common (2 entities)
- Genre
- Industry

**Legend**: ⭐ = High-priority for testing (uses advanced features)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Next Review**: After Phase 1 completion
