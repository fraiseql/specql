# Implementation Plan: Phases 2 & 3 - Cascade + Audit Trail + CDC

**Scope**: Detailed implementation plan for integrating GraphQL Cascade with existing Audit Trail (Phase 2) and CDC Outbox Pattern (Phase 3)

**Prerequisites**: Phase 1 (Cascade Generation) completed per `GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`

**Status**: Planning / Design

---

## 📋 Table of Contents

- [Phase 1 Recap](#phase-1-recap-what-we-already-have)
- [Phase 2: Cascade + Audit Trail Integration](#phase-2-cascade--audit-trail-integration)
- [Phase 3: CDC Outbox Pattern](#phase-3-cdc-outbox-pattern)
- [Testing Strategy](#testing-strategy)
- [Rollout Plan](#rollout-plan)

---

## Phase 1 Recap: What We Already Have

### ✅ Completed (Phase 1 - Issue #8)

**From**: `GRAPHQL_CASCADE_IMPLEMENTATION_PLAN.md`

1. **PostgreSQL Helper Functions**
   - `app.cascade_entity(typename, id, operation, schema, view_name)`
   - `app.cascade_deleted(typename, id)`

2. **ImpactMetadataCompiler Enhanced**
   - Declares `v_cascade_entities JSONB[]` and `v_cascade_deleted JSONB[]`
   - Builds cascade from `ActionImpact.primary`
   - Builds cascade from `ActionImpact.side_effects`
   - Integrates `_cascade` into `extra_metadata`

3. **Cascade Structure in mutation_result**
   ```json
   {
     "extra_metadata": {
       "_cascade": {
         "updated": [
           { "__typename": "Post", "id": "...", "operation": "CREATED", "entity": {...} }
         ],
         "deleted": [],
         "invalidations": [],
         "metadata": { "timestamp": "...", "affectedCount": 1 }
       },
       "_meta": { ... }
     }
   }
   ```

### ✅ Already Exists (Pre-Phase 1)

**From**: `src/generators/enterprise/audit_generator.py` and `src/patterns/temporal/`

1. **Audit Infrastructure**
   - `AuditGenerator` class - Enterprise audit trail generator
   - `AuditTrailGenerator` class - Temporal audit pattern
   - Audit tables: `app.audit_{entity}`
   - Audit triggers: Capture INSERT/UPDATE/DELETE
   - Audit query functions: `app.get_{entity}_audit_history()`

2. **Audit Table Structure**
   ```sql
   CREATE TABLE app.audit_{entity} (
       audit_id UUID PRIMARY KEY,
       entity_id UUID NOT NULL,
       tenant_id UUID NOT NULL,
       operation_type TEXT CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
       changed_by UUID,
       changed_at TIMESTAMPTZ DEFAULT NOW(),
       old_values JSONB,
       new_values JSONB,
       change_reason TEXT,
       transaction_id BIGINT,
       application_name TEXT,
       client_addr INET
   );
   ```

3. **Audit Fields on Entities**
   - `created_at`, `created_by`
   - `updated_at`, `updated_by`
   - `deleted_at`, `deleted_by`
   - `identifier_recalculated_at`, `identifier_recalculated_by`

---

## PHASE 2: Cascade + Audit Trail Integration

**Duration**: 2-3 days
**Objective**: Store cascade data in existing audit trail for complete mutation history and replay capability

**Value Proposition**:
- Complete audit trail showing all entities affected by each mutation
- Mutation replay with full cascade context
- Compliance: "What else changed when X was modified?"
- Debugging: Trace side effects back to source mutation

---

### Design Decision: Storage Strategy

We'll implement **Option A + Option B** for maximum flexibility:

| Approach | Use Case | Migration Needed |
|----------|----------|------------------|
| **Option A**: New `cascade_data` column | Production audit trail with full cascade context | ✅ Yes (ALTER TABLE) |
| **Option B**: Store in existing JSONB | Quick integration, testing, backward compatibility | ❌ No |

**Recommendation**: Start with Option B (zero migration), migrate to Option A when proven valuable.

---

### TDD CYCLE 2.1: Extend Audit Table Schema (Option A)

**🔴 RED - Write Failing Test**

```python
# tests/unit/generators/test_audit_cascade_schema.py

def test_audit_generator_includes_cascade_column():
    """Audit tables should include cascade_data column"""
    from src.generators.enterprise.audit_generator import AuditGenerator

    generator = AuditGenerator()
    sql = generator.generate_audit_trail(
        entity_name="Post",
        fields=["title", "content"],
        audit_config={"enabled": True, "include_cascade": True}
    )

    # Should include cascade_data column
    assert "cascade_data JSONB" in sql

    # Should include cascade_entities array for quick filtering
    assert "cascade_entities TEXT[]" in sql

    # Should include index on cascade_entities
    assert "idx_audit_post_cascade_entities" in sql or "CASCADE_ENTITIES" in sql
```

**🟢 GREEN - Minimal Implementation**

File: `src/generators/enterprise/audit_generator.py`

```python
def generate_audit_trail(
    self, entity_name: str, fields: List[str], audit_config: Dict[str, Any]
) -> str:
    """Generate audit trail functionality for an entity"""
    audit_table_name = f"audit_{entity_name.lower()}"
    trigger_name = f"audit_trigger_{entity_name.lower()}"

    # Check if cascade integration is enabled
    include_cascade = audit_config.get("include_cascade", False)

    sql_parts = []

    # Create audit table (EXISTING + NEW cascade columns)
    cascade_columns = ""
    if include_cascade:
        cascade_columns = """,
    cascade_data JSONB,
    cascade_entities TEXT[]  -- Quick filter: which entities were affected?"""

    sql_parts.append(f"""
-- Audit table for {entity_name}
CREATE TABLE IF NOT EXISTS app.{audit_table_name} (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    transaction_id BIGINT,
    application_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(){cascade_columns}
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_entity_id ON app.{audit_table_name}(entity_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_tenant_id ON app.{audit_table_name}(tenant_id);
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_changed_at ON app.{audit_table_name}(changed_at);
""")

    if include_cascade:
        sql_parts.append(f"""
-- Cascade-specific indexes
CREATE INDEX IF NOT EXISTS idx_{audit_table_name}_cascade_entities
    ON app.{audit_table_name} USING GIN (cascade_entities);
""")

    # ... rest of existing code ...

    return "\n".join(sql_parts)
```

**🔧 REFACTOR**

- Extract cascade column generation to separate method
- Add configuration validation
- Support cascade column migration for existing tables

```python
def _generate_cascade_columns(self, include_cascade: bool) -> str:
    """Generate cascade-related columns"""
    if not include_cascade:
        return ""

    return """,
    -- GraphQL Cascade Integration
    cascade_data JSONB,
    cascade_entities TEXT[],  -- ['Post', 'User', etc.]
    cascade_timestamp TIMESTAMPTZ,
    cascade_source TEXT  -- Mutation name that generated this cascade"""

def generate_cascade_migration(self, entity_name: str) -> str:
    """Generate migration to add cascade columns to existing audit table"""
    audit_table_name = f"audit_{entity_name.lower()}"

    return f"""
-- Migration: Add cascade columns to existing audit table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'app'
        AND table_name = '{audit_table_name}'
        AND column_name = 'cascade_data'
    ) THEN
        ALTER TABLE app.{audit_table_name}
        ADD COLUMN cascade_data JSONB,
        ADD COLUMN cascade_entities TEXT[],
        ADD COLUMN cascade_timestamp TIMESTAMPTZ,
        ADD COLUMN cascade_source TEXT;

        CREATE INDEX idx_{audit_table_name}_cascade_entities
            ON app.{audit_table_name} USING GIN (cascade_entities);
    END IF;
END $$;
"""
```

**✅ QA - Quality Verification**

```bash
# Unit tests
uv run pytest tests/unit/generators/test_audit_cascade_schema.py -v

# Integration test: Create audit table with cascade columns
uv run pytest tests/integration/test_audit_cascade_schema_e2e.py -v
```

**Integration Test**:

```python
# tests/integration/test_audit_cascade_schema_e2e.py

def test_audit_table_with_cascade_columns(db_connection):
    """Test audit table creation with cascade columns"""
    from src.generators.enterprise.audit_generator import AuditGenerator

    generator = AuditGenerator()
    sql = generator.generate_audit_trail(
        entity_name="Post",
        fields=["title", "content"],
        audit_config={"enabled": True, "include_cascade": True}
    )

    # Execute SQL
    db_connection.execute(sql)

    # Verify table structure
    columns = db_connection.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'audit_post' AND table_schema = 'app'
    """)

    column_names = [col['column_name'] for col in columns]
    assert 'cascade_data' in column_names
    assert 'cascade_entities' in column_names

    # Verify GIN index exists
    indexes = db_connection.execute("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'audit_post' AND schemaname = 'app'
    """)

    index_names = [idx['indexname'] for idx in indexes]
    assert any('cascade_entities' in idx for idx in index_names)
```

**Acceptance Criteria**:
- [ ] Audit tables include `cascade_data JSONB` column when configured
- [ ] Audit tables include `cascade_entities TEXT[]` for filtering
- [ ] GIN index created on `cascade_entities` for performance
- [ ] Migration script generated for existing audit tables
- [ ] Unit tests pass
- [ ] Integration tests pass with real PostgreSQL

---

### TDD CYCLE 2.2: Store Cascade in Audit Triggers

**🔴 RED - Write Failing Test**

```python
# tests/unit/generators/test_audit_cascade_triggers.py

def test_audit_trigger_captures_cascade_data():
    """Audit triggers should capture cascade data from action context"""
    from src.generators.enterprise.audit_generator import AuditGenerator

    generator = AuditGenerator()
    sql = generator.generate_audit_trigger_with_cascade(
        entity_name="Post",
        audit_config={"include_cascade": True}
    )

    # Should reference cascade data from session variable
    assert "current_setting('app.cascade_data')" in sql or "CASCADE_DATA" in sql

    # Should extract cascade_entities array
    assert "cascade_entities" in sql

    # Should store cascade_source (mutation name)
    assert "cascade_source" in sql
```

**🟢 GREEN - Implement Cascade Capture in Triggers**

The challenge: Triggers fire at row level, but cascade data is at mutation level.

**Solution**: Use PostgreSQL session variables to pass cascade data from action function to trigger.

File: `src/generators/enterprise/audit_generator.py`

```python
def generate_audit_trigger(self, entity: Dict, audit_config: Dict) -> str:
    """Generate audit trigger function with optional cascade capture"""
    entity_name = entity.get("name", "Entity")
    audit_table_name = f"audit_{entity_name.lower()}"
    trigger_name = f"audit_trigger_{entity_name.lower()}"
    include_cascade = audit_config.get("include_cascade", False)

    # Build cascade capture logic
    cascade_capture = ""
    if include_cascade:
        cascade_capture = """,
        cascade_data = NULLIF(current_setting('app.cascade_data', true), '')::jsonb,
        cascade_entities = NULLIF(current_setting('app.cascade_entities', true), '')::text[],
        cascade_timestamp = now(),
        cascade_source = NULLIF(current_setting('app.cascade_source', true), '')"""

    sql_parts.append(f"""
-- Audit trigger function for {entity_name}
CREATE OR REPLACE FUNCTION app.{trigger_name}()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert audit record
    INSERT INTO app.{audit_table_name} (
        entity_id,
        tenant_id,
        operation_type,
        changed_by,
        old_values,
        new_values,
        change_reason,
        transaction_id,
        application_name{', cascade_data, cascade_entities, cascade_timestamp, cascade_source' if include_cascade else ''}
    ) VALUES (
        COALESCE(NEW.id, OLD.id),
        COALESCE(NEW.tenant_id, OLD.tenant_id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.updated_by ELSE NEW.updated_by END,
        CASE WHEN TG_OP != 'INSERT' THEN row_to_json(OLD)::JSONB ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN row_to_json(NEW)::JSONB ELSE NULL END,
        CASE WHEN TG_OP = 'DELETE' THEN 'Entity deleted' ELSE 'Entity modified' END,
        txid_current(),
        current_setting('application_name', true){cascade_capture}
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger
DROP TRIGGER IF EXISTS {trigger_name} ON {{{{ entity.schema }}}}.tb_{entity_name.lower()};
CREATE TRIGGER {trigger_name}
    AFTER INSERT OR UPDATE OR DELETE ON {{{{ entity.schema }}}}.tb_{entity_name.lower()}
    FOR EACH ROW EXECUTE FUNCTION app.{trigger_name}();
""")

    return "\n".join(sql_parts)
```

**🔧 REFACTOR - Update ImpactMetadataCompiler to Set Session Variables**

File: `src/generators/actions/impact_metadata_compiler.py`

```python
def integrate_into_result(self, action: Action) -> str:
    """Integrate metadata AND cascade into mutation_result.extra_metadata"""
    if not action.impact:
        return "v_result.extra_metadata := '{}'::jsonb;"

    parts = []

    # NEW: Set session variables for audit triggers
    parts.append("""
    -- Set cascade data in session for audit triggers
    PERFORM set_config('app.cascade_data', v_cascade_data::text, true);
    PERFORM set_config('app.cascade_entities',
        array_to_string(
            ARRAY(SELECT jsonb_array_elements_text(
                v_cascade_data->'updated')->>'__typename'
            ),
            ','
        ),
        true
    );
    PERFORM set_config('app.cascade_source', '{action.name}', true);
""")

    # Build _cascade structure (EXISTING)
    parts.append("""
    v_result.extra_metadata := jsonb_build_object(
        '_cascade', v_cascade_data,
        '_meta', to_jsonb(v_meta)
    );
""")

    # NEW: Clear session variables after mutation
    parts.append("""
    -- Clear cascade session variables
    PERFORM set_config('app.cascade_data', NULL, true);
    PERFORM set_config('app.cascade_entities', NULL, true);
    PERFORM set_config('app.cascade_source', NULL, true);
""")

    return "\n    ".join(parts)
```

**✅ QA - Integration Test**

```python
# tests/integration/test_audit_cascade_capture.py

def test_audit_captures_cascade_data(db_connection):
    """Test that audit triggers capture cascade data from mutations"""

    # Setup: Create Post entity with audit trail + cascade
    setup_sql = """
        -- Create tables
        CREATE TABLE blog.tb_post (
            pk_post INTEGER PRIMARY KEY,
            id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
            title TEXT,
            tenant_id UUID NOT NULL
        );

        CREATE TABLE blog.tb_user (
            pk_user INTEGER PRIMARY KEY,
            id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
            post_count INTEGER DEFAULT 0,
            tenant_id UUID NOT NULL
        );

        -- Create audit tables with cascade
        -- (generated by AuditGenerator with include_cascade=True)
        CREATE TABLE app.audit_post (
            audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            operation_type TEXT,
            new_values JSONB,
            cascade_data JSONB,
            cascade_entities TEXT[],
            cascade_source TEXT
        );

        -- Create audit trigger
        -- (generated trigger with cascade capture)
        CREATE OR REPLACE FUNCTION app.audit_trigger_post()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO app.audit_post (
                entity_id, tenant_id, operation_type, new_values,
                cascade_data, cascade_entities, cascade_source
            ) VALUES (
                NEW.id, NEW.tenant_id, TG_OP, row_to_json(NEW),
                NULLIF(current_setting('app.cascade_data', true), '')::jsonb,
                string_to_array(NULLIF(current_setting('app.cascade_entities', true), ''), ','),
                NULLIF(current_setting('app.cascade_source', true), '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER audit_trigger_post
        AFTER INSERT ON blog.tb_post
        FOR EACH ROW EXECUTE FUNCTION app.audit_trigger_post();
    """

    db_connection.execute(setup_sql)

    # Execute mutation with cascade
    tenant_id = uuid4()
    post_id = uuid4()
    user_id = uuid4()

    mutation_sql = f"""
    DO $$
    DECLARE
        v_cascade_data JSONB;
    BEGIN
        -- Build cascade data (as action function would)
        v_cascade_data := jsonb_build_object(
            'updated', jsonb_build_array(
                jsonb_build_object(
                    '__typename', 'Post',
                    'id', '{post_id}',
                    'operation', 'CREATED'
                ),
                jsonb_build_object(
                    '__typename', 'User',
                    'id', '{user_id}',
                    'operation', 'UPDATED'
                )
            )
        );

        -- Set session variables
        PERFORM set_config('app.cascade_data', v_cascade_data::text, true);
        PERFORM set_config('app.cascade_entities', 'Post,User', true);
        PERFORM set_config('app.cascade_source', 'create_post', true);

        -- Execute mutation (trigger fires here)
        INSERT INTO blog.tb_post (id, title, tenant_id)
        VALUES ('{post_id}', 'Test Post', '{tenant_id}');

        -- Clear session variables
        PERFORM set_config('app.cascade_data', NULL, true);
        PERFORM set_config('app.cascade_entities', NULL, true);
        PERFORM set_config('app.cascade_source', NULL, true);
    END $$;
    """

    db_connection.execute(mutation_sql)

    # Verify audit record captured cascade
    audit = db_connection.execute(f"""
        SELECT
            cascade_data,
            cascade_entities,
            cascade_source
        FROM app.audit_post
        WHERE entity_id = '{post_id}'
    """).fetchone()

    assert audit is not None
    assert audit['cascade_data'] is not None
    assert 'updated' in audit['cascade_data']
    assert len(audit['cascade_data']['updated']) == 2
    assert audit['cascade_entities'] == ['Post', 'User']
    assert audit['cascade_source'] == 'create_post'
```

**Acceptance Criteria**:
- [ ] Audit triggers capture cascade data from session variables
- [ ] Action functions set session variables before DML operations
- [ ] Action functions clear session variables after completion
- [ ] Cascade data properly stored in audit tables
- [ ] Integration tests pass with real mutations

---

### TDD CYCLE 2.3: Enhanced Audit Query with Cascade

**🔴 RED - Write Failing Test**

```python
# tests/unit/generators/test_audit_query_cascade.py

def test_audit_query_includes_cascade_option():
    """Audit query functions should support cascade data retrieval"""
    from src.generators.enterprise.audit_generator import AuditGenerator

    generator = AuditGenerator()
    sql = generator.generate_audit_query_functions(
        entity_name="Post",
        audit_config={"include_cascade": True}
    )

    # Should include function with cascade
    assert "get_post_audit_history_with_cascade" in sql

    # Should return cascade_data column
    assert "cascade_data JSONB" in sql

    # Should support filtering by affected entities
    assert "p_affected_entity" in sql or "affected_entity" in sql
```

**🟢 GREEN - Generate Cascade-Aware Query Functions**

File: `src/generators/enterprise/audit_generator.py`

```python
def generate_audit_query_functions(
    self, entity_name: str, audit_config: Dict
) -> str:
    """Generate audit query functions with optional cascade support"""
    audit_table_name = f"audit_{entity_name.lower()}"
    include_cascade = audit_config.get("include_cascade", False)

    sql_parts = []

    # Standard audit history query (EXISTING)
    sql_parts.append(f"""
-- Standard audit query (backward compatible)
CREATE OR REPLACE FUNCTION app.get_{entity_name.lower()}_audit_history(
    p_entity_id UUID,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE,
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.operation_type,
        a.changed_by,
        a.changed_at,
        a.old_values,
        a.new_values,
        a.change_reason
    FROM app.{audit_table_name} a
    WHERE a.entity_id = p_entity_id
      AND a.tenant_id = p_tenant_id
    ORDER BY a.changed_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

    # NEW: Cascade-aware audit query
    if include_cascade:
        sql_parts.append(f"""
-- Cascade-aware audit query
CREATE OR REPLACE FUNCTION app.get_{entity_name.lower()}_audit_history_with_cascade(
    p_entity_id UUID,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0,
    p_affected_entity TEXT DEFAULT NULL  -- Filter by entity type in cascade
)
RETURNS TABLE (
    audit_id UUID,
    operation_type TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE,
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    cascade_data JSONB,
    cascade_entities TEXT[],
    cascade_source TEXT,
    affected_entity_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.operation_type,
        a.changed_by,
        a.changed_at,
        a.old_values,
        a.new_values,
        a.change_reason,
        a.cascade_data,
        a.cascade_entities,
        a.cascade_source,
        COALESCE(array_length(a.cascade_entities, 1), 0) as affected_entity_count
    FROM app.{audit_table_name} a
    WHERE a.entity_id = p_entity_id
      AND a.tenant_id = p_tenant_id
      AND (
          p_affected_entity IS NULL
          OR p_affected_entity = ANY(a.cascade_entities)
      )
    ORDER BY a.changed_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

        # NEW: Query mutations by affected entity
        sql_parts.append(f"""
-- Find mutations that affected a specific entity type
CREATE OR REPLACE FUNCTION app.get_mutations_affecting_entity(
    p_entity_type TEXT,
    p_tenant_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    primary_entity_id UUID,
    mutation_name TEXT,
    changed_at TIMESTAMP WITH TIME ZONE,
    cascade_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.entity_id as primary_entity_id,
        a.cascade_source as mutation_name,
        a.changed_at,
        a.cascade_data
    FROM app.{audit_table_name} a
    WHERE a.tenant_id = p_tenant_id
      AND p_entity_type = ANY(a.cascade_entities)
    ORDER BY a.changed_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
""")

    return "\n\n".join(sql_parts)
```

**🔧 REFACTOR - Add Helper Views**

```python
def generate_cascade_audit_views(self, entity_name: str) -> str:
    """Generate convenient views for cascade audit queries"""
    audit_table_name = f"audit_{entity_name.lower()}"

    return f"""
-- Cascade audit summary view
CREATE OR REPLACE VIEW app.v_{entity_name.lower()}_cascade_audit AS
SELECT
    a.audit_id,
    a.entity_id,
    a.operation_type,
    a.changed_at,
    a.cascade_source as mutation_name,
    a.cascade_entities as affected_entities,
    jsonb_array_length(a.cascade_data->'updated') as entities_updated,
    jsonb_array_length(a.cascade_data->'deleted') as entities_deleted,
    (a.cascade_data->'metadata'->>'affectedCount')::integer as total_affected
FROM app.{audit_table_name} a
WHERE a.cascade_data IS NOT NULL
ORDER BY a.changed_at DESC;

-- Recent cascade mutations view
CREATE OR REPLACE VIEW app.v_{entity_name.lower()}_recent_cascade_mutations AS
SELECT
    a.audit_id,
    a.entity_id,
    a.cascade_source as mutation_name,
    a.changed_at,
    a.cascade_entities,
    a.cascade_data
FROM app.{audit_table_name} a
WHERE a.cascade_data IS NOT NULL
  AND a.changed_at > now() - interval '7 days'
ORDER BY a.changed_at DESC;
"""
```

**✅ QA - Integration Test**

```python
# tests/integration/test_cascade_audit_queries.py

def test_cascade_audit_query_functions(db_connection):
    """Test cascade-aware audit query functions"""

    # Setup: Create audit trail with cascade data
    # (Use setup from previous test)

    # Query standard audit history
    standard_result = db_connection.execute("""
        SELECT * FROM app.get_post_audit_history(
            '123...'::uuid,
            'tenant-abc'::uuid
        )
    """).fetchall()

    assert len(standard_result) > 0
    # Standard query doesn't include cascade (backward compatible)
    assert 'cascade_data' not in standard_result[0].keys()

    # Query with cascade
    cascade_result = db_connection.execute("""
        SELECT * FROM app.get_post_audit_history_with_cascade(
            '123...'::uuid,
            'tenant-abc'::uuid
        )
    """).fetchall()

    assert len(cascade_result) > 0
    assert 'cascade_data' in cascade_result[0].keys()
    assert cascade_result[0]['cascade_data'] is not None
    assert cascade_result[0]['affected_entity_count'] >= 1

    # Query mutations affecting User
    user_mutations = db_connection.execute("""
        SELECT * FROM app.get_mutations_affecting_entity(
            'User',
            'tenant-abc'::uuid
        )
    """).fetchall()

    assert len(user_mutations) > 0
    assert user_mutations[0]['mutation_name'] == 'create_post'
```

**Acceptance Criteria**:
- [ ] `get_{entity}_audit_history()` works without cascade (backward compatible)
- [ ] `get_{entity}_audit_history_with_cascade()` returns cascade data
- [ ] `get_mutations_affecting_entity()` finds cross-entity impacts
- [ ] Cascade audit views created successfully
- [ ] Integration tests pass
- [ ] Query performance is acceptable (< 100ms)

---

### TDD CYCLE 2.4: CLI Integration

**🔴 RED - Write Failing Test**

```python
# tests/unit/cli/test_audit_cascade_cli.py

def test_generate_with_audit_cascade_flag():
    """CLI should support --with-audit-cascade flag"""
    from src.cli.generate import generate_command

    # Mock entity with audit config
    yaml_content = """
    entity: Post
    audit:
      enabled: true
      include_cascade: true
    """

    result = generate_command(
        yaml_content,
        with_audit_cascade=True
    )

    assert "CASCADE_DATA" in result or "cascade_data" in result
    assert "get_post_audit_history_with_cascade" in result
```

**🟢 GREEN - Add CLI Flag**

File: `src/cli/generate.py`

```python
import click

@click.command()
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option('--with-impacts', is_flag=True, help='Generate impact metadata')
@click.option('--with-audit-cascade', is_flag=True,
              help='Integrate cascade data with audit trail')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def generate(yaml_file, with_impacts, with_audit_cascade, output):
    """Generate SQL from SpecQL YAML"""

    # Parse YAML
    parser = SpecQLParser()
    entity = parser.parse_file(yaml_file)

    # Configure audit with cascade
    if with_audit_cascade:
        if not entity.audit:
            entity.audit = {}
        entity.audit['include_cascade'] = True

    # Generate SQL
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_all(entity)

    if output:
        Path(output).write_text(sql)
        click.echo(f"Generated SQL written to {output}")
    else:
        click.echo(sql)
```

**🔧 REFACTOR - Update Documentation**

File: `docs/features/AUDIT_TRAIL_CASCADE.md` (NEW)

```markdown
# Audit Trail with Cascade Integration

## Overview

SpecQL audit trail can capture GraphQL cascade data, providing complete
mutation history showing all affected entities.

## Usage

### Enable in YAML

```yaml
entity: Post
audit:
  enabled: true
  include_cascade: true  # ← Enable cascade integration
```

### Generate with CLI

```bash
specql generate entities/post.yaml --with-audit-cascade
```

### Query Audit History

```sql
-- Standard audit (backward compatible)
SELECT * FROM app.get_post_audit_history('123...', 'tenant-abc');

-- With cascade data
SELECT * FROM app.get_post_audit_history_with_cascade('123...', 'tenant-abc');

-- Find mutations affecting User
SELECT * FROM app.get_mutations_affecting_entity('User', 'tenant-abc');
```

## Benefits

- **Complete History**: See all entities affected by each mutation
- **Mutation Replay**: Full cascade context enables exact replay
- **Debugging**: Trace side effects back to source mutation
- **Compliance**: "What else changed?" answered in one query
```

**✅ QA**

```bash
# CLI tests
uv run pytest tests/unit/cli/test_audit_cascade_cli.py -v

# E2E: Generate and verify
specql generate examples/post_with_audit_cascade.yaml --with-audit-cascade -o /tmp/test.sql
psql -f /tmp/test.sql
```

**Acceptance Criteria**:
- [ ] CLI supports `--with-audit-cascade` flag
- [ ] YAML supports `audit.include_cascade: true`
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Tests pass

---

### Phase 2 Summary

**Deliverables**:
- ✅ Audit tables with optional `cascade_data` column
- ✅ Audit triggers capture cascade from session variables
- ✅ Action functions set/clear session variables
- ✅ Enhanced query functions with cascade
- ✅ CLI integration
- ✅ Documentation and examples

**Files Modified**:
- `src/generators/enterprise/audit_generator.py`
- `src/generators/actions/impact_metadata_compiler.py`
- `src/cli/generate.py`

**Files Created**:
- `docs/features/AUDIT_TRAIL_CASCADE.md`
- `examples/post_with_audit_cascade.yaml`
- `tests/unit/generators/test_audit_cascade_*.py`
- `tests/integration/test_audit_cascade_*.py`

**Migration Path**:
```sql
-- For existing deployments
ALTER TABLE app.audit_{entity}
ADD COLUMN cascade_data JSONB,
ADD COLUMN cascade_entities TEXT[],
ADD COLUMN cascade_source TEXT;

CREATE INDEX idx_audit_{entity}_cascade_entities
ON app.audit_{entity} USING GIN (cascade_entities);
```

---

## PHASE 3: CDC Outbox Pattern

**Duration**: 3-5 days
**Objective**: Event-driven architecture support with Debezium CDC integration

**Value Proposition**:
- Async event streaming to Kafka
- Microservices integration
- Event replay and sourcing
- Analytics pipelines
- Decoupled architecture

**Prerequisites**: Phase 1 (Cascade) + Phase 2 (Audit) completed

---

### Design Decision: Outbox Table Structure

**Transactional Outbox Pattern**:
- Write events to `app.outbox` table in same transaction as business logic
- Debezium polls outbox table and streams to Kafka
- Events marked as processed after successful streaming
- Periodic cleanup of processed events

```sql
CREATE TABLE app.outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identity
    aggregate_type TEXT NOT NULL,        -- 'Post', 'User', etc.
    aggregate_id UUID NOT NULL,          -- Entity primary ID
    event_type TEXT NOT NULL,            -- 'PostCreated', 'UserUpdated', etc.
    event_version INTEGER DEFAULT 1,     -- Schema version

    -- Event payload
    event_payload JSONB NOT NULL,        -- Full event data
    event_metadata JSONB,                -- Cascade, correlation, tracing

    -- Routing
    tenant_id UUID,                      -- Multi-tenant routing
    partition_key TEXT,                  -- Kafka partition key

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,            -- NULL = unprocessed
    processed_by TEXT,                   -- Debezium connector ID

    -- Tracing
    trace_id TEXT,                       -- Distributed tracing
    correlation_id UUID,                 -- Link related events
    causation_id UUID,                   -- Event that caused this event

    -- Audit link
    audit_id UUID,                       -- Link to audit trail

    -- Retry handling
    retry_count INTEGER DEFAULT 0,
    last_error TEXT
);

-- Indexes
CREATE INDEX idx_outbox_unprocessed
    ON app.outbox (created_at)
    WHERE processed_at IS NULL;

CREATE INDEX idx_outbox_aggregate
    ON app.outbox (aggregate_type, aggregate_id);

CREATE INDEX idx_outbox_tenant
    ON app.outbox (tenant_id);

CREATE INDEX idx_outbox_event_type
    ON app.outbox (event_type);
```

---

### TDD CYCLE 3.1: Generate Outbox Table

**🔴 RED - Write Failing Test**

```python
# tests/unit/generators/test_outbox_generator.py

def test_outbox_table_generation():
    """Generate outbox table for CDC"""
    from src.generators.cdc.outbox_generator import OutboxGenerator

    generator = OutboxGenerator()
    sql = generator.generate_outbox_table()

    # Core columns
    assert "aggregate_type TEXT" in sql
    assert "aggregate_id UUID" in sql
    assert "event_type TEXT" in sql
    assert "event_payload JSONB" in sql
    assert "event_metadata JSONB" in sql

    # Cascade integration
    assert "event_metadata" in sql  # Will store cascade data

    # Indexes
    assert "idx_outbox_unprocessed" in sql
    assert "WHERE processed_at IS NULL" in sql
```

**🟢 GREEN - Implement Outbox Generator**

File: `src/generators/cdc/outbox_generator.py` (NEW)

```python
"""
CDC Outbox Pattern Generator

Generates transactional outbox tables and helper functions for
event-driven architecture with Debezium integration.
"""

from typing import Dict, Any, Optional


class OutboxGenerator:
    """Generates CDC outbox infrastructure"""

    def generate_outbox_table(self) -> str:
        """Generate app.outbox table for CDC"""
        return """
-- Transactional Outbox Table for CDC
CREATE TABLE IF NOT EXISTS app.outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identity
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    event_version INTEGER DEFAULT 1,

    -- Event payload
    event_payload JSONB NOT NULL,
    event_metadata JSONB,  -- Includes cascade data, tracing, etc.

    -- Routing
    tenant_id UUID,
    partition_key TEXT,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,
    processed_by TEXT,

    -- Distributed tracing
    trace_id TEXT,
    correlation_id UUID,
    causation_id UUID,

    -- Audit link
    audit_id UUID,

    -- Error handling
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,

    -- Constraints
    CONSTRAINT chk_event_type CHECK (
        event_type ~ '^[A-Z][a-zA-Z]*$'  -- PascalCase
    )
);

-- Unprocessed events (Debezium polling)
CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed
    ON app.outbox (created_at)
    WHERE processed_at IS NULL;

-- Aggregate lookups
CREATE INDEX IF NOT EXISTS idx_outbox_aggregate
    ON app.outbox (aggregate_type, aggregate_id);

-- Multi-tenant routing
CREATE INDEX IF NOT EXISTS idx_outbox_tenant
    ON app.outbox (tenant_id)
    WHERE tenant_id IS NOT NULL;

-- Event type filtering
CREATE INDEX IF NOT EXISTS idx_outbox_event_type
    ON app.outbox (event_type);

-- Correlation tracking
CREATE INDEX IF NOT EXISTS idx_outbox_correlation
    ON app.outbox (correlation_id)
    WHERE correlation_id IS NOT NULL;

-- Comment for documentation
COMMENT ON TABLE app.outbox IS
'Transactional outbox for CDC (Change Data Capture) via Debezium. Events written here are streamed to Kafka.';
"""

    def generate_outbox_helper_functions(self) -> str:
        """Generate helper functions for writing to outbox"""
        return """
-- Helper: Write event to outbox
CREATE OR REPLACE FUNCTION app.write_outbox_event(
    p_aggregate_type TEXT,
    p_aggregate_id UUID,
    p_event_type TEXT,
    p_event_payload JSONB,
    p_event_metadata JSONB DEFAULT NULL,
    p_tenant_id UUID DEFAULT NULL,
    p_trace_id TEXT DEFAULT NULL,
    p_correlation_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO app.outbox (
        aggregate_type,
        aggregate_id,
        event_type,
        event_payload,
        event_metadata,
        tenant_id,
        partition_key,
        trace_id,
        correlation_id
    ) VALUES (
        p_aggregate_type,
        p_aggregate_id,
        p_event_type,
        p_event_payload,
        p_event_metadata,
        p_tenant_id,
        p_aggregate_id::text,  -- Use aggregate_id as partition key
        p_trace_id,
        p_correlation_id
    )
    RETURNING id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- Helper: Mark event as processed (called by Debezium)
CREATE OR REPLACE FUNCTION app.mark_outbox_processed(
    p_event_id UUID,
    p_processor_id TEXT DEFAULT 'debezium'
) RETURNS void AS $$
BEGIN
    UPDATE app.outbox
    SET
        processed_at = now(),
        processed_by = p_processor_id
    WHERE id = p_event_id;
END;
$$ LANGUAGE plpgsql;

-- Cleanup: Delete old processed events
CREATE OR REPLACE FUNCTION app.cleanup_outbox(
    p_retention_days INTEGER DEFAULT 7
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM app.outbox
    WHERE processed_at IS NOT NULL
      AND processed_at < now() - (p_retention_days || ' days')::interval;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;
"""

    def generate_outbox_views(self) -> str:
        """Generate views for monitoring outbox"""
        return """
-- View: Unprocessed events
CREATE OR REPLACE VIEW app.v_outbox_pending AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    retry_count,
    last_error,
    age(now(), created_at) as pending_duration
FROM app.outbox
WHERE processed_at IS NULL
ORDER BY created_at ASC;

-- View: Event processing stats
CREATE OR REPLACE VIEW app.v_outbox_stats AS
SELECT
    event_type,
    COUNT(*) as total_events,
    COUNT(*) FILTER (WHERE processed_at IS NOT NULL) as processed,
    COUNT(*) FILTER (WHERE processed_at IS NULL) as pending,
    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) FILTER (WHERE processed_at IS NOT NULL) as avg_processing_seconds,
    MAX(created_at) as latest_event
FROM app.outbox
GROUP BY event_type
ORDER BY total_events DESC;

-- View: Recent events
CREATE OR REPLACE VIEW app.v_outbox_recent AS
SELECT
    id,
    aggregate_type,
    aggregate_id,
    event_type,
    created_at,
    processed_at,
    EXTRACT(EPOCH FROM (COALESCE(processed_at, now()) - created_at)) as processing_seconds
FROM app.outbox
WHERE created_at > now() - interval '1 hour'
ORDER BY created_at DESC;
"""

    def generate_all(self) -> str:
        """Generate complete outbox infrastructure"""
        return "\n\n".join([
            self.generate_outbox_table(),
            self.generate_outbox_helper_functions(),
            self.generate_outbox_views()
        ])
```

**🔧 REFACTOR - Add to AppSchemaGenerator**

File: `src/generators/app_schema_generator.py`

```python
from src.generators.cdc.outbox_generator import OutboxGenerator

class AppSchemaGenerator:
    def generate(self, include_outbox: bool = False) -> str:
        """Generate app schema with optional CDC outbox"""
        parts = []

        # Existing components
        parts.append(self._generate_mutation_result_type())
        parts.append(self._generate_cascade_helpers())

        # NEW: CDC Outbox
        if include_outbox:
            outbox_gen = OutboxGenerator()
            parts.append(outbox_gen.generate_all())

        return "\n\n".join(parts)
```

**✅ QA**

```python
# tests/integration/test_outbox_table.py

def test_outbox_table_creation(db_connection):
    """Test outbox table and helper functions"""
    from src.generators.cdc.outbox_generator import OutboxGenerator

    generator = OutboxGenerator()
    sql = generator.generate_all()

    db_connection.execute(sql)

    # Verify table exists
    tables = db_connection.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'app' AND tablename = 'outbox'
    """).fetchall()

    assert len(tables) == 1

    # Test write_outbox_event
    event_id = db_connection.execute("""
        SELECT app.write_outbox_event(
            'Post',
            gen_random_uuid(),
            'PostCreated',
            '{"title": "Test"}'::jsonb,
            '{"cascade": {}}'::jsonb
        ) as event_id
    """).fetchone()['event_id']

    assert event_id is not None

    # Verify event in outbox
    event = db_connection.execute(f"""
        SELECT * FROM app.outbox WHERE id = '{event_id}'
    """).fetchone()

    assert event['aggregate_type'] == 'Post'
    assert event['event_type'] == 'PostCreated'
    assert event['processed_at'] is None
```

**Acceptance Criteria**:
- [ ] `app.outbox` table created successfully
- [ ] Helper functions work correctly
- [ ] Views provide useful monitoring
- [ ] Indexes optimize Debezium polling
- [ ] Integration tests pass

---

### TDD CYCLE 3.2: Write Outbox Events from Actions

**🔴 RED - Write Failing Test**

```python
# tests/unit/actions/test_action_outbox_integration.py

def test_action_writes_to_outbox():
    """Actions should optionally write events to outbox"""
    action = Action(
        name="create_post",
        impact=ActionImpact(
            primary=EntityImpact(entity="Post", operation="CREATE")
        ),
        steps=[],
        cdc=CDCConfig(enabled=True, event_type="PostCreated")  # NEW
    )

    compiler = ActionCompiler()
    sql = compiler.compile(action)

    # Should write to outbox
    assert "app.write_outbox_event" in sql
    assert "'PostCreated'" in sql
    assert "v_cascade_data" in sql  # Cascade in metadata
```

**🟢 GREEN - Add CDC Config to AST**

File: `src/core/ast_models.py`

```python
@dataclass
class CDCConfig:
    """CDC/Outbox configuration for actions"""

    enabled: bool = False
    event_type: str | None = None  # e.g., 'PostCreated'
    include_cascade: bool = True    # Include cascade in event_metadata
    include_payload: bool = True    # Include full entity data
    partition_key: str | None = None  # Custom partition key expression

@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: str | None = None
    steps: list[ActionStep] = field(default_factory=list)
    impact: ActionImpact | None = None
    hierarchy_impact: str | None = None
    cdc: CDCConfig | None = None  # NEW: CDC configuration
```

**🟢 GREEN - Generate Outbox Write in Actions**

File: `src/generators/actions/outbox_event_compiler.py` (NEW)

```python
"""
Outbox Event Compiler

Generates code to write events to app.outbox table from action functions.
"""

from dataclasses import dataclass
from src.core.ast_models import Action, CDCConfig, Entity


@dataclass
class OutboxEventCompiler:
    """Compiles outbox event writes from action metadata"""

    def compile(self, action: Action, entity: Entity) -> str:
        """Generate outbox event write if CDC enabled"""
        if not action.cdc or not action.cdc.enabled:
            return ""

        cdc = action.cdc
        event_type = cdc.event_type or self._infer_event_type(action, entity)

        # Determine aggregate info
        aggregate_type = entity.name
        aggregate_id_var = f"v_{entity.name.lower()}_id"

        # Build event payload
        payload = self._build_event_payload(action, entity, cdc)

        # Build event metadata (includes cascade)
        metadata = self._build_event_metadata(action, cdc)

        return f"""
    -- Write CDC event to outbox
    v_event_id := app.write_outbox_event(
        '{aggregate_type}',
        {aggregate_id_var},
        '{event_type}',
        {payload},
        {metadata},
        p_tenant_id,  -- Tenant routing
        p_trace_id,   -- Distributed tracing
        gen_random_uuid()  -- Correlation ID
    );
"""

    def _infer_event_type(self, action: Action, entity: Entity) -> str:
        """Infer event type from action name"""
        # create_post → PostCreated
        # update_user → UserUpdated
        # delete_comment → CommentDeleted

        if action.impact and action.impact.primary:
            operation = action.impact.primary.operation
            if operation == "CREATE":
                return f"{entity.name}Created"
            elif operation == "UPDATE":
                return f"{entity.name}Updated"
            elif operation == "DELETE":
                return f"{entity.name}Deleted"

        # Fallback: PascalCase action name
        return ''.join(word.capitalize() for word in action.name.split('_'))

    def _build_event_payload(
        self, action: Action, entity: Entity, cdc: CDCConfig
    ) -> str:
        """Build event payload JSONB expression"""
        if not cdc.include_payload:
            return "'{}'"

        # Use table view data if available
        if entity.should_generate_table_view:
            return f"""(
                SELECT data FROM {entity.schema}.tv_{entity.name.lower()}
                WHERE id = v_{entity.name.lower()}_id
            )"""

        # Fallback: Build from table
        return f"""(
            SELECT row_to_json(t.*)::jsonb
            FROM {entity.schema}.tb_{entity.name.lower()} t
            WHERE id = v_{entity.name.lower()}_id
        )"""

    def _build_event_metadata(self, action: Action, cdc: CDCConfig) -> str:
        """Build event metadata including cascade"""
        parts = ["'{}'::jsonb"]

        if cdc.include_cascade and action.impact:
            parts = [f"""jsonb_build_object(
                'cascade', v_cascade_data,
                'mutation', '{action.name}',
                'affectedEntities', ARRAY(
                    SELECT jsonb_array_elements_text(
                        v_cascade_data->'updated'
                    )->>'__typename'
                )
            )"""]

        return parts[0]

    def declare_variables(self, action: Action) -> str:
        """Declare variables needed for outbox"""
        if not action.cdc or not action.cdc.enabled:
            return ""

        return "v_event_id UUID;"
```

**🔧 REFACTOR - Integrate into Action Compilation**

File: `src/generators/actions/function_generator.py`

```python
from src.generators.actions.outbox_event_compiler import OutboxEventCompiler

class FunctionGenerator:
    def generate(self, action: Action, context: ActionContext) -> str:
        """Generate complete action function with optional outbox"""

        # Declarations
        declarations = self._generate_declarations(action, context)
        if action.cdc and action.cdc.enabled:
            outbox_compiler = OutboxEventCompiler()
            declarations += "\n    " + outbox_compiler.declare_variables(action)

        # Business logic
        logic = self._generate_business_logic(action, context)

        # Outbox event (after business logic, before return)
        outbox_event = ""
        if action.cdc and action.cdc.enabled:
            outbox_compiler = OutboxEventCompiler()
            outbox_event = outbox_compiler.compile(action, context.entity)

        # Success response
        response = self._generate_success_response(action, context)

        return f"""
CREATE OR REPLACE FUNCTION {context.function_name}(...)
RETURNS app.mutation_result AS $$
DECLARE
    {declarations}
BEGIN
    {logic}

    {outbox_event}

    {response}

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
"""
```

**✅ QA - Integration Test**

```python
# tests/integration/test_action_outbox.py

def test_action_writes_outbox_event(db_connection):
    """Test action writes event to outbox when CDC enabled"""

    yaml_content = """
    entity: Post
    schema: blog
    fields:
      title: text

    actions:
      - name: create_post
        steps:
          - insert: Post

        impact:
          primary:
            entity: Post
            operation: CREATE

        cdc:
          enabled: true
          event_type: PostCreated
          include_cascade: true
    """

    # Generate and execute
    entity = parse_specql_yaml(yaml_content)
    orchestrator = SchemaOrchestrator()
    sql = orchestrator.generate_all(entity, include_outbox=True)

    db_connection.execute(sql)

    # Execute mutation
    result = db_connection.execute("""
        SELECT blog.fn_create_post($1::jsonb) as result
    """, {'title': 'Test Post'}).fetchone()

    assert result['result']['status'] == 'success'

    # Verify outbox event created
    events = db_connection.execute("""
        SELECT * FROM app.outbox
        WHERE event_type = 'PostCreated'
        ORDER BY created_at DESC
        LIMIT 1
    """).fetchone()

    assert events is not None
    assert events['aggregate_type'] == 'Post'
    assert events['event_type'] == 'PostCreated'
    assert events['event_payload']['title'] == 'Test Post'
    assert events['event_metadata']['mutation'] == 'create_post'
    assert events['event_metadata']['cascade'] is not None
    assert events['processed_at'] is None  # Not yet processed by Debezium
```

**Acceptance Criteria**:
- [ ] Actions with `cdc.enabled: true` write to outbox
- [ ] Event type inferred or specified
- [ ] Event payload includes entity data
- [ ] Event metadata includes cascade data
- [ ] Tenant routing works correctly
- [ ] Integration tests pass

---

### TDD CYCLE 3.3: Debezium Configuration

**🔴 RED - Write Test**

```python
# tests/unit/cdc/test_debezium_config.py

def test_generate_debezium_config():
    """Generate Debezium connector configuration"""
    from src.generators.cdc.debezium_config_generator import DebeziumConfigGenerator

    generator = DebeziumConfigGenerator()
    config = generator.generate_connector_config(
        database_host="localhost",
        database_name="specql_db",
        kafka_bootstrap_servers="kafka:9092"
    )

    assert config['name'] == 'specql-outbox-connector'
    assert config['config']['table.include.list'] == 'app.outbox'
    assert config['config']['transforms'] == 'outbox'
```

**🟢 GREEN - Generate Debezium Config**

File: `src/generators/cdc/debezium_config_generator.py` (NEW)

```python
"""
Debezium Configuration Generator

Generates Debezium connector configurations for SpecQL outbox pattern.
"""

import json
from typing import Dict, Any


class DebeziumConfigGenerator:
    """Generates Debezium CDC connector configurations"""

    def generate_connector_config(
        self,
        database_host: str,
        database_name: str,
        database_user: str = "postgres",
        kafka_bootstrap_servers: str = "kafka:9092",
        kafka_topic_prefix: str = "specql",
    ) -> Dict[str, Any]:
        """Generate Debezium PostgreSQL connector config for outbox"""

        return {
            "name": "specql-outbox-connector",
            "config": {
                # Connector class
                "connector.class": "io.debezium.connector.postgresql.PostgresConnector",

                # Database connection
                "database.hostname": database_host,
                "database.port": "5432",
                "database.user": database_user,
                "database.password": "${DB_PASSWORD}",
                "database.dbname": database_name,
                "database.server.name": kafka_topic_prefix,

                # Tables to capture
                "table.include.list": "app.outbox",

                # Publication (PostgreSQL logical replication)
                "publication.name": "specql_outbox_publication",
                "publication.autocreate.mode": "filtered",

                # Slot
                "slot.name": "specql_outbox_slot",

                # Transforms: Outbox Event Router
                "transforms": "outbox",
                "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
                "transforms.outbox.table.field.event.id": "id",
                "transforms.outbox.table.field.event.key": "aggregate_id",
                "transforms.outbox.table.field.event.type": "event_type",
                "transforms.outbox.table.field.event.payload": "event_payload",
                "transforms.outbox.table.field.event.timestamp": "created_at",
                "transforms.outbox.route.topic.replacement": "${kafka_topic_prefix}.events.${routedByValue}",
                "transforms.outbox.route.by.field": "aggregate_type",

                # Topic routing
                "topic.prefix": kafka_topic_prefix,

                # Performance
                "max.batch.size": "2048",
                "poll.interval.ms": "1000",

                # Schema
                "key.converter": "org.apache.kafka.connect.json.JsonConverter",
                "value.converter": "org.apache.kafka.connect.json.JsonConverter",
                "key.converter.schemas.enable": "false",
                "value.converter.schemas.enable": "false",

                # Cleanup processed events
                "transforms.outbox.table.op.invalid.behavior": "warn"
            }
        }

    def generate_docker_compose(
        self,
        database_host: str = "postgres",
        kafka_host: str = "kafka"
    ) -> str:
        """Generate docker-compose.yml for CDC stack"""

        return f"""
version: '3.8'

services:
  # Zookeeper (required by Kafka)
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  # Kafka Connect with Debezium
  kafka-connect:
    image: debezium/connect:latest
    depends_on:
      - kafka
      - {database_host}
    ports:
      - "8083:8083"
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      GROUP_ID: 1
      CONFIG_STORAGE_TOPIC: connect_configs
      OFFSET_STORAGE_TOPIC: connect_offsets
      STATUS_STORAGE_TOPIC: connect_status
      KEY_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      VALUE_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      CONNECT_KEY_CONVERTER_SCHEMAS_ENABLE: "false"
      CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE: "false"

  # Kafka UI (optional, for monitoring)
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
"""

    def generate_deployment_script(self) -> str:
        """Generate script to deploy Debezium connector"""

        return """#!/bin/bash
# Deploy SpecQL Outbox Debezium Connector

set -e

KAFKA_CONNECT_URL="${KAFKA_CONNECT_URL:-http://localhost:8083}"
CONFIG_FILE="${1:-debezium-outbox-connector.json}"

echo "Deploying Debezium connector from $CONFIG_FILE..."

# Deploy connector
curl -X POST \\
  -H "Content-Type: application/json" \\
  -d @"$CONFIG_FILE" \\
  "$KAFKA_CONNECT_URL/connectors"

echo ""
echo "Connector deployed successfully!"

# Check status
echo ""
echo "Connector status:"
curl -s "$KAFKA_CONNECT_URL/connectors/specql-outbox-connector/status" | jq .
"""

    def generate_all(
        self,
        database_host: str,
        database_name: str,
        output_dir: str = "./cdc"
    ) -> Dict[str, str]:
        """Generate all CDC configuration files"""

        files = {}

        # Connector config
        connector_config = self.generate_connector_config(
            database_host, database_name
        )
        files['debezium-outbox-connector.json'] = json.dumps(
            connector_config, indent=2
        )

        # Docker Compose
        files['docker-compose.yml'] = self.generate_docker_compose(
            database_host
        )

        # Deployment script
        files['deploy-connector.sh'] = self.generate_deployment_script()

        return files
```

**🔧 REFACTOR - CLI Command**

File: `src/cli/cdc.py` (NEW)

```python
"""CLI commands for CDC/Outbox setup"""

import click
import json
from pathlib import Path
from src.generators.cdc.debezium_config_generator import DebeziumConfigGenerator


@click.group()
def cdc():
    """CDC and event streaming commands"""
    pass


@cdc.command()
@click.option('--database-host', default='localhost', help='PostgreSQL host')
@click.option('--database-name', required=True, help='PostgreSQL database name')
@click.option('--kafka-host', default='kafka:9092', help='Kafka bootstrap servers')
@click.option('--output-dir', default='./cdc', help='Output directory')
def generate_config(database_host, database_name, kafka_host, output_dir):
    """Generate Debezium connector configuration"""

    generator = DebeziumConfigGenerator()
    files = generator.generate_all(database_host, database_name, output_dir)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        file_path = output_path / filename
        file_path.write_text(content)
        click.echo(f"Generated {file_path}")

    click.echo(f"\nCDC configuration generated in {output_dir}/")
    click.echo("\nNext steps:")
    click.echo("1. Start CDC stack: cd cdc && docker-compose up -d")
    click.echo("2. Deploy connector: ./deploy-connector.sh")
    click.echo("3. Monitor: http://localhost:8080 (Kafka UI)")


@cdc.command()
@click.option('--kafka-connect-url', default='http://localhost:8083')
def status(kafka_connect_url):
    """Check Debezium connector status"""
    import requests

    try:
        response = requests.get(f"{kafka_connect_url}/connectors/specql-outbox-connector/status")
        status = response.json()

        click.echo(f"Connector: {status['name']}")
        click.echo(f"State: {status['connector']['state']}")
        click.echo(f"Worker: {status['connector']['worker_id']}")

        for task in status.get('tasks', []):
            click.echo(f"Task {task['id']}: {task['state']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    cdc()
```

**✅ QA**

```bash
# Generate CDC config
specql cdc generate-config \\
  --database-host=localhost \\
  --database-name=mydb \\
  --output-dir=./cdc

# Start CDC stack
cd cdc
docker-compose up -d

# Deploy connector
./deploy-connector.sh

# Check status
specql cdc status
```

**Acceptance Criteria**:
- [ ] Debezium connector config generated
- [ ] Docker Compose file with full CDC stack
- [ ] Deployment scripts provided
- [ ] CLI commands work
- [ ] Documentation included

---

### Phase 3 Summary

**Deliverables**:
- ✅ `app.outbox` table with helper functions
- ✅ Action functions write CDC events
- ✅ Cascade data included in event metadata
- ✅ Debezium connector configuration
- ✅ Docker Compose CDC stack
- ✅ CLI commands for CDC setup
- ✅ Documentation and examples

**Files Created**:
- `src/generators/cdc/outbox_generator.py`
- `src/generators/cdc/debezium_config_generator.py`
- `src/generators/actions/outbox_event_compiler.py`
- `src/cli/cdc.py`
- `docs/features/CDC_OUTBOX_PATTERN.md`
- `examples/cdc/docker-compose.yml`
- `examples/cdc/debezium-outbox-connector.json`

**Kafka Topics Created**:
- `specql.events.Post` - Post events
- `specql.events.User` - User events
- `specql.events.{Entity}` - Per-entity topics

**Event Format**:
```json
{
  "id": "123...",
  "aggregate_type": "Post",
  "aggregate_id": "456...",
  "event_type": "PostCreated",
  "event_payload": {
    "id": "456...",
    "title": "Hello World",
    "author": { "id": "789...", "name": "John" }
  },
  "event_metadata": {
    "cascade": {
      "updated": [
        { "__typename": "Post", "operation": "CREATED", ... },
        { "__typename": "User", "operation": "UPDATED", ... }
      ]
    },
    "mutation": "create_post",
    "affectedEntities": ["Post", "User"]
  },
  "trace_id": "abc123",
  "correlation_id": "def456"
}
```

---

## Testing Strategy

### Unit Tests
```bash
# Phase 2: Audit + Cascade
uv run pytest tests/unit/generators/test_audit_cascade_*.py
uv run pytest tests/unit/actions/test_audit_session_vars.py

# Phase 3: CDC Outbox
uv run pytest tests/unit/generators/test_outbox_*.py
uv run pytest tests/unit/cdc/test_debezium_*.py
```

### Integration Tests
```bash
# Phase 2: E2E Audit
uv run pytest tests/integration/test_audit_cascade_e2e.py

# Phase 3: E2E CDC
uv run pytest tests/integration/test_outbox_e2e.py
uv run pytest tests/integration/test_debezium_integration.py
```

### Performance Tests
```bash
# Cascade overhead
uv run pytest tests/performance/test_cascade_overhead.py

# Outbox write performance
uv run pytest tests/performance/test_outbox_throughput.py
```

---

## Rollout Plan

### Week 1: Phase 2 (Audit Integration)

**Day 1-2**: Schema & Triggers
- TDD Cycle 2.1: Audit table schema with cascade
- TDD Cycle 2.2: Audit triggers capture cascade
- Migration scripts

**Day 3**: Query Functions
- TDD Cycle 2.3: Enhanced audit queries
- Views and helper functions
- Integration tests

**Day 4**: CLI & Documentation
- TDD Cycle 2.4: CLI integration
- Documentation
- Examples

**Day 5**: Testing & Refinement
- Performance testing
- Bug fixes
- User acceptance testing

### Week 2: Phase 3 (CDC Outbox)

**Day 1-2**: Outbox Infrastructure
- TDD Cycle 3.1: Outbox table generation
- Helper functions
- Views and monitoring

**Day 3-4**: Action Integration
- TDD Cycle 3.2: Actions write to outbox
- Event compilation
- Integration testing

**Day 5**: Debezium Setup
- TDD Cycle 3.3: Debezium config
- Docker Compose stack
- Deployment automation
- Documentation

---

## Success Metrics

### Phase 2 Metrics
- [ ] Audit queries with cascade < 100ms
- [ ] Zero impact on mutation performance
- [ ] 90%+ test coverage
- [ ] Documentation complete
- [ ] Migration path validated

### Phase 3 Metrics
- [ ] Outbox write overhead < 10ms
- [ ] Debezium lag < 1 second
- [ ] Event throughput > 1000/sec
- [ ] Zero event loss
- [ ] 90%+ test coverage

---

## Documentation

### User Guides
- `docs/features/AUDIT_TRAIL_CASCADE.md`
- `docs/features/CDC_OUTBOX_PATTERN.md`
- `docs/guides/SETTING_UP_CDC.md`

### API Reference
- `docs/api/AUDIT_FUNCTIONS.md`
- `docs/api/OUTBOX_API.md`

### Examples
- `examples/audit_cascade/post_with_audit.yaml`
- `examples/cdc/post_with_cdc.yaml`
- `examples/cdc/docker-compose.yml`
- `examples/cdc/microservice-consumer.py`

---

**Status**: Implementation Ready
**Prerequisites**: Phase 1 (Cascade) completed
**Timeline**: 2-3 weeks total (Phase 2 + Phase 3)
**Next**: Begin TDD Cycle 2.1
