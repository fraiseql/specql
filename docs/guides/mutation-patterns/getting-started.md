# Getting Started with Mutation Patterns

Learn the fundamentals of SpecQL mutation patterns - reusable templates for common business logic operations. This guide covers pattern concepts, basic usage, and best practices.

## 🎯 What You'll Learn

- Pattern concepts and benefits
- Basic pattern structure
- How to add patterns to entities
- Pattern validation and generation
- Common pattern usage patterns

## 📋 Prerequisites

- [Entity created](../getting-started/first-entity.md)
- Basic YAML knowledge
- Understanding of database concepts

## 💡 Pattern Concepts

### What Are Patterns?

**Mutation patterns** are declarative templates that implement common business operations:

```yaml
# Declarative specification
patterns:
  - name: state_machine
    states: [pending, approved, rejected]
    transitions:
      - from: pending
        to: approved
        trigger: approve
```

**Generates:**
- Database functions (`approve_request()`)
- Constraints and triggers
- Comprehensive tests
- Documentation

### Why Use Patterns?

| Benefit | Description | Example |
|---------|-------------|---------|
| **Productivity** | 10x faster than custom SQL | 5 YAML lines → 200 lines of SQL + tests |
| **Consistency** | Standardized implementations | Same approval workflow everywhere |
| **Reliability** | Battle-tested code | Proven patterns from production apps |
| **Maintainability** | Declarative specifications | Easy to modify and version |
| **Testing** | Automatic test generation | 100% coverage out of the box |

## 🏗️ Basic Pattern Structure

### Minimal Pattern

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  status: string
  total: decimal

patterns:
  - name: state_machine
    description: "Order processing workflow"
```

### Complete Pattern

```yaml
patterns:
  - name: state_machine
    description: "Order processing workflow"
    # Pattern-specific configuration
    initial_state: pending
    states: [pending, confirmed, shipped, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm_order
        guard: "total > 0"
        action: "send_confirmation_email"
```

## 🔧 Adding Patterns to Entities

### Step 1: Choose a Pattern

Select from 27+ available patterns based on your needs:

| Need | Pattern | Example |
|------|---------|---------|
| **Status changes** | `state_machine` | Order: pending → confirmed → shipped |
| **Data validation** | `validation` | Email format, age restrictions |
| **Cross-table ops** | `multi_entity` | Order + line items transaction |
| **Bulk operations** | `batch_operations` | Mass user updates |
| **Audit logging** | `audit_trail` | Track all changes |

### Step 2: Add to Entity

```yaml
# entities/user.yaml
name: user
fields:
  id: uuid
  email: string
  status: string  # Will be managed by pattern

patterns:
  - name: state_machine
    description: "User account lifecycle"
    initial_state: inactive
    states: [inactive, active, suspended]
    transitions:
      - from: inactive
        to: active
        trigger: activate_user
```

### Step 3: Validate Configuration

```bash
# Check for syntax errors
specql validate entities/user.yaml

# Expected output:
# ✅ entities/user.yaml: Valid
```

### Step 4: Generate Implementation

```bash
# Generate database schema and functions
specql generate schema entities/user.yaml

# Check generated files
ls -la db/schema/
# 40_functions/user_state_machine.sql
```

### Step 5: Apply to Database

```bash
# Apply the pattern functions
psql $DATABASE_URL -f db/schema/40_functions/user_state_machine.sql
```

## 🧪 Testing Patterns

### Generate Tests

```bash
# Generate comprehensive tests
specql generate tests entities/user.yaml

# Check generated test files
ls -la tests/
# pgtap/user_state_machine_test.sql
# pytest/test_user_state_machine.py
```

### Run Tests

```bash
# Run pgTAP tests (fast, database-only)
specql test run --type pgtap entities/user.yaml

# Run pytest tests (comprehensive, slower)
specql test run --type pytest entities/user.yaml
```

**Expected output:**
```
✅ All tests passed
Test coverage: 100%
```

## 💻 Using Generated Functions

### Direct SQL Calls

```sql
-- Activate a user
SELECT user_activate_user('user-uuid-123');

-- Check current state
SELECT status FROM user WHERE id = 'user-uuid-123';

-- Get available transitions
SELECT * FROM user_get_available_transitions('user-uuid-123');
```

### Application Code

```python
# Python example
def activate_user(user_id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_activate_user(%s)
            """, (user_id,))
            result = cursor.fetchone()
            return result[0]  # Success/failure

# Usage
success = activate_user('user-uuid-123')
```

```javascript
// Node.js example
async function activateUser(userId) {
  const result = await pool.query(
    'SELECT user_activate_user($1)',
    [userId]
  );
  return result.rows[0];
}

// Usage
const result = await activateUser('user-uuid-123');
```

## 🎯 Pattern Categories

### State Management Patterns

**State Machine** - Entity lifecycle management
```yaml
patterns:
  - name: state_machine
    states: [draft, published, archived]
    transitions:
      - from: draft
        to: published
        trigger: publish
```

**Workflow** - Complex multi-step processes
```yaml
patterns:
  - name: workflow
    steps:
      - name: review
        assignees: [manager]
      - name: approve
        assignees: [director]
```

### Data Integrity Patterns

**Validation** - Business rule enforcement
```yaml
patterns:
  - name: validation
    rules:
      - name: email_required
        field: email
        rule: "email IS NOT NULL"
      - name: age_positive
        field: age
        rule: "age > 0"
```

**Audit Trail** - Change tracking
```yaml
patterns:
  - name: audit_trail
    track_fields: [status, email]
    track_changes: true
```

### Transaction Patterns

**Multi-Entity** - Cross-table operations
```yaml
patterns:
  - name: multi_entity
    entities: [order, order_item]
    operation: create_order_with_items
```

**Saga** - Distributed transactions
```yaml
patterns:
  - name: saga
    steps:
      - action: reserve_inventory
        compensation: release_inventory
      - action: charge_payment
        compensation: refund_payment
```

### Operational Patterns

**Batch Operations** - Bulk data processing
```yaml
patterns:
  - name: batch_operations
    operation: bulk_update_status
    batch_size: 100
```

**Soft Delete** - Safe record deletion
```yaml
patterns:
  - name: soft_delete
    retention_days: 90
```

## 🔄 Pattern Composition

### Combining Patterns

Patterns can work together on the same entity:

```yaml
# entities/order.yaml
name: order
fields:
  id: uuid
  status: string
  total: decimal
  customer_id: uuid

patterns:
  # State management
  - name: state_machine
    states: [pending, confirmed, shipped, delivered]

  # Data validation
  - name: validation
    rules:
      - name: positive_total
        rule: "total > 0"

  # Audit compliance
  - name: audit_trail
    track_fields: [status, total]
```

### Pattern Interactions

- **State machines** can trigger **validation** checks
- **Audit trails** record **state transitions**
- **Multi-entity** operations use **state machines**

## ⚙️ Pattern Configuration

### Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `description` | Human-readable purpose | `"User approval workflow"` |
| `enabled` | Enable/disable pattern | `true` |
| `priority` | Execution order | `1` |
| `timeout` | Operation timeout | `"30 seconds"` |

### Guards and Actions

**Guards** - Precondition checks
```yaml
transitions:
  - from: pending
    to: approved
    trigger: approve
    guard: "total <= approval_limit"  # Must be true
```

**Actions** - Side effects
```yaml
transitions:
  - from: pending
    to: approved
    trigger: approve
    action: "send_approval_notification"  # Function to call
```

### Events

**Event emission** - Notify external systems
```yaml
transitions:
  - from: pending
    to: approved
    trigger: approve
    events: ["order_approved"]  # PostgreSQL NOTIFY
```

## 📊 Generated Components

Each pattern generates multiple artifacts:

### Database Objects
- **Functions** - Business logic implementation
- **Constraints** - Data integrity rules
- **Triggers** - Automatic actions
- **Indexes** - Performance optimization

### Tests
- **pgTAP tests** - Database-level validation
- **pytest tests** - Application-level testing
- **Performance tests** - Benchmarking

### Documentation
- **API docs** - Function signatures
- **Usage examples** - Code samples
- **Configuration reference** - All options

## 🎯 Best Practices

### Pattern Selection
- **Start simple** - Use basic patterns first
- **Match use case** - Choose patterns that fit your domain
- **Compose thoughtfully** - Don't combine incompatible patterns

### Configuration
- **Be specific** - Clear descriptions and names
- **Use guards** - Protect against invalid transitions
- **Add actions** - Implement side effects appropriately

### Testing
- **Test early** - Validate patterns during development
- **Run all tests** - Both pgTAP and pytest
- **Check coverage** - Ensure comprehensive testing

### Performance
- **Index guards** - Speed up precondition checks
- **Monitor usage** - Track pattern performance
- **Optimize hot paths** - Critical business operations

## 🆘 Troubleshooting

### "Pattern not recognized"
```yaml
# Check spelling and available patterns
patterns:
  - name: state_machine  # ✅ Correct
  # - name: statemachine  # ❌ Wrong
```

### "Invalid pattern configuration"
```bash
# Get detailed validation errors
specql validate entities/user.yaml --verbose

# Common issues:
# - Missing required fields
# - Invalid state names
# - Circular transitions
```

### "Pattern functions not generated"
```bash
# Regenerate after configuration changes
specql generate schema entities/user.yaml --force

# Check output directory
ls -la db/schema/40_functions/
```

### "Tests failing"
```bash
# Check test output for details
specql test run entities/user.yaml --verbose

# Common issues:
# - Schema not applied
# - Test data conflicts
# - Database permissions
```

## 🎉 Congratulations!

You've learned the fundamentals of SpecQL mutation patterns:

- ✅ **Pattern concepts** - Declarative business logic
- ✅ **Basic usage** - Adding patterns to entities
- ✅ **Generation** - Creating database implementations
- ✅ **Testing** - Comprehensive test coverage
- ✅ **Best practices** - Effective pattern usage

## 🚀 What's Next?

- **[State Machines](state-machines.md)** - Complete state machine guide
- **[Multi-Entity Operations](multi-entity.md)** - Cross-table transactions
- **[Validation](validation.md)** - Data integrity patterns
- **[Examples](../../examples/)** - Real-world pattern usage

**Ready to explore specific patterns? Let's dive deeper! 🚀**