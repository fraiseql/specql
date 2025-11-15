"""
Schema Analyzer

Parse CREATE TABLE DDL to UniversalEntity.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from src.core.universal_ast import UniversalEntity, UniversalField


class SchemaAnalyzer:
    """Analyze PostgreSQL DDL schemas"""

    def extract_create_table_statements(self, ddl: str) -> List[str]:
        """
        Extract all CREATE TABLE statements from DDL

        Args:
            ddl: SQL DDL content

        Returns:
            List of CREATE TABLE statement strings
        """
        # Pattern to match CREATE TABLE ... ; (handling multi-line)
        pattern = r"CREATE\s+TABLE\s+[^;]+;"
        matches = re.finditer(pattern, ddl, re.IGNORECASE | re.DOTALL)

        return [match.group(0) for match in matches]

    def parse_create_table(self, ddl: str) -> UniversalEntity:
        """
        Parse CREATE TABLE DDL to UniversalEntity

        Args:
            ddl: CREATE TABLE statement

        Returns:
            UniversalEntity
        """
        # Extract table name
        schema, table_name = self._extract_table_name(ddl)

        # Extract entity name (remove tb_ prefix if present)
        entity_name = self._table_to_entity_name(table_name)

        # Extract columns
        columns = self._extract_columns(ddl)

        # Parse columns to fields
        fields = []
        for col in columns:
            field = self._parse_column_to_field(col)
            if field:
                fields.append(field)

        # Create entity
        entity = UniversalEntity(
            name=entity_name, schema=schema, fields=fields, actions=[]
        )

        return entity

    def _extract_table_name(self, ddl: str) -> Tuple[str, str]:
        """
        Extract schema and table name from CREATE TABLE DDL

        Args:
            ddl: CREATE TABLE statement

        Returns:
            Tuple of (schema, table_name)
        """
        # Pattern: CREATE TABLE [schema.]table_name (handles quoted identifiers)
        # Matches: schema.table, "schema"."table", table, "table"
        pattern = r'CREATE\s+TABLE\s+(?:(?:"([^"]+)"|(\w+))\.)?(?:"([^"]+)"|(\w+))'
        match = re.search(pattern, ddl, re.IGNORECASE)

        if not match:
            raise ValueError("Could not extract table name from DDL")

        # Schema is either quoted (group 1) or unquoted (group 2)
        schema = match.group(1) or match.group(2) or "public"
        # Table is either quoted (group 3) or unquoted (group 4)
        table_name = match.group(3) or match.group(4)

        return schema, table_name

    def _table_to_entity_name(self, table_name: str) -> str:
        """
        Convert table name to entity name

        Examples:
            tb_contact → Contact
            contact → Contact
            tb_order_item → OrderItem
        """
        # Remove tb_ prefix
        name = re.sub(r"^tb_", "", table_name, flags=re.IGNORECASE)

        # Convert snake_case to PascalCase
        parts = name.split("_")
        entity_name = "".join(word.capitalize() for word in parts)

        return entity_name

    def _extract_columns(self, ddl: str) -> List[Dict[str, Any]]:
        """
        Extract column definitions from CREATE TABLE

        Returns:
            List of column definition dicts
        """
        # Extract content between parentheses
        pattern = r"CREATE\s+TABLE\s+[^(]+\((.*)\)"
        match = re.search(pattern, ddl, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        columns_section = match.group(1)

        # Split by commas (but not commas inside parentheses)
        column_defs = self._split_column_definitions(columns_section)

        columns = []
        for col_def in column_defs:
            col_def = col_def.strip()

            # Skip constraints
            if self._is_constraint(col_def):
                continue

            column = self._parse_column_definition(col_def)
            if column:
                columns.append(column)

        return columns

    def _split_column_definitions(self, columns_section: str) -> List[str]:
        """Split column definitions, respecting nested parentheses"""
        definitions = []
        current = ""
        paren_depth = 0

        for char in columns_section:
            if char == "(":
                paren_depth += 1
                current += char
            elif char == ")":
                paren_depth -= 1
                current += char
            elif char == "," and paren_depth == 0:
                definitions.append(current.strip())
                current = ""
            else:
                current += char

        # Add last definition
        if current.strip():
            definitions.append(current.strip())

        return definitions

    def _is_constraint(self, definition: str) -> bool:
        """Check if definition is a constraint, not a column"""
        constraint_keywords = [
            "PRIMARY KEY",
            "FOREIGN KEY",
            "UNIQUE",
            "CHECK",
            "CONSTRAINT",
        ]

        definition_upper = definition.upper()

        # If it starts with a constraint keyword, it's a constraint
        for kw in constraint_keywords:
            if definition_upper.startswith(kw):
                return True

        # Otherwise, it's a column definition (even if it contains constraint keywords)
        return False

    def _parse_column_definition(self, col_def: str) -> Optional[Dict[str, Any]]:
        """
        Parse single column definition

        Example: 'id character varying(50) NOT NULL'

        Returns:
            Dict with column properties
        """
        parts = col_def.strip().split()
        if len(parts) < 2:
            return None

        column_name = parts[0]

        # Find the data type (may be multiple words)
        data_type_parts = []
        i = 1
        while i < len(parts):
            part = parts[i]
            data_type_parts.append(part)
            # If this part ends with a closing paren or doesn't contain paren, it might be the end
            if ")" in part or "(" not in part:
                # Check if next part looks like a constraint
                if i + 1 < len(parts) and parts[i + 1].upper() in [
                    "NOT",
                    "DEFAULT",
                    "UNIQUE",
                    "PRIMARY",
                    "REFERENCES",
                ]:
                    break
                elif i + 1 < len(parts) and parts[i + 1].startswith("DEFAULT"):
                    break
            i += 1

        data_type = " ".join(data_type_parts)
        constraints = " ".join(parts[i:])

        # Parse constraints
        is_nullable = "NOT NULL" not in constraints.upper()
        is_unique = "UNIQUE" in constraints.upper()
        has_default = "DEFAULT" in constraints.upper()
        default_value = (
            self._extract_default_value(constraints) if has_default else None
        )

        return {
            "name": column_name,
            "data_type": data_type,
            "nullable": "YES" if is_nullable else "NO",
            "unique": is_unique,
            "default": default_value,
        }

    def _extract_default_value(self, constraints: str) -> Optional[str]:
        """Extract default value from constraint string"""
        pattern = r"DEFAULT\s+([^,\s]+(?:\s*\([^)]*\))?)"
        match = re.search(pattern, constraints, re.IGNORECASE)

        if match:
            return match.group(1)

        return None

    def _parse_column_to_field(
        self, column: Dict[str, Any]
    ) -> Optional[UniversalField]:
        """
        Convert column definition to UniversalField

        Args:
            column: Column definition dict

        Returns:
            UniversalField or None if should skip
        """
        from src.parsers.plpgsql.type_mapper import TypeMapper

        column_name = column["name"]

        # Skip Trinity and audit fields as they are auto-generated
        column_name_lower = column_name.lower()
        if column_name_lower.startswith("pk_") or column_name_lower in [
            "id",
            "identifier",
            "created_at",
            "updated_at",
            "deleted_at",
        ]:
            return None

        # Map PostgreSQL type to SpecQL type
        type_mapper = TypeMapper()
        field_type = type_mapper.map_postgres_type(column["data_type"], column_name)

        return UniversalField(
            name=column_name,
            type=field_type,
            required=column["nullable"] == "NO",
            unique=column.get("unique", False),
            default=column["default"],
            postgres_type=column["data_type"],
            character_maximum_length=column.get("character_maximum_length"),
        )
