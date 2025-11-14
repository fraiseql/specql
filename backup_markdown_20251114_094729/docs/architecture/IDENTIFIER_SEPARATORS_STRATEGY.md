# Identifier Separators Strategy

**Status**: 🎯 Architectural Decision
**Impact**: All identifier generation
**Related**: `IDENTIFIER_STRATEGIES_SPECQL.md`, PrintOptim allocation pattern

---

## 📋 Problem: Multiple Levels of Separation

Identifiers need to distinguish between **3 levels of structure**:

1. **Tenant scoping** - Separate tenant from entity data
2. **Hierarchy depth** - Separate parent from child within one hierarchy
3. **Cross-hierarchy composition** - Combine identifiers from multiple hierarchies

**Example**: Allocation combines machine, location, organizational_unit, network_config
- All are hierarchical entities
- Each has own tree structure
- Need to combine them in one identifier

---

## ✅ Separator Strategy (PrintOptim Production Pattern)

### **3-Level Separator Hierarchy**

| Level | Separator | Unicode | Purpose | Example |
|-------|-----------|---------|---------|---------|
| **1. Tenant** | `\|` (pipe) | U+007C | Separate tenant from entity | `acme-corp\|...` |
| **2. Hierarchy** | `.` (dot) | U+002E | Parent-child within one tree | `warehouse.floor1.room101` |
| **3. Composition** | `∘` (ring) | U+2218 | Combine multiple hierarchies | `machine∘location∘org-unit` |
| **4. Internal** | `—` (em dash) | U+2014 | Internal components within entity | `router—gateway—ip` |

### **Visual Clarity**

```
acme-corp | 2025-Q1 ∘ hp.laser.s123 ∘ warehouse.floor1 ∘ sales.west ∘ router1—gw1—192.168.1.100
    ↑           ↑           ↑                   ↑              ↑               ↑
  Tenant      Date      Machine              Location       Org Unit     Network Config
    |                  (hierarchy)          (hierarchy)    (hierarchy)    (internal comp)
                          (.)                 (.)            (.)              (—)
               ↑________________________ Composed with ∘ ________________________↑
```

**4-Level Separator Hierarchy**:
1. **`|` (Pipe)**: Tenant scoping
2. **`.` (Dot)**: Hierarchy depth (parent-child)
3. **`∘` (Ring)**: Cross-hierarchy composition
4. **`—` (Em Dash)**: Internal components (flat list)

---

## 🏗️ Detailed Separator Rules

### **Rule 1: Tenant Prefix Separator = `|` (Pipe)**

**Always** use pipe to separate tenant from entity identifier.

**Examples**:
```
acme-corp|coffee-maker
acme-corp|warehouse.floor1
acme-corp|2025-Q1∘machine∘location
```

**Why Pipe**:
- ✅ Visually distinct from dot
- ✅ Rare in natural text
- ✅ URL-safe (no encoding needed)
- ✅ Sortable (ASCII 124)
- ✅ Industry standard for namespace separation

---

### **Rule 2: Hierarchy Separator = `.` (Dot)**

**Within a single hierarchical entity**, use dot to separate levels.

**Examples**:
```
warehouse.floor1.room101.desk5
legal.headquarters.building-a.floor-3
manufacturing.automotive.electric-vehicles
```

**Why Dot** (your preference!):
- ✅ Natural hierarchy notation (like DNS: `subdomain.domain.tld`)
- ✅ More readable than underscore
- ✅ Familiar to developers (package names: `com.acme.product`)
- ✅ URL-safe
- ✅ Shorter than underscore (less visual clutter)

**Previous Default**: Underscore `_`
**New Default**: Dot `.` ← **Updated per your preference**

---

### **Rule 3: Composition Separator = `∘` (Ring Operator)**

**When combining identifiers from DIFFERENT hierarchies**, use ring operator.

**Example - Allocation**:
```
acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1∘sales.west∘net-a
             ↑        ↑              ↑              ↑          ↑
          daterange  machine       location     org-unit   network
                    (each is its own hierarchy tree)
```

**Why Ring Operator (`∘`)**:
- ✅ Visually distinct from both pipe and dot
- ✅ Mathematical meaning: composition of functions (f ∘ g)
- ✅ Rarely appears in natural text
- ✅ Unicode-safe (UTF-8)
- ✅ Copy-paste safe
- ✅ Clear semantic: "this combines multiple things"

**Alternative**: If `∘` causes issues (encoding, fonts, etc.), fallback to `~` (tilde)

---

## 📊 Complete Example Breakdown

### **Simple Entity** (no hierarchy, tenant-scoped)

**Entity**: Product
**Pattern**: `{tenant}|{slug}`
**Example**: `acme-corp|coffee-maker`

**Separators Used**:
- `|` - Tenant prefix

---

### **Hierarchical Entity** (single hierarchy, tenant-scoped)

**Entity**: Location
**Pattern**: `{tenant}|{parent}.{parent}.{current}`
**Example**: `acme-corp|warehouse.floor1.room101`

**Separators Used**:
- `|` - Tenant prefix
- `.` - Hierarchy levels (3 levels deep)

---

### **Hierarchical with Type Prefix**

**Entity**: Location (with location_type)
**Pattern**: `{tenant}|{type}.{parent}.{current}`
**Example**: `acme-corp|legal.headquarters.building-a.floor-3`

**Separators Used**:
- `|` - Tenant prefix
- `.` - Type prefix AND hierarchy levels

**Note**: Type prefix uses same separator as hierarchy (both are "tree-like")

---

### **Cross-Hierarchy Composition** (allocation pattern)

**Entity**: Allocation
**Pattern**: `{tenant}|{daterange}∘{machine}∘{location}∘{org-unit}∘{netconf}`
**Example**: `acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1∘sales.west∘router1—gw1—192.168.1.100`

**Separators Used**:
- `|` - Tenant prefix
- `∘` - Composition (combines 5 different hierarchies)
- `.` - Within each component's hierarchy
- `—` - Within network_configuration internal components

**Component Breakdown**:
1. `acme-corp` - Tenant
2. `2025-Q1` - Date range (flat, no hierarchy)
3. `hp.laser.s123` - Machine (hierarchy: manufacturer.model.serial)
4. `warehouse.floor1` - Location (hierarchy: building.floor)
5. `sales.west` - Org unit (hierarchy: department.region)
6. `router1—gw1—192.168.1.100` - Network config (**internal composition** with em dash)

---

### **Internal Composition** (network_configuration pattern)

**Entity**: NetworkConfiguration
**Pattern**: `{tenant}|{router}—{gateway}—{ip_address}`
**Example**: `acme-corp|router1—192.168.1.1—192.168.1.100`

**Separators Used**:
- `|` - Tenant prefix
- `—` - Internal components (not a hierarchy, just a flat list)

**Why Em Dash (`—`) Instead of Ring (`∘`)**:
- ✅ NetworkConfiguration is **one entity**, not a composition of multiple entities
- ✅ Components (router, gateway, IP) are **flat list**, not hierarchies
- ✅ Em dash visually distinguishes "internal parts" from "cross-entity composition"
- ✅ When used in allocation, already has ring separator at entity level

**When Used in Allocation**:
```
acme-corp|2025-Q1∘machine∘location∘router1—gw1—192.168.1.100
                  ↑_____↑_____↑________________↑
                  Cross-entity (∘)     Internal (—)
```

**2-Level Composition**:
1. **Outer level** (`∘`): Combines different entities (machine, location, network_config)
2. **Inner level** (`—`): Parts within NetworkConfiguration entity

---

## 🔧 SpecQL Syntax

### **Default Hierarchical** (dot separator)

```yaml
entity: Location
schema: tenant
hierarchical: true

fields:
  name: text

# No identifier section needed - uses defaults:
# - Tenant prefix: "|"
# - Hierarchy separator: "." ← NEW DEFAULT
```

**Generated**: `acme-corp|warehouse.floor1.room101`

---

### **Explicit Separator Override** (rare)

```yaml
entity: Location
hierarchical: true

identifier:
  separator: "_"  # Override to underscore if needed
```

**Generated**: `acme-corp|warehouse_floor1_room101`

---

### **Internal Composition** (network_configuration pattern)

```yaml
entity: NetworkConfiguration
schema: tenant

fields:
  router: ref(Router)
  gateway: ref(Gateway)
  ip_address: inet

identifier:
  strategy: composite_flat  # NEW: Flat composition (not hierarchical)
  internal_separator: "—"  # Em dash for internal components
  components:
    - field: router.hostname  # Or router.ip_address if hostname is null
      transform: none
    - field: gateway.ip_address
      transform: none
    - field: ip_address
      transform: none
  deduplication: true
```

**Generated**:
```
acme-corp|router1—192.168.1.1—192.168.1.100
```

**Key Features**:
- ✅ Tenant prefix added automatically
- ✅ Em dash `—` separates internal components
- ✅ NOT cross-entity composition (all from same entity's fields)
- ✅ Flat list (no hierarchy)

---

### **Cross-Hierarchy Composition** (allocation pattern)

```yaml
entity: Allocation
schema: tenant

fields:
  allocation_daterange: text
  machine: ref(Machine)
  location: ref(Location)
  organizational_unit: ref(OrganizationalUnit)
  network_configuration: ref(NetworkConfiguration)

identifier:
  strategy: composite_hierarchical  # Cross-entity composition
  composition_separator: "∘"  # Ring for cross-entity
  components:
    - field: allocation_daterange
      transform: none
    - field: machine.identifier
      strip_tenant_prefix: true  # Remove "acme-corp|" from machine identifier
    - field: location.identifier
      strip_tenant_prefix: true
    - field: organizational_unit.identifier
      strip_tenant_prefix: true
    - field: network_configuration.identifier
      strip_tenant_prefix: true  # Keeps internal "—" separator!
  deduplication: true
```

**Generated**:
```
acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1∘sales.west∘router1—gw1—192.168.1.100
```

**Key Features**:
- ✅ Tenant prefix added once at start
- ✅ Each component's tenant prefix stripped (`acme-corp|warehouse.floor1` → `warehouse.floor1`)
- ✅ Components joined with `∘` (composition separator)
- ✅ Each component retains internal structure:
  - Hierarchies use `.` (dot): `hp.laser.s123`, `warehouse.floor1`
  - Internal use `—` (em dash): `router1—gw1—192.168.1.100`
- ✅ **2-level composition**: outer `∘` + inner `.` or `—`

---

## 📚 Separator Reference Table

### **When to Use Each Separator**

| Scenario | Separator | Example |
|----------|-----------|---------|
| Tenant from entity | `\|` | `acme-corp\|product` |
| Parent from child (same tree) | `.` | `parent.child.grandchild` |
| Type prefix from entity | `.` | `legal.headquarters` |
| Combine different entities | `∘` | `machine∘location∘org-unit` |
| Internal components (flat) | `—` | `router—gateway—ip` |
| Deduplication suffix | `#` | `identifier#2` |
| Ordering prefix | `-` | `001-name` |

### **Character Properties**

| Character | Unicode | ASCII | URL-Safe | SQL-Safe | Human-Readable |
|-----------|---------|-------|----------|----------|----------------|
| `\|` Pipe | U+007C | 124 | ✅ | ✅ | ✅ |
| `.` Dot | U+002E | 46 | ✅ | ✅ | ✅ |
| `∘` Ring | U+2218 | N/A | ✅ (UTF-8) | ✅ | ✅ |
| `—` Em Dash | U+2014 | N/A | ✅ (UTF-8) | ✅ | ✅ |
| `_` Underscore | U+005F | 95 | ✅ | ✅ | ⚠️ (less readable) |
| `~` Tilde | U+007E | 126 | ✅ | ✅ | ✅ (fallback for ∘) |

---

## 🎯 Implementation Guidance

### **Team B: Schema Generator**

No changes needed - separator is metadata, not schema.

---

### **Team C: Identifier Recalculation Generator**

#### **Simple Hierarchical** (updated default)

```python
def _generate_hierarchical_strategy(self, entity: EntityDefinition) -> str:
    # Default separator changed from "_" to "."
    separator = entity.identifier.separator if entity.identifier else "."

    return f"""
    -- Hierarchical identifier with dot separator
    WITH RECURSIVE hierarchy AS (
        SELECT
            pk,
            safe_slug(name) AS base_identifier
        FROM tb_entity
        WHERE fk_parent IS NULL

        UNION ALL

        SELECT
            child.pk,
            parent.base_identifier || '{separator}' || safe_slug(child.name)
        FROM tb_entity child
        JOIN hierarchy parent ON child.fk_parent = parent.pk
    )
    ...
    """
```

#### **Composite Hierarchical** (allocation pattern)

```python
def _generate_composite_hierarchical_strategy(self, entity: EntityDefinition) -> str:
    composition_sep = entity.identifier.composition_separator or "∘"

    # Build component expressions
    component_exprs = []
    for comp in entity.identifier.components:
        expr = comp.field

        # Strip tenant prefix if requested
        if comp.strip_tenant_prefix:
            tenant_field = self._detect_tenant_field(entity)
            if tenant_field:
                tenant_lookup = self._get_tenant_identifier_expression(entity)
                expr = f"""REGEXP_REPLACE(
                    {expr},
                    '^' || {tenant_lookup} || '\\|',
                    ''
                )"""

        component_exprs.append(expr)

    # Join with composition separator
    base_identifier = f" || '{composition_sep}' || ".join(component_exprs)

    return f"""
    -- Composite hierarchical identifier
    INSERT INTO tmp_identifiers (pk, base_identifier)
    SELECT
        pk,
        {tenant_expr}{base_identifier}
    FROM tb_entity;
    """
```

---

## ✅ Updated Defaults Summary

| Pattern | Old Default | New Default | Reason |
|---------|-------------|-------------|--------|
| **Tenant prefix** | `\|` | `\|` | ✅ No change (industry standard) |
| **Hierarchy separator** | `_` | `.` | ✅ **Your preference** - more readable |
| **Composition separator** | N/A | `∘` | ✅ **New feature** - allocation pattern (cross-entity) |
| **Internal separator** | N/A | `—` | ✅ **New feature** - network_config pattern (intra-entity) |
| **Deduplication suffix** | `#` | `#` | ✅ No change (clear semantic) |

---

## 🧪 Examples with New Defaults

### **Before** (underscore hierarchy)
```
acme-corp|warehouse_floor1_room101
acme-corp|legal_headquarters_building-a
```

### **After** (dot hierarchy)
```
acme-corp|warehouse.floor1.room101
acme-corp|legal.headquarters.building-a
```

### **Composition** (new pattern)
```
acme-corp|2025-Q1∘hp.laser.s123∘warehouse.floor1∘sales.west∘net-a
```

**Benefits**:
- ✅ Cleaner, more familiar notation (like DNS, package names)
- ✅ Easier to parse visually
- ✅ Industry-standard feel
- ✅ Cross-hierarchy composition clearly distinguished

---

## 🚀 Migration Path

### **Existing Code**

If you have code using underscore:
```yaml
identifier:
  separator: "_"  # Explicit override
```

### **New Code**

Default is now dot:
```yaml
# No separator specified = dot
hierarchical: true
```

Generates: `parent.child.grandchild`

---

## 📝 Acceptance Criteria

- [ ] Default hierarchy separator changed to `.` (dot)
- [ ] Tenant prefix remains `|` (pipe)
- [ ] New composition separator `∘` (ring) for cross-hierarchy
- [ ] `strip_tenant_prefix` option works for composite components
- [ ] All examples updated in documentation
- [ ] Tests pass with new defaults
- [ ] Migration guide for existing underscore usage

---

**Status**: 🎯 Ready for Implementation
**Priority**: HIGH (affects all identifier generation)
**Dependencies**: None (backward compatible via explicit override)
