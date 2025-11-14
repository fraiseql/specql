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
    INT2 = "Int2"  # smallint (16-bit)
    INT4 = "Int4"  # integer (32-bit) - most common
    INT8 = "Int8"  # bigint (64-bit)

    # Decimal types
    NUMERIC = "Numeric"  # numeric/decimal with arbitrary precision
    FLOAT4 = "Float4"  # real (32-bit float)
    FLOAT8 = "Float8"  # double precision (64-bit float)

    # Text types
    VARCHAR = "Varchar"  # variable-length string (most common)
    TEXT = "Text"  # unlimited text

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
    JSONB = "Jsonb"  # Binary JSON (recommended)

    # Arrays
    ARRAY = "Array"

    # Binary
    BYTEA = "Bytea"

    # Custom types (require setup)
    VECTOR = "Vector"  # pgvector extension

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
        "integer": DieselSqlType.INT4,  # Default integer size
        "decimal": DieselSqlType.NUMERIC,
        "text": DieselSqlType.VARCHAR,
        "boolean": DieselSqlType.BOOL,
        "timestamp": DieselSqlType.TIMESTAMPTZ,
        "date": DieselSqlType.DATE,
        "time": DieselSqlType.TIME,
        "uuid": DieselSqlType.UUID,
        "json": DieselSqlType.JSONB,
        "binary": DieselSqlType.BYTEA,
        "enum": DieselSqlType.VARCHAR,  # Enums stored as text
        "vector": DieselSqlType.VECTOR,
        "ref": DieselSqlType.INT4,  # Foreign keys are int4
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
        self, field_type: str, required: bool = True, ref_entity: Optional[str] = None
    ) -> DieselFieldType:
        """
        Map SpecQL field type to Diesel SQL type

        Args:
            field_type: SpecQL type (e.g., "text", "integer:big", "text[]", "text?")
            required: Whether field is required (False = Nullable)
            ref_entity: Referenced entity name for ref fields

        Returns:
            DieselFieldType with complete type information

        Raises:
            ValueError: If field_type is unknown
        """
        # Handle nullable syntax (text?, integer?, etc.)
        if field_type.endswith("?"):
            field_type = field_type[:-1]  # Remove ?
            required = False

        # Handle array types (text[], integer[], etc.)
        is_array = field_type.endswith("[]")
        if is_array:
            field_type = field_type[:-2]  # Remove []

        # Handle reference syntax (ref(EntityName))
        if field_type.startswith("ref(") and field_type.endswith(")"):
            ref_entity = field_type[4:-1]  # Extract EntityName
            field_type = "ref"
        elif field_type == "ref" and ref_entity is None:
            # If it's just "ref" without entity, that's an error
            raise ValueError(
                "Reference type 'ref' must specify an entity, e.g., 'ref(Company)'"
            )

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
            base_type=base_type, is_nullable=not required, is_array=is_array
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
            field_name, DieselFieldType(DieselSqlType.VARCHAR, is_nullable=True)
        )

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
