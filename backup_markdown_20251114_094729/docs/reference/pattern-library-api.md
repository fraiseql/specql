# Pattern Library API Reference

Complete reference for all SpecQL action patterns, including configuration parameters, generated SQL, and usage examples.

## Overview

SpecQL provides a comprehensive library of reusable business logic patterns that transform declarative YAML configuration into production-ready PostgreSQL functions. This reference documents all available patterns and their APIs.

## Pattern Categories

### CRUD Patterns

Basic Create, Read, Update, Delete operations with enhanced features.

#### `crud/create`

Creates new entity records with duplicate detection and automatic identifier generation.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `duplicate_check` | object | No | Duplicate detection configuration |
| `duplicate_check.fields` | array | Yes* | Fields to check for duplicates |
| `duplicate_check.error_message` | string | No | Custom error message (default: "Record already exists") |
| `duplicate_check.return_conflict_object` | boolean | No | Return conflicting record in error (default: true) |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.create_entity(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_entity_id uuid;
    v_conflict_record jsonb;
BEGIN
    -- Duplicate check (if configured)
    SELECT row_to_json(t) INTO v_conflict_record
    FROM schema.tb_entity t
    WHERE t.field1 = input_data->>'field1'
      AND t.field2 = input_data->>'field2';

    IF v_conflict_record IS NOT NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', NULL, 'NOOP', 'validation:duplicate_found',
            ARRAY[]::TEXT[], 'Record already exists', NULL, NULL,
            v_conflict_record
        );
    END IF;

    -- Insert record
    INSERT INTO schema.tb_entity (
        tenant_id, created_by, created_at,
        field1, field2, ...
    ) VALUES (
        auth_tenant_id, auth_user_id, now(),
        input_data->>'field1', input_data->>'field2', ...
    ) RETURNING id INTO v_entity_id;

    -- Identifier recalculation (if entity has identifiers)
    PERFORM schema.recalcid_entity(v_entity_id, auth_tenant_id, auth_user_id);

    -- Projection refresh (if configured)
    PERFORM app.refresh_table_view('entity_projection');

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', v_entity_id, 'CREATE', 'success',
        ARRAY[]::TEXT[], 'Entity created successfully', NULL, NULL, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
        error_message: "Contract already exists for this customer"
        return_conflict_object: true
```

**Error Codes:**
- `validation:duplicate_found` - Duplicate record detected

---

#### `crud/update`

Updates existing entity records with partial update support and field change tracking.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partial_updates` | boolean | No | Enable CASE-based partial updates (default: true) |
| `track_updated_fields` | boolean | No | Track which fields were changed (default: false) |
| `allowed_fields` | array | No | Restrict which fields can be updated |
| `required_fields` | array | No | Fields that must be provided for update |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.update_entity(entity_id uuid, user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_updated_fields text[];
    v_old_record jsonb;
    v_new_record jsonb;
BEGIN
    -- Get current record
    SELECT row_to_json(t) INTO v_old_record
    FROM schema.tb_entity t
    WHERE t.id = entity_id AND t.tenant_id = auth_tenant_id;

    IF v_old_record IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:record_not_found',
            ARRAY[]::TEXT[], 'Entity not found', NULL, NULL, NULL
        );
    END IF;

    -- Build update query with CASE expressions
    UPDATE schema.tb_entity SET
        updated_by = auth_user_id,
        updated_at = now(),
        field1 = CASE WHEN input_data ? 'field1'
                     THEN input_data->>'field1' ELSE field1 END,
        field2 = CASE WHEN input_data ? 'field2'
                     THEN input_data->>'field2' ELSE field2 END
    WHERE id = entity_id AND tenant_id = auth_tenant_id;

    -- Track changed fields (if enabled)
    SELECT array_agg(field_name) INTO v_updated_fields
    FROM jsonb_object_keys(input_data) as field_name;

    -- Get updated record
    SELECT row_to_json(t) INTO v_new_record
    FROM schema.tb_entity t
    WHERE t.id = entity_id;

    -- Identifier recalculation (if entity has identifiers)
    PERFORM schema.recalcid_entity(entity_id, auth_tenant_id, auth_user_id);

    -- Projection refresh (if configured)
    PERFORM app.refresh_table_view('entity_projection');

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', entity_id, 'UPDATE', 'success',
        v_updated_fields, 'Entity updated successfully',
        v_old_record, v_new_record, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: update_contract
    pattern: crud/update
    config:
      partial_updates: true
      track_updated_fields: true
      allowed_fields: [title, description, total_value, status]
```

**Error Codes:**
- `validation:record_not_found` - Entity not found

---

#### `crud/delete`

Deletes entity records with dependency checking and soft/hard delete support.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supports_hard_delete` | boolean | No | Allow permanent deletion (default: false) |
| `check_dependencies` | array | No | Dependency validation rules |
| `check_dependencies[].entity` | string | Yes* | Dependent entity name |
| `check_dependencies[].field` | string | Yes* | Foreign key field |
| `check_dependencies[].block_hard_delete` | boolean | No | Prevent hard delete if dependencies exist |
| `check_dependencies[].error_message` | string | No | Custom error message |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.delete_entity(entity_id uuid, user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_hard_delete boolean := input_data->>'hard_delete' = 'true';
    v_old_record jsonb;
BEGIN
    -- Get current record
    SELECT row_to_json(t) INTO v_old_record
    FROM schema.tb_entity t
    WHERE t.id = entity_id AND t.tenant_id = auth_tenant_id;

    IF v_old_record IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:record_not_found',
            ARRAY[]::TEXT[], 'Entity not found', NULL, NULL, NULL
        );
    END IF;

    -- Check dependencies
    IF EXISTS (SELECT 1 FROM schema.tb_dependent
               WHERE dependent_field = entity_id AND tenant_id = auth_tenant_id) THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:dependencies_exist',
            ARRAY[]::TEXT[], 'Cannot delete entity with existing dependencies',
            NULL, NULL, NULL
        );
    END IF;

    -- Perform deletion
    IF v_hard_delete THEN
        DELETE FROM schema.tb_entity
        WHERE id = entity_id AND tenant_id = auth_tenant_id;
    ELSE
        UPDATE schema.tb_entity SET
            deleted_at = now(),
            deleted_by = auth_user_id,
            is_deleted = true
        WHERE id = entity_id AND tenant_id = auth_tenant_id;
    END IF;

    -- Projection refresh (if configured)
    PERFORM app.refresh_table_view('entity_projection');

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', entity_id, 'DELETE', 'success',
        ARRAY[]::TEXT[], 'Entity deleted successfully',
        v_old_record, NULL, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: delete_contract
    pattern: crud/delete
    config:
      supports_hard_delete: true
      check_dependencies:
        - entity: ContractItem
          field: contract_id
          block_hard_delete: true
          error_message: "Cannot delete contract with associated items"
```

**Error Codes:**
- `validation:record_not_found` - Entity not found
- `validation:dependencies_exist` - Cannot delete due to dependencies

---

### State Machine Patterns

Patterns for managing entity state transitions with validation and side effects.

#### `state_machine/transition`

Simple state transitions with validation and side effects.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_states` | array | Yes | Valid source states for transition |
| `to_state` | string | Yes | Target state |
| `validation_checks` | array | No | Pre-transition validation rules |
| `validation_checks[].condition` | string | Yes* | SQL condition to validate |
| `validation_checks[].error` | string | Yes* | Error code/message |
| `side_effects` | array | No | Operations to perform on success |
| `input_fields` | array | No | Additional fields to set |
| `refresh_projection` | string | No | Projection to refresh |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.transition_entity(entity_id uuid, user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_current_status text;
    v_old_record jsonb;
    v_new_record jsonb;
BEGIN
    -- Get current state
    SELECT status, row_to_json(t) INTO v_current_status, v_old_record
    FROM schema.tb_entity t
    WHERE t.id = entity_id AND t.tenant_id = auth_tenant_id;

    -- Validate transition
    IF v_current_status NOT IN ('state1', 'state2') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:invalid_state_transition',
            ARRAY[]::TEXT[], 'Invalid state transition', NULL, NULL,
            jsonb_build_object('current_state', v_current_status, 'target_state', 'new_state')
        );
    END IF;

    -- Pre-transition validations
    -- [validation logic here]

    -- Perform transition
    UPDATE schema.tb_entity SET
        status = 'new_state',
        updated_by = auth_user_id,
        updated_at = now()
        -- Additional input fields
    WHERE id = entity_id AND tenant_id = auth_tenant_id;

    -- Side effects
    -- [side effect operations here]

    -- Projection refresh
    PERFORM app.refresh_table_view('entity_projection');

    -- Get updated record
    SELECT row_to_json(t) INTO v_new_record
    FROM schema.tb_entity t
    WHERE t.id = entity_id;

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', entity_id, 'UPDATE', 'success',
        ARRAY['status'], 'State transition completed',
        v_old_record, v_new_record, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: approve_contract
    pattern: state_machine/transition
    config:
      from_states: [submitted, pending_review]
      to_state: approved
      validation_checks:
        - condition: "total_value <= 10000"
          error: "value_exceeds_approval_limit"
      side_effects:
        - entity: ContractEvent
          insert:
            contract_id: v_contract_id
            event_type: approved
            event_data: input_data
      input_fields:
        - name: approved_by
          type: uuid
        - name: approval_date
          type: timestamp
```

**Error Codes:**
- `validation:invalid_state_transition` - Invalid state transition attempted

---

#### `state_machine/guarded_transition`

Complex state transitions with guard conditions for business rules.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_states` | array | Yes | Valid source states |
| `to_state` | string | Yes | Target state |
| `guards` | array | Yes | Business rule conditions |
| `guards[].name` | string | No | Guard identifier |
| `guards[].condition` | string | Yes* | SQL condition |
| `guards[].error` | string | Yes* | Error when guard fails |
| `side_effects` | array | No | Success operations |
| `input_fields` | array | No | Additional fields |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.guarded_transition_entity(entity_id uuid, user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_current_status text;
BEGIN
    -- Get current state
    SELECT status INTO v_current_status
    FROM schema.tb_entity t
    WHERE t.id = entity_id AND t.tenant_id = auth_tenant_id;

    -- Validate transition is allowed
    IF v_current_status NOT IN ('state1', 'state2') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:invalid_state_transition',
            ARRAY[]::TEXT[], 'Invalid state transition', NULL, NULL, NULL
        );
    END IF;

    -- Evaluate guards
    -- Guard 1: [condition evaluation]
    IF NOT (condition1) THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', entity_id, 'NOOP', 'validation:guard_failed',
            ARRAY[]::TEXT[], 'Guard condition failed: guard1', NULL, NULL, NULL
        );
    END IF;

    -- Guard 2: [condition evaluation]
    -- [additional guards]

    -- Perform transition
    UPDATE schema.tb_entity SET
        status = 'new_state',
        updated_by = auth_user_id,
        updated_at = now()
    WHERE id = entity_id AND tenant_id = auth_tenant_id;

    -- Side effects
    -- [side effect operations]

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', entity_id, 'UPDATE', 'success',
        ARRAY['status'], 'Guarded transition completed', NULL, NULL, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: approve_large_contract
    pattern: state_machine/guarded_transition
    config:
      from_states: [submitted]
      to_state: approved
      guards:
        - name: budget_available
          condition: "total_value <= (SELECT budget FROM departments WHERE id = department_id)"
          error: "insufficient_budget"
        - name: manager_approval
          condition: "EXISTS (SELECT 1 FROM approvals WHERE contract_id = v_contract_id AND approved = true)"
          error: "manager_approval_required"
      side_effects:
        - entity: Department
          update:
            used_budget: "used_budget + total_value"
          where: "id = department_id"
```

---

### Validation Patterns

Patterns for implementing complex business rule validation.

#### `validation/validation_chain`

Chains multiple validation rules with configurable error handling.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `validations` | array | Yes | List of validation rules |
| `validations[].name` | string | No | Rule identifier |
| `validations[].field` | string | No | Field to validate |
| `validations[].condition` | string | Yes* | SQL validation condition |
| `validations[].message` | string | Yes* | Error message |
| `stop_on_first_failure` | boolean | No | Stop on first error (default: true) |
| `collect_all_errors` | boolean | No | Return all errors (default: false) |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.validate_entity(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_errors jsonb := '[]';
    v_error_count integer := 0;
BEGIN
    -- Validation 1
    IF NOT (validation_condition_1) THEN
        v_errors := v_errors || jsonb_build_object(
            'field', 'field_name',
            'code', 'validation_error_code',
            'message', 'Error message'
        );
        v_error_count := v_error_count + 1;

        {% if stop_on_first_failure %}
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', NULL, 'NOOP', 'validation:failed',
            ARRAY[]::TEXT[], 'Validation failed', NULL, NULL, v_errors
        );
        {% endif %}
    END IF;

    -- Additional validations...

    -- Return result
    IF v_error_count > 0 THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', NULL, 'NOOP', 'validation:failed',
            ARRAY[]::TEXT[], 'Validation failed', NULL, NULL, v_errors
        );
    ELSE
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id,
            'entity', NULL, 'VALIDATE', 'success',
            ARRAY[]::TEXT[], 'Validation passed', NULL, NULL, NULL
        );
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: validate_contract_comprehensive
    pattern: validation/validation_chain
    config:
      validations:
        - name: customer_exists
          field: customer_org
          condition: "EXISTS (SELECT 1 FROM organizations WHERE id = input_data->>'customer_org')"
          message: "Customer organization must exist"
        - name: amount_positive
          field: total_value
          condition: "input_data->>'total_value' > 0"
          message: "Contract total value must be positive"
      collect_all_errors: true
```

---

### Batch Operation Patterns

Patterns for processing multiple records efficiently.

#### `batch/bulk_operation`

Process multiple records in a single operation with error handling.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_input` | string | Yes | JSONB field containing items |
| `operation` | object | Yes | Operation to perform per item |
| `error_handling` | enum | No | Error handling mode (default: continue_on_error) |
| `batch_size` | integer | No | Max items to process (default: 100) |
| `return_summary` | object | No | Summary fields to return |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.bulk_operation_entity(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_item record;
    v_processed_count integer := 0;
    v_failed_count integer := 0;
    v_failed_items jsonb := '[]';
BEGIN
    -- Process each item in batch
    FOR v_item IN SELECT * FROM jsonb_array_elements(input_data->'batch_input')
    LOOP
        BEGIN
            -- Perform operation on item
            -- [operation logic here]

            v_processed_count := v_processed_count + 1;

        EXCEPTION WHEN OTHERS THEN
            v_failed_count := v_failed_count + 1;
            v_failed_items := v_failed_items || jsonb_build_object(
                'item', v_item.value,
                'error', SQLERRM
            );

            {% if error_handling == 'fail_on_error' %}
            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                'entity', NULL, 'NOOP', 'batch:failed',
                ARRAY[]::TEXT[], 'Batch operation failed', NULL, NULL,
                jsonb_build_object('failed_items', v_failed_items)
            );
            {% endif %}
        END;
    END LOOP;

    -- Return summary
    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'entity', NULL, 'BATCH', 'success',
        ARRAY[]::TEXT[], 'Batch operation completed',
        NULL, NULL,
        jsonb_build_object(
            'processed_count', v_processed_count,
            'failed_count', v_failed_count,
            'failed_items', v_failed_items
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Usage Example:**
```yaml
actions:
  - name: bulk_update_contracts
    pattern: batch/bulk_operation
    config:
      batch_input: contract_updates
      operation:
        action: update
        entity: Contract
        set:
          status: $item.status
          total_value: $item.total_value
        where: "id = $item.id"
      error_handling: continue_on_error
      return_summary:
        processed_count: v_processed_count
        failed_count: v_failed_count
```

---

### Multi-Entity Patterns

Patterns for coordinating operations across multiple related entities.

#### `multi_entity/coordinated_update`

Coordinate updates across multiple entities in a single transaction.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entities` | array | Yes | List of entity operations |
| `entities[].entity` | string | Yes* | Entity name |
| `entities[].operation` | enum | Yes* | Operation type (insert/update/delete) |
| `entities[].fields` | array | No | Fields to include |
| `entities[].validations` | array | No | Validation rules |

**Generated SQL Structure:**
```sql
CREATE OR REPLACE FUNCTION schema.coordinated_update(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
    v_entity1_id uuid;
    v_entity2_id uuid;
BEGIN
    -- Entity 1 operation
    -- [insert/update/delete logic]

    -- Entity 2 operation
    -- [insert/update/delete logic]

    -- Additional entity operations...

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id,
        'coordinated', NULL, 'MULTI_ENTITY', 'success',
        ARRAY[]::TEXT[], 'Coordinated update completed', NULL, NULL, NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

#### `multi_entity/event_driven_orchestrator`

Trigger operations based on events or conditions.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trigger` | string | Yes | Event or condition that triggers the orchestration |
| `conditions` | array | No | Additional conditions to evaluate |
| `steps` | array | Yes | Operations to perform when triggered |

---

#### `multi_entity/parent_child_cascade`

Handle cascading operations between parent and child entities.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent_entity` | string | Yes | Parent entity name |
| `child_entity` | string | Yes | Child entity name |
| `cascade_operation` | enum | Yes | Type of cascade (delete/update) |
| `relationship_field` | string | Yes | Foreign key field |

---

#### `multi_entity/saga_orchestrator`

Implement saga pattern for distributed transactions.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `saga_steps` | array | Yes | Sequential saga steps |
| `saga_steps[].name` | string | Yes* | Step identifier |
| `saga_steps[].action` | object | Yes* | Action to perform |
| `saga_steps[].compensation` | object | No | Compensation action |

---

### Composite Patterns

High-level patterns that combine multiple operations.

#### `composite/workflow_orchestrator`

Orchestrate complex multi-step workflows.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workflow` | array | Yes | Sequential workflow steps |
| `success_action` | array | No | Actions on successful completion |
| `failure_action` | array | No | Actions on failure |

---

#### `composite/conditional_workflow`

Execute different workflows based on conditions.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conditions` | array | Yes | Conditional branches |
| `conditions[].if` | string | Yes* | Condition to evaluate |
| `conditions[].then` | array | Yes* | Actions if condition is true |
| `conditions[].else` | array | No | Actions if condition is false |

---

#### `composite/retry_orchestrator`

Retry operations with configurable backoff.

**Configuration Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `max_attempts` | integer | No | Maximum retry attempts (default: 3) |
| `backoff_seconds` | integer | No | Backoff interval (default: 60) |
| `workflow` | array | Yes | Operations to retry |

---

## Error Codes

All patterns use standardized error codes:

| Error Code | Description | Pattern Category |
|------------|-------------|------------------|
| `validation:duplicate_found` | Duplicate record detected | CRUD |
| `validation:record_not_found` | Entity not found | CRUD |
| `validation:dependencies_exist` | Cannot delete due to dependencies | CRUD |
| `validation:invalid_state_transition` | Invalid state transition | State Machine |
| `validation:guard_failed` | Business rule guard failed | State Machine |
| `validation:failed` | Validation rule failed | Validation |
| `batch:failed` | Batch operation failed | Batch |

## Best Practices

### Pattern Selection
- Use `crud/*` patterns for basic entity operations
- Use `state_machine/*` patterns for status transitions
- Use `validation/validation_chain` for complex business rules
- Use `batch/bulk_operation` for bulk data processing
- Use `multi_entity/*` patterns for cross-entity coordination

### Configuration Guidelines
- Keep validation conditions simple and readable
- Use descriptive error messages
- Prefer guard conditions over complex validation logic
- Configure appropriate error handling for batch operations

### Performance Considerations
- Batch operations reduce round trips but increase transaction time
- State machine validations execute on every transition
- Multi-entity operations require careful transaction management
- Consider projection refresh impact on performance

## Migration from Manual SQL

### Automated Analysis
```bash
# Analyze existing entities for pattern opportunities
specql analyze --entity my_entity --patterns

# Generate migration suggestions
specql migrate --entity my_entity --target-patterns crud,state_machine
```

### Manual Migration Steps
1. Identify repetitive SQL patterns in existing functions
2. Map business logic to appropriate SpecQL patterns
3. Configure pattern parameters
4. Test generated SQL equivalence
5. Deploy with rollback plan

---

**See Also:**
- [Test Generation API](test-generation-api.md)
- [YAML Schema Reference](yaml-schema.md)
- [Best Practices Guide](../best-practices/)
- [Pattern Examples](../../examples/)