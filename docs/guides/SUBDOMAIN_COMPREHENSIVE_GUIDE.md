# SpecQL Subdomain Concept - Comprehensive Analysis

## 1. WHAT IS SUBDOMAIN?

### Definition
**Subdomain** is a hierarchical organizational layer within a domain that groups related entities together in the hexadecimal numbering system.

**Key Characteristic**: Subdomain is a **SINGLE HEXADECIMAL DIGIT** (0-9, A-F) representing functional areas within a larger business domain.

### Context in Hierarchy
```
Schema Layer  →  Domain  →  Subdomain  →  Entity  →  File
    (01-03)      (1-9)      (0-F)        (0-F)     (0-F)
    2 digits    1 digit    1 digit     1 digit   1 digit
      
Example: 013211 (Manufacturer)
    01 = write_side (schema layer)
    3  = catalog (domain) 
    2  = manufacturer (subdomain) ← Single digit
    1  = first entity in subdomain
    1  = first file
```

---

## 2. HOW IS SUBDOMAIN DEFINED IN YAML ENTITIES?

### Location: `entity.organization` Section

**YAML Structure**:
```yaml
entity: Manufacturer
schema: catalog
description: "..."

organization:
  table_code: "013211"      # 6-digit hierarchical code
  domain_name: "catalog"    # Domain name (informational)
```

### What the `organization` Section Does

The `organization` section in entity YAML specifies the **entity's position in the hierarchical numbering system**:

**Fields**:
- `table_code` (required): 6-digit hexadecimal code encoding the position
- `domain_name` (optional): Name of domain for clarity

### Example from Manufacturer Entity

```yaml
entity:
  name: manufacturer
  schema: catalog
  description: "Lists recognized printer/copier manufacturers..."

  organization:
    table_code: "013211"    # 6-digit code
    domain_name: "catalog"  # Human-readable domain
```

### How Table Code is Parsed

The numbering parser breaks down the code:
```
013211:
  Position 0-1: "01"   → schema_layer (write_side)
  Position 2:   "3"    → domain_code (catalog)
  Position 3:   "2"    → subdomain_code (manufacturer)  ← SUBDOMAIN
  Position 4:   "1"    → entity_sequence (first entity)
  Position 5:   "1"    → file_sequence (first file)
```

---

## 3. HOW SUBDOMAIN AFFECTS CODE GENERATION AND FILE ORGANIZATION

### Hierarchical Directory Structure

When using `--output-format hierarchical`, subdomain determines directory organization:

**Example: Catalog Domain with Two Subdomains**

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/        ← Subdomain "1" (classification)
        01311_color_mode/
          013111_tb_color_mode.sql
        01312_duplex_mode/
          013121_tb_duplex_mode.sql
      0132_manufacturer/          ← Subdomain "2" (manufacturer)
        01321_manufacturer/
          013211_tb_manufacturer.sql
        01322_model/
          013221_tb_model.sql
```

### Directory Path Construction

The subdomain code is used to:

1. **Create subdomain directory**: `{layer}{domain}{subdomain}_{subdomain_name}/`
   - Example: `0131_classification` (4 digits: layer + domain + subdomain)

2. **Isolate related entities**: All entities with same subdomain code share a directory
   - ColorMode (013111) and DuplexMode (013121) both → `0131_classification/`
   - Manufacturer (013211) and Model (013221) both → `0132_manufacturer/`

3. **Make hierarchy navigable**: Users find related entities in same subdomain

---

## 4. EXAMPLES OF ENTITIES USING SUBDOMAIN

### PrintOptim Catalog Domain

The registry shows these subdomains:

```yaml
domains:
  '3':
    name: catalog
    description: "Product catalog, manufacturer data & inventory"
    subdomains:
      '01':
        name: classification
        description: "Product classification, categories & taxonomies"
        entities:
          ColorMode:
            table_code: '013111'

      '02':
        name: manufacturer
        description: "Manufacturer-related entities (brand, model, range)"
        entities:
          Manufacturer:
            table_code: '013211'
          Model:
            table_code: '013221'
```

### Specific Examples

**Classification Subdomain (code 1)**:
- ColorMode (013111)
- DuplexMode (013121)
- MachineFunction (013131)
- **All in**: `0131_classification/`

**Manufacturer Subdomain (code 2)**:
- Manufacturer (013211)
- ManufacturerRange (013221)
- Model (013231)
- **All in**: `0132_manufacturer/`

### CRM Domain Examples

```yaml
domains:
  '2':
    name: crm
    aliases: [management]
    subdomains:
      '01':
        name: core
        description: "Core organization entities"
        entities:
          Organization: {table_code: '012011'}
      '02':
        name: sales
        description: "Sales process entities"
      '03':
        name: customer
        description: "Customer contact entities"
        entities:
          Contact: {table_code: '012036'}
```

---

## 5. DOCUMENTATION AND RESOURCES

### Main Documentation

1. **Numbering Systems Guide** (`docs/reference/numbering-systems.md`)
   - Overview of decimal vs hexadecimal systems
   - Table code format explanation
   - Migration between systems

2. **YAML Reference** (`docs/reference/yaml-reference.md`)
   - Explains `organization` section
   - Shows `table_code` and `domain_name` fields
   - Illustrates hierarchical output structure

3. **Domain Registry** (`registry/domain_registry.yaml`)
   - Complete list of domains and subdomains
   - Entity assignments
   - Validation rules

### Issue #6 Documentation

**File**: `docs/implementation_plans/20251111_135510_issue_6_subdomain_parsing_fix.md`

Detailed analysis of:
- Correct subdomain parsing (single digit)
- Bug where it was parsed as two digits
- Examples from PrintOptim backend
- Fix implementation plan

---

## 6. SUBDOMAIN IN THE HEX HIERARCHICAL STRUCTURE

### Registry Structure

Subdomains are organized under domains in `domain_registry.yaml`:

```yaml
domains:
  '1':                    # Domain code (1 digit)
    name: core
    subdomains:
      '01':               # Subdomain code (2-digit with padding)
        name: i18n
        entities: {}
      '02':
        name: auth
        entities: {}
  '3':                    # Domain code 3 = catalog
    name: catalog
    subdomains:
      '01':               # Subdomain 1 = classification
        name: classification
        entities: {}
      '02':               # Subdomain 2 = manufacturer  
        name: manufacturer
        entities:
          Manufacturer: {table_code: '013211'}
```

### How Subdomains Drive Generation

1. **Parser extracts subdomain**: `subdomain_code = "2"` from "013211"
2. **Generator looks up in registry**: Finds subdomain_name = "manufacturer"
3. **Creates directory**: `0132_manufacturer/`
4. **Places entity**: Manufacturer goes in `0132_manufacturer/01321_manufacturer/`

---

## 7. RELATIONSHIPS: SCHEMA, DOMAIN, SUBDOMAIN, ENTITY

### Hierarchy Explained

```
PostgreSQL Schema (PostgreSQL-level)
    └── Domain (business area)
        └── Subdomain (functional grouping)
            └── Entity (specific table)

Example: catalog domain
    PostgreSQL Schema: catalog
    Domain: catalog (domain code 3)
    Subdomain: manufacturer (subdomain code 2)
    Entity: Manufacturer (entity code 1)
    
    Table Code: 013211
    Directory: 0132_manufacturer/01321_manufacturer/
    SQL Table: catalog.tb_manufacturer
```

### Terminology Clarification

| Term | Scope | Example | Notes |
|------|-------|---------|-------|
| **Schema** | PostgreSQL namespace | `catalog`, `crm`, `common` | Defined in entity's `schema:` field |
| **Domain** | Business domain grouping | `catalog` (code 3) | First digit in table code position 2 |
| **Subdomain** | Functional area | `manufacturer` (code 2) | Single digit in table code position 3 |
| **Entity** | Specific table | `Manufacturer` | Domain + subdomain + entity code |
| **Table Code** | Full numeric identifier | `013211` | 6-digit hexadecimal |

---

## 8. SUBDOMAIN INFERENCE

### Smart Subdomain Assignment

Registry includes **subdomain inference patterns** to automatically assign entities to correct subdomains:

```yaml
subdomain_inference:
  catalog:
    manufacturer:
      patterns:
        - manufacturer
        - brand
        - model
        - range
    product:
      patterns:
        - product
        - sku
        - item
        - variant
```

**Usage**: If entity name matches pattern, it's auto-assigned to that subdomain.

---

## 9. ISSUE #6: THE SUBDOMAIN PARSING BUG

### The Problem

**Original Bug**: Code incorrectly parsed subdomain as **TWO digits** instead of one.

```python
# WRONG (old code)
subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
# For 013211: "2" + "1" = "21" ❌ WRONG!

# CORRECT (fixed)
subdomain_code = components.subdomain_code
# For 013211: "2" ✅ CORRECT!
```

### Impact

**Before Fix**:
```
0131_classification/
  01311_subdomain_11/  ← WRONG: separate directory
  01312_subdomain_12/  ← WRONG: separate directory
  01313_subdomain_13/  ← WRONG: separate directory
0132_manufacturer/
  01321_subdomain_21/  ← WRONG: separate directory
```

**After Fix**:
```
0131_classification/
  01311_color_mode/    ← CORRECT: shared directory
  01312_duplex_mode/
  01313_machine_function/
0132_manufacturer/
  01321_manufacturer/  ← CORRECT: shared directory
  01322_model/
```

---

## 10. KEY TAKEAWAYS

### Core Concepts

1. **Subdomain is a single hexadecimal digit** (0-F)
   - Not two digits
   - Represents functional area within domain
   - Position 3 in 6-digit table code

2. **Defined via `organization.table_code`** in entity YAML
   - Full 6-digit code includes subdomain
   - Example: `013211` encodes subdomain `2` (manufacturer)

3. **Drives hierarchical directory structure**
   - Entities with same subdomain share directory
   - Directory code: 4 digits (layer + domain + subdomain)
   - Makes navigation intuitive

4. **Registered in `domain_registry.yaml`**
   - Lists all subdomains per domain
   - Maps entity names to codes
   - Includes inference patterns

5. **Critical for enterprise projects**
   - Without subdomains: 100+ entities in one directory (hard to navigate)
   - With subdomains: Organized hierarchy
   - Part of hexadecimal numbering system (advanced mode)

### When You Need Subdomains

✅ **Use hexadecimal system with subdomains if**:
- Project has 50+ entities
- Multiple business domains
- Enterprise-scale organization
- Strict governance required

❌ **Use simpler decimal system if**:
- Project has < 50 entities
- Simple flat structure preferred
- Fast prototyping mode

---

## 11. QUICK REFERENCE

### Parser Code
**File**: `src/numbering/numbering_parser.py`
- `TableCodeComponents` dataclass with `subdomain_code` field
- `parse_table_code_detailed()` method extracts single digit

### Generator Code
**File**: `src/generators/schema/naming_conventions.py`
- `generate_file_path()` uses subdomain code to build paths
- Registry lookup finds subdomain name

### Registry Config
**File**: `registry/domain_registry.yaml`
- Domains have `subdomains` dict
- Each subdomain has code, name, description
- Entity assignments track which subdomain they belong to

### Testing
**Files**: 
- `tests/unit/numbering/test_numbering_parser.py` - Parser tests
- `tests/integration/test_issue_6_subdomain_parsing.py` - Integration tests

---

**Summary**: Subdomain is a single-digit organizational layer that groups related entities within a domain, enabling hierarchical file organization for enterprise-scale SpecQL projects.
