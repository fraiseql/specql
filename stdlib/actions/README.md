# SpecQL Action Pattern Library

A comprehensive library of reusable business logic patterns for SpecQL entities, enabling declarative specification of complex operations that generate production-ready PostgreSQL functions.

## 🎯 Overview

The SpecQL Action Pattern Library transforms manual PL/pgSQL development into declarative YAML configuration. Instead of writing 200+ lines of SQL for complex workflows, developers can express business logic in 20 lines of YAML that automatically generates tested, optimized PostgreSQL functions.

### Key Benefits

- **80% Code Reduction**: From 200 lines PL/pgSQL to 20 lines YAML
- **Production Ready**: Auto-generated, tested, and optimized SQL
- **Consistent Architecture**: Enforced patterns across all entities
- **Rapid Development**: Copy proven patterns, customize for needs
- **Maintainable**: Self-documenting YAML with clear business intent

## 📚 Available Patterns

### CRUD Patterns

#### `crud/create`
Enhanced entity creation with duplicate detection, identifier recalculation, and projection sync.

```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
        error_message: "Contract already exists for this customer"
```

**Features**:
- Automatic duplicate detection
- Identifier sequence generation
- Projection refresh
- Consistent error handling

#### `crud/update`
Partial updates with field tracking, identifier recalculation, and projection sync.

```yaml
actions:
  - name: update_contract
    pattern: crud/update
    config:
      partial_updates: true
      track_updated_fields: true
```

**Features**:
- CASE expression-based partial updates
- Field change auditing
- Identifier recalculation
- Projection refresh

#### `crud/delete`
Dependency-aware deletion with hard delete support.

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
          error_message: "Cannot delete contract with items"
```

**Features**:
- Automatic dependency checking
- Hard vs soft delete support
- Consistent error messages

### State Machine Patterns

#### `state_machine/transition`
Simple state transitions with validation and side effects.

```yaml
actions:
  - name: submit_for_review
    pattern: state_machine/transition
    config:
      from_states: [draft]
      to_state: pending_review
      validation_checks:
        - condition: "input_data.total_value > 0"
          error: "Contract value must be positive"
      side_effects:
        - entity: ContractEvent
          insert:
            contract_id: v_contract_id
            event_type: submitted_for_review
      refresh_projection: contract_projection
```

**Features**:
- Declarative state validation
- Automatic side effects
- Audit trail generation
- Projection refresh

#### `state_machine/guarded_transition`
Complex transitions with guard conditions for business rules.

```yaml
actions:
  - name: approve_contract
    pattern: state_machine/guarded_transition
    config:
      from_states: [draft, pending_review]
      to_state: approved
      guards:
        - name: budget_available
          condition: "input_data.total_value <= (SELECT budget FROM departments WHERE id = auth_user_department_id)"
          error: "Contract exceeds department budget"
        - name: manager_approval
          condition: "EXISTS (SELECT 1 FROM approvals WHERE contract_id = v_contract_id AND approver_role = 'manager')"
          error: "Manager approval required"
      side_effects:
        - entity: Department
          updates:
            used_budget: used_budget + input_data.total_value
          where: "id = auth_user_department_id"
      input_fields:
        - name: approved_by
          type: uuid
        - name: approval_date
          type: date
```

**Features**:
- Complex guard conditions
- Multi-entity side effects
- Input field validation
- Business rule enforcement

### Validation Patterns

#### `validation/validation_chain`
Chain multiple validation rules with configurable error handling.

```yaml
actions:
  - name: validate_contract_comprehensive
    pattern: validation/validation_chain
    config:
      validations:
        - name: customer_exists
          field: customer_org
          condition: "EXISTS (SELECT 1 FROM organizations WHERE id = input_data.customer_org AND status = 'active')"
          message: "Customer organization must exist and be active"
        - name: amount_positive
          field: total_value
          condition: "input_data.total_value > 0"
          message: "Contract total value must be positive"
      stop_on_first_failure: false
      collect_all_errors: true
```

**Features**:
- Multiple validation rules
- Configurable error handling
- Field-specific validation
- All errors collection

### Batch Operation Patterns

#### `batch/bulk_operation`
Process multiple records with transaction handling and error recovery.

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

**Features**:
- Transaction-wrapped batch processing
- Configurable error handling
- Progress tracking
- Summary reporting

## 🏗️ Architecture

### Pattern Structure

Each pattern consists of:

1. **YAML Configuration Schema** - Parameter definitions and validation
2. **Jinja2 Template** - SQL generation logic
3. **Integration Tests** - Validation of generated SQL

### Template Variables

Patterns have access to:

- `entity` - Entity definition (name, schema, fields, etc.)
- `config` - Pattern-specific configuration
- All config values as top-level variables

### Generated SQL Structure

All patterns generate functions following the SpecQL architecture:

```sql
CREATE OR REPLACE FUNCTION app.action_name(user_id uuid, input_data jsonb)
RETURNS mutation_result AS $$
DECLARE
  -- Variable declarations
  v_entity_id uuid;
  -- Pattern-generated logic
BEGIN
  -- Pre-validation
  -- Core business logic
  -- Side effects
  -- Response generation
  RETURN success_response();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 🚀 Getting Started

### 1. Choose a Pattern

Identify the business logic pattern that matches your use case:

- **Single entity CRUD** → `crud/*` patterns
- **State transitions** → `state_machine/*` patterns
- **Complex validation** → `validation/validation_chain`
- **Bulk operations** → `batch/bulk_operation`

### 2. Configure the Pattern

Copy the example configuration and customize for your entity:

```yaml
actions:
  - name: my_action
    pattern: crud/create  # Choose pattern
    config:
      # Pattern-specific configuration
      duplicate_check:
        fields: [unique_field]
```

### 3. Generate and Test

```bash
# Generate SQL
specql generate --entity my_entity

# Test the generated function
specql test --entity my_entity --action my_action
```

### 4. Deploy

The generated SQL is production-ready with:
- Proper error handling
- Transaction management
- Security considerations
- Performance optimizations

## 📖 Pattern Reference

### Configuration Parameters

#### Common Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `refresh_projection` | string | Projection to refresh after operation | null |

#### CRUD Parameters

| Pattern | Parameter | Type | Description |
|---------|-----------|------|-------------|
| `crud/create` | `duplicate_check` | object | Duplicate detection configuration |
| `crud/update` | `partial_updates` | boolean | Enable CASE-based partial updates |
| `crud/update` | `track_updated_fields` | boolean | Track which fields changed |
| `crud/delete` | `supports_hard_delete` | boolean | Allow permanent deletion |
| `crud/delete` | `check_dependencies` | array | Dependency validation rules |

#### State Machine Parameters

| Pattern | Parameter | Type | Description |
|---------|-----------|------|-------------|
| `state_machine/*` | `from_states` | array | Valid source states |
| `state_machine/*` | `to_state` | string | Target state |
| `state_machine/guarded_transition` | `guards` | array | Business rule conditions |
| `state_machine/*` | `validation_checks` | array | Pre-transition validations |
| `state_machine/*` | `side_effects` | array | Operations to perform on success |
| `state_machine/*` | `input_fields` | array | Additional fields to set |

#### Validation Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `validations` | array | List of validation rules | [] |
| `stop_on_first_failure` | boolean | Stop on first validation error | true |
| `collect_all_errors` | boolean | Return all validation errors | false |

#### Batch Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `batch_input` | string | JSONB field containing items | required |
| `operation` | object | Operation to perform per item | required |
| `error_handling` | enum | How to handle errors | continue_on_error |
| `batch_size` | integer | Maximum items to process | 100 |
| `return_summary` | object | Summary fields to return | {} |

## 🧪 Testing

### Pattern Integration Tests

Each pattern includes comprehensive integration tests:

```bash
# Run all pattern tests
pytest tests/integration/patterns/

# Test specific pattern
pytest tests/integration/patterns/ -k "test_crud_create"
```

### Generated SQL Testing

Test that patterns generate correct SQL:

```bash
# Compare generated SQL with reference
specql generate --entity contract --compare reference.sql
```

## 🔄 Migration from Manual SQL

### Using the Migration Analyzer

Analyze existing entities for pattern opportunities:

```bash
# Analyze single entity
python -m src.patterns.migration_cli entities/my_entity.yaml

# Analyze directory
python -m src.patterns.migration_cli entities/ --report migration_report.md

# High-confidence suggestions only
python -m src.patterns.migration_cli entities/ --min-confidence 0.8
```

### Migration Workflow

1. **Analyze** existing manual actions
2. **Identify** applicable patterns
3. **Configure** pattern parameters
4. **Generate** new SQL
5. **Test** equivalence with old implementation
6. **Deploy** with rollback plan

### Example Migration

**Before** (200 lines PL/pgSQL):
```sql
CREATE OR REPLACE FUNCTION app.create_contract(user_id uuid, input jsonb)
RETURNS mutation_result AS $$
-- Manual duplicate check, validation, insert, projection refresh...
$$;
```

**After** (20 lines YAML):
```yaml
actions:
  - name: create_contract
    pattern: crud/create
    config:
      duplicate_check:
        fields: [customer_org, customer_contract_id]
```

## 📊 Performance Characteristics

### SQL Efficiency

- **CASE expressions** for partial updates (avoids multiple queries)
- **JSONB operations** for flexible input handling
- **Bulk operations** with single transaction
- **Indexed lookups** for validation and constraints

### Generation Performance

- **Sub-second generation** for typical entities
- **Linear scaling** with entity complexity
- **Cached templates** for repeated generation

### Runtime Performance

- **Equivalent to hand-written SQL** (same execution plans)
- **Optimized transactions** with proper locking
- **Connection pooling friendly** (standard PL/pgSQL)

## 🤝 Contributing

### Adding New Patterns

1. **Define** the pattern YAML in `stdlib/actions/`
2. **Implement** the Jinja2 template
3. **Add** integration tests
4. **Update** documentation

### Pattern Guidelines

- **Declarative**: Business intent over implementation details
- **Composable**: Work well with other patterns
- **Testable**: Comprehensive integration tests
- **Documented**: Clear examples and parameter reference

## 📚 Related Documentation

- [Migration Guide](../../docs/migration/printoptim_to_specql.md) - Converting manual SQL to patterns
- [Entity Definition](../../docs/guides/entity_definition.md) - Complete entity specification
- [Action Patterns](../../docs/patterns/) - Detailed pattern documentation
- [Testing](../../docs/testing/) - Testing generated functions

---

**Transform your SpecQL development from manual SQL implementation to declarative pattern composition!** 🎯
