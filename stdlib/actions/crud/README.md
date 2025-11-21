# CRUD Action Patterns

Enhanced Create, Read, Update, Delete operations with advanced features like duplicate detection, partial updates, and dependency checking.

## Overview

CRUD patterns provide the foundation for data manipulation operations, extending basic SpecQL CRUD with production-ready features extracted from the PrintOptim reference implementation.

## Available Patterns

### `crud/create`

Enhanced entity creation with duplicate detection and automatic identifier generation.

#### Configuration

```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
        error_message: "Contract already exists for this customer and contract ID"
        return_conflict_object: true
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `duplicate_check` | object | No | Duplicate detection configuration |
| `duplicate_check.fields` | array | Yes* | Fields to check for duplicates |
| `duplicate_check.error_message` | string | No | Custom error message |
| `duplicate_check.return_conflict_object` | boolean | No | Include conflicting object in error |

#### Generated SQL Features

- **Duplicate Detection**: Checks for existing records before insertion
- **Identifier Recalculation**: Automatic sequence-based ID generation
- **Projection Refresh**: Updates related views/materialized views
- **Audit Trail**: Records creation metadata

#### Example Output

```sql
CREATE OR REPLACE FUNCTION app.create_contract(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
  v_contract_id uuid;
  v_existing_id uuid;
BEGIN
  -- Duplicate check
  SELECT id INTO v_existing_id
  FROM tenant.tb_contract
  WHERE customer_org = (input_data->>'customer_org')::uuid
    AND customer_contract_id = input_data->>'customer_contract_id';

  IF v_existing_id IS NOT NULL THEN
    RETURN app.log_and_return_mutation(
      auth_tenant_id, auth_user_id, 'contract', v_existing_id,
      'NOOP', 'validation:duplicate_found',
      ARRAY['customer_org', 'customer_contract_id'],
      'Contract already exists for this customer and contract ID',
      v_existing_id::text, NULL,
      jsonb_build_object('conflicting_id', v_existing_id)
    );
  END IF;

  -- Insert contract
  INSERT INTO tenant.tb_contract (
    customer_org, customer_contract_id, total_value, status,
    created_at, created_by, tenant_id
  ) VALUES (
    (input_data->>'customer_org')::uuid,
    input_data->>'customer_contract_id',
    (input_data->>'total_value')::decimal,
    'draft',
    NOW(), auth_user_id, auth_tenant_id
  ) RETURNING id INTO v_contract_id;

  -- Recalculate identifier
  PERFORM tenant.recalcid_contract(v_contract_id, auth_tenant_id, auth_user_id);

  -- Refresh projections
  PERFORM tenant.refresh_contract_projection(auth_tenant_id);

  RETURN app.log_and_return_mutation(
    auth_tenant_id, auth_user_id, 'contract', v_contract_id,
    'CREATE', 'success',
    ARRAY[]::text[], 'Contract created successfully',
    v_contract_id::text, NULL, NULL
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### `crud/update`

Partial updates with field change tracking and automatic identifier recalculation.

#### Configuration

```yaml
actions:
  - name: update_contract
    pattern: crud/update
    config:
      partial_updates: true
      track_updated_fields: true
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partial_updates` | boolean | No | Use CASE expressions for partial updates |
| `track_updated_fields` | boolean | No | Track which fields were modified |

#### Generated SQL Features

- **Partial Updates**: Only updates provided fields using CASE expressions
- **Field Tracking**: Records which fields changed for audit purposes
- **Identifier Recalculation**: Updates sequence-based identifiers
- **Projection Refresh**: Updates related views

#### Example Output

```sql
CREATE OR REPLACE FUNCTION app.update_contract(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
  v_contract_id uuid := (input_data->>'id')::uuid;
  v_updated_fields text[] := ARRAY[]::text[];
BEGIN
  -- Verify contract exists and belongs to tenant
  IF NOT EXISTS (
    SELECT 1 FROM tenant.tb_contract
    WHERE id = v_contract_id AND tenant_id = auth_tenant_id
  ) THEN
    RETURN app.log_and_return_mutation(
      auth_tenant_id, auth_user_id, 'contract', v_contract_id,
      'NOOP', 'validation:not_found',
      ARRAY[]::text[], 'Contract not found', NULL, NULL, NULL
    );
  END IF;

  -- Partial update using CASE expressions
  UPDATE tenant.tb_contract SET
    customer_contract_id = CASE
      WHEN input_data ? 'customer_contract_id'
      THEN input_data->>'customer_contract_id'
      ELSE customer_contract_id
    END,
    total_value = CASE
      WHEN input_data ? 'total_value'
      THEN (input_data->>'total_value')::decimal
      ELSE total_value
    END,
    updated_at = NOW(),
    updated_by = auth_user_id
  WHERE id = v_contract_id AND tenant_id = auth_tenant_id;

  -- Track updated fields
  IF input_data ? 'customer_contract_id' THEN
    v_updated_fields := v_updated_fields || 'customer_contract_id';
  END IF;
  IF input_data ? 'total_value' THEN
    v_updated_fields := v_updated_fields || 'total_value';
  END IF;

  -- Recalculate identifier if needed
  PERFORM tenant.recalcid_contract(v_contract_id, auth_tenant_id, auth_user_id);

  -- Refresh projections
  PERFORM tenant.refresh_contract_projection(auth_tenant_id);

  RETURN app.log_and_return_mutation(
    auth_tenant_id, auth_user_id, 'contract', v_contract_id,
    'UPDATE', 'success',
    v_updated_fields, 'Contract updated successfully',
    v_contract_id::text, NULL,
    jsonb_build_object('updated_fields', v_updated_fields)
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### `crud/delete`

Dependency-aware deletion with hard delete support.

#### Configuration

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

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supports_hard_delete` | boolean | No | Allow permanent deletion |
| `check_dependencies` | array | No | Dependency validation rules |
| `check_dependencies[].entity` | string | Yes* | Related entity to check |
| `check_dependencies[].field` | string | Yes* | Foreign key field |
| `check_dependencies[].block_hard_delete` | boolean | No | Prevent hard delete if dependencies exist |
| `check_dependencies[].error_message` | string | No | Custom error message |

#### Generated SQL Features

- **Dependency Checking**: Validates related records before deletion
- **Soft Delete**: Marks records as deleted (default behavior)
- **Hard Delete**: Permanently removes records when allowed
- **Cascade Options**: Configurable dependency handling

#### Example Output

```sql
CREATE OR REPLACE FUNCTION app.delete_contract(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
  v_contract_id uuid := (input_data->>'id')::uuid;
  v_hard_delete boolean := COALESCE((input_data->>'hard_delete')::boolean, false);
  v_dependency_count integer;
BEGIN
  -- Verify contract exists
  IF NOT EXISTS (
    SELECT 1 FROM tenant.tb_contract
    WHERE id = v_contract_id AND tenant_id = auth_tenant_id
  ) THEN
    RETURN app.log_and_return_mutation(
      auth_tenant_id, auth_user_id, 'contract', v_contract_id,
      'NOOP', 'validation:not_found',
      ARRAY[]::text[], 'Contract not found', NULL, NULL, NULL
    );
  END IF;

  -- Check for contract items
  SELECT COUNT(*) INTO v_dependency_count
  FROM tenant.tb_contract_item
  WHERE contract_id = v_contract_id AND tenant_id = auth_tenant_id;

  IF v_dependency_count > 0 AND v_hard_delete THEN
    RETURN app.log_and_return_mutation(
      auth_tenant_id, auth_user_id, 'contract', v_contract_id,
      'NOOP', 'validation:dependency_exists',
      ARRAY[]::text[], 'Cannot delete contract with associated items',
      NULL, NULL, NULL
    );
  END IF;

  IF v_hard_delete THEN
    -- Hard delete
    DELETE FROM tenant.tb_contract
    WHERE id = v_contract_id AND tenant_id = auth_tenant_id;
  ELSE
    -- Soft delete
    UPDATE tenant.tb_contract SET
      deleted_at = NOW(),
      deleted_by = auth_user_id
    WHERE id = v_contract_id AND tenant_id = auth_tenant_id;
  END IF;

  -- Refresh projections
  PERFORM tenant.refresh_contract_projection(auth_tenant_id);

  RETURN app.log_and_return_mutation(
    auth_tenant_id, auth_user_id, 'contract', v_contract_id,
    'DELETE', 'success',
    ARRAY[]::text[], 'Contract deleted successfully',
    v_contract_id::text, NULL, NULL
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Migration Examples

### From Manual Create Function

**Before:**
```sql
CREATE OR REPLACE FUNCTION app.create_contract(user_id uuid, input jsonb)
RETURNS mutation_result AS $$
DECLARE
  v_contract_id uuid;
BEGIN
  -- Manual duplicate check
  IF EXISTS (SELECT 1 FROM contracts WHERE customer_contract_id = input->>'customer_contract_id') THEN
    RETURN error_response('Contract already exists');
  END IF;

  -- Manual insert
  INSERT INTO contracts (...) VALUES (...);
  -- Manual projection refresh
  -- etc.
END;
$$;
```

**After:**
```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_contract_id]
        error_message: "Contract already exists"
```

### From Manual Update Function

**Before:**
```sql
CREATE OR REPLACE FUNCTION app.update_contract(user_id uuid, input jsonb)
RETURNS mutation_result AS $$
BEGIN
  UPDATE contracts SET
    field1 = COALESCE(input->>'field1', field1),
    field2 = COALESCE(input->>'field2', field2),
    updated_at = NOW()
  WHERE id = (input->>'id')::uuid;
END;
$$;
```

**After:**
```yaml
actions:
  - name: update_contract
    pattern: crud/update
    config:
      partial_updates: true
      track_updated_fields: true
```

## Testing

### Integration Tests

```bash
# Test CRUD patterns
pytest tests/integration/patterns/ -k "crud"

# Test specific CRUD operation
pytest tests/integration/patterns/test_pattern_compilation.py::TestPatternCompilation::test_crud_create_pattern_parsing
```

### Generated SQL Validation

```sql
-- Test duplicate detection
SELECT * FROM app.create_contract(uuid_generate_v4(), '{"customer_contract_id": "DUPE"}');

-- Test partial update
SELECT * FROM app.update_contract(uuid_generate_v4(), '{"id": "...", "total_value": 1000}');

-- Test dependency checking
SELECT * FROM app.delete_contract(uuid_generate_v4(), '{"id": "...", "hard_delete": true}');
```

## Performance Considerations

- **CASE Expressions**: More efficient than multiple UPDATE statements
- **JSONB Operations**: Optimized for flexible input handling
- **Index Usage**: Leverages existing unique constraints
- **Batch Operations**: Single transaction for related updates

## Best Practices

1. **Use Duplicate Detection**: Always configure for business key fields
2. **Enable Partial Updates**: More efficient and flexible than full updates
3. **Configure Dependencies**: Prevent data integrity issues
4. **Test Thoroughly**: Validate generated SQL matches business requirements
5. **Monitor Performance**: Compare with manual implementations
