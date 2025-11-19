# FraiseQL Comment Implementation in SpecQL

This documents how SpecQL generates PostgreSQL comments compatible with FraiseQL's YAML format.

## Format Overview

All comments follow this structure:

```
[Human-readable description]

@fraiseql:[type]
[YAML configuration]
```

## Implementation

### Composite Types

Generator: `CompositeTypeGenerator`
Template: `templates/sql/composite_type_comments.sql.j2`

Example output:
```sql
COMMENT ON TYPE app.type_simple_address IS
'Simple postal address without validation.

@fraiseql:composite
name: SimpleAddress
tier: 2
storage: jsonb';
```

### Fields

Generator: `CompositeTypeGenerator`
Template: `templates/sql/field_comments.sql.j2`

Example output:
```sql
COMMENT ON COLUMN app.type_simple_address.street IS
'Street address line 1 (required).

@fraiseql:field
name: street
type: String!
required: true';
```

### Functions

Generator: `AppWrapperGenerator` + `MutationAnnotator`
Template: Generated programmatically

Example output:
```sql
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';
```

### Tables

Generator: `TableGenerator`
Template: Generated programmatically

Example output:
```sql
COMMENT ON TABLE crm.tb_contact IS
'Customer contact information.

@fraiseql:type
trinity: true';
```

### Columns

Generator: `TableGenerator`
Template: Generated programmatically

Example output:
```sql
COMMENT ON COLUMN crm.tb_contact.email IS
'Email address (validated format).

@fraiseql:field
name: email
type: Email!
required: true';
```

## Migration from Old Format

### Before (Old Format)
```sql
COMMENT ON TYPE app.mutation_result IS
  '@fraiseql:type name=MutationResult';
```

### After (YAML Format)
```sql
COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';
```

## Key Changes

1. **Multi-line format**: Description text before metadata
2. **YAML structure**: Proper YAML syntax instead of single-line
3. **Annotation names**: `@fraiseql:composite` instead of `@fraiseql:type`
4. **Field format**: Multi-line YAML instead of `name=x,type=Y`
5. **Required descriptions**: All comments must include human-readable text

## Implementation Timeline

- **Day 1**: Composite type comments migrated
- **Day 2**: Function comments migrated
- **Day 3**: Table and column comments migrated
- **Day 4**: Integration testing and documentation

## Testing

Integration test: `tests/integration/test_fraiseql_yaml_format.py`
- Tests complete SpecQL → SQL pipeline
- Verifies all comment formats are YAML-compatible
- Ensures no old format remains

## Validation Checklist

Before shipping, verify all comments match FraiseQL format:

### ✅ Composite Types
```sql
COMMENT ON TYPE schema.type_name IS
'[Description]

@fraiseql:composite
name: GraphQLName
tier: 1|2|3';
```

### ✅ Composite Fields
```sql
COMMENT ON COLUMN schema.type_name.field IS
'[Description]

@fraiseql:field
name: fieldName
type: GraphQLType
required: true|false';
```

### ✅ Functions
```sql
COMMENT ON FUNCTION schema.func IS
'[Description]

@fraiseql:mutation
name: mutationName
input_type: schema.type_input
success_type: SuccessType
failure_type: FailureType';
```

### ✅ Tables
```sql
COMMENT ON TABLE schema.tb_entity IS
'[Description]

@fraiseql:type
trinity: true';
```

### ✅ Columns
```sql
COMMENT ON COLUMN schema.tb_entity.field IS
'[Description]

@fraiseql:field
name: fieldName
type: GraphQLType
required: true|false';
```