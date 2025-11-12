# SpecQL Table View (TV_) Generation Architecture

## Executive Summary

SpecQL implements a complete CQRS-style table view generation system that creates read-optimized denormalized views (`tv_*` tables) for every entity. This architecture ensures:

- **CQRS Pattern**: Separate write (`tb_*`) and read (`tv_*`) sides
- **Denormalization**: Entity data + all related entity data in JSONB
- **GraphQL Optimization**: FraiseQL can auto-discover types from `tv_*` tables
- **Flexible Generation**: Automatic (based on foreign keys) or explicit control

---

## 1. CORE GENERATION LOGIC

### Primary Generator: `TableViewGenerator`
**File**: `/home/lionel/code/specql/src/generators/schema/table_view_generator.py`

#### Key Responsibilities:
1. Generate `CREATE TABLE tv_{entity}` DDL
2. Create indexes (tenant, FKs, JSONB, path if hierarchical)
3. Generate `refresh_tv_{entity}()` function

#### Key Methods:

```python
def should_generate() -> bool:
    """Check if tv_ should be generated based on entity.table_views config"""
    return self.entity.should_generate_table_view

def generate_schema() -> str:
    """Generate complete tv_ table with DDL + indexes + refresh function"""
    
def _generate_table_ddl() -> str:
    """Generate CREATE TABLE statement"""
    # Trinity pattern: pk_{entity}, id (UUID), tenant_id
    # FK columns: fk_{field_name}, {field_name}_id (UUID)
    # Extra filter columns (if configured)
    # data JSONB NOT NULL
    
def _generate_indexes() -> str:
    """Generate all indexes"""
    # idx_tv_{entity}_tenant
    # idx_tv_{entity}_{field}_id (for each FK)
    # idx_tv_{entity}_{extra_col} (for extra filter columns)
    # idx_tv_{entity}_data (GIN index for JSONB)
    
def _generate_refresh_function() -> str:
    """Generate refresh_tv_{entity}(p_pk_{entity} INTEGER DEFAULT NULL)"""
    # JOINs to tv_ tables (NOT tb_!)
    # Composes JSONB from related tv_.data
    # Includes scalar fields + denormalized relations
```

#### Critical Design Decisions:

1. **JOINs to `tv_` NOT `tb_` tables**
   - Ensures composition of already-denormalized relations
   - Prevents deep nesting of raw tb_ joins

2. **JSONB Composition**
   - All entity fields are in `data` column
   - Related entities: full `tv_{entity}.data` included
   - Supports explicit field selection via `include_relations`

3. **Field Naming Convention**
   - FK columns use field name: `fk_author` (not `fk_user` for "author: ref(User)")
   - UUID columns: `author_id` (not `user_id`)
   - This supports multiple refs to same entity

---

## 2. DEPENDENCY RESOLUTION

### `TableViewDependencyResolver`
**File**: `/home/lionel/code/specql/src/generators/schema/table_view_dependency.py`

Ensures proper generation order when entities reference each other.

#### Algorithm:
- Builds dependency graph from `ref()` fields
- Uses Kahn's algorithm for topological sort
- Detects circular dependencies

#### Key Methods:

```python
def get_generation_order() -> list[str]:
    """Returns entity names in dependency order for creation"""
    # User → Post → Comment (if Comment refs Post refs User)
    
def get_refresh_order_for_entity(entity_name: str) -> list[str]:
    """Returns entities that must be refreshed when given entity changes"""
    # When User changes: refresh Post, Comment
```

---

## 3. FraiseQL ANNOTATIONS

### `TableViewAnnotator`
**File**: `/home/lionel/code/specql/src/generators/fraiseql/table_view_annotator.py`

Generates SQL COMMENT statements that tell FraiseQL how to introspect `tv_` tables.

#### Annotations:

1. **Table-level**: `@fraiseql:table source=materialized,refresh=explicit,primary=true`
2. **Internal columns**: `pk_*`, `fk_*`, `refreshed_at` marked as `internal=true`
3. **Filter columns**: `tenant_id`, `{entity}_id`, extra columns with index info
4. **Data column**: `@fraiseql:jsonb expand=true` for type extraction

---

## 4. CONFIGURATION MODEL (AST)

### `TableViewConfig`
**File**: `/home/lionel/code/specql/src/core/ast_models.py` (lines 123-147)

```python
@dataclass
class TableViewConfig:
    mode: TableViewMode = AUTO        # auto | force | disable
    include_relations: list[IncludeRelation] = []  # Explicit field selection
    extra_filter_columns: list[ExtraFilterColumn] = []  # Promoted scalars
    refresh: str = "explicit"         # Always explicit for now
```

### Modes:

- **AUTO** (default): Generate tv_ if entity has foreign keys
- **FORCE**: Always generate tv_, even for simple entities
- **DISABLE**: Never generate tv_

### `IncludeRelation`
Explicitly select which fields to include from related entities:

```yaml
table_views:
  include_relations:
    - entity_name: author
      fields: [name, email]  # Only these fields from author
```

### `ExtraFilterColumn`
Promote scalar fields to top-level for filtering:

```yaml
table_views:
  extra_filter_columns:
    - name: rating
      type: INTEGER
      index_type: btree
    - name: search_text
      source: title
      index_type: gin_trgm
```

---

## 5. SCHEMA ORCHESTRATOR INTEGRATION

### `SchemaOrchestrator.generate_table_views()`
**File**: `/home/lionel/code/specql/src/generators/schema_orchestrator.py` (lines 219-258)

Entry point for generating all tv_ tables:

```python
def generate_table_views(self, entities: list[EntityDefinition]) -> str:
    """Generate all tv_ tables in dependency order"""
    
    # 1. Resolve dependencies
    resolver = TableViewDependencyResolver(entities)
    generation_order = resolver.get_generation_order()
    
    # 2. Generate each tv_ in proper order
    for entity_name in generation_order:
        entity = next(e for e in entities if e.name == entity_name)
        generator = TableViewGenerator(entity, all_entities_dict)
        tv_schema = generator.generate_schema()
        
        # 3. Add FraiseQL annotations
        annotator = TableViewAnnotator(entity)
        annotations = annotator.generate_annotations()
    
    return all_sql_combined
```

---

## 6. CLI INTEGRATION

### Command Entry Point: `specql generate`
**File**: `/home/lionel/code/specql/src/cli/generate.py`

Key CLI options:

```bash
--include-tv            # Generate table views (default: false in hierarchical mode)
--no-tv                 # Skip table view generation
--dev                   # Development mode (implies --no-tv, --output-format=confiture)
```

### Orchestrator: `CLIOrchestrator`
**File**: `/home/lionel/code/specql/src/cli/orchestrator.py` (lines 424-437)

```python
def generate_from_files(..., include_tv: bool = False, ...):
    # ... generate entities ...
    
    # Generate tv_ tables if requested
    if include_tv and entity_defs:
        tv_sql = self.schema_orchestrator.generate_table_views(entity_defs)
        if tv_sql:
            migration = MigrationFile(
                number=200,
                name="table_views",
                content=tv_sql,
                path=output_path / "200_table_views.sql",
            )
            result.migrations.append(migration)
```

### Framework Defaults
**File**: `/home/lionel/code/specql/src/cli/framework_defaults.py`

```python
FRAMEWORK_DEFAULTS = {
    "fraiseql": {"include_tv": True},   # GraphQL needs tv_
    "django": {"include_tv": False},     # ORM doesn't use tv_
    "rails": {"include_tv": False},
    "prisma": {"include_tv": False},
}
```

---

## 7. CURRENT FILE OUTPUT STRUCTURE

### Generation Flow:

```
CLIOrchestrator.generate_from_files()
  ├─ Generate foundation (app schema)
  │  └─ "db/schema/00_foundation/000_app_foundation.sql"
  │
  ├─ Generate entities (tables + helpers + mutations)
  │  ├─ "db/schema/10_tables/{entity}.sql"
  │  ├─ "db/schema/20_helpers/{entity}_helpers.sql"
  │  └─ "db/schema/30_functions/{action_name}.sql" (ONE FILE PER MUTATION)
  │
  └─ Generate table views (IF --include-tv)
     └─ "200_table_views.sql" (ALL TV_ TABLES IN ONE FILE)
```

### Key Observations:

1. **Monolithic TV_ File**: All `tv_*` tables go into a single file
   - Simple but doesn't match hierarchical structure
   - No separation by entity

2. **Dependency Order**: Handled internally (topologically sorted)
   - User created before Post created before Comment created

3. **No Registry Codes**: TV_ file doesn't get hexadecimal codes
   - Always numbered as "200"

---

## 8. MISSING PATTERNS IN CURRENT IMPLEMENTATION

### Gaps Identified:

1. **No Per-Entity TV_ Files**
   - All tv_ tables in `200_table_views.sql`
   - Should be: `db/schema/15_table_views/{entity}_tv.sql`

2. **No Hierarchical Organization**
   - TV_ files don't follow domain/subdomain/entity hierarchy
   - No registry integration for TV_ files

3. **No TV_ Registry Codes**
   - TV_ files aren't assigned hexadecimal codes
   - Can't be versioned individually

4. **Refresh Function Location**
   - Mixed with table DDL in same file
   - Should be separate: `db/schema/25_refresh_functions/{entity}_refresh.sql`

5. **No TV_ Metadata Separation**
   - FraiseQL annotations mixed with DDL
   - Should be: `db/schema/40_metadata/{entity}_tv_metadata.sql`

---

## 9. PARSER INTEGRATION

### Table View Configuration Parsing
**File**: `/home/lionel/code/specql/src/core/specql_parser.py`

```python
def _parse_table_views(self, config: dict, entity_name: str) -> TableViewConfig:
    """Parse table_views block from YAML"""
    
def _parse_refresh_table_view_step(self, step_data: dict) -> ActionStep:
    """Parse refresh_table_view step in actions"""
```

### Parser Support:

```yaml
entity: Review
table_views:
  mode: auto | force | disable
  include_relations:
    - entity_name: author
      fields: [name, email]
  extra_filter_columns:
    - name: rating
      type: INTEGER
      index_type: btree

actions:
  - name: create_review
    steps:
      - refresh_table_view: Review
      - refresh_table_view:
          scope: related        # self | related | propagate
          strategy: immediate   # immediate | deferred
```

---

## 10. TESTING

### Unit Tests
**File**: `/home/lionel/code/specql/tests/unit/schema/test_table_view_generation.py`

Covers:
- Basic DDL generation
- Index generation
- Hierarchical entities (LTREE)
- Disabled/forced generation modes
- Extra filter columns
- Multiple foreign keys
- Refresh function generation
- JSONB composition
- Field selection

### Integration Tests
**File**: `/home/lionel/code/specql/tests/integration/fraiseql/test_tv_annotations_e2e.py`

Covers:
- End-to-end annotation generation
- FraiseQL introspection

---

## 11. ENTITY DEFINITION INTEGRATION

### EntityDefinition Model
**File**: `/home/lionel/code/specql/src/core/ast_models.py` (lines 344-365)

```python
@dataclass
class EntityDefinition:
    ...
    table_views: TableViewConfig | None = None
    
    @property
    def should_generate_table_view(self) -> bool:
        """Determine if tv_ should be generated"""
        if self.table_views is None:
            # Auto-generate if has foreign keys
            return any(f.is_reference() for f in self.fields.values())
        
        if self.table_views.mode == TableViewMode.DISABLE:
            return False
        elif self.table_views.mode == TableViewMode.FORCE:
            return True
        else:  # AUTO
            return any(f.is_reference() for f in self.fields.values())
```

---

## 12. DIRECTORY STRUCTURE REFERENCE

```
src/
├── generators/
│   ├── schema/
│   │   ├── table_view_generator.py         # Main DDL + indexes + refresh function
│   │   ├── table_view_dependency.py        # Dependency resolution
│   │   └── ...
│   ├── fraiseql/
│   │   └── table_view_annotator.py         # FraiseQL comments
│   ├── schema_orchestrator.py              # Orchestrates TV_ generation
│   └── ...
├── cli/
│   ├── generate.py                         # CLI command with --include-tv flag
│   ├── orchestrator.py                     # Calls schema_orchestrator.generate_table_views()
│   ├── framework_defaults.py               # Framework-aware defaults
│   └── ...
└── core/
    └── ast_models.py                       # TableViewConfig, IncludeRelation, ExtraFilterColumn

tests/
├── unit/
│   ├── schema/
│   │   └── test_table_view_generation.py   # Comprehensive DDL/index/refresh tests
│   └── fraiseql/
│       └── test_table_view_annotator.py    # Annotation tests
└── integration/
    └── fraiseql/
        └── test_tv_annotations_e2e.py      # E2E annotation tests
```

---

## 13. KEY ENTRY POINTS FOR INTEGRATION

### When Adding File Organization for TV_:

1. **Modify `CLIOrchestrator.generate_from_files()`**
   - Lines 424-437: Change from monolithic file to per-entity files

2. **Extend `SchemaOrchestrator.generate_table_views()`**
   - Return structured output (separate DDL, refresh, metadata)

3. **Update `TableViewGenerator`**
   - Return separate components instead of monolithic string

4. **Modify CLI command**
   - Add option like `--table-views-format` (monolithic | hierarchical | separate)

5. **Registry Integration**
   - Assign hexadecimal codes to TV_ files
   - Create hierarchical paths matching entity hierarchy

---

## 14. EXISTING HIERARCHICAL ORGANIZATION (FOR REFERENCE)

Current implementation for regular entities:

```
db/schema/
├── 00_foundation/
│   └── 000_app_foundation.sql
├── 10_tables/
│   └── {entity}.sql                        # Trinity pattern table
├── 20_helpers/
│   └── {entity}_helpers.sql                # Helper functions
├── 30_functions/
│   └── {action_name}.sql                   # ONE FILE PER MUTATION
└── 40_audit/                               # Optional
    └── {entity}_audit.sql
```

**Proposed for TV_:**

```
db/schema/
├── ...existing...
├── 15_table_views/
│   ├── {entity}_tv.sql                     # CREATE TABLE tv_{entity}
│   └── ...
├── 25_refresh_functions/
│   ├── {entity}_refresh_tv.sql             # refresh_tv_{entity}() function
│   └── ...
└── 40_metadata/
    ├── {entity}_tv_metadata.sql            # @fraiseql:* annotations
    └── ...
```

---

## Summary

SpecQL's view generation is **production-ready and well-architected**, but currently **outputs all tv_ tables into a single monolithic file**. The system is designed to be extensible for per-entity hierarchical organization while maintaining:

- Clean dependency resolution
- CQRS pattern enforcement
- GraphQL/FraiseQL optimization
- Framework-aware defaults
- Comprehensive testing

All components exist to support more granular file organization; the primary change needed is in orchestration logic to write separate files while respecting entity hierarchy and registry codes.

