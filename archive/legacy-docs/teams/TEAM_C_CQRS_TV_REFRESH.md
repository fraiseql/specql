# Team C: CQRS tv_ Refresh Integration

**Team**: Action Compiler (Business Logic → PL/pgSQL)
**Impact**: MEDIUM (tv_ refresh integration in mutations)
**Timeline**: Week 6-7 (3-4 days)
**Status**: 🟡 MEDIUM PRIORITY - CQRS Write-Side Integration

---

## 📋 Overview

Team C must integrate **tv_ refresh calls** into generated PL/pgSQL mutation functions. Every write operation (INSERT, UPDATE, DELETE) must refresh the corresponding tv_ table(s).

**Key Principle**: Write to `tb_` (normalized) → Explicit refresh of `tv_` (denormalized)

---

## 🎯 Objectives

1. ✅ Compile `refresh_table_view` action step
2. ✅ Generate `PERFORM refresh_tv_{entity}()` calls in mutations
3. ✅ Handle refresh scopes (self, related, propagate, batch)
4. ✅ Return `tv_.data` in mutation results (not `tb_` fields)
5. ✅ Cascading refresh for calculated fields

---

## 🔄 Mutation Flow with tv_ Refresh

### **Standard Pattern**

```
User GraphQL Mutation
    ↓
PL/pgSQL Function
    ↓
1. Write to tb_{entity} (normalized)
    ↓
2. PERFORM refresh_tv_{entity}(pk)  ← NEW!
    ↓
3. PERFORM refresh_tv_{related}()  ← Propagate if needed
    ↓
4. Return tv_{entity}.data (denormalized) ← NEW!
```

---

## 📊 Implementation by Day

### **Day 1: SpecQL Action Step Extension**

#### **Extend SpecQL Syntax**

```yaml
entity: Review

actions:
  - name: update_rating
    steps:
      - validate: rating >= 1 AND rating <= 5
      - update: Review SET rating = $new_rating

      # NEW: Explicit tv_ refresh step
      - refresh_table_view:
          scope: self              # self | related | propagate | batch
          propagate: [author]      # Optional: specific entities to refresh
```

---

#### **AST Model Extension**

**File**: `src/core/ast_models.py`

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class RefreshScope(Enum):
    """Scope for table view refresh."""
    SELF = "self"          # Only this entity
    RELATED = "related"    # This entity + all that reference it
    PROPAGATE = "propagate"  # This entity + explicit list
    BATCH = "batch"        # Deferred refresh (bulk operations)

@dataclass
class RefreshTableViewStep:
    """Action step for refreshing table views."""
    scope: RefreshScope = RefreshScope.SELF
    propagate: List[str] = None  # Entity names to refresh
    strategy: str = "immediate"  # immediate | deferred

# Add to ActionStep union type
ActionStep = Union[
    ValidateStep,
    InsertStep,
    UpdateStep,
    DeleteStep,
    RefreshTableViewStep,  # NEW!
    # ... other steps
]
```

---

### **Day 2: Compile refresh_table_view Step**

#### **File**: `src/generators/actions/step_compiler.py`

```python
from src.core.ast_models import RefreshTableViewStep, RefreshScope, EntityAST

class StepCompiler:
    """Compile action steps to PL/pgSQL."""

    def compile_refresh_table_view(
        self,
        step: RefreshTableViewStep,
        entity: EntityAST,
        context: dict
    ) -> str:
        """Compile refresh_table_view step."""

        entity_lower = entity.name.lower()
        pk_var = f"v_pk_{entity_lower}"

        if step.scope == RefreshScope.SELF:
            # Refresh only this entity's tv_ row
            return f"""
    -- Refresh table view (self)
    PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});
""".strip()

        elif step.scope == RefreshScope.PROPAGATE:
            # Refresh this entity + specific related entities
            lines = [
                f"-- Refresh table view (self + propagate)",
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});"
            ]

            # Refresh specified related entities
            if step.propagate:
                for rel_entity in step.propagate:
                    rel_lower = rel_entity.lower()

                    # Get FK for this relation
                    fk_var = self._get_fk_var_for_entity(entity, rel_entity, context)

                    if fk_var:
                        rel_schema = self._get_entity_schema(rel_entity)
                        lines.append(
                            f"PERFORM {rel_schema}.refresh_tv_{rel_lower}({fk_var});"
                        )

            return "\n    ".join(lines)

        elif step.scope == RefreshScope.RELATED:
            # Refresh this entity + all entities that reference it
            lines = [
                f"-- Refresh table view (self + all related)",
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});"
            ]

            # Find all entities that reference this one
            for rel_entity in self._find_dependent_entities(entity):
                rel_lower = rel_entity.name.lower()
                rel_schema = rel_entity.schema

                # Refresh all rows that reference this entity
                lines.append(
                    f"-- Refresh {rel_entity.name} entities that reference this {entity.name}"
                )
                lines.append(
                    f"PERFORM {rel_schema}.refresh_tv_{rel_lower}_by_{entity_lower}({pk_var});"
                )

            return "\n    ".join(lines)

        elif step.scope == RefreshScope.BATCH:
            # Deferred refresh (collect PKs, refresh at end)
            return f"""
    -- Queue for batch refresh (deferred)
    INSERT INTO pg_temp.tv_refresh_queue VALUES ('{entity.name}', {pk_var});
""".strip()

    def _get_fk_var_for_entity(
        self,
        entity: EntityAST,
        ref_entity_name: str,
        context: dict
    ) -> Optional[str]:
        """Get FK variable name for referenced entity."""

        # Find field that references this entity
        for field in entity.fields:
            if field.field_type == f"ref({ref_entity_name})":
                return f"v_fk_{field.name.lower()}"

        return None

    def _find_dependent_entities(self, entity: EntityAST) -> List[EntityAST]:
        """Find entities that have foreign keys to this entity."""
        # This would need access to all entities
        # Implementation depends on global entity registry
        pass
```

---

### **Day 3: Return tv_.data in Mutations**

#### **Update Mutation Result Builder**

**File**: `src/generators/actions/mutation_result.py`

```python
def build_mutation_result(
    entity: EntityAST,
    pk_var: str,
    use_table_view: bool = True
) -> str:
    """Build mutation_result return value."""

    entity_lower = entity.name.lower()
    schema = entity.schema

    if use_table_view and entity.should_generate_table_view:
        # Return from tv_ (denormalized data)
        return f"""
    -- Build result from table view (denormalized)
    v_result.status := 'success';
    v_result.message := '{entity.name} operation completed';
    v_result.object_data := (
        SELECT data  -- JSONB from tv_
        FROM {schema}.tv_{entity_lower}
        WHERE pk_{entity_lower} = {pk_var}
    );

    RETURN v_result;
"""
    else:
        # Return from tb_ (normalized, fallback)
        return f"""
    -- Build result from base table (normalized)
    v_result.status := 'success';
    v_result.message := '{entity.name} operation completed';
    v_result.object_data := (
        SELECT jsonb_build_object(
            'id', id,
            {self._build_object_fields(entity)}
        )
        FROM {schema}.tb_{entity_lower}
        WHERE pk_{entity_lower} = {pk_var}
    );

    RETURN v_result;
"""

    def _build_object_fields(self, entity: EntityAST) -> str:
        """Build field list for jsonb_build_object."""
        fields = []
        for field in entity.fields:
            if not field.field_type.startswith('ref('):
                fields.append(f"'{field.name}', {field.name}")
        return ",\n            ".join(fields)
```

---

### **Day 3-4: Generate Complete Mutation Functions**

#### **Example: update_rating Mutation**

**Input SpecQL**:
```yaml
entity: Review
schema: library

fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)

actions:
  - name: update_rating
    steps:
      - validate: rating >= 1 AND rating <= 5
      - update: Review SET rating = $new_rating
      - refresh_table_view:
          scope: self
          propagate: [author]  # Recalculate author's average_rating
```

**Generated PL/pgSQL**:
```sql
CREATE OR REPLACE FUNCTION library.update_review_rating(
    p_review_id UUID,
    p_new_rating INTEGER,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_pk_review INTEGER;
    v_fk_author INTEGER;
    v_old_rating INTEGER;
    v_result mutation_result;
BEGIN
    -- Resolve UUID → INTEGER
    v_pk_review := library.review_pk(p_review_id);

    -- Get FK for propagation
    SELECT fk_author, rating INTO v_fk_author, v_old_rating
    FROM library.tb_review
    WHERE pk_review = v_pk_review;

    -- Validation
    IF p_new_rating < 1 OR p_new_rating > 5 THEN
        v_result.status := 'error';
        v_result.message := 'Rating must be between 1 and 5';
        RETURN v_result;
    END IF;

    -- Update tb_review (normalized)
    UPDATE library.tb_review
    SET rating = p_new_rating,
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_review = v_pk_review;

    -- Refresh tv_review (self) ✅
    PERFORM library.refresh_tv_review(v_pk_review);

    -- Propagate to author (recalculate average_rating) ✅
    IF v_old_rating IS DISTINCT FROM p_new_rating THEN
        -- Only refresh if rating actually changed
        PERFORM crm.refresh_tv_user(v_fk_author);
    END IF;

    -- Build result from tv_review.data ✅
    v_result.status := 'success';
    v_result.message := 'Review rating updated';
    v_result.object_data := (
        SELECT data  -- Denormalized JSONB
        FROM library.tv_review
        WHERE pk_review = v_pk_review
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### **Example: create_review Mutation**

**Input SpecQL**:
```yaml
actions:
  - name: create_review
    steps:
      - validate: rating >= 1 AND rating <= 5
      - insert: Review(rating=$rating, comment=$comment, fk_author=$author_id, fk_book=$book_id)
      - refresh_table_view:
          scope: self
          propagate: [author, book]
```

**Generated PL/pgSQL**:
```sql
CREATE OR REPLACE FUNCTION library.create_review(
    p_rating INTEGER,
    p_comment TEXT,
    p_author_id UUID,
    p_book_id UUID,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_pk_review INTEGER;
    v_fk_author INTEGER;
    v_fk_book INTEGER;
    v_result mutation_result;
BEGIN
    -- Resolve UUIDs
    v_fk_author := crm.user_pk(p_author_id);
    v_fk_book := library.book_pk(p_book_id);

    -- Validation
    IF p_rating < 1 OR p_rating > 5 THEN
        v_result.status := 'error';
        v_result.message := 'Rating must be between 1 and 5';
        RETURN v_result;
    END IF;

    -- Insert into tb_review (normalized)
    INSERT INTO library.tb_review (
        rating, comment, fk_author, fk_book,
        created_at, created_by
    ) VALUES (
        p_rating, p_comment, v_fk_author, v_fk_book,
        now(), p_caller_id
    ) RETURNING pk_review INTO v_pk_review;

    -- Refresh tv_review (self) ✅
    PERFORM library.refresh_tv_review(v_pk_review);

    -- Propagate to author (increment review_count) ✅
    PERFORM crm.refresh_tv_user(v_fk_author);

    -- Propagate to book (increment review_count) ✅
    PERFORM library.refresh_tv_book(v_fk_book);

    -- Build result from tv_review.data ✅
    v_result.status := 'success';
    v_result.message := 'Review created successfully';
    v_result.object_data := (
        SELECT data
        FROM library.tv_review
        WHERE pk_review = v_pk_review
    );

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

### **Example: delete_review Mutation**

```sql
CREATE OR REPLACE FUNCTION library.delete_review(
    p_review_id UUID,
    p_caller_id UUID DEFAULT NULL
) RETURNS mutation_result AS $$
DECLARE
    v_pk_review INTEGER;
    v_fk_author INTEGER;
    v_fk_book INTEGER;
    v_result mutation_result;
BEGIN
    v_pk_review := library.review_pk(p_review_id);

    -- Get FKs before soft delete
    SELECT fk_author, fk_book INTO v_fk_author, v_fk_book
    FROM library.tb_review
    WHERE pk_review = v_pk_review;

    -- Soft delete in tb_review
    UPDATE library.tb_review
    SET deleted_at = now(),
        deleted_by = p_caller_id
    WHERE pk_review = v_pk_review;

    -- Remove from tv_review (soft-deleted rows not in tv_) ✅
    DELETE FROM library.tv_review WHERE pk_review = v_pk_review;

    -- Propagate to author/book (decrement counts) ✅
    PERFORM crm.refresh_tv_user(v_fk_author);
    PERFORM library.refresh_tv_book(v_fk_book);

    v_result.status := 'success';
    v_result.message := 'Review deleted';
    v_result.object_data := jsonb_build_object('id', p_review_id);

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

---

## 📋 Template Files

### **File**: `templates/actions/refresh_table_view.sql.jinja2`

```jinja2
{# Template for refresh_table_view step #}

{% if step.scope == 'self' %}
-- Refresh table view (self)
PERFORM {{ entity.schema }}.refresh_tv_{{ entity.name|lower }}(v_pk_{{ entity.name|lower }});

{% elif step.scope == 'propagate' %}
-- Refresh table view (self + propagate)
PERFORM {{ entity.schema }}.refresh_tv_{{ entity.name|lower }}(v_pk_{{ entity.name|lower }});

{% for rel_entity in step.propagate %}
{%- set fk_var = 'v_fk_' + rel_entity|lower -%}
PERFORM {{ get_entity_schema(rel_entity) }}.refresh_tv_{{ rel_entity|lower }}({{ fk_var }});
{% endfor %}

{% elif step.scope == 'related' %}
-- Refresh table view (self + all related)
PERFORM {{ entity.schema }}.refresh_tv_{{ entity.name|lower }}(v_pk_{{ entity.name|lower }});

{% for rel_entity in dependent_entities %}
PERFORM {{ rel_entity.schema }}.refresh_tv_{{ rel_entity.name|lower }}_by_{{ entity.name|lower }}(v_pk_{{ entity.name|lower }});
{% endfor %}

{% elif step.scope == 'batch' %}
-- Queue for batch refresh
INSERT INTO pg_temp.tv_refresh_queue VALUES ('{{ entity.name }}', v_pk_{{ entity.name|lower }});

{% endif %}
```

---

## ✅ Acceptance Criteria

- [ ] `refresh_table_view` step compiles to PERFORM calls
- [ ] Scope: self works (refresh only this entity)
- [ ] Scope: propagate works (refresh specific entities)
- [ ] Scope: related works (refresh all dependents)
- [ ] Mutation results return tv_.data (not tb_ fields)
- [ ] Soft deletes remove from tv_ tables
- [ ] Cascading refresh works for calculated fields
- [ ] All mutation tests pass

---

## 📊 Summary

**Files to Modify**:
- `src/core/ast_models.py` - Add RefreshTableViewStep
- `src/core/specql_parser.py` - Parse refresh_table_view step
- `src/generators/actions/step_compiler.py` - Compile refresh step
- `src/generators/actions/mutation_result.py` - Return tv_.data

**New Templates**:
- `templates/actions/refresh_table_view.sql.jinja2`

**Tests**:
- `tests/unit/actions/test_refresh_table_view_compilation.py`
- `tests/integration/test_mutations_with_tv_refresh.py`

**Total**: ~800 lines

**Timeline**: 3-4 days

---

## 🔗 Dependencies

**Depends On**:
- Team A Phase 2 (table_views parsing)
- Team B Phase 9 (tv_ generation + refresh functions)

**Blocks**:
- Full CQRS integration
- FraiseQL end-to-end testing

---

**Status**: 🟡 READY TO START (after Team B Phase 9)
**Priority**: MEDIUM (completes write-side CQRS)
**Effort**: 3-4 days
**Start**: Week 6-7
