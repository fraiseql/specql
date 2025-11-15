"""
Type Mapper

Map PostgreSQL data types to SpecQL field types.
"""

from typing import Optional
from src.core.universal_ast import FieldType
import re


class TypeMapper:
    """Map PostgreSQL types to SpecQL types"""

    # Type mapping table
    TYPE_MAP = {
        # Integer types
        "INTEGER": FieldType.INTEGER,
        "INT": FieldType.INTEGER,
        "INT4": FieldType.INTEGER,
        "SMALLINT": FieldType.INTEGER,
        "INT2": FieldType.INTEGER,
        "BIGINT": FieldType.INTEGER,
        "INT8": FieldType.INTEGER,
        # Text types
        "TEXT": FieldType.TEXT,
        "VARCHAR": FieldType.TEXT,
        "CHAR": FieldType.TEXT,
        "CHARACTER VARYING": FieldType.TEXT,
        "CHARACTER": FieldType.TEXT,
        # Boolean
        "BOOLEAN": FieldType.BOOLEAN,
        "BOOL": FieldType.BOOLEAN,
        # Numeric/Decimal (map to TEXT for now, could be RICH later)
        "NUMERIC": FieldType.TEXT,
        "DECIMAL": FieldType.TEXT,
        "REAL": FieldType.TEXT,
        "FLOAT": FieldType.TEXT,
        "DOUBLE PRECISION": FieldType.TEXT,
        # Date/Time
        "TIMESTAMP": FieldType.DATETIME,
        "TIMESTAMPTZ": FieldType.DATETIME,
        "TIMESTAMP WITHOUT TIME ZONE": FieldType.DATETIME,
        "TIMESTAMP WITH TIME ZONE": FieldType.DATETIME,
        "DATE": FieldType.TEXT,  # Map to TEXT for now
        "TIME": FieldType.TEXT,  # Map to TEXT for now
        "TIMETZ": FieldType.TEXT,  # Map to TEXT for now
        # UUID (map to TEXT for now)
        "UUID": FieldType.TEXT,
        # JSON (map to TEXT for now)
        "JSON": FieldType.TEXT,
        "JSONB": FieldType.TEXT,
        # Arrays
        "ARRAY": FieldType.LIST,
    }

    def map_postgres_type(
        self, pg_type: str, column_name: Optional[str] = None
    ) -> FieldType:
        """
        Map PostgreSQL type to SpecQL FieldType

        Args:
            pg_type: PostgreSQL data type (e.g., 'INTEGER', 'TEXT', 'VARCHAR(255)')
            column_name: Column name (for context-based detection)

        Returns:
            SpecQL FieldType
        """
        # Normalize type (remove size specifications)
        base_type = self._extract_base_type(pg_type)

        # Check for foreign key pattern
        if column_name and self._is_foreign_key(column_name):
            return FieldType.REFERENCE

        # Check for array types
        if "[]" in pg_type or "ARRAY" in pg_type.upper():
            return FieldType.LIST

        # Map type
        field_type = self.TYPE_MAP.get(base_type.upper())

        if field_type:
            return field_type

        # Default to TEXT for unknown types
        return FieldType.TEXT

    def _extract_base_type(self, pg_type: str) -> str:
        """
        Extract base type from PostgreSQL type specification

        Examples:
            VARCHAR(255) → VARCHAR
            NUMERIC(10,2) → NUMERIC
            INTEGER → INTEGER
        """
        # Remove anything in parentheses
        base_type = re.sub(r"\([^)]*\)", "", pg_type)

        # Remove array brackets
        base_type = base_type.replace("[]", "")

        return base_type.strip()

    def _is_foreign_key(self, column_name: str) -> bool:
        """
        Detect if column is likely a foreign key

        Patterns:
            fk_* → foreign key
            *_id (except 'id') → foreign key
        """
        column_lower = column_name.lower()

        # fk_ prefix
        if column_lower.startswith("fk_"):
            return True

        # *_id suffix (but not just 'id')
        if column_lower.endswith("_id") and column_lower != "id":
            return True

        return False

    def extract_reference_target(self, column_name: str) -> Optional[str]:
        """
        Extract referenced entity name from foreign key column name

        Examples:
            fk_company → Company
            company_id → Company
            fk_order_item → OrderItem
        """
        column_lower = column_name.lower()

        # Remove fk_ prefix
        name = re.sub(r"^fk_", "", column_lower)

        # Remove _id suffix
        name = re.sub(r"_id$", "", name)

        # Convert to PascalCase
        parts = name.split("_")
        entity_name = "".join(word.capitalize() for word in parts)

        return entity_name
