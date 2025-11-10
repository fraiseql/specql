# Implementation Plan: Complete Mutation Pattern Library for PrintOptim Team

**Issue**: #4 - Enhancement: Complete Mutation Pattern Library with Business Logic Actions
**Goal**: Help PrintOptim team by implementing missing CRUD features and building a declarative action pattern library
**Estimated Timeline**: 10-14 weeks
**Status**: Proposal for Implementation

---

## 🎯 Executive Summary

This plan addresses critical gaps between SpecQL's current CRUD generation and PrintOptim's production requirements. We'll implement 6 missing core features and build a pattern library for declarative business logic, enabling SpecQL to generate complete, production-ready PostgreSQL + GraphQL backends from lightweight YAML definitions.

**What PrintOptim Needs**:
- ✅ Partial updates (PATCH semantics)
- ✅ Duplicate detection with structured errors
- ✅ Identifier recalculation (Trinity pattern)
- ✅ GraphQL projection sync
- ✅ Hard delete with dependency checking
- ✅ Declarative business actions (state machines, multi-entity ops, batch processing)

**Success Metric**: PrintOptim can express their entire backend in SpecQL YAML and generate 100% production-ready SQL.

---

## 📊 Current State Analysis

### What SpecQL Already Has ✅
Based on codebase review:

1. **Action Orchestrator** (`src/generators/actions/action_orchestrator.py`)
   - Multi-entity operation coordination
   - Transaction management
   - Step compiler registry

2. **Step Compilers** (`src/generators/actions/step_compilers/`)
   - `insert_compiler.py` - INSERT with Trinity pattern
   - `update_compiler.py` - UPDATE with audit fields
   - `delete_compiler.py` - Soft delete support
   - `validate_compiler.py` - Validation logic
   - `if_compiler.py` - Conditional branching
   - `foreach_compiler.py` - Loop support
   - `call_compiler.py` - Function calls
   - `notify_compiler.py` - Notifications
   - `refresh_table_view_compiler.py` - Table view refresh (EXISTS!)

3. **Foundation Components**
   - `identifier_recalc_generator.py` - Identifier recalculation (EXISTS!)
   - `success_response_generator.py` - Response formatting
   - `expression_compiler.py` - Expression → SQL compilation
   - `trinity_resolver.py` - UUID ↔ INTEGER resolution
   - `composite_type_builder.py` - Rich type handling
   - `error_codes.py` - Error code management

4. **Test Coverage**
   - 439 passing unit tests
   - Integration tests for full compilation pipeline
   - Tests for mutations with table view refresh (`test_mutations_with_tv_refresh.py`)

### What's Missing ⚠️

1. **Partial Update Support** - UpdateCompiler only does full field updates
2. **Duplicate Detection** - No pre-INSERT uniqueness checking
3. **Projection Refresh Integration** - Refresh compiler exists but not integrated into action flow
4. **Hard Delete** - DeleteCompiler only implements soft delete
5. **Dependency Checking** - No pre-delete dependency validation
6. **Action Pattern Library** - No declarative patterns for business logic

---

## 🏗️ Architecture Overview

### Current Architecture (Simplified)

```
SpecQL YAML
    ↓
Parser (Team A) → EntityDefinition + ActionDefinition
    ↓
ActionOrchestrator
    ↓
Step Compilers → PL/pgSQL Steps
    ↓
Function Generator → Complete SQL Functions
```

### Proposed Enhancements

```
SpecQL YAML
    ↓
Pattern Library Loader (NEW) → Expand patterns to steps
    ↓
Parser → EntityDefinition + ActionDefinition
    ↓
ActionOrchestrator (ENHANCED)
    ↓
    ├─ PartialUpdateCompiler (NEW)
    ├─ DuplicateCheckCompiler (NEW)
    ├─ DependencyCheckCompiler (NEW)
    ├─ IdentifierRecalcCompiler (ENHANCED - integrate existing)
    ├─ ProjectionRefreshCompiler (ENHANCED - integrate existing)
    └─ Existing Step Compilers
    ↓
Function Generator → Complete SQL Functions
```

---

## 📋 Phase 1: Core CRUD Enhancements (4 weeks)

**Goal**: Fix missing CRUD features to match PrintOptim reference implementation

### 1.1 Partial Updates (CASE-based Field Updates) - Week 1

**Current Problem**:
```python
# src/generators/actions/step_compilers/update_compiler.py:50-68
def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
    # Currently updates ALL fields regardless of input
    set_assignments = self._parse_set_clause(update_spec)
    # No CASE logic for partial updates
```

**Solution**:
```python
# NEW: src/generators/actions/step_compilers/partial_update_compiler.py
class PartialUpdateCompiler:
    """Compiles UPDATE with CASE expressions for partial updates"""

    def compile(self, step: ActionStep, entity: EntityDefinition,
                context: dict, partial: bool = True) -> str:
        """
        Generate UPDATE with CASE expressions:

        SET field1 = CASE WHEN input_payload ? 'field1'
                         THEN input_data.field1
                         ELSE field1 END,
            field2 = CASE WHEN input_payload ? 'field2'
                         THEN input_data.field2
                         ELSE field2 END
        """

        if not partial:
            # Fall back to full update
            return self._compile_full_update(step, entity, context)

        set_clauses = []
        for field_name, field_def in entity.fields.items():
            set_clauses.append(
                f"{field_name} = CASE WHEN input_payload ? '{field_name}' "
                f"THEN input_data.{field_name} ELSE {field_name} END"
            )

        # Track which fields were updated
        tracking_code = self._generate_field_tracking(entity.fields.keys())

        return f"""
    -- Partial update {entity.name}
    UPDATE {entity.schema}.tb_{entity.name.lower()}
    SET
        {', '.join(set_clauses)},
        updated_at = NOW(),
        updated_by = auth_user_id
    WHERE id = v_{entity.name.lower()}_id
      AND tenant_id = auth_tenant_id;

    {tracking_code}
"""
```

**YAML Interface**:
```yaml
# entities/tenant/contract.yaml
actions:
  - name: update_contract
    partial_updates: true  # Enable CASE-based partial updates
    track_updated_fields: true  # Track which fields changed
    steps:
      - update: Contract
```

**Generated SQL** (PrintOptim-compatible):
```sql
UPDATE tenant.tb_contract
SET
    customer_contract_id = CASE WHEN input_payload ? 'customer_contract_id'
                               THEN input_data.customer_contract_id
                               ELSE customer_contract_id END,
    provider_contract_id = CASE WHEN input_payload ? 'provider_contract_id'
                               THEN input_data.provider_contract_id
                               ELSE provider_contract_id END,
    -- ... all fields ...
    updated_at = NOW(),
    updated_by = auth_user_id
WHERE id = v_contract_id
  AND tenant_id = auth_tenant_id;

-- Track updated fields
IF input_payload ? 'customer_contract_id' THEN
    v_updated_fields := v_updated_fields || ARRAY['customer_contract_id'];
END IF;
-- ... more tracking ...
```

**Testing Strategy**:
```python
# tests/unit/actions/test_partial_update_compiler.py
def test_partial_update_generates_case_expressions():
    """Verify CASE expressions are generated for each field"""

def test_partial_update_tracks_changed_fields():
    """Verify field tracking code is generated"""

def test_partial_update_fallback_to_full():
    """Verify fallback when partial_updates=false"""

# tests/integration/actions/test_partial_updates_db.py
def test_partial_update_preserves_unspecified_fields():
    """Integration test: fields not in payload are preserved"""
```

**Files to Create/Modify**:
- ✅ Create: `src/generators/actions/step_compilers/partial_update_compiler.py`
- ✅ Modify: `src/generators/actions/action_orchestrator.py` (register compiler)
- ✅ Modify: `src/core/ast_models.py` (add `partial_updates` to ActionDefinition)
- ✅ Create: `tests/unit/actions/test_partial_update_compiler.py`
- ✅ Create: `tests/integration/actions/test_partial_updates_db.py`

**Acceptance Criteria**:
- [ ] UPDATE generates CASE expressions when `partial_updates: true`
- [ ] Fields not in payload are preserved
- [ ] Field tracking code generated when `track_updated_fields: true`
- [ ] Integration test: PATCH semantics work end-to-end
- [ ] Backward compatible: existing update actions still work

---

### 1.2 Duplicate Detection (Business Uniqueness) - Week 2

**Current Problem**:
```python
# src/generators/actions/step_compilers/insert_compiler.py:80-87
def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
    # Direct INSERT - no duplicate checking
    return f"""
    INSERT INTO {table_name} (...) VALUES (...);
"""
```

**Solution**:
```python
# NEW: src/generators/actions/step_compilers/duplicate_check_compiler.py
class DuplicateCheckCompiler:
    """Generates duplicate detection logic before INSERT"""

    def compile(self, constraint: UniqueConstraint, entity: EntityDefinition) -> str:
        """
        Generate duplicate check:

        1. Check if record exists with business key
        2. If exists, return NOOP with conflict details
        3. If not exists, continue to INSERT
        """

        check_fields = constraint.fields
        field_conditions = [
            f"{field} = input_data.{field}"
            for field in check_fields
        ]

        return f"""
    -- Check for duplicate {entity.name}
    SELECT id INTO v_existing_id
    FROM {entity.schema}.tb_{entity.name.lower()}
    WHERE {' AND '.join(field_conditions)}
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        -- Load existing object for conflict response
        SELECT data INTO v_existing_object
        FROM {entity.schema}.v_{entity.name.lower()}_projection
        WHERE id = v_existing_id;

        -- Return NOOP with conflict details
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            '{entity.name.lower()}',
            v_existing_id,
            'NOOP',
            'noop:already_exists',
            ARRAY[]::TEXT[],
            '{constraint.error_message or "Record already exists"}',
            v_existing_object,
            v_existing_object,
            jsonb_build_object(
                'trigger', 'api_create',
                'status', 'noop:already_exists',
                'reason', 'unique_constraint_violation',
                'conflict', jsonb_build_object(
                    {self._build_conflict_fields(check_fields)},
                    'conflict_object', v_existing_object
                )
            )
        );
    END IF;
"""
```

**YAML Interface**:
```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant

constraints:
  - name: unique_customer_provider_contract
    type: unique
    fields: [customer_org, provider_org, customer_contract_id]
    check_on_create: true
    error_message: "Contract already exists for this customer/provider/contract_id"
    return_conflict_object: true

actions:
  - name: create_contract
    duplicate_detection: true  # Enable duplicate check
```

**Generated SQL**:
```sql
CREATE OR REPLACE FUNCTION app.create_contract(
    auth_tenant_id UUID,
    auth_user_id UUID,
    input_payload JSONB
) RETURNS app.mutation_result AS $$
DECLARE
    input_data app.type_create_contract_input;
    v_existing_id UUID;
    v_existing_object JSONB;
BEGIN
    -- Convert input
    input_data := jsonb_populate_record(NULL::app.type_create_contract_input, input_payload);

    -- Duplicate check
    SELECT id INTO v_existing_id
    FROM tenant.tb_contract
    WHERE customer_org = input_data.customer_org
      AND provider_org = input_data.provider_org
      AND customer_contract_id = input_data.customer_contract_id
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL;

    IF v_existing_id IS NOT NULL THEN
        SELECT data INTO v_existing_object
        FROM tenant.v_contract_projection
        WHERE id = v_existing_id;

        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id, 'contract', v_existing_id,
            'NOOP', 'noop:already_exists', ARRAY[]::TEXT[],
            'Contract already exists for this customer/provider/contract_id',
            v_existing_object, v_existing_object,
            jsonb_build_object(
                'conflict', jsonb_build_object(
                    'customer_org', input_data.customer_org,
                    'provider_org', input_data.provider_org,
                    'customer_contract_id', input_data.customer_contract_id,
                    'conflict_object', v_existing_object
                )
            )
        );
    END IF;

    -- Continue with INSERT...
END;
$$;
```

**Testing Strategy**:
```python
# tests/unit/actions/test_duplicate_check_compiler.py
def test_duplicate_check_generates_exists_query():
    """Verify SELECT query for existing record"""

def test_duplicate_check_returns_noop_on_conflict():
    """Verify NOOP response with conflict details"""

def test_duplicate_check_includes_conflict_object():
    """Verify existing object included in response"""

# tests/integration/actions/test_duplicate_detection_db.py
def test_create_duplicate_returns_noop():
    """Integration: creating duplicate returns NOOP"""

def test_create_duplicate_includes_existing_object():
    """Integration: NOOP includes existing object data"""
```

**Files to Create/Modify**:
- ✅ Create: `src/generators/actions/step_compilers/duplicate_check_compiler.py`
- ✅ Modify: `src/core/ast_models.py` (add `UniqueConstraint` model)
- ✅ Modify: `src/core/specql_parser.py` (parse `constraints` section)
- ✅ Modify: `src/generators/actions/action_orchestrator.py` (integrate duplicate checks)
- ✅ Create: `tests/unit/actions/test_duplicate_check_compiler.py`
- ✅ Create: `tests/integration/actions/test_duplicate_detection_db.py`

**Acceptance Criteria**:
- [ ] Duplicate detection generates SELECT before INSERT
- [ ] Returns structured NOOP with conflict details
- [ ] Includes existing object in conflict response
- [ ] Multiple unique constraints supported per entity
- [ ] Integration test: duplicate detection works end-to-end

---

### 1.3 Identifier Recalculation Integration - Week 3

**Current State**:
- ✅ `src/generators/actions/identifier_recalc_generator.py` EXISTS
- ⚠️ Not integrated into action flow

**Problem**: Identifiers remain `NULL` or `'pending:UUID'` after INSERT/UPDATE.

**Solution**: Integrate existing identifier recalculation into action orchestrator.

**YAML Interface**:
```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant

identifier:
  pattern: "CONTRACT-{signature_date:YYYY}-{sequence:03d}"
  sequence:
    scope: [customer_org]
    group_by: [signature_date:YYYY]
  recalculate_on: [create, update]

actions:
  - name: create_contract
    recalculate_identifier: true  # Auto-call recalc after INSERT

  - name: update_contract
    recalculate_identifier: true  # Auto-call recalc after UPDATE
```

**Generated SQL**:
```sql
CREATE OR REPLACE FUNCTION app.create_contract(...) RETURNS app.mutation_result AS $$
BEGIN
    -- INSERT with pending identifier
    INSERT INTO tenant.tb_contract (
        ...,
        identifier,
        ...
    ) VALUES (
        ...,
        'pending:' || v_contract_id,
        ...
    );

    -- Recalculate identifier (INTEGRATED)
    PERFORM tenant.recalcid_contract(
        v_contract_id,
        auth_tenant_id,
        auth_user_id
    );

    -- Continue...
END;
$$;

-- Auto-generated recalculation function
CREATE OR REPLACE FUNCTION tenant.recalcid_contract(
    entity_id UUID,
    tenant_id UUID,
    user_id UUID
) RETURNS VOID AS $$
DECLARE
    v_new_identifier TEXT;
    v_sequence_num INTEGER;
BEGIN
    -- Calculate sequence number
    SELECT COALESCE(MAX(sequence_number), 0) + 1
    INTO v_sequence_num
    FROM tenant.tb_contract
    WHERE customer_org = (
        SELECT customer_org FROM tenant.tb_contract WHERE id = entity_id
    )
    AND EXTRACT(YEAR FROM signature_date) = (
        SELECT EXTRACT(YEAR FROM signature_date)
        FROM tenant.tb_contract WHERE id = entity_id
    );

    -- Build identifier
    SELECT 'CONTRACT-' ||
           to_char(signature_date, 'YYYY') || '-' ||
           lpad(v_sequence_num::TEXT, 3, '0')
    INTO v_new_identifier
    FROM tenant.tb_contract
    WHERE id = entity_id;

    -- Update identifier
    UPDATE tenant.tb_contract
    SET identifier = v_new_identifier,
        sequence_number = v_sequence_num
    WHERE id = entity_id;
END;
$$;
```

**Testing Strategy**:
```python
# tests/unit/actions/test_identifier_recalc_integration.py
def test_create_action_calls_recalcid():
    """Verify recalcid call generated after INSERT"""

def test_update_action_calls_recalcid():
    """Verify recalcid call generated after UPDATE"""

def test_recalcid_function_generation():
    """Verify recalcid function matches pattern"""

# tests/integration/actions/test_identifier_recalc_db.py
def test_create_generates_identifier():
    """Integration: INSERT generates human-readable identifier"""

def test_identifier_pattern_respected():
    """Integration: identifier matches YAML pattern"""

def test_sequence_scoping():
    """Integration: sequence resets per scope"""
```

**Files to Modify**:
- ✅ Enhance: `src/generators/actions/identifier_recalc_generator.py` (add pattern parsing)
- ✅ Modify: `src/generators/actions/action_orchestrator.py` (call recalcid after INSERT/UPDATE)
- ✅ Modify: `src/core/ast_models.py` (add `IdentifierConfig` model)
- ✅ Modify: `src/core/specql_parser.py` (parse `identifier` section)
- ✅ Create: `tests/unit/actions/test_identifier_recalc_integration.py`
- ✅ Create: `tests/integration/actions/test_identifier_recalc_db.py`

**Acceptance Criteria**:
- [ ] `recalculate_identifier: true` generates recalcid call
- [ ] Recalcid function respects identifier pattern from YAML
- [ ] Sequence scoping works (per tenant, per year, etc.)
- [ ] Integration test: identifiers auto-generated on CREATE/UPDATE
- [ ] Backward compatible: entities without identifier config work

---

### 1.4 GraphQL Projection Sync - Week 3

**Current State**:
- ✅ `src/generators/actions/step_compilers/refresh_table_view_compiler.py` EXISTS
- ⚠️ Not integrated into action flow

**Problem**: GraphQL projections (materialized views) are stale after mutations.

**Solution**: Integrate existing refresh compiler into action orchestrator.

**YAML Interface**:
```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant

projections:
  - name: graphql_view
    materialize: true
    refresh_on: [create, update, delete]
    includes:
      - customer_org: [id, name, code]
      - provider_org: [id, name, code]
      - currency: [iso_code, symbol]
      - contract_items: [id, description, quantity]

actions:
  - name: create_contract
    refresh_projection: graphql_view  # Auto-refresh after mutation

  - name: update_contract
    refresh_projection: graphql_view
```

**Generated SQL**:
```sql
-- Auto-generated projection refresh function
CREATE OR REPLACE FUNCTION tenant.refresh_contract_projection(
    entity_id UUID,
    tenant_id UUID
) RETURNS VOID AS $$
BEGIN
    DELETE FROM tenant.v_contract_projection WHERE id = entity_id;

    INSERT INTO tenant.v_contract_projection
    SELECT
        c.id,
        c.identifier,
        jsonb_build_object(
            'id', c.id,
            'identifier', c.identifier,
            'customerOrg', jsonb_build_object(
                'id', co.id,
                'name', co.name,
                'code', co.code
            ),
            'providerOrg', jsonb_build_object(
                'id', po.id,
                'name', po.name,
                'code', po.code
            ),
            'currency', jsonb_build_object(
                'isoCode', curr.iso_code,
                'symbol', curr.symbol
            ),
            'contractItems', (
                SELECT jsonb_agg(jsonb_build_object(
                    'id', ci.id,
                    'description', ci.description,
                    'quantity', ci.quantity
                ))
                FROM tenant.tb_contract_item ci
                WHERE ci.contract_id = c.id
            )
        ) AS data
    FROM tenant.tb_contract c
    LEFT JOIN management.tb_organization co ON c.customer_org = co.id
    LEFT JOIN management.tb_organization po ON c.provider_org = po.id
    LEFT JOIN catalog.tb_currency curr ON c.currency = curr.id
    WHERE c.id = entity_id
      AND c.tenant_id = tenant_id;
END;
$$;

-- Mutation function calls refresh
CREATE OR REPLACE FUNCTION app.create_contract(...) RETURNS app.mutation_result AS $$
BEGIN
    -- INSERT
    INSERT INTO tenant.tb_contract (...) VALUES (...);

    -- Recalculate identifier
    PERFORM tenant.recalcid_contract(v_contract_id, auth_tenant_id, auth_user_id);

    -- Refresh projection (INTEGRATED)
    PERFORM tenant.refresh_contract_projection(v_contract_id, auth_tenant_id);

    -- Return from projection (fresh data)
    SELECT data INTO v_payload_after
    FROM tenant.v_contract_projection
    WHERE id = v_contract_id;

    RETURN app.log_and_return_mutation(
        ...,
        v_payload_after,
        NULL
    );
END;
$$;
```

**Testing Strategy**:
```python
# tests/unit/actions/test_projection_refresh_integration.py
def test_create_action_calls_refresh():
    """Verify refresh call generated after INSERT"""

def test_refresh_function_includes_relations():
    """Verify refresh includes specified relations"""

# tests/integration/actions/test_projection_sync_db.py
def test_mutation_returns_fresh_data():
    """Integration: mutation returns data from projection"""

def test_projection_includes_relations():
    """Integration: projection includes nested relations"""
```

**Files to Modify**:
- ✅ Enhance: `src/generators/actions/step_compilers/refresh_table_view_compiler.py`
- ✅ Modify: `src/generators/actions/action_orchestrator.py` (call refresh after mutations)
- ✅ Modify: `src/core/ast_models.py` (add `ProjectionConfig` model)
- ✅ Modify: `src/core/specql_parser.py` (parse `projections` section)
- ✅ Create: `tests/unit/actions/test_projection_refresh_integration.py`
- ✅ Create: `tests/integration/actions/test_projection_sync_db.py`

**Acceptance Criteria**:
- [ ] `refresh_projection` generates refresh call after mutation
- [ ] Refresh function includes specified relations
- [ ] Mutation returns data from fresh projection
- [ ] Integration test: GraphQL queries return fresh data
- [ ] Backward compatible: entities without projections work

---

### 1.5 Hard Delete with Dependency Checking - Week 4

**Current Problem**:
```python
# src/generators/actions/step_compilers/delete_compiler.py
# Only implements soft delete
```

**Solution**:
```python
# ENHANCE: src/generators/actions/step_compilers/delete_compiler.py
class DeleteCompiler:
    """Compiles delete operations (soft or hard with dependency checking)"""

    def compile(self, step: ActionStep, entity: EntityDefinition,
                context: dict, policy: DeletePolicy) -> str:
        """
        Generate delete logic:

        1. Check dependencies if hard delete requested
        2. Block hard delete if dependencies exist
        3. Perform soft or hard delete based on policy
        """

        if policy.allow_hard_delete:
            dependency_check = self._generate_dependency_check(
                entity, policy.check_dependencies
            )
        else:
            dependency_check = ""

        return f"""
    -- Delete {entity.name}
    DECLARE
        v_hard_delete BOOLEAN := COALESCE(
            (input_payload->>'hard_delete')::BOOLEAN,
            FALSE
        );
        v_has_dependencies BOOLEAN := FALSE;
        v_dependency_details JSONB;
    BEGIN
        {dependency_check}

        -- Perform delete
        IF v_hard_delete AND NOT v_has_dependencies THEN
            -- Hard delete
            DELETE FROM {entity.schema}.tb_{entity.name.lower()}
            WHERE id = v_{entity.name.lower()}_id
              AND tenant_id = auth_tenant_id;

            RETURN app.log_and_return_mutation(
                ..., 'DELETE', 'deleted', 'Record deleted permanently', ...
            );
        ELSE
            -- Soft delete
            UPDATE {entity.schema}.tb_{entity.name.lower()}
            SET deleted_at = NOW(),
                deleted_by = auth_user_id
            WHERE id = v_{entity.name.lower()}_id
              AND tenant_id = auth_tenant_id;

            RETURN app.log_and_return_mutation(
                ..., 'UPDATE', 'soft_deleted', 'Record soft deleted', ...
            );
        END IF;
    END;
"""

    def _generate_dependency_check(self, entity: EntityDefinition,
                                   dependencies: list[DependencyCheck]) -> str:
        """Generate dependency checking code"""

        checks = []
        for dep in dependencies:
            checks.append(f"""
        -- Check {dep.entity} dependency
        IF EXISTS (
            SELECT 1 FROM {dep.entity.lower()}.tb_{dep.entity.lower()}
            WHERE {dep.field} = v_{entity.name.lower()}_id
              AND tenant_id = auth_tenant_id
              AND deleted_at IS NULL
        ) THEN
            v_has_dependencies := TRUE;
            v_dependency_details := jsonb_set(
                COALESCE(v_dependency_details, '{{}}'::JSONB),
                '{{{dep.entity}}}',
                (SELECT COUNT(*)::TEXT::JSONB
                 FROM {dep.entity.lower()}.tb_{dep.entity.lower()}
                 WHERE {dep.field} = v_{entity.name.lower()}_id)
            );
        END IF;
""")

        checks.append("""
        -- Block hard delete if dependencies exist
        IF v_hard_delete AND v_has_dependencies THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                '{entity.name.lower()}', v_{entity.name.lower()}_id,
                'NOOP', 'noop:cannot_delete_with_dependencies',
                ARRAY[]::TEXT[],
                'Cannot hard delete record with dependencies',
                NULL, NULL,
                jsonb_build_object(
                    'reason', 'has_dependencies',
                    'dependencies', v_dependency_details,
                    'suggestion', 'Use soft delete or remove dependencies first'
                )
            );
        END IF;
""")

        return '\n'.join(checks)
```

**YAML Interface**:
```yaml
# entities/tenant/machine.yaml
entity: Machine
schema: tenant

delete_policy:
  default: soft  # soft or hard
  allow_hard_delete: true
  check_dependencies:
    - entity: Allocation
      field: machine_id
      block_hard_delete: true
      error_message: "Cannot delete machine with active allocations"
    - entity: OrderLine
      field: machine_id
      block_hard_delete: true
    - entity: MachineItem
      field: machine_id
      cascade: soft_delete  # Soft delete children instead

actions:
  - name: delete_machine
    supports_hard_delete: true
    dependency_check: true
```

**Testing Strategy**:
```python
# tests/unit/actions/test_delete_compiler.py
def test_soft_delete_sets_deleted_at():
    """Verify soft delete sets deleted_at"""

def test_hard_delete_removes_row():
    """Verify hard delete generates DELETE statement"""

def test_dependency_check_generated():
    """Verify dependency checking code generated"""

# tests/integration/actions/test_delete_with_dependencies_db.py
def test_hard_delete_blocked_with_dependencies():
    """Integration: hard delete blocked when dependencies exist"""

def test_hard_delete_succeeds_without_dependencies():
    """Integration: hard delete succeeds when no dependencies"""

def test_soft_delete_always_succeeds():
    """Integration: soft delete always succeeds"""
```

**Files to Modify**:
- ✅ Enhance: `src/generators/actions/step_compilers/delete_compiler.py`
- ✅ Modify: `src/core/ast_models.py` (add `DeletePolicy`, `DependencyCheck`)
- ✅ Modify: `src/core/specql_parser.py` (parse `delete_policy`)
- ✅ Create: `tests/integration/actions/test_delete_with_dependencies_db.py`

**Acceptance Criteria**:
- [ ] Soft delete works (backward compatible)
- [ ] Hard delete generates DELETE when allowed
- [ ] Dependency checking blocks hard delete
- [ ] NOOP returned with dependency details
- [ ] Cascade options supported (soft delete children)
- [ ] Integration tests pass

---

## 📋 Phase 2: Action Pattern Library Foundation (4 weeks)

**Goal**: Build infrastructure for declarative business logic patterns

### 2.1 Pattern Library Architecture - Week 5

**Design Goals**:
1. Declarative - users specify "what" not "how"
2. Composable - patterns can be combined
3. Extensible - easy to add new patterns
4. Type-safe - validated at parse time
5. Testable - patterns have comprehensive test suites

**Directory Structure**:
```
stdlib/
├── actions/                    # Action pattern library (NEW)
│   ├── README.md              # Pattern library documentation
│   ├── crud/
│   │   ├── create.yaml        # Create pattern with duplicate check
│   │   ├── update.yaml        # Update pattern with partial updates
│   │   ├── delete.yaml        # Delete pattern with dependencies
│   │   └── upsert.yaml        # Upsert pattern
│   ├── state_machine/
│   │   ├── transition.yaml    # State transition pattern
│   │   └── validation.yaml    # State validation rules
│   ├── multi_entity/
│   │   ├── coordinated_update.yaml
│   │   └── cascade.yaml
│   ├── batch/
│   │   ├── bulk_operation.yaml
│   │   └── error_handling.yaml
│   └── common/
│       ├── identifier_recalc.yaml
│       ├── projection_refresh.yaml
│       └── audit_logging.yaml
```

**Pattern Definition Format**:
```yaml
# stdlib/actions/state_machine/transition.yaml
pattern: state_machine_transition
version: 1.0
description: "Transition entity between states with validation"
author: SpecQL Team

parameters:
  - name: from_states
    type: array<string>
    required: true
    description: "Valid source states for transition"

  - name: to_state
    type: string
    required: true
    description: "Target state"

  - name: validation_checks
    type: array<validation>
    required: false
    description: "Pre-transition validations"

  - name: side_effects
    type: array<side_effect>
    required: false
    description: "Updates to perform on success"

  - name: refresh_projection
    type: string
    required: false
    description: "Projection to refresh after transition"

template:
  steps:
    # Load current state
    - validate: |
        -- Check current state is valid for transition
        SELECT status INTO v_current_status
        FROM {{ entity.schema }}.tb_{{ entity.name | lower }}
        WHERE id = {{ input_id }}
          AND tenant_id = auth_tenant_id;

        IF v_current_status NOT IN ({{ from_states | join(', ') }}) THEN
            RETURN NOOP('validation:invalid_state_transition');
        END IF;

    # Custom validations
    {% for check in validation_checks %}
    - validate: {{ check.condition }}
      error: {{ check.error }}
    {% endfor %}

    # State transition
    - update: {{ entity.name }}
      set:
        status: {{ to_state }}
        {{ to_state }}_at: NOW()

    # Side effects
    {% for effect in side_effects %}
    {{ effect | render_side_effect }}
    {% endfor %}

    # Refresh projection
    {% if refresh_projection %}
    - refresh_table_view: {{ refresh_projection }}
    {% endif %}

examples:
  - name: decommission_machine
    description: "Decommission machine from active/maintenance to decommissioned"
    config:
      from_states: [active, maintenance]
      to_state: decommissioned
      validation_checks:
        - condition: "NOT EXISTS (SELECT 1 FROM allocation WHERE machine_id = $entity_id AND status = 'active')"
          error: "Cannot decommission machine with active allocations"
      side_effects:
        - entity: MachineItem
          update:
            status: archived
          where: "machine_id = $entity_id"
      refresh_projection: machine_projection
```

**Pattern Loader**:
```python
# NEW: src/patterns/pattern_loader.py
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

class PatternLoader:
    """Load and expand action patterns from library"""

    def __init__(self, stdlib_path: Path = Path("stdlib/actions")):
        self.stdlib_path = stdlib_path
        self.jinja_env = Environment(
            loader=FileSystemLoader(stdlib_path),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def load_pattern(self, pattern_name: str) -> PatternDefinition:
        """Load pattern definition from library"""
        pattern_path = self.stdlib_path / f"{pattern_name}.yaml"
        with open(pattern_path) as f:
            return PatternDefinition.from_yaml(yaml.safe_load(f))

    def expand_pattern(
        self,
        pattern: PatternDefinition,
        entity: EntityDefinition,
        config: dict
    ) -> list[ActionStep]:
        """Expand pattern template to action steps"""

        # Validate config against pattern parameters
        self._validate_config(pattern, config)

        # Render template with Jinja2
        template = self.jinja_env.from_string(pattern.template)
        rendered = template.render(
            entity=entity,
            config=config,
            **config
        )

        # Parse rendered YAML to action steps
        steps_data = yaml.safe_load(rendered)
        return [ActionStep.from_dict(s) for s in steps_data['steps']]

    def _validate_config(self, pattern: PatternDefinition, config: dict):
        """Validate config matches pattern parameters"""
        for param in pattern.parameters:
            if param.required and param.name not in config:
                raise ValueError(
                    f"Missing required parameter '{param.name}' for pattern '{pattern.name}'"
                )

            if param.name in config:
                value = config[param.name]
                # Type checking
                if not self._check_type(value, param.type):
                    raise TypeError(
                        f"Parameter '{param.name}' has wrong type. "
                        f"Expected {param.type}, got {type(value)}"
                    )
```

**Integration with Parser**:
```python
# MODIFY: src/core/specql_parser.py
class SpecQLParser:
    """Enhanced parser with pattern support"""

    def __init__(self):
        self.pattern_loader = PatternLoader()

    def parse(self, yaml_content: str) -> EntityDefinition:
        """Parse SpecQL YAML with pattern expansion"""
        data = yaml.safe_load(yaml_content)

        # Parse entity basics
        entity = self._parse_entity_basics(data)

        # Parse actions with pattern expansion
        entity.actions = self._parse_actions(data.get('actions', []), entity)

        return entity

    def _parse_actions(
        self,
        actions_data: list,
        entity: EntityDefinition
    ) -> list[ActionDefinition]:
        """Parse actions, expanding patterns as needed"""

        actions = []
        for action_data in actions_data:
            if 'pattern' in action_data:
                # Load and expand pattern
                pattern = self.pattern_loader.load_pattern(action_data['pattern'])
                steps = self.pattern_loader.expand_pattern(
                    pattern,
                    entity,
                    action_data.get('config', {})
                )
                action = ActionDefinition(
                    name=action_data['name'],
                    steps=steps,
                    pattern=action_data['pattern'],
                    pattern_config=action_data.get('config', {})
                )
            else:
                # Traditional step-based action
                action = self._parse_traditional_action(action_data)

            actions.append(action)

        return actions
```

**Testing Strategy**:
```python
# tests/unit/patterns/test_pattern_loader.py
def test_load_pattern_from_library():
    """Test loading pattern definition from YAML"""

def test_expand_pattern_template():
    """Test Jinja2 template expansion"""

def test_validate_pattern_config():
    """Test config validation against parameters"""

# tests/integration/patterns/test_pattern_compilation.py
def test_pattern_based_action_compiles():
    """Integration: pattern-based action compiles to SQL"""
```

**Files to Create**:
- ✅ Create: `src/patterns/pattern_loader.py`
- ✅ Create: `src/patterns/pattern_models.py` (PatternDefinition, etc.)
- ✅ Create: `stdlib/actions/crud/*.yaml`
- ✅ Create: `stdlib/actions/state_machine/*.yaml`
- ✅ Modify: `src/core/specql_parser.py` (integrate pattern loader)
- ✅ Create: `tests/unit/patterns/test_pattern_loader.py`
- ✅ Create: `tests/integration/patterns/test_pattern_compilation.py`

**Acceptance Criteria**:
- [ ] Pattern library structure created
- [ ] Pattern loader loads YAML patterns
- [ ] Jinja2 template expansion works
- [ ] Config validation works
- [ ] Parser integrates pattern expansion
- [ ] Tests pass

---

### 2.2 State Machine Pattern - Week 6

**Pattern Definition**:
```yaml
# stdlib/actions/state_machine/transition.yaml
pattern: state_machine_transition
version: 1.0
description: "Transition entity between states with validation"

parameters:
  - name: from_states
    type: array<string>
    required: true
  - name: to_state
    type: string
    required: true
  - name: validation_checks
    type: array<object>
    required: false
  - name: side_effects
    type: array<object>
    required: false
  - name: input_fields
    type: array<object>
    required: false

template: |
  steps:
    # Load and validate current state
    - raw_sql: |
        SELECT status INTO v_current_status
        FROM {{ entity.schema }}.tb_{{ entity.name | lower }}
        WHERE id = v_{{ entity.name | lower }}_id
          AND tenant_id = auth_tenant_id;

        IF v_current_status NOT IN ({% for state in from_states %}'{{ state }}'{% if not loop.last %}, {% endif %}{% endfor %}) THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                '{{ entity.name | lower }}', v_{{ entity.name | lower }}_id,
                'NOOP', 'validation:invalid_state_transition',
                ARRAY[]::TEXT[],
                format('Cannot transition from state %s to {{ to_state }}', v_current_status),
                NULL, NULL,
                jsonb_build_object(
                    'current_state', v_current_status,
                    'valid_states', ARRAY[{% for state in from_states %}'{{ state }}'{% if not loop.last %}, {% endif %}{% endfor %}],
                    'target_state', '{{ to_state }}'
                )
            );
        END IF;

    {% for check in validation_checks %}
    # Validation: {{ check.description or check.name }}
    - validate: {{ check.condition }}
      error: {{ check.error }}
    {% endfor %}

    # State transition
    - update: {{ entity.name }}
      set:
        status: '{{ to_state }}'
        {{ to_state }}_at: NOW()
        {% for field in input_fields %}
        {{ field.name }}: input_data.{{ field.name }}
        {% endfor %}

    {% for effect in side_effects %}
    # Side effect: Update {{ effect.entity }}
    - update: {{ effect.entity }}
      set:
        {% for field, value in effect.update.items() %}
        {{ field }}: {{ value }}
        {% endfor %}
      where: {{ effect.where }}
    {% endfor %}

    {% if refresh_projection %}
    # Refresh projection
    - refresh_table_view: {{ refresh_projection }}
    {% endif %}
```

**Usage Example**:
```yaml
# entities/tenant/machine.yaml
entity: Machine
schema: tenant
fields:
  status: enum(available, in_stock, allocated, decommissioned, maintenance)
  decommission_date: date
  decommission_reason: text

actions:
  - name: decommission_machine
    pattern: state_machine/transition
    config:
      from_states: [active, maintenance]
      to_state: decommissioned
      input_fields:
        - name: decommission_date
          type: date
          required: true
        - name: decommission_reason
          type: text
          required: true
      validation_checks:
        - name: no_active_allocations
          condition: |
            NOT EXISTS (
              SELECT 1 FROM tenant.tb_allocation
              WHERE machine_id = v_machine_id
                AND status = 'active'
                AND tenant_id = auth_tenant_id
            )
          error: "Cannot decommission machine with active allocations"
      side_effects:
        - entity: MachineItem
          update:
            status: archived
          where: "machine_id = v_machine_id AND tenant_id = auth_tenant_id"
        - entity: MachineEvent
          insert:
            machine_id: v_machine_id
            event_type: 'decommissioned'
            event_data: input_payload
      refresh_projection: machine_projection
```

**Generated SQL** (after pattern expansion):
```sql
CREATE OR REPLACE FUNCTION app.decommission_machine(
    auth_tenant_id UUID,
    auth_user_id UUID,
    input_payload JSONB
) RETURNS app.mutation_result AS $$
DECLARE
    input_data app.type_decommission_machine_input;
    v_machine_id UUID;
    v_current_status TEXT;
    v_updated_fields TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Convert input
    input_data := jsonb_populate_record(
        NULL::app.type_decommission_machine_input,
        input_payload
    );
    v_machine_id := input_data.id;

    -- Load and validate current state
    SELECT status INTO v_current_status
    FROM tenant.tb_machine
    WHERE id = v_machine_id
      AND tenant_id = auth_tenant_id;

    IF v_current_status NOT IN ('active', 'maintenance') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'machine', v_machine_id,
            'NOOP', 'validation:invalid_state_transition',
            ARRAY[]::TEXT[],
            format('Cannot transition from state %s to decommissioned', v_current_status),
            NULL, NULL,
            jsonb_build_object(
                'current_state', v_current_status,
                'valid_states', ARRAY['active', 'maintenance'],
                'target_state', 'decommissioned'
            )
        );
    END IF;

    -- Validation: no_active_allocations
    IF EXISTS (
        SELECT 1 FROM tenant.tb_allocation
        WHERE machine_id = v_machine_id
          AND status = 'active'
          AND tenant_id = auth_tenant_id
    ) THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'machine', v_machine_id,
            'NOOP', 'validation:has_active_allocations',
            ARRAY[]::TEXT[],
            'Cannot decommission machine with active allocations',
            NULL, NULL, NULL
        );
    END IF;

    -- State transition
    UPDATE tenant.tb_machine
    SET
        status = 'decommissioned',
        decommissioned_at = NOW(),
        decommission_date = input_data.decommission_date,
        decommission_reason = input_data.decommission_reason,
        updated_at = NOW(),
        updated_by = auth_user_id
    WHERE id = v_machine_id
      AND tenant_id = auth_tenant_id;

    v_updated_fields := ARRAY['status', 'decommission_date', 'decommission_reason'];

    -- Side effect: Update MachineItem
    UPDATE tenant.tb_machine_item
    SET
        status = 'archived',
        updated_at = NOW(),
        updated_by = auth_user_id
    WHERE machine_id = v_machine_id
      AND tenant_id = auth_tenant_id;

    -- Side effect: Insert MachineEvent
    INSERT INTO tenant.tb_machine_event (
        tenant_id, machine_id, event_type, event_data,
        created_at, created_by
    ) VALUES (
        auth_tenant_id, v_machine_id, 'decommissioned', input_payload,
        NOW(), auth_user_id
    );

    -- Refresh projection
    PERFORM tenant.refresh_machine_projection(v_machine_id, auth_tenant_id);

    -- Return success
    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'machine', v_machine_id,
        'UPDATE', 'success',
        v_updated_fields,
        'Machine decommissioned successfully',
        (SELECT data FROM tenant.v_machine_projection WHERE id = v_machine_id)::JSONB,
        NULL
    );
END;
$$;
```

**Testing Strategy**:
```python
# tests/unit/patterns/test_state_machine_pattern.py
def test_state_machine_template_expansion():
    """Test state machine pattern expands correctly"""

def test_state_machine_validation_generation():
    """Test validation checks are generated"""

def test_state_machine_side_effects():
    """Test side effects are generated"""

# tests/integration/patterns/test_state_machine_db.py
def test_decommission_machine_valid_transition():
    """Integration: valid state transition succeeds"""

def test_decommission_machine_invalid_state():
    """Integration: invalid source state returns NOOP"""

def test_decommission_machine_validation_fails():
    """Integration: validation failure returns NOOP"""

def test_decommission_machine_side_effects():
    """Integration: side effects are executed"""
```

**Files to Create**:
- ✅ Create: `stdlib/actions/state_machine/transition.yaml`
- ✅ Create: `tests/unit/patterns/test_state_machine_pattern.py`
- ✅ Create: `tests/integration/patterns/test_state_machine_db.py`
- ✅ Create: Example YAML using state machine pattern

**Acceptance Criteria**:
- [ ] State machine pattern YAML created
- [ ] Template expansion generates correct SQL
- [ ] State validation works
- [ ] Side effects execute
- [ ] Integration tests pass
- [ ] Example entity uses pattern successfully

---

### 2.3 Multi-Entity Operation Pattern - Week 7

**Pattern Definition**:
```yaml
# stdlib/actions/multi_entity/coordinated_update.yaml
pattern: multi_entity_operation
version: 1.0
description: "Coordinate changes across multiple entities in a transaction"

parameters:
  - name: primary_entity
    type: string
    required: true
  - name: operations
    type: array<operation>
    required: true
  - name: transaction_scope
    type: enum[serializable, repeatable_read, read_committed]
    default: serializable
  - name: rollback_on_error
    type: boolean
    default: true

template: |
  steps:
    {% for op in operations %}

    {% if op.action == 'get_or_create' %}
    # Get or create {{ op.entity }}
    - raw_sql: |
        SELECT id INTO v_{{ op.store_as or (op.entity | lower) }}_id
        FROM {{ op.entity | schema_for }}.tb_{{ op.entity | lower }}
        WHERE {% for field, value in op.where.items() %}{{ field }} = {{ value }}{% if not loop.last %} AND {% endif %}{% endfor %}
          AND tenant_id = auth_tenant_id
          AND deleted_at IS NULL;

        IF v_{{ op.store_as or (op.entity | lower) }}_id IS NULL THEN
            INSERT INTO {{ op.entity | schema_for }}.tb_{{ op.entity | lower }} (
                {% for field in op.create_if_missing.keys() %}{{ field }}{% if not loop.last %}, {% endif %}{% endfor %},
                created_at, created_by, tenant_id
            ) VALUES (
                {% for value in op.create_if_missing.values() %}{{ value }}{% if not loop.last %}, {% endif %}{% endfor %},
                NOW(), auth_user_id, auth_tenant_id
            ) RETURNING id INTO v_{{ op.store_as or (op.entity | lower) }}_id;
        END IF;

    {% elif op.action == 'insert' %}
    # Insert {{ op.entity }}
    - insert: {{ op.entity }}
      fields:
        {% for field, value in op.values.items() %}
        {{ field }}: {{ value }}
        {% endfor %}
      {% if op.store_as %}
      store_id_as: v_{{ op.store_as }}
      {% endif %}

    {% elif op.action == 'update' %}
    # Update {{ op.entity }}
    - update: {{ op.entity }}
      set:
        {% for field, value in op.values.items() %}
        {{ field }}: {{ value }}
        {% endfor %}
      where: {{ op.where | format_where }}

    {% endif %}

    {% endfor %}

    {% if refresh_projections %}
    # Refresh projections
    {% for projection in refresh_projections %}
    - refresh_table_view: {{ projection }}
    {% endfor %}
    {% endif %}
```

**Usage Example**:
```yaml
# entities/tenant/allocation.yaml
entity: Allocation
schema: tenant

actions:
  - name: allocate_to_stock
    pattern: multi_entity/coordinated_update
    description: "Allocate machine to stock location"
    config:
      primary_entity: Machine
      operations:
        # Get or create stock location
        - action: get_or_create
          entity: Location
          where:
            code: 'STOCK'
            tenant_id: $auth_tenant_id
          create_if_missing:
            code: STOCK
            name: Stock
            location_type: warehouse
          store_as: stock_location_id

        # Create allocation
        - action: insert
          entity: Allocation
          values:
            machine_id: $input_data.machine_id
            location_id: $stock_location_id
            allocation_type: stock
            status: active
            allocated_at: NOW()
          store_as: allocation_id

        # Update machine status
        - action: update
          entity: Machine
          where:
            id: $input_data.machine_id
          values:
            status: in_stock
            current_location_id: $stock_location_id

        # Log event
        - action: insert
          entity: AllocationEvent
          values:
            allocation_id: $allocation_id
            event_type: allocated_to_stock
            event_data: $input_payload

      refresh_projections:
        - machine_projection
        - allocation_projection

      return_entity: Allocation
      return_id: $allocation_id
```

**Testing Strategy**:
```python
# tests/unit/patterns/test_multi_entity_pattern.py
def test_multi_entity_template_expansion():
    """Test multi-entity pattern expands correctly"""

def test_get_or_create_logic():
    """Test get_or_create generates correct SQL"""

# tests/integration/patterns/test_multi_entity_db.py
def test_allocate_to_stock_creates_location():
    """Integration: creates stock location if missing"""

def test_allocate_to_stock_uses_existing_location():
    """Integration: uses existing stock location"""

def test_allocate_to_stock_updates_machine():
    """Integration: machine status updated"""

def test_allocate_to_stock_transaction_rollback():
    """Integration: transaction rolls back on error"""
```

**Files to Create**:
- ✅ Create: `stdlib/actions/multi_entity/coordinated_update.yaml`
- ✅ Create: `tests/unit/patterns/test_multi_entity_pattern.py`
- ✅ Create: `tests/integration/patterns/test_multi_entity_db.py`

**Acceptance Criteria**:
- [ ] Multi-entity pattern created
- [ ] Get-or-create logic works
- [ ] Multiple operations coordinated
- [ ] Transaction management works
- [ ] Integration tests pass

---

### 2.4 Batch Operation Pattern - Week 8

**Pattern Definition**:
```yaml
# stdlib/actions/batch/bulk_operation.yaml
pattern: batch_operation
version: 1.0
description: "Process multiple records in a single transaction"

parameters:
  - name: batch_input
    type: string
    required: true
    description: "Field name containing array of items"
  - name: operation
    type: object
    required: true
  - name: error_handling
    type: enum[stop_on_error, continue_on_error, rollback_on_any_error]
    default: continue_on_error
  - name: batch_size
    type: integer
    default: 100
  - name: return_summary
    type: object
    required: true

template: |
  steps:
    - raw_sql: |
        DECLARE
            v_item JSONB;
            v_updated_count INTEGER := 0;
            v_failed_count INTEGER := 0;
            v_failed_items JSONB := '[]'::JSONB;
        BEGIN
            -- Iterate over batch items
            FOR v_item IN
                SELECT * FROM jsonb_array_elements(input_data.{{ batch_input }})
            LOOP
                BEGIN
                    {% if operation.action == 'update' %}
                    -- Update {{ operation.entity }}
                    UPDATE {{ operation.entity | schema_for }}.tb_{{ operation.entity | lower }}
                    SET
                        {% for field, value in operation.set.items() %}
                        {{ field }} = (v_item->>'{{ value | trim_prefix('$item.') }}')::{{ field | type_for }},
                        {% endfor %}
                        updated_at = NOW(),
                        updated_by = auth_user_id
                    WHERE {{ operation.where | format_where_with_item }}
                      AND tenant_id = auth_tenant_id;

                    IF FOUND THEN
                        v_updated_count := v_updated_count + 1;
                    ELSE
                        v_failed_count := v_failed_count + 1;
                        v_failed_items := v_failed_items || jsonb_build_object(
                            'id', v_item->>'id',
                            'reason', 'not_found'
                        );
                    END IF;
                    {% endif %}

                {% if error_handling == 'continue_on_error' %}
                EXCEPTION WHEN OTHERS THEN
                    v_failed_count := v_failed_count + 1;
                    v_failed_items := v_failed_items || jsonb_build_object(
                        'id', v_item->>'id',
                        'reason', SQLERRM
                    );
                {% endif %}
                END;
            END LOOP;

            {% if refresh_projections %}
            -- Refresh projections
            {% for projection in refresh_projections %}
            PERFORM {{ entity.schema }}.refresh_{{ projection }}(auth_tenant_id);
            {% endfor %}
            {% endif %}

            -- Return summary
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                '{{ operation.entity | lower }}',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'BATCH_UPDATE',
                'success',
                ARRAY[]::TEXT[],
                format('Updated %s records, %s failed', v_updated_count, v_failed_count),
                NULL,
                jsonb_build_object(
                    {% for key, expr in return_summary.items() %}
                    '{{ key }}', {{ expr }}{% if not loop.last %},{% endif %}
                    {% endfor %}
                )
            );
        END;
```

**Usage Example**:
```yaml
# entities/tenant/contract_item.yaml
actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    description: "Update prices for multiple contract items"
    config:
      batch_input: price_updates
      operation:
        action: update
        entity: ContractItem
        set:
          unit_price: $item.unit_price
        where:
          id: $item.id
          tenant_id: $auth_tenant_id
      error_handling: continue_on_error
      refresh_projections:
        - contract_projection
      return_summary:
        updated_count: v_updated_count
        failed_count: v_failed_count
        failed_items: v_failed_items
```

**Testing Strategy**:
```python
# tests/unit/patterns/test_batch_pattern.py
def test_batch_pattern_expansion():
    """Test batch pattern expands correctly"""

def test_batch_error_handling():
    """Test error handling modes"""

# tests/integration/patterns/test_batch_db.py
def test_bulk_update_all_succeed():
    """Integration: all updates succeed"""

def test_bulk_update_some_fail():
    """Integration: some fail, others succeed"""

def test_bulk_update_summary():
    """Integration: summary includes counts"""
```

**Files to Create**:
- ✅ Create: `stdlib/actions/batch/bulk_operation.yaml`
- ✅ Create: `tests/unit/patterns/test_batch_pattern.py`
- ✅ Create: `tests/integration/patterns/test_batch_db.py`

**Acceptance Criteria**:
- [ ] Batch pattern created
- [ ] Error handling modes work
- [ ] Summary generation works
- [ ] Integration tests pass

---

## 📋 Phase 3: PrintOptim Migration & Documentation (3 weeks)

### 3.1 Reference Implementation Migration - Week 9-10

**Goal**: Express PrintOptim's reference implementation in SpecQL YAML

**Migration Strategy**:

1. **Identify Reference Patterns** (Week 9, Day 1-2)
   ```bash
   # Analyze PrintOptim reference SQL
   - Count state machine transitions
   - Count multi-entity operations
   - Count batch operations
   - Identify unique patterns not yet supported
   ```

2. **Migrate Core Entities** (Week 9, Day 3-5)
   ```yaml
   # Migrate in order:
   - Contract (CRUD + duplicate detection)
   - Machine (state machine + hard delete)
   - Allocation (multi-entity operation)
   - ContractItem (batch operations)
   ```

3. **Create Migration Examples** (Week 10, Day 1-3)
   ```
   docs/migration/
   ├── printoptim_to_specql.md
   ├── examples/
   │   ├── contract_migration.md
   │   ├── machine_migration.md
   │   ├── allocation_migration.md
   │   └── batch_operations_migration.md
   ```

4. **Verification** (Week 10, Day 4-5)
   ```python
   # Compare generated SQL to reference SQL
   def test_generated_matches_reference():
       """Verify SpecQL generates equivalent SQL to PrintOptim"""
   ```

**Acceptance Criteria**:
- [ ] All PrintOptim CRUD patterns expressible in SpecQL
- [ ] All PrintOptim business actions expressible in SpecQL
- [ ] Generated SQL functionally equivalent to reference
- [ ] Migration guide complete
- [ ] Examples documented

---

### 3.2 Documentation & Examples - Week 11

**Documentation Structure**:

```
docs/
├── patterns/
│   ├── README.md                    # Pattern library overview
│   ├── getting_started.md           # Quick start guide
│   ├── crud_patterns.md             # CRUD pattern documentation
│   ├── state_machine.md             # State machine pattern
│   ├── multi_entity.md              # Multi-entity operations
│   ├── batch_operations.md          # Batch operations
│   └── custom_patterns.md           # Creating custom patterns
├── migration/
│   ├── printoptim_to_specql.md      # Migration guide
│   └── examples/                    # Migration examples
└── api/
    ├── pattern_library_api.md       # Pattern library API reference
    └── yaml_reference.md            # Complete YAML reference
```

**Key Documents**:

1. **Pattern Library Getting Started** (`docs/patterns/getting_started.md`)
   ```markdown
   # Getting Started with Action Patterns

   ## What are Action Patterns?

   Action patterns are reusable templates for common business logic...

   ## Your First Pattern

   ```yaml
   entity: Contact
   actions:
     - name: qualify_lead
       pattern: state_machine/transition
       config:
         from_states: [lead]
         to_state: qualified
   ```

   ## Available Patterns

   - CRUD patterns
   - State machine patterns
   - Multi-entity patterns
   - Batch operations
   ...
   ```

2. **PrintOptim Migration Guide** (`docs/migration/printoptim_to_specql.md`)
   ```markdown
   # Migrating from PrintOptim SQL to SpecQL

   ## Overview

   This guide shows how to express PrintOptim's reference implementation...

   ## Pattern Mapping

   | PrintOptim SQL Pattern | SpecQL Pattern | Example |
   |------------------------|----------------|---------|
   | State transition       | state_machine/transition | [link] |
   | Multi-entity op        | multi_entity/coordinated | [link] |
   | Batch update           | batch/bulk_operation | [link] |

   ## Step-by-Step Migration

   ### 1. Identify Your SQL Pattern
   ### 2. Choose Corresponding SpecQL Pattern
   ### 3. Express in YAML
   ### 4. Verify Generated SQL
   ...
   ```

**Example Entities**:

```
entities/examples/
├── simple/
│   ├── contact.yaml             # Basic CRUD
│   └── company.yaml             # With relationships
├── patterns/
│   ├── machine.yaml             # State machine
│   ├── allocation.yaml          # Multi-entity
│   ├── contract_item.yaml       # Batch operations
│   └── order.yaml               # Complex workflow
└── printoptim/
    ├── contract.yaml            # Full PrintOptim reference
    ├── machine.yaml
    └── allocation.yaml
```

**Acceptance Criteria**:
- [ ] Complete pattern library documentation
- [ ] Migration guide written
- [ ] 10+ example entities
- [ ] API reference complete
- [ ] Quick start guide tested

---

## 📋 Phase 4: Testing & Polish (2-3 weeks)

### 4.1 Comprehensive Test Suite - Week 12

**Test Coverage Goals**:
- Unit tests: 95%+
- Integration tests: All patterns
- End-to-end tests: PrintOptim examples

**Test Organization**:

```python
tests/
├── unit/
│   ├── patterns/
│   │   ├── test_pattern_loader.py
│   │   ├── test_state_machine_pattern.py
│   │   ├── test_multi_entity_pattern.py
│   │   └── test_batch_pattern.py
│   ├── actions/
│   │   ├── test_partial_update_compiler.py
│   │   ├── test_duplicate_check_compiler.py
│   │   ├── test_identifier_recalc_integration.py
│   │   ├── test_projection_refresh_integration.py
│   │   └── test_delete_compiler.py
│   └── ...
├── integration/
│   ├── patterns/
│   │   ├── test_state_machine_db.py
│   │   ├── test_multi_entity_db.py
│   │   └── test_batch_db.py
│   ├── actions/
│   │   ├── test_partial_updates_db.py
│   │   ├── test_duplicate_detection_db.py
│   │   ├── test_identifier_recalc_db.py
│   │   ├── test_projection_sync_db.py
│   │   └── test_delete_with_dependencies_db.py
│   └── printoptim/
│       ├── test_contract_crud.py
│       ├── test_machine_lifecycle.py
│       └── test_allocation_workflow.py
└── e2e/
    ├── test_printoptim_reference.py
    └── test_full_backend_generation.py
```

**Key Test Scenarios**:

```python
# tests/e2e/test_printoptim_reference.py
def test_generate_complete_printoptim_backend():
    """
    End-to-end test:
    1. Load all PrintOptim entity YAMLs
    2. Generate complete SQL migration
    3. Apply to test database
    4. Verify all functions exist and work
    5. Run business logic tests
    """

def test_contract_full_lifecycle():
    """Test complete contract lifecycle with patterns"""
    # 1. Create contract (with duplicate detection)
    # 2. Update contract (with partial updates)
    # 3. Add contract items (batch operation)
    # 4. Close contract (state machine)
    # 5. Delete contract (with dependency check)

def test_machine_allocation_workflow():
    """Test complex multi-entity workflow"""
    # 1. Create machine
    # 2. Allocate to stock (multi-entity)
    # 3. Allocate to customer (state transition)
    # 4. Decommission (state machine with side effects)
```

**Acceptance Criteria**:
- [ ] 95%+ unit test coverage
- [ ] All patterns have integration tests
- [ ] PrintOptim examples have e2e tests
- [ ] Performance benchmarks pass
- [ ] All 439 existing tests still pass

---

### 4.2 Performance & Optimization - Week 13

**Performance Goals**:
1. Pattern expansion: <100ms per action
2. SQL generation: <500ms per entity
3. Full backend generation: <5s for 50 entities

**Optimization Areas**:

1. **Pattern Template Caching**
   ```python
   class PatternLoader:
       def __init__(self):
           self._template_cache = {}

       def load_pattern(self, name: str) -> PatternDefinition:
           if name not in self._template_cache:
               self._template_cache[name] = self._load_from_file(name)
           return self._template_cache[name]
   ```

2. **Jinja2 Template Compilation**
   ```python
   class PatternExpander:
       def __init__(self):
           self.jinja_env = Environment(
               ...,
               cache_size=400,  # Cache compiled templates
               auto_reload=False  # Disable auto-reload in production
           )
   ```

3. **Parallel Entity Processing**
   ```python
   def generate_schemas_parallel(entities: list[EntityDefinition]) -> list[str]:
       """Generate schemas in parallel"""
       with multiprocessing.Pool() as pool:
           return pool.map(generate_schema, entities)
   ```

**Benchmarking**:

```python
# tests/performance/test_pattern_expansion.py
def test_pattern_expansion_performance():
    """Verify pattern expansion meets performance goals"""
    start = time.time()
    for _ in range(100):
        expand_pattern(pattern, entity, config)
    elapsed = time.time() - start
    assert elapsed / 100 < 0.1  # <100ms per expansion

# tests/performance/test_full_generation.py
def test_printoptim_generation_performance():
    """Verify full PrintOptim backend generates in <5s"""
    start = time.time()
    generate_complete_backend(printoptim_entities)
    elapsed = time.time() - start
    assert elapsed < 5.0
```

**Acceptance Criteria**:
- [ ] Pattern expansion <100ms
- [ ] SQL generation <500ms per entity
- [ ] Full backend generation <5s for 50 entities
- [ ] Memory usage <500MB for large projects
- [ ] Benchmarks documented

---

### 4.3 Final Polish & Release Prep - Week 14

**Polish Checklist**:

1. **Error Messages**
   - [ ] Clear error messages for pattern validation
   - [ ] Helpful suggestions when config invalid
   - [ ] Good error messages for template expansion failures

2. **Developer Experience**
   - [ ] Pattern validation in IDE (JSON schema)
   - [ ] Auto-complete for pattern names
   - [ ] Inline documentation in YAML

3. **CLI Enhancements**
   - [ ] `specql patterns list` - list available patterns
   - [ ] `specql patterns validate` - validate pattern usage
   - [ ] `specql patterns doc <name>` - show pattern documentation

4. **Backward Compatibility**
   - [ ] Existing step-based actions still work
   - [ ] No breaking changes to existing APIs
   - [ ] Migration path for existing projects

5. **Release Notes**
   ```markdown
   # SpecQL v2.0 - Complete Mutation Pattern Library

   ## 🚀 New Features

   ### Core CRUD Enhancements
   - ✅ Partial updates (PATCH semantics)
   - ✅ Duplicate detection with structured errors
   - ✅ Identifier recalculation (Trinity pattern)
   - ✅ GraphQL projection sync
   - ✅ Hard delete with dependency checking

   ### Action Pattern Library
   - ✅ State machine patterns
   - ✅ Multi-entity operation patterns
   - ✅ Batch operation patterns
   - ✅ Declarative business logic

   ## 📚 PrintOptim Integration
   - ✅ Complete reference implementation expressible in YAML
   - ✅ Migration guide and examples
   - ✅ 100% production-ready SQL generation

   ## 🔧 Breaking Changes
   - None! Fully backward compatible

   ## 📖 Documentation
   - Complete pattern library documentation
   - Migration guide from PrintOptim SQL
   - 10+ example entities
   - API reference
   ```

**Acceptance Criteria**:
- [ ] Error messages reviewed and improved
- [ ] CLI enhancements complete
- [ ] Backward compatibility verified
- [ ] Release notes written
- [ ] Ready for production use

---

## 🎯 Success Metrics

### Quantitative Metrics

1. **Code Generation Leverage**
   - Target: 20 lines YAML → 2000+ lines SQL (100x)
   - Measure: Average YAML:SQL ratio across PrintOptim examples

2. **Test Coverage**
   - Unit tests: 95%+
   - Integration tests: All patterns
   - E2E tests: PrintOptim reference

3. **Performance**
   - Pattern expansion: <100ms
   - Full backend generation: <5s for 50 entities

4. **Adoption (PrintOptim Team)**
   - Can express 100% of their backend in SpecQL
   - Migration complete in <2 weeks
   - SQL generation matches reference implementation

### Qualitative Metrics

1. **Developer Experience**
   - Clear, intuitive YAML syntax
   - Helpful error messages
   - Good documentation

2. **Production Readiness**
   - Generated SQL passes PrintOptim's production requirements
   - No manual SQL needed for common patterns
   - Edge cases handled correctly

3. **Maintainability**
   - Easy to add new patterns
   - Pattern library well-organized
   - Examples cover common use cases

---

## 🚧 Risks & Mitigation

### Risk 1: Pattern Library Complexity

**Risk**: Pattern library becomes too complex, hard to maintain

**Mitigation**:
- Start with 3-4 core patterns
- Add patterns incrementally based on real needs
- Keep patterns focused and composable
- Comprehensive tests for each pattern

### Risk 2: Jinja2 Template Debugging

**Risk**: Template errors hard to debug

**Mitigation**:
- Add template validation before expansion
- Generate helpful error messages with line numbers
- Provide pattern testing utilities
- Document common template issues

### Risk 3: Backward Compatibility

**Risk**: New features break existing projects

**Mitigation**:
- All new features opt-in
- Existing step-based actions still work
- Comprehensive backward compatibility tests
- Clear migration guide

### Risk 4: Performance Regression

**Risk**: Pattern expansion slows down generation

**Mitigation**:
- Performance benchmarks for all new features
- Template caching
- Parallel processing where possible
- Profile and optimize hot paths

### Risk 5: PrintOptim-Specific Requirements

**Risk**: PrintOptim needs features not in patterns

**Mitigation**:
- Support custom step-based actions alongside patterns
- Allow pattern extension/customization
- Escape hatch for raw SQL when needed
- Iterative approach: start with 80% coverage

---

## 📅 Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|-----------------|
| **Phase 1: Core CRUD** | 4 weeks | Partial updates, duplicate detection, identifier recalc, projection sync, hard delete |
| **Phase 2: Pattern Library** | 4 weeks | Pattern loader, state machine, multi-entity, batch patterns |
| **Phase 3: Migration & Docs** | 3 weeks | PrintOptim migration, documentation, examples |
| **Phase 4: Testing & Polish** | 2-3 weeks | Test suite, performance optimization, release prep |
| **Total** | **13-14 weeks** | **Complete mutation pattern library** |

---

## 🎯 Definition of Done

The enhancement is complete when:

- [ ] All 6 core CRUD gaps implemented
- [ ] All 6 gap acceptance criteria met
- [ ] Pattern library infrastructure complete
- [ ] 3+ core patterns implemented (state machine, multi-entity, batch)
- [ ] PrintOptim reference implementation expressible in SpecQL YAML
- [ ] Migration guide complete
- [ ] 10+ example entities
- [ ] Test coverage 95%+
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Release notes written
- [ ] PrintOptim team can migrate in <2 weeks

---

## 🤝 PrintOptim Team Support

### What PrintOptim Gets

1. **Immediate Value** (Phase 1 complete)
   - Partial updates for their update mutations
   - Duplicate detection for their create mutations
   - Identifier recalculation for Trinity pattern
   - Projection sync for GraphQL
   - Hard delete for data cleanup

2. **Business Logic as Code** (Phase 2 complete)
   - Express complex workflows in YAML
   - No more manual PL/pgSQL writing
   - Consistent patterns across backend
   - Easy to review and maintain

3. **Migration Support** (Phase 3)
   - Detailed migration guide
   - Reference examples
   - Side-by-side SQL comparison
   - Support during migration

4. **Long-term Benefits**
   - Faster feature development
   - Consistent code quality
   - Easy onboarding for new developers
   - Type-safe business logic

### Migration Timeline for PrintOptim

**Week 1**: Core CRUD migration
- Migrate Contact, Company (basic CRUD)
- Verify partial updates work
- Verify duplicate detection works

**Week 2**: Business actions migration
- Migrate Machine (state machine)
- Migrate Allocation (multi-entity)
- Migrate batch operations

**Week 3+**: Advanced features & polish
- Custom patterns as needed
- Performance optimization
- Production deployment

---

## 📞 Next Steps

1. **Review & Feedback**
   - PrintOptim team reviews this plan
   - Identify any missing requirements
   - Prioritize phases if needed

2. **Kickoff**
   - Set up bi-weekly check-ins
   - Identify PrintOptim point of contact
   - Agree on success criteria

3. **Phase 1 Start**
   - Begin with partial updates (Week 1)
   - Early feedback from PrintOptim
   - Iterate based on real usage

---

**Questions? Comments?** Please comment on Issue #4 or contact the SpecQL team.
