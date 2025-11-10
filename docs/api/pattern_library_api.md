# Pattern Library API Reference

Complete reference for SpecQL action patterns, including all parameters, options, and examples.

## 📋 Table of Contents

- [State Machine Pattern](#state-machine-pattern)
- [Multi-Entity Pattern](#multi-entity-pattern)
- [Batch Operation Pattern](#batch-operation-pattern)
- [CRUD Enhancement Options](#crud-enhancement-options)
- [Common Parameters](#common-parameters)
- [Error Handling](#error-handling)

## 🔄 State Machine Pattern

**Pattern**: `state_machine/transition`

Manages entity state transitions with validation, side effects, and projection refresh.

### Parameters

#### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_states` | `array<string>` | Valid source states for transition |
| `to_state` | `string` | Target state after transition |

#### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `validation_checks` | `array<validation>` | `[]` | Pre-transition validation rules |
| `side_effects` | `array<side_effect>` | `[]` | Post-transition updates to other entities |
| `input_fields` | `array<input_field>` | `[]` | Additional fields to set during transition |
| `refresh_projection` | `string` | `null` | Projection to refresh after transition |

### Validation Check Schema

```yaml
validation_checks:
  - name: string              # Optional: descriptive name
    condition: string         # SQL expression returning boolean
    error: string            # Error message if validation fails
```

**Examples:**
```yaml
validation_checks:
  - name: no_active_allocations
    condition: "NOT EXISTS (SELECT 1 FROM allocations WHERE machine_id = v_machine_id AND status = 'active')"
    error: "Cannot transition with active allocations"

  - condition: "input_data.approved_by IS NOT NULL"
    error: "Approval requires approver ID"
```

### Side Effect Schema

```yaml
side_effects:
  - entity: string           # Entity to update
    set: object             # Fields to set {field: value}
    where: string           # WHERE clause for update
    description: string     # Optional: descriptive name
```

**Examples:**
```yaml
side_effects:
  - entity: MachineItem
    set:
      status: archived
      archived_at: NOW()
    where: "machine_id = v_machine_id"
    description: "Archive related items"

  - entity: AuditLog
    set:
      action: $input.action_type
      entity_id: v_machine_id
      user_id: $auth_user_id
    where: "entity_type = 'machine'"
```

### Input Field Schema

```yaml
input_fields:
  - name: string            # Field name
    type: string           # PostgreSQL type
    required: boolean      # Whether field is required
```

**Examples:**
```yaml
input_fields:
  - name: decommission_date
    type: date
    required: true

  - name: notes
    type: text
    required: false
```

### Complete Example

```yaml
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
        - condition: "NOT EXISTS (SELECT 1 FROM allocations WHERE machine_id = v_machine_id AND status = 'active')"
          error: "Cannot decommission with active allocations"
      side_effects:
        - entity: MachineItem
          set: {status: archived}
          where: "machine_id = v_machine_id"
        - entity: MachineEvent
          set:
            event_type: decommissioned
            event_data: $input_payload
          where: "machine_id = v_machine_id"
      refresh_projection: machine_projection
```

### Generated SQL Structure

```sql
CREATE OR REPLACE FUNCTION app.decommission_machine(...) RETURNS mutation_result AS $$
DECLARE
    v_current_status TEXT;
BEGIN
    -- Load and validate current state
    SELECT status INTO v_current_status FROM entity_table WHERE id = v_entity_id;

    IF v_current_status NOT IN ('from_state1', 'from_state2') THEN
        RETURN error_response('invalid_state_transition');
    END IF;

    -- Custom validations
    IF NOT (validation_condition) THEN
        RETURN error_response('validation_error');
    END IF;

    -- State transition
    UPDATE entity_table SET
        status = 'to_state',
        to_state_at = NOW(),
        input_field1 = input_data.input_field1,
        ...
    WHERE id = v_entity_id;

    -- Side effects
    UPDATE other_entity SET ... WHERE ...;

    -- Projection refresh
    PERFORM refresh_entity_projection(v_entity_id);

    RETURN success_response();
END;
$$;
```

## 🔗 Multi-Entity Pattern

**Pattern**: `multi_entity/coordinated_update`

Coordinates operations across multiple entities in a single transaction.

### Parameters

#### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `primary_entity` | `string` | Main entity being operated on |
| `operations` | `array<operation>` | Sequence of operations to perform |

#### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transaction_scope` | `enum` | `serializable` | Transaction isolation level |
| `refresh_projections` | `array<string>` | `[]` | Projections to refresh after operations |

### Operation Schema

Operations support different action types:

#### Get or Create Operation
```yaml
- action: get_or_create
  entity: string              # Entity to check/create
  where: object              # Conditions to find existing
  create_if_missing: object  # Fields for creation if not found
  store_as: string           # Variable to store resulting ID
```

#### Insert Operation
```yaml
- action: insert
  entity: string             # Entity to insert into
  values: object             # Field values {field: value}
  store_as: string           # Optional: store inserted ID
```

#### Update Operation
```yaml
- action: update
  entity: string             # Entity to update
  set: object                # Fields to set {field: value}
  where: string|object       # WHERE conditions
```

#### Delete Operation
```yaml
- action: delete
  entity: string             # Entity to delete from
  where: string|object       # WHERE conditions
```

### Complete Example

```yaml
actions:
  - name: allocate_to_stock
    pattern: multi_entity/coordinated_update
    config:
      primary_entity: Machine
      operations:
        - action: get_or_create
          entity: Location
          where:
            code: 'STOCK'
            tenant_id: $auth_tenant_id
          create_if_missing:
            code: STOCK
            name: 'Stock Location'
            location_type: warehouse
          store_as: stock_location_id

        - action: insert
          entity: Allocation
          values:
            machine_id: $input_data.machine_id
            location_id: $stock_location_id
            allocation_type: stock
            status: active
            allocated_at: NOW()
          store_as: allocation_id

        - action: update
          entity: Machine
          set:
            status: in_stock
            location_id: $stock_location_id
            current_allocation_id: $allocation_id
          where: "id = $input_data.machine_id"

        - action: insert
          entity: MachineEvent
          values:
            machine_id: $input_data.machine_id
            event_type: allocated_to_stock
            event_data: $input_payload

      refresh_projections:
        - machine_projection
        - allocation_projection
```

### Generated SQL Structure

```sql
CREATE OR REPLACE FUNCTION app.allocate_to_stock(...) RETURNS mutation_result AS $$
DECLARE
    v_stock_location_id UUID;
    v_allocation_id UUID;
BEGIN
    -- Get or create location
    SELECT id INTO v_stock_location_id FROM locations WHERE code = 'STOCK';
    IF v_stock_location_id IS NULL THEN
        INSERT INTO locations (...) VALUES (...) RETURNING id INTO v_stock_location_id;
    END IF;

    -- Insert allocation
    INSERT INTO allocations (...) VALUES (...) RETURNING id INTO v_allocation_id;

    -- Update machine
    UPDATE machines SET ... WHERE ...;

    -- Insert event
    INSERT INTO events (...) VALUES (...);

    -- Refresh projections
    PERFORM refresh_machine_projection(...);
    PERFORM refresh_allocation_projection(...);

    RETURN success_response();
END;
$$;
```

## 📦 Batch Operation Pattern

**Pattern**: `batch/bulk_operation`

Processes multiple records in a single operation with error handling.

### Parameters

#### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `batch_input` | `string` | Field name containing array of items |
| `operation` | `operation` | Operation to perform on each item |
| `return_summary` | `object` | Summary fields to return |

#### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `error_handling` | `enum` | `continue_on_error` | Error handling strategy |
| `batch_size` | `integer` | `100` | Maximum items to process |
| `refresh_projections` | `array<string>` | `[]` | Projections to refresh after batch |

### Operation Schema

```yaml
operation:
  action: update|insert|delete
  entity: string
  set: object                # For update: {field: $item.value}
  values: object             # For insert: {field: $item.value}
  where: string|object       # WHERE conditions with $item references
```

### Return Summary Schema

```yaml
return_summary:
  field_name: variable_name   # Maps response field to internal variable
```

**Examples:**
```yaml
return_summary:
  processed_count: v_processed_count
  failed_count: v_failed_count
  failed_items: v_failed_items
```

### Complete Example

```yaml
actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      batch_input: price_updates
      operation:
        action: update
        entity: ContractItem
        set:
          unit_price: $item.unit_price
          total_price: $item.unit_price * quantity
        where: "id = $item.id AND tenant_id = $auth_tenant_id"
      error_handling: continue_on_error
      batch_size: 100
      refresh_projections:
        - contract_item_projection
        - contract_projection
      return_summary:
        processed_count: v_processed_count
        failed_count: v_failed_count
        failed_items: v_failed_items
```

### Generated SQL Structure

```sql
CREATE OR REPLACE FUNCTION app.bulk_update_prices(...) RETURNS mutation_result AS $$
DECLARE
    v_item JSONB;
    v_processed_count INTEGER := 0;
    v_failed_count INTEGER := 0;
    v_failed_items JSONB := '[]'::JSONB;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(input_data.price_updates) LIMIT 100
    LOOP
        BEGIN
            UPDATE contract_items SET
                unit_price = (v_item->>'unit_price')::DECIMAL,
                total_price = (v_item->>'unit_price')::DECIMAL * quantity
            WHERE id = (v_item->>'id')::UUID AND tenant_id = auth_tenant_id;

            v_processed_count := v_processed_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_failed_count := v_failed_count + 1;
            v_failed_items := v_failed_items || jsonb_build_object('error', SQLERRM, 'item', v_item);
        END;
    END LOOP;

    -- Refresh projections
    PERFORM refresh_contract_item_projection();
    PERFORM refresh_contract_projection();

    RETURN success_response(jsonb_build_object(
        'processed_count', v_processed_count,
        'failed_count', v_failed_count,
        'failed_items', v_failed_items
    ));
END;
$$;
```

## 🛠️ CRUD Enhancement Options

These are not patterns but entity-level configurations that enhance CRUD operations.

### Entity Constraints

```yaml
constraints:
  - name: string              # Constraint identifier
    type: unique             # Constraint type
    fields: array           # Fields in constraint
    check_on_create: boolean # Check on INSERT
    error_message: string    # Custom error message
```

### Identifier Configuration

```yaml
identifier:
  pattern: string           # Pattern with {field:format} placeholders
  sequence:
    scope: array            # Fields defining sequence scope
    group_by: array         # Fields for grouping sequences
  recalculate_on: array     # When to recalc: [create, update]
```

### Projection Configuration

```yaml
projections:
  - name: string            # Projection name
    materialize: boolean    # Whether to create materialized view
    refresh_on: array       # When to refresh: [create, update, delete]
    includes: array         # Related entities to include
```

### Delete Policy

```yaml
delete_policy:
  default: soft|hard        # Default delete behavior
  allow_hard_delete: boolean # Whether hard delete is allowed
  check_dependencies: array  # Dependency checks before hard delete
```

### Action Enhancements

```yaml
actions:
  - name: update_entity
    partial_updates: boolean      # Use CASE expressions for partial updates
    track_updated_fields: boolean # Track which fields changed
    duplicate_detection: boolean  # Check constraints before create
    recalculate_identifier: boolean # Recalc identifier after operation
    refresh_projection: string    # Projection to refresh
    supports_hard_delete: boolean # Allow hard delete
    dependency_check: boolean     # Check dependencies before delete
```

## 🔧 Common Parameters

### Variable References

| Variable | Description | Example |
|----------|-------------|---------|
| `$input_data.field` | Input payload field | `$input_data.machine_id` |
| `$auth_user_id` | Current user ID | `updated_by: $auth_user_id` |
| `$auth_tenant_id` | Current tenant ID | `tenant_id: $auth_tenant_id` |
| `v_entity_id` | Current entity ID | `machine_id = v_entity_id` |
| `$item.field` | Batch item field | `$item.unit_price` |

### SQL Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `EXISTS(...)` | Check existence | `EXISTS (SELECT 1 FROM table WHERE ...)` |
| `NOT EXISTS(...)` | Check non-existence | `NOT EXISTS (SELECT 1 FROM ...)` |
| `COUNT(*)` | Count rows | `SELECT COUNT(*) FROM table` |
| `NOW()` | Current timestamp | `created_at: NOW()` |

### Field Types

| SpecQL Type | PostgreSQL Type | Example |
|-------------|-----------------|---------|
| `text` | `TEXT` | `name: text` |
| `uuid` | `UUID` | `id: uuid` |
| `integer` | `INTEGER` | `quantity: integer` |
| `decimal(p,s)` | `DECIMAL(p,s)` | `price: decimal(10,2)` |
| `date` | `DATE` | `start_date: date` |
| `timestamptz` | `TIMESTAMPTZ` | `created_at: timestamptz` |
| `boolean` | `BOOLEAN` | `active: boolean` |
| `enum(...)` | `ENUM` | `status: enum(active,inactive)` |

## 🚨 Error Handling

### Pattern Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing required parameter` | Required parameter not provided | Add parameter to config |
| `Invalid parameter type` | Wrong parameter type | Check parameter schema |
| `Unknown pattern` | Pattern doesn't exist | Verify pattern name |
| `Template expansion failed` | Jinja2 template error | Check template syntax |

### Runtime Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_state_transition` | Current state not in from_states | Check state machine config |
| `validation:check_name` | Validation condition failed | Fix data or validation logic |
| `has_dependencies` | Hard delete blocked by dependencies | Use soft delete or remove dependencies |

### SQL Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `relation "table" does not exist` | Wrong table name | Check entity schema |
| `column "field" does not exist` | Wrong field name | Check entity fields |
| `permission denied` | Missing database permissions | Grant appropriate permissions |

## 📊 Response Format

All patterns return a standardized `mutation_result` with:

```sql
CREATE TYPE app.mutation_result AS (
    tenant_id UUID,
    user_id UUID,
    entity_name TEXT,
    entity_id UUID,
    mutation_type TEXT,
    mutation_status TEXT,
    updated_fields TEXT[],
    message TEXT,
    payload_before JSONB,
    payload_after JSONB,
    metadata JSONB
);
```

### Success Response Fields

| Field | Description |
|-------|-------------|
| `mutation_type` | Type of mutation (CREATE, UPDATE, DELETE, BATCH_UPDATE) |
| `mutation_status` | Status (success, noop:already_exists, etc.) |
| `updated_fields` | Array of fields that were changed |
| `message` | Human-readable success message |
| `payload_after` | Entity data after mutation |
| `metadata` | Additional operation-specific data |

### Error Response Fields

| Field | Description |
|-------|-------------|
| `mutation_status` | Error status (validation:error_name) |
| `message` | Error message |
| `metadata` | Error details and conflict information |

### Batch Operation Metadata

```json
{
  "processed_count": 85,
  "failed_count": 15,
  "failed_items": [
    {"id": "uuid", "reason": "not_found"},
    {"id": "uuid", "reason": "permission_denied"}
  ]
}
```

---

## 📚 See Also

- [Pattern Library Guide](../patterns/README.md) - Getting started guide
- [Migration Guide](printoptim_to_specql.md) - Migrating from manual SQL
- [Examples](../../entities/examples/) - Working examples
- [Quick Start](../patterns/getting_started.md) - Step-by-step tutorial