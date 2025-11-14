# Week 15: Rust Code Generation - DETAILED IMPLEMENTATION PLAN

**Date**: TBD (After Week 14 completion)
**Duration**: 5 days
**Status**: 📅 Planned - Ready for Detailed Execution
**Objective**: Generate production-ready Rust/Diesel code from SpecQL entity definitions
**Complexity**: COMPLEX - Phased TDD Approach Required

**Prerequisites**:
- Week 14 complete (Rust Pattern Recognition with 98% test coverage)
- Rust parser binary built (`rust/target/release/specql_rust_parser`)
- Understanding of Diesel ORM patterns

**Output**:
- Complete Rust/Diesel code generator
- Diesel `schema.rs` generation
- Rust struct definitions with derives
- Actix Web/Axum route handlers
- Diesel query builders and business logic
- Comprehensive test suite (95%+ coverage)
- CLI integration (`specql generate --target rust`)

---

## 🎯 Executive Summary

Week 15 completes the **reverse direction** of the Rust pipeline established in Week 14:

**Week 14 (Reverse Engineering)**: Rust Code → SpecQL YAML
**Week 15 (Code Generation)**: SpecQL YAML → Rust Code

This enables the full bidirectional workflow:
1. **Greenfield**: Write SpecQL → Generate Rust/Diesel backend
2. **Brownfield**: Parse existing Rust → Modify SpecQL → Regenerate Rust
3. **Migration**: Parse Django/Rails → Generate as Rust instead

### Strategic Context

Rust generation is critical for SpecQL's multi-language moat:
- **Performance**: Rust backends for high-throughput APIs
- **Safety**: Type-safe database access with compile-time guarantees
- **Modern Stack**: Diesel + Actix/Axum = production-grade architecture
- **Framework Parity**: Equivalent quality to PostgreSQL, Python Django, Java Spring

### What Gets Generated

From a single SpecQL entity definition, generate:

```yaml
# entities/contact.yaml
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)
```

↓ Generates ↓

1. **`schema.rs`** (Diesel table definitions)
2. **`models.rs`** (Rust structs with Diesel derives)
3. **`handlers.rs`** (Actix Web/Axum route handlers)
4. **`queries.rs`** (Diesel query builders)
5. **`lib.rs`** (Module structure and exports)

### Success Criteria

By end of Week 15:
- [ ] Diesel `schema.rs` generated for all entities
- [ ] Rust structs with correct Diesel derives (Queryable, Insertable)
- [ ] Type mappings for all SpecQL types (including Trinity pattern)
- [ ] Foreign key relationships mapped correctly
- [ ] Enum types generated
- [ ] Actix Web OR Axum handlers (user choice)
- [ ] Basic CRUD query builders
- [ ] CLI command: `specql generate --target rust`
- [ ] 95%+ test coverage
- [ ] Generated code compiles with `cargo check`
- [ ] Integration test: Generate → Compile → Run

---

## 📊 Development Phases Overview

### Phase Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Week 15: 5 Major Phases                                          │
│                                                                   │
│ Phase 1: Diesel Schema Generation (Day 1)                        │
│ Phase 2: Rust Model Generation (Day 2)                           │
│ Phase 3: Query Builder Generation (Day 3)                        │
│ Phase 4: Handler Generation (Day 4)                              │
│ Phase 5: CLI Integration & End-to-End Testing (Day 5)            │
└─────────────────────────────────────────────────────────────────┘
```

Each phase follows strict TDD discipline: RED → GREEN → REFACTOR → QA

---

## 🔴 PHASE 1: Diesel Schema Generation (Day 1)

**Objective**: Generate Diesel `schema.rs` with table! macros from SpecQL entities

**Estimated Duration**: 8 hours
**Files Created**: ~8 files, ~1,200 lines
**Test Coverage Target**: 95%+

### Technical Context

Diesel's `schema.rs` is the single source of truth for database schema. It uses the `table!` macro:

```rust
// Generated schema.rs
diesel::table! {
    crm.tb_contact (pk_contact) {
        pk_contact -> Int4,
        id -> Uuid,
        email -> Varchar,
        fk_company -> Nullable<Int4>,
        status -> Varchar,
        created_at -> Timestamptz,
        created_by -> Nullable<Uuid>,
        updated_at -> Timestamptz,
        updated_by -> Nullable<Uuid>,
        deleted_at -> Nullable<Timestamptz>,
        deleted_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    crm.tb_company (pk_company) {
        pk_company -> Int4,
        id -> Uuid,
        name -> Varchar,
        // ... audit fields
    }
}

diesel::joinable!(tb_contact -> tb_company (fk_company));
diesel::allow_tables_to_appear_in_same_query!(tb_contact, tb_company);
```

---

### Phase 1.1: Type Mapping System (2 hours)

**Objective**: Map SpecQL types to Diesel SQL types

#### TDD Cycle 1.1.1: Core Type Mapper

**🔴 RED: Type Mapper Tests (30 minutes)**

**File**: `tests/unit/generators/rust/test_diesel_type_mapper.py`

```python
"""
Tests for SpecQL → Diesel SQL type mapping

Diesel uses specific type names that map to PostgreSQL types.
These must be precise for schema generation.
"""

import pytest
from src.generators.rust.diesel_type_mapper import DieselTypeMapper, DieselSqlType


class TestDieselTypeMapper:
    """Test mapping SpecQL types to Diesel SQL types"""

    @pytest.fixture
    def mapper(self):
        return DieselTypeMapper()

    def test_map_integer_to_int4(self, mapper):
        """Test integer maps to Int4 (default)"""
        result = mapper.map_field_type("integer")

        assert result == DieselSqlType.INT4
        assert result.to_rust_string() == "Int4"

    def test_map_integer_big_to_int8(self, mapper):
        """Test integer:big maps to Int8"""
        result = mapper.map_field_type("integer:big")

        assert result == DieselSqlType.INT8
        assert result.to_rust_string() == "Int8"

    def test_map_integer_small_to_int2(self, mapper):
        """Test integer:small maps to Int2"""
        result = mapper.map_field_type("integer:small")

        assert result == DieselSqlType.INT2
        assert result.to_rust_string() == "Int2"

    def test_map_text_to_varchar(self, mapper):
        """Test text maps to Varchar"""
        result = mapper.map_field_type("text")

        assert result == DieselSqlType.VARCHAR
        assert result.to_rust_string() == "Varchar"

    def test_map_text_long_to_text(self, mapper):
        """Test text:long maps to Text (unlimited)"""
        result = mapper.map_field_type("text:long")

        assert result == DieselSqlType.TEXT
        assert result.to_rust_string() == "Text"

    def test_map_decimal_to_numeric(self, mapper):
        """Test decimal maps to Numeric"""
        result = mapper.map_field_type("decimal")

        assert result == DieselSqlType.NUMERIC
        assert result.to_rust_string() == "Numeric"

    def test_map_boolean_to_bool(self, mapper):
        """Test boolean maps to Bool"""
        result = mapper.map_field_type("boolean")

        assert result == DieselSqlType.BOOL
        assert result.to_rust_string() == "Bool"

    def test_map_timestamp_to_timestamptz(self, mapper):
        """Test timestamp maps to Timestamptz (with timezone)"""
        result = mapper.map_field_type("timestamp")

        assert result == DieselSqlType.TIMESTAMPTZ
        assert result.to_rust_string() == "Timestamptz"

    def test_map_uuid_to_uuid(self, mapper):
        """Test uuid maps to Uuid"""
        result = mapper.map_field_type("uuid")

        assert result == DieselSqlType.UUID
        assert result.to_rust_string() == "Uuid"

    def test_map_json_to_jsonb(self, mapper):
        """Test json maps to Jsonb (binary JSON)"""
        result = mapper.map_field_type("json")

        assert result == DieselSqlType.JSONB
        assert result.to_rust_string() == "Jsonb"

    def test_map_enum_to_varchar(self, mapper):
        """Test enum maps to Varchar (stored as text)"""
        result = mapper.map_field_type("enum")

        assert result == DieselSqlType.VARCHAR
        assert result.to_rust_string() == "Varchar"

    def test_map_vector_to_custom_type(self, mapper):
        """Test vector maps to custom Vector type"""
        result = mapper.map_field_type("vector")

        assert result == DieselSqlType.VECTOR
        assert result.to_rust_string() == "Vector"

    def test_nullable_field(self, mapper):
        """Test optional field becomes Nullable<Type>"""
        result = mapper.map_field_type("text", required=False)

        assert result.to_rust_string() == "Nullable<Varchar>"

    def test_reference_field_maps_to_int4(self, mapper):
        """Test ref fields map to Int4 (foreign keys)"""
        result = mapper.map_field_type("ref", ref_entity="Company")

        assert result == DieselSqlType.INT4
        assert result.to_rust_string() == "Int4"

    def test_optional_reference_is_nullable(self, mapper):
        """Test optional ref becomes Nullable<Int4>"""
        result = mapper.map_field_type("ref", ref_entity="Company", required=False)

        assert result.to_rust_string() == "Nullable<Int4>"

    def test_array_type_mapping(self, mapper):
        """Test array types map to Array<Type>"""
        result = mapper.map_field_type("text[]")

        assert result.to_rust_string() == "Array<Varchar>"

    def test_unknown_type_raises_error(self, mapper):
        """Test unknown types raise descriptive error"""
        with pytest.raises(ValueError, match="Unknown SpecQL type"):
            mapper.map_field_type("unknown_type")

    def test_trinity_pattern_fields(self, mapper):
        """Test Trinity pattern audit fields map correctly"""
        trinity_fields = {
            "pk_contact": ("integer:big", True),
            "id": ("uuid", True),
            "created_at": ("timestamp", True),
            "created_by": ("uuid", False),
            "updated_at": ("timestamp", True),
            "updated_by": ("uuid", False),
            "deleted_at": ("timestamp", False),
            "deleted_by": ("uuid", False),
        }

        for field_name, (field_type, required) in trinity_fields.items():
            result = mapper.map_field_type(field_type, required=required)
            # Verify each maps correctly
            assert result is not None
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_diesel_type_mapper.py -v
# Expected: ModuleNotFoundError (RED phase - this is correct!)
```

**🟢 GREEN: Implement Type Mapper (45 minutes)**

**File**: `src/generators/rust/diesel_type_mapper.py`

```python
"""
Diesel Type Mapper

Maps SpecQL field types to Diesel SQL types for schema.rs generation.

Diesel Type Reference:
- https://docs.diesel.rs/master/diesel/sql_types/index.html
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DieselSqlType(Enum):
    """
    Diesel SQL type identifiers

    These correspond to Diesel's sql_types module.
    Each type has specific Rust and PostgreSQL equivalents.
    """
    # Integer types
    INT2 = "Int2"           # smallint (16-bit)
    INT4 = "Int4"           # integer (32-bit) - most common
    INT8 = "Int8"           # bigint (64-bit)

    # Decimal types
    NUMERIC = "Numeric"     # numeric/decimal with arbitrary precision
    FLOAT4 = "Float4"       # real (32-bit float)
    FLOAT8 = "Float8"       # double precision (64-bit float)

    # Text types
    VARCHAR = "Varchar"     # variable-length string (most common)
    TEXT = "Text"           # unlimited text

    # Boolean
    BOOL = "Bool"

    # Date/Time
    DATE = "Date"
    TIME = "Time"
    TIMESTAMP = "Timestamp"
    TIMESTAMPTZ = "Timestamptz"  # With timezone (recommended)

    # UUID
    UUID = "Uuid"

    # JSON
    JSON = "Json"
    JSONB = "Jsonb"         # Binary JSON (recommended)

    # Arrays
    ARRAY = "Array"

    # Binary
    BYTEA = "Bytea"

    # Custom types (require setup)
    VECTOR = "Vector"       # pgvector extension

    def to_rust_string(self) -> str:
        """Get the Rust string representation for schema.rs"""
        return self.value


@dataclass
class DieselFieldType:
    """
    Represents a complete Diesel field type with nullability

    Example:
        - Int4 (required integer)
        - Nullable<Varchar> (optional text)
        - Array<Int4> (array of integers)
    """
    base_type: DieselSqlType
    is_nullable: bool = False
    is_array: bool = False

    def to_rust_string(self) -> str:
        """
        Generate the complete Diesel type string

        Returns:
            String like "Int4", "Nullable<Varchar>", "Array<Int4>"
        """
        type_str = self.base_type.value

        if self.is_array:
            type_str = f"Array<{type_str}>"

        if self.is_nullable:
            type_str = f"Nullable<{type_str}>"

        return type_str


class DieselTypeMapper:
    """
    Maps SpecQL types to Diesel SQL types

    Handles:
    - Basic type mapping (text → Varchar)
    - Subtype refinement (integer:big → Int8)
    - Nullability (required=False → Nullable<T>)
    - Arrays (text[] → Array<Varchar>)
    - References (ref → Int4 for foreign keys)

    Example:
        mapper = DieselTypeMapper()

        # Basic mapping
        mapper.map_field_type("text")  # → Varchar

        # With subtype
        mapper.map_field_type("integer:big")  # → Int8

        # Nullable
        mapper.map_field_type("text", required=False)  # → Nullable<Varchar>

        # Reference
        mapper.map_field_type("ref", ref_entity="Company")  # → Int4
    """

    # Core type mappings (without subtypes)
    TYPE_MAP = {
        "integer": DieselSqlType.INT4,      # Default integer size
        "decimal": DieselSqlType.NUMERIC,
        "text": DieselSqlType.VARCHAR,
        "boolean": DieselSqlType.BOOL,
        "timestamp": DieselSqlType.TIMESTAMPTZ,
        "date": DieselSqlType.DATE,
        "time": DieselSqlType.TIME,
        "uuid": DieselSqlType.UUID,
        "json": DieselSqlType.JSONB,
        "binary": DieselSqlType.BYTEA,
        "enum": DieselSqlType.VARCHAR,      # Enums stored as text
        "vector": DieselSqlType.VECTOR,
        "ref": DieselSqlType.INT4,          # Foreign keys are int4
    }

    # Subtype refinements
    SUBTYPE_MAP = {
        "integer:small": DieselSqlType.INT2,
        "integer:int": DieselSqlType.INT4,
        "integer:big": DieselSqlType.INT8,
        "text:tiny": DieselSqlType.VARCHAR,
        "text:short": DieselSqlType.VARCHAR,
        "text:long": DieselSqlType.TEXT,
        "decimal:money": DieselSqlType.NUMERIC,
        "decimal:percent": DieselSqlType.NUMERIC,
        "decimal:geo": DieselSqlType.NUMERIC,
    }

    def map_field_type(
        self,
        field_type: str,
        required: bool = True,
        ref_entity: Optional[str] = None
    ) -> DieselFieldType:
        """
        Map SpecQL field type to Diesel SQL type

        Args:
            field_type: SpecQL type (e.g., "text", "integer:big", "text[]")
            required: Whether field is required (False = Nullable)
            ref_entity: Referenced entity name for ref fields

        Returns:
            DieselFieldType with complete type information

        Raises:
            ValueError: If field_type is unknown
        """
        # Handle array types (text[], integer[], etc.)
        is_array = field_type.endswith("[]")
        if is_array:
            field_type = field_type[:-2]  # Remove []

        # Check subtype map first (more specific)
        if field_type in self.SUBTYPE_MAP:
            base_type = self.SUBTYPE_MAP[field_type]
        else:
            # Extract base type (ignore subtype if not in map)
            base_type_name = field_type.split(":")[0]

            if base_type_name not in self.TYPE_MAP:
                raise ValueError(
                    f"Unknown SpecQL type: {field_type}. "
                    f"Valid types: {list(self.TYPE_MAP.keys())}"
                )

            base_type = self.TYPE_MAP[base_type_name]

        return DieselFieldType(
            base_type=base_type,
            is_nullable=not required,
            is_array=is_array
        )

    def map_trinity_field(self, field_name: str) -> DieselFieldType:
        """
        Map Trinity pattern audit fields

        Trinity fields have standard types:
        - pk_* → Int8 (GENERATED BY DEFAULT AS IDENTITY)
        - id → Uuid (NOT NULL, UNIQUE)
        - created_at, updated_at → Timestamptz (NOT NULL)
        - created_by, updated_by → Nullable<Uuid>
        - deleted_at, deleted_by → Nullable<Uuid> (soft delete)

        Args:
            field_name: Trinity field name

        Returns:
            DieselFieldType for the Trinity field
        """
        trinity_types = {
            # Primary keys
            "pk_": DieselFieldType(DieselSqlType.INT4, is_nullable=False),
            # UUID identifier
            "id": DieselFieldType(DieselSqlType.UUID, is_nullable=False),
            # Required timestamps
            "created_at": DieselFieldType(DieselSqlType.TIMESTAMPTZ, is_nullable=False),
            "updated_at": DieselFieldType(DieselSqlType.TIMESTAMPTZ, is_nullable=False),
            # Optional user references
            "created_by": DieselFieldType(DieselSqlType.UUID, is_nullable=True),
            "updated_by": DieselFieldType(DieselSqlType.UUID, is_nullable=True),
            "deleted_at": DieselFieldType(DieselSqlType.TIMESTAMPTZ, is_nullable=True),
            "deleted_by": DieselFieldType(DieselSqlType.UUID, is_nullable=True),
        }

        # Match by prefix for pk_*
        if field_name.startswith("pk_"):
            return trinity_types["pk_"]

        return trinity_types.get(
            field_name,
            DieselFieldType(DieselSqlType.VARCHAR, is_nullable=True)
        )
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_diesel_type_mapper.py -v --cov=src/generators/rust/diesel_type_mapper
# Expected: All tests pass, 95%+ coverage (GREEN phase)
```

**🔧 REFACTOR: Add Helper Methods (15 minutes)**

Add convenience methods to DieselTypeMapper:

```python
def get_rust_native_type(self, diesel_type: DieselFieldType) -> str:
    """
    Get the Rust native type for a Diesel type

    Used for struct field definitions.

    Example:
        Int4 → i32
        Varchar → String
        Nullable<Int4> → Option<i32>
    """
    rust_types = {
        DieselSqlType.INT2: "i16",
        DieselSqlType.INT4: "i32",
        DieselSqlType.INT8: "i64",
        DieselSqlType.NUMERIC: "BigDecimal",
        DieselSqlType.FLOAT4: "f32",
        DieselSqlType.FLOAT8: "f64",
        DieselSqlType.VARCHAR: "String",
        DieselSqlType.TEXT: "String",
        DieselSqlType.BOOL: "bool",
        DieselSqlType.TIMESTAMPTZ: "chrono::NaiveDateTime",
        DieselSqlType.UUID: "uuid::Uuid",
        DieselSqlType.JSONB: "serde_json::Value",
    }

    rust_type = rust_types.get(diesel_type.base_type, "String")

    if diesel_type.is_array:
        rust_type = f"Vec<{rust_type}>"

    if diesel_type.is_nullable:
        rust_type = f"Option<{rust_type}>"

    return rust_type
```

**✅ QA Phase** (10 minutes):
- [ ] All type mapper tests pass
- [ ] Coverage ≥ 95%
- [ ] Edge cases handled (arrays, nullability, Trinity)
- [ ] Documentation complete

**Commit**:
```bash
git add tests/unit/generators/rust/test_diesel_type_mapper.py \
        src/generators/rust/diesel_type_mapper.py
git commit -m "feat(rust): implement Diesel type mapper with comprehensive tests

- Map SpecQL types to Diesel SQL types
- Support subtypes (integer:big, text:long, etc.)
- Handle nullability and arrays
- Trinity pattern field mapping
- Rust native type conversion
- 95%+ test coverage

Part of Phase 1.1 (Type Mapping) - Week 15 Day 1
"
```

---

### Phase 1.2: Diesel Table Generator (3 hours)

**Objective**: Generate Diesel `table!` macros from SpecQL entities

#### TDD Cycle 1.2.1: Basic Table Generation

**🔴 RED: Table Generator Tests (45 minutes)**

**File**: `tests/unit/generators/rust/test_diesel_table_generator.py`

```python
"""
Tests for Diesel table! macro generation

The table! macro is Diesel's DSL for defining database tables.
"""

import pytest
from src.generators.rust.diesel_table_generator import DieselTableGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestDieselTableGenerator:
    """Test generation of Diesel table! macros"""

    @pytest.fixture
    def generator(self):
        return DieselTableGenerator()

    @pytest.fixture
    def simple_entity(self):
        """Simple entity with basic fields"""
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(name="phone", field_type="text", required=False),
                FieldDefinition(name="active", field_type="boolean", required=True),
            ]
        )

    @pytest.fixture
    def entity_with_ref(self):
        """Entity with foreign key reference"""
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=False
                ),
            ]
        )

    def test_generate_table_macro_structure(self, generator, simple_entity):
        """Test basic table! macro structure"""
        result = generator.generate_table(simple_entity)

        # Assert macro structure
        assert "diesel::table! {" in result
        assert "crm.tb_contact (pk_contact) {" in result
        assert "}" in result

    def test_generate_primary_key(self, generator, simple_entity):
        """Test primary key field generation"""
        result = generator.generate_table(simple_entity)

        # Trinity pattern: pk_{entity_name} -> Int4
        assert "pk_contact -> Int4," in result

    def test_generate_uuid_field(self, generator, simple_entity):
        """Test UUID id field generation"""
        result = generator.generate_table(simple_entity)

        # Trinity pattern: id field
        assert "id -> Uuid," in result

    def test_generate_user_fields(self, generator, simple_entity):
        """Test user-defined fields"""
        result = generator.generate_table(simple_entity)

        assert "email -> Varchar," in result
        assert "phone -> Nullable<Varchar>," in result
        assert "active -> Bool," in result

    def test_generate_audit_fields(self, generator, simple_entity):
        """Test Trinity audit fields"""
        result = generator.generate_table(simple_entity)

        # All 6 audit fields
        assert "created_at -> Timestamptz," in result
        assert "created_by -> Nullable<Uuid>," in result
        assert "updated_at -> Timestamptz," in result
        assert "updated_by -> Nullable<Uuid>," in result
        assert "deleted_at -> Nullable<Timestamptz>," in result
        assert "deleted_by -> Nullable<Uuid>," in result

    def test_generate_foreign_key(self, generator, entity_with_ref):
        """Test foreign key field generation"""
        result = generator.generate_table(entity_with_ref)

        # Ref field becomes fk_*
        assert "fk_company -> Nullable<Int4>," in result

    def test_field_ordering(self, generator, simple_entity):
        """Test fields are in correct order"""
        result = generator.generate_table(simple_entity)
        lines = [line.strip() for line in result.split("\n") if "->" in line]

        # Expected order:
        # 1. pk_* (primary key)
        # 2. id (UUID)
        # 3. User fields
        # 4. Audit fields
        assert lines[0].startswith("pk_contact")
        assert lines[1].startswith("id")
        assert lines[-1].startswith("deleted_by")

    def test_schema_prefix(self, generator, simple_entity):
        """Test table name includes schema prefix"""
        result = generator.generate_table(simple_entity)

        # Schema.table format
        assert "crm.tb_contact" in result

    def test_table_name_convention(self, generator):
        """Test table naming follows tb_ convention"""
        entity = Entity(name="Company", schema="sales", fields=[])
        result = generator.generate_table(entity)

        # tb_ prefix + snake_case
        assert "sales.tb_company" in result

    def test_generate_enum_field(self, generator):
        """Test enum field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="status",
                    field_type="enum",
                    enum_values=["lead", "qualified", "customer"],
                    required=True
                ),
            ]
        )

        result = generator.generate_table(entity)

        # Enums stored as Varchar in Diesel
        assert "status -> Varchar," in result

    def test_generate_array_field(self, generator):
        """Test array field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="tags", field_type="text[]", required=False),
            ]
        )

        result = generator.generate_table(entity)

        assert "tags -> Nullable<Array<Varchar>>," in result

    def test_generate_json_field(self, generator):
        """Test JSON field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="metadata", field_type="json", required=False),
            ]
        )

        result = generator.generate_table(entity)

        assert "metadata -> Nullable<Jsonb>," in result

    def test_multiple_entities_generate_separately(self, generator):
        """Test generating multiple entities"""
        entity1 = Entity(name="Contact", schema="crm", fields=[])
        entity2 = Entity(name="Company", schema="crm", fields=[])

        result1 = generator.generate_table(entity1)
        result2 = generator.generate_table(entity2)

        assert "tb_contact" in result1
        assert "tb_company" in result2
        assert result1 != result2
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_diesel_table_generator.py -v
# Expected: FAIL (RED phase)
```

**🟢 GREEN: Implement Table Generator (1 hour 30 minutes)**

**File**: `src/generators/rust/diesel_table_generator.py`

```python
"""
Diesel Table Generator

Generates Diesel table! macros from SpecQL entity definitions.
"""

from typing import List
from src.core.ast_models import Entity, FieldDefinition
from src.generators.rust.diesel_type_mapper import DieselTypeMapper
from src.generators.naming_utils import to_snake_case


class DieselTableGenerator:
    """
    Generates Diesel table! macro definitions

    Example output:
        diesel::table! {
            crm.tb_contact (pk_contact) {
                pk_contact -> Int4,
                id -> Uuid,
                email -> Varchar,
                fk_company -> Nullable<Int4>,
                created_at -> Timestamptz,
                // ... more fields
            }
        }
    """

    def __init__(self):
        self.type_mapper = DieselTypeMapper()

    def generate_table(self, entity: Entity) -> str:
        """
        Generate Diesel table! macro for entity

        Args:
            entity: SpecQL entity definition

        Returns:
            Complete table! macro as string
        """
        table_name = self._get_table_name(entity)
        pk_field = self._get_pk_field_name(entity)

        # Generate field lines
        fields = self._generate_fields(entity)
        field_lines = "\n".join(f"        {f}" for f in fields)

        return f"""diesel::table! {{
    {entity.schema}.{table_name} ({pk_field}) {{
{field_lines}
    }}
}}"""

    def _get_table_name(self, entity: Entity) -> str:
        """Get Diesel table name (tb_entity_name)"""
        snake_name = to_snake_case(entity.name)
        return f"tb_{snake_name}"

    def _get_pk_field_name(self, entity: Entity) -> str:
        """Get primary key field name"""
        snake_name = to_snake_case(entity.name)
        return f"pk_{snake_name}"

    def _generate_fields(self, entity: Entity) -> List[str]:
        """
        Generate all field definitions in correct order

        Order:
        1. Primary key (pk_*)
        2. UUID identifier (id)
        3. User-defined fields
        4. Audit fields (created_at, updated_at, etc.)

        Returns:
            List of field definition strings
        """
        fields = []

        # 1. Primary key
        pk_field = self._get_pk_field_name(entity)
        fields.append(f"{pk_field} -> Int4,")

        # 2. UUID identifier
        fields.append("id -> Uuid,")

        # 3. User-defined fields
        for field in entity.fields:
            field_line = self._generate_field(field)
            fields.append(field_line)

        # 4. Audit fields (Trinity pattern)
        fields.extend(self._generate_audit_fields())

        return fields

    def _generate_field(self, field: FieldDefinition) -> str:
        """
        Generate single field definition

        Args:
            field: SpecQL field definition

        Returns:
            Field line like "email -> Varchar,"
        """
        # Handle foreign key references
        if field.field_type == "ref":
            field_name = f"fk_{to_snake_case(field.ref_entity)}"
        else:
            field_name = to_snake_case(field.name)

        # Map type
        diesel_type = self.type_mapper.map_field_type(
            field.field_type,
            required=field.required,
            ref_entity=field.ref_entity if field.field_type == "ref" else None
        )

        type_str = diesel_type.to_rust_string()

        return f"{field_name} -> {type_str},"

    def _generate_audit_fields(self) -> List[str]:
        """
        Generate Trinity pattern audit fields

        Returns:
            List of 6 audit field definitions
        """
        return [
            "created_at -> Timestamptz,",
            "created_by -> Nullable<Uuid>,",
            "updated_at -> Timestamptz,",
            "updated_by -> Nullable<Uuid>,",
            "deleted_at -> Nullable<Timestamptz>,",
            "deleted_by -> Nullable<Uuid>,",
        ]

    def generate_schema_file(self, entities: List[Entity]) -> str:
        """
        Generate complete schema.rs file with all tables

        Args:
            entities: List of SpecQL entities

        Returns:
            Complete schema.rs file content
        """
        # Generate table! macros for all entities
        tables = [self.generate_table(entity) for entity in entities]

        # Generate joinable! declarations for foreign keys
        joinables = self._generate_joinables(entities)

        # Generate allow_tables_to_appear_in_same_query!
        allow_tables = self._generate_allow_tables(entities)

        # Combine all parts
        parts = (
            ["// Generated by SpecQL", "// DO NOT EDIT MANUALLY", ""]
            + tables
            + [""]
            + joinables
            + [""]
            + [allow_tables]
        )

        return "\n\n".join(parts)

    def _generate_joinables(self, entities: List[Entity]) -> List[str]:
        """
        Generate diesel::joinable! declarations

        Example:
            diesel::joinable!(tb_contact -> tb_company (fk_company));
        """
        joinables = []

        for entity in entities:
            table_name = self._get_table_name(entity)

            # Find all ref fields
            for field in entity.fields:
                if field.field_type == "ref":
                    ref_table = f"tb_{to_snake_case(field.ref_entity)}"
                    fk_field = f"fk_{to_snake_case(field.ref_entity)}"

                    joinable = f"diesel::joinable!({table_name} -> {ref_table} ({fk_field}));"
                    joinables.append(joinable)

        return joinables

    def _generate_allow_tables(self, entities: List[Entity]) -> str:
        """
        Generate allow_tables_to_appear_in_same_query! macro

        Example:
            diesel::allow_tables_to_appear_in_same_query!(
                tb_contact,
                tb_company,
            );
        """
        table_names = [self._get_table_name(e) for e in entities]
        tables_list = ",\n    ".join(table_names)

        return f"""diesel::allow_tables_to_appear_in_same_query!(
    {tables_list},
);"""
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_diesel_table_generator.py -v --cov=src/generators/rust/diesel_table_generator
# Expected: All tests pass (GREEN phase)
```

**🔧 REFACTOR & ✅ QA** (45 minutes):
- Add documentation
- Extract magic strings to constants
- Add integration test with real entity
- Verify generated code with `rustfmt`

**Commit**:
```bash
git add tests/unit/generators/rust/test_diesel_table_generator.py \
        src/generators/rust/diesel_table_generator.py
git commit -m "feat(rust): implement Diesel table! macro generator

- Generate table! macros from SpecQL entities
- Support Trinity pattern fields
- Handle foreign keys with joinable! declarations
- Generate allow_tables_to_appear_in_same_query!
- Complete schema.rs file generation
- 95%+ test coverage

Part of Phase 1.2 (Table Generation) - Week 15 Day 1
"
```

---

### Phase 1.3: Schema File Integration Tests (2 hours)

**Objective**: Integration tests that verify complete schema.rs generation

#### TDD Cycle 1.3.1: End-to-End Schema Generation

**🔴 RED: Integration Tests (30 minutes)**

**File**: `tests/integration/rust/test_schema_generation.py`

```python
"""
Integration tests for complete schema.rs generation
"""

import pytest
from pathlib import Path
from src.generators.rust.diesel_table_generator import DieselTableGenerator
from src.core.specql_parser import SpecQLParser


class TestSchemaGeneration:
    """Integration tests for schema.rs generation"""

    @pytest.fixture
    def generator(self):
        return DieselTableGenerator()

    @pytest.fixture
    def sample_entities(self):
        """Load sample SpecQL entities"""
        parser = SpecQLParser()
        # This assumes test fixtures exist
        contact = parser.parse_file("tests/fixtures/entities/contact.yaml")
        company = parser.parse_file("tests/fixtures/entities/company.yaml")
        return [contact, company]

    def test_generate_complete_schema_file(self, generator, sample_entities):
        """Test generating complete schema.rs"""
        result = generator.generate_schema_file(sample_entities)

        # Verify structure
        assert "diesel::table!" in result
        assert "tb_contact" in result
        assert "tb_company" in result
        assert "diesel::joinable!" in result
        assert "allow_tables_to_appear_in_same_query!" in result

    def test_generated_schema_is_valid_rust(self, generator, sample_entities):
        """Test generated code is valid Rust syntax"""
        result = generator.generate_schema_file(sample_entities)

        # Write to temp file
        temp_file = Path("/tmp/test_schema.rs")
        temp_file.write_text(result)

        # Verify with rustfmt (must be installed)
        import subprocess
        try:
            subprocess.run(
                ["rustfmt", "--check", str(temp_file)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Generated Rust code is invalid:\n{e.stderr.decode()}")

    def test_foreign_key_relationships(self, generator, sample_entities):
        """Test foreign key relationships are correctly defined"""
        result = generator.generate_schema_file(sample_entities)

        # Contact references Company
        assert "tb_contact -> tb_company (fk_company)" in result

    def test_all_tables_in_allow_macro(self, generator, sample_entities):
        """Test all tables appear in allow macro"""
        result = generator.generate_schema_file(sample_entities)

        # Extract allow_tables_to_appear_in_same_query! section
        allow_section = result[result.index("allow_tables_to_appear_in_same_query!"):]

        for entity in sample_entities:
            table_name = f"tb_{entity.name.lower()}"
            assert table_name in allow_section
```

**🟢 GREEN**: Make tests pass by ensuring complete implementation

**🔧 REFACTOR**: Add more edge cases, documentation

**✅ QA**: Full Phase 1 validation

---

### Phase 1 Summary

**Achievements**:
- ✅ Complete type mapping system (SpecQL → Diesel)
- ✅ Table! macro generation with Trinity pattern
- ✅ Foreign key relationships (joinable!)
- ✅ Complete schema.rs file generation
- ✅ Integration tests verifying Rust syntax validity
- ✅ 95%+ test coverage

**Files Created**:
- `src/generators/rust/diesel_type_mapper.py` (~200 lines)
- `src/generators/rust/diesel_table_generator.py` (~300 lines)
- `tests/unit/generators/rust/test_diesel_type_mapper.py` (~250 lines)
- `tests/unit/generators/rust/test_diesel_table_generator.py` (~350 lines)
- `tests/integration/rust/test_schema_generation.py` (~100 lines)

**Total**: ~1,200 lines

**Commit Count**: 3-4 focused commits

**Ready For**: Phase 2 (Rust Model Generation)

---

## 🔴 PHASE 2: Rust Model Generation (Day 2)

**Objective**: Generate Rust struct definitions with Diesel derives (Queryable, Insertable, AsChangeset)

**Estimated Duration**: 8 hours
**Files Created**: ~10 files, ~1,500 lines
**Test Coverage Target**: 95%+

### Technical Context

Diesel requires three types of structs for database operations:

1. **Queryable Struct**: Represents rows read FROM database
2. **Insertable Struct**: Represents data TO insert INTO database
3. **Changeset Struct**: Represents data TO update

Example generated code:

```rust
// models.rs
use diesel::prelude::*;
use uuid::Uuid;
use chrono::NaiveDateTime;
use super::schema::crm::tb_contact;

#[derive(Debug, Clone, Queryable, Selectable)]
#[diesel(table_name = tb_contact)]
pub struct Contact {
    pub pk_contact: i32,
    pub id: Uuid,
    pub email: String,
    pub fk_company: Option<i32>,
    pub status: String,
    pub created_at: NaiveDateTime,
    pub created_by: Option<Uuid>,
    pub updated_at: NaiveDateTime,
    pub updated_by: Option<Uuid>,
    pub deleted_at: Option<NaiveDateTime>,
    pub deleted_by: Option<Uuid>,
}

#[derive(Debug, Insertable)]
#[diesel(table_name = tb_contact)]
pub struct NewContact {
    pub email: String,
    pub fk_company: Option<i32>,
    pub status: String,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,
}

#[derive(Debug, AsChangeset)]
#[diesel(table_name = tb_contact)]
pub struct UpdateContact {
    pub email: Option<String>,
    pub fk_company: Option<i32>,
    pub status: Option<String>,
    pub updated_at: NaiveDateTime,
    pub updated_by: Option<Uuid>,
}
```

---

### Phase 2.1: Queryable Struct Generation (3 hours)

**Objective**: Generate Diesel Queryable structs that represent database rows

#### TDD Cycle 2.1.1: Basic Queryable Struct

**🔴 RED: Queryable Tests (45 minutes)**

**File**: `tests/unit/generators/rust/test_model_generator.py`

```python
"""
Tests for Rust model struct generation

Tests the generation of Queryable, Insertable, and AsChangeset structs.
"""

import pytest
from src.generators.rust.model_generator import RustModelGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestQueryableStructGeneration:
    """Test generation of Diesel Queryable structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(name="phone", field_type="text", required=False),
                FieldDefinition(name="active", field_type="boolean", required=True),
            ]
        )

    def test_generate_queryable_struct_declaration(self, generator, simple_entity):
        """Test basic struct declaration with derives"""
        result = generator.generate_queryable_struct(simple_entity)

        # Struct declaration
        assert "#[derive(Debug, Clone, Queryable, Selectable)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct Contact {" in result

    def test_queryable_includes_primary_key(self, generator, simple_entity):
        """Test primary key field is included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub pk_contact: i32," in result

    def test_queryable_includes_uuid_id(self, generator, simple_entity):
        """Test UUID id field is included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub id: Uuid," in result

    def test_queryable_includes_user_fields(self, generator, simple_entity):
        """Test user-defined fields are included with correct types"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub email: String," in result
        assert "pub phone: Option<String>," in result  # Optional field
        assert "pub active: bool," in result

    def test_queryable_includes_audit_fields(self, generator, simple_entity):
        """Test Trinity audit fields are included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub created_at: NaiveDateTime," in result
        assert "pub created_by: Option<Uuid>," in result
        assert "pub updated_at: NaiveDateTime," in result
        assert "pub updated_by: Option<Uuid>," in result
        assert "pub deleted_at: Option<NaiveDateTime>," in result
        assert "pub deleted_by: Option<Uuid>," in result

    def test_queryable_field_ordering(self, generator, simple_entity):
        """Test fields are in correct order"""
        result = generator.generate_queryable_struct(simple_entity)

        # Extract field lines
        lines = [line.strip() for line in result.split("\n") if line.strip().startswith("pub ")]

        # Expected order: pk, id, user fields, audit fields
        assert lines[0].startswith("pub pk_contact")
        assert lines[1].startswith("pub id")
        assert lines[-1].startswith("pub deleted_by")

    def test_queryable_with_foreign_key(self, generator):
        """Test foreign key field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=False
                ),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        # Foreign keys are i32 (or Option<i32>)
        assert "pub fk_company: Option<i32>," in result

    def test_queryable_with_enum_field(self, generator):
        """Test enum field becomes String"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="status",
                    field_type="enum",
                    enum_values=["lead", "qualified"],
                    required=True
                ),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        # Enums stored as String
        assert "pub status: String," in result

    def test_queryable_with_integer_subtypes(self, generator):
        """Test integer subtypes map to correct Rust types"""
        entity = Entity(
            name="Stats",
            schema="analytics",
            fields=[
                FieldDefinition(name="small_count", field_type="integer:small", required=True),
                FieldDefinition(name="regular_count", field_type="integer", required=True),
                FieldDefinition(name="big_count", field_type="integer:big", required=True),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub small_count: i16," in result
        assert "pub regular_count: i32," in result
        assert "pub big_count: i64," in result

    def test_queryable_with_decimal_field(self, generator):
        """Test decimal fields use BigDecimal"""
        entity = Entity(
            name="Product",
            schema="sales",
            fields=[
                FieldDefinition(name="price", field_type="decimal:money", required=True),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub price: BigDecimal," in result

    def test_queryable_with_json_field(self, generator):
        """Test JSON fields use serde_json::Value"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="metadata", field_type="json", required=False),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub metadata: Option<serde_json::Value>," in result

    def test_queryable_with_array_field(self, generator):
        """Test array fields use Vec<T>"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="tags", field_type="text[]", required=False),
            ]
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub tags: Option<Vec<String>>," in result

    def test_queryable_imports(self, generator, simple_entity):
        """Test required imports are included"""
        result = generator.generate_queryable_struct(simple_entity, include_imports=True)

        assert "use diesel::prelude::*;" in result
        assert "use uuid::Uuid;" in result
        assert "use chrono::NaiveDateTime;" in result
        assert "use super::schema::crm::tb_contact;" in result

    def test_queryable_documentation(self, generator, simple_entity):
        """Test documentation comment is generated"""
        simple_entity.description = "Represents a contact in the CRM"
        result = generator.generate_queryable_struct(simple_entity)

        assert "/// Represents a contact in the CRM" in result
        assert "/// Queryable struct for tb_contact table" in result
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_model_generator.py::TestQueryableStructGeneration -v
# Expected: FAIL (RED phase)
```

**🟢 GREEN: Implement Queryable Generator (1 hour 30 minutes)**

**File**: `src/generators/rust/model_generator.py`

```python
"""
Rust Model Generator

Generates Rust struct definitions for Diesel ORM.
"""

from typing import List, Optional
from src.core.ast_models import Entity, FieldDefinition
from src.generators.rust.diesel_type_mapper import DieselTypeMapper
from src.generators.naming_utils import to_snake_case, to_pascal_case


class RustModelGenerator:
    """
    Generates Diesel model structs

    Creates three types of structs:
    1. Queryable: For reading from database
    2. Insertable: For inserting into database
    3. AsChangeset: For updating database

    Example:
        generator = RustModelGenerator()

        # Generate Queryable struct
        queryable = generator.generate_queryable_struct(entity)

        # Generate all structs
        models = generator.generate_all_models(entity)
    """

    def __init__(self):
        self.type_mapper = DieselTypeMapper()

    def generate_queryable_struct(
        self,
        entity: Entity,
        include_imports: bool = False
    ) -> str:
        """
        Generate Diesel Queryable struct

        This struct represents a complete row from the database.
        Includes all fields: primary key, UUID, user fields, audit fields.

        Args:
            entity: SpecQL entity definition
            include_imports: Whether to include use statements

        Returns:
            Complete Queryable struct definition
        """
        struct_name = to_pascal_case(entity.name)
        table_name = f"tb_{to_snake_case(entity.name)}"

        # Build parts
        parts = []

        # Imports (if requested)
        if include_imports:
            parts.append(self._generate_imports(entity))
            parts.append("")

        # Documentation
        if entity.description:
            parts.append(f"/// {entity.description}")
        parts.append(f"/// Queryable struct for {table_name} table")

        # Derives
        parts.append("#[derive(Debug, Clone, Queryable, Selectable)]")
        parts.append(f"#[diesel(table_name = {table_name})]")

        # Struct declaration
        parts.append(f"pub struct {struct_name} {{")

        # Fields
        field_lines = self._generate_queryable_fields(entity)
        for field_line in field_lines:
            parts.append(f"    {field_line}")

        parts.append("}")

        return "\n".join(parts)

    def _generate_imports(self, entity: Entity) -> str:
        """Generate use statements"""
        imports = [
            "use diesel::prelude::*;",
            "use uuid::Uuid;",
            "use chrono::NaiveDateTime;",
        ]

        # Schema import
        schema_path = f"super::schema::{entity.schema}::tb_{to_snake_case(entity.name)}"
        imports.append(f"use {schema_path};")

        # BigDecimal if needed
        if self._needs_bigdecimal(entity):
            imports.append("use bigdecimal::BigDecimal;")

        # serde_json if needed
        if self._needs_serde_json(entity):
            imports.append("use serde_json;")

        return "\n".join(imports)

    def _needs_bigdecimal(self, entity: Entity) -> bool:
        """Check if entity has decimal fields"""
        return any(
            f.field_type.startswith("decimal")
            for f in entity.fields
        )

    def _needs_serde_json(self, entity: Entity) -> bool:
        """Check if entity has JSON fields"""
        return any(
            f.field_type == "json"
            for f in entity.fields
        )

    def _generate_queryable_fields(self, entity: Entity) -> List[str]:
        """
        Generate all field definitions for Queryable struct

        Order:
        1. Primary key (pk_*)
        2. UUID identifier (id)
        3. User-defined fields
        4. Audit fields

        Returns:
            List of field definition strings
        """
        fields = []

        # 1. Primary key
        pk_name = f"pk_{to_snake_case(entity.name)}"
        fields.append(f"pub {pk_name}: i32,")

        # 2. UUID identifier
        fields.append("pub id: Uuid,")

        # 3. User-defined fields
        for field in entity.fields:
            field_def = self._generate_queryable_field(field)
            fields.append(field_def)

        # 4. Audit fields
        fields.extend(self._generate_audit_fields())

        return fields

    def _generate_queryable_field(self, field: FieldDefinition) -> str:
        """
        Generate single field definition for Queryable struct

        Args:
            field: SpecQL field definition

        Returns:
            Field line like "pub email: String,"
        """
        # Handle foreign key references
        if field.field_type == "ref":
            field_name = f"fk_{to_snake_case(field.ref_entity)}"
        else:
            field_name = to_snake_case(field.name)

        # Get Rust type
        diesel_type = self.type_mapper.map_field_type(
            field.field_type,
            required=field.required,
            ref_entity=field.ref_entity if field.field_type == "ref" else None
        )

        rust_type = self.type_mapper.get_rust_native_type(diesel_type)

        return f"pub {field_name}: {rust_type},"

    def _generate_audit_fields(self) -> List[str]:
        """Generate Trinity pattern audit fields"""
        return [
            "pub created_at: NaiveDateTime,",
            "pub created_by: Option<Uuid>,",
            "pub updated_at: NaiveDateTime,",
            "pub updated_by: Option<Uuid>,",
            "pub deleted_at: Option<NaiveDateTime>,",
            "pub deleted_by: Option<Uuid>,",
        ]
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_model_generator.py::TestQueryableStructGeneration -v --cov=src/generators/rust/model_generator
# Expected: All tests pass (GREEN phase)
```

**🔧 REFACTOR** (45 minutes):
- Extract field generation to separate methods
- Add helper for common derives
- Improve documentation
- Add more edge cases

**✅ QA**: Verify coverage, test edge cases

**Commit**:
```bash
git add tests/unit/generators/rust/test_model_generator.py \
        src/generators/rust/model_generator.py
git commit -m "feat(rust): implement Queryable struct generation

- Generate Diesel Queryable structs from SpecQL entities
- Support all field types with correct Rust mappings
- Include Trinity pattern audit fields
- Handle foreign keys, enums, arrays, JSON
- Generate required use statements
- 95%+ test coverage

Part of Phase 2.1 (Queryable Structs) - Week 15 Day 2
"
```

---

### Phase 2.2: Insertable Struct Generation (2 hours)

**Objective**: Generate NewEntity structs for database inserts

#### TDD Cycle 2.2.1: Insertable Struct

**🔴 RED: Insertable Tests (30 minutes)**

**File**: `tests/unit/generators/rust/test_model_generator.py` (add class)

```python
class TestInsertableStructGeneration:
    """Test generation of Diesel Insertable structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(name="phone", field_type="text", required=False),
            ]
        )

    def test_generate_insertable_struct_declaration(self, generator, simple_entity):
        """Test basic Insertable struct declaration"""
        result = generator.generate_insertable_struct(simple_entity)

        assert "#[derive(Debug, Insertable)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct NewContact {" in result

    def test_insertable_excludes_generated_fields(self, generator, simple_entity):
        """Test Insertable excludes auto-generated fields"""
        result = generator.generate_insertable_struct(simple_entity)

        # Should NOT include:
        assert "pk_contact" not in result  # Auto-generated
        assert "id:" not in result or "id: Uuid," not in result  # Auto-generated UUID
        assert "created_at:" not in result  # Auto-generated timestamp
        assert "updated_at:" not in result  # Auto-generated timestamp
        assert "deleted_at:" not in result  # For soft delete, not insert

    def test_insertable_includes_user_fields(self, generator, simple_entity):
        """Test Insertable includes user-defined fields"""
        result = generator.generate_insertable_struct(simple_entity)

        assert "pub email: String," in result
        assert "pub phone: Option<String>," in result

    def test_insertable_includes_creator_fields(self, generator, simple_entity):
        """Test Insertable includes created_by and updated_by"""
        result = generator.generate_insertable_struct(simple_entity)

        # User who created/updated (not timestamps)
        assert "pub created_by: Option<Uuid>," in result
        assert "pub updated_by: Option<Uuid>," in result

    def test_insertable_with_required_foreign_key(self, generator):
        """Test required foreign key in Insertable"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=True  # Required FK
                ),
            ]
        )

        result = generator.generate_insertable_struct(entity)

        # Required FK is not Option
        assert "pub fk_company: i32," in result

    def test_insertable_with_optional_foreign_key(self, generator):
        """Test optional foreign key in Insertable"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=False  # Optional FK
                ),
            ]
        )

        result = generator.generate_insertable_struct(entity)

        # Optional FK is Option
        assert "pub fk_company: Option<i32>," in result

    def test_insertable_with_default_values(self, generator):
        """Test fields with defaults are still included"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="active",
                    field_type="boolean",
                    required=True,
                    default="true"
                ),
            ]
        )

        result = generator.generate_insertable_struct(entity)

        # Field still included (defaults handled at DB level)
        assert "pub active: bool," in result

    def test_insertable_derives_serialization(self, generator, simple_entity):
        """Test Insertable can optionally derive Serialize/Deserialize"""
        result = generator.generate_insertable_struct(
            simple_entity,
            with_serde=True
        )

        assert "#[derive(Debug, Insertable, Serialize, Deserialize)]" in result

    def test_insertable_validation_attributes(self, generator):
        """Test validation attributes for required fields"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="email",
                    field_type="text",
                    required=True,
                    validation={"pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"}
                ),
            ]
        )

        result = generator.generate_insertable_struct(entity)

        # Validation via custom trait (future enhancement)
        # For now, just ensure field is correct type
        assert "pub email: String," in result
```

**🟢 GREEN: Implement Insertable Generator (1 hour)**

**File**: `src/generators/rust/model_generator.py` (add method)

```python
def generate_insertable_struct(
    self,
    entity: Entity,
    include_imports: bool = False,
    with_serde: bool = False
) -> str:
    """
    Generate Diesel Insertable struct

    This struct represents data for INSERT operations.
    Excludes auto-generated fields (pk, id, timestamps).
    Includes user fields and creator tracking.

    Args:
        entity: SpecQL entity definition
        include_imports: Whether to include use statements
        with_serde: Whether to include Serialize/Deserialize derives

    Returns:
        Complete Insertable struct definition
    """
    struct_name = f"New{to_pascal_case(entity.name)}"
    table_name = f"tb_{to_snake_case(entity.name)}"

    parts = []

    # Imports (if requested)
    if include_imports:
        parts.append(self._generate_imports(entity, with_serde=with_serde))
        parts.append("")

    # Documentation
    parts.append(f"/// Insertable struct for {table_name} table")
    parts.append("/// Used for INSERT operations")

    # Derives
    derives = ["Debug", "Insertable"]
    if with_serde:
        derives.extend(["Serialize", "Deserialize"])

    parts.append(f"#[derive({', '.join(derives)})]")
    parts.append(f"#[diesel(table_name = {table_name})]")

    # Struct declaration
    parts.append(f"pub struct {struct_name} {{")

    # Fields (only user fields + creator tracking)
    field_lines = self._generate_insertable_fields(entity)
    for field_line in field_lines:
        parts.append(f"    {field_line}")

    parts.append("}")

    return "\n".join(parts)

def _generate_insertable_fields(self, entity: Entity) -> List[str]:
    """
    Generate fields for Insertable struct

    Includes:
    - User-defined fields
    - created_by, updated_by (user tracking)

    Excludes:
    - pk_* (auto-generated)
    - id (auto-generated UUID)
    - created_at, updated_at (auto-generated timestamps)
    - deleted_at, deleted_by (soft delete fields)

    Returns:
        List of field definition strings
    """
    fields = []

    # User-defined fields
    for field in entity.fields:
        field_def = self._generate_queryable_field(field)  # Same logic
        fields.append(field_def)

    # Creator tracking
    fields.append("pub created_by: Option<Uuid>,")
    fields.append("pub updated_by: Option<Uuid>,")

    return fields
```

**Run Tests**:
```bash
uv run pytest tests/unit/generators/rust/test_model_generator.py::TestInsertableStructGeneration -v
# Expected: PASS (GREEN phase)
```

**🔧 REFACTOR & ✅ QA** (30 minutes)

**Commit**:
```bash
git add tests/unit/generators/rust/test_model_generator.py \
        src/generators/rust/model_generator.py
git commit -m "feat(rust): implement Insertable struct generation

- Generate NewEntity structs for INSERT operations
- Exclude auto-generated fields (pk, id, timestamps)
- Include user tracking (created_by, updated_by)
- Optional serde support
- 95%+ test coverage

Part of Phase 2.2 (Insertable Structs) - Week 15 Day 2
"
```

---

### Phase 2.3: AsChangeset Struct Generation (2 hours)

**Objective**: Generate UpdateEntity structs for database updates

#### TDD Cycle 2.3.1: AsChangeset Struct

**🔴 RED: AsChangeset Tests (30 minutes)**

**File**: `tests/unit/generators/rust/test_model_generator.py` (add class)

```python
class TestAsChangesetStructGeneration:
    """Test generation of Diesel AsChangeset structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(name="phone", field_type="text", required=False),
                FieldDefinition(name="active", field_type="boolean", required=True),
            ]
        )

    def test_generate_changeset_struct_declaration(self, generator, simple_entity):
        """Test basic AsChangeset struct declaration"""
        result = generator.generate_changeset_struct(simple_entity)

        assert "#[derive(Debug, AsChangeset)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct UpdateContact {" in result

    def test_changeset_all_fields_optional(self, generator, simple_entity):
        """Test all updateable fields are Option<T>"""
        result = generator.generate_changeset_struct(simple_entity)

        # All user fields wrapped in Option for partial updates
        assert "pub email: Option<String>," in result
        assert "pub phone: Option<Option<String>>," in result  # Option field becomes Option<Option<>>
        assert "pub active: Option<bool>," in result

    def test_changeset_includes_updated_at(self, generator, simple_entity):
        """Test updated_at is included (required)"""
        result = generator.generate_changeset_struct(simple_entity)

        # updated_at is NOT Option (always set on update)
        assert "pub updated_at: NaiveDateTime," in result

    def test_changeset_includes_updated_by(self, generator, simple_entity):
        """Test updated_by is included"""
        result = generator.generate_changeset_struct(simple_entity)

        assert "pub updated_by: Option<Uuid>," in result

    def test_changeset_excludes_immutable_fields(self, generator, simple_entity):
        """Test immutable fields are excluded"""
        result = generator.generate_changeset_struct(simple_entity)

        # Should NOT include:
        assert "pk_contact" not in result  # Primary key never updated
        assert "id:" not in result or "id: Uuid," not in result  # UUID never updated
        assert "created_at" not in result  # Creation time never updated
        assert "created_by" not in result  # Creator never updated

    def test_changeset_with_foreign_key(self, generator):
        """Test foreign key can be updated"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=False
                ),
            ]
        )

        result = generator.generate_changeset_struct(entity)

        # FK wrapped in Option for updates
        assert "pub fk_company: Option<Option<i32>>," in result

    def test_changeset_skip_deleted_fields(self, generator, simple_entity):
        """Test soft delete fields are excluded"""
        result = generator.generate_changeset_struct(simple_entity)

        # Soft delete handled separately
        assert "deleted_at" not in result
        assert "deleted_by" not in result

    def test_changeset_with_treat_none_as_null(self, generator, simple_entity):
        """Test treat_none_as_null attribute"""
        result = generator.generate_changeset_struct(
            simple_entity,
            treat_none_as_null=True
        )

        # Diesel attribute for NULL handling
        assert "#[diesel(treat_none_as_null = true)]" in result

    def test_changeset_builder_pattern(self, generator, simple_entity):
        """Test builder pattern methods (optional enhancement)"""
        result = generator.generate_changeset_struct(
            simple_entity,
            with_builder=True
        )

        # Check for impl block with builder methods
        assert "impl UpdateContact {" in result
        assert "pub fn set_email" in result
```

**🟢 GREEN: Implement AsChangeset Generator (1 hour)**

**File**: `src/generators/rust/model_generator.py` (add method)

```python
def generate_changeset_struct(
    self,
    entity: Entity,
    include_imports: bool = False,
    treat_none_as_null: bool = True,
    with_builder: bool = False
) -> str:
    """
    Generate Diesel AsChangeset struct

    This struct represents data for UPDATE operations.
    All user fields are Option<T> for partial updates.
    Includes updated_at (required) and updated_by.

    Args:
        entity: SpecQL entity definition
        include_imports: Whether to include use statements
        treat_none_as_null: Whether Option::None sets field to NULL
        with_builder: Whether to generate builder methods

    Returns:
        Complete AsChangeset struct definition
    """
    struct_name = f"Update{to_pascal_case(entity.name)}"
    table_name = f"tb_{to_snake_case(entity.name)}"

    parts = []

    # Imports (if requested)
    if include_imports:
        parts.append(self._generate_imports(entity))
        parts.append("")

    # Documentation
    parts.append(f"/// Changeset struct for {table_name} table")
    parts.append("/// Used for UPDATE operations")
    parts.append("/// All fields are Option<T> for partial updates")

    # Derives
    parts.append("#[derive(Debug, AsChangeset)]")
    parts.append(f"#[diesel(table_name = {table_name})]")

    if treat_none_as_null:
        parts.append("#[diesel(treat_none_as_null = true)]")

    # Struct declaration
    parts.append(f"pub struct {struct_name} {{")

    # Fields
    field_lines = self._generate_changeset_fields(entity)
    for field_line in field_lines:
        parts.append(f"    {field_line}")

    parts.append("}")

    # Builder methods (optional)
    if with_builder:
        parts.append("")
        parts.append(self._generate_changeset_builder(entity, struct_name))

    return "\n".join(parts)

def _generate_changeset_fields(self, entity: Entity) -> List[str]:
    """
    Generate fields for AsChangeset struct

    All user fields become Option<T> for partial updates.
    Optional fields become Option<Option<T>>.

    Includes:
    - User-defined fields (as Option)
    - updated_at (required, NaiveDateTime)
    - updated_by (Option<Uuid>)

    Excludes:
    - pk_*, id (immutable)
    - created_at, created_by (immutable)
    - deleted_at, deleted_by (handled separately)

    Returns:
        List of field definition strings
    """
    fields = []

    # User-defined fields (all wrapped in Option)
    for field in entity.fields:
        field_def = self._generate_changeset_field(field)
        fields.append(field_def)

    # Update tracking
    fields.append("pub updated_at: NaiveDateTime,")  # Required (set to now())
    fields.append("pub updated_by: Option<Uuid>,")

    return fields

def _generate_changeset_field(self, field: FieldDefinition) -> str:
    """
    Generate single field definition for AsChangeset struct

    All fields wrapped in Option for partial updates.
    Already-optional fields become Option<Option<T>>.

    Args:
        field: SpecQL field definition

    Returns:
        Field line like "pub email: Option<String>,"
    """
    # Handle foreign key references
    if field.field_type == "ref":
        field_name = f"fk_{to_snake_case(field.ref_entity)}"
    else:
        field_name = to_snake_case(field.name)

    # Get base Rust type
    diesel_type = self.type_mapper.map_field_type(
        field.field_type,
        required=field.required,
        ref_entity=field.ref_entity if field.field_type == "ref" else None
    )

    rust_type = self.type_mapper.get_rust_native_type(diesel_type)

    # Wrap in Option for partial updates
    # Note: If already Option<T>, becomes Option<Option<T>>
    update_type = f"Option<{rust_type}>"

    return f"pub {field_name}: {update_type},"

def _generate_changeset_builder(self, entity: Entity, struct_name: str) -> str:
    """
    Generate builder pattern methods for AsChangeset struct

    Provides fluent API: update.set_email("...").set_active(true)

    Args:
        entity: SpecQL entity definition
        struct_name: Name of the struct

    Returns:
        Complete impl block with builder methods
    """
    parts = [f"impl {struct_name} {{"]

    # Constructor
    parts.append("    pub fn new() -> Self {")
    parts.append("        Self {")

    # Initialize all fields to None
    for field in entity.fields:
        if field.field_type == "ref":
            field_name = f"fk_{to_snake_case(field.ref_entity)}"
        else:
            field_name = to_snake_case(field.name)
        parts.append(f"            {field_name}: None,")

    parts.append("            updated_at: chrono::Utc::now().naive_utc(),")
    parts.append("            updated_by: None,")
    parts.append("        }")
    parts.append("    }")
    parts.append("")

    # Setter methods for each field
    for field in entity.fields:
        if field.field_type == "ref":
            field_name = f"fk_{to_snake_case(field.ref_entity)}"
        else:
            field_name = to_snake_case(field.name)

        diesel_type = self.type_mapper.map_field_type(
            field.field_type,
            required=field.required,
            ref_entity=field.ref_entity if field.field_type == "ref" else None
        )
        rust_type = self.type_mapper.get_rust_native_type(diesel_type)

        parts.append(f"    pub fn set_{field_name}(mut self, value: {rust_type}) -> Self {{")
        parts.append(f"        self.{field_name} = Some(value);")
        parts.append("        self")
        parts.append("    }")
        parts.append("")

    parts.append("}")

    return "\n".join(parts)
```

**Run Tests** + **REFACTOR** + **QA** + **Commit** (similar to previous cycles)

---

### Phase 2.4: Complete Models File Generation (1 hour)

**Objective**: Generate complete `models.rs` file with all structs

#### TDD Cycle 2.4.1: Models File Assembly

**🔴 RED + 🟢 GREEN + 🔧 REFACTOR** (1 hour)

**File**: `src/generators/rust/model_generator.py` (add method)

```python
def generate_models_file(
    self,
    entities: List[Entity],
    with_serde: bool = True,
    with_builders: bool = False
) -> str:
    """
    Generate complete models.rs file with all structs

    For each entity, generates:
    - Queryable struct (EntityName)
    - Insertable struct (NewEntityName)
    - AsChangeset struct (UpdateEntityName)

    Args:
        entities: List of SpecQL entities
        with_serde: Include Serialize/Deserialize derives
        with_builders: Include builder pattern methods

    Returns:
        Complete models.rs file content
    """
    parts = [
        "// Generated by SpecQL",
        "// DO NOT EDIT MANUALLY",
        "",
        "// Common imports",
        "use diesel::prelude::*;",
        "use uuid::Uuid;",
        "use chrono::NaiveDateTime;",
    ]

    # Conditional imports
    if any(self._needs_bigdecimal(e) for e in entities):
        parts.append("use bigdecimal::BigDecimal;")

    if any(self._needs_serde_json(e) for e in entities):
        parts.append("use serde_json;")

    if with_serde:
        parts.append("use serde::{Deserialize, Serialize};")

    parts.append("")

    # Generate structs for each entity
    for entity in entities:
        # Schema imports for this entity
        schema_path = f"use super::schema::{entity.schema}::tb_{to_snake_case(entity.name)};"
        parts.append(schema_path)
        parts.append("")

        # Queryable struct
        parts.append(self.generate_queryable_struct(entity, include_imports=False))
        parts.append("")

        # Insertable struct
        parts.append(self.generate_insertable_struct(
            entity,
            include_imports=False,
            with_serde=with_serde
        ))
        parts.append("")

        # AsChangeset struct
        parts.append(self.generate_changeset_struct(
            entity,
            include_imports=False,
            with_builder=with_builders
        ))
        parts.append("")
        parts.append("// " + "=" * 80)
        parts.append("")

    return "\n".join(parts)
```

**Integration Test**:

```python
def test_generate_complete_models_file(self, generator, sample_entities):
    """Test generating complete models.rs"""
    result = generator.generate_models_file(sample_entities)

    # Verify all structs present
    assert "pub struct Contact {" in result
    assert "pub struct NewContact {" in result
    assert "pub struct UpdateContact {" in result

    assert "pub struct Company {" in result
    assert "pub struct NewCompany {" in result
    assert "pub struct UpdateCompany {" in result

    # Verify valid Rust
    temp_file = Path("/tmp/test_models.rs")
    temp_file.write_text(result)
    subprocess.run(["rustfmt", "--check", str(temp_file)], check=True)
```

**✅ QA & Commit**

---

### Phase 2 Summary

**Achievements**:
- ✅ Queryable struct generation (complete database rows)
- ✅ Insertable struct generation (INSERT operations)
- ✅ AsChangeset struct generation (UPDATE operations)
- ✅ Complete models.rs file generation
- ✅ Builder pattern support
- ✅ 95%+ test coverage

**Files Created**:
- `src/generators/rust/model_generator.py` (~600 lines)
- `tests/unit/generators/rust/test_model_generator.py` (~800 lines)
- `tests/integration/rust/test_models_generation.py` (~150 lines)

**Total**: ~1,550 lines

**Commit Count**: 4-5 focused commits

**Ready For**: Phase 3 (Query Builder Generation)

---

## 🔴 PHASE 3: Query Builder Generation (Day 3)

**Objective**: Generate Diesel query builders for CRUD operations

**Estimated Duration**: 8 hours
**Files Created**: ~8 files, ~1,400 lines
**Test Coverage Target**: 95%+

### Technical Context

Diesel queries use a strongly-typed DSL. We need to generate helper functions that encapsulate common CRUD patterns:

```rust
// queries.rs
use diesel::prelude::*;
use diesel::result::QueryResult;
use uuid::Uuid;
use super::models::{Contact, NewContact, UpdateContact};
use super::schema::crm::tb_contact;

pub struct ContactQueries;

impl ContactQueries {
    /// Find contact by UUID
    pub fn find_by_id(conn: &mut PgConnection, contact_id: Uuid) -> QueryResult<Contact> {
        tb_contact::table
            .filter(tb_contact::id.eq(contact_id))
            .filter(tb_contact::deleted_at.is_null())
            .first::<Contact>(conn)
    }

    /// List all active contacts
    pub fn list_active(conn: &mut PgConnection) -> QueryResult<Vec<Contact>> {
        tb_contact::table
            .filter(tb_contact::deleted_at.is_null())
            .order(tb_contact::created_at.desc())
            .load::<Contact>(conn)
    }

    /// Create new contact
    pub fn create(conn: &mut PgConnection, new_contact: NewContact) -> QueryResult<Contact> {
        diesel::insert_into(tb_contact::table)
            .values(&new_contact)
            .get_result::<Contact>(conn)
    }

    /// Update contact
    pub fn update(
        conn: &mut PgConnection,
        contact_id: Uuid,
        changeset: UpdateContact
    ) -> QueryResult<Contact> {
        diesel::update(tb_contact::table)
            .filter(tb_contact::id.eq(contact_id))
            .set(&changeset)
            .get_result::<Contact>(conn)
    }

    /// Soft delete contact
    pub fn soft_delete(conn: &mut PgConnection, contact_id: Uuid) -> QueryResult<Contact> {
        use chrono::Utc;
        diesel::update(tb_contact::table)
            .filter(tb_contact::id.eq(contact_id))
            .set(tb_contact::deleted_at.eq(Utc::now().naive_utc()))
            .get_result::<Contact>(conn)
    }

    /// Find contacts by company
    pub fn find_by_company(
        conn: &mut PgConnection,
        company_id: Uuid
    ) -> QueryResult<Vec<Contact>> {
        use super::schema::crm::tb_company;

        tb_contact::table
            .inner_join(tb_company::table.on(tb_contact::fk_company.eq(tb_company::pk_company)))
            .filter(tb_company::id.eq(company_id))
            .filter(tb_contact::deleted_at.is_null())
            .select(Contact::as_select())
            .load::<Contact>(conn)
    }
}
```

### Phase 3.1: Basic CRUD Query Generation (3 hours)

#### TDD Cycle 3.1.1: Find by ID Query

**🔴 RED: Find by ID Tests (30 minutes)**

**File**: `tests/unit/generators/rust/test_query_generator.py`

```python
"""
Tests for Diesel query builder generation
"""

import pytest
from src.generators.rust.query_generator import RustQueryGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestBasicCRUDQueries:
    """Test generation of basic CRUD queries"""

    @pytest.fixture
    def generator(self):
        return RustQueryGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
            ]
        )

    def test_generate_find_by_id(self, generator, simple_entity):
        """Test find_by_id query generation"""
        result = generator.generate_find_by_id(simple_entity)

        # Function signature
        assert "pub fn find_by_id(" in result
        assert "conn: &mut PgConnection" in result
        assert "contact_id: Uuid" in result
        assert "-> QueryResult<Contact>" in result

        # Query logic
        assert "tb_contact::table" in result
        assert ".filter(tb_contact::id.eq(contact_id))" in result
        assert ".filter(tb_contact::deleted_at.is_null())" in result  # Soft delete
        assert ".first::<Contact>(conn)" in result

    def test_generate_find_by_id_documentation(self, generator, simple_entity):
        """Test query documentation"""
        result = generator.generate_find_by_id(simple_entity)

        assert "/// Find contact by UUID" in result
        assert "/// Returns the contact if found and not deleted" in result

    def test_generate_list_all(self, generator, simple_entity):
        """Test list_active query generation"""
        result = generator.generate_list_all(simple_entity)

        assert "pub fn list_active(" in result
        assert "-> QueryResult<Vec<Contact>>" in result
        assert ".filter(tb_contact::deleted_at.is_null())" in result
        assert ".order(tb_contact::created_at.desc())" in result
        assert ".load::<Contact>(conn)" in result

    def test_generate_create(self, generator, simple_entity):
        """Test create query generation"""
        result = generator.generate_create(simple_entity)

        assert "pub fn create(" in result
        assert "new_contact: NewContact" in result
        assert "diesel::insert_into(tb_contact::table)" in result
        assert ".values(&new_contact)" in result
        assert ".get_result::<Contact>(conn)" in result

    def test_generate_update(self, generator, simple_entity):
        """Test update query generation"""
        result = generator.generate_update(simple_entity)

        assert "pub fn update(" in result
        assert "contact_id: Uuid" in result
        assert "changeset: UpdateContact" in result
        assert "diesel::update(tb_contact::table)" in result
        assert ".filter(tb_contact::id.eq(contact_id))" in result
        assert ".set(&changeset)" in result
        assert ".get_result::<Contact>(conn)" in result

    def test_generate_soft_delete(self, generator, simple_entity):
        """Test soft delete query generation"""
        result = generator.generate_soft_delete(simple_entity)

        assert "pub fn soft_delete(" in result
        assert "use chrono::Utc;" in result
        assert ".set(tb_contact::deleted_at.eq(Utc::now().naive_utc()))" in result

    def test_generate_hard_delete(self, generator, simple_entity):
        """Test hard delete query generation"""
        result = generator.generate_hard_delete(simple_entity)

        assert "pub fn hard_delete(" in result
        assert "diesel::delete(tb_contact::table)" in result
        assert ".filter(tb_contact::id.eq(contact_id))" in result
        assert ".execute(conn)" in result
```

**🟢 GREEN: Implement Basic Queries (1 hour 30 minutes)**

**File**: `src/generators/rust/query_generator.py`

```python
"""
Rust Query Generator

Generates Diesel query builder functions for CRUD operations.
"""

from typing import List
from src.core.ast_models import Entity
from src.generators.naming_utils import to_snake_case, to_pascal_case


class RustQueryGenerator:
    """
    Generates Diesel query builder functions

    Creates strongly-typed query helpers for:
    - Finding records (by ID, by field)
    - Listing records (with filters)
    - Creating records
    - Updating records
    - Deleting records (soft/hard)
    - Relationship queries

    Example:
        generator = RustQueryGenerator()
        find_query = generator.generate_find_by_id(entity)
    """

    def generate_find_by_id(self, entity: Entity) -> str:
        """
        Generate find_by_id query

        Finds a single record by UUID.
        Filters out soft-deleted records.

        Args:
            entity: SpecQL entity definition

        Returns:
            Complete function definition
        """
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        param_name = f"{snake_name}_id"

        return f"""    /// Find {snake_name} by UUID
    /// Returns the {snake_name} if found and not deleted
    pub fn find_by_id(
        conn: &mut PgConnection,
        {param_name}: Uuid
    ) -> QueryResult<{struct_name}> {{
        {table_name}::table
            .filter({table_name}::id.eq({param_name}))
            .filter({table_name}::deleted_at.is_null())
            .first::<{struct_name}>(conn)
    }}"""

    def generate_list_all(self, entity: Entity) -> str:
        """Generate list_active query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"

        return f"""    /// List all active {snake_name}s
    /// Returns all non-deleted {snake_name}s ordered by creation time
    pub fn list_active(
        conn: &mut PgConnection
    ) -> QueryResult<Vec<{struct_name}>> {{
        {table_name}::table
            .filter({table_name}::deleted_at.is_null())
            .order({table_name}::created_at.desc())
            .load::<{struct_name}>(conn)
    }}"""

    def generate_create(self, entity: Entity) -> str:
        """Generate create query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        new_struct = f"New{struct_name}"
        param_name = f"new_{snake_name}"

        return f"""    /// Create new {snake_name}
    /// Inserts a new {snake_name} and returns the created record
    pub fn create(
        conn: &mut PgConnection,
        {param_name}: {new_struct}
    ) -> QueryResult<{struct_name}> {{
        diesel::insert_into({table_name}::table)
            .values(&{param_name})
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_update(self, entity: Entity) -> str:
        """Generate update query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        update_struct = f"Update{struct_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Update {snake_name}
    /// Updates a {snake_name} by UUID with the provided changeset
    pub fn update(
        conn: &mut PgConnection,
        {id_param}: Uuid,
        changeset: {update_struct}
    ) -> QueryResult<{struct_name}> {{
        diesel::update({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .set(&changeset)
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_soft_delete(self, entity: Entity) -> str:
        """Generate soft delete query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Soft delete {snake_name}
    /// Marks a {snake_name} as deleted by setting deleted_at timestamp
    pub fn soft_delete(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<{struct_name}> {{
        use chrono::Utc;
        diesel::update({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .set({table_name}::deleted_at.eq(Utc::now().naive_utc()))
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_hard_delete(self, entity: Entity) -> str:
        """Generate hard delete query"""
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Hard delete {snake_name}
    /// Permanently deletes a {snake_name} from the database
    /// WARNING: This action cannot be undone
    pub fn hard_delete(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<usize> {{
        diesel::delete({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .execute(conn)
    }}"""
```

**🔧 REFACTOR + ✅ QA + Commit** (1 hour)

---

### Phase 3.2: Relationship Queries (2 hours)

#### TDD Cycle 3.2.1: Find by Foreign Key

**🔴 RED + 🟢 GREEN + 🔧 REFACTOR** (2 hours)

**File**: `tests/unit/generators/rust/test_query_generator.py` (add tests)

```python
class TestRelationshipQueries:
    """Test generation of relationship queries"""

    @pytest.fixture
    def entity_with_ref(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields=[
                FieldDefinition(name="email", field_type="text", required=True),
                FieldDefinition(
                    name="company",
                    field_type="ref",
                    ref_entity="Company",
                    required=False
                ),
            ]
        )

    def test_generate_find_by_foreign_key(self, generator, entity_with_ref):
        """Test find_by_company query generation"""
        result = generator.generate_find_by_reference(
            entity_with_ref,
            ref_field="company"
        )

        # Function signature
        assert "pub fn find_by_company(" in result
        assert "company_id: Uuid" in result
        assert "-> QueryResult<Vec<Contact>>" in result

        # Join logic
        assert "inner_join" in result
        assert "tb_company::table" in result
        assert ".on(tb_contact::fk_company.eq(tb_company::pk_company))" in result
        assert ".filter(tb_company::id.eq(company_id))" in result
```

**Implementation**: `src/generators/rust/query_generator.py` (add method)

```python
def generate_find_by_reference(
    self,
    entity: Entity,
    ref_field: str
) -> str:
    """
    Generate query to find by foreign key reference

    Creates a query that joins to the referenced table and filters by UUID.

    Args:
        entity: SpecQL entity definition
        ref_field: Name of the reference field (e.g., "company")

    Returns:
        Complete function definition with join
    """
    # Find the field definition
    field = next(f for f in entity.fields if f.name == ref_field)
    ref_entity_name = field.ref_entity

    struct_name = to_pascal_case(entity.name)
    snake_name = to_snake_case(entity.name)
    table_name = f"tb_{snake_name}"

    ref_snake = to_snake_case(ref_entity_name)
    ref_table = f"tb_{ref_snake}"
    fk_field = f"fk_{ref_snake}"

    return f"""    /// Find {snake_name}s by {ref_field}
    /// Returns all {snake_name}s associated with the given {ref_field}
    pub fn find_by_{ref_snake}(
        conn: &mut PgConnection,
        {ref_snake}_id: Uuid
    ) -> QueryResult<Vec<{struct_name}>> {{
        use super::schema::{entity.schema}::{ref_table};

        {table_name}::table
            .inner_join({ref_table}::table.on({table_name}::{fk_field}.eq({ref_table}::pk_{ref_snake})))
            .filter({ref_table}::id.eq({ref_snake}_id))
            .filter({table_name}::deleted_at.is_null())
            .select({struct_name}::as_select())
            .load::<{struct_name}>(conn)
    }}"""
```

---

### Phase 3.3: Complete Queries File Generation (2 hours)

**Objective**: Generate complete `queries.rs` file

**Implementation**: Add `generate_queries_file` method that combines all query types

---

### Phase 3.4: Pagination & Filtering (1 hour)

**Objective**: Generate paginated queries with optional filters

**Features**:
- `list_paginated(page, per_page)`
- `count_all()`
- Field-specific filters

---

### Phase 3 Summary

**Achievements**:
- ✅ Basic CRUD queries (find, list, create, update, delete)
- ✅ Soft delete support
- ✅ Relationship queries (find by foreign key)
- ✅ Pagination helpers
- ✅ Complete queries.rs file generation
- ✅ 95%+ test coverage

**Files Created**:
- `src/generators/rust/query_generator.py` (~500 lines)
- `tests/unit/generators/rust/test_query_generator.py` (~600 lines)
- Integration tests (~300 lines)

**Total**: ~1,400 lines

**Commit Count**: 4-5 focused commits

**Ready For**: Phase 4 (Handler Generation)

---

## 🔴 PHASE 4: Handler Generation (Day 4)

**Objective**: Generate Actix Web OR Axum HTTP handlers for REST API

**Estimated Duration**: 8 hours
**Files Created**: ~10 files, ~1,600 lines
**Test Coverage Target**: 90%+ (handlers are harder to unit test)

### Technical Context

Generate RESTful API handlers that call the query functions:

```rust
// handlers/contact.rs (Actix Web)
use actix_web::{web, HttpResponse, Result};
use diesel::r2d2::{self, ConnectionManager};
use diesel::PgConnection;
use uuid::Uuid;

use super::super::models::{NewContact, UpdateContact};
use super::super::queries::ContactQueries;

type DbPool = r2d2::Pool<ConnectionManager<PgConnection>>;

/// GET /contacts/:id
pub async fn get_contact(
    pool: web::Data<DbPool>,
    contact_id: web::Path<Uuid>
) -> Result<HttpResponse> {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let contact = web::block(move || {
        ContactQueries::find_by_id(&mut conn, *contact_id)
    })
    .await?
    .map_err(|_| HttpResponse::NotFound().finish())?;

    Ok(HttpResponse::Ok().json(contact))
}

/// GET /contacts
pub async fn list_contacts(
    pool: web::Data<DbPool>
) -> Result<HttpResponse> {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let contacts = web::block(move || {
        ContactQueries::list_active(&mut conn)
    })
    .await?
    .map_err(|_| HttpResponse::InternalServerError().finish())?;

    Ok(HttpResponse::Ok().json(contacts))
}

/// POST /contacts
pub async fn create_contact(
    pool: web::Data<DbPool>,
    new_contact: web::Json<NewContact>
) -> Result<HttpResponse> {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let contact = web::block(move || {
        ContactQueries::create(&mut conn, new_contact.into_inner())
    })
    .await?
    .map_err(|_| HttpResponse::InternalServerError().finish())?;

    Ok(HttpResponse::Created().json(contact))
}

// ... more handlers
```

### Phase 4.1: Framework Selection & Basic Handlers (3 hours)

**User Choice**: Actix Web (default) OR Axum

**TDD Cycles**:
- Generate GET handler
- Generate POST handler
- Generate PUT handler
- Generate DELETE handler

**Files**:
- `src/generators/rust/handler_generator.py`
- `tests/unit/generators/rust/test_handler_generator.py`

### Phase 4.2: Route Configuration (2 hours)

Generate route registration code:

```rust
pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/contacts")
            .route("", web::get().to(list_contacts))
            .route("", web::post().to(create_contact))
            .route("/{id}", web::get().to(get_contact))
            .route("/{id}", web::put().to(update_contact))
            .route("/{id}", web::delete().to(delete_contact))
    );
}
```

### Phase 4.3: Error Handling (1 hour)

Generate custom error types and conversions

### Phase 4.4: Validation & DTOs (2 hours)

Generate request validation logic

### Phase 4 Summary

**Achievements**:
- ✅ Handler generation for chosen framework
- ✅ Route configuration
- ✅ Error handling
- ✅ Request validation
- ✅ 90%+ test coverage

**Files Created**: ~1,600 lines
**Commit Count**: 4-5 commits

**Ready For**: Phase 5 (CLI Integration)

---

## 🔴 PHASE 5: CLI Integration & End-to-End Testing (Day 5)

**Objective**: Integrate with SpecQL CLI and verify end-to-end workflow

**Estimated Duration**: 8 hours
**Files Created**: ~6 files, ~800 lines

### Phase 5.1: CLI Command Implementation (3 hours)

**Objective**: Add `specql generate --target rust` command

**File**: `src/cli/generate.py` (extend existing)

```python
@click.option(
    "--target",
    type=click.Choice(["postgresql", "python_django", "rust"]),
    help="Target language for code generation",
)
def generate(entity_files, target, **kwargs):
    """Generate code from SpecQL entities"""

    if target == "rust":
        from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator

        orchestrator = RustGeneratorOrchestrator()
        orchestrator.generate(entity_files, **kwargs)
    # ... existing code
```

**Tests**:
```python
def test_cli_generate_rust(tmpdir):
    """Test CLI generates Rust code"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        'generate',
        'tests/fixtures/entities/contact.yaml',
        '--target', 'rust',
        '--output-dir', str(tmpdir)
    ])

    assert result.exit_code == 0
    assert (tmpdir / 'schema.rs').exists()
    assert (tmpdir / 'models.rs').exists()
    assert (tmpdir / 'queries.rs').exists()
```

### Phase 5.2: Orchestrator Implementation (2 hours)

**File**: `src/generators/rust/rust_generator_orchestrator.py`

```python
class RustGeneratorOrchestrator:
    """
    Orchestrates Rust code generation

    Coordinates:
    - Schema generation
    - Model generation
    - Query generation
    - Handler generation
    - Module structure

    Creates a complete, compilable Rust project.
    """

    def generate(self, entity_files: List[Path], **options):
        """Generate complete Rust backend"""
        # Parse entities
        entities = self._parse_entities(entity_files)

        # Generate schema.rs
        schema_gen = DieselTableGenerator()
        schema_rs = schema_gen.generate_schema_file(entities)

        # Generate models.rs
        model_gen = RustModelGenerator()
        models_rs = model_gen.generate_models_file(entities)

        # Generate queries.rs
        query_gen = RustQueryGenerator()
        queries_rs = query_gen.generate_queries_file(entities)

        # Generate handlers (optional)
        if options.get('with_handlers'):
            handler_gen = RustHandlerGenerator()
            handlers = handler_gen.generate_handlers(entities)

        # Write files
        self._write_files(...)
```

### Phase 5.3: End-to-End Integration Tests (2 hours)

**File**: `tests/integration/rust/test_end_to_end_generation.py`

```python
def test_full_rust_generation_pipeline():
    """Test complete SpecQL → Rust workflow"""
    # Given: SpecQL entity files
    entities = [
        parse_entity("tests/fixtures/entities/contact.yaml"),
        parse_entity("tests/fixtures/entities/company.yaml"),
    ]

    # When: Generate Rust code
    orchestrator = RustGeneratorOrchestrator()
    output_dir = Path("/tmp/test_rust_gen")
    orchestrator.generate(entities, output_dir=output_dir)

    # Then: All files created
    assert (output_dir / "schema.rs").exists()
    assert (output_dir / "models.rs").exists()
    assert (output_dir / "queries.rs").exists()

    # And: Code compiles
    result = subprocess.run(
        ["cargo", "check"],
        cwd=output_dir,
        capture_output=True
    )
    assert result.returncode == 0

def test_generated_code_passes_tests():
    """Test generated Rust code passes tests"""
    # Generate code
    # Run cargo test
    # Verify success
```

### Phase 5.4: Documentation & Examples (1 hour)

**File**: `docs/rust_generation_guide.md`

Complete usage guide with examples

### Phase 5 Summary

**Achievements**:
- ✅ CLI command implemented
- ✅ Orchestrator coordinates all generators
- ✅ End-to-end tests verify compilation
- ✅ Documentation complete
- ✅ Example projects

**Files Created**: ~800 lines
**Commit Count**: 3-4 commits

**Week 15 COMPLETE**

---

## 📊 Week 15 Final Summary

### Quantitative Achievements
- ✅ 3,000+ lines of generator code
- ✅ 3,500+ lines of test code
- ✅ 95%+ test coverage
- ✅ 40+ unit tests
- ✅ 10+ integration tests
- ✅ Generated code compiles with `cargo check`
- ✅ 20+ commits (4-5 per day)

### Files Created (Complete List)

**Generators**:
- `src/generators/rust/diesel_type_mapper.py` (~200 lines)
- `src/generators/rust/diesel_table_generator.py` (~300 lines)
- `src/generators/rust/model_generator.py` (~600 lines)
- `src/generators/rust/query_generator.py` (~500 lines)
- `src/generators/rust/handler_generator.py` (~600 lines)
- `src/generators/rust/rust_generator_orchestrator.py` (~300 lines)

**Tests**:
- `tests/unit/generators/rust/test_diesel_type_mapper.py` (~250 lines)
- `tests/unit/generators/rust/test_diesel_table_generator.py` (~350 lines)
- `tests/unit/generators/rust/test_model_generator.py` (~800 lines)
- `tests/unit/generators/rust/test_query_generator.py` (~600 lines)
- `tests/unit/generators/rust/test_handler_generator.py` (~500 lines)
- `tests/integration/rust/test_schema_generation.py` (~150 lines)
- `tests/integration/rust/test_models_generation.py` (~150 lines)
- `tests/integration/rust/test_end_to_end_generation.py` (~300 lines)

**Documentation**:
- `docs/rust_generation_guide.md`
- Updated CLI help text

### Qualitative Achievements
- ✅ Generated Rust code is idiomatic
- ✅ Diesel patterns match official examples
- ✅ Type safety maintained throughout
- ✅ Trinity pattern fully supported
- ✅ Foreign keys and relationships work correctly
- ✅ Code follows Rust conventions (snake_case, module structure)

### Integration Achievements
- ✅ CLI command works: `specql generate --target rust entities/*.yaml`
- ✅ Can generate full Rust backend from SpecQL
- ✅ Generated code passes `cargo check`
- ✅ Generated code passes `cargo test` (with DB setup)
- ✅ Documentation enables immediate usage

---

## 🚀 Next Steps (Week 16+)

After Week 15, the Rust pipeline is complete and production-ready. Future enhancements:

1. **Week 16**: Advanced query patterns (aggregation, subqueries)
2. **Week 17**: GraphQL integration (Juniper)
3. **Week 18**: WebSocket handlers
4. **Week 19**: Authentication/authorization middleware
5. **Week 20**: Caching layer integration

---

**Status**: 🟢 Fully Detailed and Ready to Execute
**Next Action**: Begin Phase 1.1 - Create `tests/unit/generators/rust/test_diesel_type_mapper.py`
**Estimated Completion**: 5 days of focused TDD development

---

## 📊 Week 15 Success Metrics

### Quantitative Metrics
- [ ] 1,200+ lines of generator code
- [ ] 2,000+ lines of test code
- [ ] 95%+ test coverage
- [ ] 10+ integration tests
- [ ] Generated code compiles with `cargo check`

### Qualitative Metrics
- [ ] Generated Rust code is idiomatic
- [ ] Diesel patterns match best practices
- [ ] Type safety maintained throughout
- [ ] Trinity pattern fully supported
- [ ] Foreign keys work correctly

### Integration Metrics
- [ ] CLI command works end-to-end
- [ ] Can generate full Rust backend from SpecQL
- [ ] Generated code passes `cargo test`
- [ ] Documentation complete

---

## 🚀 Getting Started

### Day 1 Morning (RIGHT NOW)

```bash
# Create directory structure
mkdir -p src/generators/rust
mkdir -p tests/unit/generators/rust
mkdir -p tests/integration/rust
mkdir -p tests/fixtures/entities

# Create __init__.py files
touch src/generators/rust/__init__.py
touch tests/unit/generators/rust/__init__.py

# Create first test file
# Then run: uv run pytest tests/unit/generators/rust/test_diesel_type_mapper.py -v
```

---

**Status**: 🟢 Ready to Execute
**Next Action**: Create `tests/unit/generators/rust/test_diesel_type_mapper.py`
**Estimated Completion**: End of Week 15 (5 days from start)
