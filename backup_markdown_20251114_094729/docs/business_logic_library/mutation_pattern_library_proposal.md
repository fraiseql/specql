# Enhancement: Complete Mutation Pattern Library with Business Logic Actions

## 🎯 Executive Summary

SpecQL's generated mutations follow the correct architectural pattern (app wrapper + core logic) and match the PrintOptim reference implementation structure. However, several critical features from the reference implementation are missing, preventing full production readiness.

This issue proposes building a **comprehensive mutation pattern library** similar to stdlib's reference entity library, allowing users to specify business logic actions in YAML and have complete, production-ready SQL functions generated.

---

## 🏗️ Current State

**What Works Well** ✅:
- Two-tier architecture (app wrapper + core logic)
- Input type conversion (JSONB → typed composites)
- Basic validation (required fields, FK existence)
- Trinity pattern integration (UUID → INTEGER helpers)
- FraiseQL metadata comments
- Audit logging via `app.log_and_return_mutation()`
- Soft delete implementation

**What's Missing** ⚠️:
- Partial update support (only update fields present in payload)
- Duplicate detection (business uniqueness constraints)
- Identifier recalculation (Trinity identifier pattern)
- Materialized view refresh (GraphQL projection sync)
- Hard delete with dependency checking
- Business action implementations (currently scaffolds only)

---

## 📋 Priority 1: Core CRUD Gaps

### Gap #1: Partial Updates (CASE-based Field Updates)

**Current Behavior**: Generated update functions appear to perform full-field updates.

**Expected Behavior**: Only update fields present in the input payload (like PATCH in REST APIs).

**Reference Implementation** (`reference_sql/0_schema/03_functions/034_dim/0344_agreement/03441_contract/034412_update_contract.sql:112-150`):

```sql
-- PrintOptim Reference: Partial updates using CASE expressions
UPDATE tenant.tb_contract
SET
    customer_contract_id = CASE WHEN input_payload ? 'customer_contract_id'
                               THEN input_data.customer_contract_id
                               ELSE customer_contract_id END,
    provider_contract_id = CASE WHEN input_payload ? 'provider_contract_id'
                               THEN input_data.provider_contract_id
                               ELSE provider_contract_id END,
    fk_provider_org = CASE WHEN input_payload ? 'provider_id'
                          THEN input_data.provider_id
                          ELSE fk_provider_org END,
    signature_date = CASE WHEN input_payload ? 'signature_date'
                         THEN input_data.signature_date
                         ELSE signature_date END,
    -- ... more fields ...
    updated_at = NOW(),
    updated_by = input_updated_by
WHERE pk_contract = input_pk_entity
  AND fk_customer_org = input_pk_organization;

-- Track which fields were in the update request
IF input_payload ? 'customer_contract_id' THEN
    v_updated_fields := v_updated_fields || ARRAY['customer_contract_id'];
END IF;
-- ... more tracking ...
```

**SpecQL Generated** (needs enhancement):

```sql
-- Current: Appears to update all fields regardless of presence
UPDATE tenant.tb_contract_item
SET
    item_identifier = input_data.item_identifier,
    description = input_data.description,
    -- ... all fields ...
    updated_at = now(),
    updated_by = auth_user_id
WHERE id = v_contractitem_id;
```

**Proposed SpecQL Enhancement**:

```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant
fields:
  customer_contract_id: text
  provider_contract_id: text
  signature_date: date
  # ...

actions:
  - name: update_contract
    partial_updates: true  # Enable CASE-based partial updates
    track_updated_fields: true  # Track which fields changed
```

**Impact**:
- ❌ Current: Client must always send full entity to avoid nullifying fields
- ✅ Expected: Client can send only changed fields (PATCH semantics)
- 🎯 **Critical for API usability**

---

### Gap #2: Duplicate Detection (Business Uniqueness Constraints)

**Current Behavior**: No duplicate checking beyond database constraints.

**Expected Behavior**: Check business uniqueness rules before INSERT, return structured NOOP if duplicate exists.

**Reference Implementation** (`reference_sql/0_schema/03_functions/034_dim/0344_agreement/03441_contract/034411_create_contract.sql:126-169`):

```sql
-- PrintOptim Reference: Check for existing contract with business key
SELECT pk_contract INTO v_existing_id
FROM tenant.tb_contract
WHERE fk_customer_org = input_pk_organization
  AND fk_provider_org = input_data.provider_id
  AND customer_contract_id = input_data.customer_contract_id
LIMIT 1;

IF v_existing_id IS NOT NULL THEN
    SELECT data INTO v_payload_before
    FROM public.tv_contract
    WHERE id = v_existing_id;

    v_op := 'NOOP';
    v_status := 'noop:already_exists';
    v_message := 'Contract already exists.';
    v_reason := 'unique_constraint_violation';
    v_fields := ARRAY[]::TEXT[];
    v_extra_metadata := jsonb_build_object(
        'trigger', 'api_create',
        'status', v_status,
        'reason', v_reason,
        'conflict', jsonb_build_object(
            'client_id', input_pk_organization,
            'provider_id', input_data.provider_id,
            'customer_contract_id', input_data.customer_contract_id,
            'conflict_object', v_payload_before
        )
    );

    RETURN core.log_and_return_mutation(
        input_pk_organization,
        input_created_by,
        v_entity,
        v_existing_id,
        v_op,
        v_status,
        v_fields,
        v_message,
        v_payload_before,
        v_payload_before,
        v_extra_metadata
    );
END IF;
```

**SpecQL Generated** (needs enhancement):

```sql
-- Current: No duplicate detection
INSERT INTO tenant.tb_contract_item (...)
VALUES (...);
-- May fail with generic constraint violation
```

**Proposed SpecQL Enhancement**:

```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant
fields:
  customer_contract_id: text
  provider_org: ref(Organization)
  # ...

constraints:
  - name: unique_customer_provider_contract
    type: unique
    fields: [customer_org, provider_org, customer_contract_id]
    check_on_create: true
    error_message: "Contract already exists for this customer/provider/contract_id combination"
    return_conflict_object: true  # Include existing entity in NOOP response

actions:
  - name: create_contract
    duplicate_detection: true  # Generate duplicate check code
```

**Impact**:
- ❌ Current: Generic constraint violation error
- ✅ Expected: Structured NOOP response with conflict details
- 🎯 **Critical for API error handling and idempotency**

---

### Gap #3: Identifier Recalculation (Trinity Identifier Pattern)

**Current Behavior**: No automatic identifier recalculation after INSERT/UPDATE.

**Expected Behavior**: After creating/updating an entity, recalculate its business identifier based on domain rules.

**Reference Implementation** (`reference_sql/0_schema/03_functions/034_dim/0344_agreement/03441_contract/034411_create_contract.sql:214-215`):

```sql
-- PrintOptim Reference: Recalculate identifier after INSERT
INSERT INTO tenant.tb_contract (
    pk_contract,
    fk_customer_org,
    identifier,  -- Initially: 'pending:' || uuid
    -- ... other fields ...
) VALUES (
    v_id,
    input_pk_organization,
    v_initial_identifier,  -- 'pending:01234567-...'
    -- ...
);

-- Recalculate business identifier
PERFORM core.recalcid_contract(v_ctx);
-- Updates identifier to: 'CONTRACT-2024-001' or similar

-- Refresh the contract projection
PERFORM app.refresh_single_contract(v_id);
```

**Corresponding Recalculation Function** (`reference_sql/0_schema/03_functions/030_common/0301_recalcid/`):

```sql
-- Example: core.recalcid_contract
CREATE OR REPLACE FUNCTION core.recalcid_contract(
    ctx core.recalculation_context
) RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_new_identifier TEXT;
BEGIN
    -- Business logic to calculate identifier
    SELECT 'CONTRACT-' ||
           to_char(signature_date, 'YYYY') || '-' ||
           lpad(seq_number::TEXT, 3, '0')
    INTO v_new_identifier
    FROM tenant.tb_contract
    WHERE pk_contract = ctx.entity_id;

    -- Update the identifier
    UPDATE tenant.tb_contract
    SET identifier = v_new_identifier
    WHERE pk_contract = ctx.entity_id;
END;
$$;
```

**SpecQL Generated** (needs enhancement):

```sql
-- Current: No identifier recalculation
INSERT INTO tenant.tb_contract_item (...)
VALUES (...);
-- identifier remains NULL or initial value
```

**Proposed SpecQL Enhancement**:

```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant
fields:
  customer_contract_id: text
  signature_date: date
  # ... (identifier is auto-added by Trinity pattern)

identifier:
  pattern: "CONTRACT-{signature_date:YYYY}-{sequence:03d}"
  sequence:
    scope: [customer_org]  # Reset sequence per customer
    group_by: [signature_date:YYYY]  # Reset yearly
  recalculate_on: [create, update]  # When to recalculate

actions:
  - name: create_contract
    recalculate_identifier: true  # Generate recalculation call
```

**Generated SQL**:

```sql
-- SpecQL should generate:
INSERT INTO tenant.tb_contract (..., identifier, ...)
VALUES (..., 'pending:' || v_contract_id, ...);

-- Call auto-generated recalculation function
PERFORM tenant.recalcid_contract(
    v_contract_id,
    auth_tenant_id,
    auth_user_id
);
```

**Impact**:
- ❌ Current: Identifiers remain pending or NULL
- ✅ Expected: Human-readable business identifiers auto-generated
- 🎯 **Critical for business processes and user experience**

---

### Gap #4: Materialized View Refresh (GraphQL Projection Sync)

**Current Behavior**: No view refresh after mutations.

**Expected Behavior**: Refresh GraphQL projections (materialized views) after mutations to keep data in sync.

**Reference Implementation** (`reference_sql/0_schema/03_functions/034_dim/0344_agreement/03441_contract/034411_create_contract.sql:218`):

```sql
-- PrintOptim Reference: Refresh projection after mutation
INSERT INTO tenant.tb_contract (...) VALUES (...);

PERFORM core.recalcid_contract(v_ctx);

-- Refresh the contract projection (for GraphQL queries)
PERFORM app.refresh_single_contract(v_id);

-- Final payload from materialized view
SELECT data INTO v_payload_after
FROM public.tv_contract  -- Materialized view with JOINs
WHERE id = v_id;
```

**Refresh Function Pattern**:

```sql
-- Example: app.refresh_single_contract
CREATE OR REPLACE FUNCTION app.refresh_single_contract(
    input_pk_contract UUID
) RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
    -- Refresh materialized view row for this entity
    DELETE FROM public.tv_contract WHERE id = input_pk_contract;

    INSERT INTO public.tv_contract
    SELECT
        c.pk_contract AS id,
        c.identifier,
        jsonb_build_object(
            'id', c.pk_contract,
            'identifier', c.identifier,
            'customer', jsonb_build_object('id', org.pk_organization, 'name', org.name),
            'provider', jsonb_build_object('id', prov.pk_organization, 'name', prov.name),
            'currency', jsonb_build_object('code', curr.iso_code, 'symbol', curr.symbol),
            'contractItems', (SELECT jsonb_agg(ci.*) FROM tenant.tb_contract_item ci WHERE ci.fk_contract = c.id)
        ) AS data
    FROM tenant.tb_contract c
    LEFT JOIN management.tb_organization org ON c.fk_customer_org = org.pk_organization
    LEFT JOIN management.tb_organization prov ON c.fk_provider_org = prov.pk_organization
    LEFT JOIN catalog.tb_currency curr ON c.fk_currency = curr.pk_currency
    WHERE c.pk_contract = input_pk_contract;
END;
$$;
```

**SpecQL Generated** (needs enhancement):

```sql
-- Current: No view refresh
INSERT INTO tenant.tb_contract_item (...)
VALUES (...);

-- Return from base table
RETURN app.log_and_return_mutation(
    ...,
    (SELECT row_to_json(t.*) FROM tenant.tb_contract_item t WHERE t.id = v_contractitem_id)::JSONB,
    NULL
);
-- GraphQL projection is stale!
```

**Proposed SpecQL Enhancement**:

```yaml
# entities/tenant/contract.yaml
entity: Contract
schema: tenant
fields:
  customer_org: ref(Organization)
  provider_org: ref(Organization)
  currency: ref(Currency)
  # ...

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
    refresh_projection: graphql_view
  - name: update_contract
    refresh_projection: graphql_view
```

**Generated SQL**:

```sql
-- SpecQL should generate view refresh function
CREATE OR REPLACE FUNCTION tenant.refresh_contract_projection(
    entity_id UUID,
    tenant_id UUID
) RETURNS VOID AS $$ ... $$;

-- And call it after mutation
INSERT INTO tenant.tb_contract (...) VALUES (...);
PERFORM tenant.recalcid_contract(v_contract_id, auth_tenant_id, auth_user_id);
PERFORM tenant.refresh_contract_projection(v_contract_id, auth_tenant_id);

-- Return from projection
SELECT data INTO v_payload_after
FROM tenant.v_contract_projection
WHERE id = v_contract_id;
```

**Impact**:
- ❌ Current: GraphQL queries return stale data
- ✅ Expected: GraphQL queries immediately reflect mutations
- 🎯 **Critical for GraphQL API correctness**

---

## 📋 Priority 2: Enhanced CRUD Features

### Gap #5: Hard Delete with Dependency Checking

**Current Behavior**: Only soft delete (sets `deleted_at`).

**Expected Behavior**: Support hard delete (physical removal) with dependency checking, configurable per entity.

**Reference Implementation** (`reference_sql/0_schema/03_functions/034_dim/0345_mat/03451_machine/034513_delete_machine.sql`):

```sql
-- PrintOptim Reference: Hard delete with dependency checks
CREATE OR REPLACE FUNCTION core.delete_machine(
    input_pk_entity UUID,
    input_pk_organization UUID,
    input_hard_delete BOOLEAN,
    input_deleted_by UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_has_dependencies BOOLEAN := FALSE;
    v_dependency_details JSONB;
BEGIN
    -- Check for dependencies
    SELECT
        COUNT(*) > 0,
        jsonb_build_object(
            'allocations', (SELECT COUNT(*) FROM tenant.tb_allocation WHERE fk_machine = input_pk_entity),
            'orders', (SELECT COUNT(*) FROM tenant.tb_order_line WHERE fk_machine = input_pk_entity),
            'machine_items', (SELECT COUNT(*) FROM tenant.tb_machine_item WHERE fk_machine = input_pk_entity)
        )
    INTO v_has_dependencies, v_dependency_details
    FROM tenant.tb_allocation
    WHERE fk_machine = input_pk_entity;

    -- If hard delete requested but dependencies exist, block it
    IF input_hard_delete AND v_has_dependencies THEN
        RETURN core.log_and_return_mutation(
            input_pk_organization,
            input_deleted_by,
            'machine',
            input_pk_entity,
            'NOOP',
            'noop:cannot_delete_machine_with_dependencies',
            ARRAY[]::TEXT[],
            'Cannot hard delete machine with dependencies',
            NULL, NULL,
            jsonb_build_object(
                'reason', 'has_dependencies',
                'dependencies', v_dependency_details,
                'suggestion', 'Use soft delete or remove dependencies first'
            )
        );
    END IF;

    -- Hard delete if requested and no dependencies
    IF input_hard_delete AND NOT v_has_dependencies THEN
        DELETE FROM tenant.tb_machine
        WHERE pk_machine = input_pk_entity
          AND fk_customer_org = input_pk_organization;

        RETURN core.log_and_return_mutation(..., 'DELETE', 'deleted', ...);
    END IF;

    -- Soft delete (default)
    UPDATE tenant.tb_machine
    SET deleted_at = NOW(), deleted_by = input_deleted_by
    WHERE pk_machine = input_pk_entity
      AND fk_customer_org = input_pk_organization;

    RETURN core.log_and_return_mutation(..., 'UPDATE', 'updated', ...);
END;
$$;
```

**SpecQL Generated** (needs enhancement):

```sql
-- Current: Soft delete only
UPDATE tenant.tb_contract_item
SET deleted_at = now(), deleted_by = auth_user_id
WHERE id = v_contractitem_id;
```

**Proposed SpecQL Enhancement**:

```yaml
# entities/tenant/machine.yaml
entity: Machine
schema: tenant
fields:
  serial_number: text
  # ...

delete_policy:
  default: soft  # soft or hard
  allow_hard_delete: true
  check_dependencies:
    - entity: Allocation
      field: machine
      block_hard_delete: true
      error_message: "Cannot delete machine with active allocations"
    - entity: OrderLine
      field: machine
      block_hard_delete: true
    - entity: MachineItem
      field: machine
      cascade: soft_delete  # Soft delete children instead of blocking

actions:
  - name: delete_machine
    supports_hard_delete: true
    dependency_check: true
```

**Generated SQL**:

```sql
CREATE OR REPLACE FUNCTION app.delete_machine(
    auth_tenant_id UUID,
    auth_user_id UUID,
    input_payload JSONB  -- {id: UUID, hard_delete?: boolean}
) RETURNS app.mutation_result AS $$
DECLARE
    input_hard_delete BOOLEAN := COALESCE((input_payload->>'hard_delete')::BOOLEAN, FALSE);
BEGIN
    -- Check dependencies if hard delete requested
    -- Perform soft or hard delete based on input
    -- Return appropriate mutation_result
END;
$$;
```

**Impact**:
- ❌ Current: Cannot physically remove test/invalid data
- ✅ Expected: Flexible delete strategy with safety checks
- 🎯 **Important for data maintenance and compliance (GDPR)**

---

## 📋 Priority 3: Business Logic Action Library

### Gap #6: Business Action Implementation Library

**Current Behavior**: Business actions generate scaffolds with placeholder implementations.

**Expected Behavior**: Library of common business action patterns that can be composed and customized.

**Reference Implementation Examples**:

#### Example 1: State Machine Transition (`decommission_machine`)

```sql
-- PrintOptim Reference: Complex state machine transition
CREATE OR REPLACE FUNCTION core.decommission_machine(
    input_pk_entity UUID,
    input_pk_organization UUID,
    input_data app.type_decommission_input,
    input_payload JSONB,
    input_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_machine tenant.tb_machine%ROWTYPE;
    v_active_allocations INTEGER;
BEGIN
    -- Load current machine
    SELECT * INTO v_machine
    FROM tenant.tb_machine
    WHERE pk_machine = input_pk_entity
      AND fk_customer_org = input_pk_organization;

    -- Check current status
    IF v_machine.status != 'active' THEN
        RETURN core.log_and_return_mutation(
            ..., 'NOOP', 'noop:invalid_status_transition',
            'Can only decommission active machines', ...
        );
    END IF;

    -- Check for active allocations
    SELECT COUNT(*) INTO v_active_allocations
    FROM tenant.tb_allocation
    WHERE fk_machine = input_pk_entity
      AND status = 'active';

    IF v_active_allocations > 0 THEN
        RETURN core.log_and_return_mutation(
            ..., 'NOOP', 'noop:has_active_allocations',
            'Cannot decommission machine with active allocations', ...
        );
    END IF;

    -- Update machine status
    UPDATE tenant.tb_machine
    SET
        status = 'decommissioned',
        decommission_date = input_data.decommission_date,
        decommission_reason = input_data.reason,
        updated_at = NOW(),
        updated_by = input_user_id
    WHERE pk_machine = input_pk_entity;

    -- Archive related data
    UPDATE tenant.tb_machine_item
    SET status = 'archived'
    WHERE fk_machine = input_pk_entity;

    -- Log event
    INSERT INTO tenant.tb_machine_event (fk_machine, event_type, event_data)
    VALUES (input_pk_entity, 'decommissioned', input_payload);

    -- Refresh projection
    PERFORM app.refresh_single_machine(input_pk_entity);

    RETURN core.log_and_return_mutation(
        ..., 'UPDATE', 'success', 'Machine decommissioned', ...
    );
END;
$$;
```

#### Example 2: Multi-Entity Operation (`allocate_to_stock`)

```sql
-- PrintOptim Reference: Multi-table allocation
CREATE OR REPLACE FUNCTION core.allocate_to_stock(
    input_pk_organization UUID,
    input_data app.type_allocation_input,
    input_payload JSONB,
    input_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_allocation_id UUID := gen_random_uuid();
    v_machine_id UUID;
    v_stock_location_id UUID;
BEGIN
    -- Validate machine availability
    SELECT pk_machine INTO v_machine_id
    FROM tenant.tb_machine
    WHERE pk_machine = input_data.machine_id
      AND fk_customer_org = input_pk_organization
      AND status = 'available'
      AND deleted_at IS NULL;

    IF v_machine_id IS NULL THEN
        RETURN core.log_and_return_mutation(
            ..., 'NOOP', 'noop:machine_not_available', ...
        );
    END IF;

    -- Get or create stock location
    SELECT pk_location INTO v_stock_location_id
    FROM tenant.tb_location
    WHERE code = 'STOCK'
      AND fk_customer_org = input_pk_organization;

    IF v_stock_location_id IS NULL THEN
        -- Create stock location
        INSERT INTO tenant.tb_location (pk_location, fk_customer_org, code, name)
        VALUES (gen_random_uuid(), input_pk_organization, 'STOCK', 'Stock')
        RETURNING pk_location INTO v_stock_location_id;
    END IF;

    -- Create allocation
    INSERT INTO tenant.tb_allocation (
        pk_allocation,
        fk_customer_org,
        fk_machine,
        fk_location,
        allocation_type,
        status,
        allocated_at,
        created_by
    ) VALUES (
        v_allocation_id,
        input_pk_organization,
        v_machine_id,
        v_stock_location_id,
        'stock',
        'active',
        NOW(),
        input_user_id
    );

    -- Update machine status
    UPDATE tenant.tb_machine
    SET
        status = 'in_stock',
        current_location = v_stock_location_id,
        updated_at = NOW()
    WHERE pk_machine = v_machine_id;

    -- Log event
    INSERT INTO tenant.tb_allocation_event (fk_allocation, event_type)
    VALUES (v_allocation_id, 'allocated_to_stock');

    -- Refresh projections
    PERFORM app.refresh_single_machine(v_machine_id);
    PERFORM app.refresh_single_allocation(v_allocation_id);

    RETURN core.log_and_return_mutation(
        ..., 'INSERT', 'success', 'Machine allocated to stock', ...
    );
END;
$$;
```

#### Example 3: Batch Operation (`bulk_update_prices`)

```sql
-- PrintOptim Reference: Batch operation with transaction
CREATE OR REPLACE FUNCTION core.bulk_update_prices(
    input_pk_organization UUID,
    input_data app.type_bulk_price_update_input,
    input_payload JSONB,
    input_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_updated_count INTEGER := 0;
    v_failed_count INTEGER := 0;
    v_failed_items JSONB := '[]'::JSONB;
    v_price_item JSONB;
BEGIN
    -- Iterate over price updates
    FOR v_price_item IN SELECT * FROM jsonb_array_elements(input_data.price_updates)
    LOOP
        BEGIN
            UPDATE tenant.tb_contract_item
            SET
                unit_price = (v_price_item->>'unit_price')::DECIMAL,
                updated_at = NOW(),
                updated_by = input_user_id
            WHERE pk_contract_item = (v_price_item->>'id')::UUID
              AND fk_customer_org = input_pk_organization;

            IF FOUND THEN
                v_updated_count := v_updated_count + 1;
            ELSE
                v_failed_count := v_failed_count + 1;
                v_failed_items := v_failed_items || jsonb_build_object(
                    'id', v_price_item->>'id',
                    'reason', 'not_found'
                );
            END IF;
        EXCEPTION WHEN OTHERS THEN
            v_failed_count := v_failed_count + 1;
            v_failed_items := v_failed_items || jsonb_build_object(
                'id', v_price_item->>'id',
                'reason', SQLERRM
            );
        END;
    END LOOP;

    -- Refresh affected contracts
    PERFORM app.refresh_contracts_by_org(input_pk_organization);

    RETURN core.log_and_return_mutation(
        input_pk_organization,
        input_user_id,
        'contract_item',
        '00000000-0000-0000-0000-000000000000'::UUID,
        'BATCH_UPDATE',
        'success',
        ARRAY[]::TEXT[],
        format('Updated %s prices, %s failed', v_updated_count, v_failed_count),
        NULL,
        NULL,
        jsonb_build_object(
            'updated_count', v_updated_count,
            'failed_count', v_failed_count,
            'failed_items', v_failed_items
        )
    );
END;
$$;
```

**Proposed SpecQL Action Library**:

```yaml
# Library: stdlib/actions/state_machine.yaml
action_pattern: state_machine
description: "Transition entity between states with validation"
parameters:
  - name: from_states
    type: array
    description: "Valid source states for transition"
  - name: to_state
    type: string
    description: "Target state"
  - name: validation_checks
    type: array
    description: "Pre-transition validations"
  - name: side_effects
    type: array
    description: "Updates to perform on success"

# Library: stdlib/actions/multi_entity_operation.yaml
action_pattern: multi_entity_operation
description: "Coordinate changes across multiple entities"
parameters:
  - name: primary_entity
    type: string
  - name: related_updates
    type: array
    description: "Updates to related entities"
  - name: transaction_scope
    type: string
    default: "serializable"

# Library: stdlib/actions/batch_operation.yaml
action_pattern: batch_operation
description: "Process multiple records in a single transaction"
parameters:
  - name: batch_input
    type: array
  - name: error_handling
    type: enum
    values: [stop_on_error, continue_on_error, rollback_on_any_error]
  - name: batch_size
    type: integer
    default: 100
```

**Usage in Entity YAML**:

```yaml
# entities/tenant/machine.yaml
entity: Machine
schema: tenant
fields:
  status: enum(available, in_stock, allocated, decommissioned, maintenance)
  decommission_date: date
  decommission_reason: text

actions:
  # CRUD (auto-generated)
  - name: create_machine
  - name: update_machine
  - name: delete_machine

  # Business actions using library patterns
  - name: decommission_machine
    pattern: state_machine
    from_states: [active, maintenance]
    to_state: decommissioned
    validation_checks:
      - check: no_active_allocations
        entity: Allocation
        condition: "status = 'active' AND machine_id = $entity_id"
        error: "Cannot decommission machine with active allocations"
    side_effects:
      - entity: MachineItem
        update:
          status: archived
        where: "machine_id = $entity_id"
      - entity: MachineEvent
        insert:
          machine_id: $entity_id
          event_type: 'decommissioned'
          event_data: $input_payload
    refresh_projections: [machine_projection]
    input_fields:
      - decommission_date: {type: date, required: true}
      - decommission_reason: {type: text, required: true}

  - name: allocate_to_stock
    pattern: multi_entity_operation
    description: "Allocate machine to stock location"
    primary_entity: Machine
    validations:
      - field: status
        equals: available
        error: "Only available machines can be allocated to stock"
    operations:
      - action: get_or_create
        entity: Location
        where: {code: 'STOCK', customer_org: $auth_tenant_id}
        create_if_missing:
          code: STOCK
          name: Stock
          customer_org: $auth_tenant_id
        store_as: stock_location_id

      - action: insert
        entity: Allocation
        values:
          customer_org: $auth_tenant_id
          machine_id: $entity_id
          location_id: $stock_location_id
          allocation_type: stock
          status: active
          allocated_at: now()
        store_as: allocation_id

      - action: update
        entity: Machine
        where: {id: $entity_id}
        values:
          status: in_stock
          current_location: $stock_location_id

      - action: insert
        entity: AllocationEvent
        values:
          allocation_id: $allocation_id
          event_type: allocated_to_stock

    refresh_projections: [machine_projection, allocation_projection]
    return_entity: Allocation
    return_id: $allocation_id

# entities/tenant/contract_item.yaml
actions:
  - name: bulk_update_prices
    pattern: batch_operation
    description: "Update prices for multiple contract items"
    input_type:
      price_updates:
        type: array
        items:
          id: uuid
          unit_price: decimal
    error_handling: continue_on_error
    batch_processing:
      for_each: price_updates
      update:
        entity: ContractItem
        where: {id: $item.id, customer_org: $auth_tenant_id}
        set:
          unit_price: $item.unit_price
      collect_errors: true
    refresh_projections: [contract_projection]
    return_summary:
      updated_count: count(success)
      failed_count: count(failed)
      failed_items: collect(failed, [id, reason])
```

**Generated SQL** (for `decommission_machine`):

```sql
-- SpecQL generates full implementation from pattern
CREATE OR REPLACE FUNCTION tenant.decommission_machine(
    auth_tenant_id UUID,
    input_data app.type_decommission_machine_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql AS $$
DECLARE
    v_machine_id UUID := input_data.id;
    v_current_status TEXT;
    v_active_allocations INTEGER;
BEGIN
    -- Load and validate current state
    SELECT status INTO v_current_status
    FROM tenant.tb_machine
    WHERE id = v_machine_id
      AND tenant_id = auth_tenant_id;

    -- State machine validation: from_states check
    IF v_current_status NOT IN ('active', 'maintenance') THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id, 'machine', v_machine_id,
            'NOOP', 'validation:invalid_state_transition',
            ARRAY[]::TEXT[],
            format('Cannot decommission machine in state %s', v_current_status),
            NULL, NULL,
            jsonb_build_object(
                'current_state', v_current_status,
                'valid_states', ARRAY['active', 'maintenance']
            )
        );
    END IF;

    -- Validation check: no_active_allocations
    SELECT COUNT(*) INTO v_active_allocations
    FROM tenant.tb_allocation
    WHERE machine_id = v_machine_id
      AND status = 'active'
      AND tenant_id = auth_tenant_id;

    IF v_active_allocations > 0 THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id, auth_user_id, 'machine', v_machine_id,
            'NOOP', 'validation:has_active_allocations',
            ARRAY[]::TEXT[],
            'Cannot decommission machine with active allocations',
            NULL, NULL,
            jsonb_build_object('active_allocations', v_active_allocations)
        );
    END IF;

    -- Primary state transition
    UPDATE tenant.tb_machine
    SET
        status = 'decommissioned',
        decommission_date = input_data.decommission_date,
        decommission_reason = input_data.decommission_reason,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_machine_id
      AND tenant_id = auth_tenant_id;

    -- Side effect: Update MachineItem
    UPDATE tenant.tb_machine_item
    SET status = 'archived', updated_at = now()
    WHERE machine_id = v_machine_id
      AND tenant_id = auth_tenant_id;

    -- Side effect: Insert MachineEvent
    INSERT INTO tenant.tb_machine_event (
        tenant_id, machine_id, event_type, event_data, created_by
    ) VALUES (
        auth_tenant_id, v_machine_id, 'decommissioned',
        input_payload, auth_user_id
    );

    -- Refresh projection
    PERFORM tenant.refresh_machine_projection(v_machine_id, auth_tenant_id);

    RETURN app.log_and_return_mutation(
        auth_tenant_id, auth_user_id, 'machine', v_machine_id,
        'UPDATE', 'success',
        ARRAY['status', 'decommission_date', 'decommission_reason'],
        'Machine decommissioned successfully',
        (SELECT row_to_json(t.*) FROM tenant.v_machine_projection t WHERE t.id = v_machine_id)::JSONB,
        NULL
    );
END;
$$;
```

**Impact**:
- ❌ Current: Business actions are scaffolds requiring manual implementation
- ✅ Expected: Declarative business logic with full implementation generated
- 🎯 **Critical for rapid development of production-ready backends**

---

## 🎯 Proposed Solution: Mutation Pattern Library

### Architecture

```
specql/
├── stdlib/
│   ├── entities/           # Reference entities (existing)
│   └── actions/            # Action pattern library (NEW)
│       ├── crud/
│       │   ├── create.yaml
│       │   ├── update.yaml           # With partial updates
│       │   ├── delete.yaml           # With hard/soft + dependencies
│       │   └── duplicate_check.yaml
│       ├── state_machine/
│       │   ├── transition.yaml
│       │   └── validation_rules.yaml
│       ├── multi_entity/
│       │   ├── coordinated_update.yaml
│       │   └── cascading_changes.yaml
│       ├── batch/
│       │   ├── bulk_operation.yaml
│       │   └── error_handling.yaml
│       └── common/
│           ├── identifier_recalc.yaml
│           ├── projection_refresh.yaml
│           └── audit_logging.yaml
```

### Benefits

1. **Declarative Business Logic**: Specify "what" not "how"
2. **Consistency**: All actions follow same patterns
3. **Reusability**: Import common patterns like stdlib entities
4. **Type Safety**: Validated at YAML level before SQL generation
5. **Maintainability**: Update pattern library, regenerate all implementations
6. **Documentation**: Patterns are self-documenting
7. **Testing**: Pattern library can have comprehensive test suite

### Example Usage

```yaml
# Import action patterns (like importing stdlib entities)
imports:
  - from: stdlib/actions/state_machine
    use: [transition, validation_rules]
  - from: stdlib/actions/multi_entity
    use: [coordinated_update]

entity: Machine
schema: tenant

actions:
  # Simple reference to library pattern
  - name: create_machine
    extends: stdlib/actions/crud/create
    duplicate_check:
      fields: [customer_org, serial_number]

  # Compose patterns
  - name: decommission_machine
    extends: stdlib/actions/state_machine/transition
    config:
      from_states: [active, maintenance]
      to_state: decommissioned
      validations:
        - no_active_allocations
      side_effects:
        - archive_machine_items
        - log_decommission_event
```

---

## 🚀 Implementation Roadmap

### Phase 1: Core CRUD Enhancements (2-3 weeks)
- [ ] Implement partial updates (CASE expressions)
- [ ] Add duplicate detection pattern
- [ ] Add identifier recalculation hooks
- [ ] Add projection refresh support

### Phase 2: Enhanced Delete (1 week)
- [ ] Implement hard delete option
- [ ] Add dependency checking
- [ ] Add cascade configuration

### Phase 3: Action Pattern Library (4-6 weeks)
- [ ] Design pattern library structure
- [ ] Implement state machine pattern
- [ ] Implement multi-entity operation pattern
- [ ] Implement batch operation pattern
- [ ] Create pattern documentation
- [ ] Add pattern validation

### Phase 4: Migration & Testing (2-3 weeks)
- [ ] Migrate reference implementation patterns
- [ ] Create pattern test suite
- [ ] Document migration guide
- [ ] Create example entities using all patterns

---

## 📚 Success Criteria

1. ✅ All CRUD operations support partial updates
2. ✅ Duplicate detection works for business uniqueness constraints
3. ✅ Identifiers auto-recalculate after mutations
4. ✅ GraphQL projections stay in sync via auto-refresh
5. ✅ Hard delete with dependency checking available
6. ✅ State machine pattern generates correct validation logic
7. ✅ Multi-entity operations maintain transactional integrity
8. ✅ Batch operations handle errors gracefully
9. ✅ Action library has 90%+ test coverage
10. ✅ Full PrintOptim reference implementation can be expressed in YAML + patterns

---

## 🔗 Related Context

- **Reference Implementation**: PrintOptim backend (`reference_sql/0_schema/03_functions/`)
- **Current Generated Code**: `specql/db/schema/30_functions/`
- **PrintOptim Analysis**: See detailed comparison in project documentation
- **SpecQL Architecture**: Two-tier functions (app wrapper + core logic)
- **Trinity Pattern**: UUID (pk) + INTEGER (id) + TEXT (identifier)
- **FraiseQL**: GraphQL metadata in SQL comments

---

## 💬 Discussion Points

1. Should action patterns be YAML or a DSL?
2. How to handle custom business logic that doesn't fit patterns?
3. Should we support pattern composition (combining multiple patterns)?
4. How to version the pattern library?
5. Should patterns generate tests automatically?

---

**Priority**: High
**Complexity**: Medium-High
**Impact**: Critical for production readiness
**Status**: Proposal for discussion
