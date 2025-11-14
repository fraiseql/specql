# Team C: Return Value Tracking Design

## Problem Statement

Generated PL/pgSQL functions must return all affected entities with only their ID + modified fields, enabling GraphQL clients to efficiently update caches without additional queries.

## Requirements

1. **Track All Modifications**: Capture every INSERT/UPDATE/DELETE across all action steps
2. **Field-Level Precision**: Return only fields that were actually modified, not entire records
3. **Multiple Entities**: Handle actions that affect multiple entity types
4. **Performance**: Minimal overhead on function execution
5. **GraphQL Compatible**: Return structure must map cleanly to GraphQL mutation responses

## Design Overview

### Core Pattern: RETURNING Clause + Accumulator

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
    v_affected_entities jsonb := '[]'::jsonb;  -- Accumulator
    v_step_result jsonb;
BEGIN
    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);

    -- Step 1: Validation (no modifications)
    -- ... validation logic ...

    -- Step 2: Update with RETURNING
    UPDATE crm.tb_contact
    SET
        status = 'qualified',
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk
    RETURNING jsonb_build_object(
        'entity', 'Contact',
        'id', id,
        'modified_fields', jsonb_build_object(
            'status', status,
            'updated_at', updated_at
        )
    ) INTO v_step_result;

    -- Accumulate result
    v_affected_entities := v_affected_entities || v_step_result;

    -- Step 3: Insert notification with RETURNING
    INSERT INTO core.tb_notification (fk_user, message, sent_at)
    SELECT fk_owner, 'Contact qualified', now()
    FROM crm.tb_contact WHERE pk_contact = v_pk
    RETURNING jsonb_build_object(
        'entity', 'Notification',
        'id', id,
        'modified_fields', jsonb_build_object(
            'message', message,
            'sent_at', sent_at
        )
    ) INTO v_step_result;

    -- Accumulate result
    v_affected_entities := v_affected_entities || v_step_result;

    -- Return aggregated results
    RETURN jsonb_build_object(
        'success', true,
        'affected_entities', v_affected_entities
    );
END;
$$ LANGUAGE plpgsql;
```

## Implementation Architecture

### 1. ModificationTracker Class

**Responsibility**: Track which fields are modified by each step

```python
# src/generators/actions/return_tracker/modification_tracker.py

from dataclasses import dataclass
from typing import List, Set

@dataclass
class StepModification:
    """Represents modifications made by a single action step"""
    entity_name: str          # e.g., "Contact"
    operation: str            # "insert", "update", "delete"
    modified_fields: Set[str] # Fields modified in this step
    step_index: int           # Which step in the action

class ModificationTracker:
    """Tracks all modifications across an action's steps"""

    def track_update(self, step: UpdateStep) -> StepModification:
        """Analyze an UPDATE step to determine modified fields"""
        entity = step.entity_name
        fields = set(assignment.field for assignment in step.assignments)
        # Always add audit fields
        fields.update(['updated_at', 'updated_by'])

        return StepModification(
            entity_name=entity,
            operation="update",
            modified_fields=fields,
            step_index=step.index
        )

    def track_insert(self, step: InsertStep) -> StepModification:
        """Analyze an INSERT step to determine created fields"""
        entity = step.entity_name
        fields = set(step.fields.keys())
        # Add auto-generated fields
        fields.update(['id', 'created_at', 'created_by'])

        return StepModification(
            entity_name=entity,
            operation="insert",
            modified_fields=fields,
            step_index=step.index
        )
```

### 2. ReturningClauseGenerator Class

**Responsibility**: Generate RETURNING clauses for SQL statements

```python
# src/generators/actions/return_tracker/returning_clause_gen.py

class ReturningClauseGenerator:
    """Generates RETURNING clauses for INSERT/UPDATE/DELETE statements"""

    def generate_for_update(self,
                           entity: Entity,
                           modified_fields: Set[str],
                           var_name: str) -> str:
        """
        Generate RETURNING clause for UPDATE statement

        Returns SQL like:
            RETURNING jsonb_build_object(
                'entity', 'Contact',
                'id', id,
                'modified_fields', jsonb_build_object(
                    'status', status,
                    'updated_at', updated_at
                )
            ) INTO v_step_result_1
        """
        field_pairs = [f"'{field}', {field}" for field in modified_fields]

        return f"""
    RETURNING jsonb_build_object(
        'entity', '{entity.name}',
        'id', id,
        'modified_fields', jsonb_build_object(
            {', '.join(field_pairs)}
        )
    ) INTO {var_name}"""

    def generate_for_insert(self,
                           entity: Entity,
                           created_fields: Set[str],
                           var_name: str) -> str:
        """Generate RETURNING clause for INSERT statement"""
        # Similar to update, but mark as 'insert' operation
        field_pairs = [f"'{field}', {field}" for field in created_fields]

        return f"""
    RETURNING jsonb_build_object(
        'entity', '{entity.name}',
        'id', id,
        'operation', 'insert',
        'modified_fields', jsonb_build_object(
            {', '.join(field_pairs)}
        )
    ) INTO {var_name}"""
```

### 3. ResultBuilder Class

**Responsibility**: Build final return structure with all accumulated results

```python
# src/generators/actions/return_tracker/result_builder.py

class ResultBuilder:
    """Builds the final JSONB return structure for a function"""

    def generate_declaration(self, num_steps: int) -> str:
        """Generate DECLARE section variables for tracking"""
        return f"""
    v_affected_entities jsonb := '[]'::jsonb;
    v_step_result jsonb;"""

    def generate_accumulation(self, step_index: int) -> str:
        """Generate code to accumulate a step's result"""
        return f"""
    -- Accumulate step {step_index} result
    IF v_step_result IS NOT NULL THEN
        v_affected_entities := v_affected_entities || jsonb_build_array(v_step_result);
    END IF;"""

    def generate_final_return(self, action_name: str) -> str:
        """Generate final RETURN statement"""
        return """
    -- Return aggregated results
    RETURN jsonb_build_object(
        'success', true,
        'affected_entities', v_affected_entities
    );"""
```

### 4. Enhanced ActionCompiler Integration

```python
# src/generators/actions/action_compiler.py

from .return_tracker.modification_tracker import ModificationTracker
from .return_tracker.returning_clause_gen import ReturningClauseGenerator
from .return_tracker.result_builder import ResultBuilder

class ActionCompiler:
    """Compiles SpecQL actions to PL/pgSQL functions"""

    def __init__(self):
        self.step_generators = {...}  # Existing
        self.modification_tracker = ModificationTracker()
        self.returning_gen = ReturningClauseGenerator()
        self.result_builder = ResultBuilder()

    def compile_action(self, action: Action, entities: Dict[str, Entity]) -> str:
        """Compile an action to a complete PL/pgSQL function"""

        # Track modifications across all steps
        modifications = []
        for step in action.steps:
            if isinstance(step, (UpdateStep, InsertStep)):
                mod = self.modification_tracker.track_update(step)
                modifications.append(mod)

        # Generate function signature
        signature = self._generate_signature(action)

        # Generate DECLARE section with return tracking vars
        declares = self.result_builder.generate_declaration(len(modifications))

        # Generate step SQL with RETURNING clauses
        step_sql = []
        for i, step in enumerate(action.steps):
            sql = self._generate_step_sql(step, entities)

            # Add RETURNING if this step modifies data
            if i < len(modifications):
                entity = entities[modifications[i].entity_name]
                var_name = f"v_step_result"
                returning = self.returning_gen.generate_for_update(
                    entity,
                    modifications[i].modified_fields,
                    var_name
                )
                sql += returning

                # Add accumulation
                sql += self.result_builder.generate_accumulation(i)

            step_sql.append(sql)

        # Generate final return
        return_sql = self.result_builder.generate_final_return(action.name)

        # Assemble complete function
        return self._assemble_function(signature, declares, step_sql, return_sql)
```

## Example Output

### Input SpecQL
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - insert: Notification(user=Contact.owner, message='Lead qualified')
```

### Generated Function
```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
    v_status TEXT;
    v_affected_entities jsonb := '[]'::jsonb;
    v_step_result jsonb;
BEGIN
    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);

    -- Step 1: Validation (no RETURNING needed)
    SELECT status INTO v_status
    FROM crm.tb_contact
    WHERE pk_contact = v_pk;

    IF v_status != 'lead' THEN
        RAISE EXCEPTION 'validation_failed: Contact is not a lead';
    END IF;

    -- Step 2: Update with RETURNING
    UPDATE crm.tb_contact
    SET
        status = 'qualified',
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk
    RETURNING jsonb_build_object(
        'entity', 'Contact',
        'id', id,
        'modified_fields', jsonb_build_object(
            'status', status,
            'updated_at', updated_at
        )
    ) INTO v_step_result;

    -- Accumulate result
    IF v_step_result IS NOT NULL THEN
        v_affected_entities := v_affected_entities || jsonb_build_array(v_step_result);
    END IF;

    -- Step 3: Insert notification with RETURNING
    INSERT INTO core.tb_notification (fk_user, message, created_at)
    SELECT fk_owner, 'Lead qualified', now()
    FROM crm.tb_contact
    WHERE pk_contact = v_pk
    RETURNING jsonb_build_object(
        'entity', 'Notification',
        'id', id,
        'operation', 'insert',
        'modified_fields', jsonb_build_object(
            'id', id,
            'message', message,
            'created_at', created_at
        )
    ) INTO v_step_result;

    -- Accumulate result
    IF v_step_result IS NOT NULL THEN
        v_affected_entities := v_affected_entities || jsonb_build_array(v_step_result);
    END IF;

    -- Event emission
    PERFORM core.emit_event('contact.qualified', jsonb_build_object('id', p_contact_id));

    -- Return aggregated results
    RETURN jsonb_build_object(
        'success', true,
        'affected_entities', v_affected_entities
    );
END;
$$ LANGUAGE plpgsql;
```

### Example Return Value
```json
{
  "success": true,
  "affected_entities": [
    {
      "entity": "Contact",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "modified_fields": {
        "status": "qualified",
        "updated_at": "2025-11-08T10:30:15.123Z"
      }
    },
    {
      "entity": "Notification",
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "operation": "insert",
      "modified_fields": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "message": "Lead qualified",
        "created_at": "2025-11-08T10:30:15.123Z"
      }
    }
  ]
}
```

## Benefits for GraphQL/FraiseQL

This return structure maps perfectly to GraphQL mutation responses:

```graphql
mutation QualifyLead($contactId: UUID!) {
  qualifyLead(contactId: $contactId) {
    success
    affectedEntities {
      entity
      id
      modifiedFields
    }
  }
}
```

FraiseQL can automatically:
1. Update Apollo/Relay cache with returned entity data
2. Invalidate queries that depend on modified entities
3. Provide optimistic UI updates with actual field values
4. Avoid additional roundtrips to fetch updated data

## Testing Strategy

### Unit Tests
```python
# tests/unit/actions/return_tracker/test_modification_tracker.py

def test_track_update_identifies_modified_fields():
    step = UpdateStep(
        entity_name='Contact',
        assignments=[
            Assignment(field='status', value='qualified'),
            Assignment(field='notes', value='Updated by action')
        ]
    )

    tracker = ModificationTracker()
    mod = tracker.track_update(step)

    assert mod.entity_name == 'Contact'
    assert mod.operation == 'update'
    assert 'status' in mod.modified_fields
    assert 'notes' in mod.modified_fields
    assert 'updated_at' in mod.modified_fields  # Auto-added
    assert 'updated_by' in mod.modified_fields  # Auto-added
```

### Integration Tests
```python
# tests/integration/test_action_return_values.py

def test_action_returns_all_affected_entities(db_connection):
    """Test that generated function returns all modifications"""

    # Setup: Create test contact
    contact_id = create_test_contact(db_connection, status='lead')

    # Execute: Run generated function
    result = db_connection.execute(
        "SELECT crm.qualify_lead(%s)",
        [contact_id]
    ).fetchone()[0]

    # Assert: Check return structure
    assert result['success'] is True
    assert len(result['affected_entities']) == 2  # Contact + Notification

    contact_update = result['affected_entities'][0]
    assert contact_update['entity'] == 'Contact'
    assert contact_update['id'] == str(contact_id)
    assert 'status' in contact_update['modified_fields']
    assert contact_update['modified_fields']['status'] == 'qualified'

    notification = result['affected_entities'][1]
    assert notification['entity'] == 'Notification'
    assert notification['operation'] == 'insert'
```

## Performance Considerations

1. **RETURNING Clause Overhead**: Minimal - PostgreSQL optimizes RETURNING clauses efficiently
2. **JSONB Construction**: Modern PostgreSQL (12+) has highly optimized JSONB operations
3. **Array Accumulation**: `||` operator is efficient for small arrays (typical: 1-5 entities per action)
4. **No Additional Queries**: All data collected during modifications, no extra SELECTs

**Benchmark Target**: < 5ms overhead for return value construction (compared to function without RETURNING)

## Future Enhancements

1. **Delta Tracking**: Return old vs new values for updates
   ```json
   {
     "modified_fields": {
       "status": {"old": "lead", "new": "qualified"}
     }
   }
   ```

2. **Conditional Returns**: Only return entities if requested (function parameter)
   ```sql
   CREATE FUNCTION qualify_lead(p_contact_id UUID, p_return_entities BOOLEAN DEFAULT true)
   ```

3. **Related Entity Loading**: Optionally include related data
   ```json
   {
     "entity": "Contact",
     "id": "...",
     "modified_fields": {...},
     "related": {
       "company": {"id": "...", "name": "Acme Corp"}
     }
   }
   ```

## Team C Responsibilities (Updated)

### Core Compilation (Existing)
- Parse action steps
- Generate PL/pgSQL control flow
- Handle validations, conditionals, loops

### Return Value Tracking (New)
- Track modifications per step
- Generate RETURNING clauses
- Accumulate results across steps
- Build final return structure

### Integration Points
- Coordinate with Team D (FraiseQL metadata must match return structure)
- Work with Team E (CLI should validate return value format)

---

**Status**: Design Complete - Ready for Implementation (Week 3)
**Complexity**: Medium-High
**Implementation Time**: 2-3 days within Team C's Week 3 sprint
**Testing Time**: 1-2 days
**Dependencies**: Team A AST (completed)
