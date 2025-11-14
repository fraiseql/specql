# SpecQL Subdomain - Code Examples & File References

## FILE LOCATIONS - WHERE SUBDOMAIN IS DEFINED

### 1. Entity YAML Definition
**Location**: `/home/lionel/code/specql/entities/examples/manufacturer.yaml` (lines 15-17)

```yaml
organization:
  table_code: "013211"
  domain_name: "catalog"
```

**Breakdown of "013211"**:
- `01` = schema layer (write_side)
- `3` = domain (catalog)
- `2` = subdomain (manufacturer) ← **THIS IS SUBDOMAIN**
- `1` = entity sequence
- `1` = file sequence

---

### 2. Parser Implementation
**Location**: `/home/lionel/code/specql/src/numbering/numbering_parser.py`

```python
@dataclass
class TableCodeComponents:
    """Structured representation of parsed table code components"""
    schema_layer: str      # "01"
    domain_code: str       # "3"
    subdomain_code: str    # "2"  ← SINGLE DIGIT (NOT two digits!)
    entity_sequence: str   # "1"
    file_sequence: str     # "1"

def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
    """Parse 6-character hexadecimal table code into structured components"""
    table_code = table_code.upper()
    
    if not re.match(r"^[0-9A-F]{6}$", table_code):
        raise ValueError(f"Invalid table_code: {table_code}")
    
    return TableCodeComponents(
        schema_layer=table_code[0:2],      # Positions 0-1
        domain_code=table_code[2],         # Position 2
        subdomain_code=table_code[3],      # Position 3  ← SINGLE DIGIT
        entity_sequence=table_code[4],     # Position 4
        file_sequence=table_code[5],       # Position 5
    )
```

**Key Method** (lines 65-100):
- Extracts subdomain as **single digit** at position 3
- Returns structured `TableCodeComponents` object

---

### 3. Generator Implementation
**Location**: `/home/lionel/code/specql/src/generators/schema/naming_conventions.py`

Uses the parsed subdomain to build hierarchical paths:

```python
def generate_file_path(
    self,
    entity: Entity,
    table_code: str,
    file_type: str = "table",
    base_dir: str = "generated/migrations",
) -> str:
    """Generate hierarchical file path for entity"""
    
    components = self.parser.parse_table_code_detailed(table_code)
    
    # Schema layer directory
    schema_layer_name = self.registry.registry["schema_layers"].get(
        components.schema_layer, f"schema_{components.schema_layer}"
    )
    schema_dir = f"{components.schema_layer}_{schema_layer_name}"
    # Result: "01_write_side"
    
    # Domain directory
    domain_data = self.registry.registry["domains"].get(components.domain_code, {})
    domain_name = domain_data.get("name", f"domain_{components.domain_code}")
    domain_dir = f"{components.full_domain}_{domain_name}"
    # Result: "013_catalog"
    
    # Subdomain directory - USES SINGLE DIGIT
    subdomain_code = components.subdomain_code  # "2" (SINGLE DIGIT)
    subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code, {})
    subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")
    # Result: "manufacturer"
    
    # Build subdomain directory code: 4 digits
    subdomain_dir_code = f"{components.schema_layer}{components.domain_code}{subdomain_code}"
    # Result: "0132" (write_side + catalog + manufacturer)
    
    subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"
    # Result: "0132_manufacturer"
    
    # Rest of path construction...
    return str(Path(base_dir) / schema_dir / domain_dir / subdomain_dir / ...)
```

**Output Path for Manufacturer (013211)**:
```
generated/migrations/01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql
```

---

### 4. Registry Configuration
**Location**: `/home/lionel/code/specql/registry/domain_registry.yaml`

```yaml
domains:
  '3':
    name: catalog
    description: "Product catalog, manufacturer data & inventory"
    multi_tenant: false
    subdomains:
      '01':                               # Subdomain code 1
        name: classification
        description: "Product classification, categories & taxonomies"
        next_entity_sequence: 1
        entities: {}
      
      '02':                               # Subdomain code 2 ← MANUFACTURER
        name: manufacturer
        description: "Manufacturer-related entities (brand, model, range)"
        next_entity_sequence: 43
        entities:
          Manufacturer:
            table_code: '013211'          # Code 2 in position 3
            entity_code: MNF
            assigned_at: '2025-11-10T09:17:31.604441'
          Model:
            table_code: '013221'          # Same subdomain (2)
            entity_code: MDL
            assigned_at: '2025-11-10T09:17:31.665985'
      
      '03':
        name: product
        description: "Product entities, SKUs & variants"
        next_entity_sequence: 1
        entities: {}
```

**Key Insight**: Both Manufacturer and Model have subdomain code `2`, so they share the `0132_manufacturer/` directory.

---

## WORKING EXAMPLES

### Example 1: Manufacturer Entity

**YAML Definition**:
```yaml
entity:
  name: manufacturer
  schema: catalog
  description: "Lists recognized printer/copier manufacturers..."
  organization:
    table_code: "013211"
    domain_name: "catalog"
```

**Table Code Breakdown**:
```
013211
  01 → write_side
  3  → catalog (domain)
  2  → manufacturer (subdomain) ← POSITION 3
  1  → entity sequence
  1  → file sequence
```

**Generated Path**:
```
generated/
  01_write_side/
    013_catalog/
      0132_manufacturer/            ← Subdomain directory (4 digits)
        01321_manufacturer/         ← Entity group directory (5 digits)
          013211_tb_manufacturer.sql ← File (6 digits in filename)
```

---

### Example 2: Multiple Entities in Same Subdomain

**Classification Subdomain** (code 1):

```yaml
# Entity 1: ColorMode (013111)
entity: ColorMode
organization:
  table_code: "013111"

# Entity 2: DuplexMode (013121)
entity: DuplexMode
organization:
  table_code: "013121"

# Entity 3: MachineFunction (013131)
entity: MachineFunction
organization:
  table_code: "013131"
```

**All Use Subdomain Code "1"**, so they share one directory:

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/          ← Shared subdomain directory
        01311_color_mode/           ← Separate entity groups
          013111_tb_color_mode.sql
        01312_duplex_mode/
          013121_tb_duplex_mode.sql
        01313_machine_function/
          013131_tb_machine_function.sql
```

**Without Subdomain** (if parsed wrong as "11", "12", "13"):
```
generated/
  01_write_side/
    013_catalog/
      01311_subdomain_11/           ← WRONG: separate directories
        013111_tb_color_mode.sql
      01312_subdomain_12/           ← WRONG: separate directories
        013121_tb_duplex_mode.sql
      01313_subdomain_13/           ← WRONG: separate directories
        013131_tb_machine_function.sql
```

---

### Example 3: Cross-Subdomain Separation

**Catalog Domain with Multiple Subdomains**:

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/          ← Subdomain 1
        01311_color_mode/
        01312_duplex_mode/
      0132_manufacturer/            ← Subdomain 2
        01321_manufacturer/
        01322_model/
      0133_product/                 ← Subdomain 3
        01331_product/
      0134_generic/                 ← Subdomain 4
        01341_product_specification/
      0135_financing/               ← Subdomain 5
        01351_financing_option/
```

Each subdomain code (1, 2, 3, 4, 5) creates a separate directory.

---

## TESTING CODE

### Parser Tests
**Location**: `/home/lionel/code/specql/tests/unit/numbering/test_numbering_parser.py`

```python
def test_parse_table_code_subdomain_single_digit():
    """Subdomain should be SINGLE digit (position 3)"""
    parser = NumberingParser()
    
    # Test case: ColorMode entity
    components = parser.parse_table_code_detailed("013111")
    
    assert components.schema_layer == "01"
    assert components.domain_code == "3"
    assert components.subdomain_code == "1"    # ← SINGLE DIGIT
    assert components.entity_sequence == "1"
    assert components.file_sequence == "1"

def test_parse_table_code_manufacturer_subdomain():
    """Manufacturer subdomain (code 2) should parse correctly"""
    parser = NumberingParser()
    
    components = parser.parse_table_code_detailed("013211")
    
    assert components.subdomain_code == "2"    # ← SINGLE DIGIT
    assert components.entity_sequence == "1"
```

### Integration Tests
**Location**: `/home/lionel/code/specql/tests/integration/test_issue_6_subdomain_parsing.py`

Tests verify that:
1. Entities in same subdomain share directory
2. Different subdomains create separate directories
3. Correct subdomain names from registry are used
4. No `subdomain_XX` generic names generated

---

## QUICK LOOKUP TABLE

| Entity | Table Code | Breakdown | Subdomain | Directory |
|--------|-----------|-----------|-----------|-----------|
| ColorMode | 013111 | 01-3-**1**-1-1 | 1 (classification) | `0131_classification/` |
| DuplexMode | 013121 | 01-3-**1**-2-1 | 1 (classification) | `0131_classification/` |
| Manufacturer | 013211 | 01-3-**2**-1-1 | 2 (manufacturer) | `0132_manufacturer/` |
| Model | 013221 | 01-3-**2**-2-1 | 2 (manufacturer) | `0132_manufacturer/` |
| Product | 013311 | 01-3-**3**-1-1 | 3 (product) | `0133_product/` |

**Key**: Subdomain is the third hexadecimal digit (position 3) in the 6-digit code.

---

## RELATED DOCUMENTATION

| File | Purpose | Key Section |
|------|---------|------------|
| `/home/lionel/code/specql/docs/reference/numbering-systems.md` | Complete numbering system guide | Lines 96-107: Table Code Format |
| `/home/lionel/code/specql/docs/reference/yaml-reference.md` | Entity YAML documentation | Lines 320-362: organization section |
| `/home/lionel/code/specql/registry/domain_registry.yaml` | Current subdomain configuration | domains -> subdomains structure |
| `/home/lionel/code/specql/docs/implementation_plans/20251111_135510_issue_6_subdomain_parsing_fix.md` | Issue #6 detailed analysis | Complete subdomain parsing bug report |
| `/home/lionel/code/specql/docs/architecture/SCHEMA_ORGANIZATION_STRATEGY.md` | Schema organization design | Multi-tenant and shared domains |

---

**Complete File Reference Summary**:

- **Parser**: `/home/lionel/code/specql/src/numbering/numbering_parser.py` (lines 10-100)
- **Generator**: `/home/lionel/code/specql/src/generators/schema/naming_conventions.py` (entire file)
- **Registry**: `/home/lionel/code/specql/registry/domain_registry.yaml` (entire file)
- **Entity Example**: `/home/lionel/code/specql/entities/examples/manufacturer.yaml` (lines 1-50)
- **Tests**: `/home/lionel/code/specql/tests/unit/numbering/test_numbering_parser.py`
- **Integration Tests**: `/home/lionel/code/specql/tests/integration/test_issue_6_subdomain_parsing.py`
- **Documentation**: `/home/lionel/code/specql/docs/reference/numbering-systems.md`
