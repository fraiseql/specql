# SpecQL Pattern Examples

This directory contains complete working examples demonstrating SpecQL action patterns in real business scenarios.

## 📚 Available Examples

### Core Pattern Demonstrations

| Example | Patterns Used | Business Domain | Description |
|---------|---------------|-----------------|-------------|
| `machine_with_patterns.yaml` | State Machine | Manufacturing | Equipment lifecycle management |
| `allocation_with_patterns.yaml` | Multi-Entity | Manufacturing | Machine allocation workflows |
| `contract_item_with_patterns.yaml` | Batch Operations | Commerce | Bulk contract item management |

### Business Domain Examples

| Example | Patterns Used | Business Domain | Description |
|---------|---------------|-----------------|-------------|
| `user_registration.yaml` | Multi-Entity, State Machine | User Management | Complete user onboarding flow |
| `order_workflow.yaml` | State Machine, Multi-Entity, Batch | E-commerce | Order lifecycle from creation to delivery |
| `inventory_management.yaml` | Batch Operations, Multi-Entity, State Machine | Inventory | Product inventory and stock management |

## 🚀 Getting Started

### 1. Choose an Example

Pick an example that matches your business domain:

```bash
# Copy an example to your entities directory
cp entities/examples/machine_with_patterns.yaml entities/my_machine.yaml

# Edit to match your requirements
vim entities/my_machine.yaml
```

### 2. Generate SQL

```bash
# Generate SQL for your entity
specql generate --entity my_machine

# Check the generated functions
cat generated/my_machine.sql
```

### 3. Test the Patterns

```bash
# Run tests
specql test --entity my_machine

# Test specific functions
psql -d your_database -f generated/my_machine.sql
```

## 📖 Example Walkthroughs

### Machine Lifecycle Management

**File**: `machine_with_patterns.yaml`

This example shows a complete equipment management system:

1. **CRUD Operations**: Create, update, delete machines
2. **State Machine**: Transition between `active` → `maintenance` → `decommissioned`
3. **Business Rules**: Validation checks prevent invalid transitions
4. **Side Effects**: Automatic cleanup when decommissioning

**Key Patterns Used**:
- `state_machine/transition` for lifecycle management
- Enhanced CRUD with projections
- Validation rules and side effects

### User Registration Flow

**File**: `user_registration.yaml`

Complete user onboarding with multi-entity coordination:

1. **Multi-Entity Creation**: User + Profile + Preferences in one transaction
2. **State Machine**: Email verification workflow
3. **Business Validation**: Duplicate email prevention

**Key Patterns Used**:
- `multi_entity/coordinated_update` for registration
- `state_machine/transition` for verification
- Constraint-based duplicate detection

### E-commerce Order Processing

**File**: `order_workflow.yaml`

Complex order lifecycle with multiple state transitions:

1. **Order Creation**: Multi-entity order + items + payment
2. **Status Transitions**: pending → confirmed → processing → shipped → delivered
3. **Business Rules**: Payment required before confirmation
4. **Batch Operations**: Bulk status updates

**Key Patterns Used**:
- `multi_entity/coordinated_update` for order creation
- `state_machine/transition` for status changes
- `batch/bulk_operation` for bulk updates

### Inventory Management

**File**: `inventory_management.yaml`

Product inventory with bulk operations:

1. **Batch Updates**: Price changes, inventory adjustments, status updates
2. **Multi-Entity**: Purchase order receiving with inventory updates
3. **State Machine**: Product status management (active → out_of_stock → discontinued)

**Key Patterns Used**:
- `batch/bulk_operation` for bulk inventory operations
- `multi_entity/coordinated_update` for purchase receiving
- `state_machine/transition` for product lifecycle

## 🛠️ Customization Guide

### Adapting Examples to Your Domain

1. **Change Entity Names**:
   ```yaml
   entity: YourEntity  # Change this
   ```

2. **Update Field Names**:
   ```yaml
   fields:
     your_field: text!  # Change field names
   ```

3. **Modify Business Rules**:
   ```yaml
   validation_checks:
     - condition: "your_business_rule"  # Update conditions
   ```

4. **Customize Side Effects**:
   ```yaml
   side_effects:
     - entity: YourRelatedEntity  # Change related entities
   ```

### Adding New Patterns

1. **Copy an existing pattern**:
   ```bash
   cp machine_with_patterns.yaml my_new_entity.yaml
   ```

2. **Replace the business logic**:
   ```yaml
   # Change actions to match your workflow
   actions:
     - name: your_business_action
       pattern: state_machine/transition
       config:
         # Your configuration
   ```

## 🧪 Testing Examples

### Automated Testing

```bash
# Test all examples
for example in entities/examples/*.yaml; do
    entity_name=$(basename "$example" .yaml)
    echo "Testing $entity_name..."
    specql generate --entity "$entity_name"
    specql test --entity "$entity_name"
done
```

### Manual Testing

```sql
-- Test machine decommissioning
SELECT * FROM tenant.decommission_machine(
    'tenant-uuid'::UUID,
    'user-uuid'::UUID,
    '{
        "id": "machine-uuid",
        "decommission_date": "2024-01-01",
        "decommission_reason": "End of life"
    }'::JSONB
);

-- Test bulk price updates
SELECT * FROM tenant.bulk_update_prices(
    'tenant-uuid'::UUID,
    'user-uuid'::UUID,
    '{
        "price_updates": [
            {"id": "product-1", "new_price": 29.99},
            {"id": "product-2", "new_price": 39.99}
        ]
    }'::JSONB
);
```

## 📊 Performance Considerations

### Pattern Performance Characteristics

| Pattern | Performance | Use Case |
|---------|-------------|----------|
| State Machine | Fast | Frequent status changes |
| Multi-Entity | Medium | Complex transactions |
| Batch Operations | Variable | Bulk data operations |

### Optimization Tips

1. **Use appropriate batch sizes** (50-100 items for batch operations)
2. **Index foreign keys** used in pattern operations
3. **Monitor projection refresh performance**
4. **Consider partial updates** for large entities

## 🚨 Troubleshooting

### Common Issues

**"Pattern not found"**
- Check pattern name spelling
- Ensure `pattern:` key is present

**"Field not found in expression"**
- SQL expressions can't reference undefined fields
- Use `$variable` syntax for input variables

**"Template expansion failed"**
- Check YAML indentation
- Validate Jinja2 template syntax

**"Constraint violation"**
- Check unique constraints
- Verify foreign key relationships

### Getting Help

1. **Check the generated SQL** for syntax errors
2. **Review pattern documentation** in `docs/patterns/`
3. **Test individual functions** before integration
4. **Use the API reference** for parameter details

## 📚 Related Documentation

- [Pattern Library Guide](../../docs/patterns/README.md) - Complete pattern reference
- [Migration Guide](../../docs/migration/printoptim_to_specql.md) - Migrating from manual SQL
- [API Reference](../../docs/api/pattern_library_api.md) - Detailed parameter specs
- [Quick Start](../../docs/patterns/getting_started.md) - Step-by-step tutorial

---

**Ready to build?** Start with the example that matches your business domain, customize it for your needs, and generate production-ready SQL with complex business logic!