# GraphQL Cascade Implementation Plan

**Issue**: [#8 - Add GraphQL Cascade Support](https://github.com/fraiseql/specql/issues/8)
**Status**: Planning
**Duration**: 3-5 days
**Approach**: Automatic Always-On Cascade via Existing Impact Metadata

---

## 🎯 Executive Summary

Enhance SpecQL to automatically generate GraphQL Cascade data in `mutation_result.extra_metadata._cascade` by leveraging the existing `ActionImpact` metadata system. This enables FraiseQL to automatically update GraphQL client caches.

### Key Insight

SpecQL already tracks all entity mutations via `ActionImpact`:
- Primary entity (CREATE/UPDATE/DELETE)
- Side effects (secondary entity mutations)
- Cache invalidations

**We can automatically convert this metadata into cascade data at the PostgreSQL level!**

### Flexible Configuration

**Default Behavior**: Automatic cascade generation for all actions with impact metadata

**Override Options**: Configure at application level OR per-mutation level

#### Option 1: Application-Wide Configuration (Recommended)

```yaml
# specql.config.yaml (applies to all entities/actions)
cascade:
  enabled: true              # Default: true
  include_full_entities: true  # Include complete entity data
  include_deleted: true      # Include deleted entities
```

#### Option 2: Per-Mutation Configuration

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
    impact:
      primary:
        entity: Post
        operation: CREATE
        fields: [title, content]

    # Optional: Override cascade behavior for this action
    cascade:
      enabled: true           # Override: enable/disable for this action
      include_entities: [Post, User]  # Only these entities in cascade
      exclude_entities: []    # Exclude specific entities
      include_full_data: true # Include complete entity objects
```

#### Option 3: Minimal (Zero Config)

```yaml
# No cascade configuration needed!
entity: Post
actions:
  - name: create_post
    impact: { ... }
    # ← Cascade automatically generated from impact
```

---

## 🏗️ Architecture

### Current Flow
```
SpecQL YAML → Parser → AST (with ActionImpact)
                ↓
    Action Compiler generates:
    - v_meta (impact metadata)
    - extra_metadata._meta
```

### Enhanced Flow
```
SpecQL YAML → Parser → AST (with ActionImpact)
                ↓
    Action Compiler generates:
    - v_meta (impact metadata)          [EXISTING]
    - v_cascade_entities (from impact)  [NEW]
    - v_cascade_deleted (from impact)   [NEW]
    - extra_metadata._cascade           [NEW]
    - extra_metadata._meta              [EXISTING]
```

### Cascade Data Structure

```typescript
interface CascadeData {
  updated: CascadeEntity[];       // Created or updated entities
  deleted: DeletedEntity[];        // Deleted entity IDs
  invalidations: QueryInvalidation[]; // From cache_invalidations
  metadata: {
    timestamp: string;
    affectedCount: number;
  };
}

interface CascadeEntity {
  __typename: string;   // GraphQL type name
  id: string;          // Entity UUID
  operation: 'CREATED' | 'UPDATED';
  entity: object;      // Full entity data from table view
}

interface DeletedEntity {
  __typename: string;
  id: string;
  operation: 'DELETED';
}
```

---

## 📋 Implementation Phases

---

## PHASE 0: Configuration System (NEW)

**Duration**: 0.5-1 day
**Team**: Core Parser
**Objective**: Add cascade configuration support at application and action levels

### TDD Cycle 0.1: Add CascadeConfig to AST

**🔴 RED - Write Failing Test**

```python
# tests/unit/core/test_cascade_config.py

def test_parse_application_cascade_config():
    """Parse application-wide cascade configuration"""
    yaml_content = """
    cascade:
      enabled: true
      include_full_entities: true
      include_deleted: true

    entity: Post
    """

    config = parse_specql_yaml(yaml_content)
    assert config.cascade.enabled is True
    assert config.cascade.include_full_entities is True


def test_parse_action_cascade_config():
    """Parse per-action cascade configuration"""
    yaml_content = """
    entity: Post
    actions:
      - name: create_post
        impact: { ... }
        cascade:
          enabled: true
          include_entities: [Post, User]
          exclude_entities: []
    """

    entity = parse_specql_yaml(yaml_content)
    action = entity.actions[0]
    assert action.cascade.enabled is True
    assert action.cascade.include_entities == ['Post', 'User']


def test_cascade_defaults_to_enabled():
    """Cascade should be enabled by default if impact exists"""
    yaml_content = """
    entity: Post
    actions:
      - name: create_post
        impact:
          primary: { entity: Post, operation: CREATE }
    """

    entity = parse_specql_yaml(yaml_content)
    action = entity.actions[0]
    # Default: enabled if impact exists
    assert action.should_generate_cascade() is True
```

**🟢 GREEN - Minimal Implementation**

File: `src/core/ast_models.py`

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CascadeConfig:
    """Configuration for GraphQL Cascade generation"""

    # Enable/disable cascade
    enabled: bool = True  # Default: enabled if impact exists

    # Entity filtering
    include_entities: list[str] | None = None  # Whitelist
    exclude_entities: list[str] = field(default_factory=list)  # Blacklist

    # Data inclusion
    include_full_data: bool = True  # Include complete entity objects
    include_deleted: bool = True    # Include deleted entities in cascade

    # Performance
    max_entities: int | None = None  # Limit number of entities in cascade

    def should_include_entity(self, entity_name: str) -> bool:
        """Check if entity should be included in cascade"""
        # Whitelist takes precedence
        if self.include_entities is not None:
            return entity_name in self.include_entities

        # Blacklist
        if entity_name in self.exclude_entities:
            return False

        return True


@dataclass
class ApplicationConfig:
    """Application-wide configuration"""

    cascade: CascadeConfig | None = None
    audit: dict | None = None
    cdc: dict | None = None

    @classmethod
    def default(cls) -> 'ApplicationConfig':
        """Default application configuration"""
        return cls(
            cascade=CascadeConfig(enabled=True),
            audit=None,
            cdc=None
        )


@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: str | None = None
    steps: list[ActionStep] = field(default_factory=list)
    impact: ActionImpact | None = None
    hierarchy_impact: str | None = None

    # Per-action cascade override
    cascade: CascadeConfig | None = None

    def get_effective_cascade_config(
        self,
        app_config: ApplicationConfig | None = None
    ) -> CascadeConfig | None:
        """Get effective cascade config (action overrides app)"""
        # Action-level config takes precedence
        if self.cascade is not None:
            return self.cascade

        # Fall back to application config
        if app_config and app_config.cascade:
            return app_config.cascade

        # Default: enabled if impact exists
        if self.impact:
            return CascadeConfig(enabled=True)

        # No impact = no cascade
        return None

    def should_generate_cascade(
        self,
        app_config: ApplicationConfig | None = None
    ) -> bool:
        """Check if cascade should be generated for this action"""
        config = self.get_effective_cascade_config(app_config)
        return config is not None and config.enabled
```

**🔧 REFACTOR - Update Parser**

File: `src/core/specql_parser.py`

```python
class SpecQLParser:
    def parse(self, yaml_content: str) -> Entity:
        """Parse SpecQL YAML with application config"""
        data = yaml.safe_load(yaml_content)

        # Parse application-wide config
        app_config = self._parse_application_config(data)

        # Parse entity
        entity = self._parse_entity(data, app_config)

        return entity

    def _parse_application_config(self, data: dict) -> ApplicationConfig:
        """Parse application-wide configuration"""
        config = ApplicationConfig.default()

        # Parse cascade config
        if 'cascade' in data:
            cascade_data = data['cascade']
            config.cascade = CascadeConfig(
                enabled=cascade_data.get('enabled', True),
                include_entities=cascade_data.get('include_entities'),
                exclude_entities=cascade_data.get('exclude_entities', []),
                include_full_data=cascade_data.get('include_full_data', True),
                include_deleted=cascade_data.get('include_deleted', True),
                max_entities=cascade_data.get('max_entities')
            )

        # Parse audit config
        if 'audit' in data:
            config.audit = data['audit']

        # Parse CDC config
        if 'cdc' in data:
            config.cdc = data['cdc']

        return config

    def _parse_action(self, action_data: dict, app_config: ApplicationConfig) -> Action:
        """Parse action with cascade config"""
        # ... existing parsing ...

        # Parse action-level cascade override
        cascade_config = None
        if 'cascade' in action_data:
            cascade_data = action_data['cascade']

            # Shorthand: cascade: false
            if isinstance(cascade_data, bool):
                cascade_config = CascadeConfig(enabled=cascade_data)
            # Full config: cascade: { enabled: true, ... }
            else:
                cascade_config = CascadeConfig(
                    enabled=cascade_data.get('enabled', True),
                    include_entities=cascade_data.get('include_entities'),
                    exclude_entities=cascade_data.get('exclude_entities', []),
                    include_full_data=cascade_data.get('include_full_data', True),
                    include_deleted=cascade_data.get('include_deleted', True),
                    max_entities=cascade_data.get('max_entities')
                )

        return Action(
            name=action_data['name'],
            steps=steps,
            impact=impact,
            cascade=cascade_config  # ← NEW
        )
```

**✅ QA - Quality Verification**

```bash
# Unit tests
uv run pytest tests/unit/core/test_cascade_config.py -v

# Test priority: action > app > default
uv run pytest tests/unit/core/test_config_priority.py -v
```

**Acceptance Criteria**:
- [ ] Application-wide cascade config parsed correctly
- [ ] Per-action cascade config parsed correctly
- [ ] Action config overrides application config
- [ ] Default: enabled if impact exists
- [ ] Shorthand syntax works: `cascade: false`
- [ ] Full syntax works: `cascade: { enabled: true, ... }`
- [ ] Entity filtering works (include/exclude)
- [ ] Unit tests pass

---

## PHASE 1: PostgreSQL Helper Functions

**Duration**: 1 day
**Team**: Team B (Schema Generation)
**Objective**: Create PostgreSQL utility functions for building cascade entities

### TDD Cycle 1.1: Generate `app.cascade_entity()` Helper

**🔴 RED - Write Failing Test**

```python
# tests/unit/generators/test_app_schema_cascade.py

def test_app_schema_includes_cascade_entity_helper():
    """AppSchemaGenerator should include cascade_entity() helper function"""
    generator = AppSchemaGenerator()
    sql = generator.generate()

    assert "CREATE OR REPLACE FUNCTION app.cascade_entity" in sql
    assert "p_typename TEXT" in sql
    assert "p_id UUID" in sql
    assert "p_operation TEXT" in sql
    assert "p_schema TEXT" in sql
    assert "p_view_name TEXT" in sql
    assert "RETURNS JSONB" in sql
```

**🟢 GREEN - Minimal Implementation**

File: `src/generators/app_schema_generator.py`

```python
def generate(self) -> str:
    """Generate app schema with mutation_result type and cascade helpers"""
    parts = []

    # Existing: mutation_result type
    parts.append(self._generate_mutation_result_type())

    # NEW: Cascade helper functions
    parts.append(self._generate_cascade_helpers())

    return "\n\n".join(parts)

def _generate_cascade_helpers(self) -> str:
    """Generate cascade helper functions"""
    return """
-- Helper: Build cascade entity with full data from table view
CREATE OR REPLACE FUNCTION app.cascade_entity(
    p_typename TEXT,
    p_id UUID,
    p_operation TEXT,
    p_schema TEXT,
    p_view_name TEXT
) RETURNS JSONB AS $$
DECLARE
    v_entity_data JSONB;
BEGIN
    -- Try to fetch from table view first
    BEGIN
        EXECUTE format('SELECT data FROM %I.%I WHERE id = $1', p_schema, p_view_name)
        INTO v_entity_data
        USING p_id;
    EXCEPTION WHEN undefined_table THEN
        -- Fallback: try table directly
        BEGIN
            EXECUTE format(
                'SELECT row_to_json(t.*)::jsonb FROM %I.tb_%I t WHERE id = $1',
                p_schema,
                lower(p_typename)
            )
            INTO v_entity_data
            USING p_id;
        EXCEPTION WHEN OTHERS THEN
            v_entity_data := NULL;
        END;
    END;

    -- Build cascade entity structure
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', p_operation,
        'entity', COALESCE(v_entity_data, '{}'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;

-- Helper: Build deleted entity (no data, just ID)
CREATE OR REPLACE FUNCTION app.cascade_deleted(
    p_typename TEXT,
    p_id UUID
) RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', 'DELETED'
    );
END;
$$ LANGUAGE plpgsql;
"""
```

**🔧 REFACTOR**

- Extract SQL templates to separate files if needed
- Add comprehensive error handling
- Optimize dynamic SQL execution

**✅ QA - Quality Verification**

```bash
# Unit tests
uv run pytest tests/unit/generators/test_app_schema_cascade.py -v

# Integration test with real PostgreSQL
uv run pytest tests/integration/test_cascade_helpers_e2e.py -v
```

**Integration Test**:

```python
# tests/integration/test_cascade_helpers_e2e.py

def test_cascade_entity_with_table_view(db_connection):
    """Test cascade_entity() with table view"""
    # Setup: Create test entity with table view
    db_connection.execute("""
        CREATE TABLE blog.tb_post (
            pk_post INTEGER PRIMARY KEY,
            id UUID NOT NULL UNIQUE,
            title TEXT
        );

        CREATE VIEW blog.tv_post AS
        SELECT jsonb_build_object(
            'id', id,
            'title', title
        ) as data
        FROM blog.tb_post
        WHERE id = ...;
    """)

    # Insert test data
    post_id = uuid4()
    db_connection.execute(
        "INSERT INTO blog.tb_post (id, title) VALUES ($1, $2)",
        post_id, "Test Post"
    )

    # Test cascade_entity
    result = db_connection.execute("""
        SELECT app.cascade_entity(
            'Post',
            $1::uuid,
            'CREATED',
            'blog',
            'tv_post'
        ) as cascade
    """, post_id)

    cascade = result['cascade']
    assert cascade['__typename'] == 'Post'
    assert cascade['id'] == str(post_id)
    assert cascade['operation'] == 'CREATED'
    assert cascade['entity']['title'] == 'Test Post'
```

**Acceptance Criteria**:
- [ ] `app.cascade_entity()` function generated in app schema
- [ ] `app.cascade_deleted()` function generated in app schema
- [ ] Helper functions work with table views (tv_*)
- [ ] Helper functions fallback to tables (tb_*) if view missing
- [ ] Error handling for missing entities
- [ ] Integration tests pass with real PostgreSQL

---

## PHASE 2: Extend ImpactMetadataCompiler for Cascade

**Duration**: 1-2 days
**Team**: Team C (Action Compilation)
**Objective**: Automatically build cascade arrays from existing `ActionImpact` metadata

### TDD Cycle 2.1: Declare Cascade Variables

**🔴 RED - Write Failing Test**

```python
# tests/unit/actions/test_impact_metadata_cascade.py

def test_compile_declares_cascade_variables():
    """Compiler should declare cascade variables when impact exists"""
    action = Action(
        name="create_post",
        impact=ActionImpact(
            primary=EntityImpact(entity="Post", operation="CREATE")
        ),
        steps=[]
    )
    entity = Entity(name="Post", schema="blog")

    compiler = ImpactMetadataCompiler()
    sql = compiler.compile(action, entity)

    # Should declare cascade arrays
    assert "v_cascade_entities JSONB[]" in sql
    assert "v_cascade_deleted JSONB[]" in sql

    # Should still declare existing metadata
    assert "v_meta mutation_metadata.mutation_impact_metadata" in sql
```

**🟢 GREEN - Minimal Implementation**

File: `src/generators/actions/impact_metadata_compiler.py`

```python
from src.core.ast_models import Action, ActionImpact, EntityImpact, Entity

@dataclass
class ImpactMetadataCompiler:
    """Compiles impact metadata AND cascade data using composite types"""

    def compile(self, action: Action, entity: Entity) -> str:
        """Generate impact metadata + cascade construction"""
        if not action.impact:
            return ""

        impact = action.impact
        parts = []

        # Declare metadata variable (EXISTING)
        parts.append("v_meta mutation_metadata.mutation_impact_metadata;")

        # NEW: Declare cascade variables
        parts.append("v_cascade_entities JSONB[];")
        parts.append("v_cascade_deleted JSONB[];")

        # Primary entity impact (EXISTING)
        parts.append(self.build_primary_impact(impact))

        # Side effects (EXISTING)
        if impact.side_effects:
            parts.append(self.build_side_effects(impact))

        # Cache invalidations (EXISTING)
        if impact.cache_invalidations:
            parts.append(self.build_cache_invalidations(impact))

        return "\n    ".join(parts)
```

**🔧 REFACTOR**: Clean up, add type hints

**✅ QA**: Run unit tests

---

### TDD Cycle 2.2: Build Primary Cascade Entity

**🔴 RED - Write Failing Test**

```python
def test_compile_builds_primary_cascade_entity():
    """Should build cascade entity from primary impact"""
    action = Action(
        name="create_post",
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Post",
                operation="CREATE",
                fields=["title", "content"]
            )
        ),
        steps=[]
    )
    entity = Entity(name="Post", schema="blog")

    compiler = ImpactMetadataCompiler()
    sql = compiler.compile(action, entity)

    # Should call cascade_entity helper
    assert "app.cascade_entity" in sql
    assert "'Post'" in sql
    assert "'CREATE'" in sql or "'CREATED'" in sql
    assert "'blog'" in sql
    assert "'tv_post'" in sql
```

**🟢 GREEN - Implement Primary Cascade**

```python
def compile(self, action: Action, entity: Entity) -> str:
    """Generate impact metadata + cascade construction"""
    if not action.impact:
        return ""

    impact = action.impact
    parts = []

    # Declarations...
    parts.append("v_meta mutation_metadata.mutation_impact_metadata;")
    parts.append("v_cascade_entities JSONB[];")
    parts.append("v_cascade_deleted JSONB[];")

    # Primary entity impact (EXISTING)
    parts.append(self.build_primary_impact(impact))

    # NEW: Build primary cascade entity
    parts.append(self.build_primary_cascade(impact, entity))

    # Side effects...
    if impact.side_effects:
        parts.append(self.build_side_effects(impact))
        # NEW: Build side effects cascade
        parts.append(self.build_side_effects_cascade(impact, entity))

    # Cache invalidations...
    if impact.cache_invalidations:
        parts.append(self.build_cache_invalidations(impact))

    return "\n    ".join(parts)

def build_primary_cascade(self, impact: ActionImpact, entity: Entity) -> str:
    """Build cascade entity for primary impact"""
    typename = impact.primary.entity
    operation = impact.primary.operation
    schema = entity.schema
    view_name = f"tv_{typename.lower()}"

    # Map operation to GraphQL convention
    operation_graphql = self._map_operation(operation)

    # Determine ID variable based on operation
    # For CREATE: v_{entity}_id (captured from INSERT)
    # For UPDATE/DELETE: p_{entity}_id (function parameter)
    if operation == "CREATE":
        id_var = f"v_{typename.lower()}_id"
    else:
        id_var = f"p_{typename.lower()}_id"

    return f"""
    -- Build cascade entity for primary impact
    v_cascade_entities := ARRAY[
        app.cascade_entity(
            '{typename}',
            {id_var},
            '{operation_graphql}',
            '{schema}',
            '{view_name}'
        )
    ];
"""

def _map_operation(self, operation: str) -> str:
    """Map SpecQL operation to GraphQL cascade operation"""
    mapping = {
        "CREATE": "CREATED",
        "UPDATE": "UPDATED",
        "DELETE": "DELETED"
    }
    return mapping.get(operation, operation)
```

**🔧 REFACTOR**: Extract operation mapping, variable naming logic

**✅ QA**: Unit tests

---

### TDD Cycle 2.3: Build Side Effects Cascade

**🔴 RED - Write Failing Test**

```python
def test_compile_builds_side_effects_cascade():
    """Should build cascade entities for side effects"""
    action = Action(
        name="create_post",
        impact=ActionImpact(
            primary=EntityImpact(entity="Post", operation="CREATE"),
            side_effects=[
                EntityImpact(entity="User", operation="UPDATE", fields=["post_count"]),
                EntityImpact(entity="Notification", operation="CREATE")
            ]
        ),
        steps=[]
    )
    entity = Entity(name="Post", schema="blog")

    compiler = ImpactMetadataCompiler()
    sql = compiler.compile(action, entity)

    # Should append to v_cascade_entities
    assert "v_cascade_entities := v_cascade_entities || ARRAY[" in sql

    # Should include User entity
    assert "app.cascade_entity('User'" in sql
    assert "'UPDATED'" in sql

    # Should include Notification entity
    assert "app.cascade_entity('Notification'" in sql
    assert "'CREATED'" in sql
```

**🟢 GREEN - Implement Side Effects Cascade**

```python
def build_side_effects_cascade(self, impact: ActionImpact, entity: Entity) -> str:
    """Build cascade entities for side effects"""
    if not impact.side_effects:
        return ""

    cascade_calls = []

    for effect in impact.side_effects:
        typename = effect.entity
        operation = effect.operation
        schema = entity.schema  # Assume same schema (TODO: support cross-schema)
        view_name = f"tv_{typename.lower()}"
        operation_graphql = self._map_operation(operation)

        # Determine ID variable (convention: v_{entity}_id)
        id_var = f"v_{typename.lower()}_id"

        if operation == "DELETE":
            # Deleted entities don't include full data
            cascade_calls.append(
                f"app.cascade_deleted('{typename}', {id_var})"
            )
        else:
            # Created/Updated entities include full data
            cascade_calls.append(
                f"app.cascade_entity('{typename}', {id_var}, '{operation_graphql}', '{schema}', '{view_name}')"
            )

    if not cascade_calls:
        return ""

    # Append to existing cascade array
    return f"""
    -- Append side effect cascade entities
    v_cascade_entities := v_cascade_entities || ARRAY[
        {(',\n        '.join(cascade_calls))}
    ];
"""
```

**🔧 REFACTOR**: Extract common logic, handle cross-schema references

**✅ QA**: Unit tests with various side effect combinations

---

### TDD Cycle 2.4: Integrate Cascade into `extra_metadata`

**🔴 RED - Write Failing Test**

```python
def test_extra_metadata_includes_cascade_automatically():
    """extra_metadata should include _cascade when impact exists"""
    action = Action(
        name="create_post",
        impact=ActionImpact(
            primary=EntityImpact(entity="Post", operation="CREATE")
        ),
        steps=[]
    )

    compiler = ImpactMetadataCompiler()
    metadata_sql = compiler.integrate_into_result(action)

    # Should include _cascade
    assert "'_cascade'" in metadata_sql
    assert "v_cascade_entities" in metadata_sql
    assert "v_cascade_deleted" in metadata_sql

    # Should include timestamp and affectedCount
    assert "'timestamp'" in metadata_sql
    assert "'affectedCount'" in metadata_sql

    # Should still include _meta (backward compatibility)
    assert "'_meta'" in metadata_sql
    assert "to_jsonb(v_meta)" in metadata_sql
```

**🟢 GREEN - Implement Cascade Integration**

```python
def integrate_into_result(self, action: Action) -> str:
    """Integrate metadata AND cascade into mutation_result.extra_metadata"""
    if not action.impact:
        return "v_result.extra_metadata := '{}'::jsonb;"

    parts = []

    # NEW: Add _cascade structure
    parts.append("""'_cascade', jsonb_build_object(
            'updated', COALESCE(
                (SELECT jsonb_agg(e) FROM unnest(v_cascade_entities) e),
                '[]'::jsonb
            ),
            'deleted', COALESCE(
                (SELECT jsonb_agg(e) FROM unnest(v_cascade_deleted) e),
                '[]'::jsonb
            ),
            'invalidations', COALESCE(to_jsonb(v_meta.cache_invalidations), '[]'::jsonb),
            'metadata', jsonb_build_object(
                'timestamp', now(),
                'affectedCount', COALESCE(array_length(v_cascade_entities, 1), 0) +
                                 COALESCE(array_length(v_cascade_deleted, 1), 0)
            )
        )""")

    # EXISTING: Side effect collections (e.g., createdNotifications)
    for effect in action.impact.side_effects:
        if effect.collection:
            parts.append(f"'{effect.collection}', {self._build_collection_query(effect)}")

    # EXISTING: Add _meta
    parts.append("'_meta', to_jsonb(v_meta)")

    separator = ",\n        "
    return f"""
    v_result.extra_metadata := jsonb_build_object(
        {separator.join(parts)}
    );
"""
```

**🔧 REFACTOR**: Extract cascade structure building to separate method

**✅ QA**: Test final JSON structure matches FraiseQL expectations

---

### Phase 2 Acceptance Criteria

- [ ] Cascade variables declared when impact exists
- [ ] Primary entity converted to cascade format
- [ ] Side effects converted to cascade format
- [ ] DELETE operations use `cascade_deleted()`
- [ ] `_cascade` structure added to `extra_metadata`
- [ ] Backward compatibility: `_meta` still included
- [ ] Unit tests pass (90%+ coverage)
- [ ] SQL syntax is valid PostgreSQL

---

## PHASE 3: Verify Step Compilers Track Entity IDs

**Duration**: 1 day
**Team**: Team C (Action Compilation)
**Objective**: Ensure all step compilers properly capture entity IDs for cascade tracking

### TDD Cycle 3.1: Verify INSERT Step Captures ID

**🔴 RED - Write Test**

```python
# tests/unit/actions/test_insert_step_cascade.py

def test_insert_step_captures_entity_id():
    """INSERT step should capture RETURNING id INTO v_{entity}_id"""
    step = ActionStep(
        type="insert",
        entity="Post",
        fields={"title": "Test", "content": "Hello"}
    )

    context = ActionContext(
        entity_name="Post",
        entity_schema="blog",
        function_name="create_post"
    )

    compiler = InsertStepCompiler()
    sql = compiler.compile(step, context)

    # Should capture ID
    assert "RETURNING id INTO v_post_id" in sql or "v_post_id uuid" in sql
```

**🟢 GREEN - Verify or Implement**

Check `src/generators/actions/step_compilers/insert_step.py`:

```python
def compile(self, step: ActionStep, context: ActionContext) -> str:
    """Compile INSERT step"""
    entity_name = step.entity
    id_var = f"v_{entity_name.lower()}_id"

    # Build INSERT statement
    sql = f"""
    -- Insert {entity_name}
    INSERT INTO {context.entity_schema}.tb_{entity_name.lower()} (
        {', '.join(fields)}
    )
    VALUES (
        {', '.join(values)}
    )
    RETURNING id INTO {id_var};  -- ← Captures ID for cascade
"""
    return sql
```

**🔧 REFACTOR**: Ensure consistent variable naming

**✅ QA**: Unit tests

---

### TDD Cycle 3.2: Verify UPDATE Step Uses Correct ID

**🔴 RED - Write Test**

```python
def test_update_step_uses_parameter_id():
    """UPDATE step should use p_{entity}_id parameter"""
    step = ActionStep(
        type="update",
        entity="Post",
        fields={"status": "published"},
        where_clause="id = p_post_id"
    )

    context = ActionContext(
        entity_name="Post",
        entity_schema="blog",
        function_name="publish_post"
    )

    compiler = UpdateStepCompiler()
    sql = compiler.compile(step, context)

    # Should reference p_post_id
    assert "p_post_id" in sql or "p_id" in sql
```

**🟢 GREEN - Verify**

Check that UPDATE steps properly use function parameters.

**🔧 REFACTOR**: N/A

**✅ QA**: Unit tests

---

### TDD Cycle 3.3: Handle Multi-Step Actions

**🔴 RED - Write Test**

```python
def test_multi_step_action_tracks_all_entities():
    """Multi-step action should track IDs for all affected entities"""
    action = Action(
        name="create_post_with_notification",
        steps=[
            ActionStep(type="insert", entity="Post"),
            ActionStep(type="insert", entity="Notification")
        ],
        impact=ActionImpact(
            primary=EntityImpact(entity="Post", operation="CREATE"),
            side_effects=[
                EntityImpact(entity="Notification", operation="CREATE")
            ]
        )
    )

    # Should declare both IDs
    # Should track both in cascade
    pass
```

**🟢 GREEN - Verify**

Ensure multi-step actions properly track all entity IDs.

**🔧 REFACTOR**: N/A

**✅ QA**: Integration test

---

### Phase 3 Acceptance Criteria

- [ ] INSERT steps capture `v_{entity}_id`
- [ ] UPDATE steps use `p_{entity}_id` parameter
- [ ] DELETE steps track deleted entity IDs
- [ ] Multi-step actions track all entity IDs
- [ ] Variable naming is consistent
- [ ] Unit tests pass

---

## PHASE 4: End-to-End Integration Testing

**Duration**: 1 day
**Team**: Team E (CLI & Integration)
**Objective**: Verify complete flow works end-to-end with real PostgreSQL

### TDD Cycle 4.1: Complete E2E Test

**🔴 RED - Write E2E Test**

```python
# tests/integration/test_automatic_cascade_e2e.py

def test_automatic_cascade_generation_e2e(db_connection):
    """
    Complete flow test:
    1. Parse YAML with impact metadata
    2. Generate SQL with automatic cascade
    3. Execute in PostgreSQL
    4. Call mutation function
    5. Verify cascade data in mutation_result
    """
    yaml_content = """
entity: Post
schema: blog
table_views:
  mode: force
  include_relations:
    - entity: User
      fields: [name, email]

fields:
  title: text
  content: text
  author: ref(User)

actions:
  - name: create_post
    steps:
      - insert: Post

    impact:
      primary:
        entity: Post
        operation: CREATE
        fields: [id, title, content, author, created_at]
"""

    # Parse and generate
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_all(entity)

    # Execute SQL in test database
    db_connection.execute(sql)

    # Create test user
    user_id = uuid4()
    db_connection.execute("""
        INSERT INTO blog.tb_user (id, name, email)
        VALUES ($1, 'Test User', 'test@example.com')
    """, user_id)

    # Execute mutation
    result = db_connection.execute("""
        SELECT blog.fn_create_post($1::jsonb) as result
    """, {
        'title': 'Test Post',
        'content': 'Hello World',
        'author_id': str(user_id)
    })

    mutation_result = result['result']
    extra_metadata = mutation_result['extra_metadata']

    # Verify cascade structure exists
    assert '_cascade' in extra_metadata, "Missing _cascade in extra_metadata"

    cascade = extra_metadata['_cascade']
    assert 'updated' in cascade
    assert 'deleted' in cascade
    assert 'invalidations' in cascade
    assert 'metadata' in cascade

    # Verify primary entity in updated array
    updated = cascade['updated']
    assert len(updated) >= 1, "Should have at least primary entity"

    primary_entity = updated[0]
    assert primary_entity['__typename'] == 'Post'
    assert primary_entity['operation'] == 'CREATED'
    assert 'entity' in primary_entity
    assert primary_entity['entity']['title'] == 'Test Post'
    assert primary_entity['entity']['content'] == 'Hello World'

    # Verify metadata
    assert cascade['metadata']['affectedCount'] >= 1
    assert 'timestamp' in cascade['metadata']

    # Verify backward compatibility: _meta still exists
    assert '_meta' in extra_metadata
    assert extra_metadata['_meta']['primary_entity']['entity_type'] == 'Post'
```

**🟢 GREEN - Fix Integration Issues**

Run the test and fix any issues that arise:
- SQL syntax errors
- Missing variables
- Type mismatches
- View access errors

**🔧 REFACTOR**

- Performance optimization
- Error handling
- Edge case handling

**✅ QA - Full Test Suite**

```bash
# Run all tests
uv run pytest tests/ -v

# Specific integration tests
uv run pytest tests/integration/test_automatic_cascade_e2e.py -v

# Performance benchmark
uv run pytest tests/integration/test_cascade_performance.py -v
```

---

### TDD Cycle 4.2: Test with Side Effects

**🔴 RED - Write Test**

```python
def test_cascade_with_side_effects(db_connection):
    """Test cascade includes side effect entities"""
    yaml_content = """
entity: Post
schema: blog
actions:
  - name: create_post_with_notification
    steps:
      - insert: Post
      - insert: Notification

    impact:
      primary:
        entity: Post
        operation: CREATE
      side_effects:
        - entity: Notification
          operation: CREATE
        - entity: User
          operation: UPDATE
          fields: [post_count]
"""

    # ... generate and execute ...

    result = db_connection.execute("SELECT blog.fn_create_post_with_notification(...)")
    cascade = result['result']['extra_metadata']['_cascade']

    # Should have multiple entities in updated array
    assert len(cascade['updated']) >= 2

    # Verify side effect entities
    entity_types = [e['__typename'] for e in cascade['updated']]
    assert 'Post' in entity_types
    assert 'Notification' in entity_types
    assert 'User' in entity_types
```

**🟢 GREEN - Fix Issues**

**🔧 REFACTOR**: N/A

**✅ QA**: Integration test

---

### TDD Cycle 4.3: Backward Compatibility Test

**🔴 RED - Write Test**

```python
def test_actions_without_impact_still_work(db_connection):
    """Actions without impact metadata should work (no cascade)"""
    yaml_content = """
entity: Post
actions:
  - name: simple_action
    steps:
      - insert: Post
    # No impact metadata
"""

    # ... generate and execute ...

    result = db_connection.execute("SELECT blog.fn_simple_action(...)")

    # Should work without errors
    assert result['result']['status'] == 'success'

    # extra_metadata should be empty or minimal
    extra_metadata = result['result']['extra_metadata']
    # Should not crash, either empty or no _cascade
    assert '_cascade' not in extra_metadata or extra_metadata['_cascade'] is None
```

**🟢 GREEN - Fix Issues**

**🔧 REFACTOR**: Ensure graceful handling of missing impact

**✅ QA**: Backward compatibility tests

---

### Phase 4 Acceptance Criteria

- [ ] E2E test passes with real PostgreSQL
- [ ] Cascade data structure matches FraiseQL expectations
- [ ] Primary entity included in cascade
- [ ] Side effects included in cascade
- [ ] DELETE operations tracked properly
- [ ] Backward compatible with actions without impact
- [ ] Performance is acceptable (< 10ms overhead)
- [ ] All tests pass (unit + integration)

---

## PHASE 5: Documentation & Examples

**Duration**: 0.5 days
**Team**: Team D (FraiseQL Integration)
**Objective**: Document automatic cascade feature

### Tasks

#### 5.1: Feature Documentation

Create `docs/features/AUTOMATIC_GRAPHQL_CASCADE.md`:

```markdown
# Automatic GraphQL Cascade Support

## Overview

SpecQL automatically generates GraphQL Cascade data for all actions with impact metadata.
This enables FraiseQL to automatically update GraphQL client caches without manual configuration.

## How It Works

When you define an action with impact metadata:

```yaml
entity: Post
actions:
  - name: create_post
    steps:
      - insert: Post
    impact:
      primary:
        entity: Post
        operation: CREATE
        fields: [title, content]
```

SpecQL automatically generates SQL that includes cascade data in `mutation_result.extra_metadata._cascade`.

## Generated Structure

```json
{
  "extra_metadata": {
    "_cascade": {
      "updated": [
        {
          "__typename": "Post",
          "id": "123e4567-...",
          "operation": "CREATED",
          "entity": { ... full post data ... }
        }
      ],
      "deleted": [],
      "invalidations": [],
      "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "affectedCount": 1
      }
    },
    "_meta": { ... impact metadata ... }
  }
}
```

## Benefits

- **Zero Configuration**: Works automatically for all actions with impact metadata
- **Always Consistent**: Can't forget to enable cascade
- **Type-Safe**: Uses PostgreSQL composite types
- **Performance**: Native PostgreSQL operations
- **FraiseQL Integration**: Perfect for GraphQL cache updates

## Examples

See `examples/cascade_*.yaml` for complete examples.
```

#### 5.2: Update Examples

Create `examples/cascade_basic.yaml`:

```yaml
entity: Post
schema: blog
table_views:
  mode: force

fields:
  title: text
  content: text
  author: ref(User)

actions:
  - name: create_post
    steps:
      - insert: Post

    impact:
      primary:
        entity: Post
        operation: CREATE
        fields: [id, title, content, author, created_at]
```

Create `examples/cascade_with_side_effects.yaml`:

```yaml
entity: Post
schema: blog

actions:
  - name: create_post_with_notification
    steps:
      - insert: Post
      - insert: Notification
      - update: User SET post_count = post_count + 1

    impact:
      primary:
        entity: Post
        operation: CREATE
      side_effects:
        - entity: Notification
          operation: CREATE
        - entity: User
          operation: UPDATE
          fields: [post_count]
```

#### 5.3: Update README

Add to `README.md`:

```markdown
## 🚀 GraphQL Cascade Support

SpecQL automatically generates GraphQL Cascade data for FraiseQL integration,
enabling automatic GraphQL client cache updates.

**Zero configuration required!** Just define impact metadata in your actions:

```yaml
actions:
  - name: create_post
    impact:
      primary:
        entity: Post
        operation: CREATE
```

SpecQL automatically includes cascade data in `mutation_result.extra_metadata._cascade`.

See [Automatic GraphQL Cascade](docs/features/AUTOMATIC_GRAPHQL_CASCADE.md) for details.
```

#### 5.4: CHANGELOG Entry

Add to `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added

- **Automatic GraphQL Cascade Support**: SpecQL now automatically generates cascade data
  in `mutation_result.extra_metadata._cascade` for all actions with impact metadata.
  This enables FraiseQL to automatically update GraphQL client caches.
  - Zero configuration required
  - Works with all existing actions that have impact metadata
  - Includes primary entity and all side effects
  - Backward compatible
  - PostgreSQL helper functions: `app.cascade_entity()`, `app.cascade_deleted()`
```

### Phase 5 Acceptance Criteria

- [ ] Feature documentation complete
- [ ] Examples created and tested
- [ ] README updated
- [ ] CHANGELOG entry added
- [ ] Documentation is clear and accurate

---

## 📊 Overall Acceptance Criteria

### Functional Requirements
- [ ] Cascade data automatically generated for actions with impact metadata
- [ ] Primary entity included in cascade
- [ ] Side effects included in cascade
- [ ] DELETE operations handled correctly
- [ ] Cascade structure matches FraiseQL expectations
- [ ] Backward compatible with existing actions

### Technical Requirements
- [ ] PostgreSQL helper functions generated
- [ ] Type-safe implementation using composite types
- [ ] No performance degradation (< 10ms overhead)
- [ ] SQL syntax valid and optimized
- [ ] Error handling for edge cases

### Testing Requirements
- [ ] Unit tests: 90%+ coverage for new code
- [ ] Integration tests with real PostgreSQL
- [ ] E2E tests for complete flow
- [ ] Backward compatibility tests
- [ ] Performance benchmarks

### Documentation Requirements
- [ ] Feature documentation complete
- [ ] Examples provided
- [ ] README updated
- [ ] CHANGELOG entry
- [ ] Code comments for complex logic

---

## 🚀 Rollout Timeline

### Day 1: Phase 1
- Morning: Helper functions implementation
- Afternoon: Integration into AppSchemaGenerator
- Evening: Integration tests

### Day 2-3: Phase 2
- Day 2 Morning: Declare cascade variables
- Day 2 Afternoon: Build primary cascade
- Day 3 Morning: Build side effects cascade
- Day 3 Afternoon: Integrate into extra_metadata

### Day 4: Phase 3
- Morning: Verify INSERT step tracking
- Afternoon: Verify UPDATE/DELETE steps
- Evening: Multi-step action tests

### Day 4-5: Phase 4
- Day 4 Evening: Start E2E tests
- Day 5 Morning: Side effects tests
- Day 5 Afternoon: Backward compatibility tests

### Day 5: Phase 5
- Afternoon: Documentation
- Evening: Examples and CHANGELOG

**Total: 3-5 days**

---

## 🎯 Success Metrics

- ✅ All tests pass (unit + integration)
- ✅ Zero breaking changes to existing code
- ✅ Performance overhead < 10ms per mutation
- ✅ 90%+ test coverage for new code
- ✅ Documentation complete and clear
- ✅ FraiseQL integration verified

---

## 📚 Related Files

### Files to Create
- `tests/unit/generators/test_app_schema_cascade.py`
- `tests/integration/test_cascade_helpers_e2e.py`
- `tests/unit/actions/test_impact_metadata_cascade.py`
- `tests/integration/test_automatic_cascade_e2e.py`
- `docs/features/AUTOMATIC_GRAPHQL_CASCADE.md`
- `examples/cascade_basic.yaml`
- `examples/cascade_with_side_effects.yaml`

### Files to Modify
- `src/generators/app_schema_generator.py` - Add cascade helper functions
- `src/generators/actions/impact_metadata_compiler.py` - Build cascade arrays
- `src/generators/actions/step_compilers/insert_step.py` - Verify ID capture (if needed)
- `README.md` - Add cascade feature mention
- `CHANGELOG.md` - Add feature entry

---

**Status**: Ready for Implementation
**Next Step**: Begin Phase 1 - PostgreSQL Helper Functions
