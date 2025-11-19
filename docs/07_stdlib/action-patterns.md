# Action Patterns: Pre-Built Business Logic

> **Transform 200 lines of PL/pgSQL into 20 lines of YAML—battle-tested action patterns for common business operations**

## Overview

SpecQL's **Action Pattern Library** is a collection of reusable business logic templates that automatically generate production-ready PostgreSQL functions. Instead of writing hundreds of lines of PL/pgSQL, you configure proven patterns in YAML.

**Think of it as**: GitHub Actions meets AWS Step Functions, but for database business logic.

---

## The Power of Action Patterns

### Without Patterns (Traditional Approach)

```sql
-- Manual PL/pgSQL: 200+ lines
CREATE OR REPLACE FUNCTION app.create_contract(user_id uuid, input_data jsonb)
RETURNS app.mutation_result AS $$
DECLARE
  v_contract_id integer;
  v_customer_org_id integer;
  v_duplicate_exists boolean;
BEGIN
  -- Manual duplicate check
  SELECT EXISTS (
    SELECT 1 FROM contracts
    WHERE customer_org = (input_data->>'customer_org')::uuid
      AND customer_contract_id = input_data->>'customer_contract_id'
      AND deleted_at IS NULL
  ) INTO v_duplicate_exists;

  IF v_duplicate_exists THEN
    RAISE EXCEPTION 'Contract already exists' USING ERRCODE = 'P0001';
  END IF;

  -- Manual FK resolution (UUID → INTEGER)
  SELECT pk_organization INTO v_customer_org_id
  FROM crm.tb_organization
  WHERE id = (input_data->>'customer_org')::uuid;

  IF v_customer_org_id IS NULL THEN
    RAISE EXCEPTION 'Customer organization not found';
  END IF;

  -- Manual insert
  INSERT INTO contracts (
    customer_org_fk,
    customer_contract_id,
    total_value,
    -- ... 15 more fields
  ) VALUES (
    v_customer_org_id,
    input_data->>'customer_contract_id',
    (input_data->>'total_value')::numeric,
    -- ... 15 more values
  ) RETURNING pk_contract INTO v_contract_id;

  -- Manual identifier recalculation
  UPDATE contracts SET identifier = ...;

  -- Manual projection refresh
  REFRESH MATERIALIZED VIEW CONCURRENTLY contract_projection;

  -- Manual response
  RETURN success_response(v_contract_id, ...);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Time**: 2-3 hours to write properly
**Lines**: 200+ lines of SQL
**Bugs**: High risk—easy to miss edge cases
**Maintainability**: Low—business logic buried in SQL

### With Patterns (SpecQL Approach)

```yaml
# Pattern-based YAML: 20 lines
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
        error_message: "Contract already exists for this customer"
      refresh_projection: contract_projection
```

**Time**: 5 minutes to configure
**Lines**: 20 lines of YAML
**Bugs**: Zero—pattern is battle-tested
**Maintainability**: High—business intent is clear

**Result**: Same 200+ lines of SQL generated automatically with proper error handling, Trinity pattern resolution, audit trails, and FraiseQL integration.

---

## Available Pattern Categories

### 1. CRUD Patterns (`crud/`)

Pre-built create, read, update, delete operations with advanced features.

**Patterns**:
- `crud/create` - Entity creation with duplicate detection
- `crud/update` - Partial updates with field tracking
- `crud/delete` - Dependency-aware deletion

**Common Features**:
- Trinity pattern FK resolution (UUID → INTEGER)
- Automatic `identifier` recalculation
- Audit field updates (`updated_at`, `updated_by`)
- Materialized view refresh
- FraiseQL `mutation_result` response

### 2. State Machine Patterns (`state_machine/`)

State transitions with validation, guards, and side effects.

**Patterns**:
- `state_machine/transition` - Simple state transitions
- `state_machine/guarded_transition` - Complex transitions with business rules

**Common Features**:
- Declarative state validation
- Guard conditions (business rules)
- Automatic audit trail
- Multi-entity side effects
- Rollback on failure

### 3. Validation Patterns (`validation/`)

Complex validation workflows with comprehensive error handling.

**Patterns**:
- `validation/validation_chain` - Chain multiple validation rules
- `validation/recursive_dependency_validator` - Deep dependency validation

**Common Features**:
- Multiple validation rules
- Configurable error handling (stop-on-first vs collect-all)
- Field-specific validation
- Custom error messages

### 4. Batch Operation Patterns (`batch/`)

Process multiple records efficiently with transaction handling.

**Patterns**:
- `batch/bulk_operation` - Batch updates/inserts/deletes

**Common Features**:
- Transaction-wrapped processing
- Configurable error handling (fail-fast vs continue)
- Progress tracking
- Summary reporting

### 5. Multi-Entity Patterns (`multi_entity/`)

Coordinate operations across multiple entities.

**Patterns**:
- `multi_entity/coordinated_update` - Update multiple entities atomically
- `multi_entity/parent_child_cascade` - Cascade operations to children
- `multi_entity/saga_orchestrator` - Distributed transaction patterns
- `multi_entity/event_driven_orchestrator` - Event-driven workflows

**Common Features**:
- Atomic transactions
- Rollback on failure
- Event logging
- Dependency ordering

### 6. Composite Patterns (`composite/`)

Complex workflows combining multiple patterns.

**Patterns**:
- `composite/workflow_orchestrator` - Multi-step business processes
- `composite/conditional_workflow` - Branching workflows
- `composite/retry_orchestrator` - Retry logic with backoff

**Common Features**:
- Step-by-step execution
- Conditional branching
- Error recovery
- Progress tracking

### 7. Temporal Patterns (`temporal/`)

Time-based constraints and versioning.

**Patterns**:
- `temporal/non_overlapping_daterange` - Prevent date overlaps

**Common Features**:
- Date range validation
- Temporal constraints
- Versioning support

---

## Pattern Deep Dive

### CRUD Patterns

#### `crud/create` - Enhanced Entity Creation

**Features**:
- Duplicate detection
- Identifier sequence generation
- Projection refresh
- Consistent error handling

**Configuration**:

```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      # Duplicate check configuration
      duplicate_check:
        fields: [customer_org, customer_contract_id]
        error_message: "Contract already exists for this customer"
        error_code: "DUPLICATE_CONTRACT"

      # Projection refresh
      refresh_projection: contract_projection

      # Custom validation
      pre_validations:
        - condition: "total_value > 0"
          error: "Contract value must be positive"
```

**Generated SQL**:

```sql
CREATE OR REPLACE FUNCTION app.create_contract(user_id uuid, input_data jsonb)
RETURNS app.mutation_result AS $$
DECLARE
  v_contract_id integer;
  v_customer_org_fk integer;
  v_duplicate_exists boolean;
BEGIN
  -- Duplicate check
  SELECT EXISTS (
    SELECT 1 FROM crm.tb_contract
    WHERE customer_org_fk = (SELECT pk_organization FROM crm.tb_organization WHERE id = (input_data->>'customer_org')::uuid)
      AND customer_contract_id = input_data->>'customer_contract_id'
      AND deleted_at IS NULL
  ) INTO v_duplicate_exists;

  IF v_duplicate_exists THEN
    RAISE EXCEPTION 'Contract already exists for this customer'
      USING ERRCODE = 'P0001', HINT = 'DUPLICATE_CONTRACT';
  END IF;

  -- Pre-validations
  IF NOT ((input_data->>'total_value')::numeric > 0) THEN
    RAISE EXCEPTION 'Contract value must be positive';
  END IF;

  -- Trinity FK resolution
  SELECT pk_organization INTO v_customer_org_fk
  FROM crm.tb_organization
  WHERE id = (input_data->>'customer_org')::uuid;

  -- Insert
  INSERT INTO crm.tb_contract (
    customer_org_fk,
    customer_contract_id,
    total_value,
    created_by
  ) VALUES (
    v_customer_org_fk,
    input_data->>'customer_contract_id',
    (input_data->>'total_value')::numeric,
    user_id
  ) RETURNING pk_contract INTO v_contract_id;

  -- Identifier recalculation
  UPDATE crm.tb_contract
  SET identifier = CONCAT('CONTRACT-', v_contract_id::text)
  WHERE pk_contract = v_contract_id;

  -- Projection refresh
  REFRESH MATERIALIZED VIEW CONCURRENTLY contract_projection;

  -- Return success
  RETURN (
    'success',
    v_contract_id,
    (SELECT to_jsonb(c) FROM crm.tb_contract c WHERE pk_contract = v_contract_id),
    jsonb_build_object('_meta', jsonb_build_object(
      'impact', 'created_contract',
      'projection_refreshed', 'contract_projection'
    ))
  )::app.mutation_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

#### `crud/update` - Partial Updates

**Features**:
- CASE expression-based partial updates (only update provided fields)
- Field change auditing
- Identifier recalculation
- Projection refresh

**Configuration**:

```yaml
actions:
  - name: update_contract
    pattern: crud/update
    config:
      # Enable partial updates (only update provided fields)
      partial_updates: true

      # Track which fields were updated
      track_updated_fields: true

      # Fields that can be updated
      updatable_fields:
        - total_value
        - status
        - notes

      # Immutable fields (cannot be updated)
      immutable_fields:
        - customer_org
        - customer_contract_id

      # Refresh projection after update
      refresh_projection: contract_projection
```

**Generated SQL**:

```sql
CREATE OR REPLACE FUNCTION app.update_contract(user_id uuid, input_data jsonb)
RETURNS app.mutation_result AS $$
DECLARE
  v_contract_id integer;
  v_updated_fields text[] := '{}';
BEGIN
  -- Resolve ID
  SELECT pk_contract INTO v_contract_id
  FROM crm.tb_contract
  WHERE id = (input_data->>'id')::uuid;

  IF v_contract_id IS NULL THEN
    RAISE EXCEPTION 'Contract not found';
  END IF;

  -- Partial update using CASE expressions
  UPDATE crm.tb_contract
  SET
    total_value = CASE
      WHEN input_data ? 'total_value' THEN (input_data->>'total_value')::numeric
      ELSE total_value
    END,
    status = CASE
      WHEN input_data ? 'status' THEN input_data->>'status'
      ELSE status
    END,
    notes = CASE
      WHEN input_data ? 'notes' THEN input_data->>'notes'
      ELSE notes
    END,
    updated_at = NOW(),
    updated_by = user_id
  WHERE pk_contract = v_contract_id;

  -- Track updated fields
  IF input_data ? 'total_value' THEN v_updated_fields := array_append(v_updated_fields, 'total_value'); END IF;
  IF input_data ? 'status' THEN v_updated_fields := array_append(v_updated_fields, 'status'); END IF;
  IF input_data ? 'notes' THEN v_updated_fields := array_append(v_updated_fields, 'notes'); END IF;

  -- Refresh projection
  REFRESH MATERIALIZED VIEW CONCURRENTLY contract_projection;

  -- Return success with updated fields metadata
  RETURN (
    'success',
    v_contract_id,
    (SELECT to_jsonb(c) FROM crm.tb_contract c WHERE pk_contract = v_contract_id),
    jsonb_build_object('_meta', jsonb_build_object(
      'impact', 'updated_contract',
      'updated_fields', v_updated_fields
    ))
  )::app.mutation_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

#### `crud/delete` - Dependency-Aware Deletion

**Features**:
- Automatic dependency checking
- Hard vs soft delete support
- Consistent error messages

**Configuration**:

```yaml
actions:
  - name: delete_contract
    pattern: crud/delete
    config:
      # Support both soft and hard delete
      supports_hard_delete: true
      default_delete_type: soft

      # Check dependencies before deletion
      check_dependencies:
        - entity: ContractItem
          field: contract_id
          block_hard_delete: true
          error_message: "Cannot delete contract with items"

        - entity: Invoice
          field: contract_id
          block_hard_delete: true
          error_message: "Cannot delete contract with invoices"

      # Cascade soft deletes to children
      cascade_soft_delete:
        - entity: ContractItem
          field: contract_id
```

**Generated SQL**:

```sql
CREATE OR REPLACE FUNCTION app.delete_contract(user_id uuid, input_data jsonb)
RETURNS app.mutation_result AS $$
DECLARE
  v_contract_id integer;
  v_delete_type text;
  v_has_items boolean;
  v_has_invoices boolean;
BEGIN
  -- Resolve ID
  SELECT pk_contract INTO v_contract_id
  FROM crm.tb_contract
  WHERE id = (input_data->>'id')::uuid;

  IF v_contract_id IS NULL THEN
    RAISE EXCEPTION 'Contract not found';
  END IF;

  -- Determine delete type
  v_delete_type := COALESCE(input_data->>'delete_type', 'soft');

  -- Check dependencies
  SELECT EXISTS (
    SELECT 1 FROM crm.tb_contract_item
    WHERE contract_fk = v_contract_id AND deleted_at IS NULL
  ) INTO v_has_items;

  SELECT EXISTS (
    SELECT 1 FROM billing.tb_invoice
    WHERE contract_fk = v_contract_id AND deleted_at IS NULL
  ) INTO v_has_invoices;

  IF v_delete_type = 'hard' THEN
    IF v_has_items THEN
      RAISE EXCEPTION 'Cannot delete contract with items';
    END IF;

    IF v_has_invoices THEN
      RAISE EXCEPTION 'Cannot delete contract with invoices';
    END IF;

    -- Hard delete
    DELETE FROM crm.tb_contract WHERE pk_contract = v_contract_id;
  ELSE
    -- Soft delete
    UPDATE crm.tb_contract
    SET deleted_at = NOW(), deleted_by = user_id
    WHERE pk_contract = v_contract_id;

    -- Cascade soft delete to items
    UPDATE crm.tb_contract_item
    SET deleted_at = NOW(), deleted_by = user_id
    WHERE contract_fk = v_contract_id AND deleted_at IS NULL;
  END IF;

  -- Return success
  RETURN (
    'success',
    v_contract_id,
    jsonb_build_object('id', (SELECT id FROM crm.tb_contract WHERE pk_contract = v_contract_id)),
    jsonb_build_object('_meta', jsonb_build_object(
      'impact', 'deleted_contract',
      'delete_type', v_delete_type
    ))
  )::app.mutation_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

### State Machine Patterns

#### `state_machine/transition` - Simple State Transitions

**Features**:
- Declarative state validation
- Automatic side effects
- Audit trail generation
- Projection refresh

**Configuration**:

```yaml
actions:
  - name: submit_for_review
    pattern: state_machine/transition
    config:
      # State transition
      from_states: [draft]
      to_state: pending_review

      # Pre-transition validation
      validation_checks:
        - condition: "total_value > 0"
          error: "Contract value must be positive"
        - condition: "customer_org IS NOT NULL"
          error: "Customer organization is required"

      # Side effects on successful transition
      side_effects:
        - entity: ContractEvent
          insert:
            contract_id: v_contract_id
            event_type: submitted_for_review
            created_by: user_id

      # Refresh projection
      refresh_projection: contract_projection
```

**Use Case**: Document approval workflows, order processing, lead qualification.

---

#### `state_machine/guarded_transition` - Complex Transitions

**Features**:
- Complex guard conditions (business rules)
- Multi-entity side effects
- Input field validation
- Business rule enforcement

**Configuration**:

```yaml
actions:
  - name: approve_contract
    pattern: state_machine/guarded_transition
    config:
      # State transition
      from_states: [draft, pending_review]
      to_state: approved

      # Guard conditions (must all pass)
      guards:
        - name: budget_available
          condition: |
            (SELECT budget - used_budget FROM departments WHERE id = auth_user_department_id)
            >= input_data.total_value
          error: "Contract exceeds available department budget"

        - name: manager_approval
          condition: |
            EXISTS (
              SELECT 1 FROM approvals
              WHERE contract_id = v_contract_id
                AND approver_role = 'manager'
                AND approved = TRUE
            )
          error: "Manager approval required before contract approval"

        - name: customer_active
          condition: |
            EXISTS (
              SELECT 1 FROM crm.tb_organization
              WHERE pk_organization = (SELECT customer_org_fk FROM crm.tb_contract WHERE pk_contract = v_contract_id)
                AND status = 'active'
            )
          error: "Customer organization must be active"

      # Side effects on approval
      side_effects:
        # Deduct from department budget
        - entity: Department
          update:
            used_budget: used_budget + input_data.total_value
          where: "id = auth_user_department_id"

        # Create approval event
        - entity: ContractEvent
          insert:
            contract_id: v_contract_id
            event_type: approved
            approved_by: input_data.approved_by
            approval_date: input_data.approval_date

      # Additional input fields
      input_fields:
        - name: approved_by
          type: uuid
          required: true
        - name: approval_date
          type: date
          required: true
        - name: approval_notes
          type: text
          required: false
```

**Use Case**: Financial approvals, procurement workflows, compliance checks.

---

### Validation Patterns

#### `validation/validation_chain` - Complex Validation

**Features**:
- Multiple validation rules
- Configurable error handling (stop-on-first vs collect-all)
- Field-specific validation
- Custom error messages

**Configuration**:

```yaml
actions:
  - name: validate_contract_comprehensive
    pattern: validation/validation_chain
    config:
      # Validation rules (executed in order)
      validations:
        - name: customer_exists
          field: customer_org
          condition: |
            EXISTS (
              SELECT 1 FROM crm.tb_organization
              WHERE id = (input_data->>'customer_org')::uuid
                AND status = 'active'
                AND deleted_at IS NULL
            )
          message: "Customer organization must exist and be active"
          severity: error

        - name: amount_positive
          field: total_value
          condition: "(input_data->>'total_value')::numeric > 0"
          message: "Contract total value must be positive"
          severity: error

        - name: reasonable_amount
          field: total_value
          condition: "(input_data->>'total_value')::numeric < 1000000"
          message: "Contract value exceeds $1M, requires executive approval"
          severity: warning

        - name: valid_dates
          field: start_date
          condition: |
            (input_data->>'start_date')::date <= (input_data->>'end_date')::date
          message: "Start date must be before end date"
          severity: error

      # Error handling strategy
      stop_on_first_failure: false  # Continue validation, collect all errors
      collect_all_errors: true
      return_warnings: true
```

**Use Case**: Form validation, data quality checks, pre-submission validation.

---

### Batch Operation Patterns

#### `batch/bulk_operation` - Bulk Processing

**Features**:
- Transaction-wrapped batch processing
- Configurable error handling
- Progress tracking
- Summary reporting

**Configuration**:

```yaml
actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      # Input JSONB array field
      batch_input: price_updates  # input_data.price_updates[]

      # Operation to perform per item
      operation:
        action: update
        entity: ContractItem
        set:
          unit_price: $item.unit_price
          total_price: $item.unit_price * quantity
          updated_by: user_id
        where:
          id: $item.id

      # Error handling
      error_handling: continue_on_error  # or "fail_fast"
      batch_size: 100  # Process in batches of 100

      # Return summary
      return_summary:
        processed_count: v_processed_count
        failed_count: v_failed_count
        failed_items: v_failed_items
        total_amount_updated: v_total_amount
```

**Generated SQL**:

```sql
CREATE OR REPLACE FUNCTION app.bulk_update_prices(user_id uuid, input_data jsonb)
RETURNS app.mutation_result AS $$
DECLARE
  v_item jsonb;
  v_processed_count integer := 0;
  v_failed_count integer := 0;
  v_failed_items jsonb[] := '{}';
  v_total_amount numeric := 0;
BEGIN
  -- Iterate over batch items
  FOR v_item IN SELECT * FROM jsonb_array_elements(input_data->'price_updates')
  LOOP
    BEGIN
      -- Update operation
      UPDATE crm.tb_contract_item
      SET
        unit_price = (v_item->>'unit_price')::numeric,
        total_price = (v_item->>'unit_price')::numeric * quantity,
        updated_by = user_id,
        updated_at = NOW()
      WHERE id = (v_item->>'id')::uuid;

      v_processed_count := v_processed_count + 1;
      v_total_amount := v_total_amount + (v_item->>'unit_price')::numeric;

    EXCEPTION WHEN OTHERS THEN
      v_failed_count := v_failed_count + 1;
      v_failed_items := array_append(v_failed_items, v_item || jsonb_build_object('error', SQLERRM));
    END;
  END LOOP;

  -- Return summary
  RETURN (
    'success',
    NULL,
    jsonb_build_object(
      'processed_count', v_processed_count,
      'failed_count', v_failed_count,
      'failed_items', v_failed_items,
      'total_amount_updated', v_total_amount
    ),
    jsonb_build_object('_meta', jsonb_build_object(
      'impact', 'bulk_update_prices',
      'batch_size', jsonb_array_length(input_data->'price_updates')
    ))
  )::app.mutation_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Use Case**: Price updates, bulk imports, batch status changes.

---

## Pattern Selection Guide

### Decision Tree

```
Start
│
├─ Single entity operation?
│  ├─ Yes
│  │  ├─ Creating new record? → crud/create
│  │  ├─ Updating existing? → crud/update
│  │  └─ Deleting record? → crud/delete
│  │
│  └─ No
│     ├─ State transition? → state_machine/*
│     ├─ Validation only? → validation/validation_chain
│     ├─ Batch processing? → batch/bulk_operation
│     └─ Multi-entity coordination? → multi_entity/*
│
├─ Simple state transition?
│  ├─ Yes → state_machine/transition
│  └─ No (complex rules) → state_machine/guarded_transition
│
└─ Complex workflow?
   ├─ Yes → composite/workflow_orchestrator
   └─ Conditional logic? → composite/conditional_workflow
```

### Pattern Comparison

| Pattern | Complexity | Entities | Use Case |
|---------|------------|----------|----------|
| `crud/create` | Low | 1 | Simple record creation |
| `crud/update` | Low | 1 | Simple record updates |
| `crud/delete` | Medium | 1+ | Deletion with dependencies |
| `state_machine/transition` | Medium | 1+ | Basic workflows |
| `state_machine/guarded_transition` | High | 2+ | Complex approvals |
| `validation/validation_chain` | Medium | 1+ | Multi-rule validation |
| `batch/bulk_operation` | Medium | 1 | Batch processing |
| `multi_entity/coordinated_update` | High | 2+ | Atomic multi-entity |
| `composite/workflow_orchestrator` | Very High | 3+ | Multi-step processes |

---

## Migration from Manual SQL

### Using the Migration Analyzer

SpecQL includes a CLI tool to analyze existing manual actions and suggest patterns:

```bash
# Analyze single entity
python -m src.patterns.migration_cli entities/contract.yaml

# Analyze directory
python -m src.patterns.migration_cli entities/ --report migration_report.md

# High-confidence suggestions only
python -m src.patterns.migration_cli entities/ --min-confidence 0.8
```

### Example Migration

**Before** (Manual SQL - 200 lines):
```yaml
entity: Contract
actions:
  - name: create_contract
    implementation: manual  # Links to SQL file
```

**After** (Pattern - 20 lines):
```yaml
entity: Contract
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
```

**Result**: Same functionality, 90% less code, battle-tested pattern.

---

## Performance Considerations

### SQL Efficiency

Patterns generate optimized SQL:
- **CASE expressions** for partial updates (single query)
- **Indexed lookups** for validation
- **Bulk operations** in single transaction
- **Materialized view refresh** (CONCURRENTLY when possible)

### Generation Performance

- Sub-second generation for typical entities
- Linear scaling with entity complexity
- Cached templates for repeated generation

### Runtime Performance

- Equivalent to hand-written SQL (same execution plans)
- Optimized transactions with proper locking
- Connection pooling friendly

---

## Best Practices

### 1. Start Simple, Iterate

```yaml
# Start with basic CRUD
actions:
  - name: create_contract
    pattern: crud/create

# Add validation as needed
actions:
  - name: create_contract
    pattern: crud/create
    config:
      pre_validations:
        - condition: "total_value > 0"
          error: "Value must be positive"

# Add duplicate detection
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
      pre_validations:
        - condition: "total_value > 0"
```

### 2. Use Composition Over Complexity

Instead of one mega-pattern, combine simpler ones:

```yaml
# ❌ Bad: Complex custom pattern
actions:
  - name: approve_and_invoice
    pattern: custom/complex_approval_with_invoicing

# ✅ Good: Compose simpler patterns
actions:
  - name: approve_contract
    pattern: state_machine/guarded_transition
    config:
      to_state: approved

  - name: create_invoice
    pattern: crud/create
    config:
      depends_on: approve_contract
```

### 3. Test Generated SQL

Always validate generated SQL:

```bash
# Generate and compare
specql generate entities/contract.yaml --compare reference.sql

# Run integration tests
specql test entities/contract.yaml --action create_contract
```

---

## Summary

### Pattern Categories

| Category | Patterns | Use Cases |
|----------|----------|-----------|
| **CRUD** | create, update, delete | Basic entity operations |
| **State Machine** | transition, guarded_transition | Workflows, approvals |
| **Validation** | validation_chain | Complex validation |
| **Batch** | bulk_operation | Bulk processing |
| **Multi-Entity** | coordinated_update, saga | Distributed transactions |
| **Composite** | workflow_orchestrator | Complex processes |
| **Temporal** | non_overlapping_daterange | Time-based constraints |

### Key Benefits

1. **80% Code Reduction**: 200 lines SQL → 20 lines YAML
2. **Battle-Tested**: Proven patterns from production systems
3. **Consistent Architecture**: Same structure across all actions
4. **Self-Documenting**: Business intent clear in YAML
5. **Type-Safe**: Automatic type checking and validation

### Next Steps

1. **Explore stdlib Entities**: See `crm-entities.md`, `geo-entities.md` for pre-built entities
2. **Learn Infrastructure**: See `infrastructure-overview.md` for deployment
3. **Reference Documentation**: Check `action-steps.md` for step-level syntax

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: Complete action pattern library documentation
