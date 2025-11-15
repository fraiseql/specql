# Actions Overview

**Business logic in YAML** - Declarative action definitions that compile to production PL/pgSQL

Actions are the heart of SpecQL - they define your business logic in a declarative, testable, and maintainable way. Instead of writing complex SQL procedures, you describe what should happen using simple steps.

## 🎯 What Are Actions?

Actions are business operations that:
- **Validate** data and business rules
- **Manipulate** database records
- **Enforce** security and permissions
- **Notify** other systems
- **Return** structured responses

## 📋 Action Structure

```yaml
actions:
  - name: qualify_lead
    description: "Convert a lead to a qualified prospect"
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

## 🔧 Action Properties

### name
**Type**: String (snake_case)
**Required**: Yes

Action identifier. Must be:
- snake_case
- Unique within the entity
- Descriptive of the business operation

```yaml
name: qualify_lead        # ✅ Good
name: QualifyLead         # ❌ PascalCase
name: qualify-lead        # ❌ hyphens
```

### description
**Type**: String
**Required**: No (but recommended)

Human-readable description for:
- API documentation
- Developer understanding
- Generated comments

### requires
**Type**: String (permission expression)
**Required**: No

Authorization requirement. Examples:
```yaml
requires: caller.can_edit_contact     # Specific permission
requires: caller.is_admin            # Admin access
requires: owner.id = caller.id       # Self-access only
```

### steps
**Type**: Array of step objects
**Required**: Yes

Sequence of operations to execute.

## 🚀 Generated Code

SpecQL compiles actions to PL/pgSQL functions:

### Core Function
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
-- Compiled business logic
$$;
```

### GraphQL Wrapper
```sql
CREATE OR REPLACE FUNCTION app.qualify_lead(args JSONB)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN crm.qualify_lead(
        (args->>'contact_id')::UUID,
        (args->>'caller_id')::UUID
    );
END;
$$;
```

## 📊 Step Types

Actions support 25+ step types organized by category:

### Core Steps (Universal)
- `validate` - Data and business rule validation
- `if` - Conditional execution
- `insert` - Create new records
- `update` - Modify existing records
- `delete` - Remove records
- `call` - Invoke other actions
- `notify` - Send notifications
- `foreach` - Iterate over collections

### Advanced Steps
- `partial_update` - Selective field updates
- `duplicate_check` - Prevent duplicates
- `call_service` - External service calls
- `aggregate` - Data aggregation
- `call_function` - Direct function calls
- `cte` - Common table expressions
- `declare` - Variable declarations
- `exception_handling` - Error management
- `for_query` - Query-based loops
- `json_build` - JSON construction
- `return_early` - Premature returns
- `subquery` - Subquery operations
- `switch` - Multi-condition branching
- `while` - Conditional loops

## 🔄 Action Execution Flow

1. **Authorization Check** - Verify `requires` permission
2. **Parameter Resolution** - Map inputs to internal values
3. **Step Execution** - Process steps in order
4. **Response Building** - Construct structured result
5. **Transaction Management** - Automatic commit/rollback

## 🎯 Action Patterns

### CRUD Operations
```yaml
actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL
      - insert: Contact

  - name: update_contact
    steps:
      - validate: caller.can_edit_contact
      - update: Contact SET email = $email

  - name: delete_contact
    steps:
      - validate: status != 'active'
      - delete: Contact
```

### Business Workflows
```yaml
actions:
  - name: process_order
    steps:
      - validate: inventory >= quantity
      - update: Product SET inventory = inventory - $quantity
      - insert: Order
      - notify: customer(email, "Order confirmed")
```

### Complex Validation
```yaml
actions:
  - name: approve_loan
    steps:
      - validate: credit_score >= 700
        error: "insufficient_credit"
      - validate: income >= 50000
        error: "insufficient_income"
      - validate: existing_loans < 3
        error: "too_many_loans"
      - update: Loan SET status = 'approved'
```

## 🔐 Authorization

### Permission-Based
```yaml
actions:
  - name: delete_user
    requires: caller.is_admin
    steps:
      - delete: User
```

### Data-Based
```yaml
actions:
  - name: update_profile
    requires: owner.id = caller.id
    steps:
      - update: User SET profile = $profile
```

### Complex Rules
```yaml
actions:
  - name: approve_expense
    requires: caller.can_approve_expenses AND amount <= caller.approval_limit
    steps:
      - update: Expense SET status = 'approved'
```

## 📝 Error Handling

Actions provide structured error responses:

```yaml
actions:
  - name: transfer_money
    steps:
      - validate: balance >= amount
        error: "insufficient_funds"
      - validate: target_account IS NOT NULL
        error: "invalid_target"
      - update: Account SET balance = balance - $amount WHERE id = $source
      - update: Account SET balance = balance + $amount WHERE id = $target
```

**Error Response**:
```json
{
  "success": false,
  "message": "Transfer failed",
  "errors": [
    {
      "code": "insufficient_funds",
      "message": "Account balance too low"
    }
  ]
}
```

## 🔄 Transaction Management

Actions run in transactions automatically:
- **Success**: All steps commit
- **Failure**: All steps rollback
- **Nested calls**: Participate in parent transaction

## 🎯 Best Practices

### Action Design
- **Single Responsibility**: One action, one business operation
- **Descriptive Names**: `qualify_lead`, not `update_status`
- **Validation First**: Check conditions before actions
- **Clear Errors**: Meaningful error codes and messages

### Step Organization
- **Logical Order**: Validation → Processing → Notification
- **Error Handling**: Plan for failure scenarios
- **Performance**: Minimize database round trips
- **Readability**: Group related steps

### Authorization
- **Defense in Depth**: Multiple permission checks
- **Clear Requirements**: Explicit permission expressions
- **Audit Trail**: Log security-sensitive operations

## 🚀 Advanced Patterns

### State Machines
```yaml
actions:
  - name: transition_order
    steps:
      - validate: status IN ('pending', 'processing')
      - switch: $new_status
        cases:
          shipped: "status = 'pending'"
          delivered: "status = 'shipped'"
      - update: Order SET status = $new_status
```

### Bulk Operations
```yaml
actions:
  - name: bulk_update_contacts
    steps:
      - foreach: contacts
        steps:
          - validate: item.email IS NOT NULL
          - update: Contact SET status = $status WHERE id = item.id
```

### Complex Workflows
```yaml
actions:
  - name: process_refund
    steps:
      - call: validate_refund_eligibility
      - call: calculate_refund_amount
      - call: process_payment_refund
      - notify: customer(email, "Refund processed")
```

## 📊 Performance Considerations

- **Batch Operations**: Use bulk operations for multiple records
- **Indexing**: Ensure proper indexes on queried fields
- **CTE Usage**: Use Common Table Expressions for complex queries
- **Caching**: Consider caching for reference data

## 🔍 Testing Actions

Actions are automatically tested with:
- **Unit Tests**: Individual step validation
- **Integration Tests**: Full action execution
- **Performance Tests**: Load and stress testing

## 🚀 Next Steps

- **[All Step Types](all_step_types.md)** - Complete step reference
- **[YAML Reference](../../03_reference/yaml/complete_reference.md)** - Action syntax
- **[Workflows Guide](../WORKFLOWS.md)** - Development workflows