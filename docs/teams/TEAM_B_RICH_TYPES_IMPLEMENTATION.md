# Team B: Rich Types Implementation - Schema Generator Extension

**Epic**: Add FraiseQL Rich Type Support to Schema Generator
**Timeline**: Week 2, Days 2-3 (after Team A completes parser)
**Complexity**: Medium-High (DDL generation with constraints)

---

## 🎯 Objective

Extend the Schema Generator to create PostgreSQL DDL with appropriate storage types, CHECK constraints, and validation for FraiseQL rich types.

**Success Criteria**:
- ✅ Maps rich types to optimal PostgreSQL types
- ✅ Generates CHECK constraints for validated types (email, url, phone)
- ✅ Uses PostgreSQL native types where available (INET, MACADDR, UUID)
- ✅ Generates indexes appropriate for rich types
- ✅ Maintains backward compatibility
- ✅ Generated SQL is valid and efficient
- ✅ 90%+ test coverage

---

## 📋 PHASE 1: Type Mapping & Basic DDL Generation

**Duration**: 3 hours

### 🔴 RED Phase: Write Failing Tests

**Test File**: `tests/unit/schema/test_rich_type_ddl.py`

```python
import pytest
from src.generators.schema.schema_generator import SchemaGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_generates_text_with_constraint():
    """Test: email type generates TEXT with CHECK constraint"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type="email", nullable=False)
        }
    )

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(entity.fields["email"], entity)

    # Expected: TEXT with email validation
    assert "email TEXT NOT NULL" in ddl
    assert "CHECK" in ddl
    assert "~*" in ddl  # Regex operator
    assert "@" in ddl   # Email pattern


def test_url_field_generates_text_with_url_constraint():
    """Test: url type generates TEXT with URL validation"""
    field = FieldDefinition(name="website", type="url", nullable=True)

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "website TEXT" in ddl
    assert "CHECK" in ddl
    assert "https?" in ddl


def test_ip_address_uses_inet_type():
    """Test: ipAddress type uses PostgreSQL INET (no CHECK needed)"""
    field = FieldDefinition(name="ip_address", type="ipAddress")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    # Expected: PostgreSQL INET type (built-in validation)
    assert "ip_address INET" in ddl
    assert "CHECK" not in ddl  # INET has built-in validation


def test_mac_address_uses_macaddr_type():
    """Test: macAddress type uses PostgreSQL MACADDR"""
    field = FieldDefinition(name="mac", type="macAddress")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "mac MACADDR" in ddl
    assert "CHECK" not in ddl  # MACADDR has built-in validation


def test_coordinates_generates_point_with_constraint():
    """Test: coordinates type generates POINT with lat/lng validation"""
    field = FieldDefinition(name="location", type="coordinates")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    # Expected: POINT type with bounds check
    assert "location POINT" in ddl
    assert "CHECK" in ddl
    # Latitude: -90 to 90, Longitude: -180 to 180
    assert "-90" in ddl and "90" in ddl
    assert "-180" in ddl and "180" in ddl


def test_money_generates_numeric_with_precision():
    """Test: money type generates NUMERIC(19,4)"""
    field = FieldDefinition(name="price", type="money", nullable=False)

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "price NUMERIC(19,4) NOT NULL" in ddl


def test_money_with_metadata_uses_custom_precision():
    """Test: money(precision=2) generates NUMERIC(19,2)"""
    field = FieldDefinition(
        name="price",
        type="money",
        type_metadata={"precision": 2}
    )

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "price NUMERIC(19,2)" in ddl


def test_phone_number_generates_text_with_e164_constraint():
    """Test: phoneNumber type generates TEXT with E.164 validation"""
    field = FieldDefinition(name="phone", type="phoneNumber")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "phone TEXT" in ddl
    assert "CHECK" in ddl
    # E.164 format: +[1-9][0-9]{1,14}
    assert r"\+?" in ddl or "+" in ddl


def test_color_generates_text_with_hex_constraint():
    """Test: color type generates TEXT with hex code validation"""
    field = FieldDefinition(name="theme_color", type="color")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "theme_color TEXT" in ddl
    assert "CHECK" in ddl
    assert "#" in ddl
    assert "[0-9A-Fa-f]" in ddl


def test_slug_generates_text_with_url_safe_constraint():
    """Test: slug type generates TEXT with lowercase-hyphen validation"""
    field = FieldDefinition(name="slug", type="slug")

    generator = SchemaGenerator()
    ddl = generator.generate_field_ddl(field, None)

    assert "slug TEXT" in ddl
    assert "CHECK" in ddl
    assert "[a-z0-9]" in ddl
    assert "[-]" in ddl or "-" in ddl


def test_complete_table_with_multiple_rich_types():
    """Test: Generate complete table with multiple rich types"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type="email", nullable=False),
            "website": FieldDefinition(name="website", type="url"),
            "phone": FieldDefinition(name="phone", type="phoneNumber"),
            "ip_address": FieldDefinition(name="ip_address", type="ipAddress"),
            "first_name": FieldDefinition(name="first_name", type="text"),
        }
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table_ddl(entity)

    # Verify table structure
    assert "CREATE TABLE crm.tb_contact" in ddl

    # Verify Trinity pattern (Team B's existing functionality)
    assert "pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in ddl
    assert "id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE" in ddl
    assert "identifier TEXT UNIQUE" in ddl

    # Verify rich type fields
    assert "email TEXT NOT NULL CHECK" in ddl
    assert "website TEXT CHECK" in ddl
    assert "phone TEXT CHECK" in ddl
    assert "ip_address INET" in ddl

    # Verify basic type (backward compatibility)
    assert "first_name TEXT" in ddl


def test_backward_compatibility_basic_types():
    """Test: Existing basic types still work correctly"""
    entity = Entity(
        name="Product",
        schema="sales",
        fields={
            "name": FieldDefinition(name="name", type="text", nullable=False),
            "quantity": FieldDefinition(name="quantity", type="integer"),
            "active": FieldDefinition(name="active", type="boolean"),
            "metadata": FieldDefinition(name="metadata", type="jsonb"),
        }
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "name TEXT NOT NULL" in ddl
    assert "quantity INTEGER" in ddl
    assert "active BOOLEAN" in ddl
    assert "metadata JSONB" in ddl
```

**Run Tests**:
```bash
uv run pytest tests/unit/schema/test_rich_type_ddl.py -v
# Expected: FAILED (not implemented)
```

---

### 🟢 GREEN Phase: Minimal Implementation

**File**: `src/generators/schema/rich_type_mapper.py`

```python
"""
Rich Type Mapper
Maps FraiseQL rich types to PostgreSQL DDL with constraints
"""

from dataclasses import dataclass
from typing import Optional
from src.core.ast_models import FieldDefinition
from src.core.type_registry import get_type_registry


@dataclass
class FieldDDL:
    """PostgreSQL field DDL components"""
    column_name: str
    data_type: str
    nullable: bool
    default: Optional[str] = None
    check_constraint: Optional[str] = None


class RichTypeMapper:
    """Maps rich types to PostgreSQL DDL"""

    def __init__(self):
        self.type_registry = get_type_registry()

    def map_field_to_ddl(self, field: FieldDefinition) -> FieldDDL:
        """Map field definition to PostgreSQL DDL components"""

        # Get base PostgreSQL type
        pg_type = field.get_postgres_type()

        # Get CHECK constraint if needed
        check_constraint = self._generate_check_constraint(field)

        # Format default value
        default = self._format_default(field.default) if field.default else None

        return FieldDDL(
            column_name=field.name,
            data_type=pg_type,
            nullable=field.nullable,
            default=default,
            check_constraint=check_constraint
        )

    def _generate_check_constraint(self, field: FieldDefinition) -> Optional[str]:
        """Generate CHECK constraint for validated rich types"""

        if not field.is_rich_type():
            return None

        # Get validation pattern from type registry
        pattern = field.get_validation_pattern()
        if not pattern:
            # Some types have built-in validation (INET, MACADDR, UUID)
            return None

        # Generate regex CHECK constraint
        return f"{field.name} ~* '{pattern}'"

    def _format_default(self, default_value: any) -> str:
        """Format default value for SQL"""
        if isinstance(default_value, str):
            return f"'{default_value}'"
        elif isinstance(default_value, bool):
            return str(default_value).upper()
        else:
            return str(default_value)

    def generate_special_constraints(self, field: FieldDefinition) -> Optional[str]:
        """Generate special constraints for specific rich types"""

        if field.type == "coordinates":
            # POINT type: validate latitude/longitude bounds
            return (
                f"{field.name}[0] BETWEEN -90 AND 90 AND "
                f"{field.name}[1] BETWEEN -180 AND 180"
            )

        elif field.type == "latitude":
            return f"{field.name} BETWEEN -90 AND 90"

        elif field.type == "longitude":
            return f"{field.name} BETWEEN -180 AND 180"

        elif field.type == "percentage":
            return f"{field.name} BETWEEN 0 AND 100"

        return None
```

---

**File**: `src/generators/schema/schema_generator.py`

```python
"""
Schema Generator with Rich Type Support
"""

from typing import List
from src.core.ast_models import Entity, FieldDefinition
from src.generators.schema.rich_type_mapper import RichTypeMapper, FieldDDL


class SchemaGenerator:
    """Generates PostgreSQL DDL with rich type support"""

    def __init__(self):
        self.rich_type_mapper = RichTypeMapper()

    def generate_table_ddl(self, entity: Entity) -> str:
        """Generate complete CREATE TABLE statement"""

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Start DDL
        ddl_parts = [f"CREATE TABLE {table_name} ("]

        # Trinity pattern (existing Team B code)
        ddl_parts.extend(self._generate_trinity_fields(entity))

        # Business fields with rich type support
        for field_name, field_def in entity.fields.items():
            field_ddl = self.generate_field_ddl(field_def, entity)
            ddl_parts.append(f"    {field_ddl},")

        # Audit fields (existing Team B code)
        ddl_parts.extend(self._generate_audit_fields())

        # Close table
        ddl_parts.append(");")

        return "\n".join(ddl_parts)

    def generate_field_ddl(self, field: FieldDefinition, entity: Entity) -> str:
        """Generate DDL for a single field with rich type support"""

        # Map to PostgreSQL DDL
        field_ddl = self.rich_type_mapper.map_field_to_ddl(field)

        # Build field definition
        parts = [field_ddl.column_name, field_ddl.data_type]

        # NULL constraint
        if not field_ddl.nullable:
            parts.append("NOT NULL")

        # Default value
        if field_ddl.default:
            parts.append(f"DEFAULT {field_ddl.default}")

        # CHECK constraint (for validated rich types)
        if field_ddl.check_constraint:
            parts.append(f"CHECK ({field_ddl.check_constraint})")

        # Special constraints (coordinates, percentage, etc.)
        special_constraint = self.rich_type_mapper.generate_special_constraints(field)
        if special_constraint:
            parts.append(f"CHECK ({special_constraint})")

        return " ".join(parts)

    def _generate_trinity_fields(self, entity: Entity) -> List[str]:
        """Generate Trinity pattern fields (existing code)"""
        entity_lower = entity.name.lower()
        return [
            f"    pk_{entity_lower} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,",
            f"    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,",
            f"    identifier TEXT UNIQUE,",
        ]

    def _generate_audit_fields(self) -> List[str]:
        """Generate audit fields (existing code)"""
        return [
            "    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),",
            "    created_by UUID,",
            "    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),",
            "    updated_by UUID,",
            "    deleted_at TIMESTAMPTZ",
        ]
```

---

### 🔧 REFACTOR Phase

**Improvements**:

1. **Extract constraint generators**:

```python
class ConstraintGenerator:
    """Generates CHECK constraints for rich types"""

    def generate_email_constraint(self, field_name: str) -> str:
        """Generate email validation constraint"""
        # RFC 5322 compliant pattern (simplified)
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
        return f"{field_name} ~* '{pattern}'"

    def generate_url_constraint(self, field_name: str) -> str:
        """Generate URL validation constraint"""
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return f"{field_name} ~* '{pattern}'"

    # ... other constraint generators
```

2. **Add constraint naming**:

```python
def generate_constraint_name(self, table_name: str, field_name: str, constraint_type: str) -> str:
    """Generate consistent constraint names"""
    return f"chk_{table_name}_{field_name}_{constraint_type}"
```

3. **Optimize constraint patterns**:

```python
# Use PostgreSQL domain types for reusable constraints
CREATE DOMAIN email_address AS TEXT
    CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');
```

---

### ✅ QA Phase

```bash
# Unit tests
uv run pytest tests/unit/schema/test_rich_type_ddl.py -v

# Integration test with real PostgreSQL
uv run pytest tests/integration/schema/test_rich_types_postgres.py -v

# Backward compatibility
uv run pytest tests/unit/schema/ -v

# Coverage
uv run pytest tests/unit/schema/ --cov=src/generators/schema/ --cov-report=term-missing
# Target: 90%+
```

---

## 📋 PHASE 2: Index Generation for Rich Types

**Duration**: 1 hour

### 🔴 RED Phase

```python
def test_email_field_gets_btree_index():
    """Test: Email fields get efficient indexes"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type="email", nullable=False)
        }
    )

    generator = SchemaGenerator()
    indexes = generator.generate_indexes(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_contact_email" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_url_field_gets_gin_index_for_pattern_search():
    """Test: URL fields get GIN index for pattern matching"""
    entity = Entity(
        name="Page",
        fields={
            "url": FieldDefinition(name="url", type="url")
        }
    )

    generator = SchemaGenerator()
    indexes = generator.generate_indexes(entity)

    # Expected: GIN index for LIKE/regex searches
    assert any("idx_page_url" in idx for idx in indexes)
    assert any("gin" in idx.lower() for idx in indexes)


def test_coordinates_field_gets_gist_index():
    """Test: Coordinates field gets GiST index for spatial queries"""
    entity = Entity(
        name="Location",
        fields={
            "coordinates": FieldDefinition(name="coordinates", type="coordinates")
        }
    )

    generator = SchemaGenerator()
    indexes = generator.generate_indexes(entity)

    # Expected: GiST index for spatial operations
    assert any("idx_location_coordinates" in idx for idx in indexes)
    assert any("gist" in idx.lower() for idx in indexes)
```

### 🟢 GREEN Phase

```python
class IndexGenerator:
    """Generates indexes appropriate for rich types"""

    def generate_indexes_for_field(self, field: FieldDefinition, entity: Entity) -> List[str]:
        """Generate indexes based on field type"""

        indexes = []
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        if field.type == "email":
            # B-tree for exact lookups
            indexes.append(
                f"CREATE INDEX idx_{entity.name.lower()}_{field.name} "
                f"ON {table_name} ({field.name});"
            )

        elif field.type == "url":
            # GIN for pattern matching
            indexes.append(
                f"CREATE INDEX idx_{entity.name.lower()}_{field.name} "
                f"ON {table_name} USING gin ({field.name} gin_trgm_ops);"
            )

        elif field.type in ("coordinates", "latitude", "longitude"):
            # GiST for spatial queries
            indexes.append(
                f"CREATE INDEX idx_{entity.name.lower()}_{field.name} "
                f"ON {table_name} USING gist ({field.name});"
            )

        elif field.type == "ipAddress":
            # GiST for network operations (contains, overlaps)
            indexes.append(
                f"CREATE INDEX idx_{entity.name.lower()}_{field.name} "
                f"ON {table_name} USING gist ({field.name} inet_ops);"
            )

        return indexes
```

---

## 📋 PHASE 3: Integration Testing

**Duration**: 1 hour

### Integration Tests

**File**: `tests/integration/schema/test_rich_types_postgres.py`

```python
import pytest
import psycopg2
from src.generators.schema.schema_generator import SchemaGenerator
from src.core.ast_models import Entity, FieldDefinition


@pytest.fixture
def db_connection():
    """PostgreSQL test database connection"""
    conn = psycopg2.connect("postgresql://localhost/test_specql")
    yield conn
    conn.close()


def test_email_constraint_accepts_valid_emails(db_connection):
    """Integration: Email constraint accepts valid emails"""
    entity = Entity(
        name="Contact",
        schema="public",
        fields={
            "email": FieldDefinition(name="email", type="email", nullable=False)
        }
    )

    # Generate and apply DDL
    generator = SchemaGenerator()
    ddl = generator.generate_table_ddl(entity)

    cursor = db_connection.cursor()
    cursor.execute(ddl)

    # Test valid emails
    valid_emails = [
        "user@example.com",
        "test.user@example.co.uk",
        "admin+tag@company.org"
    ]

    for email in valid_emails:
        cursor.execute(
            "INSERT INTO public.tb_contact (email) VALUES (%s)",
            (email,)
        )
        # Should succeed
        db_connection.commit()


def test_email_constraint_rejects_invalid_emails(db_connection):
    """Integration: Email constraint rejects invalid emails"""
    # ... DDL setup ...

    invalid_emails = [
        "not-an-email",
        "@example.com",
        "user@",
        "user@domain"
    ]

    cursor = db_connection.cursor()
    for email in invalid_emails:
        with pytest.raises(psycopg2.errors.CheckViolation):
            cursor.execute(
                "INSERT INTO public.tb_contact (email) VALUES (%s)",
                (email,)
            )
            db_connection.commit()
        db_connection.rollback()


def test_inet_type_validates_ip_addresses(db_connection):
    """Integration: INET type validates IP addresses"""
    entity = Entity(
        name="Server",
        schema="public",
        fields={
            "ip_address": FieldDefinition(name="ip_address", type="ipAddress")
        }
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table_ddl(entity)

    cursor = db_connection.cursor()
    cursor.execute(ddl)

    # Valid IP addresses
    valid_ips = ["192.168.1.1", "10.0.0.1", "2001:0db8:85a3::8a2e:0370:7334"]
    for ip in valid_ips:
        cursor.execute(
            "INSERT INTO public.tb_server (ip_address) VALUES (%s)",
            (ip,)
        )
        db_connection.commit()

    # Invalid IP
    with pytest.raises(psycopg2.errors.InvalidTextRepresentation):
        cursor.execute(
            "INSERT INTO public.tb_server (ip_address) VALUES (%s)",
            ("not-an-ip",)
        )
```

---

## 📊 Acceptance Criteria

### Must Have
- ✅ All rich types map to correct PostgreSQL types
- ✅ CHECK constraints generated for validated types
- ✅ Native types used where available (INET, MACADDR, UUID)
- ✅ Constraints accept valid values
- ✅ Constraints reject invalid values
- ✅ Appropriate indexes generated
- ✅ Backward compatible with existing types
- ✅ All tests pass (unit + integration)
- ✅ 90%+ test coverage

### Nice to Have
- ✅ Optimized regex patterns for constraints
- ✅ Named constraints for better error messages
- ✅ PostgreSQL DOMAIN types for reusable constraints
- ✅ Performance benchmarks for constraint validation

---

## 🎯 Definition of Done

- [ ] `RichTypeMapper` class created
- [ ] `ConstraintGenerator` class created
- [ ] `IndexGenerator` updated for rich types
- [ ] All rich types generate correct DDL
- [ ] CHECK constraints validate correctly
- [ ] Integration tests pass with real PostgreSQL
- [ ] Backward compatibility verified
- [ ] 90%+ code coverage
- [ ] Documentation updated
- [ ] Examples added
- [ ] Performance tested
- [ ] Code reviewed
- [ ] Merged to main

---

## 📚 PostgreSQL Type Mappings Reference

| Rich Type | PostgreSQL | Constraint Type | Index Type |
|-----------|-----------|----------------|------------|
| email | TEXT | CHECK (regex) | btree |
| url | TEXT | CHECK (regex) | gin |
| phone | TEXT | CHECK (regex) | btree |
| ipAddress | INET | Built-in | gist |
| macAddress | MACADDR | Built-in | btree |
| coordinates | POINT | CHECK (bounds) | gist |
| money | NUMERIC(19,4) | None | btree |
| date | DATE | Built-in | btree |
| uuid | UUID | Built-in | btree |
| slug | TEXT | CHECK (regex) | btree |
| color | TEXT | CHECK (hex) | btree |

---

**Team B: Schema generation with rich types ready to implement!** 🚀

This provides everything Team B needs to generate production-ready PostgreSQL schemas with FraiseQL rich type support.
