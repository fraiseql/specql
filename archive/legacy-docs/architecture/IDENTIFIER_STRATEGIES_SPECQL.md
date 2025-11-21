# Identifier Strategies in SpecQL

**Status**: 🎯 Architectural Design
**Impact**: Team A (Parser), Team B (Schema), Team C (Actions)
**Related**: `IDENTIFIER_CALCULATION_PATTERNS.md`, `EXPLICIT_VALIDATION_IMPLEMENTATION_PLAN.md`

---

## 📋 Current State Analysis

### What We Have Now

**Automatic Identifier Field** (Team B generates):
```sql
CREATE TABLE schema.tb_entity (
    identifier TEXT UNIQUE,  -- Simple, no strategy
    ...
);
```

**No Calculation Logic**: Currently just an empty TEXT field that users must populate manually.

**Deduplication Pattern Exists** (`src/generators/schema/deduplication.py`):
```sql
identifier TEXT NOT NULL,
sequence_number INTEGER NOT NULL DEFAULT 1,
display_identifier TEXT GENERATED ALWAYS AS (
    CASE
        WHEN sequence_number > 1
        THEN identifier || '#' || sequence_number
        ELSE identifier
    END
) STORED
```

But **no automatic calculation** of the base `identifier` value!

---

## 🎯 Problem Statement

Users need identifiers to be:
1. **Automatically calculated** (not manually entered)
2. **Human-readable** (e.g., `warehouse-a_floor-1_zone-3`)
3. **Unique** (with automatic deduplication: `#2`, `#3`)
4. **Hierarchical** (for tree structures)
5. **Configurable** (different strategies for different entities)

---

## ✅ Proposed Solution: Declarative Identifier Strategies

### Philosophy

**Sane defaults** with **optional customization**

- ✅ **Default**: Simple slug from `name` field (90% of entities)
- ✅ **Custom**: Declare strategy when needed (hierarchical, composite, etc.)
- ✅ **Explicit**: Clear what identifier will look like
- ✅ **Automatic**: Generated and maintained by framework

---

## 🏗️ SpecQL Syntax Design

### **Multi-Tenant Entities: Automatic Tenant Prefix** 🎯

**IMPORTANT**: All entities in tenant-scoped schemas (`tenant.*`, etc.) **automatically get tenant prefix**.

**SpecQL** (no explicit config needed):
```yaml
entity: Product
schema: tenant  # Multi-tenant schema

fields:
  name: text
```

**Generated Identifier**: `{tenant_identifier}|{slug}` with deduplication
- Tenant "acme-corp", Product "Coffee Maker" → `acme-corp|coffee-maker`
- Tenant "acme-corp", Product "Coffee Maker" (duplicate) → `acme-corp|coffee-maker#2`
- Tenant "globex", Product "Coffee Maker" → `globex|coffee-maker` (different tenant, no conflict)

**Why Automatic**:
- ✅ Human-readable identifiers show ownership
- ✅ External sharing (exports, APIs, integrations)
- ✅ Debugging (immediately see tenant)
- ✅ Natural partitioning in logs/monitoring
- ✅ Uniqueness across tenants (even without RLS)

**Tenant Field Detection**:
Framework automatically detects tenant field:
1. Look for `tenant_id` field (Trinity pattern)
2. Look for `fk_tenant` or `fk_organization` field
3. Use that entity's identifier as prefix

---

### **Strategy 1: Default (Simple Slug)** - 90% of entities

#### **1a. Global Entities** (no tenant)

**SpecQL** (catalog, reference data):
```yaml
entity: Country
schema: catalog  # Global schema

fields:
  name: text
```

**Generated Identifier**: `safe_slug(name)` with deduplication
- `"United States"` → `united-states`
- `"United States"` (duplicate) → `united-states#2`

#### **1b. Tenant-Scoped Entities** (automatic tenant prefix)

**SpecQL**:
```yaml
entity: Product
schema: tenant  # Multi-tenant schema

fields:
  name: text
```

**Generated Identifier**: `{tenant}|{slug}` with deduplication
- Tenant "acme-corp": `acme-corp|coffee-maker`
- Tenant "globex": `globex|coffee-maker`

**Implementation**:
- Team B: Generates `identifier`, `sequence_number`, `display_identifier` fields
- Team C: Generates `recalculate_identifier()` function with **automatic tenant prefix**
- Automatically recalculated on INSERT/UPDATE of `name` or tenant change
- Deduplication scoped **within tenant** (each tenant can have `coffee-maker`)

---

### **Strategy 2: Hierarchical Slug** - Tree structures

#### **2a. Tenant-Scoped Hierarchical** (automatic tenant prefix)

**SpecQL**:
```yaml
entity: Location
schema: tenant
hierarchical: true  # Enables parent field

fields:
  name: text
  location_type: ref(LocationType)
  parent: ref(Location)

identifier:
  strategy: hierarchical_slug
  components:
    - name  # Will be slugified
  separator: "_"  # Default for hierarchy
```

**Generated Identifier**: `{tenant}|{hierarchical_path}`
- Tenant "acme-corp", Root: `acme-corp|warehouse-a`
- Tenant "acme-corp", Child: `acme-corp|warehouse-a_floor-1`
- Tenant "acme-corp", Grandchild: `acme-corp|warehouse-a_floor-1_room-101`
- Tenant "globex", Root: `globex|warehouse-a` (different tenant, different namespace)

**Tenant Prefix Behavior**:
- ✅ Added **only to root nodes** (not repeated in children)
- ✅ Children inherit tenant from path hierarchy
- ✅ Deduplication scoped **within tenant**

#### **2b. Global Hierarchical** (no tenant, rare)

**SpecQL**:
```yaml
entity: IndustryClassification
schema: catalog  # Global reference data
hierarchical: true

fields:
  name: text
```

**Generated Identifier**: Pure hierarchical (no tenant prefix)
- Root: `manufacturing`
- Child: `manufacturing_automotive`
- Grandchild: `manufacturing_automotive_electric-vehicles`

**Implementation**:
- Recursive CTE to build hierarchy
- Concatenate parent identifier + separator + current slug
- Deduplication at each level

---

### **Strategy 3: Hierarchical with Type Prefix**

**SpecQL**:
```yaml
entity: Location
schema: tenant
hierarchical: true

fields:
  name: text
  location_type: ref(LocationType)
  parent: ref(Location)

identifier:
  strategy: hierarchical_slug
  type_prefix:  # Applied after tenant prefix
    - field: location_type.identifier
      transform: none  # Don't slugify (already slug)
  components:
    - name
  separator: "."
```

**Generated Identifier**: `{tenant}|{type}.{hierarchical_path}`
- Tenant "acme-corp":
  - `acme-corp|legal.headquarters`
  - `acme-corp|legal.headquarters.building-a`
  - `acme-corp|legal.headquarters.building-a.floor-1`
- Tenant "globex":
  - `globex|operational.warehouse`
  - `globex|operational.warehouse.loading-dock`

**Pattern**: Tenant prefix `|` Type prefix `.` Hierarchy

---

### **Strategy 4: Hierarchical with Ordering**

**SpecQL**:
```yaml
entity: Location
schema: tenant
hierarchical: true

fields:
  name: text
  int_ordered: integer  # Sort order
  parent: ref(Location)

identifier:
  strategy: hierarchical_slug
  components:
    - field: int_ordered
      format: "LPAD({value}::TEXT, 3, '0')"  # 001, 002, 003
      separator: "-"
    - name
  separator: "."
```

**Generated Identifier**: `ordered-slug.ordered-slug`
- `001-headquarters`
- `001-headquarters.002-building-a`
- `001-headquarters.002-building-a.003-floor-1`

**Sort Order**: Natural alphabetical sorting works: `001-` comes before `002-`

---

### **Strategy 5: Composite Key** - Natural unique identifiers

**SpecQL**:
```yaml
entity: Machine
schema: tenant

fields:
  model: ref(Model)
  serial_number: text

identifier:
  strategy: composite
  components:
    - field: model.identifier
      transform: none
      replace: {"|": "."}  # Replace pipes with dots
    - field: serial_number
      transform: none
  separator: "."
  deduplication: false  # Serial numbers are already unique
```

**Generated Identifier**: `{tenant}|{model}.{serial}` (tenant prefix automatic)
- Tenant "acme-corp": `acme-corp|hp.laserjet-pro-4001n.ABC123XYZ`
- Tenant "globex": `globex|canon.pixma-ts8320.XYZ789ABC`

**No Deduplication**: Serial numbers should be naturally unique

**Global Composite** (catalog entities):
```yaml
entity: Model
schema: catalog  # No tenant

fields:
  manufacturer: ref(Manufacturer)
  name: text

identifier:
  strategy: composite
  components:
    - field: manufacturer.identifier
    - name
```

**Generated**: `hp|laserjet-pro-4001n` (no tenant prefix for catalog)

---

### **Strategy 6: Template-Based** - Full control

**SpecQL**:
```yaml
entity: Contract
schema: tenant

fields:
  organization: ref(Organization)
  contract_number: text
  year: integer

identifier:
  strategy: template
  template: "{organization.identifier}|{year}-{contract_number}"
  transforms:
    organization.identifier: none
    contract_number: uppercase
  deduplication: false
```

**Generated Identifier**: `org + "|" + year + "-" + contract_number`
- `acme-corp|2025-CNT-001`

**Custom Transforms**:
- `none`: Use as-is
- `slugify`: Convert to slug
- `uppercase`: Convert to uppercase
- `lowercase`: Convert to lowercase
- Custom SQL expression

---

## 📚 Complete SpecQL Identifier Config Reference

### Identifier Configuration Block

```yaml
identifier:
  # Strategy selection (required if declaring identifier config)
  strategy: simple | hierarchical_slug | composite | template

  # Tenant prefix (AUTOMATIC for tenant-scoped schemas)
  # Override only if you want to disable or customize
  tenant_prefix:
    enabled: true  # Default: true for tenant.*, false for catalog.*
    field: tenant_id  # Default: auto-detected (tenant_id, fk_tenant, fk_organization)
    separator: "|"  # Default: "|"

  # Type prefix (applied AFTER tenant prefix, before components)
  type_prefix:
    - field: location_type.identifier
      transform: none | slugify | uppercase | lowercase
      separator: "."  # Separator AFTER type prefix

  # Main components
  components:
    - name  # Shorthand for field: name, transform: slugify
    # OR detailed:
    - field: name
      transform: slugify
      format: "LPAD({value}::TEXT, 3, '0')"  # Optional SQL formatting
      separator: "-"  # Separator AFTER this component
      replace: {"|": ".", " ": "-"}  # Character replacements

  # Hierarchy separator (for hierarchical_slug strategy)
  separator: "_" | "." | "-"

  # Template (for template strategy)
  # NOTE: Tenant prefix still applied automatically!
  # Template generates: {tenant}|{template_result}
  template: "{year}-{contract_number}"

  # Transforms (for template strategy)
  transforms:
    field_name: none | slugify | uppercase | lowercase

  # Deduplication
  deduplication: true | false  # Default: true
  deduplication_suffix: "#"  # Default: "#"
  deduplication_scope: tenant | global  # Default: tenant (for tenant schemas)

  # Recalculation triggers
  recalculate:
    on: [insert, update, parent_change, related_change, tenant_change]
    fields: [name, type_id]  # Which field changes trigger recalc
    cascade: none | descendants | subtree  # For hierarchical entities
```

### **Tenant Prefix Defaults by Schema**

| Schema | Tenant Prefix | Deduplication Scope | Example |
|--------|---------------|---------------------|---------|
| `tenant.*` | ✅ Automatic | Within tenant | `acme-corp\|product` |
| `management.*` | ✅ Automatic | Within tenant | `acme-corp\|location` |
| `catalog.*` | ❌ Disabled | Global | `hp\|laserjet` |
| `core.*` | ❌ Disabled | Global | `admin\|system-user` |

**Override Tenant Prefix** (rare):
```yaml
identifier:
  tenant_prefix:
    enabled: false  # Disable for tenant schema (unusual!)
  # OR customize:
  tenant_prefix:
    field: fk_organization  # Use different field
    separator: ":"  # Use different separator
```

---

## 🔧 Implementation Details

### Team A: Parser Updates

**File**: `src/core/ast_models.py` (UPDATE)

```python
@dataclass
class IdentifierComponent:
    """Component of identifier calculation."""
    field: str  # Field name or path (e.g., "name" or "organization.identifier")
    transform: str = "slugify"  # none, slugify, uppercase, lowercase
    format: Optional[str] = None  # SQL formatting expression
    separator: str = ""  # Separator after this component
    replace: Optional[Dict[str, str]] = None  # Character replacements

@dataclass
class IdentifierConfig:
    """Identifier calculation strategy."""
    strategy: str  # simple, hierarchical_slug, composite, template

    # Components
    prefix: List[IdentifierComponent] = field(default_factory=list)
    components: List[IdentifierComponent] = field(default_factory=list)

    # Hierarchy
    separator: str = "_"  # For hierarchical strategies

    # Template
    template: Optional[str] = None  # For template strategy
    transforms: Optional[Dict[str, str]] = None

    # Deduplication
    deduplication: bool = True
    deduplication_suffix: str = "#"

    # Recalculation
    recalculate_on: List[str] = field(default_factory=lambda: ["insert", "update"])
    recalculate_fields: List[str] = field(default_factory=list)
    recalculate_cascade: str = "none"  # none, descendants, subtree

@dataclass
class EntityDefinition:
    """Represents an entity in SpecQL"""

    name: str
    schema: str
    description: str = ""

    # Fields
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)

    # Actions
    actions: List["ActionDefinition"] = field(default_factory=list)

    # Identifier strategy (NEW)
    identifier: Optional[IdentifierConfig] = None

    # ... existing fields ...
```

**File**: `src/core/specql_parser.py` (UPDATE)

```python
class SpecQLParser:
    def _parse_identifier_config(self, yaml_data: dict) -> Optional[IdentifierConfig]:
        """Parse identifier configuration from YAML."""

        if "identifier" not in yaml_data:
            return None  # Use default strategy

        id_config = yaml_data["identifier"]

        # Parse strategy
        strategy = id_config.get("strategy", "simple")

        # Parse components
        prefix = self._parse_identifier_components(id_config.get("prefix", []))
        components = self._parse_identifier_components(id_config.get("components", []))

        # If components is empty but we have a name field, use it as default
        if not components and "name" in self.entity.fields:
            components = [IdentifierComponent(field="name", transform="slugify")]

        return IdentifierConfig(
            strategy=strategy,
            prefix=prefix,
            components=components,
            separator=id_config.get("separator", "_"),
            template=id_config.get("template"),
            transforms=id_config.get("transforms"),
            deduplication=id_config.get("deduplication", True),
            deduplication_suffix=id_config.get("deduplication_suffix", "#"),
            recalculate_on=id_config.get("recalculate", {}).get("on", ["insert", "update"]),
            recalculate_fields=id_config.get("recalculate", {}).get("fields", []),
            recalculate_cascade=id_config.get("recalculate", {}).get("cascade", "none")
        )

    def _parse_identifier_components(
        self,
        components: List[Union[str, dict]]
    ) -> List[IdentifierComponent]:
        """Parse identifier components (shorthand or detailed)."""

        result = []

        for comp in components:
            if isinstance(comp, str):
                # Shorthand: just field name
                result.append(IdentifierComponent(field=comp, transform="slugify"))
            else:
                # Detailed config
                result.append(IdentifierComponent(
                    field=comp["field"],
                    transform=comp.get("transform", "slugify"),
                    format=comp.get("format"),
                    separator=comp.get("separator", ""),
                    replace=comp.get("replace")
                ))

        return result
```

---

### Team B: Schema Generator Updates

**File**: `src/generators/schema/schema_generator.py` (UPDATE)

```python
def _generate_identifier_fields(self, entity: EntityDefinition) -> List[str]:
    """Generate identifier fields based on strategy."""

    fields = []

    if entity.identifier and entity.identifier.strategy != "simple":
        # Complex strategy: identifier + base_identifier + sequence
        fields.extend([
            "identifier TEXT NOT NULL",
            "base_identifier TEXT",
            "sequence_number INTEGER NOT NULL DEFAULT 1",
            "display_identifier TEXT GENERATED ALWAYS AS (",
            "    CASE",
            "        WHEN sequence_number > 1",
            "        THEN identifier || '#' || sequence_number",
            "        ELSE identifier",
            "    END",
            ") STORED"
        ])
    else:
        # Simple strategy: just identifier with deduplication
        fields.extend([
            "identifier TEXT NOT NULL",
            "sequence_number INTEGER NOT NULL DEFAULT 1",
            "display_identifier TEXT GENERATED ALWAYS AS (",
            "    CASE",
            "        WHEN sequence_number > 1",
            "        THEN identifier || '#' || sequence_number",
            "        ELSE identifier",
            "    END",
            ") STORED"
        ])

    # Recalculation audit fields
    fields.extend([
        "identifier_recalculated_at TIMESTAMPTZ",
        "identifier_recalculated_by UUID"
    ])

    return fields
```

---

### Tenant Prefix Auto-Detection Logic

**File**: `src/generators/actions/identifier_recalc_generator.py` (NEW)

```python
class IdentifierRecalcGenerator:
    """Generate identifier recalculation functions."""

    def _detect_tenant_field(self, entity: EntityDefinition) -> Optional[str]:
        """Auto-detect tenant field for prefix."""

        # Check if entity is in tenant-scoped schema
        tenant_schemas = ['tenant', 'management']
        if entity.schema not in tenant_schemas:
            return None  # No tenant prefix for catalog/core

        # Priority order for tenant field detection
        candidates = [
            'tenant_id',           # Primary (Trinity pattern)
            'fk_tenant',           # Alternative FK
            'fk_organization',     # Organization as tenant
            'fk_customer_org'      # Customer org as tenant
        ]

        for field_name in candidates:
            if field_name in entity.fields:
                return field_name

        # Warn if tenant-scoped schema has no tenant field
        logger.warning(
            f"Entity '{entity.name}' in tenant schema '{entity.schema}' "
            f"has no tenant field. Identifiers will not have tenant prefix."
        )
        return None

    def _should_apply_tenant_prefix(
        self,
        entity: EntityDefinition
    ) -> bool:
        """Determine if tenant prefix should be applied."""

        # Explicit override
        if entity.identifier and entity.identifier.tenant_prefix:
            return entity.identifier.tenant_prefix.get('enabled', True)

        # Auto-detect based on schema
        return self._detect_tenant_field(entity) is not None

    def _get_tenant_identifier_expression(
        self,
        entity: EntityDefinition
    ) -> Optional[str]:
        """Get SQL expression for tenant identifier lookup."""

        tenant_field = self._detect_tenant_field(entity)
        if not tenant_field:
            return None

        # Determine reference entity
        field_def = entity.fields[tenant_field]
        if hasattr(field_def, 'reference'):
            # e.g., ref(Organization) → tb_organization
            ref_entity = field_def.reference.lower()
            ref_table = f"tb_{ref_entity}"

            return f"""
            (SELECT identifier
             FROM management.{ref_table}
             WHERE pk_{ref_entity} = t.{tenant_field})
            """
        else:
            # Direct UUID field - need to look up
            # Assume tenant_id → tb_tenant
            return f"""
            (SELECT identifier
             FROM management.tb_tenant
             WHERE id = t.{tenant_field})
            """
```

---

### Team C: Identifier Recalculation Function Generator

**NEW File**: `src/generators/actions/identifier_recalc_generator.py`

```python
"""Generate recalculate_identifier() functions based on strategy."""

from src.core.ast_models import EntityDefinition, IdentifierConfig

class IdentifierRecalcGenerator:
    """Generate identifier recalculation functions."""

    def generate(self, entity: EntityDefinition) -> str:
        """Generate recalculate_identifier function for entity."""

        if not entity.identifier:
            # Default simple strategy
            return self._generate_simple_strategy(entity)

        strategy = entity.identifier.strategy

        if strategy == "simple":
            return self._generate_simple_strategy(entity)
        elif strategy == "hierarchical_slug":
            return self._generate_hierarchical_strategy(entity)
        elif strategy == "composite":
            return self._generate_composite_strategy(entity)
        elif strategy == "template":
            return self._generate_template_strategy(entity)
        else:
            raise ValueError(f"Unknown identifier strategy: {strategy}")

    def _generate_simple_strategy(self, entity: EntityDefinition) -> str:
        """Generate simple slug-based identifier recalculation."""

        entity_lower = entity.name.lower()
        schema = entity.schema

        # Determine source field (default to 'name')
        source_field = "name"
        if entity.identifier and entity.identifier.components:
            source_field = entity.identifier.components[0].field

        # Check for tenant prefix
        has_tenant_prefix = self._should_apply_tenant_prefix(entity)
        tenant_expr = ""
        if has_tenant_prefix:
            tenant_lookup = self._get_tenant_identifier_expression(entity)
            tenant_expr = f"{tenant_lookup} || '|' || "

        return f"""
-- Recalculate identifiers for {entity.name} (simple slug strategy)
-- Tenant prefix: {'YES - ' + tenant_expr if has_tenant_prefix else 'NO (catalog/global entity)'}
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
    v_record RECORD;
    v_new_identifier TEXT;
    v_suffix INTEGER;
    v_final_identifier TEXT;
BEGIN
    -- Create temp table for new identifiers
    DROP TABLE IF EXISTS tmp_{entity_lower}_identifiers;
    CREATE TEMP TABLE tmp_{entity_lower}_identifiers (
        pk_{entity_lower} INTEGER,
        base_identifier TEXT,
        unique_identifier TEXT,
        sequence_number INTEGER
    ) ON COMMIT DROP;

    -- Calculate base identifiers (WITH TENANT PREFIX if applicable)
    INSERT INTO tmp_{entity_lower}_identifiers (pk_{entity_lower}, base_identifier)
    SELECT
        t.pk_{entity_lower},
        {tenant_expr}public.safe_slug(t.{source_field})
    FROM {schema}.tb_{entity_lower} t
    WHERE
        CASE
            WHEN ctx.pk IS NOT NULL THEN t.id = ctx.pk
            WHEN ctx.pk_tenant IS NOT NULL THEN t.tenant_id = ctx.pk_tenant
            ELSE true
        END;

    -- Deduplicate (WITHIN TENANT if applicable)
    FOR v_record IN
        SELECT pk_{entity_lower}, base_identifier
        FROM tmp_{entity_lower}_identifiers
    LOOP
        v_new_identifier := v_record.base_identifier;
        v_suffix := 1;

        -- Find unique identifier (scoped to tenant if tenant prefix exists)
        LOOP
            EXIT WHEN NOT EXISTS (
                SELECT 1 FROM {schema}.tb_{entity_lower}
                WHERE identifier = v_new_identifier
                  AND pk_{entity_lower} != v_record.pk_{entity_lower}
                  AND deleted_at IS NULL
                  -- Tenant scoping: identifiers are already prefixed with tenant,
                  -- so exact match on identifier ensures within-tenant uniqueness
            ) AND NOT EXISTS (
                SELECT 1 FROM tmp_{entity_lower}_identifiers
                WHERE unique_identifier = v_new_identifier
                  AND pk_{entity_lower} != v_record.pk_{entity_lower}
            );

            v_suffix := v_suffix + 1;
            v_new_identifier := v_record.base_identifier || '#' || v_suffix;
        END LOOP;

        -- Update temp table
        UPDATE tmp_{entity_lower}_identifiers
        SET
            unique_identifier = v_new_identifier,
            sequence_number = v_suffix
        WHERE pk_{entity_lower} = v_record.pk_{entity_lower};
    END LOOP;

    -- Apply to live table
    UPDATE {schema}.tb_{entity_lower} t
    SET
        identifier = tmp.unique_identifier,
        sequence_number = tmp.sequence_number,
        identifier_recalculated_at = now(),
        identifier_recalculated_by = ctx.updated_by
    FROM tmp_{entity_lower}_identifiers tmp
    WHERE t.pk_{entity_lower} = tmp.pk_{entity_lower}
      AND (
          t.identifier IS DISTINCT FROM tmp.unique_identifier OR
          t.sequence_number IS DISTINCT FROM tmp.sequence_number
      );

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate simple slug-based identifiers for {entity.name}.
Strategy: simple (slug from {source_field})
Pattern: safe_slug({source_field}) + deduplication';
""".strip()

    def _generate_hierarchical_strategy(self, entity: EntityDefinition) -> str:
        """Generate hierarchical slug-based identifier recalculation."""

        # Similar to simple, but with recursive CTE
        # See IDENTIFIER_CALCULATION_PATTERNS.md for full implementation

        entity_lower = entity.name.lower()
        schema = entity.schema
        parent_field = f"fk_parent_{entity_lower}"

        # Build component expression
        component_expr = self._build_component_expression(
            entity.identifier.components
        )

        return f"""
-- Recalculate identifiers for {entity.name} (hierarchical slug strategy)
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
    v_root_pk INTEGER;
BEGIN
    -- Find root if ctx.pk provided
    -- (Find root logic - walk up to NULL parent)

    -- Create temp table
    DROP TABLE IF EXISTS tmp_{entity_lower}_identifiers;
    CREATE TEMP TABLE tmp_{entity_lower}_identifiers (
        pk_{entity_lower} INTEGER,
        base_identifier TEXT,
        unique_identifier TEXT,
        sequence_number INTEGER
    ) ON COMMIT DROP;

    -- Build hierarchical base identifiers using recursive CTE
    WITH RECURSIVE hierarchy AS (
        -- Anchor: Root nodes
        SELECT
            pk_{entity_lower},
            {component_expr} AS base_identifier
        FROM {schema}.tb_{entity_lower}
        WHERE {parent_field} IS NULL

        UNION ALL

        -- Recursive: Child nodes
        SELECT
            child.pk_{entity_lower},
            parent.base_identifier || '{entity.identifier.separator}' || {component_expr}
        FROM {schema}.tb_{entity_lower} child
        JOIN hierarchy parent ON child.{parent_field} = parent.pk_{entity_lower}
    )
    INSERT INTO tmp_{entity_lower}_identifiers (pk_{entity_lower}, base_identifier)
    SELECT pk_{entity_lower}, base_identifier
    FROM hierarchy;

    -- Deduplicate (same loop as simple strategy)
    -- ... deduplication logic ...

    -- Apply to live table (same as simple strategy)
    -- ... update logic ...

    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate hierarchical slug-based identifiers for {entity.name}.
Strategy: hierarchical_slug
Pattern: parent_identifier + "{entity.identifier.separator}" + current_slug + deduplication';
""".strip()

    def _build_component_expression(
        self,
        components: List[IdentifierComponent]
    ) -> str:
        """Build SQL expression for identifier components."""

        parts = []

        for comp in components:
            # Get field value
            field_expr = comp.field

            # Apply format if specified
            if comp.format:
                field_expr = comp.format.replace("{value}", field_expr)

            # Apply transform
            if comp.transform == "slugify":
                field_expr = f"public.safe_slug({field_expr})"
            elif comp.transform == "uppercase":
                field_expr = f"UPPER({field_expr})"
            elif comp.transform == "lowercase":
                field_expr = f"LOWER({field_expr})"
            # else: none - use as-is

            # Apply character replacements
            if comp.replace:
                for old_char, new_char in comp.replace.items():
                    field_expr = f"REPLACE({field_expr}, '{old_char}', '{new_char}')"

            parts.append(field_expr)

            # Add separator after component
            if comp.separator:
                parts.append(f"'{comp.separator}'")

        # Concatenate all parts
        return " || ".join(parts)
```

---

## 📊 Default Behavior Summary

### **Tenant-Scoped Entities** (automatic tenant prefix)

#### If NO `identifier:` section declared:

**SpecQL**:
```yaml
entity: Product
schema: tenant  # Multi-tenant

fields:
  name: text
```

**Generated**:
- Schema: `identifier`, `sequence_number`, `display_identifier` fields
- Function: `recalculate_product_identifier()` with **tenant prefix + simple slug**
- Pattern: `{tenant_identifier}|{safe_slug(name)}`

**Result Examples**:
- Tenant "acme-corp", Product "Coffee Maker" → `acme-corp|coffee-maker`
- Tenant "acme-corp", duplicate → `acme-corp|coffee-maker#2`
- Tenant "globex", Product "Coffee Maker" → `globex|coffee-maker` (different tenant)

---

#### If `hierarchical: true` but NO `identifier:` section:

**SpecQL**:
```yaml
entity: Location
schema: tenant  # Multi-tenant
hierarchical: true

fields:
  name: text
```

**Generated**:
- Uses hierarchical strategy automatically
- Pattern: `{tenant}|{parent_slug}_{current_slug}`

**Result Examples**:
- Tenant "acme-corp", Root "Warehouse A" → `acme-corp|warehouse-a`
- Tenant "acme-corp", Child "Floor 1" → `acme-corp|warehouse-a_floor-1`
- Tenant "globex", Root "Warehouse A" → `globex|warehouse-a` (different namespace)

**Auto-Detection**: Framework knows to:
1. Add tenant prefix (schema = tenant)
2. Use hierarchical strategy (hierarchical = true)

---

### **Global Entities** (no tenant prefix)

#### Catalog/Reference Data:

**SpecQL**:
```yaml
entity: Country
schema: catalog  # Global

fields:
  name: text
```

**Generated**:
- Pattern: `safe_slug(name)` (NO tenant prefix)

**Result Examples**:
- "United States" → `united-states`
- "United Kingdom" → `united-kingdom`

**Deduplication**: Global scope (across all tenants)

---

## ✅ Benefits of This Design

1. **Sane Defaults**: Works without configuration (90% of cases)
2. **Declarative**: Clear what identifier will look like
3. **Flexible**: Supports simple to complex patterns
4. **Type-Safe**: Validated by Team A parser
5. **Automatic**: Recalculated by framework
6. **Human-Readable**: Slugs, not UUIDs
7. **Unique**: Automatic deduplication
8. **Hierarchical**: Natural support for trees

---

## 🧪 Testing Strategy

### Unit Tests (Team A - Parser)

```python
def test_parse_simple_identifier_strategy():
    yaml_content = """
entity: Product
identifier:
  strategy: simple
  components: [name]
"""
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.identifier is not None
    assert entity.identifier.strategy == "simple"
    assert len(entity.identifier.components) == 1
    assert entity.identifier.components[0].field == "name"

def test_parse_hierarchical_identifier_with_ordering():
    yaml_content = """
entity: Location
hierarchical: true
identifier:
  strategy: hierarchical_slug
  components:
    - field: int_ordered
      format: "LPAD({value}::TEXT, 3, '0')"
      separator: "-"
    - name
  separator: "."
"""
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.identifier.strategy == "hierarchical_slug"
    assert entity.identifier.separator == "."
    assert len(entity.identifier.components) == 2
```

### Integration Tests (Team C - Generator)

```python
def test_generate_simple_identifier_recalc_function():
    entity = EntityDefinition(
        name="Product",
        schema="catalog",
        identifier=IdentifierConfig(
            strategy="simple",
            components=[IdentifierComponent(field="name")]
        )
    )

    generator = IdentifierRecalcGenerator()
    sql = generator.generate(entity)

    assert "CREATE OR REPLACE FUNCTION catalog.recalculate_product_identifier" in sql
    assert "public.safe_slug(name)" in sql
    assert "v_suffix := v_suffix + 1" in sql  # Deduplication
```

---

## 📝 Migration Path

### Existing Code

Currently `identifier` is just an empty TEXT field. Users must:
1. Manually calculate identifiers
2. Manually ensure uniqueness
3. Manually update when dependencies change

### With This Implementation

1. **Add `identifier:` section** to SpecQL YAML
2. **Run code generator** → Creates `recalculate_*_identifier()` function
3. **Call recalculation** → Populates identifiers automatically

```sql
-- Initial population
SELECT catalog.recalculate_product_identifier();

-- Ongoing: Automatic via mutation functions
-- (Team C generates explicit calls in mutations)
```

---

## 🎯 Acceptance Criteria

- [ ] Parser supports `identifier:` configuration
- [ ] Default simple strategy works without config
- [ ] Hierarchical strategy auto-detected for `hierarchical: true`
- [ ] All 6 strategies implemented
- [ ] Deduplication works (#2, #3, etc.)
- [ ] Recalculation functions generated
- [ ] Integration with mutation functions (explicit calls)
- [ ] Comprehensive tests (90%+ coverage)
- [ ] Documentation complete

---

**Status**: 🎯 Ready for Implementation
**Priority**: HIGH (needed for Team B/C Week 2-3)
**Dependencies**: Team A parser, `safe_slug()` function
