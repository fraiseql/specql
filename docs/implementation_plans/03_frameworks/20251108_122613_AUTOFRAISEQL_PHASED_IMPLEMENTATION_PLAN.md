# AutoFraiseQL: Phased Implementation Plan (CTO Perspective)

**Author**: FraiseQL CTO
**Date**: November 8, 2025
**Version**: 1.0
**Context**: Strategic plan for PostgreSQL metadata-driven auto-discovery
**Timeline**: 10 weeks (conservative estimate with buffer)

---

## Executive Summary

**The Vision:**
Transform FraiseQL from a "write Python decorators" framework into a "write SQL comments" framework. This positions FraiseQL as the **first truly zero-code GraphQL backend** while maintaining 100% backward compatibility.

**The Prize:**
- **Market differentiation**: Only framework with full auto-discovery from PostgreSQL
- **Developer experience**: 10-20x productivity gain
- **SpecQL compatibility**: Seamless integration with declarative business logic
- **Backward compatible**: Existing apps continue to work

**Strategic Importance:**
This is a **Category-Defining Feature** that transforms FraiseQL from "fast GraphQL framework" to "database-first application platform."

---

## 🎯 Success Metrics

### **Technical Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Reduction** | 80-90% | Lines of Python vs metadata |
| **Discovery Speed** | < 2s | Time to introspect 100 tables |
| **Schema Generation** | < 5s | Time to generate 100 types |
| **Backward Compat** | 100% | All existing tests pass |
| **Type Coverage** | 95%+ | PostgreSQL types mapped |
| **Performance** | < 5% overhead | vs manual FraiseQL |

### **Business Metrics**

| Metric | Target | Timeline |
|--------|--------|----------|
| **Adoption Rate** | 30% of users | 6 months post-release |
| **GitHub Stars** | +500 | 3 months post-release |
| **Documentation Views** | +2000/month | 3 months post-release |
| **Bug Reports** | < 10 critical | 3 months post-release |

---

## 📐 Architecture Overview

### **High-Level Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                    AutoFraiseQL Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   PostgreSQL     │
│   Database       │
│                  │
│  - Views (v_*)   │
│  - Functions     │
│  - COMMENTs      │
└────────┬─────────┘
         │
         │ Introspection
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Introspection Layer                            │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Schema         │  │ Metadata        │  │ Column           │  │
│  │ Discovery      │  │ Parser          │  │ Analyzer         │  │
│  │ (pg_catalog)   │  │ (YAML/JSON)     │  │ (types, nulls)   │  │
│  └────────────────┘  └─────────────────┘  └──────────────────┘  │
└────────┬─────────────────────────────────────────────────────────┘
         │
         │ TypeMetadata, MutationMetadata
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Generation Layer                               │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Type           │  │ Query           │  │ Mutation         │  │
│  │ Generator      │  │ Generator       │  │ Generator        │  │
│  │ (@type)        │  │ (@query)        │  │ (@mutation)      │  │
│  └────────────────┘  └─────────────────┘  └──────────────────┘  │
│  ┌────────────────┐  ┌─────────────────┐                        │
│  │ Filter         │  │ OrderBy         │                        │
│  │ Generator      │  │ Generator       │                        │
│  │ (WhereInput)   │  │ (OrderByInput)  │                        │
│  └────────────────┘  └─────────────────┘                        │
└────────┬─────────────────────────────────────────────────────────┘
         │
         │ Python classes, functions
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Registry & Cache Layer                         │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Type           │  │ Schema          │  │ Performance      │  │
│  │ Registry       │  │ Cache           │  │ Cache            │  │
│  │ (runtime)      │  │ (metadata)      │  │ (queries)        │  │
│  └────────────────┘  └─────────────────┘  └──────────────────┘  │
└────────┬─────────────────────────────────────────────────────────┘
         │
         │ GraphQL Schema
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Existing FraiseQL Core                         │
│  (No changes needed - perfect backward compatibility)             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Phase 0: Pre-Implementation (Week 0)

**Duration**: 1 week
**Goal**: Technical validation, team alignment, infrastructure setup

### **Tasks**

#### **0.1: Technical Spike (2 days)**

```python
# Prototype: Can we introspect and generate dynamically?

import asyncpg

async def spike_introspection():
    """Validate introspection approach."""
    conn = await asyncpg.connect("postgresql://...")

    # Test 1: Can we introspect views efficiently?
    views = await conn.fetch("""
        SELECT schemaname, viewname, definition
        FROM pg_views
        WHERE schemaname = 'public'
        LIMIT 10
    """)
    print(f"✅ Found {len(views)} views")

    # Test 2: Can we read comments?
    comments = await conn.fetch("""
        SELECT obj_description(c.oid, 'pg_class') as comment
        FROM pg_class c
        WHERE c.relname = 'v_user'
    """)
    print(f"✅ Read comment: {comments[0]['comment']}")

    # Test 3: Can we parse YAML from comments?
    import yaml
    metadata = yaml.safe_load(comments[0]['comment'].split('@fraiseql:type')[1])
    print(f"✅ Parsed metadata: {metadata}")

    # Test 4: Can we dynamically create @type classes?
    from fraiseql import type as fraiseql_type

    User = type('User', (object,), {
        '__annotations__': {'id': 'UUID', 'name': 'str'},
        '__doc__': 'Auto-generated type'
    })
    User = fraiseql_type(sql_source="v_user")(User)
    print(f"✅ Created type: {User}")

# Run spike
asyncio.run(spike_introspection())
```

**Deliverable**: Proof-of-concept validates approach

---

#### **0.2: Architecture Review (1 day)**

**Questions to answer:**
1. Where does introspection code live? (`src/fraiseql/introspection/`?)
2. How to integrate with existing `create_fraiseql_app`?
3. How to handle type registry conflicts (auto vs manual)?
4. Caching strategy for introspection results?
5. Migration path for existing users?

**Decisions needed:**
- [ ] Module structure (`fraiseql.introspection.*`)
- [ ] API design (`auto_discover=True` vs `AutoDiscovery(...)`)
- [ ] Caching layer (Redis? In-memory? File-based?)
- [ ] Backward compatibility strategy

**Deliverable**: ADR (Architecture Decision Record) document

---

#### **0.3: Team Alignment (1 day)**

**Stakeholders:**
- [ ] Core FraiseQL maintainers
- [ ] Key users/contributors (get feedback)
- [ ] DevOps (deployment impact)

**Alignment topics:**
1. **Scope**: What's in v1.0 vs v2.0?
2. **Timeline**: Can we commit to 10 weeks?
3. **Resources**: Do we need additional help?
4. **Risk mitigation**: What could go wrong?

**Deliverable**: Go/No-Go decision from team

---

#### **0.4: Infrastructure Setup (2 days)**

```bash
# New module structure
mkdir -p src/fraiseql/introspection
mkdir -p tests/unit/introspection
mkdir -p tests/integration/introspection
mkdir -p docs/auto-discovery

# CI/CD updates
# - Add introspection tests to quality gate
# - Add benchmarks for discovery speed
# - Add integration tests with real database

# Dependencies audit
# - Ensure pyyaml is sufficient
# - Add psycopg metadata helpers
# - Consider asyncpg for introspection (faster?)
```

**Deliverable**: Infrastructure ready for development

---

## 🚀 Phase 1: Introspection Engine (Week 1-2)

**Duration**: 2 weeks
**Goal**: Reliable PostgreSQL metadata introspection
**Risk**: Medium (PostgreSQL catalog queries can be complex)

### **Week 1: Core Introspection**

#### **1.1: PostgresIntrospector Base Class (2 days)**

```python
# src/fraiseql/introspection/postgres_introspector.py

from dataclasses import dataclass
from typing import Optional
import asyncpg

@dataclass
class ViewMetadata:
    """Metadata for a database view."""
    schema_name: str
    view_name: str
    definition: str
    comment: Optional[str]
    columns: dict[str, ColumnInfo]

@dataclass
class ColumnInfo:
    """Column metadata."""
    name: str
    pg_type: str
    nullable: bool
    comment: Optional[str]

class PostgresIntrospector:
    """Introspect PostgreSQL database for FraiseQL metadata."""

    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool

    async def discover_views(
        self,
        pattern: str = "v_%",
        schemas: list[str] = ["public"]
    ) -> list[ViewMetadata]:
        """
        Discover views matching pattern.

        Implementation:
        1. Query pg_views for view definitions
        2. Query pg_class for comments
        3. Query pg_attribute for column info
        4. Combine into ViewMetadata objects
        """
        async with self.pool.acquire() as conn:
            # Complex query joining pg_catalog tables
            # See implementation in AUTOFRAISEQL_REQUIREMENTS.md
            pass

    async def discover_functions(
        self,
        pattern: str = "fn_%",
        schemas: list[str] = ["public"]
    ) -> list[FunctionMetadata]:
        """Discover functions matching pattern."""
        pass
```

**Tests:**
```python
# tests/unit/introspection/test_postgres_introspector.py

async def test_discover_views():
    """Test view discovery."""
    # Given: Database with v_user, v_post views
    # When: discover_views(pattern="v_%")
    # Then: Returns 2 ViewMetadata objects

async def test_discover_views_with_comments():
    """Test comment extraction."""
    # Given: View with COMMENT ON VIEW
    # When: discover_views()
    # Then: ViewMetadata.comment is populated

async def test_discover_views_columns():
    """Test column introspection."""
    # Given: View with multiple columns
    # When: discover_views()
    # Then: ViewMetadata.columns has all columns with types
```

**Deliverable**: Working view introspection

---

#### **1.2: Function Introspection (2 days)**

```python
# src/fraiseql/introspection/postgres_introspector.py (continued)

@dataclass
class FunctionMetadata:
    """Metadata for a database function."""
    schema_name: str
    function_name: str
    parameters: list[ParameterInfo]
    return_type: str
    comment: Optional[str]
    language: str

@dataclass
class ParameterInfo:
    """Function parameter metadata."""
    name: str
    pg_type: str
    mode: str  # IN, OUT, INOUT
    default_value: Optional[str]

class PostgresIntrospector:
    async def discover_functions(
        self,
        pattern: str = "fn_%",
        schemas: list[str] = ["public"]
    ) -> list[FunctionMetadata]:
        """
        Discover functions matching pattern.

        Queries:
        - pg_proc: function definitions
        - pg_get_function_arguments(): parameter list
        - pg_get_function_result(): return type
        """
        async with self.pool.acquire() as conn:
            query = """
            SELECT
                n.nspname as schema_name,
                p.proname as function_name,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as return_type,
                obj_description(p.oid, 'pg_proc') as comment,
                l.lanname as language
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            JOIN pg_language l ON l.oid = p.prolang
            WHERE n.nspname = ANY($1)
              AND p.proname LIKE $2
            ORDER BY n.nspname, p.proname
            """
            rows = await conn.fetch(query, schemas, pattern)
            # Parse into FunctionMetadata
```

**Tests:**
```python
async def test_discover_functions():
    """Test function discovery."""
    # Given: fn_create_user, fn_update_user
    # When: discover_functions(pattern="fn_%")
    # Then: Returns 2 FunctionMetadata objects

async def test_discover_functions_parameters():
    """Test parameter parsing."""
    # Given: fn_create_user(p_name TEXT, p_email TEXT)
    # When: discover_functions()
    # Then: parameters list has 2 ParameterInfo objects
```

**Deliverable**: Working function introspection

---

### **Week 2: Metadata Parsing**

#### **1.3: Metadata Parser (3 days)**

```python
# src/fraiseql/introspection/metadata_parser.py

import yaml
from dataclasses import dataclass
from typing import Optional

@dataclass
class TypeAnnotation:
    """Parsed @fraiseql:type annotation."""
    trinity: bool = False
    use_projection: bool = False
    description: Optional[str] = None
    expose_fields: Optional[list[str]] = None
    filter_config: Optional[dict] = None

@dataclass
class MutationAnnotation:
    """Parsed @fraiseql:mutation annotation."""
    input_schema: dict[str, dict]
    success_type: str
    failure_type: str
    description: Optional[str] = None
    permissions: Optional[list[str]] = None

class MetadataParser:
    """Parse @fraiseql annotations from PostgreSQL comments."""

    ANNOTATION_MARKER = '@fraiseql:'

    def parse_type_annotation(
        self,
        comment: Optional[str]
    ) -> Optional[TypeAnnotation]:
        """
        Parse @fraiseql:type annotation from view comment.

        Format:
            @fraiseql:type
            trinity: true
            description: User account
            expose_fields:
              - id
              - name
              - email

        Returns:
            TypeAnnotation if valid, None otherwise
        """
        if not comment or self.ANNOTATION_MARKER not in comment:
            return None

        try:
            # Extract YAML content after marker
            marker = '@fraiseql:type'
            if marker not in comment:
                return None

            yaml_start = comment.index(marker) + len(marker)
            yaml_content = comment[yaml_start:].strip()

            # Handle multi-line YAML
            # Stop at next @fraiseql: marker or end of comment
            if self.ANNOTATION_MARKER in yaml_content:
                next_marker = yaml_content.index(self.ANNOTATION_MARKER)
                yaml_content = yaml_content[:next_marker]

            # Parse YAML
            data = yaml.safe_load(yaml_content) or {}

            return TypeAnnotation(
                trinity=data.get('trinity', False),
                use_projection=data.get('use_projection', False),
                description=data.get('description'),
                expose_fields=data.get('expose_fields'),
                filter_config=data.get('filters')
            )

        except (yaml.YAMLError, ValueError) as e:
            # Log warning but don't fail
            logger.warning(f"Failed to parse @fraiseql:type: {e}")
            return None

    def parse_mutation_annotation(
        self,
        comment: Optional[str]
    ) -> Optional[MutationAnnotation]:
        """Parse @fraiseql:mutation annotation."""
        # Similar to parse_type_annotation
        # Handle input schema, success/failure types
        pass
```

**Tests:**
```python
def test_parse_type_annotation_basic():
    """Test basic type annotation."""
    comment = """
    @fraiseql:type
    trinity: true
    description: User account
    """
    result = parser.parse_type_annotation(comment)
    assert result.trinity is True
    assert result.description == "User account"

def test_parse_type_annotation_with_fields():
    """Test expose_fields parsing."""
    comment = """
    @fraiseql:type
    expose_fields:
      - id
      - name
      - email
    """
    result = parser.parse_type_annotation(comment)
    assert result.expose_fields == ['id', 'name', 'email']

def test_parse_type_annotation_invalid_yaml():
    """Test error handling."""
    comment = "@fraiseql:type\ninvalid: yaml: [unclosed"
    result = parser.parse_type_annotation(comment)
    assert result is None  # Should not crash
```

**Deliverable**: Robust metadata parsing

---

#### **1.4: Integration Tests (2 days)**

```python
# tests/integration/introspection/test_end_to_end_introspection.py

async def test_discover_and_parse_view():
    """Test full introspection + parsing."""
    # Given: Database with annotated view
    await db.execute("""
        CREATE VIEW v_user AS SELECT ...;
        COMMENT ON VIEW v_user IS '@fraiseql:type
        trinity: true
        description: User account';
    """)

    # When: Introspect and parse
    introspector = PostgresIntrospector(pool)
    views = await introspector.discover_views()
    parser = MetadataParser()
    annotation = parser.parse_type_annotation(views[0].comment)

    # Then: Annotation is correctly parsed
    assert annotation.trinity is True
    assert annotation.description == "User account"

async def test_introspection_performance():
    """Benchmark introspection speed."""
    # Given: 100 views
    # When: discover_views()
    # Then: Completes in < 2 seconds
```

**Deliverable**: Phase 1 complete, introspection working

---

## 🚀 Phase 2: Type Generation (Week 3-4)

**Duration**: 2 weeks
**Goal**: Dynamically generate `@type` classes from metadata
**Risk**: Medium (Dynamic class generation, type mapping)

### **Week 3: Core Type Generation**

#### **2.1: Type Mapping System (2 days)**

```python
# src/fraiseql/introspection/type_mapper.py

from typing import Any, get_type_hints
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID

class TypeMapper:
    """Map PostgreSQL types to Python types."""

    # PostgreSQL → Python type mapping
    PG_TO_PYTHON = {
        'uuid': UUID,
        'text': str,
        'character varying': str,
        'varchar': str,
        'char': str,
        'integer': int,
        'int': int,
        'int4': int,
        'bigint': int,
        'int8': int,
        'smallint': int,
        'int2': int,
        'boolean': bool,
        'bool': bool,
        'timestamp with time zone': datetime,
        'timestamptz': datetime,
        'timestamp without time zone': datetime,
        'timestamp': datetime,
        'date': date,
        'jsonb': dict,
        'json': dict,
        'numeric': Decimal,
        'decimal': Decimal,
        'double precision': float,
        'float8': float,
        'real': float,
        'float4': float,
        # Array types
        'text[]': list[str],
        'integer[]': list[int],
        'uuid[]': list[UUID],
        # Custom types (extensible)
    }

    def pg_type_to_python(
        self,
        pg_type: str,
        nullable: bool = False
    ) -> type:
        """
        Map PostgreSQL type to Python type.

        Args:
            pg_type: PostgreSQL type name (e.g., "text", "integer")
            nullable: Whether the column is nullable

        Returns:
            Python type (with Optional[] if nullable)
        """
        # Normalize type name
        pg_type_clean = pg_type.lower().strip()

        # Handle array types
        if pg_type_clean.endswith('[]'):
            base_type = pg_type_clean[:-2]
            element_type = self.PG_TO_PYTHON.get(base_type, str)
            python_type = list[element_type]
        else:
            python_type = self.PG_TO_PYTHON.get(pg_type_clean, str)

        # Add Optional if nullable
        if nullable:
            from typing import Optional
            return Optional[python_type]
        else:
            return python_type

    def register_custom_type(
        self,
        pg_type: str,
        python_type: type
    ):
        """Register custom type mapping."""
        self.PG_TO_PYTHON[pg_type.lower()] = python_type
```

**Tests:**
```python
def test_basic_type_mapping():
    """Test basic types."""
    mapper = TypeMapper()
    assert mapper.pg_type_to_python('text') is str
    assert mapper.pg_type_to_python('integer') is int
    assert mapper.pg_type_to_python('uuid') is UUID

def test_nullable_type_mapping():
    """Test nullable types."""
    mapper = TypeMapper()
    result = mapper.pg_type_to_python('text', nullable=True)
    assert result == Optional[str]

def test_array_type_mapping():
    """Test array types."""
    mapper = TypeMapper()
    result = mapper.pg_type_to_python('text[]')
    assert result == list[str]
```

**Deliverable**: Reliable type mapping

---

#### **2.2: Dynamic Class Generation (3 days)**

```python
# src/fraiseql/introspection/type_generator.py

from fraiseql import type as fraiseql_type
from fraiseql.introspection.type_mapper import TypeMapper
from typing import Type

class TypeGenerator:
    """Generate FraiseQL @type classes dynamically."""

    def __init__(self, type_mapper: TypeMapper):
        self.type_mapper = type_mapper

    async def generate_type_class(
        self,
        view_metadata: ViewMetadata,
        annotation: TypeAnnotation,
        db_pool: asyncpg.Pool
    ) -> Type:
        """
        Generate a @type class from view metadata.

        Steps:
        1. Introspect JSONB data column to get field structure
        2. Map PostgreSQL types → Python types
        3. Build class dynamically with __annotations__
        4. Apply @type decorator
        5. Register in type registry

        Args:
            view_metadata: Metadata from introspection
            annotation: Parsed @fraiseql:type annotation
            db_pool: Database connection pool

        Returns:
            Decorated Python class
        """
        # 1. Get JSONB structure by querying sample row
        jsonb_fields = await self._introspect_jsonb_column(
            view_metadata.view_name,
            view_metadata.schema_name,
            db_pool
        )

        # 2. Build class name (PascalCase from view name)
        class_name = self._view_name_to_class_name(
            view_metadata.view_name
        )

        # 3. Build field annotations
        annotations = {}
        for field_name, field_info in jsonb_fields.items():
            python_type = self.type_mapper.pg_type_to_python(
                field_info['type'],
                field_info['nullable']
            )
            annotations[field_name] = python_type

        # 4. Create class dynamically
        cls = type(
            class_name,
            (object,),
            {
                '__annotations__': annotations,
                '__doc__': annotation.description or f"Auto-generated from {view_metadata.view_name}",
                '__module__': 'fraiseql.introspection.generated',
            }
        )

        # 5. Apply @type decorator
        sql_source = f"{view_metadata.schema_name}.{view_metadata.view_name}"
        decorated_cls = fraiseql_type(
            sql_source=sql_source,
            jsonb_column="data"
        )(cls)

        # 6. Register in type registry
        from fraiseql.db import _type_registry
        _type_registry[class_name] = decorated_cls

        return decorated_cls

    async def _introspect_jsonb_column(
        self,
        view_name: str,
        schema_name: str,
        db_pool: asyncpg.Pool
    ) -> dict[str, dict]:
        """
        Introspect JSONB data column structure.

        Strategy:
        1. Query one row from view
        2. Extract 'data' column (JSONB)
        3. Infer types from actual values
        4. Return field_name → {type, nullable} mapping
        """
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT data FROM {schema_name}.{view_name} LIMIT 1"
            )

            if not row or not row['data']:
                # View is empty, introspect view definition instead
                return await self._introspect_view_definition(
                    view_name, schema_name, conn
                )

            # Parse JSONB structure
            data = row['data']
            fields = {}

            for field_name, field_value in data.items():
                fields[field_name] = {
                    'type': self._infer_pg_type_from_value(field_value),
                    'nullable': field_value is None
                }

            return fields

    def _infer_pg_type_from_value(self, value: Any) -> str:
        """Infer PostgreSQL type from Python value."""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'double precision'
        elif isinstance(value, str):
            # Check if it's a UUID string
            try:
                UUID(value)
                return 'uuid'
            except:
                return 'text'
        elif isinstance(value, (dict, list)):
            return 'jsonb'
        else:
            return 'text'  # Default fallback

    def _view_name_to_class_name(self, view_name: str) -> str:
        """Convert v_user_profile → UserProfile."""
        # Remove v_ prefix
        name = view_name.replace('v_', '').replace('tv_', '')
        # Split on underscore, capitalize each part
        parts = name.split('_')
        return ''.join(part.capitalize() for part in parts)
```

**Tests:**
```python
async def test_generate_type_class():
    """Test dynamic class generation."""
    # Given: View with JSONB data
    # When: generate_type_class()
    # Then: Returns decorated class with correct annotations

async def test_generate_type_class_trinity():
    """Test trinity pattern."""
    # Given: View with trinity annotation
    # When: generate_type_class()
    # Then: Class has id, identifier fields

async def test_view_name_to_class_name():
    """Test naming conversion."""
    gen = TypeGenerator(TypeMapper())
    assert gen._view_name_to_class_name('v_user') == 'User'
    assert gen._view_name_to_class_name('v_user_profile') == 'UserProfile'
    assert gen._view_name_to_class_name('tv_machine_item') == 'MachineItem'
```

**Deliverable**: Working type generation

---

### **Week 4: Query Generation**

#### **2.3: Query Generator (3 days)**

```python
# src/fraiseql/introspection/query_generator.py

from fraiseql import query
from typing import Type, Optional
from uuid import UUID

class QueryGenerator:
    """Generate standard queries for auto-discovered types."""

    def generate_queries_for_type(
        self,
        type_class: Type,
        view_name: str,
        schema_name: str,
        annotation: TypeAnnotation
    ) -> list[callable]:
        """
        Generate standard queries for a type.

        Generates:
        1. find_one(id) → Single item by UUID
        2. find_all(where, order_by, limit, offset) → List
        3. connection(first, after, where) → Relay pagination

        Returns:
            List of decorated query functions
        """
        queries = []

        # 1. Generate find_one query
        queries.append(
            self._generate_find_one_query(
                type_class, view_name, schema_name
            )
        )

        # 2. Generate find_all query
        queries.append(
            self._generate_find_all_query(
                type_class, view_name, schema_name
            )
        )

        # 3. Generate connection query (optional, for Relay)
        if annotation.filter_config:
            queries.append(
                self._generate_connection_query(
                    type_class, view_name, schema_name
                )
            )

        return queries

    def _generate_find_one_query(
        self,
        type_class: Type,
        view_name: str,
        schema_name: str
    ) -> callable:
        """Generate find_one(id) query."""

        # Create query function dynamically
        @query
        async def find_one_impl(info, id: UUID) -> Optional[type_class]:
            """Get a single item by ID."""
            db = info.context["db"]
            sql_source = f"{schema_name}.{view_name}"
            result = await db.find_one(sql_source, where={"id": id})
            return result

        # Rename function
        type_name = type_class.__name__
        find_one_impl.__name__ = type_name[0].lower() + type_name[1:]
        find_one_impl.__qualname__ = find_one_impl.__name__

        return find_one_impl

    def _generate_find_all_query(
        self,
        type_class: Type,
        view_name: str,
        schema_name: str
    ) -> callable:
        """Generate find_all(where, order_by, ...) query."""

        @query
        async def find_all_impl(
            info,
            where: Optional[dict] = None,
            order_by: Optional[dict] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
        ) -> list[type_class]:
            """Get all items with optional filtering."""
            db = info.context["db"]
            sql_source = f"{schema_name}.{view_name}"
            results = await db.find(
                sql_source,
                where=where,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            return results

        # Rename function
        type_name = type_class.__name__
        plural_name = type_name[0].lower() + type_name[1:] + 's'
        find_all_impl.__name__ = plural_name
        find_all_impl.__qualname__ = plural_name

        return find_all_impl
```

**Tests:**
```python
async def test_generate_find_one_query():
    """Test find_one generation."""
    # Given: User type
    # When: generate_queries_for_type()
    # Then: find_one query works

async def test_generate_find_all_query():
    """Test find_all generation."""
    # Given: User type
    # When: generate_queries_for_type()
    # Then: find_all query works with filtering
```

**Deliverable**: Phase 2 complete, types + queries generated

---

## 🚀 Phase 3: Mutation Generation (Week 5-6)

**Duration**: 2 weeks
**Goal**: Generate mutations from PostgreSQL functions
**Risk**: High (Complex return type handling, error cases)

### **Week 5: Mutation Infrastructure**

#### **3.1: Input Type Generation (2 days)**

```python
# src/fraiseql/introspection/input_generator.py

class InputGenerator:
    """Generate GraphQL input types from function parameters."""

    def generate_input_type(
        self,
        function_metadata: FunctionMetadata,
        annotation: MutationAnnotation
    ) -> Type:
        """
        Generate input class for mutation.

        Example:
            fn_create_user(p_name TEXT, p_email TEXT)
            →
            class CreateUserInput:
                name: str
                email: str
        """
        class_name = self._function_to_input_name(
            function_metadata.function_name
        )

        annotations = {}
        for param in function_metadata.parameters:
            if param.mode == 'IN' and not param.name.startswith('input_pk'):
                # Map parameter to input field
                field_name = param.name.replace('p_', '')  # Remove p_ prefix
                python_type = self.type_mapper.pg_type_to_python(
                    param.pg_type,
                    nullable=(param.default_value is not None)
                )
                annotations[field_name] = python_type

        # Create input class
        input_cls = type(
            class_name,
            (object,),
            {'__annotations__': annotations}
        )

        return input_cls
```

---

#### **3.2: Mutation Generator (3 days)**

```python
# src/fraiseql/introspection/mutation_generator.py

from fraiseql import mutation
from typing import Union

class MutationGenerator:
    """Generate mutations from PostgreSQL functions."""

    def generate_mutation_for_function(
        self,
        function_metadata: FunctionMetadata,
        annotation: MutationAnnotation,
        type_registry: dict[str, Type]
    ) -> callable:
        """
        Generate mutation from function.

        Steps:
        1. Generate input type
        2. Resolve success/failure types
        3. Create mutation function
        4. Handle JSONB return parsing
        """
        # 1. Generate input type
        input_cls = self.input_generator.generate_input_type(
            function_metadata, annotation
        )

        # 2. Get success/failure types
        success_type = type_registry.get(annotation.success_type)
        failure_type = type_registry.get(annotation.failure_type)

        if not success_type or not failure_type:
            logger.warning(
                f"Cannot generate mutation {function_metadata.function_name}: "
                f"missing types {annotation.success_type} or {annotation.failure_type}"
            )
            return None

        # 3. Create mutation function
        @mutation
        async def mutation_impl(
            info,
            input: input_cls
        ) -> Union[success_type, failure_type]:
            """Auto-generated mutation."""
            db = info.context["db"]

            # Call PostgreSQL function
            result = await db.execute_function(
                f"{function_metadata.schema_name}.{function_metadata.function_name}",
                **input.__dict__
            )

            # Parse JSONB result
            # Expected format: {"success": true, "user": {...}}
            #              or: {"success": false, "error": "..."}
            if result.get('success'):
                # Success case
                entity_key = annotation.success_type.lower()
                entity_data = result.get(entity_key)
                return success_type(**entity_data)
            else:
                # Failure case
                return failure_type(**result)

        # 4. Rename function
        mutation_name = self._function_to_mutation_name(
            function_metadata.function_name
        )
        mutation_impl.__name__ = mutation_name
        mutation_impl.__qualname__ = mutation_name
        mutation_impl.__doc__ = annotation.description

        return mutation_impl

    def _function_to_mutation_name(self, function_name: str) -> str:
        """Convert fn_create_user → createUser."""
        name = function_name.replace('fn_', '')
        parts = name.split('_')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])
```

**Deliverable**: Mutation generation working

---

### **Week 6: Error Handling & Edge Cases**

#### **3.3: Union Type Handling (2 days)**

```python
# Handle Union[Success, Failure] return types correctly
# Ensure GraphQL schema generates proper union types
# Test error cases thoroughly
```

#### **3.4: Integration Tests (3 days)**

```python
async def test_mutation_success_case():
    """Test successful mutation."""
    # Given: fn_create_user function
    # When: Execute createUser mutation
    # Then: Returns User type

async def test_mutation_failure_case():
    """Test mutation validation errors."""
    # Given: Invalid input
    # When: Execute mutation
    # Then: Returns ValidationError type
```

**Deliverable**: Phase 3 complete, mutations working

---

## 🚀 Phase 4: Filter Auto-Generation (Week 7)

**Duration**: 1 week
**Goal**: Leverage existing WhereInput/OrderBy generation
**Risk**: Low (existing code, just integration)

### **4.1: WhereInput Generation (2 days)**

```python
# src/fraiseql/introspection/filter_generator.py

from fraiseql.sql.graphql_where_generator import generate_where_input_type

class FilterGenerator:
    """Auto-generate filter inputs."""

    def generate_where_input(
        self,
        type_class: Type,
        view_metadata: ViewMetadata
    ) -> Type:
        """
        Generate WhereInput for a type.

        Leverages existing fraiseql.sql.graphql_where_generator.
        """
        where_input = generate_where_input_type(
            type_name=type_class.__name__,
            fields=self._extract_filterable_fields(view_metadata),
            sql_source=view_metadata.view_name
        )
        return where_input

    def _extract_filterable_fields(
        self,
        view_metadata: ViewMetadata
    ) -> dict:
        """Extract fields for filter generation."""
        # Map column info to filter-compatible format
        # Return field_name → {type, operators} mapping
```

**Deliverable**: Filters auto-generated

---

## 🚀 Phase 5: Auto-Discovery API (Week 8)

**Duration**: 1 week
**Goal**: Orchestration layer + public API
**Risk**: Low (composition of existing components)

### **5.1: AutoDiscovery Class (3 days)**

```python
# src/fraiseql/auto_discovery.py

class AutoDiscovery:
    """Orchestrate auto-discovery from PostgreSQL."""

    async def discover_all(self) -> dict:
        """
        Full discovery pipeline.

        Returns:
            {
                'types': [User, Post, ...],
                'queries': [user, users, ...],
                'mutations': [createUser, ...],
                'where_inputs': {...},
                'order_by_inputs': {...}
            }
        """
        # 1. Introspect database
        # 2. Parse metadata
        # 3. Generate types
        # 4. Generate queries
        # 5. Generate mutations
        # 6. Generate filters
        # 7. Return registry
```

### **5.2: Update create_fraiseql_app (2 days)**

```python
# src/fraiseql/fastapi/__init__.py

async def create_fraiseql_app(
    database_url: str,
    auto_discover: bool = False,
    **kwargs
):
    """Extended with auto_discover parameter."""
    if auto_discover:
        schema = await auto_discover(database_url)
        # Merge with manual definitions
```

**Deliverable**: Public API ready

---

## 🚀 Phase 6: Production Polish (Week 9-10)

**Duration**: 2 weeks
**Goal**: Production-ready quality
**Risk**: Low (polish and testing)

### **Week 9: Performance & Caching**

#### **6.1: Caching Layer (3 days)**

```python
# Cache introspection results
# - File-based cache for development
# - Redis cache for production
# - TTL configuration
# - Cache invalidation on schema changes
```

#### **6.2: Performance Optimization (2 days)**

```python
# - Parallel introspection (views + functions)
# - Lazy loading of types
# - Connection pooling tuning
# - Benchmark tests (< 2s for 100 tables)
```

---

### **Week 10: Documentation & Examples**

#### **6.3: Documentation (3 days)**

- [ ] Usage guide (auto-discovery)
- [ ] Migration guide (manual → auto)
- [ ] Best practices for metadata
- [ ] Troubleshooting guide
- [ ] API reference

#### **6.4: Examples (2 days)**

```python
# Complete example: SpecQL → AutoFraiseQL
# Real-world use case (blog, e-commerce)
# Performance benchmarks
```

**Deliverable**: Production-ready release

---

## 🎯 Release Strategy

### **Alpha Release (End of Week 8)**

```python
# Limited release to early adopters
# Version: 1.4.0-alpha
# Features:
# - Basic auto-discovery
# - Types + queries working
# - Mutations (basic)
# Audience: 10-20 beta users
```

### **Beta Release (End of Week 10)**

```python
# Version: 1.4.0-beta
# Features:
# - Full auto-discovery
# - Production-ready
# - Documentation
# Audience: All users (opt-in)
```

### **Stable Release (Week 12)**

```python
# Version: 1.4.0 (or 2.0.0?)
# Features:
# - Battle-tested
# - Performance optimized
# - Complete docs
# Audience: GA (general availability)
```

---

## ✅ Success Criteria

AutoFraiseQL is **production-ready** when:

1. ✅ **Zero Python code** needed for CRUD (just metadata)
2. ✅ **< 2s introspection** for 100 tables
3. ✅ **100% backward compatible** (all existing tests pass)
4. ✅ **95%+ type coverage** (PostgreSQL types mapped)
5. ✅ **< 5% performance overhead** vs manual FraiseQL
6. ✅ **Documentation complete** (guides, examples, API ref)
7. ✅ **Battle-tested** (3+ production users, < 10 critical bugs)

---

## 🚨 Risk Mitigation

### **Technical Risks**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Type mapping edge cases** | High | Medium | Comprehensive test suite, fallback to `str` |
| **Dynamic class issues** | Medium | High | Extensive testing, Python 3.13 compatibility |
| **Performance degradation** | Low | High | Benchmarks, caching, lazy loading |
| **Backward incompatibility** | Low | Critical | 100% test coverage of existing behavior |

### **Business Risks**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **User adoption slow** | Medium | Medium | Marketing, examples, migrations guides |
| **Competition copies** | High | Low | Open source advantage, community |
| **Scope creep** | High | Medium | Strict phase boundaries, MVP focus |

---

## 📊 Resource Requirements

### **Team**

- **Lead Developer** (full-time, 10 weeks) - Core implementation
- **Backend Engineer** (50%, 10 weeks) - Testing, integration
- **Tech Writer** (25%, 4 weeks) - Documentation
- **DevOps** (10%, 10 weeks) - CI/CD, infrastructure

### **Infrastructure**

- PostgreSQL test instances (multiple versions)
- CI/CD pipeline updates
- Benchmarking infrastructure

### **Budget Estimate**

- Development: 15 person-weeks × $5k/week = **$75k**
- Infrastructure: $2k
- Contingency (20%): $15k
- **Total: ~$92k**

---

## 🎯 Next Steps (Immediate Actions)

### **Week 0 (This Week)**

1. **Get team buy-in** (2 days)
   - Present this plan
   - Discuss concerns
   - Get go/no-go decision

2. **Technical spike** (2 days)
   - Validate introspection approach
   - Test dynamic class generation
   - Measure performance

3. **Infrastructure setup** (1 day)
   - Create module structure
   - Setup CI/CD
   - Prepare test database

### **Week 1 (Next Week)**

- Start Phase 1: Introspection Engine
- Daily standups to track progress
- Early feedback loop with users

---

## 💡 Final Thoughts (CTO Perspective)

**This is a Category-Defining Feature.**

AutoFraiseQL transforms FraiseQL from "a fast GraphQL framework" to **"the database-first application platform"**.

**Strategic Positioning:**
- **Unique**: No other framework offers full auto-discovery from PostgreSQL metadata
- **SpecQL-ready**: Perfect complement to declarative business logic
- **Developer experience**: 10-20x productivity gain
- **Backward compatible**: Zero breaking changes

**The Market Opportunity:**

Developers are tired of:
- Writing boilerplate code
- Keeping schemas in sync
- Managing multiple sources of truth
- Complex ORMs and code generation

AutoFraiseQL solves all of this with **one simple principle**:

> **Your database schema IS your API schema.**

**Let's build this. 🚀**

---

**END OF PHASED IMPLEMENTATION PLAN**
