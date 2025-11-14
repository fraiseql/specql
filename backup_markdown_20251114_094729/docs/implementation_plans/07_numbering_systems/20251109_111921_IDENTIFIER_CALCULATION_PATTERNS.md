# Identifier Calculation Patterns - Real-World Analysis

**Source**: PrintOptim Backend `/db` directory - Real production patterns
**Purpose**: Complement the recalcid implementation plan with actual identifier calculation logic
**Date**: 2025-11-08

---

## Executive Summary

After analyzing the PrintOptim backend codebase, identifier calculation follows a **hierarchical, slug-based pattern** with these characteristics:

1. **Format**: `{tenant}|{hierarchy-path}[#n]`
2. **Slug-based**: Human-readable kebab-case slugs from meaningful data
3. **Hierarchical**: Dot-separated tree paths
4. **Unique**: Automatic deduplication with `#2`, `#3` suffixes
5. **Two-tier storage**: Both `identifier` (unique with suffix) and `base_identifier` (template)

---

## Core Patterns Discovered

### Pattern 1: Hierarchical Location Identifier

**Format**: `{address-identifier}|{location-type}.{ordered-name}.{child}[#n]`

**Example**: `toulouse-rue-de-la-pomme|legal.001-headquarters.002-building-a.003-floor-1`

**Components**:
- `{address-identifier}`: From `tb_public_address.identifier` (NOT slugified - already canonical)
- `{location-type}`: Slugified location type (e.g., `legal`, `operational`, `billing`)
- `{ordered-name}`: `001-headquarters` format (3-digit order prefix + slugified name)
- Hierarchy: Dot-separated child paths
- Deduplication: `#2`, `#3` suffix if conflicts

**Source**: `/db/0_schema/03_functions/034_dim/0341_geo/03411_location/034114_recalcid_location.sql`

**Algorithm**:
```sql
-- Root location
base_identifier = address_identifier || '|' || type_slug || '.' || LPAD(int_ordered, 3, '0') || '-' || slugify(name)

-- Child location
base_identifier = parent.base_identifier || '.' || LPAD(int_ordered, 3, '0') || '-' || slugify(name)

-- Deduplication
identifier = base_identifier (if unique)
identifier = base_identifier || '#' || suffix (if conflict)
```

**Key Features**:
- **Ordered hierarchy**: `int_ordered` field provides explicit sort order (defaults to 10)
- **Preserves address identifier**: Address comes pre-formatted, not re-slugified
- **Cascading recalculation**: Updates entire subtree when parent changes
- **Both tables updated**: `tb_location.identifier` gets unique version, `tb_location_info.identifier` gets base version

---

### Pattern 2: Organizational Unit Identifier

**Format**: `{org-slug}|{org-unit}.{child-unit}[#n]`

**Example**: `acme-corp|sales.west-region.san-francisco`

**Components**:
- `{org-slug}`: Slugified organization identifier
- Hierarchy: Dot-separated unit names (all slugified)
- No ordering prefix (unlike location)
- Deduplication: `#2`, `#3` suffix

**Source**: `/db/0_schema/03_functions/034_dim/0342_org/03421_organizational_unit/034214_recalcid_organizational_unit.sql`

**Algorithm**:
```sql
-- Root organizational unit
base_identifier = slugify(org.identifier) || '|' || slugify(ou_info.name)

-- Child organizational unit
base_identifier = parent.base_identifier || '.' || slugify(child_info.name)

-- Fallback for NULL names
base_identifier = 'fallback-unit-' || pk_organizational_unit::text (if name IS NULL)
```

**Key Features**:
- **Simpler than location**: No type prefix, no ordering
- **Robust NULL handling**: Fallback identifiers for missing names
- **Recursive CTE**: Builds hierarchy in single query
- **Two-table update**: Both `tb_organizational_unit` and `tb_organizational_unit_info`

---

### Pattern 3: Machine Identifier

**Format**: `{org-identifier}|{model-identifier}.{serial-number}`

**Example**: `acme-corp|hp.laserjet-pro-4001n.ABC123XYZ`

**Components**:
- `{org-identifier}`: Organization identifier (not slugified if already canonical)
- `{model-identifier}`: Model identifier with dots replacing pipes
- `{serial-number}`: Machine serial number
- No deduplication (serial numbers should be naturally unique)

**Source**: `/db/0_schema/03_functions/034_dim/0345_mat/03451_machine/034515_recalcid_machine.sql`

**Algorithm**:
```sql
identifier = CONCAT(
    org.identifier,
    '|',
    replace(model.identifier, '|', '.'),
    '.',
    machine.machine_serial_number
)
```

**Key Features**:
- **Flat structure**: No hierarchy (machines don't have parent machines)
- **Pipe replacement**: Model identifiers may have pipes, convert to dots
- **No deduplication**: Serial numbers are assumed unique
- **Updates materialized view**: Also updates `tv_machine` denormalized view

---

### Pattern 4: Model Identifier

**Format**: `{manufacturer}|{range}-{model-name}[#n]` OR `{manufacturer}|{model-name}[#n]`

**Example**:
- With range: `hp|laserjet-pro-4001n`
- Without range: `canon|pixma-ts8320#2`

**Components**:
- `{manufacturer}`: Manufacturer identifier
- `{range}` (optional): Manufacturer range/series
- `{model-name}`: Slugified model name
- Deduplication: `#2`, `#3` suffix

**Source**: `/db/0_schema/03_functions/033_catalog/0332_manufacturer/03321_model/033214_recalcid_model.sql`

**Algorithm**:
```sql
base_identifier = CASE
    WHEN manufacturer_range.identifier IS NOT NULL
        THEN manufacturer.identifier || '|' || manufacturer_range.identifier || '-' || slugify(model.name)
    ELSE manufacturer.identifier || '|' || slugify(model.name)
END
```

**Key Features**:
- **Optional range**: Two-tier product hierarchy (manufacturer → range → model)
- **Dry-run mode**: Can preview identifier without persisting (`dry_run` parameter)
- **Deduplication**: Uses `#n` suffix pattern

---

## Common Implementation Patterns

### 1. Slugify Function

**Purpose**: Convert human-readable text to URL-safe kebab-case

**Implementation**:
```sql
CREATE OR REPLACE FUNCTION public.slugify(value TEXT)
RETURNS TEXT AS $$
BEGIN
  -- With unaccent if available (removes accents: café → cafe)
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'unaccent') THEN
    RETURN trim(BOTH '-' FROM regexp_replace(
      lower(unaccent(value)),
      '[^a-z0-9]+',
      '-',
      'gi'
    ));
  ELSE
    -- Simple version without accent removal
    RETURN trim(BOTH '-' FROM regexp_replace(
      lower(value),
      '[^a-z0-9]+',
      '-',
      'gi'
    ));
  END IF;
END;
$$ LANGUAGE plpgsql STABLE STRICT;
```

**Examples**:
- `"San Francisco"` → `"san-francisco"`
- `"Bâtiment A"` → `"batiment-a"` (with unaccent)
- `"1st Floor (East)"` → `"1st-floor-east"`

**Note**: `STABLE`, not `IMMUTABLE` - cannot use in generated columns

---

### 2. Deduplication Pattern

**Common Loop**:
```sql
v_identifier := base_identifier;
v_suffix := 1;

LOOP
    EXIT WHEN
        NOT EXISTS (
            SELECT 1 FROM tb_entity
            WHERE identifier = v_identifier
              AND pk != current_pk
              AND deleted_at IS NULL
        )
        AND NOT EXISTS (
            SELECT 1 FROM tmp_new_identifiers
            WHERE unique_identifier = v_identifier
              AND pk != current_pk
        );

    v_suffix := v_suffix + 1;
    v_identifier := base_identifier || '#' || v_suffix;
END LOOP;
```

**Behavior**:
1. Start with `base_identifier`
2. Check if unique across existing table AND temp table
3. If conflict, append `#2`, `#3`, etc.
4. Loop until unique

**Edge Case**: Excludes soft-deleted records (`deleted_at IS NULL`)

---

### 3. Temporary Table Pattern

**All recalcid functions use temp tables**:

```sql
DROP TABLE IF EXISTS tmp_entity_identifiers;
CREATE TEMP TABLE tmp_entity_identifiers (
    pk_entity UUID,
    fk_entity_info UUID,  -- If applicable
    base_identifier TEXT,
    unique_identifier TEXT
) ON COMMIT DROP;

-- Populate with new base identifiers
INSERT INTO tmp_entity_identifiers
SELECT pk, ..., calculated_base_identifier, NULL
FROM ...;

-- Deduplicate (see pattern above)
-- ...

-- Apply to live tables
UPDATE tb_entity
SET
    identifier = tmp.unique_identifier,
    base_identifier = tmp.base_identifier,
    updated_by = COALESCE(ctx.updated_by, tb_entity.updated_by),
    updated_at = NOW()
FROM tmp_entity_identifiers tmp
WHERE tb_entity.pk = tmp.pk
  AND (
      tb_entity.identifier IS DISTINCT FROM tmp.unique_identifier OR
      tb_entity.base_identifier IS DISTINCT FROM tmp.base_identifier
  );
```

**Benefits**:
- Safe calculation without locking main table
- Atomic update (all or nothing)
- Can validate before commit
- Automatic cleanup (`ON COMMIT DROP`)

---

### 4. Recalculation Context Usage

**Type Definition** (from production):
```sql
CREATE TYPE core.recalculation_context AS (
    pk UUID,                -- Specific entity to recalculate
    pk_organization INTEGER, -- Or all entities in this org
    updated_by UUID         -- Audit trail
);
```

**Usage Patterns**:

```sql
-- Recalculate single entity and descendants
SELECT core.recalcid_location(
    ROW(
        '123e4567-e89b-12d3-a456-426614174000'::UUID,  -- pk
        NULL,                                           -- pk_organization
        '987fcdeb-51a2-43f1-9c8d-123456789abc'::UUID   -- updated_by
    )::core.recalculation_context
);

-- Recalculate all entities in organization
SELECT core.recalcid_location(
    ROW(
        NULL,   -- pk
        123,    -- pk_organization
        'system-recalc'::UUID
    )::core.recalculation_context
);

-- Recalculate ALL entities (dangerous - production maintenance only)
SELECT core.recalcid_location(
    ROW(NULL, NULL, NULL)::core.recalculation_context
);
```

**Default Parameter**:
```sql
CREATE OR REPLACE FUNCTION core.recalcid_entity(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
)
```

This allows calling without parameters: `SELECT core.recalcid_entity();`

---

### 5. Two-Table Identifier Storage

**Node Table** (`tb_location`):
```sql
identifier TEXT NOT NULL UNIQUE,      -- "toulouse|legal.001-hq#2" (with deduplication)
base_identifier TEXT,                  -- "toulouse|legal.001-hq" (without suffix)
```

**Info Table** (`tb_location_info`):
```sql
identifier TEXT,  -- Same as base_identifier (no suffix)
```

**Why Both?**:
- `identifier`: Globally unique, used for external references, queries
- `base_identifier`: Template for regeneration, pattern matching
- Info table gets base (no suffix) for cleaner presentation

**Index Strategy**:
```sql
CREATE INDEX idx_location_base_identifier ON tb_location(base_identifier);
CREATE INDEX idx_location_slug ON tb_location(lower(slugify_simple(base_identifier)))
    WHERE deleted_at IS NULL;
```

---

## Hierarchical Patterns

### Recursive CTE for Hierarchy Building

**Standard Pattern** (used in location, organizational_unit):

```sql
WITH RECURSIVE t_hierarchy AS (
    -- Anchor: Root nodes
    SELECT
        pk,
        fk_parent,
        calculated_slug,
        calculated_slug AS full_path
    FROM tb_entity
    WHERE fk_parent IS NULL
      AND (context filtering...)

    UNION ALL

    -- Recursive: Child nodes
    SELECT
        child.pk,
        child.fk_parent,
        calculated_child_slug,
        parent.full_path || '.' || calculated_child_slug
    FROM tb_entity child
    JOIN t_hierarchy parent ON child.fk_parent = parent.pk
)
SELECT * FROM t_hierarchy;
```

**Key Points**:
1. **Anchor**: Starts with root nodes (no parent)
2. **Context filtering**: Respects `ctx.pk`, `ctx.pk_organization`
3. **Path building**: Concatenates parent path with child slug
4. **Dot separator**: Standard hierarchy delimiter

---

### Finding Root of Subtree

**When `ctx.pk` is provided**, find its root to recalculate entire tree:

```sql
WITH RECURSIVE t_parent_chain AS (
    -- Start from specified node
    SELECT pk_entity, fk_parent_entity
    FROM tb_entity
    WHERE pk_entity = ctx.pk

    UNION ALL

    -- Walk up to root
    SELECT parent.pk_entity, parent.fk_parent_entity
    FROM tb_entity parent
    JOIN t_parent_chain ON t_parent_chain.fk_parent_entity = parent.pk_entity
)
SELECT pk_entity INTO v_root_entity
FROM t_parent_chain
WHERE fk_parent_entity IS NULL
LIMIT 1;
```

**Then recalculate from root downward** to ensure consistency.

---

### LTREE Path Maintenance

**Not calculated in recalcid functions!**

LTREE paths are maintained by **triggers** (separate from identifier calculation):

```sql
-- Trigger updates path when parent changes
CREATE TRIGGER trg_location_update_path
    BEFORE INSERT OR UPDATE OF fk_parent_location, identifier
    ON tenant.tb_location
    FOR EACH ROW
    EXECUTE FUNCTION update_location_path();
```

**Path vs Identifier**:
- **`path` (LTREE)**: Structural hierarchy for queries (`WHERE path <@ 'root.child'`)
- **`identifier` (TEXT)**: Human-readable unique reference

**They can differ!** Path uses structural parent relationship, identifier uses business logic (address, type, etc.)

---

## Identifier Calculation Rules (Specification for Code Generation)

### Rule 1: Tenant Prefix (Multi-Tenant Entities)

**Entities**: Location, Machine, Organizational Unit, Allocation, etc.

**Format**: Always prefix with tenant/organization identifier

```
{org-identifier}|{entity-specific-parts}
```

**Why**: Ensures identifiers are globally unique across tenants

---

### Rule 2: Hierarchical Path (Hierarchical Entities)

**Entities**: Location, Organizational Unit, Industry Classification, etc.

**Format**: Dot-separated hierarchy

```
{root-slug}.{child-slug}.{grandchild-slug}
```

**Rules**:
- Use slugified names (kebab-case)
- Parent path + current slug
- Optional ordering prefix: `001-name`, `002-name`

---

### Rule 3: Meaningful Components (All Entities)

**Choose from entity's most identifying fields**:

| Entity | Components |
|--------|------------|
| Location | address, location_type, name |
| Machine | organization, model, serial_number |
| Model | manufacturer, range (optional), name |
| Organizational Unit | organization, unit_name |
| Contract | organization, contract_number |
| Allocation | machine, organizational_unit, dates |

**Prioritize**:
1. Tenant/org (for scoping)
2. External identifiers (serial numbers, contract numbers)
3. Meaningful names (location name, product name)
4. Type/category (location type, product category)

---

### Rule 4: Deduplication Strategy

**Always deduplicate** with `#n` suffix:

```
base-identifier    → identifier (if unique)
base-identifier    → base-identifier#2 (if conflict)
base-identifier    → base-identifier#3 (if #2 also exists)
```

**Implementation**:
- Check against existing `tb_entity.identifier WHERE deleted_at IS NULL`
- Check against temp table during batch recalculation
- Increment suffix until unique

---

### Rule 5: Update Strategy

**Only update if changed**:

```sql
UPDATE tb_entity
SET
    identifier = new_identifier,
    base_identifier = new_base_identifier,
    updated_by = ctx.updated_by,
    updated_at = NOW()
WHERE pk = ...
  AND (
      identifier IS DISTINCT FROM new_identifier OR
      base_identifier IS DISTINCT FROM new_base_identifier
  );
```

**Why**: Avoids unnecessary triggers, updated_at changes

---

### Rule 6: Two-Table Update (Node+Info Pattern)

**For entities with info table**:

```sql
-- Update node table
UPDATE tb_entity
SET identifier = unique_identifier,
    base_identifier = base_identifier
WHERE ...;

-- Update info table (base only)
UPDATE tb_entity_info
SET identifier = base_identifier
WHERE ...;
```

**Info table gets base identifier** (no `#n` suffix) for cleaner presentation.

---

## SpecQL Integration Proposal

### Option 1: Declarative Identifier Rules

```yaml
entity: Location
schema: tenant

hierarchical: true
metadata_split: true

fields:
  parent: ref(Location)
  name: text
  location_type: ref(LocationType)
  public_address: ref(PublicAddress)
  int_ordered: integer  # Sort order

identifier:
  format: hierarchical
  components:
    - field: public_address.identifier  # Don't slugify
      prefix: true
    - field: location_type.identifier
      transform: slugify
      separator: "."
    - field: int_ordered
      format: "LPAD({value}, 3, '0')"
      separator: "-"
    - field: name
      transform: slugify
  deduplication: suffix  # Adds #2, #3, etc.
  recalculate:
    trigger: [insert, update]
    cascade: descendants  # Recalculate child nodes
```

**Generated Function**:
- `core.recalcid_location(ctx)` based on rules
- Hierarchical CTE builder
- Deduplication loop
- Two-table update (node + info)

---

### Option 2: Template-Based

```yaml
entity: Machine
schema: tenant

identifier:
  template: "{organization.identifier}|{model.identifier}.{machine_serial_number}"
  transforms:
    model.identifier:
      - replace: {"|": "."}
  deduplication: none  # Serial numbers are unique
  recalculate:
    trigger: [insert, update]
    fields: [fk_organization, fk_model, machine_serial_number]
```

**Simpler for non-hierarchical entities**

---

### Option 3: Hybrid (Recommended)

```yaml
entity: Location
schema: tenant

hierarchical: true
metadata_split: true

identifier:
  strategy: hierarchical_slug  # Built-in strategy
  components:
    tenant: public_address.identifier  # Tenant prefix (not slugified)
    type: location_type.identifier     # Type classifier (slugified)
    name: name                          # Entity name (slugified)
    ordering: int_ordered               # Optional ordering
  deduplication: suffix
  recalculate:
    on: [insert, update, parent_change]
    cascade: descendants
```

**Framework provides**:
- `hierarchical_slug` strategy (generates CTE, deduplication, etc.)
- `flat_slug` strategy (for non-hierarchical like Model)
- `composite_key` strategy (for entities with natural unique keys like Machine)

---

## Code Generation Strategy

### Phase 1: Generate slugify Function (Team B)

**One-time in migration 000**:

```sql
-- Simple slugify (no dependencies)
CREATE OR REPLACE FUNCTION public.slugify_simple(value TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN trim(BOTH '-' FROM regexp_replace(
    lower(value),
    '[^a-z0-9]+',
    '-',
    'gi'
  ));
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Unaccent version (if extension available)
CREATE OR REPLACE FUNCTION public.slugify_with_unaccent(value TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN trim(BOTH '-' FROM regexp_replace(
    lower(unaccent(value)),
    '[^a-z0-9]+',
    '-',
    'gi'
  ));
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Wrapper with runtime detection
CREATE OR REPLACE FUNCTION public.slugify(value TEXT)
RETURNS TEXT AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'unaccent') THEN
    RETURN slugify_with_unaccent(value);
  ELSE
    RETURN slugify_simple(value);
  END IF;
END;
$$ LANGUAGE plpgsql STABLE STRICT;
```

---

### Phase 2: Generate recalcid Function Template (Team C)

**Base Template**:

```python
# src/generators/actions/recalcid_generator.py

class RecalcidGenerator:
    def generate(self, entity: Entity) -> str:
        """Generate recalcid_{entity}() function"""

        if not entity.identifier_config:
            return ""  # No custom identifier logic

        strategy = entity.identifier_config.strategy

        if strategy == "hierarchical_slug":
            return self._generate_hierarchical_recalcid(entity)
        elif strategy == "flat_slug":
            return self._generate_flat_recalcid(entity)
        elif strategy == "composite_key":
            return self._generate_composite_recalcid(entity)
        else:
            raise ValueError(f"Unknown identifier strategy: {strategy}")

    def _generate_hierarchical_recalcid(self, entity: Entity) -> str:
        """Generate hierarchical slug-based recalcid function"""

        # Build recursive CTE
        hierarchy_cte = self._build_hierarchy_cte(entity)

        # Build slug expression
        slug_expression = self._build_slug_expression(entity)

        # Build deduplication loop
        dedup_loop = self._build_deduplication_loop(entity)

        # Build update statements
        update_statements = self._build_update_statements(entity)

        return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.recalcid_{entity.name.lower()}(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_record RECORD;
    v_identifier TEXT;
    v_suffix INT;
    v_root_{entity.name.lower()} UUID;
BEGIN
    -- Create temp table
    DROP TABLE IF EXISTS tmp_{entity.name.lower()}_identifiers;
    CREATE TEMP TABLE tmp_{entity.name.lower()}_identifiers (
        pk_{entity.name.lower()} UUID,
        {self._temp_table_columns(entity)},
        base_identifier TEXT,
        unique_identifier TEXT
    ) ON COMMIT DROP;

    -- Find root if ctx.pk provided
    {self._find_root_logic(entity)}

    -- Build hierarchy and base identifiers
    {hierarchy_cte}

    -- Deduplicate
    {dedup_loop}

    -- Apply updates
    {update_statements}
END;
$$;

COMMENT ON FUNCTION {entity.schema}.recalcid_{entity.name.lower()} IS
  'Recalculates hierarchical slug-based identifiers for {entity.name}';
"""
```

---

### Phase 3: Add Identifier Fields to Schema (Team B)

**Auto-add to all entities**:

```python
# src/generators/schema/schema_generator.py

class SchemaGenerator:
    def _generate_identifier_columns(self, entity: Entity) -> List[str]:
        """Generate identifier columns based on strategy"""

        columns = []

        if entity.identifier_config:
            # Unique identifier (with deduplication suffix)
            columns.append("identifier TEXT NOT NULL UNIQUE")

            # Base identifier (template without suffix)
            columns.append("base_identifier TEXT")
        else:
            # Default: Trinity pattern identifier only
            columns.append("identifier TEXT UNIQUE")

        return columns
```

**Generate indexes**:

```python
def _generate_identifier_indexes(self, entity: Entity) -> str:
    """Generate indexes for identifier fields"""

    indexes = []
    table_name = f"{entity.schema}.tb_{entity.name.lower()}"

    if entity.identifier_config:
        # Base identifier index (for pattern matching)
        indexes.append(f"""
CREATE INDEX idx_{entity.name.lower()}_base_identifier
    ON {table_name}(base_identifier);
""")

        # Slug index (for search)
        indexes.append(f"""
CREATE INDEX idx_{entity.name.lower()}_slug
    ON {table_name}(lower(slugify_simple(base_identifier)))
    WHERE deleted_at IS NULL;
""")

    return "\n".join(indexes)
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/actions/test_identifier_calculation.py

def test_hierarchical_slug_generation():
    """Should generate hierarchical slugs with dot separator"""
    entity = Entity(
        name="Location",
        identifier_config=IdentifierConfig(
            strategy="hierarchical_slug",
            components=[
                IdentifierComponent(field="public_address.identifier", prefix=True),
                IdentifierComponent(field="location_type.identifier", transform="slugify"),
                IdentifierComponent(field="name", transform="slugify")
            ]
        )
    )

    generator = RecalcidGenerator()
    sql = generator.generate(entity)

    # Should build hierarchical CTE
    assert "WITH RECURSIVE t_hierarchy" in sql

    # Should use slugify
    assert "slugify(" in sql

    # Should deduplicate
    assert "v_suffix := v_suffix + 1" in sql
    assert "base_identifier || '#' || v_suffix" in sql

def test_flat_slug_without_hierarchy():
    """Non-hierarchical entities should not use recursive CTE"""
    entity = Entity(
        name="Model",
        is_hierarchical=False,
        identifier_config=IdentifierConfig(
            strategy="flat_slug",
            components=[
                IdentifierComponent(field="manufacturer.identifier"),
                IdentifierComponent(field="name", transform="slugify")
            ]
        )
    )

    generator = RecalcidGenerator()
    sql = generator.generate(entity)

    # Should NOT have recursive CTE
    assert "WITH RECURSIVE" not in sql

    # Should have simple SELECT
    assert "SELECT" in sql
    assert "slugify(" in sql
```

---

### Integration Tests

```python
# tests/integration/test_identifier_recalculation.py

def test_location_identifier_recalculation(test_db):
    """Should recalculate location identifiers hierarchically"""

    # Setup: Create organization, address, location type
    test_db.execute("""
        INSERT INTO management.tb_organization (identifier)
        VALUES ('acme-corp') RETURNING pk_organization
    """)
    org_pk = test_db.fetchone()[0]

    test_db.execute("""
        INSERT INTO common.tb_public_address (identifier)
        VALUES ('123-main-st') RETURNING pk_public_address
    """)
    address_pk = test_db.fetchone()[0]

    # Create location info
    test_db.execute(f"""
        INSERT INTO tenant.tb_location_info (name, fk_location_type, fk_public_address)
        VALUES ('Headquarters', 1, {address_pk}) RETURNING pk_location_info
    """)
    info_pk = test_db.fetchone()[0]

    # Create location (node)
    test_db.execute(f"""
        INSERT INTO tenant.tb_location (fk_customer_org, fk_location_info, identifier)
        VALUES ({org_pk}, {info_pk}, 'temp') RETURNING pk_location
    """)
    location_pk = test_db.fetchone()[0]

    # Call recalcid
    test_db.execute(f"""
        SELECT core.recalcid_location(
            ROW({location_pk}, NULL, NULL)::core.recalculation_context
        )
    """)

    # Verify identifier calculated correctly
    test_db.execute(f"""
        SELECT identifier
        FROM tenant.tb_location
        WHERE pk_location = {location_pk}
    """)

    identifier = test_db.fetchone()[0]

    # Should be: {address}|{type}.{name}
    assert identifier.startswith('123-main-st|')
    assert 'headquarters' in identifier

def test_deduplication_adds_suffix(test_db):
    """Should add #2 suffix for duplicate identifiers"""

    # Create two locations with same name
    # ... setup code ...

    # Both would generate 'acme|legal.headquarters'
    # First should be 'acme|legal.headquarters'
    # Second should be 'acme|legal.headquarters#2'

    test_db.execute("SELECT core.recalcid_location()")

    test_db.execute("""
        SELECT identifier
        FROM tenant.tb_location
        ORDER BY created_at
    """)

    identifiers = [row[0] for row in test_db.fetchall()]
    assert identifiers[0] == 'acme|legal.headquarters'
    assert identifiers[1] == 'acme|legal.headquarters#2'
```

---

## Summary: What to Implement

### Immediate (Weeks 1-2) - Foundation

1. ✅ **slugify() functions** (migration 000)
   - `slugify_simple()` - No dependencies
   - `slugify_with_unaccent()` - Requires unaccent extension
   - `slugify()` - Wrapper with runtime detection

2. ✅ **Identifier fields in schema** (Team B)
   - `identifier TEXT NOT NULL UNIQUE` - Final unique identifier
   - `base_identifier TEXT` - Template without suffix
   - Indexes on both

3. ✅ **recalculation_context type** (already in plan)

---

### Short-term (Weeks 3-4) - Basic Generation

4. ✅ **Identifier config in AST** (Team A)
   - Parse `identifier:` section in SpecQL
   - `strategy`, `components`, `deduplication` fields
   - Validation logic

5. ✅ **Basic recalcid generation** (Team C)
   - Template for hierarchical entities
   - Recursive CTE builder
   - Slug expression builder
   - Deduplication loop generator

---

### Medium-term (Weeks 5-6) - Complete Features

6. ✅ **Advanced strategies** (Team C)
   - `hierarchical_slug` (Location, Org Unit)
   - `flat_slug` (Model, Product)
   - `composite_key` (Machine with serial number)

7. ✅ **Cascade integration** (Team C)
   - Trigger recalcid on parent change
   - Recalculate descendants
   - Handle circular dependencies

8. ✅ **Two-table update** (Team B + C)
   - Update both node and info tables
   - info table gets base_identifier

---

## Open Questions

1. **Should identifier calculation be mandatory or optional?**
   - Current thinking: Optional, defaults to simple Trinity `identifier` field
   - Entities with business logic needs can declare `identifier:` config

2. **How to handle references to other entities?**
   - e.g., `public_address.identifier` - need to JOIN in recalcid function
   - Solution: Build JOIN chain from component field paths

3. **When to trigger recalculation?**
   - INSERT (always)
   - UPDATE (which fields?) - specified in `recalculate.fields`
   - Parent change (hierarchical entities)
   - Related entity change (e.g., address changes)

4. **Performance with large hierarchies?**
   - 10k+ locations could be slow
   - Solution: Scope by organization (`ctx.pk_organization`)
   - Consider batch processing / async jobs

---

## Conclusion

Identifier calculation in PrintOptim follows **well-defined patterns**:

1. **Hierarchical slugs** for tree structures (Location, Org Unit)
2. **Composite keys** for unique business identifiers (Machine = org + model + serial)
3. **Flat slugs** for catalog entities (Model, Product)
4. **Automatic deduplication** with `#n` suffixes
5. **Two-tier storage** (identifier + base_identifier)

**Code generator should**:
- Provide **built-in strategies** (hierarchical_slug, flat_slug, composite_key)
- Allow **declarative configuration** in SpecQL YAML
- Generate **recalcid functions** automatically
- Handle **cascading recalculation** for hierarchies
- Ensure **uniqueness** with deduplication logic

This complements the existing recalcid implementation plan with **concrete, production-tested patterns**.
