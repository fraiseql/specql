# SpecQL Code Format Specification - HEXADECIMAL

**Version**: 4.0 (Hexadecimal support - CORRECT)
**Date**: 2025-11-12

---

## Format: 6-Character Hexadecimal Code

**Pattern**: `0LDSEV`

Where each component is a **hexadecimal digit (0-9, A-F)**:
- `0` = Schema prefix (always 0)
- `L` = Layer (1=write, 2=read, 3=functions)
- `D` = Domain code (0-F, **16 domains possible**)
- `S` = Subdomain code (1-F, **15 subdomains per domain**)
- `E` = Entity number (1-F, **15 entities per subdomain**)
- `V` = File/variant number (1-F, **15 files per entity**)

**Total**: 6 hex characters for file codes

---

## Hexadecimal vs Decimal

### Values Per Digit

| Hex | Dec | Hex | Dec | Hex | Dec | Hex | Dec |
|-----|-----|-----|-----|-----|-----|-----|-----|
| 0 | 0 | 4 | 4 | 8 | 8 | C | 12 |
| 1 | 1 | 5 | 5 | 9 | 9 | D | 13 |
| 2 | 2 | 6 | 6 | A | 10 | E | 14 |
| 3 | 3 | 7 | 7 | B | 11 | F | 15 |

### Capacity

| Component | Hex Range | Decimal Range | Count |
|-----------|-----------|---------------|-------|
| Domain | 0-F | 0-15 | **16 domains** |
| Subdomain | 1-F | 1-15 | **15 subdomains** |
| Entity | 1-F | 1-15 | **15 entities** |
| File | 1-F | 1-15 | **15 files** |

**Note**: Subdomain 0 not used (reserved)

---

## Examples from Reference

### Example 1: Language Table

**Code**: `010111`
- Schema: `0`
- Layer: `1` (write_side)
- Domain: `0` (i18n)
- Subdomain: `1` (locale)
- Entity: `1` (language)
- File: `1` (primary table)

All decimal values (0-9) in this example.

---

### Example 2: Location Table

**Code**: `014112`
- Schema: `0`
- Layer: `1` (write_side)
- Domain: `4` (dim)
- Subdomain: `1` (geo)
- Entity: `1` (location)
- File: `2` (second file)

All decimal values (0-9) in this example.

---

### Example 3: Hypothetical Hex Usage

**Code**: `01A3C5` (hypothetical)
- Schema: `0`
- Layer: `1` (write_side)
- Domain: `A` (hex A = decimal 10, e.g., "analytics" domain)
- Subdomain: `3` (third subdomain)
- Entity: `C` (hex C = decimal 12, 12th entity)
- File: `5` (fifth file)

**Path**:
```
0_schema/01_write_side/01A_analytics/01A3_marketing/01A3C_customer_segment/01A3C5_tb_segment.sql
```

---

## Directory Structure Pattern

### Pattern
```
0_schema/
└── 0{L}_{layer_name}/
    └── 0{L}{D}_{domain_name}/
        └── 0{L}{D}{S}_{subdomain_name}/
            └── 0{L}{D}{S}{E}_{entity_name}/
                └── 0{L}{D}{S}{E}{V}_{file_type}_{name}.sql
```

### With Hex Example
```
0_schema/
└── 01_write_side/
    └── 01A_analytics/                    ← Domain A (hex)
        └── 01A3_marketing/               ← Subdomain 3
            └── 01A3C_customer_segment/   ← Entity C (hex)
                └── 01A3C5_tb_segment.sql ← File 5
```

---

## Capacity Analysis

### Maximum Capacity (Full Hex)

**Per Subdomain**:
- 15 write-side entities × 15 files = **225 write files**
- 15 read-side entities × 15 files = **225 read files**

**Per Domain**:
- 15 subdomains × 225 write files = **3,375 write files**
- 15 subdomains × 225 read files = **3,375 read files**

**Total System**:
- 16 domains × 3,375 write files = **54,000 write files possible**
- 16 domains × 3,375 read files = **54,000 read files possible**

**This is MORE than sufficient for any realistic system!**

---

## Registry Schema (Hex Support)

### Example with Hex Values

```yaml
domains:
  '4':  # Hex domain code (dim)
    name: dim
    subdomains:
      '1':  # Hex subdomain code (geo)
        name: geo
        next_write_entity: 2  # Next will be entity 2
        write_entities:
          location_info:
            entity_num: '1'  # Hex: 1
            files:
              - code: '014111'
                type: tb_
          location:
            entity_num: '1'  # Same entity, different file
            files:
              - code: '014112'
                type: tb_

  'A':  # Hex domain A (decimal 10)
    name: analytics
    subdomains:
      '3':  # Hex subdomain 3
        name: marketing
        next_write_entity: 'D'  # Next will be entity D (decimal 13)
        write_entities:
          customer_segment:
            entity_num: 'C'  # Hex C (decimal 12)
            files:
              - code: '01A3C1'
                type: tb_
                name: tb_customer_segment
              - code: '01A3C2'
                type: tb_
                name: tb_segment_member
```

---

## Code Generation Algorithm (Hex-Aware)

### Assign New Entity Code

```python
def assign_write_entity_code(
    domain: str,      # Hex: '0'-'F'
    subdomain: str,   # Hex: '1'-'F'
    entity_name: str
) -> str:
    """
    Assign next write-side entity code with hex support.

    Returns: 6-character hex code like '01A3C5'
    """
    # Get next entity number in this subdomain
    next_entity_hex = registry.get_next_write_entity(domain, subdomain)

    # Build code: 0 + 1 (write) + domain + subdomain + entity + 1 (first file)
    code = f"01{domain}{subdomain}{next_entity_hex}1"

    # Increment hex counter (handle A-F)
    registry.increment_write_entity_hex(domain, subdomain)

    return code


def increment_hex_sequence(current: str) -> str:
    """
    Increment hex sequence value.

    Examples:
        '1' → '2'
        '9' → 'A'
        'F' → raises OverflowError (max reached)
    """
    current_int = int(current, 16)  # Parse hex to int
    if current_int >= 15:
        raise OverflowError(f"Max entity count (15) reached in subdomain")

    next_int = current_int + 1
    return format(next_int, 'X')  # Format as uppercase hex
```

### Parse Hex Code

```python
def parse_hex_code(code: str) -> dict:
    """
    Parse 6-character hex code into components.

    Example:
        '01A3C5' → {
            'schema': '0',
            'layer': 1,
            'domain': 10,
            'subdomain': 3,
            'entity': 12,
            'file': 5
        }
    """
    return {
        'schema': code[0],
        'layer': int(code[1], 16),       # Hex to int
        'domain': int(code[2], 16),      # Hex to int
        'subdomain': int(code[3], 16),   # Hex to int
        'entity': int(code[4], 16),      # Hex to int
        'file': int(code[5], 16),        # Hex to int
    }
```

### Generate Path from Hex Code

```python
def generate_path_from_hex_code(
    code: str,
    entity_name: str,
    layer_name: str,
    domain_name: str,
    subdomain_name: str
) -> Path:
    """
    Generate full path from hex code.

    Example:
        code = '01A3C5'
        Returns: 0_schema/01_write_side/01A_analytics/01A3_marketing/01A3C_customer_segment/01A3C5_tb_segment.sql
    """
    schema = code[0]      # '0'
    layer = code[1]       # '1'
    domain = code[2]      # 'A'
    subdomain = code[3]   # '3'
    entity = code[4]      # 'C'
    file_num = code[5]    # '5'

    # Build path components (keep hex characters as-is)
    layer_dir = f"0{layer}_{layer_name}"
    domain_dir = f"0{layer}{domain}_{domain_name}"
    subdomain_dir = f"0{layer}{domain}{subdomain}_{subdomain_name}"
    entity_dir = f"0{layer}{domain}{subdomain}{entity}_{entity_name}"
    filename = f"{code}_tb_{entity_name}.sql"

    return Path("0_schema") / layer_dir / domain_dir / subdomain_dir / entity_dir / filename
```

---

## Migration from Decimal to Hex

### Existing Codes (Decimal 0-9)

All existing codes using 0-9 **remain valid** - they're just the first 10 values of hex!

**No migration needed** for existing files.

### New Codes (Beyond 9)

When you exceed 9 entities, use A-F:

```python
# Entity sequence: 1, 2, 3, ..., 9, A, B, C, D, E, F
```

**Example progression**:
```
Entity 1:  014111
Entity 2:  014121
...
Entity 9:  014191
Entity 10: 01419A  ← Hex A (decimal 10)
Entity 11: 01419B
Entity 12: 01419C
Entity 13: 01419D
Entity 14: 01419E
Entity 15: 01419F
```

---

## Validation Rules

### Valid Hex Characters

```python
def is_valid_hex_code(code: str) -> bool:
    """
    Validate hex code format.

    Rules:
    - Length: 6 characters
    - Position 1: Must be '0'
    - Position 2: Must be '1', '2', or '3'
    - Positions 3-6: Must be hex (0-9, A-F)
    - Subdomain/Entity/File: Cannot be '0' (1-F only)
    """
    if len(code) != 6:
        return False

    if code[0] != '0':
        return False

    if code[1] not in ['1', '2', '3']:
        return False

    # Check all are valid hex
    try:
        int(code, 16)
    except ValueError:
        return False

    # Check subdomain, entity, file are not 0
    if code[3] == '0' or code[4] == '0' or code[5] == '0':
        return False

    return True
```

---

## Naming Convention

### Case Sensitivity

**Hex digits should be UPPERCASE** for consistency:
- ✅ `01A3C5`
- ❌ `01a3c5`

### Registry Storage

Store hex values as **uppercase strings**:

```yaml
entities:
  customer_segment:
    entity_num: 'C'  # Uppercase
    files:
      - code: '01A3C5'  # Uppercase
```

---

## Updated Constraints

### Limits (Hexadecimal)

| Component | Range | Count | Notes |
|-----------|-------|-------|-------|
| Domains | 0-F | **16** | 0-9, A-F |
| Subdomains | 1-F | **15** | 0 reserved |
| Entities | 1-F | **15** | 0 reserved |
| Files | 1-F | **15** | 0 reserved |

### Practical Capacity

**Most systems will stay in 0-9 range** for readability, but hex support allows growth to:
- **16 domains**
- **15 subdomains per domain**
- **15 entities per subdomain per layer**

This is **more than sufficient** for enterprise-scale systems.

---

## Examples with Hex

### Large System Example

**Domain E (hex 14): "Supply Chain"**
**Subdomain D (hex 13): "Logistics"**
**Entity A (hex 10): "Shipment"**

**Code**: `01EDA1`
```
0  1  E  D  A  1
│  │  │  │  │  └─ File 1
│  │  │  │  └──── Entity A (hex 10)
│  │  │  └─────── Subdomain D (hex 13)
│  │  └────────── Domain E (hex 14)
│  └───────────── Layer 1 (write)
└──────────────── Schema 0
```

**Path**:
```
0_schema/01_write_side/01E_supply_chain/01ED_logistics/01EDA_shipment/01EDA1_tb_shipment.sql
```

---

## Summary

**Format**: `0LDSEV` (6 hex characters)
- **Schema**: Always `0`
- **Layer**: `1`=write, `2`=read, `3`=functions
- **Domain**: Hex `0-F` (**16 domains**)
- **Subdomain**: Hex `1-F` (**15 subdomains**)
- **Entity**: Hex `1-F` (**15 entities per subdomain per layer**)
- **File**: Hex `1-F` (**15 files per entity**)

**Key Points**:
1. ✅ Full hexadecimal support (0-9, A-F)
2. ✅ Existing decimal codes (0-9) remain valid
3. ✅ Use uppercase for hex digits (A-F)
4. ✅ Capacity: 54,000+ files per layer possible
5. ✅ No practical limits for any realistic system

---

**Next**: Update implementation plan with hex-aware code generation logic
