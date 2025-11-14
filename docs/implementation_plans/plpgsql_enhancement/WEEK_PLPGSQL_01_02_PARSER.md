# Week PL/pgSQL 1-2: PL/pgSQL Parser & Reverse Engineering

**Date**: TBD
**Duration**: 2 weeks (80 hours)
**Status**: 📅 Planned
**Objective**: Create comprehensive PostgreSQL → SpecQL reverse engineering parser

**Prerequisites**:
- Understanding of PostgreSQL DDL syntax
- Understanding of PL/pgSQL function syntax
- Familiarity with SpecQL YAML format
- Access to sample PostgreSQL databases

**Output**:
- Complete PLpgSQLParser implementation
- 40+ parser unit tests
- 10+ integration tests
- Parser documentation

---

## 🎯 Executive Summary

This 2-week sprint creates the **missing foundation** for PL/pgSQL support: a comprehensive parser that can reverse engineer existing PostgreSQL databases into SpecQL YAML.

### Why This Matters

Currently, SpecQL has excellent **forward generation** (SpecQL → SQL) but weak **reverse engineering** (SQL → SpecQL). This creates an asymmetry:

- **Java**: ✅ Spring Boot → SpecQL → Spring Boot (complete bidirectional)
- **Rust**: ✅ Diesel → SpecQL → Diesel (complete bidirectional)
- **PL/pgSQL**: ⚠️ SpecQL → PostgreSQL (only one direction)

### Key Objectives

1. **Parse DDL to Entities**: `CREATE TABLE` → SpecQL entity
2. **Detect Patterns**: Recognize Trinity pattern, audit fields, deduplication
3. **Parse Functions to Actions**: PL/pgSQL functions → SpecQL actions
4. **Handle Complex Types**: Enums, composites, arrays, JSON
5. **Extract Relationships**: Foreign keys → references

---

## 📅 Week 1: Parser Implementation

### Day 1: Architecture & Schema Analyzer (8 hours)

**Objective**: Set up parser architecture and basic table parsing

#### Morning (4 hours): Project Setup

**Step 1.1: Create parser directory structure** (1 hour)

```bash
cd /home/lionel/code/specql

# Create parser package
mkdir -p src/parsers/plpgsql
touch src/parsers/plpgsql/__init__.py

# Create test structure
mkdir -p tests/unit/parsers/plpgsql
touch tests/unit/parsers/plpgsql/__init__.py

mkdir -p tests/integration/plpgsql
touch tests/integration/plpgsql/__init__.py
```

**Step 1.2: Design parser architecture** (1 hour)

Create `src/parsers/plpgsql/__init__.py`:

```python
"""
PL/pgSQL Parser Package

Reverse engineer PostgreSQL databases to SpecQL YAML:
- DDL parsing (CREATE TABLE, CREATE TYPE, etc.)
- PL/pgSQL function parsing
- Pattern detection (Trinity, audit fields)
- Type mapping (PostgreSQL → SpecQL)
"""

from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.parsers.plpgsql.function_analyzer import FunctionAnalyzer
from src.parsers.plpgsql.pattern_detector import PatternDetector
from src.parsers.plpgsql.type_mapper import TypeMapper

__all__ = [
    "PLpgSQLParser",
    "SchemaAnalyzer",
    "FunctionAnalyzer",
    "PatternDetector",
    "TypeMapper",
]
```

**Step 1.3: Create main parser class** (2 hours)

Create `src/parsers/plpgsql/plpgsql_parser.py`:

```python
"""
Main PL/pgSQL Parser

Entry point for PostgreSQL → SpecQL reverse engineering.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

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
        include_functions: bool = True
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

        with psycopg2.connect(connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get list of schemas to parse
                if schemas is None:
                    schemas = self._get_user_schemas(cur)

                # Parse each schema
                for schema in schemas:
                    schema_entities = self._parse_schema(
                        cur,
                        schema,
                        include_functions
                    )
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
            entity = self.schema_analyzer.parse_create_table(table_ddl)

            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(entity)
            entity.metadata = entity.metadata or {}
            entity.metadata['detected_patterns'] = patterns
            entity.metadata['confidence'] = patterns.get('confidence', 0.0)

            # Only include if confidence meets threshold
            if entity.metadata['confidence'] >= self.confidence_threshold:
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
        return [row['schema_name'] for row in cursor.fetchall()]

    def _parse_schema(
        self,
        cursor,
        schema: str,
        include_functions: bool
    ) -> List[UniversalEntity]:
        """Parse all tables in a schema"""
        entities = []

        # Get all tables in schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema,))

        tables = cursor.fetchall()

        for table in tables:
            entity = self._parse_table_from_db(
                cursor,
                schema,
                table['table_name']
            )

            if include_functions:
                # Find associated functions
                functions = self._get_table_functions(
                    cursor,
                    schema,
                    table['table_name']
                )
                entity.actions = self.function_analyzer.parse_functions(functions)

            entities.append(entity)

        return entities

    def _parse_table_from_db(
        self,
        cursor,
        schema: str,
        table_name: str
    ) -> UniversalEntity:
        """Parse single table from database"""
        # Get table DDL
        # PostgreSQL doesn't have SHOW CREATE TABLE, so we reconstruct it
        ddl = self._reconstruct_table_ddl(cursor, schema, table_name)

        # Parse the DDL
        entity = self.schema_analyzer.parse_create_table(ddl)

        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(entity)
        entity.metadata = entity.metadata or {}
        entity.metadata['detected_patterns'] = patterns
        entity.metadata['confidence'] = patterns.get('confidence', 0.0)

        return entity

    def _reconstruct_table_ddl(
        self,
        cursor,
        schema: str,
        table_name: str
    ) -> str:
        """Reconstruct CREATE TABLE DDL from information_schema"""
        # This is a simplified version - full implementation would be more complex
        cursor.execute("""
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
        """, (schema, table_name))

        columns = cursor.fetchall()

        # Build CREATE TABLE statement
        ddl_parts = [f"CREATE TABLE {schema}.{table_name} ("]

        for col in columns:
            col_def = f"    {col['column_name']} {col['data_type']}"

            if col['is_nullable'] == 'NO':
                col_def += " NOT NULL"

            if col['column_default']:
                col_def += f" DEFAULT {col['column_default']}"

            ddl_parts.append(col_def + ",")

        # Remove last comma
        ddl_parts[-1] = ddl_parts[-1].rstrip(',')
        ddl_parts.append(");")

        return "\n".join(ddl_parts)

    def _get_table_functions(
        self,
        cursor,
        schema: str,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get PL/pgSQL functions associated with a table"""
        cursor.execute("""
            SELECT
                routine_name,
                routine_definition,
                external_language
            FROM information_schema.routines
            WHERE routine_schema = %s
            AND routine_type = 'FUNCTION'
            AND external_language = 'plpgsql'
            AND routine_name LIKE %s
            ORDER BY routine_name
        """, (schema, f"%{table_name.lower()}%"))

        return cursor.fetchall()
```

#### Afternoon (4 hours): Schema Analyzer

**Step 1.4: Implement SchemaAnalyzer** (4 hours)

Create `src/parsers/plpgsql/schema_analyzer.py`:

```python
"""
Schema Analyzer

Parse CREATE TABLE DDL to UniversalEntity.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


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
        pattern = r'CREATE\s+TABLE\s+[^;]+;'
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
            name=entity_name,
            schema=schema,
            fields=fields
        )

        return entity

    def _extract_table_name(self, ddl: str) -> Tuple[str, str]:
        """
        Extract schema and table name from CREATE TABLE

        Returns:
            (schema, table_name)
        """
        # Pattern: CREATE TABLE schema.table_name
        pattern = r'CREATE\s+TABLE\s+(?:(\w+)\.)?(\w+)'
        match = re.search(pattern, ddl, re.IGNORECASE)

        if not match:
            raise ValueError(f"Could not extract table name from DDL")

        schema = match.group(1) or 'public'
        table_name = match.group(2)

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
        name = re.sub(r'^tb_', '', table_name, flags=re.IGNORECASE)

        # Convert snake_case to PascalCase
        parts = name.split('_')
        entity_name = ''.join(word.capitalize() for word in parts)

        return entity_name

    def _extract_columns(self, ddl: str) -> List[Dict[str, Any]]:
        """
        Extract column definitions from CREATE TABLE

        Returns:
            List of column definition dicts
        """
        # Extract content between parentheses
        pattern = r'CREATE\s+TABLE\s+[^(]+\((.*)\)'
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
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
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
            'PRIMARY KEY',
            'FOREIGN KEY',
            'UNIQUE',
            'CHECK',
            'CONSTRAINT',
        ]

        definition_upper = definition.upper()
        return any(kw in definition_upper for kw in constraint_keywords)

    def _parse_column_definition(self, col_def: str) -> Optional[Dict[str, Any]]:
        """
        Parse single column definition

        Example: 'email TEXT NOT NULL DEFAULT ...'

        Returns:
            Dict with column properties
        """
        # Pattern: column_name data_type [constraints]
        pattern = r'(\w+)\s+(\w+(?:\([^)]+\))?)(.*)'
        match = re.match(pattern, col_def.strip(), re.IGNORECASE)

        if not match:
            return None

        column_name = match.group(1)
        data_type = match.group(2)
        constraints = match.group(3)

        # Parse constraints
        is_nullable = 'NOT NULL' not in constraints.upper()
        has_default = 'DEFAULT' in constraints.upper()
        default_value = self._extract_default_value(constraints) if has_default else None

        return {
            'name': column_name,
            'data_type': data_type,
            'nullable': is_nullable,
            'default': default_value,
        }

    def _extract_default_value(self, constraints: str) -> Optional[str]:
        """Extract default value from constraint string"""
        pattern = r'DEFAULT\s+([^,\s]+(?:\s*\([^)]*\))?)'
        match = re.search(pattern, constraints, re.IGNORECASE)

        if match:
            return match.group(1)

        return None

    def _parse_column_to_field(self, column: Dict[str, Any]) -> Optional[UniversalField]:
        """
        Convert column definition to UniversalField

        Args:
            column: Column definition dict

        Returns:
            UniversalField or None if should skip
        """
        from src.parsers.plpgsql.type_mapper import TypeMapper

        column_name = column['name']

        # Skip Trinity pattern fields (will be auto-generated)
        if column_name in ['pk_*', 'id', 'identifier']:
            return None

        # Skip audit fields (will be auto-generated)
        if column_name in ['created_at', 'updated_at', 'deleted_at']:
            return None

        # Skip deduplication fields
        if column_name in ['dedup_key', 'dedup_hash', 'is_unique']:
            return None

        # Map PostgreSQL type to SpecQL type
        type_mapper = TypeMapper()
        field_type = type_mapper.map_postgres_type(column['data_type'])

        # Create field
        field = UniversalField(
            name=column_name,
            type=field_type,
            required=not column['nullable'],
            default=column.get('default')
        )

        return field
```

**Day 1 Deliverables**:
- ✅ Parser architecture designed
- ✅ PLpgSQLParser main class created
- ✅ SchemaAnalyzer implementation started
- ✅ Basic CREATE TABLE parsing working

---

### Day 2: Type Mapper & Pattern Detector (8 hours)

**Objective**: Complete type mapping and pattern detection

#### Morning (4 hours): Type Mapper

**Step 2.1: Implement TypeMapper** (4 hours)

Create `src/parsers/plpgsql/type_mapper.py`:

```python
"""
Type Mapper

Map PostgreSQL data types to SpecQL field types.
"""

from typing import Optional, Dict, Any
from src.core.universal_ast import FieldType
import re


class TypeMapper:
    """Map PostgreSQL types to SpecQL types"""

    # Type mapping table
    TYPE_MAP = {
        # Integer types
        'INTEGER': FieldType.INTEGER,
        'INT': FieldType.INTEGER,
        'INT4': FieldType.INTEGER,
        'SMALLINT': FieldType.INTEGER,
        'INT2': FieldType.INTEGER,
        'BIGINT': FieldType.INTEGER,
        'INT8': FieldType.INTEGER,

        # Text types
        'TEXT': FieldType.TEXT,
        'VARCHAR': FieldType.TEXT,
        'CHAR': FieldType.TEXT,
        'CHARACTER VARYING': FieldType.TEXT,
        'CHARACTER': FieldType.TEXT,

        # Boolean
        'BOOLEAN': FieldType.BOOLEAN,
        'BOOL': FieldType.BOOLEAN,

        # Numeric/Decimal
        'NUMERIC': FieldType.DECIMAL,
        'DECIMAL': FieldType.DECIMAL,
        'REAL': FieldType.DECIMAL,
        'FLOAT': FieldType.DECIMAL,
        'DOUBLE PRECISION': FieldType.DECIMAL,

        # Date/Time
        'TIMESTAMP': FieldType.DATETIME,
        'TIMESTAMPTZ': FieldType.DATETIME,
        'TIMESTAMP WITHOUT TIME ZONE': FieldType.DATETIME,
        'TIMESTAMP WITH TIME ZONE': FieldType.DATETIME,
        'DATE': FieldType.DATE,
        'TIME': FieldType.TIME,
        'TIMETZ': FieldType.TIME,

        # UUID
        'UUID': FieldType.UUID,

        # JSON
        'JSON': FieldType.JSON,
        'JSONB': FieldType.JSON,

        # Arrays
        'ARRAY': FieldType.LIST,
    }

    def map_postgres_type(
        self,
        pg_type: str,
        column_name: Optional[str] = None
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
        if '[]' in pg_type or 'ARRAY' in pg_type.upper():
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
        base_type = re.sub(r'\([^)]*\)', '', pg_type)

        # Remove array brackets
        base_type = base_type.replace('[]', '')

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
        if column_lower.startswith('fk_'):
            return True

        # *_id suffix (but not just 'id')
        if column_lower.endswith('_id') and column_lower != 'id':
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
        name = re.sub(r'^fk_', '', column_lower)

        # Remove _id suffix
        name = re.sub(r'_id$', '', name)

        # Convert to PascalCase
        parts = name.split('_')
        entity_name = ''.join(word.capitalize() for word in parts)

        return entity_name
```

#### Afternoon (4 hours): Pattern Detector

**Step 2.2: Implement PatternDetector** (4 hours)

Create `src/parsers/plpgsql/pattern_detector.py`:

```python
"""
Pattern Detector

Detect SpecQL patterns in parsed entities:
- Trinity Pattern (pk_*, id, identifier)
- Audit Fields (created_at, updated_at, deleted_at)
- Deduplication Pattern (dedup_key, dedup_hash, is_unique)
- Hierarchical Entities (parent references)
"""

from typing import Dict, Any, List
from src.core.universal_ast import UniversalEntity, UniversalField


class PatternDetector:
    """Detect SpecQL patterns in entities"""

    def detect_patterns(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect all patterns in an entity

        Returns:
            Dict with pattern detection results and confidence score
        """
        patterns = {
            'trinity': self._detect_trinity_pattern(entity),
            'audit': self._detect_audit_fields(entity),
            'deduplication': self._detect_deduplication(entity),
            'hierarchical': self._detect_hierarchical(entity),
            'soft_delete': self._detect_soft_delete(entity),
        }

        # Calculate overall confidence
        confidence = self._calculate_confidence(patterns)
        patterns['confidence'] = confidence

        return patterns

    def _detect_trinity_pattern(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect Trinity Pattern fields

        Trinity Pattern:
            - pk_* (INTEGER PRIMARY KEY)
            - id (UUID)
            - identifier (TEXT)
        """
        field_names = [f.name.lower() for f in entity.fields]

        # Look for pk_* field
        has_pk = any(name.startswith('pk_') for name in field_names)

        # Look for id field
        has_id = 'id' in field_names

        # Look for identifier field
        has_identifier = 'identifier' in field_names

        # Trinity is complete if has all three
        is_complete = has_pk and has_id and has_identifier

        # Confidence based on how many parts present
        confidence = sum([has_pk, has_id, has_identifier]) / 3.0

        return {
            'detected': is_complete,
            'has_pk': has_pk,
            'has_id': has_id,
            'has_identifier': has_identifier,
            'confidence': confidence,
        }

    def _detect_audit_fields(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect audit fields

        Audit Fields:
            - created_at (TIMESTAMPTZ)
            - updated_at (TIMESTAMPTZ)
            - deleted_at (TIMESTAMPTZ, nullable)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_created_at = 'created_at' in field_names
        has_updated_at = 'updated_at' in field_names
        has_deleted_at = 'deleted_at' in field_names

        # Audit is complete if has created_at and updated_at
        # deleted_at is optional (soft delete)
        is_complete = has_created_at and has_updated_at

        # Confidence
        confidence = sum([has_created_at, has_updated_at]) / 2.0

        return {
            'detected': is_complete,
            'has_created_at': has_created_at,
            'has_updated_at': has_updated_at,
            'has_deleted_at': has_deleted_at,
            'confidence': confidence,
        }

    def _detect_deduplication(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect deduplication pattern

        Deduplication Fields:
            - dedup_key (TEXT)
            - dedup_hash (TEXT)
            - is_unique (BOOLEAN)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_dedup_key = 'dedup_key' in field_names
        has_dedup_hash = 'dedup_hash' in field_names
        has_is_unique = 'is_unique' in field_names

        is_complete = has_dedup_key and has_dedup_hash and has_is_unique

        confidence = sum([has_dedup_key, has_dedup_hash, has_is_unique]) / 3.0

        return {
            'detected': is_complete,
            'has_dedup_key': has_dedup_key,
            'has_dedup_hash': has_dedup_hash,
            'has_is_unique': has_is_unique,
            'confidence': confidence,
        }

    def _detect_hierarchical(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect hierarchical entity (self-referential)

        Looks for:
            - fk_parent, parent_id, or similar field
            - Reference to same entity
        """
        # Look for self-reference fields
        parent_field_patterns = ['fk_parent', 'parent_id', f'fk_{entity.name.lower()}_parent']

        field_names = [f.name.lower() for f in entity.fields]

        has_parent_field = any(
            pattern in field_names
            for pattern in parent_field_patterns
        )

        return {
            'detected': has_parent_field,
            'parent_field': next(
                (name for name in field_names if name in parent_field_patterns),
                None
            ),
            'confidence': 1.0 if has_parent_field else 0.0,
        }

    def _detect_soft_delete(self, entity: UniversalEntity) -> Dict[str, Any]:
        """
        Detect soft delete pattern

        Soft Delete:
            - deleted_at field (nullable timestamp)
        """
        field_names = [f.name.lower() for f in entity.fields]

        has_deleted_at = 'deleted_at' in field_names

        return {
            'detected': has_deleted_at,
            'confidence': 1.0 if has_deleted_at else 0.0,
        }

    def _calculate_confidence(self, patterns: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score

        Weighted average of pattern confidences:
            - Trinity: 40% weight (most important)
            - Audit: 30% weight
            - Deduplication: 15% weight
            - Hierarchical: 10% weight
            - Soft Delete: 5% weight
        """
        weights = {
            'trinity': 0.40,
            'audit': 0.30,
            'deduplication': 0.15,
            'hierarchical': 0.10,
            'soft_delete': 0.05,
        }

        weighted_sum = 0.0
        for pattern_name, weight in weights.items():
            pattern_data = patterns.get(pattern_name, {})
            pattern_confidence = pattern_data.get('confidence', 0.0)
            weighted_sum += weight * pattern_confidence

        return weighted_sum
```

**Day 2 Deliverables**:
- ✅ TypeMapper implementation complete
- ✅ PatternDetector implementation complete
- ✅ Type mapping tests written
- ✅ Pattern detection tests written

---

### Day 3: Function Analyzer (8 hours)

**Objective**: Parse PL/pgSQL functions to SpecQL actions

#### Full Day (8 hours): Function Analyzer Implementation

**Step 3.1: Implement FunctionAnalyzer** (8 hours)

Create `src/parsers/plpgsql/function_analyzer.py`:

```python
"""
Function Analyzer

Parse PL/pgSQL functions to SpecQL actions.
"""

from typing import List, Dict, Any, Optional
import re
from src.core.universal_ast import UniversalAction, UniversalStep, StepType


class FunctionAnalyzer:
    """Analyze PL/pgSQL functions and convert to actions"""

    def parse_functions(
        self,
        functions: List[Dict[str, Any]]
    ) -> List[UniversalAction]:
        """
        Parse list of PL/pgSQL functions to actions

        Args:
            functions: List of function definitions from database

        Returns:
            List of UniversalAction objects
        """
        actions = []

        for func in functions:
            action = self.parse_function(func)
            if action:
                actions.append(action)

        return actions

    def parse_function(self, function: Dict[str, Any]) -> Optional[UniversalAction]:
        """
        Parse single PL/pgSQL function to action

        Args:
            function: Function definition dict with:
                - routine_name: function name
                - routine_definition: PL/pgSQL code
                - external_language: should be 'plpgsql'

        Returns:
            UniversalAction or None if cannot parse
        """
        if function['external_language'] != 'plpgsql':
            return None

        action_name = function['routine_name']
        function_body = function['routine_definition']

        # Parse function body to steps
        steps = self._parse_function_body(function_body)

        if not steps:
            return None

        # Create action
        action = UniversalAction(
            name=action_name,
            entity=self._extract_entity_from_function_name(action_name),
            steps=steps,
            impacts=[],  # TODO: Analyze which tables are affected
        )

        return action

    def _parse_function_body(self, body: str) -> List[UniversalStep]:
        """
        Parse PL/pgSQL function body to action steps

        Detects:
            - IF statements → validate steps
            - UPDATE statements → update steps
            - INSERT statements → insert steps
            - DELETE statements → delete steps
            - RAISE EXCEPTION → error steps
        """
        steps = []

        # Split body into statements
        statements = self._split_statements(body)

        for stmt in statements:
            step = self._parse_statement(stmt)
            if step:
                steps.append(step)

        return steps

    def _split_statements(self, body: str) -> List[str]:
        """Split function body into individual statements"""
        # Remove comments
        body = re.sub(r'--[^\n]*', '', body)
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)

        # Split by semicolons (simplified - doesn't handle all cases)
        statements = [s.strip() for s in body.split(';') if s.strip()]

        return statements

    def _parse_statement(self, stmt: str) -> Optional[UniversalStep]:
        """Parse single PL/pgSQL statement to step"""
        stmt_upper = stmt.upper().strip()

        # IF statement → validate step
        if stmt_upper.startswith('IF'):
            return self._parse_if_statement(stmt)

        # UPDATE statement → update step
        if stmt_upper.startswith('UPDATE'):
            return self._parse_update_statement(stmt)

        # INSERT statement → insert step
        if stmt_upper.startswith('INSERT'):
            return self._parse_insert_statement(stmt)

        # DELETE statement → delete step
        if stmt_upper.startswith('DELETE'):
            return self._parse_delete_statement(stmt)

        # RAISE EXCEPTION → error step
        if 'RAISE EXCEPTION' in stmt_upper:
            return self._parse_raise_exception(stmt)

        return None

    def _parse_if_statement(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse IF statement to validate step

        Example:
            IF status != 'pending' THEN
                RAISE EXCEPTION 'not_pending';
            END IF;

        → validate: status = 'pending'
        """
        # Extract condition
        pattern = r'IF\s+(.+?)\s+THEN'
        match = re.search(pattern, stmt, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        condition = match.group(1).strip()

        # Invert condition (IF NOT x → validate x)
        inverted_condition = self._invert_condition(condition)

        return UniversalStep(
            type=StepType.VALIDATE,
            expression=inverted_condition
        )

    def _parse_update_statement(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse UPDATE statement to update step

        Example:
            UPDATE contact SET status = 'active' WHERE pk_contact = v_pk_contact

        → update: Contact SET status = 'active'
        """
        # Extract table and SET clause
        pattern = r'UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE|$)'
        match = re.search(pattern, stmt, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        table = match.group(1)
        set_clause = match.group(2).strip()

        # Convert table name to entity name
        entity_name = self._table_to_entity_name(table)

        # Parse SET clause to field updates
        fields = self._parse_set_clause(set_clause)

        return UniversalStep(
            type=StepType.UPDATE,
            entity=entity_name,
            fields=fields
        )

    def _parse_insert_statement(self, stmt: str) -> Optional[UniversalStep]:
        """Parse INSERT statement to insert step"""
        # TODO: Implement INSERT parsing
        return None

    def _parse_delete_statement(self, stmt: str) -> Optional[UniversalStep]:
        """Parse DELETE statement to delete step"""
        # TODO: Implement DELETE parsing
        return None

    def _parse_raise_exception(self, stmt: str) -> Optional[UniversalStep]:
        """
        Parse RAISE EXCEPTION to error code

        Example:
            RAISE EXCEPTION 'not_pending'

        → validate step with error code
        """
        pattern = r"RAISE\s+EXCEPTION\s+'([^']+)'"
        match = re.search(pattern, stmt, re.IGNORECASE)

        if match:
            error_code = match.group(1)
            # Store error code in step metadata
            return UniversalStep(
                type=StepType.VALIDATE,
                expression="false",  # Will fail
                metadata={'error_code': error_code}
            )

        return None

    def _invert_condition(self, condition: str) -> str:
        """
        Invert a boolean condition

        Examples:
            status != 'pending' → status = 'pending'
            is_active = false → is_active = true
        """
        # Replace != with =
        if '!=' in condition:
            condition = condition.replace('!=', '=')
        # Replace <> with =
        elif '<>' in condition:
            condition = condition.replace('<>', '=')
        # TODO: Handle more complex inversions

        return condition

    def _parse_set_clause(self, set_clause: str) -> Dict[str, Any]:
        """
        Parse SET clause to field→value mapping

        Example:
            status = 'active', updated_at = NOW()

        → {'status': "'active'", 'updated_at': 'NOW()'}
        """
        fields = {}

        # Split by commas
        assignments = set_clause.split(',')

        for assignment in assignments:
            parts = assignment.split('=', 1)
            if len(parts) == 2:
                field_name = parts[0].strip()
                value = parts[1].strip()
                fields[field_name] = value

        return fields

    def _table_to_entity_name(self, table: str) -> str:
        """Convert table name to entity name"""
        # Remove tb_ prefix
        name = re.sub(r'^tb_', '', table, flags=re.IGNORECASE)

        # Convert to PascalCase
        parts = name.split('_')
        return ''.join(word.capitalize() for word in parts)

    def _extract_entity_from_function_name(self, func_name: str) -> str:
        """
        Extract entity name from function name

        Examples:
            create_contact → Contact
            update_order_status → Order
            app.qualify_lead → Lead
        """
        # Remove schema prefix if present
        if '.' in func_name:
            func_name = func_name.split('.')[-1]

        # Remove action prefix
        for prefix in ['create_', 'update_', 'delete_', 'app_', 'core_']:
            if func_name.startswith(prefix):
                func_name = func_name[len(prefix):]
                break

        # Convert to PascalCase
        parts = func_name.split('_')
        return parts[0].capitalize() if parts else "Unknown"
```

**Day 3 Deliverables**:
- ✅ FunctionAnalyzer implementation complete
- ✅ PL/pgSQL function parsing working
- ✅ Basic action step detection implemented
- ✅ Function analyzer tests written

---

### Day 4-5: Unit Tests & Integration (16 hours)

**Objective**: Comprehensive test suite for parser

#### Day 4: Unit Tests (8 hours)

**Step 4.1: SchemaAnalyzer tests** (3 hours)

Create `tests/unit/parsers/plpgsql/test_schema_analyzer.py`:

```python
"""Unit tests for SchemaAnalyzer"""
import pytest
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.core.universal_ast import FieldType


class TestSchemaAnalyzer:
    """Test SchemaAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        return SchemaAnalyzer()

    def test_extract_table_name_with_schema(self, analyzer):
        """Test extracting schema and table name"""
        ddl = "CREATE TABLE crm.tb_contact (id INTEGER)"
        schema, table = analyzer._extract_table_name(ddl)

        assert schema == "crm"
        assert table == "tb_contact"

    def test_extract_table_name_without_schema(self, analyzer):
        """Test extracting table name without schema"""
        ddl = "CREATE TABLE contact (id INTEGER)"
        schema, table = analyzer._extract_table_name(ddl)

        assert schema == "public"
        assert table == "contact"

    def test_table_to_entity_name(self, analyzer):
        """Test converting table names to entity names"""
        assert analyzer._table_to_entity_name("tb_contact") == "Contact"
        assert analyzer._table_to_entity_name("contact") == "Contact"
        assert analyzer._table_to_entity_name("tb_order_item") == "OrderItem"
        assert analyzer._table_to_entity_name("order_item") == "OrderItem"

    def test_extract_columns(self, analyzer):
        """Test extracting column definitions"""
        ddl = """
        CREATE TABLE contact (
            pk_contact INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            first_name TEXT
        )
        """

        columns = analyzer._extract_columns(ddl)

        assert len(columns) == 3
        assert columns[0]['name'] == 'pk_contact'
        assert columns[1]['name'] == 'email'
        assert columns[2]['name'] == 'first_name'

    def test_parse_column_definition(self, analyzer):
        """Test parsing individual column"""
        col_def = "email TEXT NOT NULL DEFAULT 'test@example.com'"

        column = analyzer._parse_column_definition(col_def)

        assert column['name'] == 'email'
        assert column['data_type'] == 'TEXT'
        assert column['nullable'] == False
        assert column['default'] == "'test@example.com'"

    def test_parse_complete_table(self, analyzer):
        """Test parsing complete CREATE TABLE"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            fk_company INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
        """

        entity = analyzer.parse_create_table(ddl)

        assert entity.name == "Contact"
        assert entity.schema == "crm"

        # Should have business fields only (Trinity and audit fields excluded)
        field_names = [f.name for f in entity.fields]
        assert "email" in field_names
        assert "first_name" in field_names
        assert "last_name" in field_names

        # Trinity and audit fields should be excluded
        assert "pk_contact" not in field_names
        assert "id" not in field_names
        assert "created_at" not in field_names
```

**Step 4.2: TypeMapper tests** (2 hours)

Create `tests/unit/parsers/plpgsql/test_type_mapper.py`:

```python
"""Unit tests for TypeMapper"""
import pytest
from src.parsers.plpgsql.type_mapper import TypeMapper
from src.core.universal_ast import FieldType


class TestTypeMapper:
    """Test TypeMapper"""

    @pytest.fixture
    def mapper(self):
        return TypeMapper()

    def test_map_integer_types(self, mapper):
        """Test mapping integer types"""
        assert mapper.map_postgres_type("INTEGER") == FieldType.INTEGER
        assert mapper.map_postgres_type("INT") == FieldType.INTEGER
        assert mapper.map_postgres_type("BIGINT") == FieldType.INTEGER
        assert mapper.map_postgres_type("SMALLINT") == FieldType.INTEGER

    def test_map_text_types(self, mapper):
        """Test mapping text types"""
        assert mapper.map_postgres_type("TEXT") == FieldType.TEXT
        assert mapper.map_postgres_type("VARCHAR") == FieldType.TEXT
        assert mapper.map_postgres_type("VARCHAR(255)") == FieldType.TEXT
        assert mapper.map_postgres_type("CHAR(10)") == FieldType.TEXT

    def test_map_boolean_type(self, mapper):
        """Test mapping boolean"""
        assert mapper.map_postgres_type("BOOLEAN") == FieldType.BOOLEAN
        assert mapper.map_postgres_type("BOOL") == FieldType.BOOLEAN

    def test_map_decimal_types(self, mapper):
        """Test mapping decimal types"""
        assert mapper.map_postgres_type("NUMERIC") == FieldType.DECIMAL
        assert mapper.map_postgres_type("DECIMAL") == FieldType.DECIMAL
        assert mapper.map_postgres_type("NUMERIC(10,2)") == FieldType.DECIMAL

    def test_map_datetime_types(self, mapper):
        """Test mapping date/time types"""
        assert mapper.map_postgres_type("TIMESTAMP") == FieldType.DATETIME
        assert mapper.map_postgres_type("TIMESTAMPTZ") == FieldType.DATETIME
        assert mapper.map_postgres_type("DATE") == FieldType.DATE
        assert mapper.map_postgres_type("TIME") == FieldType.TIME

    def test_map_uuid_type(self, mapper):
        """Test mapping UUID"""
        assert mapper.map_postgres_type("UUID") == FieldType.UUID

    def test_map_json_types(self, mapper):
        """Test mapping JSON types"""
        assert mapper.map_postgres_type("JSON") == FieldType.JSON
        assert mapper.map_postgres_type("JSONB") == FieldType.JSON

    def test_detect_foreign_key(self, mapper):
        """Test detecting foreign key columns"""
        assert mapper._is_foreign_key("fk_company") == True
        assert mapper._is_foreign_key("company_id") == True
        assert mapper._is_foreign_key("id") == False
        assert mapper._is_foreign_key("email") == False

    def test_extract_reference_target(self, mapper):
        """Test extracting reference target entity"""
        assert mapper.extract_reference_target("fk_company") == "Company"
        assert mapper.extract_reference_target("company_id") == "Company"
        assert mapper.extract_reference_target("fk_order_item") == "OrderItem"
```

**Step 4.3: PatternDetector tests** (3 hours)

Create `tests/unit/parsers/plpgsql/test_pattern_detector.py`:

```python
"""Unit tests for PatternDetector"""
import pytest
from src.parsers.plpgsql.pattern_detector import PatternDetector
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class TestPatternDetector:
    """Test PatternDetector"""

    @pytest.fixture
    def detector(self):
        return PatternDetector()

    def test_detect_trinity_pattern_complete(self, detector):
        """Test detecting complete Trinity pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.UUID),
                UniversalField(name="identifier", type=FieldType.TEXT),
            ]
        )

        result = detector._detect_trinity_pattern(entity)

        assert result['detected'] == True
        assert result['has_pk'] == True
        assert result['has_id'] == True
        assert result['has_identifier'] == True
        assert result['confidence'] == 1.0

    def test_detect_trinity_pattern_partial(self, detector):
        """Test detecting partial Trinity pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.UUID),
                # Missing identifier
            ]
        )

        result = detector._detect_trinity_pattern(entity)

        assert result['detected'] == False
        assert result['confidence'] == 2/3  # 2 out of 3

    def test_detect_audit_fields_complete(self, detector):
        """Test detecting complete audit fields"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="created_at", type=FieldType.DATETIME),
                UniversalField(name="updated_at", type=FieldType.DATETIME),
                UniversalField(name="deleted_at", type=FieldType.DATETIME),
            ]
        )

        result = detector._detect_audit_fields(entity)

        assert result['detected'] == True
        assert result['has_created_at'] == True
        assert result['has_updated_at'] == True
        assert result['has_deleted_at'] == True

    def test_detect_deduplication_pattern(self, detector):
        """Test detecting deduplication pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="dedup_key", type=FieldType.TEXT),
                UniversalField(name="dedup_hash", type=FieldType.TEXT),
                UniversalField(name="is_unique", type=FieldType.BOOLEAN),
            ]
        )

        result = detector._detect_deduplication(entity)

        assert result['detected'] == True
        assert result['confidence'] == 1.0

    def test_detect_hierarchical_entity(self, detector):
        """Test detecting hierarchical entity"""
        entity = UniversalEntity(
            name="Category",
            schema="catalog",
            fields=[
                UniversalField(name="fk_parent", type=FieldType.REFERENCE),
            ]
        )

        result = detector._detect_hierarchical(entity)

        assert result['detected'] == True
        assert result['parent_field'] == 'fk_parent'

    def test_calculate_overall_confidence(self, detector):
        """Test calculating overall confidence score"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                # Complete Trinity
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.UUID),
                UniversalField(name="identifier", type=FieldType.TEXT),
                # Complete Audit
                UniversalField(name="created_at", type=FieldType.DATETIME),
                UniversalField(name="updated_at", type=FieldType.DATETIME),
                UniversalField(name="deleted_at", type=FieldType.DATETIME),
                # Business fields
                UniversalField(name="email", type=FieldType.TEXT),
            ]
        )

        patterns = detector.detect_patterns(entity)

        # Trinity (40%) + Audit (30%) = 70% minimum
        assert patterns['confidence'] >= 0.70
```

#### Day 5: Integration Tests (8 hours)

**Step 5.1: Basic parser integration tests** (4 hours)

Create `tests/integration/plpgsql/test_parser_integration.py`:

```python
"""Integration tests for PLpgSQLParser"""
import pytest
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser


class TestPLpgSQLParserIntegration:
    """Test complete parser integration"""

    @pytest.fixture
    def parser(self):
        return PLpgSQLParser(confidence_threshold=0.70)

    def test_parse_simple_table_ddl(self, parser):
        """Test parsing simple CREATE TABLE"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );
        """

        entities = parser.parse_ddl_string(ddl)

        assert len(entities) == 1
        entity = entities[0]

        assert entity.name == "Contact"
        assert entity.schema == "crm"

        # Should have business fields only
        field_names = [f.name for f in entity.fields]
        assert "email" in field_names
        assert "first_name" in field_names
        assert "last_name" in field_names

        # Pattern detection
        assert entity.metadata['detected_patterns']['trinity']['detected'] == True
        assert entity.metadata['detected_patterns']['audit']['detected'] == True
        assert entity.metadata['confidence'] >= 0.70

    def test_parse_table_with_foreign_keys(self, parser):
        """Test parsing table with foreign key relationships"""
        ddl = """
        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            fk_company INTEGER REFERENCES crm.tb_company(pk_company),
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """

        entities = parser.parse_ddl_string(ddl)
        entity = entities[0]

        # Find company field
        company_field = next(f for f in entity.fields if f.name == "fk_company")
        assert company_field.type == FieldType.REFERENCE
        # TODO: Add reference target parsing

    def test_parse_multiple_tables(self, parser):
        """Test parsing multiple tables"""
        ddl = """
        CREATE TABLE crm.tb_company (
            pk_company INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );

        CREATE TABLE crm.tb_contact (
            pk_contact INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            fk_company INTEGER,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """

        entities = parser.parse_ddl_string(ddl)

        assert len(entities) == 2
        entity_names = [e.name for e in entities]
        assert "Company" in entity_names
        assert "Contact" in entity_names

    def test_parse_ddl_file(self, parser, tmp_path):
        """Test parsing DDL from file"""
        ddl_file = tmp_path / "schema.sql"
        ddl_file.write_text("""
        CREATE TABLE test.tb_product (
            pk_product INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price NUMERIC(10,2),
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        """)

        entities = parser.parse_ddl_file(str(ddl_file))

        assert len(entities) == 1
        assert entities[0].name == "Product"

    def test_confidence_threshold_filtering(self, parser):
        """Test that low-confidence entities are filtered"""
        # Table without Trinity or audit fields
        ddl = """
        CREATE TABLE test.simple_table (
            id INTEGER,
            value TEXT
        );
        """

        entities = parser.parse_ddl_string(ddl)

        # Should be filtered out (confidence < 0.70)
        assert len(entities) == 0
```

**Step 5.2: Database parsing tests** (4 hours)

Create `tests/integration/plpgsql/test_database_parsing.py`:

```python
"""Integration tests for database parsing"""
import pytest
import psycopg2
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser


@pytest.fixture(scope="module")
def test_database(postgresql):
    """Create test database with sample schema"""
    conn = psycopg2.connect(
        host=postgresql.info.host,
        port=postgresql.info.port,
        user=postgresql.info.user,
        dbname=postgresql.info.dbname,
    )

    with conn.cursor() as cur:
        # Create test schema
        cur.execute("""
        CREATE SCHEMA IF NOT EXISTS test_schema;

        CREATE TABLE test_schema.tb_contact (
            pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            email TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );

        CREATE TABLE test_schema.tb_company (
            pk_company INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            identifier TEXT,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        );
        """)
        conn.commit()

    yield postgresql.info
    conn.close()


class TestDatabaseParsing:
    """Test parsing live database"""

    def test_parse_database(self, test_database):
        """Test parsing entire database"""
        parser = PLpgSQLParser()

        connection_string = f"postgresql://{test_database.user}@{test_database.host}:{test_database.port}/{test_database.dbname}"

        entities = parser.parse_database(
            connection_string,
            schemas=['test_schema']
        )

        assert len(entities) == 2
        entity_names = [e.name for e in entities]
        assert "Contact" in entity_names
        assert "Company" in entity_names

    def test_parse_specific_schemas(self, test_database):
        """Test parsing only specific schemas"""
        parser = PLpgSQLParser()

        connection_string = f"postgresql://{test_database.user}@{test_database.host}:{test_database.port}/{test_database.dbname}"

        entities = parser.parse_database(
            connection_string,
            schemas=['test_schema']  # Only test_schema
        )

        # All entities should be from test_schema
        assert all(e.schema == 'test_schema' for e in entities)
```

**Week 1 Deliverables**:
- ✅ PLpgSQLParser complete implementation
- ✅ SchemaAnalyzer with table parsing
- ✅ TypeMapper with PostgreSQL → SpecQL mapping
- ✅ PatternDetector for SpecQL patterns
- ✅ FunctionAnalyzer for PL/pgSQL functions
- ✅ 30+ unit tests passing
- ✅ 10+ integration tests passing

---

## 📅 Week 2: Testing, Documentation & Polish

(Content continues in next file due to length...)

---

## ✅ Success Criteria

### Must Have (Week 1-2)
- [x] PLpgSQLParser implementation complete
- [x] Parse CREATE TABLE → UniversalEntity
- [x] Detect Trinity pattern (90%+ accuracy)
- [x] Detect audit fields (90%+ accuracy)
- [x] Parse PL/pgSQL functions → actions (70%+ accuracy)
- [x] Type mapping (PostgreSQL → SpecQL)
- [x] 40+ unit tests passing (>95% coverage)
- [x] 10+ integration tests passing
- [x] Parse from DDL files
- [x] Parse from live database

### Nice to Have
- [ ] Parse composite types
- [ ] Parse views
- [ ] Parse triggers
- [ ] Detect more complex patterns

---

**Status**: 📅 Planned
**Risk Level**: Medium (new parser implementation)
**Estimated Effort**: 80 hours (2 weeks)
**Prerequisites**: Understanding of PostgreSQL internals
**Confidence**: High (clear requirements, proven patterns from Java/Rust)

---

*Last Updated*: 2025-11-14
*Author*: SpecQL Team
*Junior Developer Friendly*: Yes ✨
