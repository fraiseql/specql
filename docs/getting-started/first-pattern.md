# Use Your First Pattern

Learn how to add business logic to your entities using SpecQL's mutation patterns. Patterns are reusable templates for common operations like state machines, validation, and multi-entity transactions.

## 🎯 What You'll Learn

- Understand mutation patterns
- Add a state machine pattern
- Configure pattern options
- Generate and test pattern logic
- Use patterns in your applications

## 📋 Prerequisites

- [First entity created](first-entity.md)
- Basic understanding of YAML
- PostgreSQL database ready

## 🔄 Step 1: Understand Mutation Patterns

SpecQL provides 27+ reusable patterns for common business logic:

### Available Patterns

| Pattern | Purpose | Use Case |
|---------|---------|----------|
| **state_machine** | Manage entity states | Order workflow, user status |
| **validation** | Data validation rules | Business constraints |
| **multi_entity** | Cross-table operations | Order with line items |
| **batch_operations** | Bulk data processing | Mass updates |
| **audit_trail** | Change tracking | Compliance logging |
| **soft_delete** | Safe deletion | Data recovery |
| **versioning** | Data versioning | Historical records |

## 🏗️ Step 2: Add State Machine Pattern

Let's add a user account lifecycle to your user entity:

```yaml
# entities/user.yaml
name: user
description: "User account with profile information"

fields:
  id: uuid
  email: string
  first_name: string
  last_name: string
  status: string          # Will be managed by state machine
  company_id: uuid?
  phone: string?
  date_of_birth: date?
  is_active: boolean
  created_at: timestamp
  updated_at: timestamp

patterns:
  - name: state_machine
    description: "User account lifecycle management"
    states:
      - inactive
      - pending_verification
      - active
      - suspended
      - deactivated
    initial_state: inactive
    transitions:
      - from: inactive
        to: pending_verification
        trigger: request_verification
        guard: "email IS NOT NULL"
      - from: pending_verification
        to: active
        trigger: verify_email
        action: "send_welcome_email"
      - from: active
        to: suspended
        trigger: suspend
        reason: "Violation of terms"
      - from: suspended
        to: active
        trigger: reactivate
      - from: active
        to: deactivated
        trigger: deactivate
        guard: "is_active = false"
```

## ⚙️ Step 3: Configure Pattern Options

### State Machine Configuration

```yaml
patterns:
  - name: state_machine
    # Basic settings
    initial_state: inactive    # Starting state
    allow_self_transitions: false  # Can transition to same state?

    # State definitions with metadata
    states:
      - name: inactive
        description: "Account created but not verified"
        color: "gray"
      - name: active
        description: "Fully active account"
        color: "green"
      - name: suspended
        description: "Temporarily disabled"
        color: "red"

    # Transition rules
    transitions:
      - from: inactive
        to: pending_verification
        trigger: request_verification
        guard: "email IS NOT NULL"          # Condition must be true
        action: "send_verification_email"   # Function to call
        events: ["user_verification_requested"]  # Events to emit
```

### Common Pattern Options

| Option | Purpose | Example |
|--------|---------|---------|
| `guard` | Precondition check | `"balance > 0"` |
| `action` | Function to execute | `"send_notification"` |
| `events` | Events to emit | `["order_created"]` |
| `timeout` | Time limit | `"30 minutes"` |
| `retries` | Retry attempts | `3` |

## 🔧 Step 4: Generate Pattern Code

```bash
# Validate the pattern configuration
specql validate entities/user.yaml

# Generate the schema with patterns
specql generate schema entities/user.yaml

# Check generated files
ls -la db/schema/
# 00_foundation/
# 10_tables/
# ├── user.sql
# 20_constraints/
# 30_indexes/
# 40_functions/
# └── user_state_machine.sql
```

## 📄 Step 5: Review Generated Functions

```bash
# View the state machine functions
cat db/schema/40_functions/user_state_machine.sql
```

**Generated functions include:**

```sql
-- State transition functions
CREATE FUNCTION user_request_verification(user_id UUID)
RETURNS user_state_transition_result AS $$
-- Validate guard: email IS NOT NULL
-- Execute transition: inactive -> pending_verification
-- Call action: send_verification_email
-- Emit events: user_verification_requested
$$ LANGUAGE plpgsql;

CREATE FUNCTION user_verify_email(user_id UUID, token TEXT)
RETURNS user_state_transition_result AS $$
-- Validate token
-- Execute transition: pending_verification -> active
-- Call action: send_welcome_email
-- Update user status
$$ LANGUAGE plpgsql;

-- State query functions
CREATE FUNCTION user_get_available_transitions(user_id UUID)
RETURNS TABLE(transition_name TEXT, from_state TEXT, to_state TEXT) AS $$
-- Return possible transitions from current state
$$ LANGUAGE sql;

CREATE FUNCTION user_can_transition(user_id UUID, transition TEXT)
RETURNS BOOLEAN AS $$
-- Check if transition is allowed
$$ LANGUAGE sql;
```

## 🗄️ Step 6: Apply to Database

```bash
# Apply all schema components
psql $DATABASE_URL -f db/schema/00_foundation/*.sql
psql $DATABASE_URL -f db/schema/10_tables/user.sql
psql $DATABASE_URL -f db/schema/20_constraints/*.sql
psql $DATABASE_URL -f db/schema/30_indexes/*.sql
psql $DATABASE_URL -f db/schema/40_functions/user_state_machine.sql
```

## 🧪 Step 7: Test the State Machine

```bash
# Connect to database
psql $DATABASE_URL

# Create a test user
INSERT INTO user (email, first_name, last_name)
VALUES ('john@example.com', 'John', 'Doe')
RETURNING id;

# Check initial state
SELECT id, email, status FROM user;

# Try invalid transition (should fail)
SELECT user_verify_email(user_id, 'invalid-token');

# Request verification
SELECT user_request_verification(user_id);

# Check available transitions
SELECT * FROM user_get_available_transitions(user_id);

# Complete verification
SELECT user_verify_email(user_id, 'valid-token');

# Check final state
SELECT id, email, status, updated_at FROM user;
```

**Expected workflow:**
```
1. User created: status = 'inactive'
2. Request verification: status = 'pending_verification'
3. Verify email: status = 'active'
```

## 🎯 Step 8: Use in Application Code

### Direct SQL Calls

```python
import psycopg2

def activate_user(user_id, token):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_verify_email(%s, %s)
            """, (user_id, token))
            result = cursor.fetchone()
            return result[0]  # Success/failure
```

### GraphQL Integration

```graphql
mutation VerifyUserEmail($userId: UUID!, $token: String!) {
  verifyUserEmail(userId: $userId, token: $token) {
    success
    newState
    transitionedAt
    errors {
      message
      code
    }
  }
}
```

### REST API

```javascript
// POST /api/users/{userId}/verify-email
app.post('/api/users/:userId/verify-email', async (req, res) => {
  const { userId } = req.params;
  const { token } = req.body;

  try {
    const result = await db.query(
      'SELECT user_verify_email($1, $2)',
      [userId, token]
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

## 🚀 Step 9: Add More Patterns

### Combine Multiple Patterns

```yaml
patterns:
  # State machine for status
  - name: state_machine
    states: [inactive, active, suspended]
    transitions:
      - from: inactive
        to: active
        trigger: activate

  # Validation for data integrity
  - name: validation
    rules:
      - name: email_format
        field: email
        rule: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
      - name: age_positive
        field: date_of_birth
        rule: "date_of_birth IS NULL OR date_of_birth < CURRENT_DATE - INTERVAL '13 years'"

  # Audit trail for compliance
  - name: audit_trail
    track_fields: [status, email]
    track_changes: true
```

### Pattern Interactions

Patterns can work together:
- **State machines** trigger **validation** checks
- **Audit trails** record **state transitions**
- **Multi-entity** operations use **state machines**

## 🎯 Best Practices

### Pattern Selection
- **Start simple**: Use basic patterns first
- **Combine thoughtfully**: Don't over-engineer
- **Test thoroughly**: Each pattern adds complexity

### State Machine Design
- **Clear states**: Use descriptive names
- **Minimal transitions**: Avoid complex flows
- **Guards**: Protect against invalid transitions
- **Actions**: Keep side effects minimal

### Error Handling
- **Validate inputs**: Check data before transitions
- **Handle failures**: Plan for transition failures
- **Log events**: Track state changes for debugging

## 🆘 Troubleshooting

### "Pattern validation failed"
```bash
# Check pattern syntax
specql validate entities/user.yaml --verbose

# Common issues:
# - Invalid state names (use lowercase, underscores)
# - Missing required fields
# - Circular transitions
```

### "Function does not exist"
```bash
# Regenerate after pattern changes
specql generate schema entities/user.yaml --force

# Apply the new functions
psql $DATABASE_URL -f db/schema/40_functions/user_state_machine.sql
```

### "Guard condition failed"
```bash
# Check the guard logic
# Guards must be valid SQL WHERE clauses
SELECT * FROM user WHERE email IS NOT NULL AND id = 'your-id';
```

### "Transition not allowed"
```bash
# Check current state
SELECT status FROM user WHERE id = 'your-id';

# Check available transitions
SELECT * FROM user_get_available_transitions('your-id');
```

## 🎉 Congratulations!

You've successfully:
- ✅ Added a state machine pattern to your entity
- ✅ Configured states, transitions, and guards
- ✅ Generated database functions automatically
- ✅ Tested state transitions
- ✅ Integrated patterns into your application

## 🚀 What's Next?

- **[Generate Tests](first-tests.md)** - Automated testing for patterns
- **[Multi-Entity Patterns](../guides/mutation-patterns/multi-entity.md)** - Cross-table operations
- **[Custom Patterns](../guides/mutation-patterns/custom-patterns.md)** - Build your own patterns

## 📚 Related Topics

- **[All Patterns](../guides/mutation-patterns/)** - Complete pattern catalog
- **[State Machines](../guides/mutation-patterns/state-machines.md)** - Advanced state machine features
- **[Pattern Composition](../guides/mutation-patterns/composing-patterns.md)** - Combining multiple patterns

**Ready to test your patterns? Let's continue! 🚀**