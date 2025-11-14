# Pattern Selection Best Practices

Guidelines for choosing the right SpecQL patterns for your business logic, with decision trees, examples, and anti-patterns to avoid.

## Overview

SpecQL provides 27+ reusable patterns, but choosing the right one can be overwhelming. This guide helps you select patterns based on your use case, data relationships, and business requirements.

## Quick Pattern Selection Guide

### For Single Entity Operations

**Use Case: Basic CRUD with business rules**
```yaml
# ✅ GOOD: Use CRUD patterns
actions:
  - name: create_user
    pattern: crud/create
    config:
      duplicate_check:
        fields: [email]

  - name: update_user
    pattern: crud/update
    config:
      partial_updates: true

  - name: delete_user
    pattern: crud/delete
```

**Use Case: Status-based workflows**
```yaml
# ✅ GOOD: Use state machines
actions:
  - name: activate_user
    pattern: state_machine/transition
    config:
      from_states: [pending, inactive]
      to_state: active
```

### For Multi-Entity Operations

**Use Case: Related data in one transaction**
```yaml
# ✅ GOOD: Use coordinated updates
actions:
  - name: create_order_with_items
    pattern: multi_entity/coordinated_update
    config:
      entities:
        - entity: Order
          operation: insert
        - entity: OrderItem
          operation: insert
```

**Use Case: Complex distributed workflows**
```yaml
# ✅ GOOD: Use saga orchestrator
actions:
  - name: process_order_fulfillment
    pattern: multi_entity/saga_orchestrator
    config:
      saga_steps:
        - name: payment
          action: call_external
          compensation: refund
        - name: inventory
          action: update
          compensation: restock
```

### For Data Validation

**Use Case: Multiple validation rules**
```yaml
# ✅ GOOD: Use validation chain
actions:
  - name: validate_contract
    pattern: validation/validation_chain
    config:
      validations:
        - condition: "amount > 0"
          error: "invalid_amount"
        - condition: "customer_id IS NOT NULL"
          error: "customer_required"
```

### For Bulk Operations

**Use Case: Process multiple records**
```yaml
# ✅ GOOD: Use batch operations
actions:
  - name: bulk_update_prices
    pattern: batch/bulk_operation
    config:
      operation:
        action: update
        entity: Product
        set: {price: $item.price}
```

## Decision Tree for Pattern Selection

```
Does your operation involve multiple entities?
├── YES → Multi-entity operation
│   ├── Is it a simple transaction? → multi_entity/coordinated_update
│   ├── Does it need compensation? → multi_entity/saga_orchestrator
│   └── Is it event-driven? → multi_entity/event_driven_orchestrator
│
└── NO → Single entity operation
    ├── Is it basic CRUD?
    │   ├── Create → crud/create
    │   ├── Read → (automatic)
    │   ├── Update → crud/update
    │   └── Delete → crud/delete
    │
    ├── Is it status-based workflow?
    │   ├── Simple transition → state_machine/transition
    │   └── Complex guards → state_machine/guarded_transition
    │
    ├── Is it data validation?
    │   └── Multiple rules → validation/validation_chain
    │
    └── Is it bulk processing?
        └── Multiple records → batch/bulk_operation
```

## Pattern Comparison Matrix

| Pattern | Use Case | Complexity | Performance | Error Handling | Best For |
|---------|----------|------------|-------------|----------------|----------|
| `crud/create` | Entity creation | Low | High | Basic | All create operations |
| `crud/update` | Entity updates | Low | High | Basic | All update operations |
| `crud/delete` | Entity deletion | Low | High | Dependencies | All delete operations |
| `state_machine/transition` | Status changes | Medium | High | State validation | Simple workflows |
| `state_machine/guarded_transition` | Complex workflows | High | Medium | Business rules | Approval processes |
| `validation/validation_chain` | Data validation | Medium | High | Multiple errors | Form validation |
| `batch/bulk_operation` | Bulk processing | Medium | Variable | Partial failures | Data imports |
| `multi_entity/coordinated_update` | Related updates | Medium | High | Transaction | Order processing |
| `multi_entity/saga_orchestrator` | Distributed tx | High | Medium | Compensation | E-commerce |
| `composite/workflow_orchestrator` | Complex workflows | High | Medium | Orchestration | Business processes |

## Common Pattern Selection Mistakes

### ❌ Anti-Pattern: Overusing State Machines

**Wrong:**
```yaml
# Don't use state machines for simple flags
actions:
  - name: mark_featured
    pattern: state_machine/transition
    config:
      from_states: [false]
      to_state: true
```

**Right:**
```yaml
# Use simple updates for boolean flags
actions:
  - name: mark_featured
    pattern: crud/update
    config:
      partial_updates: true
      allowed_fields: [is_featured]
```

### ❌ Anti-Pattern: Complex Single Actions

**Wrong:**
```yaml
# Don't cram everything into one action
actions:
  - name: process_order
    pattern: composite/workflow_orchestrator
    config:
      workflow:
        - step: validate
        - step: charge
        - step: ship
        - step: email
        - step: audit
```

**Right:**
```yaml
# Break into focused actions
actions:
  - name: validate_order
    pattern: validation/validation_chain

  - name: charge_payment
    pattern: state_machine/transition

  - name: ship_order
    pattern: state_machine/guarded_transition

  - name: send_confirmation
    pattern: crud/create  # Create notification record
```

### ❌ Anti-Pattern: Ignoring Performance

**Wrong:**
```yaml
# Don't use batch operations for single records
actions:
  - name: update_single_product
    pattern: batch/bulk_operation
    config:
      operation: {...}
```

**Right:**
```yaml
# Use appropriate patterns for data volume
actions:
  - name: update_product
    pattern: crud/update  # For single records

  - name: bulk_update_products
    pattern: batch/bulk_operation  # For multiple records
```

## Pattern Implementation Guidelines

### CRUD Patterns

**When to Use:**
- Basic create, read, update, delete operations
- Simple business rules (duplicates, required fields)
- Standard audit trails

**Configuration Tips:**
```yaml
actions:
  - name: create_entity
    pattern: crud/create
    config:
      # Always check for duplicates
      duplicate_check:
        fields: [unique_field]
        error_message: "Custom message"
        return_conflict_object: true

  - name: update_entity
    pattern: crud/update
    config:
      # Enable partial updates
      partial_updates: true
      # Track what changed
      track_updated_fields: true
      # Restrict updatable fields
      allowed_fields: [safe_field1, safe_field2]

  - name: delete_entity
    pattern: crud/delete
    config:
      # Choose delete strategy
      supports_hard_delete: false  # Prefer soft deletes
      # Check for dependencies
      check_dependencies:
        - entity: RelatedEntity
          field: foreign_key
          error_message: "Cannot delete with dependencies"
```

### State Machine Patterns

**When to Use:**
- Entities with clear status lifecycles
- Business processes with defined states
- Operations that depend on current state

**Configuration Tips:**
```yaml
# Simple transitions
actions:
  - name: approve_request
    pattern: state_machine/transition
    config:
      from_states: [pending, draft]
      to_state: approved
      # Add validation
      validation_checks:
        - condition: "amount <= approval_limit"
          error: "amount_exceeds_limit"
      # Add side effects
      side_effects:
        - entity: AuditLog
          insert:
            action: approved
            old_status: pending
            new_status: approved

# Complex transitions with guards
actions:
  - name: approve_large_request
    pattern: state_machine/guarded_transition
    config:
      from_states: [pending]
      to_state: approved
      # Business rule guards
      guards:
        - name: budget_check
          condition: "amount <= user_budget()"
          error: "insufficient_budget"
        - name: manager_approval
          condition: "has_manager_approval(id)"
          error: "manager_approval_required"
```

### Validation Patterns

**When to Use:**
- Multiple validation rules
- Complex business logic validation
- Need to collect all errors

**Configuration Tips:**
```yaml
actions:
  - name: validate_comprehensive
    pattern: validation/validation_chain
    config:
      # Define validation rules
      validations:
        - name: required_fields
          field: name
          condition: "input_data.name IS NOT NULL"
          message: "Name is required"
        - name: email_format
          field: email
          condition: "input_data.email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'"
          message: "Invalid email format"
        - name: unique_email
          condition: "NOT EXISTS (SELECT 1 FROM users WHERE email = input_data.email)"
          message: "Email already exists"
      # Control error behavior
      collect_all_errors: true
      stop_on_first_failure: false
```

### Batch Operation Patterns

**When to Use:**
- Processing multiple records
- Bulk imports/updates
- Performance-critical operations

**Configuration Tips:**
```yaml
actions:
  - name: bulk_process
    pattern: batch/bulk_operation
    config:
      # Define input format
      batch_input: items_array
      # Configure operation
      operation:
        action: update
        entity: Product
        set:
          price: "$item.new_price"
          updated_at: "now()"
        where: "id = $item.id"
      # Error handling
      error_handling: continue_on_error
      batch_size: 100
      # Return summary
      return_summary:
        processed_count: v_processed
        failed_count: v_failed
```

### Multi-Entity Patterns

**When to Use:**
- Operations span multiple tables
- Need transaction consistency
- Complex business processes

**Configuration Tips:**
```yaml
# Coordinated updates
actions:
  - name: create_order_complete
    pattern: multi_entity/coordinated_update
    config:
      entities:
        - entity: Order
          operation: insert
          fields: [customer_id, total]
        - entity: OrderItem
          operation: insert
          fields: [order_id, product_id, quantity]
        - entity: Product
          operation: update
          fields: [stock_quantity: "stock_quantity - OrderItem.quantity"]
          condition: "id = OrderItem.product_id"

# Saga orchestrator
actions:
  - name: process_payment_flow
    pattern: multi_entity/saga_orchestrator
    config:
      saga_steps:
        - name: reserve_funds
          action: call_external
          service: payment
          compensation:
            action: release_funds
        - name: update_inventory
          action: update
          entity: Product
          compensation:
            action: restock_inventory
```

## Performance Considerations

### Pattern Performance Characteristics

| Pattern Category | Performance | Scalability | Best Use Case |
|------------------|-------------|-------------|---------------|
| CRUD | Excellent | High | 90% of operations |
| State Machines | Good | High | Status workflows |
| Validation | Excellent | High | Input validation |
| Batch Operations | Variable | High | Bulk processing |
| Multi-Entity | Good | Medium | Related operations |
| Saga | Fair | Medium | Distributed systems |

### Optimization Strategies

**For High-Volume CRUD:**
```yaml
actions:
  - name: create_bulk_users
    pattern: batch/bulk_operation
    config:
      operation:
        action: insert
        entity: User
      error_handling: continue_on_error
```

**For Complex Validation:**
```yaml
# Cache expensive validation checks
actions:
  - name: validate_with_cache
    pattern: validation/validation_chain
    config:
      validations:
        - condition: "is_email_deliverable(input_data.email)"  # Cache this
          message: "Email not deliverable"
```

**For State Machines:**
```yaml
# Pre-validate common transitions
actions:
  - name: quick_approve
    pattern: state_machine/transition
    config:
      from_states: [pending]
      to_state: approved
      validation_checks:
        - condition: "amount <= 1000"  # Fast check
```

## Migration from Manual Code

### Identifying Pattern Opportunities

**Manual SQL → Pattern Mapping:**

| Manual Pattern | SpecQL Pattern | Example |
|----------------|----------------|---------|
| `INSERT ... SELECT` | `crud/create` | Basic entity creation |
| `UPDATE ... WHERE` | `crud/update` | Entity updates |
| `DELETE ... WHERE` | `crud/delete` | Entity deletion |
| `IF status = 'X' THEN UPDATE` | `state_machine/transition` | Status changes |
| `IF condition THEN action` | `state_machine/guarded_transition` | Business rules |
| Multiple `IF` validations | `validation/validation_chain` | Input validation |
| `FOR item IN items LOOP` | `batch/bulk_operation` | Bulk processing |
| Multi-table transactions | `multi_entity/coordinated_update` | Related updates |
| Complex error handling | `multi_entity/saga_orchestrator` | Distributed tx |

### Migration Steps

1. **Analyze** existing stored procedures
2. **Identify** repetitive patterns
3. **Map** to SpecQL patterns
4. **Configure** pattern parameters
5. **Test** equivalence
6. **Deploy** incrementally

### Example Migration

**Before (200 lines of PL/pgSQL):**
```sql
CREATE OR REPLACE FUNCTION create_contract(user_id uuid, input jsonb)
RETURNS mutation_result AS $$
-- Manual duplicate check, validation, insert, audit...
$$ LANGUAGE plpgsql;
```

**After (20 lines of YAML):**
```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, contract_id]
```

## Common Questions

### Q: When should I use state machines vs simple updates?

**A:** Use state machines when:
- Status has business meaning (approved, rejected, shipped)
- Invalid transitions should be prevented
- You need audit trails of status changes
- Status affects available operations

Use simple updates for:
- Boolean flags (active/inactive)
- Numeric values (quantity, score)
- Free-form text (notes, descriptions)

### Q: Should I use batch operations for single records?

**A:** No. Batch operations have overhead for:
- JSON processing
- Loop iteration
- Error aggregation

Use CRUD patterns for single records, batch patterns only for multiple records.

### Q: When to use saga vs coordinated updates?

**A:** Use coordinated updates for:
- Simple multi-table transactions
- All operations in one database
- Fast, atomic operations

Use sagas for:
- Distributed systems (multiple services)
- Long-running operations
- Need for compensation logic
- External service calls

### Q: How do I handle complex business logic?

**A:** Break it down:
1. **Validation** → `validation/validation_chain`
2. **State changes** → `state_machine/*`
3. **Side effects** → Include in state machine side_effects
4. **Complex workflows** → `composite/workflow_orchestrator`

Don't try to fit everything into one pattern.

---

**See Also:**
- [Entity Design Best Practices](entity-design.md)
- [Testing Strategy](testing-strategy.md)
- [Performance Best Practices](performance.md)
- [Pattern Library API](../reference/pattern-library-api.md)