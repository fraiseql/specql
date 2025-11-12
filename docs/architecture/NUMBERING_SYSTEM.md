# Numbering System Architecture

## Overview

SpecQL uses a unified 6-digit hexadecimal numbering system (SDSEX) for all database objects across write-side, read-side, and function layers.

## Format Specification

### SDSEX: 6-Digit Unified Code

```
SDSEX
││││││
│││││└─ X: File Sequence (0-9) - distinguishes multiple files for same entity
││││└── E: Entity Sequence (0-9) - distinguishes entities within subdomain
│││└─── S: Subdomain Code (0-9) - distinguishes subdomains within domain
││└──── D: Domain Code (0-9) - distinguishes domains
│└───── S: Schema Layer (01=write, 02=read, 03=functions)
└────── S: Schema Layer (01=write, 02=read, 03=functions)
```

### Digit Allocation

- **SS (Schema Layer)**: 2 digits
  - `01`: Write-side (tables, constraints, indexes)
  - `02`: Read-side (views, materialized views)
  - `03`: Functions (stored procedures, triggers)

- **D (Domain)**: 1 digit (0-9)
  - `1`: core
  - `2`: crm
  - `3`: catalog
  - `4`: projects
  - `5`: analytics
  - `6`: finance

- **S (Subdomain)**: 1 digit (0-9)
  - Max 10 subdomains per domain
  - Examples: `customer`, `core`, `manufacturer`, etc.

- **E (Entity)**: 1 digit (0-9)
  - Max 10 entities per subdomain
  - Auto-assigned sequentially

- **X (File)**: 1 digit (0-9)
  - `1`: Main table/view/function
  - `2`: Helpers, audit tables, etc.
  - `3+`: Additional files

## Directory Structure

Each level adds exactly one digit, creating a progressive hierarchy:

```
0_schema/
├── 01_write_side/           (2 digits: SS)
│   ├── 012_crm/             (3 digits: SS+D)
│   │   ├── 0123_customer/   (4 digits: SS+D+S)
│   │   │   ├── 01232_contact/  (5 digits: SS+D+S+E)
│   │   │   │   ├── 012321_tb_contact.sql     (6 digits: SS+D+S+E+X)
│   │   │   │   ├── 012322_tb_contact_audit.sql
│   │   │   │   └── 012323_fn_contact_create.sql
│   │   │   └── 01231_company/
│   │   │       └── 012311_tb_company.sql
│   │   └── 0121_core/
│   │       └── 01211_user/
│   │           └── 012111_tb_user.sql
│   └── 013_catalog/
│       └── 0132_manufacturer/
│           └── 01321_product/
│               └── 013211_tb_product.sql
├── 02_query_side/          (read-side views)
│   └── 022_crm/
│       └── 0223_customer/
│           └── 02232_contact/
│               └── 022321_v_contact.sql
└── 03_functions/           (stored functions)
    └── 032_crm/
        └── 0323_customer/
            └── 03232_contact/
                └── 032321_fn_update_contact.sql
```

## Code Examples

### Write-Side Table
```yaml
entity: Contact
schema: crm
subdomain: customer
table_code: "012321"  # 01=write, 2=crm, 3=customer, 2=contact_entity, 1=main_table
```

**Generated Path**: `01_write_side/012_crm/0123_customer/01232_contact/012321_tb_contact.sql`

### Read-Side View
```yaml
# Auto-derived from table_code "012321"
view_code: "022321"  # 02=read, 2=crm, 3=customer, 2=contact_entity, 1=main_view
```

**Generated Path**: `02_query_side/022_crm/0223_customer/02232_contact/022321_v_contact.sql`

### Function
```yaml
# Auto-derived from table_code "012321"
function_code: "032321"  # 03=functions, 2=crm, 3=customer, 2=contact_entity, 1=main_function
```

**Generated Path**: `03_functions/032_crm/0323_customer/03232_contact/032321_fn_update_contact.sql`

## Migration from 7-Digit System

The previous system used 7-digit codes (SSDSSEX) with 2-digit subdomains. The new system:

- **Removes** the 7th digit (file sequence was always "1")
- **Converts** 2-digit subdomains to 1-digit (drop leading zero)
- **Maintains** all other semantics

### Migration Examples

| Old (7-digit) | New (6-digit) | Description |
|---------------|---------------|-------------|
| `0120391` | `012321` | Contact table (crm.customer subdomain) |
| `0120191` | `012121` | Order table (crm.core subdomain) |
| `0130291` | `013021` | Manufacturer table (catalog.manufacturer) |

### Registry Updates

Subdomain codes in `registry/domain_registry.yaml` changed from 2-digit to 1-digit:

```yaml
# Before
domains:
  '2':
    subdomains:
      '01': {name: core}
      '03': {name: customer}

# After
domains:
  '2':
    subdomains:
      '1': {name: core}
      '3': {name: customer}
```

## Benefits

1. **Unified Length**: All codes are exactly 6 digits
2. **Progressive Structure**: Each directory level adds exactly 1 digit
3. **Scalable**: 10 domains × 10 subdomains × 10 entities × 10 files = 10,000 objects per schema layer
4. **Compatible**: Works with UUID encoding requirements
5. **Consistent**: Same structure across write-side, read-side, and functions

## Validation Rules

- Must be exactly 6 hexadecimal digits (0-9, a-f)
- Schema layer must be `01`, `02`, or `03`
- Domain code must exist in registry
- Subdomain code must exist for the domain
- Entity sequence must be valid for the subdomain

## Implementation Notes

- **Parser**: `src/numbering/numbering_parser.py`
- **Registry**: `registry/domain_registry.yaml`
- **Generators**: `src/generators/schema/naming_conventions.py`
- **Path Logic**: `src/generators/schema/*_path_generator.py`</content>
</xai:function_call">Create the NUMBERING_SYSTEM.md documentation file