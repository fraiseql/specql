# Snake_case Conversion Examples - Issue #6 Phase 4.5

This document shows how various entity names will be converted to snake_case.

## Conversion Algorithm

```python
def camel_to_snake(name: str) -> str:
    """
    1. Insert underscore before uppercase letters preceded by lowercase
    2. Insert underscore before uppercase letters preceded by digits
    3. Lowercase the entire result
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()
```

---

## Common Entity Names

### Simple CamelCase (Most Common)

| Entity Name | Snake_case | Directory Example |
|-------------|-----------|-------------------|
| `Contact` | `contact` | `01231_contact/` |
| `Company` | `company` | `01232_company/` |
| `User` | `user` | `01233_user/` |
| `Product` | `product` | `01331_product/` |

### Multi-word CamelCase (Very Common)

| Entity Name | Snake_case | Directory Example |
|-------------|-----------|-------------------|
| `ColorMode` | `color_mode` | `01311_color_mode/` |
| `DuplexMode` | `duplex_mode` | `01312_duplex_mode/` |
| `MachineFunction` | `machine_function` | `01313_machine_function/` |
| `ManufacturerRange` | `manufacturer_range` | `01323_manufacturer_range/` |
| `ItemCategory` | `item_category` | `01312_item_category/` |
| `SalesOpportunity` | `sales_opportunity` | `01221_sales_opportunity/` |
| `CustomerAccount` | `customer_account` | `01231_customer_account/` |
| `EmailTemplate` | `email_template` | `01251_email_template/` |

### With Numbers (Less Common)

| Entity Name | Snake_case | Explanation |
|-------------|-----------|-------------|
| `Product2B` | `product_2_b` | Number + uppercase letter separated |
| `Level3Support` | `level_3_support` | Number in middle |
| `Tier1Customer` | `tier_1_customer` | Number between words |
| `Plan2023` | `plan_2023` | Trailing number |
| `Model3D` | `model_3_d` | Number + uppercase letter |

### Acronyms (Rare but Important)

| Entity Name | Snake_case | Explanation |
|-------------|-----------|-------------|
| `HTTPServer` | `http_server` | Acronym followed by word |
| `XMLParser` | `xml_parser` | Acronym followed by word |
| `URLShortener` | `url_shortener` | Acronym followed by word |
| `PDFDocument` | `pdf_document` | Acronym in middle |
| `IPv4Address` | `i_pv_4_address` | Complex: each component separated |
| `API` | `api` | Acronym only |
| `URL` | `url` | Acronym only |

### Edge Cases

| Entity Name | Snake_case | Note |
|-------------|-----------|------|
| `color_mode` | `color_mode` | Already snake_case - pass through |
| `PRODUCT` | `product` | All caps - lowercase |
| `A` | `a` | Single letter |
| `AB` | `ab` | Two letters - no separator needed |
| `ABC` | `abc` | Three letters - no separator needed |
| `ABc` | `a_bc` | Acronym + lowercase |

---

## PrintOptim Catalog Examples (Real World)

### Classification Subdomain (code 1)

| Entity Name | Table Code | Snake_case | Full Path |
|-------------|-----------|-----------|-----------|
| `ColorMode` | `013111` | `color_mode` | `0131_classification/01311_color_mode/` |
| `DuplexMode` | `013121` | `duplex_mode` | `0131_classification/01312_duplex_mode/` |
| `MachineFunction` | `013131` | `machine_function` | `0131_classification/01313_machine_function/` |
| `PaperSize` | `013141` | `paper_size` | `0131_classification/01314_paper_size/` |
| `MediaType` | `013151` | `media_type` | `0131_classification/01315_media_type/` |

### Manufacturer Subdomain (code 2)

| Entity Name | Table Code | Snake_case | Full Path |
|-------------|-----------|-----------|-----------|
| `Manufacturer` | `013211` | `manufacturer` | `0132_manufacturer/01321_manufacturer/` |
| `ManufacturerRange` | `013221` | `manufacturer_range` | `0132_manufacturer/01322_manufacturer_range/` |
| `Model` | `013231` | `model` | `0132_manufacturer/01323_model/` |
| `Accessory` | `013241` | `accessory` | `0132_manufacturer/01324_accessory/` |

---

## File Naming Examples

### Table Files

```
Entity: ColorMode
Directory: 01311_color_mode/
File: 013111_tb_color_mode.sql

Entity: DuplexMode
Directory: 01312_duplex_mode/
File: 013121_tb_duplex_mode.sql
```

### Function Files

```
Entity: ColorMode
Action: activate_mode
File: 013111_fn_color_mode_activate_mode.sql

Entity: MachineFunction
Action: enable_function
File: 013131_fn_machine_function_enable_function.sql
```

### Helper Files

```
Entity: ColorMode
File: color_mode_helpers.sql

Entity: ManufacturerRange
File: manufacturer_range_helpers.sql
```

---

## Comparison: Before vs After Phase 4.5

### Before (lowercase only, with _group)

```
0131_classification/
  ├── 01311_colormode_group/          ❌ No underscores, has _group
  │   └── 013111_tb_colormode.sql
  ├── 01312_duplexmode_group/         ❌ No underscores, has _group
  │   └── 013121_tb_duplexmode.sql
  └── 01313_machinefunction_group/    ❌ No underscores, has _group
      └── 013131_tb_machinefunction.sql
```

### After (snake_case, no _group)

```
0131_classification/
  ├── 01311_color_mode/               ✅ Snake_case, no _group
  │   └── 013111_tb_color_mode.sql
  ├── 01312_duplex_mode/              ✅ Snake_case, no _group
  │   └── 013121_tb_duplex_mode.sql
  └── 01313_machine_function/         ✅ Snake_case, no _group
      └── 013131_tb_machine_function.sql
```

---

## Why Snake_case?

### 1. **Consistency**
PostgreSQL convention is snake_case for table/column names:
```sql
CREATE TABLE tb_color_mode (...);  -- Matches directory name
```

### 2. **Readability**
```
color_mode          ✅ Clear word boundaries
colormode           ❌ Harder to read
```

### 3. **Framework Standard**
The PostgreSQL adapter specifies `naming_case="snake_case"`:
```python
adapter = PostgreSQLAdapter(naming_case="snake_case")
```

### 4. **Industry Standard**
- Python: snake_case for functions/variables
- PostgreSQL: snake_case for identifiers
- REST APIs: snake_case for JSON keys (common)

---

## Special Cases to Note

### Numbers Create Boundaries

```
Product2B → product_2_b (NOT product_2b)
```

This is intentional because:
1. **Clarity**: `product_2_b` is more explicit
2. **Consistency**: Treats digits like uppercase letters
3. **Safety**: Avoids ambiguity (is it "2b" or "2" + "b"?)

### Acronyms Split Completely

```
HTTPServer → http_server
IPv4Address → i_pv_4_address
```

This is a trade-off:
- **Pro**: Algorithmic consistency, no special cases
- **Con**: `i_pv_4_address` is verbose

For most business entities (ColorMode, DuplexMode, etc.), this isn't an issue.

### Already Snake_case Pass Through

```python
if "_" in name and name.islower():
    return name  # No conversion needed
```

This prevents double-conversion and supports migrations.

---

## Testing Your Entity Names

Quick test in Python:

```python
import re

def camel_to_snake(name: str) -> str:
    if "_" in name and name.islower():
        return name
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()

# Test your entity names
print(camel_to_snake("YourEntity"))
print(camel_to_snake("ColorMode"))
print(camel_to_snake("Product2B"))
```

---

## Migration Impact

### Low Impact ✅
- New projects starting with v0.2.1
- Regenerating with `--output-format hierarchical`

### Medium Impact ⚠️
- Existing scripts referencing old paths
- Need to update path patterns:
  ```bash
  # Old
  generated/**/colormode_group/

  # New
  generated/**/color_mode/
  ```

### No Impact ✅
- SQL generation (unchanged)
- Database schema (unchanged)
- Confiture format (already flat, no hierarchy)

---

**Recommendation**: Use clear, multi-word CamelCase entity names (e.g., `ColorMode`, `DuplexMode`) which convert beautifully to snake_case. Avoid complex acronyms or numbers in entity names when possible.

---

*Part of Issue #6 Phase 4.5 - Snake_case Conversion*
*Last Updated: 2025-11-11*
