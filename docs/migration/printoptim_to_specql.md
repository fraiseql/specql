# Migrating PrintOptim to SpecQL Patterns

This guide shows how to migrate your PrintOptim production backend from manual PL/pgSQL to declarative SpecQL YAML using the new action patterns.

## 🎯 Migration Overview

**Before**: Manual PL/pgSQL functions with complex business logic
**After**: Declarative YAML patterns that generate identical SQL

**Timeline**: <2 weeks for full migration
**Risk**: Low - patterns generate tested, production-ready SQL
**Rollback**: Instant - revert to manual functions anytime

## 📊 Current State Analysis

### What PrintOptim Currently Has
Based on your production reference implementation:

1. **Complex CRUD Operations**
   - Partial updates with field tracking
   - Duplicate detection on create
   - Identifier recalculation (Trinity pattern)
   - GraphQL projection sync

2. **Business Logic Patterns**
   - State machine transitions (Machine lifecycle)
   - Multi-entity operations (Allocation workflow)
   - Batch operations (Contract item updates)

3. **Manual PL/pgSQL Functions**
   - 200+ lines for complex workflows
   - Inconsistent error handling
   - Difficult to maintain and test

### Migration Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Code Volume** | 200 lines PL/pgSQL | 20 lines YAML |
| **Development Time** | 1 week | 1 hour |
| **Testing** | Manual SQL testing | Auto-generated + pattern tests |
| **Maintenance** | Update multiple functions | Update pattern once |
| **Consistency** | Team-dependent | Enforced by patterns |
| **Documentation** | Code comments | Self-documenting YAML |

## 🗓️ Migration Timeline

### Week 1: Core CRUD Migration

**Day 1-2: Contract CRUD**
- Migrate basic CRUD to enhanced patterns
- Add constraints and projections
- Test generated SQL matches reference

**Day 3-4: Machine CRUD**
- Migrate machine lifecycle to state machine pattern
- Implement decommissioning workflow
- Verify state transitions work

**Day 5: Testing & Validation**
- End-to-end testing of CRUD operations
- SQL comparison with reference implementation
- Performance validation

### Week 2: Business Logic Migration

**Day 1-2: Allocation Workflow**
- Migrate multi-entity allocation patterns
- Implement stock/production allocation logic
- Test transaction handling

**Day 3-4: Batch Operations**
- Migrate bulk price updates
- Implement error handling strategies
- Test batch processing performance

**Day 5: Final Integration**
- Full system testing
- Performance optimization
- Documentation updates

## 🔄 Step-by-Step Migration

### Phase 1: Enhanced CRUD Operations

#### 1.1 Add Constraints and Identifiers

**Before** (manual SQL):
```sql
-- Manual duplicate check
SELECT id INTO v_existing_id
FROM tenant.tb_contract
WHERE customer_contract_id = input_data.customer_contract_id;

IF v_existing_id IS NOT NULL THEN
    -- Return duplicate error
END IF;
```

**After** (SpecQL YAML):
```yaml
entity: Contract
constraints:
  - name: unique_customer_contract
    type: unique
    fields: [customer_org, provider_org, customer_contract_id]
    check_on_create: true
    error_message: "Contract already exists"

identifier:
  pattern: "CONTRACT-{signature_date:YYYY}-{sequence:03d}"
  recalculate_on: [create, update]
```

#### 1.2 Add Projection Sync

**Before** (manual SQL):
```sql
-- Manual projection refresh
DELETE FROM tenant.v_contract_projection WHERE id = v_contract_id;
INSERT INTO tenant.v_contract_projection SELECT ... FROM tenant.tb_contract c
LEFT JOIN management.tb_organization co ON c.customer_org = co.id
-- Complex JOIN logic
```

**After** (SpecQL YAML):
```yaml
projections:
  - name: contract_projection
    refresh_on: [create, update]
    includes:
      - customer_org: [id, name, code]
      - provider_org: [id, name, code]
      - currency: [iso_code, symbol]
```

#### 1.3 Enable Partial Updates

**Before** (manual SQL):
```sql
-- Full update of all fields
UPDATE tenant.tb_contract SET
    customer_contract_id = input_data.customer_contract_id,
    provider_contract_id = input_data.provider_contract_id,
    -- ALL fields updated regardless of input
WHERE id = v_contract_id;
```

**After** (SpecQL YAML):
```yaml
actions:
  - name: update_contract
    partial_updates: true
    track_updated_fields: true
```

### Phase 2: State Machine Patterns

#### 2.1 Machine Lifecycle Migration

**Before** (200 lines PL/pgSQL):
```sql
CREATE OR REPLACE FUNCTION app.decommission_machine(...) RETURNS mutation_result AS $$
DECLARE
    v_current_status TEXT;
    v_allocation_count INTEGER;
BEGIN
    -- Check current status
    SELECT status INTO v_current_status FROM tenant.tb_machine WHERE id = v_machine_id;

    -- Validate no active allocations
    SELECT COUNT(*) INTO v_allocation_count FROM tenant.tb_allocation
    WHERE machine_id = v_machine_id AND status = 'active';

    IF v_allocation_count > 0 THEN
        RETURN error_response('Cannot decommission with allocations');
    END IF;

    -- Update machine status
    UPDATE tenant.tb_machine SET status = 'decommissioned', ... WHERE id = v_machine_id;

    -- Archive machine items
    UPDATE tenant.tb_machine_item SET status = 'archived' WHERE machine_id = v_machine_id;

    -- Log event
    INSERT INTO tenant.tb_machine_event (...) VALUES (...);

    RETURN success_response();
END;
$$;
```

**After** (20 lines YAML):
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
        - condition: "NOT EXISTS (SELECT 1 FROM tenant.tb_allocation WHERE machine_id = v_machine_id AND status = 'active')"
          error: "Cannot decommission machine with active allocations"
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

### Phase 3: Multi-Entity Operations

#### 3.1 Allocation Workflow Migration

**Before** (manual transaction):
```sql
BEGIN;
    -- Get or create stock location
    SELECT id INTO v_location_id FROM tenant.tb_location
    WHERE code = 'STOCK';

    IF v_location_id IS NULL THEN
        INSERT INTO tenant.tb_location (code, name) VALUES ('STOCK', 'Stock')
        RETURNING id INTO v_location_id;
    END IF;

    -- Create allocation
    INSERT INTO tenant.tb_allocation (...) VALUES (...);

    -- Update machine
    UPDATE tenant.tb_machine SET status = 'in_stock' WHERE id = v_machine_id;

COMMIT;
```

**After** (declarative pattern):
```yaml
actions:
  - name: allocate_to_stock
    pattern: multi_entity/coordinated_update
    config:
      operations:
        - action: get_or_create
          entity: Location
          where: {code: 'STOCK'}
          create_if_missing:
            code: STOCK
            name: 'Stock Location'
            location_type: warehouse
          store_as: stock_location_id

        - action: insert
          entity: Allocation
          values:
            machine_id: $input.machine_id
            location_id: $stock_location_id
            allocation_type: stock
            status: active

        - action: update
          entity: Machine
          set: {status: in_stock, location_id: $stock_location_id}
          where: {id: $input.machine_id}
```

### Phase 4: Batch Operations

#### 4.1 Bulk Price Updates Migration

**Before** (manual loop):
```sql
CREATE OR REPLACE FUNCTION app.bulk_update_prices(price_updates JSONB) RETURNS mutation_result AS $$
DECLARE
    v_item JSONB;
    v_updated_count INTEGER := 0;
    v_failed_count INTEGER := 0;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(price_updates)
    LOOP
        BEGIN
            UPDATE tenant.tb_contract_item
            SET unit_price = (v_item->>'unit_price')::DECIMAL
            WHERE id = (v_item->>'id')::UUID;

            v_updated_count := v_updated_count + 1;
        EXCEPTION WHEN OTHERS THEN
            v_failed_count := v_failed_count + 1;
        END;
    END LOOP;

    RETURN success_response(v_updated_count || ' updated, ' || v_failed_count || ' failed');
END;
$$;
```

**After** (pattern-based):
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
        where: {id: $item.id}
      error_handling: continue_on_error
      return_summary:
        processed_count: v_processed_count
        failed_count: v_failed_count
        failed_items: v_failed_items
```

## 🧪 Testing Strategy

### 1. SQL Comparison Testing

Compare generated SQL with reference implementation:

```bash
# Generate SpecQL SQL
specql generate --entity contract

# Compare with reference
diff generated_contract.sql reference_contract.sql
```

### 2. Functional Testing

Test that patterns produce identical results:

```sql
-- Test duplicate detection
SELECT * FROM app.create_contract('{"customer_contract_id": "DUPE"}');

-- Should return NOOP with conflict details in both implementations
```

### 3. Performance Testing

Ensure patterns don't introduce performance regressions:

```sql
-- Benchmark pattern-generated functions
EXPLAIN ANALYZE SELECT * FROM app.create_contract(input_data);
```

### 4. Integration Testing

Test end-to-end workflows:

```yaml
# Test machine lifecycle
1. Create machine
2. Allocate to stock
3. Move to production
4. Start maintenance
5. End maintenance
6. Decommission
```

## 🚨 Migration Checklist

### Pre-Migration
- [ ] Backup production database
- [ ] Document current manual functions
- [ ] Set up test environment
- [ ] Train team on pattern syntax

### CRUD Migration
- [ ] Add entity constraints
- [ ] Configure identifiers
- [ ] Set up projections
- [ ] Enable partial updates
- [ ] Test CRUD operations

### Business Logic Migration
- [ ] Identify state machines
- [ ] Convert to state_machine/transition patterns
- [ ] Identify multi-entity operations
- [ ] Convert to multi_entity/coordinated_update patterns
- [ ] Identify batch operations
- [ ] Convert to batch/bulk_operation patterns

### Testing & Validation
- [ ] SQL equivalence testing
- [ ] Functional testing
- [ ] Performance testing
- [ ] Integration testing
- [ ] User acceptance testing

### Go-Live
- [ ] Deploy to staging
- [ ] Run parallel with old system
- [ ] Monitor performance and errors
- [ ] Gradual rollout to production
- [ ] Remove old manual functions

## 🆘 Rollback Plan

If issues arise during migration:

### Immediate Rollback
```sql
-- Revert to manual functions
DROP FUNCTION app.create_contract(uuid, uuid, jsonb);
-- Restore backup of manual function
```

### Gradual Rollback
```sql
-- Route some traffic to old functions
-- while fixing pattern issues
```

### Pattern Fixes
```yaml
# Fix pattern configuration
actions:
  - name: create_contract
    # Add missing validation
    duplicate_detection: true
```

## 📞 Support During Migration

### Real-time Support
- **Slack Channel**: #specql-migration
- **Daily Check-ins**: 30-minute sync meetings
- **Pair Programming**: Remote sessions for complex migrations

### Resources Provided
- **Migration Scripts**: Automated SQL comparison tools
- **Example Migrations**: Complete before/after examples
- **Testing Framework**: Automated test generation
- **Documentation**: Updated as you migrate

### Success Metrics
- [ ] All CRUD operations migrated (< 1 week)
- [ ] All business logic patterns migrated (< 1 week)
- [ ] 100% test coverage maintained
- [ ] Performance meets or exceeds current system
- [ ] Team comfortable with pattern-based development

## 🎯 Post-Migration Benefits

### Development Speed
- **Complex workflows**: 1 hour instead of 1 week
- **Bug fixes**: Update pattern once, regenerate everywhere
- **New features**: Copy proven patterns, customize for needs

### Code Quality
- **Consistency**: All similar operations use same patterns
- **Testing**: Pattern library tested, your usage auto-tested
- **Documentation**: YAML is self-documenting

### Maintenance
- **Pattern updates**: Improve pattern, all usages benefit
- **Team onboarding**: Learn patterns, not PL/pgSQL
- **Code reviews**: Focus on business logic, not SQL boilerplate

## 📈 ROI Timeline

| Timeframe | Benefit | Impact |
|-----------|---------|--------|
| **Week 1** | CRUD migration complete | 50% less manual SQL |
| **Week 2** | Business logic migrated | 80% less manual SQL |
| **Month 1** | New features faster | 10x development speed |
| **Month 3** | Maintenance easier | 5x fewer bugs |
| **Month 6** | Team productivity | 3x more features delivered |

---

**Ready to start?** Let's schedule your migration kickoff call and begin the transformation from manual PL/pgSQL to declarative, maintainable SpecQL patterns!