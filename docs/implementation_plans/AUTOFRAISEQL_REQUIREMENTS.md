# AutoFraiseQL Requirements

**Date**: November 8, 2025
**Context**: SpecQL → Database → AutoFraiseQL Pipeline
**Goal**: Auto-generate complete GraphQL API from PostgreSQL metadata

---

## Executive Summary

**The Pipeline:**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│   SpecQL     │ ──▶│  PostgreSQL  │ ──▶│  AutoFraiseQL    │
│   (YAML)     │    │  (Metadata)  │    │  (GraphQL API)   │
└──────────────┘    └──────────────┘    └──────────────────┘
     │                     │                      │
     │                     │                      │
  Business              Database              GraphQL API
   Rules               Structure            (auto-generated)
```

**What AutoFraiseQL needs to do:**

1. **Introspect PostgreSQL** → Discover views, functions, types
2. **Parse metadata comments** → Extract `@fraiseql:type`, `@fraiseql:mutation` annotations
3. **Generate GraphQL schema** → Types, queries, mutations
4. **No Python code required** → Pure introspection-driven

---

## 🎯 Required Features for AutoFraiseQL

### **Feature 1: PostgreSQL Introspection Engine**

**What it does:**
- Connects to PostgreSQL database
- Discovers all views matching pattern (e.g., `v_*`, `tv_*`)
- Discovers all functions matching pattern (e.g., `fn_*`)
- Reads COMMENT metadata from views and functions
- Parses JSONB column structure from views

**Implementation:**

```python
# src/fraiseql/introspection/postgres_introspector.py

class PostgresIntrospector:
    """Introspect PostgreSQL database for FraiseQL metadata."""

    async def discover_types(
        self,
        view_pattern: str = "v_%",
        schemas: list[str] = ["public"]
    ) -> list[TypeMetadata]:
        """
        Discover all views that should become GraphQL types.

        Returns:
            List of TypeMetadata with fields, descriptions, etc.
        """
        query = """
        SELECT
            schemaname,
            viewname,
            obj_description(c.oid, 'pg_class') as view_comment,
            jsonb_object_agg(
                a.attname,
                jsonb_build_object(
                    'type', format_type(a.atttypid, a.atttypmod),
                    'nullable', NOT a.attnotnull,
                    'comment', col_description(c.oid, a.attnum)
                )
            ) as columns
        FROM pg_views v
        JOIN pg_class c ON c.relname = v.viewname
        JOIN pg_attribute a ON a.attrelid = c.oid
        WHERE schemaname = ANY($1)
          AND viewname LIKE $2
          AND a.attnum > 0
          AND NOT a.attisdropped
        GROUP BY schemaname, viewname, c.oid
        """
        # Execute and parse results

    async def discover_mutations(
        self,
        function_pattern: str = "fn_%",
        schemas: list[str] = ["public"]
    ) -> list[MutationMetadata]:
        """
        Discover all functions that should become GraphQL mutations.

        Returns:
            List of MutationMetadata with parameters, return types, etc.
        """
        query = """
        SELECT
            n.nspname as schema_name,
            p.proname as function_name,
            pg_get_function_arguments(p.oid) as arguments,
            pg_get_function_result(p.oid) as return_type,
            obj_description(p.oid, 'pg_proc') as function_comment
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = ANY($1)
          AND p.proname LIKE $2
        """
        # Execute and parse results
```

---

### **Feature 2: Metadata Parser**

**What it does:**
- Parses `@fraiseql:type` annotations from view comments
- Parses `@fraiseql:mutation` annotations from function comments
- Extracts YAML-like metadata from comments
- Validates metadata structure

**Implementation:**

```python
# src/fraiseql/introspection/metadata_parser.py

from dataclasses import dataclass
from typing import Optional
import yaml

@dataclass
class TypeAnnotation:
    """Parsed @fraiseql:type annotation."""
    trinity: bool = False
    use_projection: bool = False
    description: Optional[str] = None
    expose_fields: Optional[list[str]] = None

@dataclass
class MutationAnnotation:
    """Parsed @fraiseql:mutation annotation."""
    input_schema: dict[str, dict]
    success_type: str
    failure_type: str
    description: Optional[str] = None

class MetadataParser:
    """Parse @fraiseql annotations from PostgreSQL comments."""

    def parse_type_annotation(self, comment: str) -> Optional[TypeAnnotation]:
        """
        Parse @fraiseql:type annotation.

        Example input:
            @fraiseql:type
            trinity: true
            use_projection: false
            description: User account
            expose_fields:
              - id
              - identifier
              - email

        Returns:
            TypeAnnotation instance or None
        """
        if not comment or '@fraiseql:type' not in comment:
            return None

        # Extract YAML after @fraiseql:type marker
        yaml_start = comment.index('@fraiseql:type') + len('@fraiseql:type')
        yaml_content = comment[yaml_start:].strip()

        # Parse YAML
        data = yaml.safe_load(yaml_content)

        return TypeAnnotation(
            trinity=data.get('trinity', False),
            use_projection=data.get('use_projection', False),
            description=data.get('description'),
            expose_fields=data.get('expose_fields')
        )

    def parse_mutation_annotation(self, comment: str) -> Optional[MutationAnnotation]:
        """
        Parse @fraiseql:mutation annotation.

        Example input:
            @fraiseql:mutation
            input:
              name:
                type: string
                description: User full name
              email:
                type: string
                description: Email address
            success: User
            failure: ValidationError
            description: Create a new user

        Returns:
            MutationAnnotation instance or None
        """
        if not comment or '@fraiseql:mutation' not in comment:
            return None

        yaml_start = comment.index('@fraiseql:mutation') + len('@fraiseql:mutation')
        yaml_content = comment[yaml_start:].strip()

        data = yaml.safe_load(yaml_content)

        return MutationAnnotation(
            input_schema=data.get('input', {}),
            success_type=data['success'],
            failure_type=data['failure'],
            description=data.get('description')
        )
```

---

### **Feature 3: Type Generator (from Views)**

**What it does:**
- Takes TypeMetadata from introspection
- Generates Python `@type` classes dynamically
- Maps PostgreSQL types → Python types
- Handles trinity pattern (id, identifier, data)

**Implementation:**

```python
# src/fraiseql/introspection/type_generator.py

from typing import Type, Any
from fraiseql import type as fraiseql_type

class TypeGenerator:
    """Generate FraiseQL @type classes from database metadata."""

    # PostgreSQL type → Python type mapping
    TYPE_MAPPING = {
        'uuid': 'UUID',
        'text': 'str',
        'character varying': 'str',
        'integer': 'int',
        'bigint': 'int',
        'boolean': 'bool',
        'timestamp with time zone': 'datetime',
        'timestamp without time zone': 'datetime',
        'date': 'date',
        'jsonb': 'dict',
        'json': 'dict',
        'numeric': 'Decimal',
        'double precision': 'float',
    }

    def generate_type_class(
        self,
        type_metadata: TypeMetadata,
        annotation: TypeAnnotation
    ) -> Type:
        """
        Generate a FraiseQL @type class dynamically.

        Args:
            type_metadata: Metadata from PostgreSQL introspection
            annotation: Parsed @fraiseql:type annotation

        Returns:
            Dynamically created Python class with @type decorator
        """
        # Build class attributes
        attributes = {}
        annotations = {}

        # Parse JSONB data column to extract fields
        if 'data' in type_metadata.columns:
            # Introspect a sample row to get JSONB structure
            sample_data = self._get_sample_data(type_metadata.view_name)
            if sample_data:
                for field_name, field_value in sample_data.items():
                    python_type = self._infer_python_type(field_value)
                    annotations[field_name] = python_type

        # Create class dynamically
        cls_name = self._to_pascal_case(type_metadata.view_name.replace('v_', ''))

        cls = type(
            cls_name,
            (object,),
            {
                '__annotations__': annotations,
                '__doc__': annotation.description,
                **attributes
            }
        )

        # Apply @type decorator
        decorated_cls = fraiseql_type(
            sql_source=type_metadata.view_name,
            jsonb_column="data"
        )(cls)

        return decorated_cls

    def _get_sample_data(self, view_name: str) -> dict:
        """Query one row from view to inspect JSONB structure."""
        query = f"SELECT data FROM {view_name} LIMIT 1"
        # Execute and return first row's data column

    def _infer_python_type(self, value: Any) -> str:
        """Infer Python type annotation from JSON value."""
        if isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            return 'str'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        else:
            return 'Any'

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in snake_str.split('_'))
```

---

### **Feature 4: Query Generator (Auto-Generate Queries)**

**What it does:**
- For each discovered type, generates standard queries:
  - `find_one(id)` → Single item by ID
  - `find_all(where, order_by, limit, offset)` → List with filters
  - `connection(first, after, where)` → Relay-style pagination
- No Python code needed from user

**Implementation:**

```python
# src/fraiseql/introspection/query_generator.py

from fraiseql import query

class QueryGenerator:
    """Generate standard queries for each discovered type."""

    def generate_queries_for_type(
        self,
        type_class: Type,
        view_name: str
    ) -> list[callable]:
        """
        Generate standard queries for a type.

        Returns:
            List of query functions decorated with @query
        """
        queries = []

        # 1. Generate find_one query
        @query
        async def find_one(info, id: UUID) -> Optional[type_class]:
            db = info.context["db"]
            result = await db.find_one(view_name, where={"id": id})
            return result

        # Rename function dynamically
        find_one.__name__ = f"{type_class.__name__.lower()}"
        queries.append(find_one)

        # 2. Generate find_all query
        @query
        async def find_all(
            info,
            where: Optional[dict] = None,
            order_by: Optional[dict] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
        ) -> list[type_class]:
            db = info.context["db"]
            results = await db.find(
                view_name,
                where=where,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            return results

        find_all.__name__ = f"{type_class.__name__.lower()}s"
        queries.append(find_all)

        # 3. Generate connection query (Relay pagination)
        @query
        async def connection(
            info,
            first: Optional[int] = None,
            after: Optional[str] = None,
            where: Optional[dict] = None
        ) -> Connection[type_class]:
            db = info.context["db"]
            # Implement Relay connection pattern
            # ...

        connection.__name__ = f"{type_class.__name__.lower()}Connection"
        queries.append(connection)

        return queries
```

---

### **Feature 5: Mutation Generator (from Functions)**

**What it does:**
- For each discovered function with `@fraiseql:mutation`, generates GraphQL mutation
- Parses function parameters → GraphQL input type
- Parses function return type → Union[SuccessType, FailureType]
- Handles JSONB return format

**Implementation:**

```python
# src/fraiseql/introspection/mutation_generator.py

from fraiseql import mutation
from typing import Union

class MutationGenerator:
    """Generate mutations from PostgreSQL functions."""

    def generate_mutation_for_function(
        self,
        function_metadata: MutationMetadata,
        annotation: MutationAnnotation,
        type_registry: dict[str, Type]
    ) -> callable:
        """
        Generate a mutation from a PostgreSQL function.

        Args:
            function_metadata: Metadata from introspection
            annotation: Parsed @fraiseql:mutation annotation
            type_registry: Map of type names to Python classes

        Returns:
            Mutation function decorated with @mutation
        """
        # Get success/failure types
        success_type = type_registry[annotation.success_type]
        failure_type = type_registry[annotation.failure_type]

        # Build input class dynamically
        input_class = self._build_input_class(
            annotation.input_schema,
            function_metadata.function_name
        )

        # Generate mutation function
        @mutation
        async def mutation_fn(
            info,
            input: input_class
        ) -> Union[success_type, failure_type]:
            db = info.context["db"]

            # Call PostgreSQL function
            result = await db.execute_function(
                function_metadata.function_name,
                **input.__dict__
            )

            # Parse JSONB result
            if result.get('success'):
                # Return success type
                return success_type(**result[annotation.success_type.lower()])
            else:
                # Return failure type
                return failure_type(**result)

        # Rename function
        mutation_fn.__name__ = self._to_camel_case(
            function_metadata.function_name.replace('fn_', '')
        )
        mutation_fn.__doc__ = annotation.description

        return mutation_fn

    def _build_input_class(
        self,
        input_schema: dict,
        function_name: str
    ) -> Type:
        """Build GraphQL input class from schema."""
        class_name = f"{self._to_pascal_case(function_name)}Input"

        annotations = {}
        for field_name, field_def in input_schema.items():
            python_type = self._graphql_type_to_python(field_def['type'])
            annotations[field_name] = python_type

        input_cls = type(
            class_name,
            (object,),
            {'__annotations__': annotations}
        )

        return input_cls

    def _graphql_type_to_python(self, graphql_type: str) -> str:
        """Map GraphQL type string to Python type."""
        mapping = {
            'string': 'str',
            'int': 'int',
            'boolean': 'bool',
            'float': 'float',
            'uuid': 'UUID',
        }
        return mapping.get(graphql_type.lower(), 'str')
```

---

### **Feature 6: WhereInput & OrderBy Auto-Generation**

**What it does:**
- For each type, generates `WhereInput` with field-specific operators
- For each type, generates `OrderByInput` with ASC/DESC options
- Uses existing FraiseQL filter generation (Issue #122, #124)

**Implementation:**

```python
# src/fraiseql/introspection/filter_generator.py

class FilterGenerator:
    """Auto-generate WhereInput and OrderBy types."""

    def generate_where_input(
        self,
        type_class: Type,
        type_metadata: TypeMetadata
    ) -> Type:
        """
        Generate WhereInput type for filtering.

        Leverages existing auto-generation from Issue #122/#124.
        """
        # Use existing fraiseql.sql.graphql_where_generator
        from fraiseql.sql.graphql_where_generator import generate_where_input_type

        where_input = generate_where_input_type(
            type_name=type_class.__name__,
            fields=type_metadata.columns,
            sql_source=type_metadata.view_name
        )

        return where_input

    def generate_order_by_input(
        self,
        type_class: Type,
        type_metadata: TypeMetadata
    ) -> Type:
        """
        Generate OrderByInput type for sorting.

        Leverages existing auto-generation.
        """
        from fraiseql.sql.graphql_order_by_generator import generate_order_by_type

        order_by = generate_order_by_type(
            type_name=type_class.__name__,
            fields=type_metadata.columns
        )

        return order_by
```

---

### **Feature 7: Auto-Discovery API**

**What it does:**
- Main entry point for users
- Orchestrates introspection → generation → app creation
- Single function call: `auto_discover=True`

**Implementation:**

```python
# src/fraiseql/auto_discovery.py

from fraiseql.introspection import (
    PostgresIntrospector,
    MetadataParser,
    TypeGenerator,
    QueryGenerator,
    MutationGenerator,
    FilterGenerator
)

class AutoDiscovery:
    """Auto-discover and generate GraphQL API from PostgreSQL."""

    def __init__(
        self,
        database_url: str,
        view_pattern: str = "v_%",
        function_pattern: str = "fn_%",
        schemas: list[str] = ["public"]
    ):
        self.database_url = database_url
        self.view_pattern = view_pattern
        self.function_pattern = function_pattern
        self.schemas = schemas

        self.introspector = PostgresIntrospector(database_url)
        self.metadata_parser = MetadataParser()
        self.type_generator = TypeGenerator()
        self.query_generator = QueryGenerator()
        self.mutation_generator = MutationGenerator()
        self.filter_generator = FilterGenerator()

    async def discover_all(self) -> dict:
        """
        Discover and generate complete GraphQL schema.

        Returns:
            {
                'types': [User, Post, ...],
                'queries': [user, users, post, posts, ...],
                'mutations': [createUser, updateUser, ...],
                'where_inputs': {...},
                'order_by_inputs': {...}
            }
        """
        result = {
            'types': [],
            'queries': [],
            'mutations': [],
            'where_inputs': {},
            'order_by_inputs': {}
        }

        # 1. Discover types from views
        type_metadata_list = await self.introspector.discover_types(
            view_pattern=self.view_pattern,
            schemas=self.schemas
        )

        type_registry = {}

        for type_metadata in type_metadata_list:
            # Parse annotation
            annotation = self.metadata_parser.parse_type_annotation(
                type_metadata.view_comment
            )

            if not annotation:
                continue  # Skip views without @fraiseql:type

            # Generate type class
            type_class = self.type_generator.generate_type_class(
                type_metadata,
                annotation
            )

            result['types'].append(type_class)
            type_registry[type_class.__name__] = type_class

            # Generate queries for this type
            queries = self.query_generator.generate_queries_for_type(
                type_class,
                type_metadata.view_name
            )
            result['queries'].extend(queries)

            # Generate filter inputs
            where_input = self.filter_generator.generate_where_input(
                type_class,
                type_metadata
            )
            order_by = self.filter_generator.generate_order_by_input(
                type_class,
                type_metadata
            )

            result['where_inputs'][type_class.__name__] = where_input
            result['order_by_inputs'][type_class.__name__] = order_by

        # 2. Discover mutations from functions
        mutation_metadata_list = await self.introspector.discover_mutations(
            function_pattern=self.function_pattern,
            schemas=self.schemas
        )

        for mutation_metadata in mutation_metadata_list:
            # Parse annotation
            annotation = self.metadata_parser.parse_mutation_annotation(
                mutation_metadata.function_comment
            )

            if not annotation:
                continue  # Skip functions without @fraiseql:mutation

            # Generate mutation
            mutation_fn = self.mutation_generator.generate_mutation_for_function(
                mutation_metadata,
                annotation,
                type_registry
            )

            result['mutations'].append(mutation_fn)

        return result


# Public API
async def auto_discover(
    database_url: str,
    **options
) -> dict:
    """
    Auto-discover GraphQL API from PostgreSQL metadata.

    Usage:
        schema = await auto_discover("postgresql://localhost/mydb")
        app = create_fraiseql_app(**schema)
    """
    discovery = AutoDiscovery(database_url, **options)
    return await discovery.discover_all()
```

---

### **Feature 8: Updated create_fraiseql_app**

**What it does:**
- Extends existing `create_fraiseql_app` to support `auto_discover=True`
- Handles auto-discovered types, queries, mutations

**Implementation:**

```python
# src/fraiseql/fastapi/__init__.py (extend existing)

from fraiseql.auto_discovery import auto_discover

async def create_fraiseql_app(
    database_url: str,
    types: Optional[list[Type]] = None,
    queries: Optional[list[callable]] = None,
    mutations: Optional[list[callable]] = None,
    auto_discover: bool = False,  # NEW
    auto_discover_options: Optional[dict] = None,  # NEW
    **kwargs
):
    """
    Create FraiseQL FastAPI application.

    Args:
        database_url: PostgreSQL connection string
        types: List of @type classes (optional if auto_discover=True)
        queries: List of @query functions (optional if auto_discover=True)
        mutations: List of @mutation functions (optional if auto_discover=True)
        auto_discover: Enable automatic schema discovery from PostgreSQL
        auto_discover_options: Options for auto-discovery
    """
    if auto_discover:
        # Auto-discover schema from database
        schema = await auto_discover(
            database_url,
            **(auto_discover_options or {})
        )

        # Merge with manually defined types/queries/mutations
        types = (types or []) + schema['types']
        queries = (queries or []) + schema['queries']
        mutations = (mutations or []) + schema['mutations']

    # Existing app creation logic
    # ...
```

---

## 📋 Implementation Checklist

### **Phase 1: Core Introspection (Week 1)**

- [ ] **PostgresIntrospector** class
  - [ ] `discover_types()` - Find views with metadata
  - [ ] `discover_mutations()` - Find functions with metadata
  - [ ] Connection pooling and error handling

- [ ] **MetadataParser** class
  - [ ] `parse_type_annotation()` - Parse `@fraiseql:type`
  - [ ] `parse_mutation_annotation()` - Parse `@fraiseql:mutation`
  - [ ] YAML parsing and validation

**Deliverable**: Can introspect database and parse metadata

---

### **Phase 2: Type Generation (Week 2)**

- [ ] **TypeGenerator** class
  - [ ] `generate_type_class()` - Create Python classes dynamically
  - [ ] PostgreSQL type → Python type mapping
  - [ ] JSONB column introspection
  - [ ] Handle trinity pattern (id, identifier, data)

- [ ] **Unit tests** for type generation
  - [ ] Test all PostgreSQL type mappings
  - [ ] Test JSONB field extraction
  - [ ] Test class decoration

**Deliverable**: Can generate @type classes from views

---

### **Phase 3: Query Generation (Week 3)**

- [ ] **QueryGenerator** class
  - [ ] `generate_queries_for_type()` - Standard queries
  - [ ] find_one(id) query
  - [ ] find_all(where, order_by) query
  - [ ] connection(first, after) query (Relay)

- [ ] **Integration tests**
  - [ ] Test generated queries execute correctly
  - [ ] Test filtering with WhereInput
  - [ ] Test sorting with OrderBy

**Deliverable**: Can generate queries automatically

---

### **Phase 4: Mutation Generation (Week 4)**

- [ ] **MutationGenerator** class
  - [ ] `generate_mutation_for_function()` - Create mutations
  - [ ] Parse function parameters → GraphQL input
  - [ ] Handle JSONB return type
  - [ ] Union[Success, Failure] return types

- [ ] **Integration tests**
  - [ ] Test mutation execution
  - [ ] Test success/failure handling
  - [ ] Test input validation

**Deliverable**: Can generate mutations from functions

---

### **Phase 5: Filter Auto-Generation (Week 5)**

- [ ] **FilterGenerator** class
  - [ ] Integrate with existing `graphql_where_generator.py`
  - [ ] Integrate with existing `graphql_order_by_generator.py`
  - [ ] Generate WhereInput per type
  - [ ] Generate OrderByInput per type

- [ ] **Tests**
  - [ ] Test filter generation for all field types
  - [ ] Test operator availability (eq, neq, gt, contains, etc.)

**Deliverable**: Auto-generated filters work end-to-end

---

### **Phase 6: Auto-Discovery API (Week 6)**

- [ ] **AutoDiscovery** class
  - [ ] `discover_all()` - Orchestrate full discovery
  - [ ] Handle type registry (resolve references)
  - [ ] Error handling and logging

- [ ] **Updated create_fraiseql_app**
  - [ ] `auto_discover=True` parameter
  - [ ] Merge auto-discovered + manual schema
  - [ ] Documentation

- [ ] **End-to-end tests**
  - [ ] Test complete pipeline: DB → GraphQL
  - [ ] Test with printoptim_backend schema
  - [ ] Performance benchmarks

**Deliverable**: Full auto-discovery works end-to-end

---

### **Phase 7: Production Polish (Week 7-8)**

- [ ] **Error handling**
  - [ ] Graceful handling of missing metadata
  - [ ] Validation of @fraiseql annotations
  - [ ] Helpful error messages

- [ ] **Performance**
  - [ ] Cache introspection results
  - [ ] Lazy loading of types
  - [ ] Connection pooling

- [ ] **Documentation**
  - [ ] Usage guide for auto-discovery
  - [ ] Migration guide (manual → auto)
  - [ ] Best practices for metadata annotations

- [ ] **Examples**
  - [ ] Complete example with SpecQL → AutoFraiseQL
  - [ ] Real-world use cases

**Deliverable**: Production-ready AutoFraiseQL

---

## 🎯 API Usage Example

### **Before (Manual FraiseQL)**

```python
from fraiseql import type, query, mutation
from fraiseql.fastapi import create_fraiseql_app

# Must define every type manually
@type(sql_source="v_user")
class User:
    id: UUID
    identifier: str
    email: str
    name: str

# Must define every query manually
@query
async def user(info, id: UUID) -> User:
    db = info.context["db"]
    return await db.find_one("v_user", where={"id": id})

@query
async def users(info, where: dict = None) -> list[User]:
    db = info.context["db"]
    return await db.find("v_user", where=where)

# Must define every mutation manually
@mutation
async def create_user(info, name: str, email: str) -> User:
    # ...

app = create_fraiseql_app(
    database_url="postgresql://localhost/mydb",
    types=[User],
    queries=[user, users],
    mutations=[create_user]
)
```

**Lines of Python code**: ~40 lines

---

### **After (AutoFraiseQL)**

```python
from fraiseql.fastapi import create_fraiseql_app

# PostgreSQL already has metadata:
# COMMENT ON VIEW v_user IS '@fraiseql:type ...'
# COMMENT ON FUNCTION fn_create_user IS '@fraiseql:mutation ...'

app = create_fraiseql_app(
    database_url="postgresql://localhost/mydb",
    auto_discover=True  # 🎯 That's it!
)
```

**Lines of Python code**: ~5 lines

**Reduction**: 87% less code

---

## 💡 Key Design Decisions

### **1. Metadata in PostgreSQL Comments**

**Why?**
- Single source of truth (database schema)
- Version controlled with migrations
- Visible in database tools (pgAdmin, DBeaver)
- No external configuration files

**Format:**
```sql
COMMENT ON VIEW v_user IS '@fraiseql:type
trinity: true
description: User account';
```

---

### **2. YAML in Comments**

**Why?**
- Readable and writable by humans
- Structured data (not just text)
- Easy to parse (yaml library)
- Familiar to developers

---

### **3. Pattern-Based Discovery**

**Why?**
- Explicit opt-in (views/functions must match pattern)
- Prevents accidental exposure
- Follows PostgreSQL conventions (v_*, fn_*)

**Configuration:**
```python
auto_discover=True,
auto_discover_options={
    'view_pattern': 'v_%',     # Only v_* views
    'function_pattern': 'fn_%', # Only fn_* functions
    'schemas': ['public', 'catalog']  # Specific schemas
}
```

---

### **4. Merge Auto + Manual**

**Why?**
- Gradual migration path
- Custom logic for complex cases
- Override auto-generated behavior

**Example:**
```python
# Some types auto-discovered, some manual
app = create_fraiseql_app(
    database_url="...",
    auto_discover=True,  # Discovers 90% of schema
    types=[CustomComplexType],  # Override 10% manually
    queries=[custom_query]
)
```

---

## 🚀 Benefits

### **1. Developer Productivity**

- **Before**: 40 lines Python per entity
- **After**: 0 lines Python (just metadata in SQL)
- **Speedup**: 10-20x faster development

### **2. Maintainability**

- **Single source of truth**: Database schema
- **Version controlled**: SQL migrations
- **No code duplication**: Type definitions in one place

### **3. SpecQL Compatibility**

```
SpecQL (YAML) → SQL Generator → PostgreSQL (with metadata)
                                       ↓
                                 AutoFraiseQL
                                       ↓
                                  GraphQL API
```

**Complete pipeline**: YAML business logic → Working API (no Python)

---

## ✅ Success Criteria

AutoFraiseQL is successful when:

1. ✅ **Zero Python code required** for standard CRUD operations
2. ✅ **Complete introspection** of views, functions, types from PostgreSQL
3. ✅ **Metadata-driven** schema generation from comments
4. ✅ **Compatible with SpecQL** generated schemas
5. ✅ **Performance** equivalent to manual FraiseQL
6. ✅ **Production-ready** error handling, caching, docs
7. ✅ **Backward compatible** with existing manual FraiseQL apps

---

## 📊 Estimated Effort

| Phase | Duration | Complexity |
|-------|----------|------------|
| Core Introspection | 1 week | Medium |
| Type Generation | 1 week | Medium |
| Query Generation | 1 week | Low |
| Mutation Generation | 1 week | High |
| Filter Auto-Gen | 1 week | Low (leverage existing) |
| Auto-Discovery API | 1 week | Medium |
| Production Polish | 2 weeks | Medium |
| **Total** | **8 weeks** | **Medium-High** |

---

## 🎯 Next Steps

1. **Validate approach** with FraiseQL team
2. **Create POC** for introspection + type generation (Week 1)
3. **Iterate** based on feedback
4. **Full implementation** (Weeks 2-8)
5. **Release** as FraiseQL v2.0 or v1.4 feature

---

**END OF REQUIREMENTS DOCUMENT**
