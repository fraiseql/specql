# Pattern Authoring Guide

This guide teaches you how to create custom domain patterns for SpecQL, enabling you to capture and reuse your organization's business logic patterns.

## Overview

Domain patterns are reusable business logic templates that combine:

- **YAML Configuration Schema**: Parameter definitions and validation
- **Jinja2 Templates**: SQL generation logic for PostgreSQL, Django, and SQLAlchemy
- **Integration Tests**: Validation of generated code
- **Documentation**: Usage examples and parameter reference

## When to Create Patterns

Create a pattern when you find yourself:

- **Repeating similar logic** across multiple entities
- **Implementing common business workflows** (approvals, state machines, auditing)
- **Following organizational standards** that could be templated
- **Solving domain-specific problems** that recur

## Pattern Structure

### 1. YAML Configuration Schema

Define the pattern's parameters and their validation:

```yaml
# patterns/my_pattern.yaml
pattern: my_custom_pattern
category: business_logic
description: "Custom business logic pattern for [domain]"

parameters:
  entity_name:
    type: string
    required: true
    description: "Name of the entity to apply pattern to"

  enable_feature_x:
    type: boolean
    required: false
    default: true
    description: "Whether to enable feature X"

  max_items:
    type: integer
    required: false
    default: 10
    minimum: 1
    maximum: 100
    description: "Maximum number of items allowed"

implementation:
  # Pattern implementation details
```

### 2. Database Schema

Define additional tables, fields, and relationships:

```yaml
# Add fields to main entity
fields:
  - name: custom_status
    type: enum
    values: [pending, active, completed]
    default: pending

  - name: created_by
    type: uuid
    description: "User who created this record"

# Create related tables
tables:
  - name: "{{ entity_name }}_history"
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: entity_id
        type: uuid
        references: "{{ entity_name }}.id"
      - name: action
        type: text
      - name: old_values
        type: jsonb
      - name: new_values
        type: jsonb
      - name: changed_by
        type: uuid
      - name: changed_at
        type: timestamp
        default: NOW()
```

### 3. Business Actions

Define the actions that implement the pattern:

```yaml
actions:
  - name: perform_custom_action
    description: "Execute the custom business logic"
    parameters:
      - name: input_param
        type: text
        required: true
    steps:
      # Implementation steps using primitives
      - type: validate
        condition: "input_param IS NOT NULL"
        error_message: "Input parameter is required"

      - type: update
        table: "{{ entity_name }}"
        data:
          custom_status: "'active'"
          updated_at: "NOW()"
        where: "id = {{ entity_id }}"

      - type: insert
        table: "{{ entity_name }}_history"
        data:
          entity_id: "{{ entity_id }}"
          action: "'custom_action'"
          new_values: "jsonb_build_object('status', 'active')"
          changed_by: "{{ user_id }}"
```

## Template Variables

Patterns have access to rich context variables:

### Entity Context
- `entity_name`: The entity name (e.g., "user", "product")
- `entity_schema`: The database schema (e.g., "app", "crm")
- `entity_fields`: List of entity fields with their definitions
- `entity_actions`: List of entity actions

### Pattern Parameters
- All pattern parameters are available as top-level variables
- Use Jinja2 templating: `{{ parameter_name }}`

### Framework Context
- `framework`: Target framework ("postgresql", "django", "sqlalchemy")
- `namespace`: Entity namespace
- `table_prefix`: Table prefix convention

## Multi-Language Generation

Patterns must generate code for all supported languages:

### PostgreSQL Functions
```sql
CREATE OR REPLACE FUNCTION {{ entity_schema }}.{{ action_name }}(
    user_id uuid,
    input_data jsonb
)
RETURNS mutation_result AS $$
DECLARE
    v_entity_id uuid;
    -- Pattern variables
BEGIN
    -- Pattern implementation
    RETURN success_response();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Django Models
```python
class {{ entity_name|title }}(models.Model):
    # Pattern fields
    custom_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')],
        default='pending'
    )

    def perform_custom_action(self, input_param):
        """Execute custom business logic"""
        # Pattern implementation
        pass
```

### SQLAlchemy Models
```python
class {{ entity_name|title }}(Base):
    __tablename__ = '{{ entity_schema }}.tb_{{ entity_name }}'

    # Pattern fields
    custom_status = Column(Enum('pending', 'active', 'completed'), default='pending')

    def perform_custom_action(self, input_param):
        """Execute custom business logic"""
        # Pattern implementation
        pass
```

## Testing Patterns

### Unit Tests
Test pattern logic in isolation:

```python
def test_custom_pattern_basic():
    """Test basic pattern functionality"""
    pattern_config = {
        "entity_name": "test_entity",
        "enable_feature_x": True,
        "max_items": 5
    }

    # Test parameter validation
    assert validate_pattern_config("my_pattern", pattern_config)

    # Test SQL generation
    sql = generate_pattern_sql("my_pattern", pattern_config, "postgresql")
    assert "CREATE OR REPLACE FUNCTION" in sql
    assert "custom_status" in sql
```

### Integration Tests
Test pattern with real entities:

```python
def test_custom_pattern_integration():
    """Test pattern integrated with entity"""
    entity_yaml = """
    entity: TestEntity
    fields:
      name: text
    patterns:
      - my_custom_pattern:
          enable_feature_x: true
    """

    # Generate code
    generated = generate_schema(entity_yaml)

    # Test PostgreSQL generation
    assert "custom_status" in generated["postgresql"]
    assert "perform_custom_action" in generated["postgresql"]

    # Test Django generation
    assert "custom_status" in generated["django"]
    assert "perform_custom_action" in generated["django"]
```

### End-to-End Tests
Test complete workflows:

```python
def test_custom_pattern_e2e():
    """Test complete pattern workflow"""
    # Create test entity with pattern
    entity = create_test_entity_with_pattern("my_custom_pattern")

    # Execute pattern action
    result = execute_action(entity, "perform_custom_action", {"input_param": "test"})

    # Verify results
    assert result["success"] == True
    assert entity.custom_status == "active"

    # Check audit trail
    history = get_entity_history(entity.id)
    assert len(history) == 1
    assert history[0]["action"] == "custom_action"
```

## Pattern Categories

### Business Logic Patterns
- **State Machines**: Entity lifecycle management
- **Approval Workflows**: Multi-step approval processes
- **Audit Trails**: Change tracking and compliance
- **Validation Chains**: Complex business rule validation

### Data Management Patterns
- **Soft Delete**: Logical deletion with recovery
- **Versioning**: Data versioning and history
- **Archiving**: Data archiving strategies
- **Partitioning**: Table partitioning schemes

### Integration Patterns
- **Event Publishing**: Event-driven architecture
- **API Integration**: External service integration
- **Queue Processing**: Asynchronous processing
- **Cache Management**: Caching strategies

### Domain-Specific Patterns
- **Financial**: Accounting, invoicing, payments
- **Healthcare**: Patient management, appointments
- **E-commerce**: Orders, inventory, shipping
- **HR**: Employee management, payroll

## Advanced Pattern Features

### Conditional Logic
Use Jinja2 conditionals for flexible generation:

```yaml
fields:
{% if enable_audit %}
  - name: created_at
    type: timestamp
    default: NOW()
  - name: created_by
    type: uuid
{% endif %}

actions:
{% if enable_notifications %}
  - name: send_notification
    # Notification implementation
{% endif %}
```

### Loops and Iteration
Generate repetitive structures:

```yaml
{% for field in entity_fields %}
  - name: validate_{{ field.name }}
    type: validate
    condition: "{{ field.name }} IS NOT NULL"
    error_message: "{{ field.name }} is required"
{% endfor %}
```

### Inheritance and Composition
Build complex patterns from simpler ones:

```yaml
base_patterns: [audit_trail, soft_delete]

# Extend with custom logic
custom_implementation:
  # Additional fields and actions
```

## Pattern Registry

### Registering Patterns
Add patterns to the pattern library:

```python
from src.pattern_library.api import PatternLibrary

library = PatternLibrary("pattern_library.db")

# Register pattern
library.add_pattern(
    name="my_custom_pattern",
    category="business_logic",
    abstract_syntax={...},  # Parameter schema
    description="Custom business logic pattern"
)

# Add implementations
library.add_implementation(
    pattern_name="my_custom_pattern",
    language_name="postgresql",
    template=postgresql_template
)

library.add_implementation(
    pattern_name="my_custom_pattern",
    language_name="django",
    template=django_template
)
```

### Pattern Discovery
Make patterns discoverable:

```python
# Add metadata for discovery
library.add_pattern_metadata(
    pattern_name="my_custom_pattern",
    tags=["workflow", "validation", "custom"],
    use_cases=["Order processing", "User management"],
    complexity="intermediate",
    maintenance_cost="low"
)
```

## Best Practices

### Design Principles
1. **Single Responsibility**: Each pattern should do one thing well
2. **Configurable**: Make patterns adaptable to different use cases
3. **Composable**: Design patterns that work well together
4. **Testable**: Ensure patterns can be thoroughly tested

### Implementation Guidelines
1. **Validate Inputs**: Always validate pattern parameters
2. **Handle Errors**: Provide clear error messages
3. **Document Thoroughly**: Include examples and parameter descriptions
4. **Version Carefully**: Consider backward compatibility

### Performance Considerations
1. **Efficient SQL**: Generate optimized database queries
2. **Index Strategy**: Include appropriate indexes
3. **Connection Usage**: Minimize database connections
4. **Caching**: Consider caching for expensive operations

## Example: Complete Pattern

Here's a complete custom pattern for task management:

```yaml
# patterns/task_management.yaml
pattern: task_management
category: workflow
description: "Task lifecycle management with assignment and tracking"

parameters:
  entity_name:
    type: string
    required: true
  enable_time_tracking:
    type: boolean
    default: false
  enable_priorities:
    type: boolean
    default: true

implementation:
  fields:
    - name: status
      type: enum
      values: [open, in_progress, completed, cancelled]
      default: open

    - name: assigned_to
      type: uuid
      description: "User assigned to this task"

    - name: priority
      type: enum
      values: [low, medium, high, urgent]
      default: medium

    {% if enable_time_tracking %}
    - name: time_spent
      type: interval
      description: "Total time spent on task"
    {% endif %}

  actions:
    - name: assign_task
      parameters:
        - name: task_id
          type: uuid
        - name: user_id
          type: uuid
      steps:
        - type: update
          table: "{{ entity_name }}"
          data:
            assigned_to: "{{ user_id }}"
            status: "'in_progress'"
          where: "id = {{ task_id }}"

    - name: complete_task
      parameters:
        - name: task_id
          type: uuid
      steps:
        - type: update
          table: "{{ entity_name }}"
          data:
            status: "'completed'"
            completed_at: "NOW()"
          where: "id = {{ task_id }}"
```

## Troubleshooting

### Common Issues

**"Pattern not found"**
- Check pattern name spelling
- Verify pattern is registered in library
- Ensure correct category

**"Parameter validation failed"**
- Check parameter types and requirements
- Verify parameter names match schema
- Review default values

**"Template rendering failed"**
- Check Jinja2 syntax
- Verify variable references
- Test template with sample data

**"Generated code has errors"**
- Test SQL syntax manually
- Check for missing imports in generated code
- Validate against target framework requirements

### Debugging Patterns

Enable debug logging for pattern development:

```python
import logging
logging.getLogger('specql.patterns').setLevel(logging.DEBUG)

# This will show template rendering and parameter resolution
```

## Contributing Patterns

### Pattern Review Process
1. **Submit Pattern**: Create PR with pattern implementation
2. **Documentation**: Include comprehensive documentation
3. **Tests**: Provide complete test coverage
4. **Review**: Get feedback from pattern maintainers
5. **Approval**: Merge after review and testing

### Pattern Standards
- Follow naming conventions
- Include parameter validation
- Provide migration examples
- Document performance characteristics
- Support all target languages

## Related Documentation

- [Primitives Reference](../reference/primitives.md) - Low-level building blocks
- [Domain Patterns](../reference/domain_patterns.md) - Available patterns
- [Testing Guide](../TESTING.md) - Testing generated code
- [Contributing Guide](contributing.md) - Contribution guidelines