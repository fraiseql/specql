"""
Base Table (tb_) Generator

Generates normalized storage tables with complete Trinity pattern:
- pk_* INTEGER primary key
- id UUID stable identifier
- tenant_id for multi-tenant schemas
- Full 6-field audit trail
- Business fields with proper SQL types
- Foreign key constraints
- Comprehensive indexing
"""

from dataclasses import dataclass
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from src.core.ast_models import Entity


@dataclass
class SQLField:
    """SQL field representation"""
    name: str
    sql_type: str
    required: bool
    default: Optional[str] = None
    description: str = ""


@dataclass
class ForeignKey:
    """Foreign key constraint"""
    column: str
    ref_schema: str
    ref_table: str
    ref_column: str
    entity_name: str = ""  # Add entity name for better naming

    @property
    def name(self) -> str:
        """Generate FK constraint name"""
        # fk_contact_company
        if self.entity_name:
            return f"fk_{self.entity_name.lower()}_{self.column}"
        return f"fk_{self.column}"


@dataclass
class Index:
    """Index definition"""
    name: str
    columns: List[str]
    method: Optional[str] = None
    comment: str = ""


@dataclass
class Constraint:
    """Check constraint"""
    name: str
    definition: str


class BaseTableGenerator:
    """Generates base tables (tb_) with Trinity pattern"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("base_table.sql.j2")

    def generate(self, entity: Entity) -> str:
        """
        Generate base table SQL for entity

        Args:
            entity: Entity to generate table for

        Returns:
            SQL DDL for base table with Trinity pattern
        """
        table_name = f"tb_{entity.name.lower()}"

        # Convert Entity fields to SQL fields
        fields = self._convert_fields(entity)

        # Generate foreign keys
        foreign_keys = self._generate_foreign_keys(entity)

        # Generate indexes
        indexes = self._generate_indexes(entity)

        # Generate constraints
        constraints = self._generate_constraints(entity)

        # Render template
        return self.template.render(
            entity=entity,
            schema=entity.schema,
            table_name=table_name,
            fields=fields,
            foreign_keys=foreign_keys,
            indexes=indexes,
            constraints=constraints
        )

    def _convert_fields(self, entity: Entity) -> List[SQLField]:
        """Convert Entity fields to SQL fields"""
        sql_fields = []

        for field_name, field_def in entity.fields.items():
            sql_type = self._map_field_type(field_def)

            sql_fields.append(SQLField(
                name=field_name,
                sql_type=sql_type,
                required=not field_def.nullable,
                default=field_def.default,
                description=field_def.description or ""
            ))

        return sql_fields

    def _map_field_type(self, field_def) -> str:
        """
        Map field type to SQL type with enhanced subtype support

        Format: type:subtype
        - integer → context-aware (BIGINT for IDs, SMALLINT for age, INTEGER default)
        - integer:small → SMALLINT
        - integer:int → INTEGER
        - integer:big → BIGINT
        - decimal → context-aware (NUMERIC(10,2) for money)
        - decimal:money → NUMERIC(10,2)
        - decimal:geo → NUMERIC(9,6)
        - decimal:percent → NUMERIC(5,4)
        - decimal:high → NUMERIC(20,10)
        - text → TEXT (default)
        - text:tiny → VARCHAR(10)
        - text:short → VARCHAR(255)
        - text:long → TEXT
        """
        # Parse type:subtype format
        type_name = field_def.type_name
        if ':' in type_name:
            base_type, subtype = type_name.split(':', 1)
        else:
            base_type = type_name
            subtype = None

        # Handle ref and enum (no subtypes)
        if base_type == "ref":
            return "INTEGER"  # Trinity: FK to pk_* INTEGER

        if base_type == "enum":
            return "TEXT"

        if base_type == "list":
            return "TEXT[]"

        # Integer subtypes
        if base_type == "integer":
            if subtype == "small":
                return "SMALLINT"
            elif subtype == "int":
                return "INTEGER"
            elif subtype == "big":
                return "BIGINT"
            else:
                # Context-aware inference
                return self._infer_integer_type(field_def)

        # Decimal subtypes
        if base_type == "decimal":
            if subtype == "money":
                return "NUMERIC(10,2)"
            elif subtype == "geo":
                return "NUMERIC(9,6)"
            elif subtype == "percent":
                return "NUMERIC(5,4)"
            elif subtype == "high":
                return "NUMERIC(20,10)"
            else:
                # Context-aware inference
                return self._infer_decimal_type(field_def)

        # Text subtypes
        if base_type == "text":
            if subtype == "tiny":
                return "VARCHAR(10)"
            elif subtype == "short":
                return "VARCHAR(255)"
            elif subtype == "long":
                return "TEXT"
            else:
                # Context-aware inference
                return self._infer_text_type(field_def)

        # Default mappings
        type_map = {
            "boolean": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMPTZ",
            "json": "JSONB",
        }

        return type_map.get(base_type, "TEXT")

    def _infer_integer_type(self, field_def) -> str:
        """Infer integer SQL type based on field name and context"""
        field_lower = field_def.name.lower()

        # IDs are always BIGINT for scalability
        if field_lower.endswith('_id') or field_lower == 'id':
            return "BIGINT"

        # Age fields are SMALLINT (0-255 is plenty)
        if 'age' in field_lower:
            return "SMALLINT"

        # Count, quantity usually fit in INTEGER
        if any(word in field_lower for word in ['count', 'quantity', 'number']):
            return "INTEGER"

        # Default to INTEGER for backward compatibility
        return "INTEGER"

    def _infer_decimal_type(self, field_def) -> str:
        """Infer decimal SQL type based on field name"""
        field_lower = field_def.name.lower()

        # Money fields: NUMERIC(10,2)
        if any(word in field_lower for word in ['price', 'amount', 'cost', 'fee', 'salary', 'revenue']):
            return "NUMERIC(10,2)"

        # Geographic coordinates: NUMERIC(9,6)
        if any(word in field_lower for word in ['lat', 'lon', 'latitude', 'longitude', 'coord']):
            return "NUMERIC(9,6)"

        # Percentages: NUMERIC(5,4)
        if any(word in field_lower for word in ['percent', 'rate', 'ratio']):
            return "NUMERIC(5,4)"

        # Default to general NUMERIC
        return "NUMERIC"

    def _infer_text_type(self, field_def) -> str:
        """Infer text SQL type based on field name"""
        field_lower = field_def.name.lower()

        # Code/slug fields are tiny
        if any(word in field_lower for word in ['code', 'slug', 'key', 'token']):
            return "VARCHAR(10)"

        # Phone numbers are shorter
        if 'phone' in field_lower:
            return "VARCHAR(50)"

        # Email, URL, username are short
        if any(word in field_lower for word in ['email', 'url', 'link', 'username']):
            return "VARCHAR(255)"

        # Description, content, notes are long
        if any(word in field_lower for word in ['description', 'content', 'note', 'comment', 'bio']):
            return "TEXT"

        # Default to TEXT for flexibility
        return "TEXT"

    def _generate_foreign_keys(self, entity: Entity) -> List[ForeignKey]:
        """Generate foreign key constraints for ref fields"""
        fks = []

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                ref_entity_lower = field_def.reference_entity.lower()

                fks.append(ForeignKey(
                    column=field_name,
                    ref_schema=field_def.reference_schema or entity.schema,
                    ref_table=f"tb_{ref_entity_lower}",
                    ref_column=f"pk_{ref_entity_lower}",
                    entity_name=entity.name
                ))

        return fks

    def _generate_indexes(self, entity: Entity) -> List[Index]:
        """Generate indexes for enum fields and other indexed columns"""
        indexes = []

        for field_name, field_def in entity.fields.items():
            # Index enum fields for query performance
            if field_def.type_name == "enum":
                indexes.append(Index(
                    name=f"idx_tb_{entity.name.lower()}_{field_name}",
                    columns=[field_name],
                    comment=f"Index on enum field {field_name}"
                ))

        return indexes

    def _generate_constraints(self, entity: Entity) -> List[Constraint]:
        """Generate check constraints for enum fields"""
        constraints = []

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "enum" and field_def.values:
                enum_list = ", ".join(f"'{v}'" for v in field_def.values)

                constraints.append(Constraint(
                    name=f"chk_tb_{entity.name.lower()}_{field_name}",
                    definition=f"CHECK ({field_name} IN ({enum_list}))"
                ))

        return constraints