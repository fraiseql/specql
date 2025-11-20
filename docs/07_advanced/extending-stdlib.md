# Extending the Standard Library

> **Contribute new patterns, rich types, and generators to SpecQL**

## Overview

SpecQL's standard library (stdlib) is extensible. You can:
- ✅ Add new rich types
- ✅ Create reusable patterns
- ✅ Contribute custom generators
- ✅ Share with the community

**Goal**: Build a comprehensive library of battle-tested patterns.

---

## Contributing Rich Types

### Creating a New Rich Type

**File**: `src/core/scalar_types.py`

```python
# Add to SCALAR_TYPES dictionary
SCALAR_TYPES = {
    # ... existing types

    # New rich type: Credit card number
    'creditCard': {
        'postgres_type': 'TEXT',
        'validation': r'^[0-9]{13,19}$',  # 13-19 digits
        'graphql_scalar': 'CreditCard',
        'description': 'Credit card number (PCI-compliant storage requires encryption)',
        'examples': ['4111111111111111', '5500000000000004'],
    },

    # New rich type: Social Security Number (US)
    'ssn': {
        'postgres_type': 'TEXT',
        'validation': r'^\d{3}-\d{2}-\d{4}$',  # XXX-XX-XXXX format
        'graphql_scalar': 'SSN',
        'description': 'US Social Security Number (must be encrypted)',
        'examples': ['123-45-6789'],
        'requires_encryption': True,  # Flag for sensitive data
    },

    # New rich type: Color hex code
    'colorHex': {
        'postgres_type': 'TEXT(7)',
        'validation': r'^#[0-9A-Fa-f]{6}$',  # #RRGGBB
        'graphql_scalar': 'ColorHex',
        'description': 'Hexadecimal color code',
        'examples': ['#FF5733', '#00FF00'],
    },
}
```

---

### Testing New Rich Types

**File**: `tests/unit/core/test_scalar_types.py`

```python
import pytest
from src.core.scalar_types import SCALAR_TYPES, validate_scalar_value

def test_credit_card_validation():
    """Test credit card validation"""
    assert validate_scalar_value('creditCard', '4111111111111111') == True
    assert validate_scalar_value('creditCard', '5500000000000004') == True
    assert validate_scalar_value('creditCard', 'invalid') == False
    assert validate_scalar_value('creditCard', '123') == False  # Too short

def test_ssn_validation():
    """Test SSN validation"""
    assert validate_scalar_value('ssn', '123-45-6789') == True
    assert validate_scalar_value('ssn', '000-00-0000') == True
    assert validate_scalar_value('ssn', '123456789') == False  # Missing dashes
    assert validate_scalar_value('ssn', '12-345-6789') == False  # Wrong format

def test_color_hex_validation():
    """Test hex color validation"""
    assert validate_scalar_value('colorHex', '#FF5733') == True
    assert validate_scalar_value('colorHex', '#00ff00') == True  # Lowercase OK
    assert validate_scalar_value('colorHex', 'FF5733') == False  # Missing #
    assert validate_scalar_value('colorHex', '#FFF') == False  # Short form not supported
```

---

### Documenting Rich Types

**File**: `docs/06_reference/rich-types-reference.md`

Add to appropriate category:

```markdown
## Financial & Identity

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| `creditCard` | 13-19 digits | `4111111111111111` | Requires PCI compliance + encryption |
| `ssn` | XXX-XX-XXXX | `123-45-6789` | Requires encryption (SECURITY) |
| `colorHex` | #RRGGBB | `#FF5733` | CSS hex color |
```

---

## Contributing Patterns

### Creating a New Pattern

**File**: `src/patterns/stdlib/workflow/escalation.yaml`

```yaml
pattern: escalation_workflow
description: Automatic escalation after timeout

parameters:
  escalation_hours: integer = 24
  escalation_role: text = 'manager'

fields:
  assigned_to: ref(User)
  assigned_at: datetime
  escalated_to: ref(User)
  escalated_at: datetime
  escalation_reason: text

actions:
  - name: check_escalation
    steps:
      # Check if escalation needed
      - if: |
          assigned_at IS NOT NULL AND
          escalated_at IS NULL AND
          NOW() - assigned_at > INTERVAL '${escalation_hours} hours'
        then:
          # Find escalation user
          - query: |
              SELECT id FROM User
              WHERE roles @> ARRAY['${escalation_role}']
              ORDER BY random()
              LIMIT 1
            result: $escalation_user

          # Escalate
          - update: ENTITY SET
              escalated_to = $escalation_user.id,
              escalated_at = NOW(),
              escalation_reason = 'timeout_after_${escalation_hours}_hours'

          # Notify
          - notify: task_escalated, to: $escalation_user.email

triggers:
  # Auto-check escalation on updates
  - event: update
    when: assigned_at IS NOT NULL
    action: check_escalation
```

---

### Testing Patterns

**File**: `tests/unit/patterns/test_escalation_workflow.py`

```python
import pytest
from src.patterns.pattern_registry import PatternRegistry

def test_escalation_workflow_pattern():
    """Test escalation workflow pattern"""
    registry = PatternRegistry()
    pattern = registry.get_pattern('escalation_workflow')

    assert pattern is not None
    assert 'assigned_to' in pattern.fields
    assert 'escalated_to' in pattern.fields
    assert 'check_escalation' in pattern.actions

def test_escalation_workflow_applied(db_connection):
    """Test pattern applied to entity"""
    # Apply pattern to Task entity
    task_yaml = """
    entity: Task
    patterns:
      - escalation_workflow:
          escalation_hours: 48
          escalation_role: 'supervisor'

    fields:
      title: text!
      description: text
    """

    # Generate schema
    sql = generate_schema(task_yaml)

    # Verify fields added
    assert 'assigned_to' in sql
    assert 'escalated_to' in sql

    # Verify action created
    assert 'check_escalation' in sql
```

---

### Documenting Patterns

**File**: `docs/07_advanced/custom-patterns.md`

```markdown
### escalation_workflow

**Purpose**: Auto-escalate tasks after timeout

**Parameters**:
- `escalation_hours` (default: 24) - Hours before escalation
- `escalation_role` (default: 'manager') - Role to escalate to

**Adds**:
- `assigned_to: ref(User)` - Current assignee
- `escalated_to: ref(User)` - Escalation recipient
- `escalation_reason: text` - Why escalated

**Usage**:
```yaml
entity: SupportTicket
patterns:
  - escalation_workflow:
      escalation_hours: 48
      escalation_role: 'supervisor'

fields:
  title: text!
  priority: enum(low, medium, high)!
```
```

---

## Contributing Generators

### Custom Generator Structure

**File**: `src/generators/custom/notification_generator.py`

```python
from typing import Dict, List
from src.core.ast_models import Entity, Action

class NotificationGenerator:
    """Generate notification infrastructure for actions"""

    def generate(self, entities: List[Entity]) -> str:
        """Generate notification SQL"""
        sql_parts = []

        # Generate notification channels table
        sql_parts.append(self._generate_channels_table())

        # Generate notification log table
        sql_parts.append(self._generate_log_table())

        # Generate notification function
        sql_parts.append(self._generate_notification_function())

        # Generate triggers for actions with notifications
        for entity in entities:
            for action in entity.actions:
                if self._has_notify_steps(action):
                    sql_parts.append(
                        self._generate_notification_trigger(entity, action)
                    )

        return '\n\n'.join(sql_parts)

    def _generate_channels_table(self) -> str:
        """Generate notification channels configuration table"""
        return """
CREATE TABLE IF NOT EXISTS core.notification_channels (
    channel_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    channel_name TEXT UNIQUE NOT NULL,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('email', 'sms', 'webhook', 'push')),
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notification_channels_name ON core.notification_channels(channel_name);
"""

    def _generate_log_table(self) -> str:
        """Generate notification log table"""
        return """
CREATE TABLE IF NOT EXISTS core.notification_log (
    log_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    channel_name TEXT NOT NULL,
    recipient TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    metadata JSONB,
    sent_at TIMESTAMP DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    error_message TEXT
);

CREATE INDEX idx_notification_log_channel ON core.notification_log(channel_name);
CREATE INDEX idx_notification_log_status ON core.notification_log(status);
CREATE INDEX idx_notification_log_sent_at ON core.notification_log(sent_at);
"""

    def _generate_notification_function(self) -> str:
        """Generate core notification dispatch function"""
        return """
CREATE OR REPLACE FUNCTION core.send_notification(
    p_channel_name TEXT,
    p_recipient TEXT,
    p_subject TEXT DEFAULT NULL,
    p_body TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS BIGINT AS $$
DECLARE
    v_log_id BIGINT;
BEGIN
    -- Log notification
    INSERT INTO core.notification_log (
        channel_name,
        recipient,
        subject,
        body,
        metadata,
        status
    ) VALUES (
        p_channel_name,
        p_recipient,
        p_subject,
        p_body,
        p_metadata,
        'pending'
    ) RETURNING log_id INTO v_log_id;

    -- Trigger async processing (via LISTEN/NOTIFY or job queue)
    PERFORM pg_notify('notification_pending', v_log_id::TEXT);

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;
"""

    def _has_notify_steps(self, action: Action) -> bool:
        """Check if action has notify steps"""
        return any(step.type == 'notify' for step in action.steps)

    def _generate_notification_trigger(self, entity: Entity, action: Action) -> str:
        """Generate trigger to send notifications after action"""
        return f"""
-- Notification trigger for {entity.name}.{action.name}
CREATE OR REPLACE FUNCTION core.notify_after_{entity.name}_{action.name}()
RETURNS TRIGGER AS $$
BEGIN
    -- Send notifications configured in action
    -- (Implementation depends on action steps)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_{entity.name}_{action.name}_notify
    AFTER INSERT OR UPDATE ON {entity.schema}.tb_{entity.name.lower()}
    FOR EACH ROW
    EXECUTE FUNCTION core.notify_after_{entity.name}_{action.name}();
"""
```

---

### Integrating Custom Generator

**File**: `src/cli/orchestrator.py`

```python
from src.generators.custom.notification_generator import NotificationGenerator

class GenerationOrchestrator:
    def __init__(self):
        # ... existing generators
        self.notification_generator = NotificationGenerator()

    def generate_all(self, entities: List[Entity], output_dir: str):
        """Generate all code"""
        # ... existing generation

        # Generate notification infrastructure
        notification_sql = self.notification_generator.generate(entities)
        self._write_file(
            f"{output_dir}/schema/05_infrastructure/notifications.sql",
            notification_sql
        )
```

---

## Contribution Process

### 1. Fork and Clone

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
git checkout -b feature/new-rich-type-credit-card
```

---

### 2. Make Changes

```bash
# Add rich type
vim src/core/scalar_types.py

# Add tests
vim tests/unit/core/test_scalar_types.py

# Add documentation
vim docs/06_reference/rich-types-reference.md
```

---

### 3. Run Tests

```bash
# Run all tests
make test

# Run specific team tests
make teamA-test  # Parser tests

# Check coverage
pytest --cov=src --cov-report=html
```

---

### 4. Submit Pull Request

```bash
git add .
git commit -m "feat: add creditCard rich type with PCI validation"
git push origin feature/new-rich-type-credit-card
```

**PR Template**:
```markdown
## Description
Adds `creditCard` rich type for credit card number validation.

## Type of Change
- [x] New rich type
- [ ] New pattern
- [ ] New generator
- [ ] Bug fix
- [ ] Documentation

## Testing
- [x] Unit tests added
- [x] Integration tests pass
- [x] Documentation updated

## Security Considerations
- Credit card numbers require PCI compliance
- Recommends encryption at-rest
- Added warning in documentation
```

---

## Best Practices

### ✅ DO

**Follow naming conventions**:
```python
# Good: camelCase for rich types
'creditCard', 'phoneNumber', 'emailAddress'

# Good: snake_case for patterns
'audit_trail', 'soft_delete', 'multi_tenant'

# Good: PascalCase for GraphQL scalars
'CreditCard', 'PhoneNumber', 'EmailAddress'
```

**Add comprehensive examples**:
```python
'creditCard': {
    # ... type definition
    'examples': [
        '4111111111111111',  # Visa
        '5500000000000004',  # Mastercard
        '340000000000009',   # Amex
    ],
    'invalid_examples': [
        '123',              # Too short
        'not-a-card',       # Invalid format
    ],
}
```

**Document security implications**:
```python
'ssn': {
    # ...
    'security_warning': 'MUST be encrypted at-rest. Use pgcrypto or application-level encryption.',
    'compliance': ['PII', 'GDPR', 'HIPAA'],
}
```

---

### ❌ DON'T

**Don't add overly specific types**:
```python
# Bad: Too specific
'amazonProductId': {...}  # Use generic 'sku' instead

# Good: Generic and reusable
'sku': {...}
```

**Don't skip tests**:
```python
# Bad: No tests
def new_generator(...):
    # Complex logic with no tests
    ...

# Good: Comprehensive tests
def test_new_generator():
    assert generated_code == expected_code
```

---

## Community Patterns Repository

### Publishing Patterns

**Create pattern package**:

```
my-pattern/
├── pattern.yaml           # Pattern definition
├── README.md             # Documentation
├── examples/             # Usage examples
│   └── order_workflow.yaml
└── tests/                # Pattern tests
    └── test_pattern.py
```

**Publish to npm** (for TypeScript patterns):
```bash
npm publish @specql-patterns/my-pattern
```

**Install pattern**:
```bash
specql pattern install @specql-patterns/order-workflow
```

---

## Next Steps

### Learn More

- **[Custom Patterns](custom-patterns.md)** - Pattern creation guide
- **[Testing Guide](testing.md)** - Test your contributions

### Contribute

- **GitHub**: https://github.com/fraiseql/specql
- **Discord**: https://discord.gg/specql
- **Forum**: https://discuss.specql.dev

---

## Summary

You've learned:
- ✅ How to add new rich types
- ✅ How to create reusable patterns
- ✅ How to build custom generators
- ✅ Contribution process
- ✅ Best practices for stdlib extensions

**Key Takeaway**: SpecQL is extensible—contribute your patterns and types to benefit the entire community.

**Next**: Optimize GraphQL with [GraphQL Optimization](graphql-optimization.md) →

---

**Extend the standard library—share your expertise with the community.**
