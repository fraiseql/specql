# Mutation Patterns Library

SpecQL provides 27+ reusable mutation patterns for common business logic operations. Patterns are pre-built templates that generate database functions, constraints, and tests automatically.

## 🎯 What Are Mutation Patterns?

**Mutation patterns** are declarative templates that implement common business operations:

- **State Machines** - Order workflows, approval processes
- **Validation** - Data integrity and business rules
- **Multi-Entity Operations** - Complex transactions across tables
- **Batch Operations** - Bulk data processing
- **Audit Trails** - Change tracking and compliance
- **And 22 more...**

Instead of writing custom SQL functions, you declare what you want to achieve, and SpecQL generates the implementation.

## 💡 Why Use Patterns?

### ✅ Benefits
- **Consistency** - Standardized implementations across your application
- **Reliability** - Battle-tested patterns from real-world applications
- **Productivity** - 10x faster development than custom SQL
- **Maintainability** - Declarative specifications are easy to modify
- **Testing** - Automatic test generation with comprehensive coverage

### 🚀 Productivity Impact
| Approach | Time to Implement | Lines of Code | Test Coverage |
|----------|------------------|---------------|----------------|
| **Custom SQL** | 2-3 days | 200+ lines | Manual (incomplete) |
| **SpecQL Pattern** | 30 minutes | 5 lines YAML | Auto (100%) |

## 📚 Available Patterns

### Core Business Logic (Essential)

| Pattern | Purpose | Use Cases | Complexity |
|---------|---------|-----------|------------|
| **[`state_machine`](state-machines.md)** | Entity lifecycle management | User accounts, orders, approvals | 🟢 Beginner |
| **[`validation`](validation.md)** | Data integrity rules | Business constraints, input validation | 🟢 Beginner |
| **[`multi_entity`](multi-entity.md)** | Cross-table transactions | Order with line items, account transfers | 🟡 Intermediate |
| **[`batch_operations`](batch-operations.md)** | Bulk data processing | Mass updates, imports | 🟡 Intermediate |
| **`soft_delete`** | Safe record deletion | Data recovery, audit compliance | 🟢 Beginner |

### Advanced Patterns (Complex Logic)

| Pattern | Purpose | Use Cases | Complexity |
|---------|---------|-----------|------------|
| **`audit_trail`** | Change tracking | Compliance, debugging | 🟢 Beginner |
| **`versioning`** | Data versioning | Historical records, rollback | 🟡 Intermediate |
| **`workflow`** | Complex processes | Multi-step approvals, routing | 🔴 Advanced |
| **`scheduling`** | Time-based operations | Recurring tasks, deadlines | 🟡 Intermediate |
| **`notifications`** | Event-driven messaging | Email alerts, webhooks | 🟡 Intermediate |

### Integration Patterns (External Systems)

| Pattern | Purpose | Use Cases | Complexity |
|---------|---------|-----------|------------|
| **`api_integration`** | External API calls | Payment processing, third-party services | 🔴 Advanced |
| **`event_sourcing`** | Event-driven architecture | Audit logs, CQRS | 🔴 Advanced |
| **`saga`** | Distributed transactions | Multi-service operations | 🔴 Advanced |
| **`circuit_breaker`** | Fault tolerance | Service degradation handling | 🔴 Advanced |

### Utility Patterns (Infrastructure)

| Pattern | Purpose | Use Cases | Complexity |
|---------|---------|-----------|------------|
| **`rate_limiting`** | Request throttling | API protection, abuse prevention | 🟡 Intermediate |
| **`feature_flags`** | Dynamic features | A/B testing, gradual rollouts | 🟡 Intermediate |
| **`permissions`** | Access control | Role-based security | 🟡 Intermediate |
| **`data_archiving`** | Long-term storage | Compliance, performance | 🟡 Intermediate |
| **`search_indexing`** | Full-text search | Product catalogs, content | 🟡 Intermediate |
| **`caching`** | Performance optimization | Frequent queries, computed values | 🟡 Intermediate |

**Legend**: 🟢 Beginner • 🟡 Intermediate • 🔴 Advanced

## 🚀 Quick Start

### 1. Add Pattern to Entity

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
    states: [inactive, active, suspended]
    initial_state: inactive
    transitions:
      - from: inactive
        to: active
        trigger: activate
```

### 2. Generate

```bash
# Generate schema with patterns
specql generate schema entities/user.yaml
```

### 3. Use Generated Functions

```sql
-- Activate user
SELECT user_activate('user-uuid-123');

-- Check available transitions
SELECT * FROM user_get_available_transitions('user-uuid-123');
```

## 📖 Pattern Guides

### Getting Started
- **[Getting Started](getting-started.md)** - Pattern basics and concepts
- **[State Machines](state-machines.md)** - Complete state machine guide
- **[Multi-Entity Operations](multi-entity.md)** - Cross-table transactions

### Core Patterns
- **[Validation](validation.md)** - Data integrity and business rules
- **[Batch Operations](batch-operations.md)** - Bulk data processing
- **[Composing Patterns](composing-patterns.md)** - Combining multiple patterns

### Advanced Patterns
- **[Custom Patterns](custom-patterns.md)** - Creating your own patterns
- **[Pattern Extensions](extensions.md)** - Extending existing patterns

## 💡 Pattern Concepts

### Declarative vs Imperative

**Imperative (Traditional SQL):**
```sql
-- Custom function with business logic
CREATE FUNCTION activate_user(user_id UUID) RETURNS VOID AS $$
BEGIN
  -- Check current status
  IF (SELECT status FROM users WHERE id = user_id) != 'inactive' THEN
    RAISE EXCEPTION 'User not inactive';
  END IF;

  -- Update status
  UPDATE users SET status = 'active', activated_at = NOW()
  WHERE id = user_id;

  -- Log the change
  INSERT INTO audit_log (action, user_id, old_status, new_status)
  VALUES ('activate', user_id, 'inactive', 'active');
END;
$$ LANGUAGE plpgsql;
```

**Declarative (SpecQL Pattern):**
```yaml
patterns:
  - name: state_machine
    states: [inactive, active]
    transitions:
      - from: inactive
        to: active
        trigger: activate
        action: "log_user_activation"
```

### Pattern Composition

Patterns can work together:

```yaml
patterns:
  # State machine for status
  - name: state_machine
    states: [draft, published, archived]

  # Validation for business rules
  - name: validation
    rules:
      - name: published_must_have_title
        condition: "status = 'published' AND title IS NOT NULL"

  # Audit trail for compliance
  - name: audit_trail
    track_fields: [status, title]
```

### Generated Components

Each pattern generates multiple components:

```
Pattern: state_machine
├── Functions: user_activate(), user_get_transitions()
├── Constraints: CHECK (status IN ('inactive', 'active'))
├── Triggers: Automatic status validation
├── Tests: Comprehensive test coverage
└── Documentation: Auto-generated guides
```

## 🎯 Choosing the Right Pattern

### Decision Tree

```
Need to manage entity states?
├── Yes → state_machine
└── No → Need data validation?
    ├── Yes → validation
    └── No → Need cross-table operations?
        ├── Yes → multi_entity
        └── No → Need bulk processing?
            ├── Yes → batch_operations
            └── No → Need audit trail?
                ├── Yes → audit_trail
                └── No → Check advanced patterns...
```

### Common Combinations

| Use Case | Pattern Combination |
|----------|-------------------|
| **E-commerce Order** | `state_machine` + `multi_entity` + `validation` |
| **User Management** | `state_machine` + `audit_trail` + `permissions` |
| **Content Management** | `workflow` + `versioning` + `validation` |
| **Financial Transaction** | `saga` + `audit_trail` + `validation` |

## 🔧 Pattern Configuration

### Basic Structure

```yaml
patterns:
  - name: pattern_name
    description: "What this pattern does"
    # Pattern-specific configuration
    option1: value1
    option2: value2
```

### Advanced Configuration

```yaml
patterns:
  - name: state_machine
    description: "Order processing workflow"
    # Basic settings
    initial_state: pending
    allow_self_transitions: false

    # State definitions
    states:
      - name: pending
        description: "Awaiting payment"
      - name: paid
        description: "Payment received"

    # Transition rules
    transitions:
      - from: pending
        to: paid
        trigger: mark_paid
        guard: "total_amount > 0"
        action: "send_order_confirmation"
        events: ["order_paid"]
```

## 🧪 Testing Patterns

Patterns generate comprehensive tests automatically:

```bash
# Generate tests
specql generate tests entities/user.yaml

# Run tests
specql test run entities/user.yaml

# Check coverage
specql test coverage entities/user.yaml
```

**Generated test coverage:**
- ✅ **Happy path** - Normal operation
- ✅ **Edge cases** - Boundary conditions
- ✅ **Error conditions** - Invalid inputs
- ✅ **Guard conditions** - Precondition validation
- ✅ **Actions** - Side effect execution

## 📊 Performance Characteristics

| Pattern | Performance | Use Case |
|---------|-------------|----------|
| **state_machine** | ⚡ Fast | High-frequency operations |
| **validation** | ⚡ Fast | Data integrity checks |
| **multi_entity** | 🐌 Slower | Complex transactions |
| **audit_trail** | ⚡ Fast | Compliance logging |
| **batch_operations** | 🐌 Slower | Bulk processing |

## 🚀 Best Practices

### Pattern Design
- **Start simple** - Use basic patterns first
- **Compose thoughtfully** - Don't over-engineer
- **Test early** - Validate patterns work as expected
- **Document intent** - Clear descriptions for maintenance

### Performance
- **Index guard fields** - Speed up precondition checks
- **Batch where possible** - Use batch patterns for bulk operations
- **Monitor slow patterns** - Profile performance-critical patterns

### Maintenance
- **Version patterns** - Track pattern changes
- **Refactor gradually** - Test changes thoroughly
- **Document extensions** - Explain custom pattern modifications

## 🆘 Troubleshooting

### "Pattern not found"
```yaml
# Check pattern name spelling
patterns:
  - name: state_machine  # ✅ Correct
  # - name: statemachine  # ❌ Wrong
```

### "Invalid pattern configuration"
```bash
# Validate configuration
specql validate entities/user.yaml --verbose

# Check pattern documentation for required fields
```

### "Pattern conflicts"
```yaml
# Some patterns can't be combined
patterns:
  - name: soft_delete
  - name: versioning  # May conflict with soft_delete
```

### "Performance issues"
```bash
# Add indexes for guard conditions
indexes:
  - fields: [status]
    where: "status IN ('active', 'inactive')"
```

## 🎉 Next Steps

- **[Getting Started](getting-started.md)** - Learn pattern basics
- **[State Machines](state-machines.md)** - Complete state machine guide
- **[Examples](../../examples/)** - See patterns in action
- **[Custom Patterns](custom-patterns.md)** - Create your own patterns

**Ready to add business logic to your entities? Let's explore the patterns! 🚀**