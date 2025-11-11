# Issue #6 Visual Guide: Subdomain Parsing Fix

## Table Code Breakdown

```
Table Code: 0 1 3 1 1 1
            │ │ │ │ │ │
            │ │ │ │ │ └─── File Sequence (F)
            │ │ │ │ └───── Entity Sequence (W)
            │ │ │ └─────── Subdomain Code (W) ← THE BUG IS HERE
            │ │ └───────── Domain Code (Z)
            │ └─────────── Schema Layer (Y)
            └───────────── Schema Layer (X)

Format: XYZWWF (6 hexadecimal characters)
```

---

## The Bug Visualized

### Current (WRONG) Parsing

```
Input: "013111"

Position: [0][1][2][3][4][5]
Value:     0  1  3  1  1  1

Parsing:
  schema_layer = [0][1] = "01" ✅
  domain_code = [2] = "3" ✅
  subdomain = [3][4] = "11" ❌ WRONG! Takes 2 digits
  entity_seq = ?
  file_seq = [5] = "1"

Result:
  Directory: "01311_subdomain_11" ❌
```

### Correct Parsing

```
Input: "013111"

Position: [0][1][2][3][4][5]
Value:     0  1  3  1  1  1

Parsing:
  schema_layer = [0][1] = "01" ✅
  domain_code = [2] = "3" ✅
  subdomain_code = [3] = "1" ✅ Correct! Single digit
  entity_sequence = [4] = "1" ✅
  file_sequence = [5] = "1" ✅

Result:
  Directory: "0131_classification" ✅
```

---

## Real-World Example: PrintOptim Catalog

### Scenario: 6 Entities, 2 Subdomains

```
Entities and their table codes:

Classification Subdomain (code "1"):
  ColorMode       013111
  DuplexMode      013121
  MachineFunction 013131

Manufacturer Subdomain (code "2"):
  Manufacturer    013211
  Model           013231
  Accessory       013242
```

### Current Output (WRONG) ❌

```
generated/
  01_write_side/
    013_catalog/
      ├── 01311_subdomain_11/         ← Wrong code, generic name
      │   └── 013111_colormode_group/
      │       └── 013111_tb_colormode.sql
      │
      ├── 01312_subdomain_12/         ← DIFFERENT directory (should be same!)
      │   └── 013121_duplexmode_group/
      │       └── 013121_tb_duplexmode.sql
      │
      ├── 01313_subdomain_13/         ← DIFFERENT directory (should be same!)
      │   └── 013131_machinefunction_group/
      │       └── 013131_tb_machinefunction.sql
      │
      ├── 01321_subdomain_21/         ← Wrong code, generic name
      │   └── 013211_manufacturer_group/
      │       └── 013211_tb_manufacturer.sql
      │
      ├── 01323_subdomain_23/         ← DIFFERENT directory (should be same!)
      │   └── 013231_model_group/
      │       └── 013231_tb_model.sql
      │
      └── 01324_subdomain_24/         ← DIFFERENT directory (should be same!)
          └── 013242_accessory_group/
              └── 013242_tb_accessory.sql

❌ Problems:
  - 6 subdomain directories instead of 2
  - Generic names ("subdomain_11") instead of registry names
  - 5-digit codes (01311) instead of 4-digit (0131)
  - Entities in same subdomain are separated
```

### Expected Output (CORRECT) ✅

```
generated/
  01_write_side/
    013_catalog/
      ├── 0131_classification/        ← Correct code, registry name
      │   ├── 01311_color_mode/       ← Snake_case, no _group ✅
      │   │   └── 013111_tb_color_mode.sql
      │   │
      │   ├── 01312_duplex_mode/      ← Snake_case, no _group ✅
      │   │   └── 013121_tb_duplex_mode.sql
      │   │
      │   └── 01313_machine_function/ ← Snake_case, no _group ✅
      │       └── 013131_tb_machine_function.sql
      │
      └── 0132_manufacturer/          ← Correct code, registry name
          ├── 01321_manufacturer/     ← Snake_case, no _group ✅
          │   └── 013211_tb_manufacturer.sql
          │
          ├── 01323_model/            ← Snake_case, no _group ✅
          │   └── 013231_tb_model.sql
          │
          └── 01324_accessory/        ← Snake_case, no _group ✅
              └── 013242_tb_accessory.sql

✅ Benefits:
  - 2 subdomain directories (matches domain structure)
  - Registry names ("classification", "manufacturer")
  - 4-digit codes (0131, 0132)
  - Snake_case entity names (framework convention)
  - No unnecessary _group suffix
  - Same-subdomain entities grouped together
```

---

## Code Changes Visualization

### File 1: `src/numbering/numbering_parser.py`

```diff
@dataclass
class TableCodeComponents:
    schema_layer: str      # 2 hex chars
    domain_code: str       # 1 hex char
    subdomain_code: str    # 1 hex char: subdomain (0-F)
    entity_sequence: str   # 1 hex char: entity sequence
    file_sequence: str     # 1 hex char

def parse_table_code_detailed(self, table_code: str):
    return TableCodeComponents(
        schema_layer=table_code[0:2],
        domain_code=table_code[2],
        subdomain_code=table_code[3],    # ← SINGLE DIGIT
        entity_sequence=table_code[4],
+       entity_sequence=table_code[4],
        file_sequence=table_code[5],
    )
```

### File 2: `src/generators/schema/naming_conventions.py` (generate_file_path)

```diff
def generate_file_path(self, entity, table_code, ...):
    components = self.parser.parse_table_code_detailed(table_code)

    # Subdomain directory
-   subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
-   # Result: "11" for table_code "013111" ❌
+   subdomain_code = components.subdomain_code
+   # Result: "1" for table_code "013111" ✅

    subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code, {})
-   subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")
-   # Result: "subdomain_11" ❌
+   subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")
+   # Result: "classification" ✅

-   subdomain_dir = f"{components.full_domain}{subdomain_code}_{subdomain_name}"
-   # Result: "01311_subdomain_11" ❌
+   subdomain_dir_code = f"{components.schema_layer}{components.domain_code}{subdomain_code}"
+   subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"
+   # Result: "0131_classification" ✅
```

### File 3: `src/generators/schema/naming_conventions.py` (register_entity_auto)

```diff
def register_entity_auto(self, entity, table_code):
    components = self.parser.parse_table_code_detailed(table_code)

-   subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
-   # For "013111": subdomain_code = "11" ❌
+   subdomain_code = components.subdomain_code
+   # For "013111": subdomain_code = "1" ✅
+
+   # Registry uses 2-digit codes with leading zero
+   subdomain_code_padded = subdomain_code.zfill(2)
+   # "1" → "01" (matches registry format)

    self.registry.register_entity(
        entity_name=entity.name,
        table_code=table_code,
        entity_code=entity_sequence,
        domain_code=components.domain_code,
-       subdomain_code=subdomain_code,  # "11" ❌
+       subdomain_code=subdomain_code_padded,  # "01" ✅
    )
```

---

## Registry Lookup Flow

```
Table Code: 013111

Step 1: Parse table code
  ┌─────────────────────────────────┐
  │ table_code[3] = "1"             │ ← Single digit
  │ components.subdomain_code = "1" │
  └─────────────────────────────────┘

Step 2: Pad for registry lookup
  ┌──────────────────────────────────┐
  │ subdomain_code.zfill(2) = "01"   │ ← 2 digits
  └──────────────────────────────────┘

Step 3: Look up in registry
  ┌─────────────────────────────────────────────┐
  │ registry["domains"]["3"]["subdomains"]["01"]│
  │   {                                         │
  │     "name": "classification",               │
  │     "description": "Product classification" │
  │   }                                         │
  └─────────────────────────────────────────────┘

Step 4: Build directory name
  ┌────────────────────────────────────────────┐
  │ schema_layer (01) + domain (3) +           │
  │ subdomain (1) + _ + name                   │
  │                                            │
  │ Result: "0131_classification"              │
  └────────────────────────────────────────────┘
```

---

## Comparison Table

| Aspect | Before (Wrong) | After (Correct) |
|--------|----------------|-----------------|
| **Subdomain digits** | 2 (`"11"`) | 1 (`"1"`) |
| **Directory code** | 5 digits (`01311`) | 4 digits (`0131`) |
| **Directory name** | Generic (`subdomain_11`) | Registry (`classification`) |
| **Entities per dir** | 1 (split) | Multiple (grouped) |
| **Classification entities** | 3 separate dirs | 1 shared dir |
| **Manufacturer entities** | 3 separate dirs | 1 shared dir |
| **Total subdomain dirs** | 6 | 2 |
| **Registry lookup** | Fails (no "11") | Works ("01") |

---

## Test Flow Diagram

```
                    ┌──────────────┐
                    │ Parser Tests │
                    └──────┬───────┘
                           │
                           ↓ Parse "013111"
                    ┌──────────────────┐
                    │ subdomain = "1"  │ ✅
                    │ entity_seq = "1" │ ✅
                    └──────┬───────────┘
                           │
                           ↓
                  ┌────────────────────┐
                  │ Path Gen Tests     │
                  └────────┬───────────┘
                           │
                           ↓ Generate path
                  ┌──────────────────────────┐
                  │ "0131_classification/"   │ ✅
                  │ (not "01311_subdomain")  │
                  └────────┬─────────────────┘
                           │
                           ↓
                  ┌──────────────────────┐
                  │ Registration Tests   │
                  └────────┬─────────────┘
                           │
                           ↓ Register entity
                  ┌──────────────────────────┐
                  │ domains["3"]             │
                  │   .subdomains["01"]      │ ✅
                  │     .entities["ColorMode"]│
                  └────────┬─────────────────┘
                           │
                           ↓
                  ┌──────────────────────┐
                  │ Integration Tests    │
                  └────────┬─────────────┘
                           │
                           ↓ Generate multiple entities
                  ┌───────────────────────────────┐
                  │ Same subdomain = shared dir   │ ✅
                  │ Different subdomain = split   │ ✅
                  └───────────────────────────────┘
```

---

## Phase-by-Phase Visual

### Phase 1: Parser ✅
```
Before:                After:
┌─────────────┐       ┌──────────────────┐
│subdomain_code   │ New field name for subdomain │
│entity_sequence │ New field name for entity sequence │
└─────────────┘       └──────────────────┘
   2 digits              1 digit each
```

### Phase 2: Path Generation ✅
```
Before:                After:
┌──────────────┐      ┌────────────────────┐
│ 01311_       │  →   │ 0131_              │
│ subdomain_11 │  →   │ classification     │
└──────────────┘      └────────────────────┘
  5 digits + generic    4 digits + registry
```

### Phase 3: Registration ✅
```
Before:                After:
┌──────────────┐      ┌────────────────┐
│ subdomains   │      │ subdomains     │
│   "11": ???  │  →   │   "01":        │
│   (not found)│      │     ColorMode  │
└──────────────┘      └────────────────┘
   Wrong code           Correct code
```

### Phase 4: Integration ✅
```
Before:                           After:
┌─────────────────────┐          ┌──────────────────┐
│ 01311_subdomain_11/ │          │ 0131_            │
│   ColorMode         │          │ classification/  │
├─────────────────────┤    →     │   ColorMode      │
│ 01312_subdomain_12/ │          │   DuplexMode     │
│   DuplexMode        │          │   MachineFunc    │
├─────────────────────┤          └──────────────────┘
│ 01313_subdomain_13/ │           1 shared directory
│   MachineFunc       │
└─────────────────────┘
  3 separate directories
```

---

## Summary

```
┌────────────────────────────────────────────────────────┐
│                    THE FIX                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Bug:    Subdomain = 2 digits ("11")                 │
│  Fix:    Subdomain = 1 digit ("1")                   │
│                                                        │
│  Impact: Directory structure matches registry         │
│          Same-subdomain entities grouped together     │
│          Meaningful names instead of generic          │
│                                                        │
│  Risk:   LOW (no SQL changes)                         │
│  Time:   9-15 hours (6 phases)                       │
│  Status: Ready for implementation                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

*For detailed implementation steps, see: [`issue_6_subdomain_parsing_fix.md`](./issue_6_subdomain_parsing_fix.md)*
