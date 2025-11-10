# Team D: Database Decisions Implementation Plan

**Team**: FraiseQL Metadata Generator
**Impact**: LOW (metadata annotations only)
**Timeline**: Week 5 (2-3 days)
**Status**: 🟢 LOW PRIORITY - Metadata layer

---

## 📋 Overview

Team D has **minimal impact** from database decisions. The changes are mostly **additive metadata annotations**.

**Changes**:
1. ✅ Annotate deduplication fields (identifier, sequence_number, display_identifier)
2. ✅ Annotate recalculation audit fields
3. ✅ Annotate node+info split views
4. ✅ Document INTEGER-based path format

**Total Effort**: 2-3 days

---

## 🎯 Phase 1: Deduplication Field Annotations (Day 1)

### **Objective**: Add FraiseQL metadata for 3-field deduplication

### **1.1: Field Annotations**

**File**: `src/generators/fraiseql/field_annotations.py`

```python
def generate_deduplication_annotations(entity: EntityAST, schema: str) -> str:
    """Generate FraiseQL annotations for deduplication fields."""

    entity_name = entity.name
    entity_lower = entity.name.lower()
    table_name = f"{schema}.tb_{entity_lower}"

    return f"""
-- Deduplication Field Annotations

-- Base identifier (internal, not exposed directly)
COMMENT ON COLUMN {table_name}.identifier IS
'@fraiseql:field name=_baseIdentifier,type=String!,internal=true,description=Base identifier before deduplication suffix';

-- Sequence number (internal, not exposed directly)
COMMENT ON COLUMN {table_name}.sequence_number IS
'@fraiseql:field name=_sequenceNumber,type=Int!,internal=true,description=Deduplication sequence number';

-- Display identifier (exposed as "identifier" in GraphQL)
COMMENT ON COLUMN {table_name}.display_identifier IS
'@fraiseql:field name=identifier,type=String!,description=Unique identifier with optional #n suffix for duplicates';
""".strip()
```

**Generated GraphQL**:
```graphql
type Location {
  id: UUID!
  identifier: String!  # Exposed (display_identifier)
  # _baseIdentifier: String!  # Internal (not exposed)
  # _sequenceNumber: Int!      # Internal (not exposed)
}
```

---

### **1.2: Deduplication Metadata in Mutations**

**File**: `templates/fraiseql/mutation_metadata.sql.jinja2`

```sql
-- Mutation impact: Identifier may change due to deduplication
COMMENT ON FUNCTION {{ schema }}.create_{{ entity_lower }}(...) IS
'@fraiseql:mutation
name=create{{ entity }}
input=Create{{ entity }}Input
success_type=Create{{ entity }}Success
metadata_mapping={
  "_identifierInfo": "IdentifierDeduplicationInfo"
}
impact={
  "identifierDeduplication": true,
  "description": "Identifier may have #n suffix if duplicate"
}';
```

**GraphQL Type**:
```graphql
type IdentifierDeduplicationInfo {
  baseIdentifier: String!
  sequenceNumber: Int!
  finalIdentifier: String!
  wasDeduplicated: Boolean!
}

type CreateLocationSuccess {
  status: String!
  message: String!
  location: Location!
  _identifierInfo: IdentifierDeduplicationInfo
}
```

---

## 🎯 Phase 2: Recalculation Audit Annotations (Day 2)

### **Objective**: Annotate separate audit fields

### **2.1: Audit Field Annotations**

**File**: `src/generators/fraiseql/audit_annotations.py`

```python
def generate_recalculation_audit_annotations(entity: EntityAST, schema: str) -> str:
    """Generate annotations for recalculation audit fields."""

    entity_lower = entity.name.lower()
    table_name = f"{schema}.tb_{entity_lower}"

    annotations = []

    # Standard audit fields
    annotations.append(f"""
-- Standard Business Audit
COMMENT ON COLUMN {table_name}.created_at IS
'@fraiseql:field name=createdAt,type=DateTime!';

COMMENT ON COLUMN {table_name}.updated_at IS
'@fraiseql:field name=updatedAt,type=DateTime!,description=Last business data change';

COMMENT ON COLUMN {table_name}.deleted_at IS
'@fraiseql:field name=deletedAt,type=DateTime,internal=true';
""")

    # Recalculation audit (internal, not exposed in main type)
    annotations.append(f"""
-- Identifier Recalculation Audit (internal)
COMMENT ON COLUMN {table_name}.identifier_recalculated_at IS
'@fraiseql:field name=_identifierRecalculatedAt,type=DateTime,internal=true';

COMMENT ON COLUMN {table_name}.identifier_recalculated_by IS
'@fraiseql:field name=_identifierRecalculatedBy,type=UUID,internal=true';
""")

    if entity.hierarchical:
        # Path audit (internal)
        annotations.append(f"""
-- Path Recalculation Audit (internal)
COMMENT ON COLUMN {table_name}.path_updated_at IS
'@fraiseql:field name=_pathUpdatedAt,type=DateTime,internal=true';

COMMENT ON COLUMN {table_name}.path_updated_by IS
'@fraiseql:field name=_pathUpdatedBy,type=UUID,internal=true';
""")

    return '\n'.join(annotations)
```

**Result**: Recalculation audit fields are marked `internal=true` (not exposed in GraphQL)

---

## 🎯 Phase 3: Node+Info Split Annotations (Day 3)

### **Objective**: Annotate node+info split views

### **3.1: View Annotations**

**File**: `src/generators/fraiseql/view_annotations.py`

```python
def generate_split_view_annotations(entity: EntityAST, schema: str) -> str:
    """Generate FraiseQL annotations for node+info split views."""

    if not entity.metadata_split:
        return ""

    entity_name = entity.name
    entity_lower = entity.name.lower()

    return f"""
-- View combines node + info tables
COMMENT ON VIEW {schema}.v_{entity_lower} IS
'@fraiseql:type name={entity_name},schema={schema},source=view,description=Combined view of {entity_name} structure and attributes';

-- Indicate this is the primary GraphQL type
COMMENT ON VIEW {schema}.v_{entity_lower} IS
'@fraiseql:primary_type Expose this view as the main {entity_name} type in GraphQL';

-- Node table (internal structure, not exposed directly)
COMMENT ON TABLE {schema}.tb_{entity_lower}_node IS
'@fraiseql:internal Structure table for {entity_name} (not exposed in GraphQL)';

-- Info table (internal attributes, not exposed directly)
COMMENT ON TABLE {schema}.tb_{entity_lower}_info IS
'@fraiseql:internal Attributes table for {entity_name} (not exposed in GraphQL)';
""".strip()
```

**Result**: FraiseQL exposes the VIEW as the GraphQL type, hides internal tables

---

## 🎯 Phase 4: INTEGER Path Documentation (Day 3)

### **Objective**: Document INTEGER-based path format in metadata

### **4.1: Path Field Annotation**

**File**: `src/generators/fraiseql/hierarchy_annotations.py`

```python
def generate_hierarchy_annotations(entity: EntityAST, schema: str) -> str:
    """Generate annotations for hierarchical fields."""

    if not entity.hierarchical:
        return ""

    entity_lower = entity.name.lower()
    table_name = f"{schema}.tb_{entity_lower}"

    return f"""
-- LTREE path field (INTEGER-based format)
COMMENT ON COLUMN {table_name}.path IS
'@fraiseql:field name=_path,type=String!,internal=true,format=ltree_integer,description=Hierarchical path using INTEGER primary keys (e.g., 1.5.23.47)';

-- Parent foreign key
COMMENT ON COLUMN {table_name}.fk_parent_{entity_lower} IS
'@fraiseql:field name=parentId,type=UUID,relation=many-to-one,target={entity.name},description=Parent {entity.name}';

-- Rich hierarchy queries via helper functions
COMMENT ON FUNCTION {schema}.get_{entity_lower}_ancestors(UUID) IS
'@fraiseql:query name={entity_lower}Ancestors,description=Get all ancestor nodes,useHelperFunction=true';

COMMENT ON FUNCTION {schema}.get_{entity_lower}_descendants(UUID) IS
'@fraiseql:query name={entity_lower}Descendants,description=Get all descendant nodes,useHelperFunction=true';
""".strip()
```

**Generated GraphQL** (via FraiseQL rich filters):
```graphql
type Location {
  id: UUID!
  identifier: String!
  parentId: UUID
  parent: Location  # Auto-resolved via parentId

  # Rich hierarchy queries
  ancestors: [Location!]!  # Uses get_location_ancestors()
  descendants: [Location!]!  # Uses get_location_descendants()
}

input LocationFilter {
  # Standard filters
  id: UUIDFilter
  identifier: StringFilter

  # Hierarchy filters (FraiseQL auto-generates from LTREE)
  isDescendantOf: UUID
  isAncestorOf: UUID
  isChildOf: UUID
  depth: IntFilter
}
```

---

## 📊 Summary: Team D Deliverables

### **Files to Modify**

| File | Purpose | Changes |
|------|---------|---------|
| `src/generators/fraiseql/field_annotations.py` | Deduplication | Add annotations |
| `src/generators/fraiseql/audit_annotations.py` | Audit fields | Add internal markers |
| `src/generators/fraiseql/view_annotations.py` | Node+info split | Add view annotations |
| `src/generators/fraiseql/hierarchy_annotations.py` | INTEGER paths | Document format |

### **New Annotations**

| Annotation Type | Count | Purpose |
|-----------------|-------|---------|
| Deduplication fields | 3 | identifier, sequence_number, display_identifier |
| Recalculation audit | 4 | identifier_recalculated_at/by, path_updated_at/by |
| Node+info views | 3 | v_{entity}, tb_{entity}_node, tb_{entity}_info |
| Hierarchy helpers | 5 | get_ancestors, get_descendants, etc. |

### **Timeline**

- **Day 1**: Deduplication annotations
- **Day 2**: Recalculation audit annotations
- **Day 3**: Node+info split + INTEGER path docs

**Total**: 3 days

---

## ✅ Acceptance Criteria

- [ ] Deduplication fields annotated correctly
- [ ] display_identifier exposed as `identifier` in GraphQL
- [ ] Internal fields marked with `internal=true`
- [ ] Recalculation audit fields not exposed in GraphQL
- [ ] Node+info views annotated (view exposed, tables internal)
- [ ] INTEGER path format documented
- [ ] Helper functions annotated for FraiseQL discovery

---

## 🔗 Dependencies

**Depends On**:
- Team B Phase 2 (deduplication schema)
- Team B Phase 5 (audit fields)
- Team B Phase 8 (node+info split)

**Blocks**:
- None (metadata layer is final step)

---

**Status**: 🟢 WAITING ON TEAM B
**Priority**: LOW (metadata only)
**Effort**: 3 days
**Start**: After Team B completes all phases
