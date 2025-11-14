# SpecQL Action Pattern Library

The SpecQL Action Pattern Library provides declarative templates for common business logic patterns, enabling you to express complex workflows in simple YAML instead of writing manual PL/pgSQL.

## 🎯 What Are Action Patterns?

Action patterns are reusable templates that encapsulate common business logic patterns:

- **State Machine Transitions**: Declarative state changes with validation and side effects
- **Multi-Entity Operations**: Coordinated updates across multiple entities
- **Batch Operations**: Bulk processing with error handling and progress tracking
- **CRUD Enhancements**: Advanced create/read/update/delete with constraints and projections

## 📚 Available Patterns

### State Machine Pattern (`state_machine/transition`)

Manages entity lifecycle transitions with validation and side effects.

```yaml
actions:
  - name: decommission_machine
    pattern: state_machine/transition
    config:
      from_states: [active, maintenance]
      to_state: decommissioned
      validation_checks:
        - condition: "NOT EXISTS (SELECT 1 FROM allocations WHERE machine_id = $entity_id)"
          error: "Cannot decommission with active allocations"
      side_effects:
        - entity: MachineItem
          set: {status: archived}
          where: "machine_id = $entity_id"
```

**Generated SQL**: Automatic state validation, transition logic, and side effect execution.

### Multi-Entity Pattern (`multi_entity/coordinated_update`)

Coordinates changes across multiple entities in a single transaction.

```yaml
actions:
  - name: allocate_to_stock
    pattern: multi_entity/coordinated_update
    config:
      operations:
        - action: get_or_create
          entity: Location
          where: {code: 'STOCK'}
          create_if_missing: {code: STOCK, name: 'Stock'}
        - action: insert
          entity: Allocation
          values: {machine_id: $input.machine_id, location_id: $location_id}
        - action: update
          entity: Machine
          set: {status: in_stock}
          where: {id: $input.machine_id}
```

**Generated SQL**: Transaction-wrapped operations with proper error handling.

### Batch Operation Pattern (`batch/bulk_operation`)

Processes multiple records with configurable error handling.

```yaml
actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      batch_input: price_updates
      operation:
        action: update
        entity: ContractItem
        set: {unit_price: $item.price}
        where: {id: $item.id}
      error_handling: continue_on_error
      return_summary:
        processed: v_processed_count
        failed: v_failed_count
```

**Generated SQL**: Loop-based processing with progress tracking and error collection.

## 🚀 Getting Started

### 1. Choose Your Pattern

Identify which pattern matches your business logic:

| Use Case | Pattern | Example |
|----------|---------|---------|
| Status changes with rules | `state_machine/transition` | Order approval workflow |
| Cross-entity updates | `multi_entity/coordinated_update` | User registration with profile |
| Bulk data operations | `batch/bulk_operation` | Price updates, status changes |
| Advanced CRUD | Enhanced entity config | Duplicate detection, projections |

### 2. Configure the Pattern

Each pattern has required and optional parameters. Start with the minimal config:

```yaml
actions:
  - name: my_action
    pattern: state_machine/transition
    config:
      from_states: [draft]
      to_state: active
```

### 3. Add Business Logic

Enhance with validation, side effects, and error handling:

```yaml
actions:
  - name: my_action
    pattern: state_machine/transition
    config:
      from_states: [draft]
      to_state: active
      validation_checks:
        - condition: "field IS NOT NULL"
          error: "Required field missing"
      side_effects:
        - entity: AuditLog
          set: {action: 'activated', timestamp: NOW()}
```

### 4. Test and Iterate

Patterns generate complete SQL functions. Test them like any other SpecQL action:

```bash
# Generate and test
specql generate
specql test
```

## 📖 Pattern Reference

### State Machine Pattern

**Parameters:**
- `from_states` (required): Array of valid source states
- `to_state` (required): Target state
- `validation_checks`: Array of pre-transition validations
- `side_effects`: Array of post-transition updates
- `input_fields`: Additional fields to set during transition
- `refresh_projection`: Projection to refresh after transition

**Validation Checks:**
```yaml
validation_checks:
  - name: check_name
    condition: "SQL expression returning boolean"
    error: "Error message if condition fails"
```

**Side Effects:**
```yaml
side_effects:
  - entity: EntityName
    set: {field: value, ...}
    where: "WHERE clause"
```

### Multi-Entity Pattern

**Parameters:**
- `primary_entity` (required): Main entity being operated on
- `operations` (required): Array of operations to perform
- `transaction_scope`: Transaction isolation level
- `refresh_projections`: Projections to refresh

**Operations:**
```yaml
operations:
  - action: get_or_create|insert|update|delete
    entity: EntityName
    # ... action-specific config
```

### Batch Operation Pattern

**Parameters:**
- `batch_input` (required): Field containing array of items
- `operation` (required): Operation to perform on each item
- `error_handling`: `continue_on_error` or `stop_on_error`
- `batch_size`: Maximum items to process
- `return_summary`: Summary fields to return

**Operations:**
```yaml
operation:
  action: update|insert|delete
  entity: EntityName
  set: {field: $item.value}
  where: {id: $item.id}
```

## 🔧 Advanced Usage

### Custom Validation Expressions

Use SQL expressions for complex validation:

```yaml
validation_checks:
  - condition: |
      EXISTS (
        SELECT 1 FROM related_table
        WHERE related_id = v_entity_id
          AND status = 'active'
      )
    error: "Related records must be active"
```

### Dynamic Side Effects

Reference input data and entity variables:

```yaml
side_effects:
  - entity: AuditLog
    set:
      entity_id: v_entity_id
      action: $input.action
      user_id: $auth_user_id
      timestamp: NOW()
```

### Error Handling Strategies

Choose appropriate error handling for your use case:

```yaml
# Stop on first error
error_handling: stop_on_error

# Continue and collect errors
error_handling: continue_on_error
return_summary:
  failed_items: v_failed_items
```

## 🎯 Best Practices

### 1. Start Simple
Begin with basic pattern configuration and add complexity gradually.

### 2. Use Meaningful Names
Name your actions clearly: `activate_contract`, not `change_status`.

### 3. Validate Early
Use validation checks to catch business rule violations before state changes.

### 4. Handle Errors Gracefully
Design for partial failures in batch operations and multi-entity updates.

### 5. Refresh Projections
Keep GraphQL projections fresh by specifying `refresh_projection` in state changes.

### 6. Test Thoroughly
Patterns generate complex SQL - test edge cases and error conditions.

## 🚨 Troubleshooting

### Pattern Not Found
- Check pattern name spelling
- Ensure pattern exists in `stdlib/actions/`
- Verify file permissions

### Validation Errors
- Check SQL syntax in conditions
- Verify field references exist
- Use `$entity_id` for current entity ID

### Template Expansion Issues
- Validate YAML syntax
- Check required parameters are provided
- Review Jinja2 template syntax

### SQL Generation Problems
- Test generated functions individually
- Check database permissions
- Verify entity relationships

## 📚 Examples

See `entities/examples/` for complete working examples:

- `machine_with_patterns.yaml` - State machine transitions
- `allocation_with_patterns.yaml` - Multi-entity coordination
- `contract_item_with_patterns.yaml` - Batch operations

## 🔗 Related Documentation

- [Migration Guide](migration/printoptim_to_specql.md) - Migrating from manual SQL
- [API Reference](api/pattern_library_api.md) - Complete parameter reference
- [Quick Start](getting_started.md) - Step-by-step tutorial