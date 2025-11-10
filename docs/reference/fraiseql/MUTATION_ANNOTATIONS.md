# FraiseQL Mutation Annotations

**Status**: ✅ Implemented
**Team**: Team D (FraiseQL Integration)
**Purpose**: Enable GraphQL mutations for SpecQL actions with impact metadata

---

## Overview

Mutation annotations tell FraiseQL how to expose PostgreSQL functions as GraphQL mutations. They include:

- GraphQL mutation name mapping
- Input/output type specifications
- Primary entity identification
- Impact metadata for cache invalidation

**Key Insight**: Annotations are generated automatically from SpecQL action definitions with impact metadata.

---

## How It Works

### 1. SpecQL Action Definition

```yaml
entity: Contact
schema: crm

actions:
  - name: qualify_lead
    impact:
      primary:
        entity: Contact
        operation: update
        fields: [status, qualified_at]
```

### 2. Generated PostgreSQL Function

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    auth_tenant_id UUID,
    input_data app.type_qualify_lead_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
-- Business logic here
$$;
```

### 3. FraiseQL Mutation Annotation (Auto-Generated)

```sql
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation
   name=qualifyLead
   input=QualifyLeadInput
   success_type=QualifyLeadSuccess
   error_type=QualifyLeadError
   primary_entity=Contact
   metadata_mapping={"_meta": "MutationImpactMetadata", "primary_impact": {"entity": "Contact", "operation": "update", "fields": ["status", "qualified_at"]}}';
```

### 4. GraphQL Schema (Auto-Generated)

```graphql
type Mutation {
  qualifyLead(input: QualifyLeadInput!): QualifyLeadPayload!
}

type QualifyLeadPayload {
  success: QualifyLeadSuccess
  error: QualifyLeadError
}

type QualifyLeadSuccess {
  # Success fields
}

type QualifyLeadError {
  # Error fields
}
```

---

## Annotation Structure

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | GraphQL mutation name (camelCase) | `qualifyLead` |
| `input` | GraphQL input type name | `QualifyLeadInput` |
| `success_type` | GraphQL success type name | `QualifyLeadSuccess` |
| `error_type` | GraphQL error type name | `QualifyLeadError` |
| `primary_entity` | Primary entity being mutated | `Contact` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `metadata_mapping` | JSON with impact metadata | `{"_meta": "MutationImpactMetadata", ...}` |

---

## Impact Metadata

The `metadata_mapping` field includes impact information for frontend cache invalidation:

```json
{
  "_meta": "MutationImpactMetadata",
  "primary_impact": {
    "entity": "Contact",
    "operation": "update",
    "fields": ["status", "qualified_at"]
  },
  "side_effects": [
    {
      "entity": "AuditLog",
      "operation": "create",
      "fields": ["action", "timestamp"]
    }
  ]
}
```

### Impact Structure

- **`primary_impact`**: Main entity and operation
  - `entity`: Entity name
  - `operation`: `create`, `update`, `delete`
  - `fields`: Affected field names

- **`side_effects`**: Secondary impacts (optional)
  - Array of impact objects for related entities

---

## Generation Process

### 1. Action Analysis

The `MutationAnnotator` analyzes each SpecQL action:

```python
from src.generators.fraiseql.mutation_annotator import MutationAnnotator

annotator = MutationAnnotator("crm", "Contact")
sql = annotator.generate_mutation_annotation(action)
```

### 2. Name Conversion

- PostgreSQL: `qualify_lead` (snake_case)
- GraphQL: `qualifyLead` (camelCase)
- Types: `QualifyLeadInput`, `QualifyLeadSuccess`, `QualifyLeadError` (PascalCase)

### 3. Metadata Extraction

Impact metadata is extracted from the action's `impact` field and serialized to JSON.

### 4. SQL Comment Generation

The complete annotation is formatted as a PostgreSQL `COMMENT ON FUNCTION` statement.

---

## Integration Points

### Schema Orchestrator

Mutation annotations are automatically added by the `SchemaOrchestrator`:

```python
# In src/generators/schema_orchestrator.py
if entity.actions:
    for action in entity.actions:
        annotator = MutationAnnotator(entity.schema, entity.name)
        annotation = annotator.generate_mutation_annotation(action)
        # Added to migration SQL
```

### No Manual Configuration

**Before (Manual)**:
```sql
-- Developer had to write this manually
COMMENT ON FUNCTION crm.qualify_lead IS
'@fraiseql:mutation
 name=qualifyLead
 input=QualifyLeadInput
 ...';
```

**After (Automatic)**:
```yaml
# Just write SpecQL - annotations generated automatically
actions:
  - name: qualify_lead
    impact:
      primary:
        entity: Contact
        operation: update
```

---

## Examples

### Simple Update Action

```yaml
actions:
  - name: update_profile
    impact:
      primary:
        entity: User
        operation: update
        fields: [name, email]
```

**Generated Annotation**:
```sql
COMMENT ON FUNCTION auth.update_profile IS
  '@fraiseql:mutation
   name=updateProfile
   input=UpdateProfileInput
   success_type=UpdateProfileSuccess
   error_type=UpdateProfileError
   primary_entity=User
   metadata_mapping={"_meta": "MutationImpactMetadata", "primary_impact": {"entity": "User", "operation": "update", "fields": ["name", "email"]}}';
```

### Complex Action with Side Effects

```yaml
actions:
  - name: transfer_ownership
    impact:
      primary:
        entity: Account
        operation: update
        fields: [owner_id]
      side_effects:
        - entity: User
          operation: update
          fields: [account_count]
        - entity: AuditLog
          operation: create
          fields: [action, old_owner, new_owner]
```

**Generated Annotation**:
```sql
COMMENT ON FUNCTION crm.transfer_ownership IS
  '@fraiseql:mutation
   name=transferOwnership
   input=TransferOwnershipInput
   success_type=TransferOwnershipSuccess
   error_type=TransferOwnershipError
   primary_entity=Account
   metadata_mapping={"_meta": "MutationImpactMetadata", "primary_impact": {"entity": "Account", "operation": "update", "fields": ["owner_id"]}, "side_effects": [{"entity": "User", "operation": "update", "fields": ["account_count"]}, {"entity": "AuditLog", "operation": "create", "fields": ["action", "old_owner", "new_owner"]}]}';
```

### Action Without Impact

```yaml
actions:
  - name: send_notification
    # No impact specified
```

**Generated Annotation**:
```sql
COMMENT ON FUNCTION app.send_notification IS
  '@fraiseql:mutation
   name=sendNotification
   input=SendNotificationInput
   success_type=SendNotificationSuccess
   error_type=SendNotificationError
   primary_entity=Contact
   metadata_mapping={}'';
```

---

## Benefits

### 1. Zero Configuration
- ✅ No manual `@fraiseql:mutation` annotations needed
- ✅ Automatic GraphQL type generation
- ✅ Impact metadata for cache invalidation

### 2. Type Safety
- ✅ PostgreSQL functions become GraphQL mutations
- ✅ Input validation at GraphQL layer
- ✅ Type-safe frontend integration

### 3. Cache Invalidation
- ✅ Frontend can invalidate affected queries
- ✅ Based on actual mutation impact
- ✅ Automatic cache management

### 4. Developer Experience
- ✅ GraphQL Playground shows mutations
- ✅ Auto-complete for mutation inputs
- ✅ Inline documentation from PostgreSQL comments

---

## Testing

### Unit Tests

```bash
# Test mutation annotator logic
uv run pytest tests/unit/fraiseql/test_mutation_annotator.py -v
```

### Integration Tests

```bash
# Test end-to-end annotation generation
uv run pytest tests/integration/fraiseql/test_mutation_annotations_e2e.py -v
```

### Manual Verification

```bash
# Generate schema with actions
uv run python -m src.cli.generate entities/examples/contact_with_actions.yaml

# Check generated annotations
grep "@fraiseql:mutation" generated/*.sql
```

---

## Architecture Notes

### Separation of Concerns

- **Core Functions**: Business logic (generated by Team C)
- **FraiseQL Annotations**: GraphQL integration (generated by Team D)
- **Input Types**: Parameter validation (generated by Team B)

### No Duplication

- Annotations are generated once per function
- No duplicate comments or conflicting metadata
- Single source of truth: SpecQL action definitions

### Extensibility

- Impact metadata can be extended for complex cache invalidation
- Side effects support for multi-entity operations
- Custom metadata fields can be added as needed

---

## Troubleshooting

### Missing Annotations

**Problem**: Function doesn't appear in GraphQL schema

**Check**:
1. Does the action have an `impact` field?
2. Is the function generated in the migration?
3. Are there any SQL syntax errors?

**Solution**: Add impact metadata to the action definition

### Incorrect Types

**Problem**: GraphQL types don't match expected names

**Check**:
1. Is the action name in snake_case?
2. Is the entity name correct?

**Solution**: Verify naming conventions in SpecQL

### Cache Issues

**Problem**: Frontend cache not invalidating properly

**Check**:
1. Is `metadata_mapping` present in the annotation?
2. Does it include the correct impact information?

**Solution**: Verify impact metadata in action definition

---

## Future Enhancements

### 1. Advanced Cache Invalidation
- Query-specific invalidation rules
- Dependency graph analysis
- Automatic cache key generation

### 2. Subscription Support
- Real-time updates for mutated entities
- WebSocket integration
- Live query invalidation

### 3. Authorization Integration
- Permission-based field exposure
- Row-level security mapping
- GraphQL directive generation

---

**Status**: ✅ Complete
**Implementation**: `src/generators/fraiseql/mutation_annotator.py`
**Tests**: `tests/unit/fraiseql/test_mutation_annotator.py`
**Integration**: `tests/integration/fraiseql/test_mutation_annotations_e2e.py`