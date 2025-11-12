# Current vs Target: Visual Comparison

## File Structure Comparison

### CURRENT: Monolithic Single File

```
specql_output/
├── 100_schema.sql
├── 110_tables.sql
├── 120_indexes.sql
├── 130_functions.sql
└── 200_table_views.sql          ← ALL tv_* tables here
    ├── -- Table View: crm.tv_contact
    ├── CREATE TABLE crm.tv_contact ...
    ├── CREATE INDEX idx_tv_contact_tenant ...
    ├── CREATE FUNCTION crm.refresh_tv_contact() ...
    ├── COMMENT ON TABLE crm.tv_contact ...
    ├──
    ├── -- Table View: crm.tv_company
    ├── CREATE TABLE crm.tv_company ...
    ├── CREATE INDEX idx_tv_company_tenant ...
    ├── CREATE FUNCTION crm.refresh_tv_company() ...
    └── COMMENT ON TABLE crm.tv_company ...
```

**Problems**:
- ❌ Hard to navigate (all entities mixed)
- ❌ No hierarchical organization
- ❌ Doesn't match write-side structure
- ❌ Poor maintainability for large codebases
- ❌ No code assignment system

---

### TARGET: Hierarchical Organization (Reference System)

```
0_schema/
│
├── 01_write_side/                          ← WRITE SIDE (tables)
│   ├── 012_crm/
│   │   └── 0123_customer/
│   │       ├── 01231_company/
│   │       │   └── 012311_tb_company.sql          Code: 012311
│   │       └── 01236_contact/
│   │           └── 012361_tb_contact.sql          Code: 012361
│   │
│   └── 014_dim/
│       └── 0141_geo/
│           └── 01411_location/
│               ├── 014111_tb_location_info.sql    Code: 014111
│               └── 014112_tb_location.sql         Code: 014112
│
└── 02_query_side/                          ← READ SIDE (views)
    ├── 022_crm/
    │   └── 0223_customer/
    │       ├── 02231_v_company_summary.sql        Code: 02231
    │       ├── 02232_tv_company.sql               Code: 02232 ← tv_!
    │       ├── 02236_v_contact_list.sql           Code: 02236
    │       └── 02237_tv_contact.sql               Code: 02237 ← tv_!
    │
    └── 024_dim/
        └── 0241_geo/
            ├── 02411_v_count_allocations.sql      Code: 02411
            ├── 02412_v_location.sql               Code: 02412
            ├── 02413_tv_location.sql              Code: 02413 ← tv_!
            └── 02414_v_flat_location.sql          Code: 02414
```

**Benefits**:
- ✅ Hierarchical organization by domain/subdomain
- ✅ Write-side and read-side mirror each other
- ✅ Systematic code assignment (01* vs 02*)
- ✅ One file per entity/view
- ✅ Easy navigation and maintenance
- ✅ Scalable to hundreds of entities

---

## Code Assignment Comparison

### CURRENT: Write-Side Only

**Registry Entry** (registry/domain_registry.yaml):
```yaml
domains:
  '2':
    name: crm
    subdomains:
      '03':
        name: customer
        entities:
          Contact:
            table_code: '012036'     # Only write-side code
            entity_code: CNT
```

**Generated Table** (tb_contact.sql):
```sql
COMMENT ON TABLE crm.tb_contact IS
  '[Table: 012036 | Write-Side.CRM.Customer.Contact] ...';
```

**Generated TV_** (200_table_views.sql):
```sql
-- NO CODE ASSIGNMENT!
-- Table View: crm.tv_contact
CREATE TABLE crm.tv_contact (...);
```

---

### TARGET: Write-Side + Read-Side Tracking

**Registry Entry** (enhanced):
```yaml
domains:
  '2':
    name: crm
    subdomains:
      '03':
        name: customer
        next_entity_sequence: 37
        entities:
          Contact:
            # Write-side (01_write_side)
            table_code: '012036'
            entity_code: CNT

            # Read-side (02_query_side)
            tv_base_code: '022037'        # Base code for this entity
            next_tv_file_sequence: 2      # Next file number
            tv_files:
              - code: '0220371'           # First tv_ file
                type: table_view
                name: tv_contact
                path: 02_query_side/022_crm/0223_customer/0220371_tv_contact.sql
```

**Generated TV_** (0220371_tv_contact.sql):
```sql
-- File: 02_query_side/022_crm/0223_customer/0220371_tv_contact.sql

COMMENT ON TABLE crm.tv_contact IS
  '[Table View: 0220371 | Read-Side.CRM.Customer.Contact]
   Denormalized view of contact with company and status enrichment.';

CREATE TABLE crm.tv_contact (...);
CREATE INDEX idx_tv_contact_tenant ...;
CREATE FUNCTION crm.refresh_tv_contact() ...;
```

---

## Code Format Breakdown

### Write-Side Code: `014112`

```
0 1 4 1 1 2
│ │ │ │ │ └─ File sequence (2nd file for this entity)
│ │ │ │ └─── Entity sequence (1st entity in subdomain)
│ │ │ └───── Subdomain code (1 = first subdomain)
│ │ └─────── Domain code (4 = dimensions)
│ └───────── Schema layer (1 = write_side)
└─────────── Always 0 for schema files
```

**Example**: Location table
- `0` = schema file prefix
- `1` = write_side
- `4` = dim (dimensions domain)
- `11` = geo subdomain (position 1)
- `2` = second entity file

---

### Read-Side Code: `024130`

```
0 2 4 1 3 0
│ │ │ │ │ └─ File type (0 = base tv_ file)
│ │ │ │ └─── File sequence in subdomain
│ │ │ └───── Subdomain code (1 = geo)
│ │ └─────── Domain code (4 = dimensions)
│ └───────── Schema layer (2 = read_side) ← KEY DIFFERENCE
└─────────── Always 0 for schema files
```

**Example**: Location table view
- `0` = schema file prefix
- `2` = read_side (vs `1` for write)
- `4` = dim (same domain)
- `13` = file position in geo subdomain
- `0` = base tv_ file

---

## Path Generation Comparison

### CURRENT: Fixed Flat Path

**Code** (src/cli/orchestrator.py:433):
```python
migration = MigrationFile(
    number=200,
    name="table_views",
    content=tv_sql,
    path=output_path / "200_table_views.sql",  # Hardcoded!
)
```

**Output**:
```
output/200_table_views.sql
```

---

### TARGET: Hierarchical Path Generation

**Code** (proposed):
```python
def generate_tv_path(entity: Entity, registry: DomainRegistry) -> Path:
    """
    Generate hierarchical path for tv_ file.

    Example:
      entity.name = "Location"
      entity.domain = "dim" (code: 4)
      entity.subdomain = "geo" (code: 41)
      tv_code = "024130"

    Returns:
      0_schema/02_query_side/024_dim/0241_geo/024130_tv_location.sql
    """
    # Get registry info
    entry = registry.get_entity(entity.name)
    tv_code = entry.tv_base_code + "0"  # Base + file sequence

    # Build path components
    schema_layer = "02_query_side"
    domain_path = f"0{entry.domain_code}{entry.subdomain_code[0]}_{entry.domain_name}"
    subdomain_path = f"0{entry.domain_code}{entry.subdomain_code}_{entry.subdomain_name}"
    filename = f"{tv_code}_tv_{entity.name.lower()}.sql"

    return Path("0_schema") / schema_layer / domain_path / subdomain_path / filename
```

**Output**:
```
0_schema/
└── 02_query_side/
    └── 024_dim/
        └── 0241_geo/
            └── 024130_tv_location.sql
```

---

## Content Comparison

### CURRENT: Concatenated String

**Generated Content** (200_table_views.sql):
```sql
-- Table View: crm.tv_company
CREATE TABLE crm.tv_company (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    name text,
    data jsonb,
    ...
);
CREATE INDEX idx_tv_company_tenant ON crm.tv_company(tenant_id);
CREATE FUNCTION crm.refresh_tv_company() RETURNS void AS $$ ... $$;
COMMENT ON TABLE crm.tv_company IS 'Company table view';

-- Table View: crm.tv_contact
CREATE TABLE crm.tv_contact (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    fk_company INTEGER,        -- JOIN to tb_company
    fk_company_ref uuid,       -- Filter on uuid
    data jsonb,
    ...
);
CREATE INDEX idx_tv_contact_tenant ON crm.tv_contact(tenant_id);
CREATE FUNCTION crm.refresh_tv_contact() RETURNS void AS $$ ... $$;
COMMENT ON TABLE crm.tv_contact IS 'Contact table view';
```

**Issues**:
- Multiple entities mixed together
- No clear separation
- Hard to find specific entity
- No metadata about structure

---

### TARGET: Individual Complete Files

**File 1**: `0_schema/02_query_side/022_crm/0223_customer/0223211_tv_company.sql`
```sql
-- ============================================================================
-- Table View: crm.tv_company
-- Code: 0223211
-- Domain: CRM > Customer
-- Generated: 2025-11-12
-- ============================================================================

CREATE TABLE crm.tv_company (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    identifier text,
    name text,
    data jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE ONLY crm.tv_company ADD CONSTRAINT tv_company_id_key UNIQUE (id);

-- Indexes
CREATE INDEX idx_tv_company_tenant ON crm.tv_company(tenant_id);
CREATE INDEX idx_tv_company_identifier ON crm.tv_company(identifier);
CREATE INDEX idx_tv_company_data_gin ON crm.tv_company USING GIN (data);

-- Refresh Function
CREATE FUNCTION crm.refresh_tv_company() RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    -- Refresh logic here
END;
$$;

-- Metadata
COMMENT ON TABLE crm.tv_company IS
  '[Table View: 0223211 | Read-Side.CRM.Customer.Company]
   Denormalized company data with enriched metadata for GraphQL queries.

   @fraiseql:entity Company
   @fraiseql:domain crm
   @fraiseql:type table_view';

COMMENT ON COLUMN crm.tv_company.id IS 'UUID identifier for company';
COMMENT ON COLUMN crm.tv_company.tenant_id IS 'Multi-tenant isolation key';
COMMENT ON COLUMN crm.tv_company.data IS 'JSONB containing full entity data + relations';

-- Cache Invalidation Trigger
CREATE TRIGGER trg_tv_company_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE ON crm.tv_company
FOR EACH ROW
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation();
```

**File 2**: `0_schema/02_query_side/022_crm/0223_customer/0223612_tv_contact.sql`
```sql
-- ============================================================================
-- Table View: crm.tv_contact
-- Code: 0223612
-- Domain: CRM > Customer
-- Dependencies: tv_company (0223211)
-- Generated: 2025-11-12
-- ============================================================================

CREATE TABLE crm.tv_contact (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    identifier text,
    email text,

    -- Foreign keys (dual: pk_ for JOIN, uuid for filter)
    fk_company INTEGER,        -- JOIN to tb_company.pk_company
    fk_company_ref uuid,       -- Filter on company UUID

    data jsonb,                -- Denormalized data including company
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE ONLY crm.tv_contact ADD CONSTRAINT tv_contact_id_key UNIQUE (id);

-- Indexes
CREATE INDEX idx_tv_contact_tenant ON crm.tv_contact(tenant_id);
CREATE INDEX idx_tv_contact_email ON crm.tv_contact(email);
CREATE INDEX idx_tv_contact_fk_company ON crm.tv_contact(fk_company);
CREATE INDEX idx_tv_contact_data_gin ON crm.tv_contact USING GIN (data);

-- Refresh Function (joins to tv_company, not tb_company!)
CREATE FUNCTION crm.refresh_tv_contact() RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    TRUNCATE crm.tv_contact;

    INSERT INTO crm.tv_contact (id, tenant_id, identifier, email, fk_company, fk_company_ref, data)
    SELECT
        c.pk_contact AS id,
        c.tenant_id,
        c.identifier,
        c.email,
        c.fk_company,
        tc.id AS fk_company_ref,
        jsonb_build_object(
            'id', c.pk_contact,
            'email', c.email,
            'company', tc.data  -- Denormalized from tv_company!
        ) AS data
    FROM crm.tb_contact c
    LEFT JOIN crm.tv_company tc ON tc.fk_company_pk = c.fk_company
    WHERE c.deleted_at IS NULL;
END;
$$;

-- Metadata
COMMENT ON TABLE crm.tv_contact IS
  '[Table View: 0223612 | Read-Side.CRM.Customer.Contact]
   Denormalized contact data with company enrichment.

   @fraiseql:entity Contact
   @fraiseql:domain crm
   @fraiseql:type table_view
   @fraiseql:depends_on tv_company';

-- Cache Invalidation Trigger
CREATE TRIGGER trg_tv_contact_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE ON crm.tv_contact
FOR EACH ROW
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation();
```

**Benefits**:
- ✅ Complete entity definition in one file
- ✅ Clear dependency documentation
- ✅ Comprehensive metadata
- ✅ Easy to review and maintain
- ✅ File can be version controlled independently

---

## Registry Comparison

### CURRENT: No TV_ Tracking

```yaml
# registry/domain_registry.yaml
domains:
  '2':
    name: crm
    subdomains:
      '03':
        name: customer
        next_entity_sequence: 37
        entities:
          Contact:
            table_code: '012036'
            entity_code: CNT
            assigned_at: '2025-11-10T12:33:27'
          # No tv_ information!
```

**Problems**:
- No tv_ code tracking
- No file sequence management
- Can't reconstruct paths from registry
- No audit trail for tv_ files

---

### TARGET: Complete Tracking

```yaml
# registry/domain_registry.yaml (enhanced)
domains:
  '2':
    name: crm
    multi_tenant: true
    subdomains:
      '03':
        name: customer
        next_entity_sequence: 37      # For new entities
        next_tv_file_sequence: 15     # For new tv_ files in subdomain
        entities:
          Contact:
            # Write-side
            table_code: '012036'
            entity_code: CNT
            assigned_at: '2025-11-10T12:33:27'

            # Read-side
            tv_base_code: '022037'      # Derived from table_code
            tv_assigned_at: '2025-11-12T14:22:15'
            tv_files:
              - code: '0220371'
                type: table_view
                name: tv_contact
                path: 02_query_side/022_crm/0223_customer/0220371_tv_contact.sql
                depends_on:
                  - tv_company
                assigned_at: '2025-11-12T14:22:15'

              # Future: Additional views for same entity
              - code: '0220372'
                type: regular_view
                name: v_contact_summary
                path: 02_query_side/022_crm/0223_customer/0220372_v_contact_summary.sql
                assigned_at: '2025-11-12T15:30:00'
```

**Benefits**:
- ✅ Complete audit trail
- ✅ Dependency tracking
- ✅ Path reconstruction
- ✅ File sequence management
- ✅ Extensible for multiple views per entity

---

## Summary Table

| Aspect | Current | Target |
|--------|---------|--------|
| **File Structure** | Single flat file | Hierarchical by domain/subdomain |
| **File Count** | 1 file (200_table_views.sql) | 1 file per entity |
| **Code Assignment** | No codes for tv_ | Systematic 02* codes |
| **Registry Tracking** | Write-side only | Write + read-side |
| **Navigation** | Search within file | Directory hierarchy |
| **Maintainability** | Poor (large files) | Excellent (small focused files) |
| **Scalability** | Degrades with size | Scales to hundreds of entities |
| **Dependencies** | Implicit (order) | Explicit (metadata + path) |
| **Version Control** | Monolithic diffs | Granular per-entity diffs |
| **Consistency** | Doesn't match write-side | Mirrors write-side structure |

---

**Next**: See full implementation plan in `20251112_hierarchical_view_organization.md`
