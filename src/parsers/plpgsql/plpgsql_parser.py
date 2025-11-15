"""
Main PL/pgSQL Parser

Entry point for PostgreSQL → SpecQL reverse engineering.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import psycopg
from psycopg.rows import dict_row

from src.core.universal_ast import UniversalEntity
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.parsers.plpgsql.function_analyzer import FunctionAnalyzer
from src.parsers.plpgsql.pattern_detector import PatternDetector


class PLpgSQLParser:
    """
    Parse PostgreSQL databases and DDL to SpecQL entities

    Supports:
    - Live database connection parsing
    - DDL file parsing
    - DDL string parsing
    - Pattern detection (Trinity, audit fields)
    - Function → action conversion
    """

    def __init__(self, confidence_threshold: float = 0.70):
        """
        Initialize parser

        Args:
            confidence_threshold: Minimum confidence for pattern detection (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.schema_analyzer = SchemaAnalyzer()
        self.function_analyzer = FunctionAnalyzer()
        self.pattern_detector = PatternDetector()

    def parse_database(
        self,
        connection_string: str,
        schemas: Optional[List[str]] = None,
        include_functions: bool = True,
    ) -> List[UniversalEntity]:
        """
        Parse entire database to SpecQL entities

        Args:
            connection_string: PostgreSQL connection string
            schemas: List of schemas to parse (None = all non-system schemas)
            include_functions: Whether to parse PL/pgSQL functions as actions

        Returns:
            List of parsed UniversalEntity objects
        """
        entities = []

        with psycopg.connect(connection_string) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get list of schemas to parse
                if schemas is None:
                    schemas = self._get_user_schemas(cur)

                # Parse each schema
                for schema in schemas:
                    schema_entities = self._parse_schema(cur, schema, include_functions)
                    entities.extend(schema_entities)

        return entities

    def parse_ddl_file(self, file_path: str) -> List[UniversalEntity]:
        """
        Parse DDL file to SpecQL entities

        Args:
            file_path: Path to SQL file

        Returns:
            List of parsed entities
        """
        ddl_content = Path(file_path).read_text()
        return self.parse_ddl_string(ddl_content)

    def parse_ddl_string(self, ddl: str) -> List[UniversalEntity]:
        """
        Parse DDL string to SpecQL entities

        Args:
            ddl: SQL DDL content

        Returns:
            List of parsed entities
        """
        # Extract CREATE TABLE statements
        tables = self.schema_analyzer.extract_create_table_statements(ddl)

        entities = []
        for table_ddl in tables:
            # First detect patterns from raw DDL
            patterns = self.pattern_detector.detect_patterns_from_ddl(table_ddl)

            # Only parse entity if confidence meets threshold
            if patterns.get("confidence", 0.0) >= self.confidence_threshold:
                entity = self.schema_analyzer.parse_create_table(table_ddl)
                entities.append(entity)

        return entities

    def _get_user_schemas(self, cursor) -> List[str]:
        """Get list of user-defined schemas (exclude system schemas)"""
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        return [row["schema_name"] for row in cursor.fetchall()]

    def _parse_schema(
        self, cursor, schema: str, include_functions: bool
    ) -> List[UniversalEntity]:
        """Parse all tables in a schema"""
        entities = []

        # Get all tables in schema
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """,
            (schema,),
        )

        tables = cursor.fetchall()

        for table in tables:
            entity = self._parse_table_from_db(cursor, schema, table["table_name"])

            if entity is None:
                continue  # Skip tables that don't meet confidence threshold

            if include_functions:
                # Find associated functions
                functions = self._get_table_functions(
                    cursor, schema, table["table_name"]
                )
                entity.actions = self.function_analyzer.parse_functions(functions)

            entities.append(entity)

        return entities

    def _parse_table_from_db(
        self, cursor, schema: str, table_name: str
    ) -> Optional[UniversalEntity]:
        """Parse single table from database"""
        # Get table DDL
        # PostgreSQL doesn't have SHOW CREATE TABLE, so we reconstruct it
        ddl = self._reconstruct_table_ddl(cursor, schema, table_name)

        # Detect patterns from DDL first
        patterns = self.pattern_detector.detect_patterns_from_ddl(ddl)

        # Only parse entity if confidence meets threshold
        if patterns.get("confidence", 0.0) >= self.confidence_threshold:
            # Parse the DDL
            entity = self.schema_analyzer.parse_create_table(ddl)

            # Extract and set foreign key references
            self._set_foreign_key_references(cursor, schema, table_name, entity)

            # Extract and set unique constraints
            self._set_unique_constraints(cursor, schema, table_name, entity)

            # Detect patterns on parsed entity (for future use)
            self.pattern_detector.detect_patterns(entity)

            return entity

        return None

    def _reconstruct_table_ddl(self, cursor, schema: str, table_name: str) -> str:
        """Reconstruct CREATE TABLE DDL from information_schema"""
        # This is a simplified version - full implementation would be more complex
        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """,
            (schema, table_name),
        )

        columns = cursor.fetchall()

        # Build CREATE TABLE statement
        ddl_parts = [f"CREATE TABLE {schema}.{table_name} ("]

        for col in columns:
            # Handle both dict and tuple formats
            if isinstance(col, dict):
                col_name = col["column_name"]
                data_type = col["data_type"]
                is_nullable = col["is_nullable"]
                column_default = col["column_default"]
                char_max_len = col["character_maximum_length"]
                numeric_precision = col.get("numeric_precision")
                numeric_scale = col.get("numeric_scale")
            else:
                # Tuple format: (column_name, data_type, is_nullable, column_default, character_maximum_length, numeric_precision, numeric_scale)
                col_name = col[0]
                data_type = col[1]
                is_nullable = col[2]
                column_default = col[3]
                char_max_len = col[4]
                numeric_precision = col[5] if len(col) > 5 else None
                numeric_scale = col[6] if len(col) > 6 else None

            # Add length for character varying
            if data_type == "character varying" and char_max_len:
                data_type = f"character varying({char_max_len})"

            # Add precision/scale for numeric types
            if (
                data_type in ("numeric", "decimal")
                and numeric_precision is not None
                and numeric_scale is not None
            ):
                data_type = f"numeric({numeric_precision},{numeric_scale})"

            col_def = f"    {col_name} {data_type}"

            if is_nullable == "NO":
                col_def += " NOT NULL"

            if column_default:
                col_def += f" DEFAULT {column_default}"

            ddl_parts.append(col_def + ",")

        # Remove last comma
        ddl_parts[-1] = ddl_parts[-1].rstrip(",")
        ddl_parts.append(");")

        return "\n".join(ddl_parts)

    def _get_table_functions(
        self, cursor, schema: str, table_name: str
    ) -> List[Dict[str, Any]]:
        """Get PL/pgSQL functions associated with a table"""
        # Get all functions in the schema
        cursor.execute(
            """
            SELECT
                routine_name,
                routine_definition,
                external_language
            FROM information_schema.routines
            WHERE routine_schema = %s
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """,
            (schema,),
        )

        all_functions = cursor.fetchall()

        # Filter for PL/pgSQL (case insensitive)
        functions = [
            f for f in all_functions if f["external_language"].upper() == "PLPGSQL"
        ]

        # Filter functions that reference the table
        table_functions = []
        table_lower = table_name.lower()

        for func in functions:
            # Check if function name or body references the table
            func_name = func["routine_name"].lower()
            func_body = (
                func["routine_definition"].lower() if func["routine_definition"] else ""
            )

            # Match if function name contains table name (e.g., create_contact for tb_contact)
            # or if function body contains table reference
            if (
                table_lower in func_name
                or table_lower in func_body
                or table_name in func_body
            ):
                table_functions.append(func)

        return table_functions

    def _set_foreign_key_references(
        self, cursor, schema: str, table_name: str, entity: UniversalEntity
    ) -> None:
        """Extract foreign key constraints and set references on fields"""
        cursor.execute(
            """
            SELECT
                kcu.column_name,
                ccu.table_schema AS referenced_schema,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """,
            (schema, table_name),
        )

        fk_rows = cursor.fetchall()

        # Group by constraint (for multi-column FKs, though we handle single column for now)
        for row in fk_rows:
            col_name = row["column_name"]
            row["referenced_schema"]
            ref_table = row["referenced_table"]
            row["referenced_column"]

            # Convert table name to entity name (remove tb_ prefix)
            ref_entity_name = ref_table.replace("tb_", "").capitalize()

            # Set reference on the field
            for field in entity.fields:
                if field.name == col_name:
                    field.references = ref_entity_name
                    break

    def _set_unique_constraints(
        self, cursor, schema: str, table_name: str, entity: UniversalEntity
    ) -> None:
        """Extract unique constraints and set unique=True on fields"""
        cursor.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'UNIQUE'
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """,
            (schema, table_name),
        )

        unique_rows = cursor.fetchall()

        # For now, handle single-column unique constraints
        # Multi-column unique constraints would need more complex handling
        unique_columns = {row["column_name"] for row in unique_rows}

        # Set unique=True on fields
        for field in entity.fields:
            if field.name in unique_columns:
                field.unique = True
