# Team C Generators API Reference

This document provides technical details for the Team C action compilation system.

## Core Classes

### CoreLogicGenerator

Generates core layer business logic functions.

#### Methods

##### `generate_core_create_function(entity: Entity) -> str`

Generates a core CREATE function.

**Parameters:**
- `entity`: Entity definition with fields and actions

**Returns:** SQL string for the core create function

**Example:**
```python
generator = CoreLogicGenerator()
sql = generator.generate_core_create_function(contact_entity)
# Returns: CREATE OR REPLACE FUNCTION crm.create_contact(...) ...
```

##### `generate_core_update_function(entity: Entity) -> str`

Generates a core UPDATE function.

**Parameters:**
- `entity`: Entity definition

**Returns:** SQL string for the core update function

##### `generate_core_delete_function(entity: Entity) -> str`

Generates a core soft DELETE function.

**Parameters:**
- `entity`: Entity definition

**Returns:** SQL string for the core delete function

##### `generate_core_custom_action(entity: Entity, action) -> str`

Generates a core custom business action function.

**Parameters:**
- `entity`: Entity definition
- `action`: Action definition with steps

**Returns:** SQL string for the custom action function

##### `detect_action_pattern(action_name: str) -> str`

Detects the action pattern from the name.

**Parameters:**
- `action_name`: Name of the action

**Returns:** One of: 'create', 'update', 'delete', 'custom'

**Examples:**
```python
detect_action_pattern("create_contact")  # → "create"
detect_action_pattern("qualify_lead")    # → "custom"
```

## AppWrapperGenerator

Generates app layer wrapper functions that handle JSONB input/output.

#### Methods

##### `generate_app_wrapper_for_create(entity: Entity) -> str`

Generates app wrapper for CREATE actions.

**Parameters:**
- `entity`: Entity definition

**Returns:** SQL string for app.create_* function

##### `generate_app_wrapper_for_update(entity: Entity) -> str`

Generates app wrapper for UPDATE actions.

**Parameters:**
- `entity`: Entity definition

**Returns:** SQL string for app.update_* function

##### `generate_app_wrapper_for_delete(entity: Entity) -> str`

Generates app wrapper for DELETE actions.

**Parameters:**
- `entity`: Entity definition

**Returns:** SQL string for app.delete_* function

##### `generate_app_wrapper_for_custom_action(entity: Entity, action) -> str`

Generates app wrapper for custom actions.

**Parameters:**
- `entity`: Entity definition
- `action`: Action definition

**Returns:** SQL string for app.custom_action function

## ActionValidator

Validates action definitions and provides warnings.

#### Methods

##### `validate_action(action, entity) -> List[str]`

Validates an action definition.

**Parameters:**
- `action`: Action to validate
- `entity`: Entity context

**Returns:** List of validation error messages

##### `validate_entity_actions(entity) -> Dict[str, List[str]]`

Validates all actions for an entity.

**Parameters:**
- `entity`: Entity with actions

**Returns:** Dict mapping action names to error lists

## ActionOrchestrator

Coordinates complex actions involving multiple entities.

#### Methods

##### `compile_multi_entity_action(action, primary_entity, related_entities) -> str`

Compiles actions that affect multiple entities.

**Parameters:**
- `action`: Multi-entity action definition
- `primary_entity`: Main entity being acted upon
- `related_entities`: Related entities involved

**Returns:** Complete PL/pgSQL function with transaction management

## Step Compilers

Individual compilers for each step type.

### ValidateStepCompiler

Compiles validation steps.

#### `compile(step, entity, context) -> str`

**Parameters:**
- `step`: Validation step with expression and error
- `entity`: Entity context
- `context`: Compilation context

**Returns:** PL/pgSQL validation code

### InsertStepCompiler

Compiles insert operations.

#### `compile(step, entity, context) -> str`

**Returns:** INSERT statement with Trinity pattern

### UpdateStepCompiler

Compiles update operations.

#### `compile(step, entity, context) -> str`

**Returns:** UPDATE statement with audit fields

### DeleteStepCompiler

Compiles soft delete operations.

#### `compile(step, entity, context) -> str`

**Returns:** UPDATE statement setting deleted_at/deleted_by

### IfStepCompiler

Compiles conditional logic.

#### `compile(step, entity, context) -> str`

**Returns:** IF/THEN/ELSE PL/pgSQL block

### ForEachStepCompiler

Compiles iteration over collections.

#### `compile(step, entity, context) -> str`

**Returns:** FOR loop over collection

### CallStepCompiler

Compiles function calls.

#### `compile(step, entity, context) -> str`

**Returns:** PERFORM or SELECT statement

### NotifyStepCompiler

Compiles notification emissions.

#### `compile(step, entity, context) -> str`

**Returns:** Event emission code

## Support Classes

### ExpressionCompiler

Compiles SpecQL expressions to SQL.

#### `compile_expression(expr: str, entity) -> str`

**Parameters:**
- `expr`: SpecQL expression (e.g., "email MATCHES email_pattern")
- `entity`: Entity for field resolution

**Returns:** SQL WHERE clause fragment

### TrinityResolver

Handles UUID → INTEGER foreign key resolution.

#### `generate_trinity_helpers(entity) -> str`

**Returns:** Helper functions for FK resolution

#### `resolve_foreign_keys(entity) -> List[Dict]`

**Returns:** FK resolution metadata

### ImpactMetadataCompiler

Generates FraiseQL mutation impact metadata.

#### `compile_impact_metadata(action, entity) -> Dict`

**Returns:** Metadata for GraphQL schema generation

### CompositeTypeBuilder

Creates PostgreSQL composite types.

#### `build_input_type(action, entity) -> str`

**Returns:** CREATE TYPE statement for input

#### `build_result_type() -> str`

**Returns:** Standard mutation_result type

## FunctionGenerator

High-level generator that orchestrates the complete function generation.

#### Methods

##### `generate_action_functions(entity) -> str`

Generates all functions for an entity's actions.

**Parameters:**
- `entity`: Entity with actions

**Returns:** Complete SQL with all functions

##### `generate_migration_file(entity, output_path) -> str`

Generates a complete migration file.

**Parameters:**
- `entity`: Entity to generate for
- `output_path`: Where to write the file

**Returns:** Path to generated migration file

## Error Handling

### Error Codes

Standardized error codes used throughout:

- `validation:required_field` - Missing required field
- `validation:invalid_enum` - Invalid enum value
- `validation:reference_not_found` - FK not found
- `constraint:unique_violation` - Unique constraint violation
- `security:tenant_isolation` - Tenant access violation

### Structured Errors

All errors return consistent format:

```sql
RETURN app.log_and_return_mutation(
    auth_tenant_id, auth_user_id,
    'entity_name', entity_id,
    'operation', 'failed:error_code',
    ARRAY['field'], 'Error message',
    NULL, jsonb_build_object(
        'code', 'error_code',
        'user_action', 'What user should do',
        'field', 'field_name',
        'entity', 'EntityName'
    )
);
```

## Templates

### Core Function Templates

Located in `templates/sql/`:

- `core_create_function.sql.j2` - CREATE pattern
- `core_update_function.sql.j2` - UPDATE pattern
- `core_delete_function.sql.j2` - DELETE pattern
- `core_custom_action.sql.j2` - Custom actions

### App Wrapper Templates

- `app_wrapper.sql.j2` - JSONB → composite type conversion

## Dependencies

### Required Components

- **Team B**: Schema foundation, Trinity helpers
- **Team A**: Scalar types and validation
- **Team D**: FraiseQL integration (optional)

### Generated Dependencies

Functions reference:

- `app.log_and_return_mutation()` - Audit logging
- `app.mutation_result` - Return type
- `schema.entity_pk(uuid, tenant)` - Trinity helpers
- `app.type_*_input` - Composite types

## Testing

### Unit Tests

Located in `tests/unit/generators/`:

- `test_core_logic_generator.py` - Core function generation
- `test_app_wrapper_generator.py` - App wrapper generation
- `test_function_generator.py` - Integration tests

### Integration Tests

Located in `tests/integration/actions/`:

- `test_full_action_compilation.py` - End-to-end compilation
- `test_database_roundtrip.py` - Database execution tests

### Test Fixtures

- `tests/fixtures/mock_entities.py` - Test entity definitions
- `tests/conftest.py` - Shared test configuration

## Configuration

### Template Directories

```python
generator = CoreLogicGenerator(templates_dir="custom/templates")
```

### Output Customization

Override templates by placing custom versions in the templates directory.

### Debug Mode

Enable verbose SQL comments:

```python
# Set in environment or config
DEBUG_MODE = True
```

## Performance Considerations

### Compilation Speed

- Templates cached after first load
- Expression compilation optimized
- Minimal object creation

### Generated SQL Performance

- Parameterized queries prevent SQL injection
- Trinity pattern optimizes FK lookups
- Automatic indexes on audit fields
- Tenant filtering prevents table scans

### Memory Usage

- Templates loaded once per generator instance
- AST models are lightweight
- No external dependencies for generation

## Extension Points

### Adding Step Types

1. Create step compiler class
2. Implement `compile(step, entity, context)` method
3. Register in ActionOrchestrator step registry
4. Add template if needed
5. Write tests

### Custom Validation

Override `ActionValidator` methods for custom rules.

### Template Customization

Modify Jinja2 templates in `templates/sql/` directory.

## Troubleshooting

### Common Issues

1. **Template not found**: Check templates directory path
2. **Type errors**: Verify Entity and Action definitions
3. **SQL syntax errors**: Check generated SQL manually
4. **Missing dependencies**: Ensure Team B components generated first

### Debug Output

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

generator = CoreLogicGenerator()
sql = generator.generate_core_create_function(entity)
print(sql)  # Inspect generated SQL
```

### Validation

```python
validator = ActionValidator()
errors = validator.validate_entity_actions(entity)
for action_name, action_errors in errors.items():
    print(f"{action_name}: {action_errors}")
```
