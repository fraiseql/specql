# SpecQL Code Format Specification - FINAL

**Version**: 3.0 (Correct understanding based on reference analysis)
**Date**: 2025-11-12

---

## Format: 6-Digit Hierarchical Code

**Pattern**: `0LDDSSEV`

Where each component maps to directory hierarchy:
- `0` = Schema prefix (always 0)
- `L` = Layer (1=write, 2=read, 3=functions)
- `DD` = Domain code (00-99, typically 10-99)
- `SS` = Subdomain code (01-99)
- `E` = Entity number within subdomain (1-9)
- `V` = File/variant number (1-9)

**Total**: 6 digits for file codes

---

## Analyzed Examples from Reference

### Example 1: Language Table

**File**: `010111_tb_language.sql`
**Path**: `01_write_side/010_i18n/0101_locale/01011_language/`

**Breakdown**:
```
0  1  0  01  1  1
│  │  │  │   │  └─ File 1 (first file for this entity)
│  │  │  │   └──── Entity 1 (language is first entity)
│  │  │  └─────── Subdomain 01 (locale)
│  │  └────────── Domain 0 (but shown as "10" in dir: 010_i18n)
│  └───────────── Layer 1 (write_side)
└──────────────── Schema prefix
```

**Wait - the domain shows as `010_i18n` not `00_i18n`!**

Let me reparse: `010111`
- First 3 digits: `010` = layer (01) + domain (0?)
- But directory shows `010_i18n`

I think the mapping is:
- Code: `010111`
- Dir level 1: `01_write_side` (layer)
- Dir level 2: `010_i18n` (layer + domain: `01` + `0` = `010`)
- Dir level 3: `0101_locale` (layer + domain + subdomain: `01` + `01` = `0101`)
- Dir level 4: `01011_language` (layer + domain + subdomain + entity: `01` + `01` + `1` = `01011`)
- File: `010111_tb_language.sql` (full code)

So parsing `010111`:
- `01` = layer (write_side)
- `0` = domain (i18n)
- `1` = subdomain first digit
- `1` = subdomain second digit
-Actually wait, `01` is subdomain in the directory...

Let me try different parsing of `010111`:
- Positions: `0-1-0-1-1-1`
  - `0` = schema prefix
  - `1` = layer
  - `0` = domain first digit
  - `1` = domain second digit OR subdomain first digit?

Looking at directory `0101_locale`, this suggests:
- `01` (layer) + `01` (subdomain) = `0101`

But then domain is missing... unless domain is encoded differently.

Let me look at another example:

### Example 2: Location Table

**File**: `014112_tb_location.sql`
**Path**: `01_write_side/014_dim/0141_geo/01411_location/`

**Breakdown of code** `014112`:
- Dir level 2: `014_dim` → layer `01` + domain `4`
- Dir level 3: `0141_geo` → layer `01` + domain `4` + subdomain `1`
- Dir level 4: `01411_location` → layer `01` + domain `4` + subdomain `1` + entity `1`
- File: `014112` → layer `01` + domain `4` + subdomain `1` + entity `1` + file `2`

So parsing `014112`:
```
0  1  4  1  1  2
│  │  │  │  │  └─ File 2
│  │  │  │  └──── Entity 1
│  │  │  └─────── Subdomain 1
│  │  └────────── Domain 4
│  └───────────── Layer 1
└──────────────── Schema 0
```

This matches! Domain is single digit `4`.

Now back to Example 1:

**File**: `010111_tb_language.sql`

Parsing `010111`:
```
0  1  0  1  1  1
│  │  │  │  │  └─ File 1
│  │  │  │  └──── Entity 1
│  │  │  └─────── Subdomain 1
│  │  └────────── Domain 0
│  └───────────── Layer 1
└──────────────── Schema 0
```

But wait, directory shows:
- `010_i18n` which is `01` (layer) + `0` (domain)
- `0101_locale` which is `01` (layer) + `01` (???)

Ah! `0101` must be layer `01` + domain `0` + subdomain `1`:
- `01` = layer
- `0` = domain
- `1` = subdomain

So subdomain is single digit!

Let me reparse:

### CORRECT Parsing

**Code**: `010111`
```
0  1  0  1  1  1
│  │  │  │  │  └─ File 1
│  │  │  │  └──── Entity 1
│  │  │  └─────── Subdomain 1
│  │  └────────── Domain 0
│  └───────────── Layer 1
└──────────────── Schema 0
```

**Directories**:
- `010_i18n` = `01` (layer) + `0` (domain) ✓
- `0101_locale` = `01` (layer) + `0` (domain) + `1` (subdomain) ✓
- `01011_language` = `01` (layer) + `0` (domain) + `1` (subdomain) + `1` (entity) ✓

**Code**: `014112`
```
0  1  4  1  1  2
│  │  │  │  │  └─ File 2
│  │  │  │  └──── Entity 1
│  │  │  └─────── Subdomain 1
│  │  └────────── Domain 4
│  └───────────── Layer 1
└──────────────── Schema 0
```

**Directories**:
- `014_dim` = `01` (layer) + `4` (domain) ✓
- `0141_geo` = `01` (layer) + `4` (domain) + `1` (subdomain) ✓
- `01411_location` = `01` (layer) + `4` (domain) + `1` (subdomain) + `1` (entity) ✓

Perfect! This matches!

---

## Final Format Specification

### 6-Digit Code: `0LDSEV`

| Position | Name | Values | Meaning |
|----------|------|--------|---------|
| 1 | Schema | `0` | Always 0 for schema files |
| 2 | Layer | `1-3` | 1=write, 2=read, 3=functions |
| 3 | Domain | `0-9` | Single digit domain code |
| 4 | Subdomain | `1-9` | Single digit subdomain code |
| 5 | Entity | `1-9` | Entity sequence in subdomain |
| 6 | File/Variant | `1-9` | File number for this entity |

### Directory Structure Pattern

```
0_schema/
└── 0{L}_{layer_name}/
    └── 0{L}{D}_{domain_name}/
        └── 0{L}{D}{S}_{subdomain_name}/
            └── 0{L}{D}{S}{E}_{entity_name}/
                └── 0{L}{D}{S}{E}{V}_{file_type}_{name}.sql
```

### Complete Examples

#### Write-Side: Language

**Code**: `010111`
- Schema: `0`
- Layer: `1` (write_side)
- Domain: `0` (i18n)
- Subdomain: `1` (locale)
- Entity: `1` (language)
- File: `1` (primary table)

**Path**:
```
0_schema/01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql
```

#### Write-Side: Location

**Code**: `014112`
- Schema: `0`
- Layer: `1` (write_side)
- Domain: `4` (dim)
- Subdomain: `1` (geo)
- Entity: `1` (location)
- File: `2` (second file, main table vs info table)

**Path**:
```
0_schema/01_write_side/014_dim/0141_geo/01411_location/014112_tb_location.sql
```

#### Read-Side: Location View

For read-side, same pattern but layer = `2`:

**Code**: `024130` (hypothetical)
- Schema: `0`
- Layer: `2` (read_side)
- Domain: `4` (dim)
- Subdomain: `1` (geo)
- Entity: `3` (third entity on read-side)
- File: `0` (primary view file)

**Path**:
```
0_schema/02_query_side/024_dim/0241_geo/024130_tv_location.sql
```

---

## Key Insights

### 1. Single-Digit Domain and Subdomain

**Limits**:
- Max 10 domains (0-9)
- Max 9 subdomains per domain (1-9, subdomain 0 not used)
- Max 9 entities per subdomain (1-9)
- Max 9 files per entity (1-9)

### 2. Independent Sequencing Per Layer

- Write-side entity 1 in subdomain 1 = `...11.`
- Read-side entity 1 in subdomain 1 = `...11.` (SAME SEQUENCE, INDEPENDENT!)
- They don't conflict because layer digit differs

**Example**:
- `010111` - write-side, domain 0, subdomain 1, entity 1, file 1
- `020111` - read-side, domain 0, subdomain 1, entity 1, file 1
- Different files, different layers, same numbering scheme

### 3. Directory Hierarchy Builds Progressively

Each level adds one component:
```
01_write_side/          ← Layer
  010_i18n/             ← Layer + Domain
    0101_locale/        ← Layer + Domain + Subdomain
      01011_language/   ← Layer + Domain + Subdomain + Entity
        010111_...sql   ← Full code (Layer + Domain + Subdomain + Entity + File)
```

---

## Mapping to Registry

### Registry Structure (Revised with Single Digits)

```yaml
domains:
  '0':  # Single digit!
    name: i18n
    subdomains:
      '1':  # Single digit!
        name: locale

        # Write-side
        next_write_entity: 3
        write_entities:
          language:
            entity_num: 1
            files:
              - code: '010111'
                type: tb_
                name: tb_language

          locale:
            entity_num: 2
            files:
              - code: '010121'
                type: tb_
                name: tb_locale

        # Read-side (independent!)
        next_read_entity: 2
        read_entities:
          v_locale:
            entity_num: 1
            files:
              - code: '020111'
                type: v_
                name: v_locale

  '4':  # Single digit!
    name: dim
    subdomains:
      '1':  # Single digit!
        name: geo

        write_entities:
          location_info:
            entity_num: 1
            files:
              - code: '014111'
                type: tb_
                name: tb_location_info
              - code: '014112'
                type: tb_
                name: tb_location
```

---

## Code Generation Algorithm

### Assign New Entity Code

```python
def assign_write_entity_code(
    domain: str,      # Single digit: '0', '4', etc.
    subdomain: str,   # Single digit: '1', '2', etc.
    entity_name: str
) -> str:
    """
    Assign next write-side entity code.

    Returns: 6-digit code like '014113'
    """
    # Get next entity number in this subdomain
    next_entity = registry.get_next_write_entity(domain, subdomain)

    # Build code: 0 + 1 (write) + domain + subdomain + entity + 1 (first file)
    code = f"01{domain}{subdomain}{next_entity}1"

    # Increment counter
    registry.increment_write_entity(domain, subdomain)

    return code
```

### Assign Read-Side Entity Code (Independent)

```python
def assign_read_entity_code(
    domain: str,
    subdomain: str,
    view_name: str
) -> str:
    """
    Assign next read-side entity code (INDEPENDENT from write-side).

    Returns: 6-digit code like '024130'
    """
    next_entity = registry.get_next_read_entity(domain, subdomain)

    # Build code: 0 + 2 (read) + domain + subdomain + entity + 0 (tv_ primary file)
    code = f"02{domain}{subdomain}{next_entity}0"

    registry.increment_read_entity(domain, subdomain)

    return code
```

### Generate Path from Code

```python
def generate_path_from_code(code: str, entity_name: str, layer_name: str, domain_name: str, subdomain_name: str) -> Path:
    """
    Generate full path from 6-digit code.

    Example:
        code = '014112'
        entity_name = 'location'
        layer_name = 'write_side'
        domain_name = 'dim'
        subdomain_name = 'geo'

    Returns:
        0_schema/01_write_side/014_dim/0141_geo/01411_location/014112_tb_location.sql
    """
    # Parse code
    schema = code[0]      # '0'
    layer = code[1]       # '1'
    domain = code[2]      # '4'
    subdomain = code[3]   # '1'
    entity = code[4]      # '1'
    file_num = code[5]    # '2'

    # Build path components
    layer_dir = f"0{layer}_{layer_name}"                      # 01_write_side
    domain_dir = f"0{layer}{domain}_{domain_name}"            # 014_dim
    subdomain_dir = f"0{layer}{domain}{subdomain}_{subdomain_name}"  # 0141_geo
    entity_dir = f"0{layer}{domain}{subdomain}{entity}_{entity_name}" # 01411_location
    filename = f"{code}_tb_{entity_name}.sql"                 # 014112_tb_location.sql

    return Path("0_schema") / layer_dir / domain_dir / subdomain_dir / entity_dir / filename
```

---

## Constraints and Limitations

### Hard Limits (Single Digit Components)

| Component | Max Value | Limit |
|-----------|-----------|-------|
| Domains | 0-9 | 10 domains total |
| Subdomains per domain | 1-9 | 9 subdomains |
| Entities per subdomain | 1-9 | 9 entities |
| Files per entity | 1-9 | 9 files |

### Scalability Considerations

**If you need more than 9 entities in a subdomain**:
- Create a new subdomain
- Reorganize domain structure
- Consider hexadecimal (0-F) if format allows

**If you need more than 9 subdomains**:
- Split into multiple domains
- Use hierarchical subdomains (not currently supported)

---

## Summary

**Format**: `0LDSEV` (6 digits)
- **Schema**: Always `0`
- **Layer**: `1`=write, `2`=read
- **Domain**: Single digit `0-9`
- **Subdomain**: Single digit `1-9`
- **Entity**: Single digit `1-9` (independent per layer!)
- **File**: Single digit `1-9`

**Directory Pattern**:
```
0{L}_{layer}/0{L}{D}_{domain}/0{L}{D}{S}_{subdomain}/0{L}{D}{S}{E}_{entity}/{code}_{name}.sql
```

**Key Principle**: Read-side and write-side entity sequences are **completely independent** even though they use the same numbering scheme.

---

**Next**: Update implementation plan with correct 6-digit format and single-digit constraints
