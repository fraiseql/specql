# SpecQL YAML Complete Reference

## Table of Contents
1. Entity Structure Overview
2. Top-Level Fields
3. Fields Section
4. Actions Section
5. Organization Metadata
6. Table Views (CQRS Read Layer)
7. Advanced Features
8. Auto-Generated Features
9. Examples Section
10. Reference

## 1. Entity Structure Overview
[Minimal example with all sections]

## 2. Top-Level Fields

### Required Fields
- `entity` (string, PascalCase)
  - Description: Entity name
  - Example: `entity: Contact`
  - Rules: Must be PascalCase, must be unique in schema

- `schema` (string, snake_case)
  - Description: PostgreSQL schema name
  - Example: `schema: crm`
  - Rules: Must be registered in domain registry

- `fields` (object)
  - Description: Field definitions
  - See Fields Section below

### Optional Fields
- `description` (string)
  - Purpose: Entity documentation
  - Example: `description: "Customer contact information"`
  - Impact: Added as PostgreSQL comment

- `organization` (object)
  - Purpose: Advanced metadata for migrations
  - See Organization Metadata section
  - When to use: Migrating from existing systems with numbering

- `actions` (array)
  - Purpose: Business logic definitions
  - See Actions Section

- `translations` (array)
  - Purpose: i18n support
  - Status: Implemented
  - Reference: docs/guides/i18n-guide.md (if exists)

- `hierarchical` (boolean)
  - Purpose: Enable hierarchical identifiers
  - Default: false
  - Reference: docs/guides/hierarchical-entities.md

## 3. Fields Section

### Scalar Types

#### text
- SQL Type: TEXT
- Use for: Free-form text, names, descriptions
- Example: `name: text`
- Auto-generated features: None
- Validation: None (use rich types for validated text)

#### integer
- SQL Type: INTEGER
- Use for: Whole numbers, counts, quantities
- Example: `quantity: integer`
- Auto-generated features: None
- Validation: Must be whole number

#### decimal
- SQL Type: NUMERIC
- Use for: Monetary values, precise calculations
- Example: `price: decimal`
- Auto-generated features: None
- Validation: Precision depends on PostgreSQL defaults

#### boolean
- SQL Type: BOOLEAN
- Use for: True/false flags
- Example: `is_active: boolean`
- Auto-generated features: None
- Validation: Must be true/false

#### timestamp
- SQL Type: TIMESTAMP WITH TIME ZONE
- Use for: Precise date-time values
- Example: `delivered_at: timestamp`
- Auto-generated features: None (except created_at/updated_at)
- Validation: ISO 8601 format

#### date
- SQL Type: DATE
- Use for: Dates without time component
- Example: `birthday: date`
- Auto-generated features: None
- Validation: YYYY-MM-DD format

#### json
- SQL Type: JSONB
- Use for: Semi-structured data, flexible schemas
- Example: `metadata: json`
- Auto-generated features: GIN index
- Validation: Must be valid JSON

### Rich Types (Composite Types)

#### email
- SQL Type: app.email (composite)
- Use for: Email addresses
- Example: `contact_email: email`
- Structure: `{address: TEXT, display_name: TEXT}`
- Validation: Basic email format

#### phone
- SQL Type: app.phone (composite)
- Use for: Phone numbers
- Example: `mobile: phone`
- Structure: `{country_code: TEXT, number: TEXT, extension: TEXT}`
- Validation: None (international format varies)

#### money
- SQL Type: app.money (composite)
- Use for: Monetary values with currency
- Example: `total_amount: money`
- Structure: `{amount: NUMERIC, currency: TEXT}`
- Validation: ISO 4217 currency codes

#### dimensions
- SQL Type: app.dimensions (composite)
- Use for: Physical measurements
- Example: `package_size: dimensions`
- Structure: `{length: NUMERIC, width: NUMERIC, height: NUMERIC, unit: TEXT}`
- Validation: None

#### contact_info
- SQL Type: app.contact_info (composite)
- Use for: Complete contact details
- Example: `primary_contact: contact_info`
- Structure: `{email: email, phone: phone, address: address}`
- Validation: Validates nested types

### Relational Types

#### ref(Entity)
- SQL Type: INTEGER (FK to tb_entity.id)
- Use for: Foreign key relationships
- Example: `company: ref(Company)`
- Auto-generated features:
  - Foreign key constraint: `fk_tb_contact_company`
  - Index: `idx_tb_contact_company`
  - ON DELETE RESTRICT by default
- Validation: Referenced entity must exist

#### enum(value1, value2, ...)
- SQL Type: TEXT with CHECK constraint
- Use for: Fixed set of values
- Example: `status: enum(lead, qualified, customer)`
- Auto-generated features:
  - CHECK constraint
  - Index: `idx_tb_contact_status`
- Validation: Must be one of listed values

#### list(Type)
- SQL Type: Type[] (PostgreSQL array)
- Use for: Multiple values of same type
- Example: `tags: list(text)`
- Auto-generated features: GIN index
- Validation: All elements must be valid Type

### Field Modifiers

#### nullable
- Syntax: `field: text?` or `field: "text | null"`
- Effect: Field can be NULL
- Default: All fields are NOT NULL
- Example: `middle_name: text?`

#### required (default)
- Syntax: `field: text` (no modifier)
- Effect: Field must have value
- Example: `email: text`

## 4. Actions Section

### Action Structure
```yaml
actions:
  - name: action_name
    description: "What this action does"
    impacts:
      entities: [Entity1, Entity2]
      read: [Entity3]
      write: [Entity1]
    steps:
      - [step definitions]
```

### Step Types

#### validate
- Purpose: Check preconditions
- Syntax: `validate: <expression>`
- Example: `validate: status = 'draft'`
- On failure: Returns error, halts execution
- Expression syntax: SQL WHERE clause

#### if
- Purpose: Conditional branching
- Syntax:
  ```yaml
  - if: <condition>
    then:
      - [steps]
    else:
      - [steps]
  ```
- Example:
  ```yaml
  - if: amount > 1000
    then:
      - update: Order SET requires_approval = true
    else:
      - update: Order SET approved = true
  ```

#### insert
- Purpose: Create new record
- Syntax: `insert: Entity [SET field = value, ...]`
- Example: `insert: AuditLog SET action = 'created'`
- Returns: Complete inserted object
- Auto-generated: id, created_at, created_by

#### update
- Purpose: Modify existing record
- Syntax: `update: Entity SET field = value [WHERE condition]`
- Example: `update: Contact SET status = 'qualified' WHERE id = :contact_id`
- Returns: Updated object
- Auto-generated: updated_at, updated_by

#### soft_delete
- Purpose: Mark record as deleted
- Syntax: `soft_delete: Entity [WHERE condition]`
- Example: `soft_delete: Contact WHERE id = :id`
- Effect: Sets deleted_at = NOW(), deleted_by = current_user
- Returns: Deleted object

#### call
- Purpose: Invoke another action
- Syntax: `call: schema.action_name(param1: value1, ...)`
- Example: `call: crm.send_welcome_email(contact_id: :id)`
- Returns: Result from called action

#### notify
- Purpose: Send notification/event
- Syntax: `notify: channel WITH payload`
- Example: `notify: contact_created WITH {contact_id: :id}`
- Effect: PostgreSQL NOTIFY

#### foreach
- Purpose: Loop over collection
- Syntax:
  ```yaml
  - foreach: item IN <collection>
    do:
      - [steps with :item available]
  ```
- Example:
  ```yaml
  - foreach: line IN order_lines
    do:
      - update: Product SET stock = stock - :line.quantity WHERE id = :line.product_id
  ```

### Expression Syntax

#### Variables
- `:param_name` - Input parameter
- `:item.field` - Foreach item field
- `CURRENT_TIMESTAMP` - Current time
- `CURRENT_USER` - Current user UUID

#### Operators
- Comparison: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `AND`, `OR`, `NOT`
- Null: `IS NULL`, `IS NOT NULL`
- Pattern: `LIKE`, `ILIKE`
- Membership: `IN (value1, value2)`

#### Functions
- String: `LOWER()`, `UPPER()`, `TRIM()`
- Date: `NOW()`, `CURRENT_DATE`
- Math: `ABS()`, `ROUND()`
- Aggregation: Use subqueries

## 5. Organization Metadata

### Purpose
Advanced metadata for migrations and hierarchical output structure.

### When to Use
- ✅ Migrating from existing system with file numbering (e.g., `012311_tb_contact.sql`)
- ✅ Generating hierarchical directory structure with `--output-format hierarchical`
- ✅ Maintaining traceability to legacy database code
- ❌ New projects (not needed)
- ❌ Simple prototypes

### Fields

#### table_code
- Type: string (6-character hex)
- Format: `[0-9A-F]{6}`
- Example: `table_code: "012311"`
- Purpose: Unique identifier for migration files
- Validation: Must be unique across all entities
- Check with: `specql check-codes entities/**/*.yaml`

#### domain
- Type: string
- Example: `domain: "CRM"`
- Purpose: High-level business domain classification
- Use: Documentation and organization

#### subdomain
- Type: string
- Example: `subdomain: "Customer Management"`
- Purpose: Functional area within domain
- Use: Documentation and hierarchical structure

### Example
```yaml
entity: Contact
schema: crm
organization:
  table_code: "012311"
  domain: "CRM"
  subdomain: "Customer"
fields:
  email: text
```

### Output Impact
With `--output-format hierarchical`:
```
db/schema/10_tables/
└── CRM/
    └── Customer/
        └── 012311_contact.sql
```

Without (default flat):
```
db/schema/10_tables/
└── contact.sql
```

## 6. Table Views (CQRS Read Layer)

### Overview
Table views (`tv_*`) are SpecQL's CQRS read layer - denormalized tables with JSONB payloads optimized for FraiseQL/GraphQL queries.

**Purpose**: Compose related entity data into pre-built JSONB objects for high-performance reads.

**Use Cases**:
- GraphQL API integration (FraiseQL auto-discovery)
- Read-heavy workloads
- Dashboard data with multiple related entities
- Pre-composed data for frontend consumption

**Architecture**:
```
tb_contract (Write) → refresh_tv_contract() → tv_contract (Read) → FraiseQL → GraphQL
```

### Configuration Structure

```yaml
table_views:
  mode: auto|force|disable

  include_relations:
    - EntityName:
        fields: [field1, field2, ...] | ["*"]
        include_relations: [...]  # Optional nested

  extra_filter_columns:
    - name: column_name
      type: SQL_TYPE
      index_type: btree|gin|...
```

### Field Reference

#### mode (optional)
- **Type**: `auto` | `force` | `disable`
- **Default**: `auto`
- **Description**: Controls table view generation
  - `auto`: Generate if `include_relations` present
  - `force`: Always generate (even without includes)
  - `disable`: Skip generation entirely

**Example**:
```yaml
table_views:
  mode: force  # Generate tv_contract even without includes
```

#### include_relations (array, optional)
- **Type**: Array of entity composition configurations
- **Purpose**: Compose JSONB from related entity table views
- **Key Feature**: Composes from `tv_*` tables (already denormalized), not `tb_*` tables

**Wildcard Composition** (automatic field inclusion):
```yaml
table_views:
  include_relations:
    - Organization:
        fields: ["*"]  # All fields from tv_organization.data
```

**Explicit Field Selection**:
```yaml
table_views:
  include_relations:
    - Organization:
        fields: [name, code, identifier]  # Only these fields
```

**Nested Composition** (multi-level relationships):
```yaml
table_views:
  include_relations:
    - Book:
        fields: [title, isbn]
        include_relations:
          - Publisher:
              fields: [name]
              include_relations:
                - Country:
                    fields: [name, code]
```

**Generated JSONB Structure**:
```json
{
  "book": {
    "title": "Clean Code",
    "isbn": "978-0132350884",
    "publisher": {
      "name": "Prentice Hall",
      "country": {
        "name": "United States",
        "code": "US"
      }
    }
  }
}
```

#### extra_filter_columns (array, optional)
- **Type**: Array of column configurations
- **Purpose**: Promote fields outside JSONB for fast btree index filtering
- **Use Cases**:
  - Status/enum fields with frequent WHERE clauses
  - Date ranges (created_at, effective_date)
  - Numeric comparisons (amount > X)
  - Foreign key UUIDs for JOIN conditions

**Configuration**:
```yaml
table_views:
  extra_filter_columns:
    - name: status
      type: TEXT
      index_type: btree

    - name: created_at
      type: TIMESTAMPTZ
      index_type: btree

    - name: total_amount
      type: NUMERIC
      index_type: btree
```

**Generated SQL**:
```sql
CREATE TABLE tenant.tv_contract (
    pk_contract INTEGER PRIMARY KEY,
    id UUID NOT NULL,

    -- Extra filter columns (promoted for fast queries)
    status TEXT,
    created_at TIMESTAMPTZ,
    total_amount NUMERIC,

    -- Full JSONB payload
    data JSONB NOT NULL
);

-- Fast btree indexes
CREATE INDEX idx_tv_contract_status ON tenant.tv_contract(status);
CREATE INDEX idx_tv_contract_created ON tenant.tv_contract(created_at);
CREATE INDEX idx_tv_contract_amount ON tenant.tv_contract(total_amount);
```

**Performance Benefit**:
```sql
-- Fast: Uses btree index on status column
SELECT * FROM tenant.tv_contract WHERE status = 'active';

-- Slower: Uses GIN index on JSONB column
SELECT * FROM tenant.tv_contract WHERE data->>'status' = 'active';
```

### Cross-Schema Composition

**Problem**: Entities reference other entities in different schemas.

**Solution**: Schema resolution is automatic - just declare schema in field definition.

```yaml
entity: Contract
schema: tenant

fields:
  # Declare schemas for cross-schema references
  customer_org:
    type: ref(Organization)
    schema: management  # ← Schema declared here

  currency:
    type: ref(Currency)
    schema: catalog  # ← Different schema

table_views:
  include_relations:
    # NO schema needed - auto-resolved via domain registry
    - Organization:  # Resolves to management.tv_organization
        fields: ["*"]

    - Currency:  # Resolves to catalog.tv_currency
        fields: [iso_code, symbol, name]
```

**How It Works**:
1. Field declaration captures schema: `schema: management`
2. Domain registry maps entity names to schemas
3. Generator creates correct cross-schema JOINs automatically

**Generated SQL**:
```sql
-- Automatic cross-schema JOINs
LEFT JOIN management.tv_organization
    ON tb.fk_customer_org = tv_organization.pk_organization
LEFT JOIN catalog.tv_currency
    ON tb.fk_currency = tv_currency.pk_currency
```

### Wildcard vs Explicit Fields

| Aspect | Wildcard `["*"]` | Explicit `[a, b, c]` |
|--------|-----------------|---------------------|
| Maintenance | ✅ Zero - auto-updates | ❌ Manual field list updates |
| Payload Size | Larger (~2x) | Smaller (selective) |
| Use Case | Internal entities | External APIs, mobile |
| DRY | ✅ Yes | ❌ No (repeated lists) |
| Sensitive Data | ⚠️ May include PII | ✅ Can filter out PII |

**Recommendation**: Start with wildcards, optimize to explicit only if profiling shows payload size issues.

### Complete Example

```yaml
entity: Contract
schema: tenant
description: Multi-tenant contract with cross-schema references

fields:
  # Management schema (shared across tenants)
  customer_org:
    type: ref(Organization)
    schema: management

  provider_org:
    type: ref(Organization)
    schema: management

  # Catalog schema (reference data)
  currency:
    type: ref(Currency)
    schema: catalog

  # Contract fields
  contract_number: text
  start_date: date
  end_date: date
  total_amount: decimal
  status: enum(draft, active, expired, cancelled)

# CQRS read layer configuration
table_views:
  mode: auto

  # Compose from related table views
  include_relations:
    # Wildcard composition - zero maintenance
    - Organization:
        fields: ["*"]  # All Organization fields

    # Explicit composition - selective fields
    - Currency:
        fields: [iso_code, symbol, name, decimal_places]

  # Promote hot-path fields for fast filtering
  extra_filter_columns:
    - name: status
      type: TEXT
      index_type: btree

    - name: start_date
      type: DATE
      index_type: btree

    - name: end_date
      type: DATE
      index_type: btree

actions:
  - name: create
    description: Create a new contract

  - name: activate
    description: Activate a draft contract
    steps:
      - validate: status = 'draft'
      - update: Contract SET status = 'active'
```

**Generated Table Structure**:
```sql
CREATE TABLE tenant.tv_contract (
    -- Trinity pattern
    pk_contract INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,

    -- Foreign keys (INTEGER for JOINs during refresh)
    fk_customer_org INTEGER NOT NULL,
    fk_provider_org INTEGER NOT NULL,
    fk_currency INTEGER NOT NULL,

    -- UUID foreign keys (for external filtering)
    customer_org_id UUID NOT NULL,
    provider_org_id UUID NOT NULL,
    currency_id UUID NOT NULL,

    -- Extra filter columns (promoted for performance)
    status TEXT,
    start_date DATE,
    end_date DATE,

    -- Denormalized JSONB payload
    data JSONB NOT NULL,

    -- Metadata
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_tv_contract_tenant ON tenant.tv_contract(tenant_id);
CREATE INDEX idx_tv_contract_customer ON tenant.tv_contract(customer_org_id);
CREATE INDEX idx_tv_contract_currency ON tenant.tv_contract(currency_id);
CREATE INDEX idx_tv_contract_status ON tenant.tv_contract(status);
CREATE INDEX idx_tv_contract_start ON tenant.tv_contract(start_date);
CREATE INDEX idx_tv_contract_end ON tenant.tv_contract(end_date);
CREATE INDEX idx_tv_contract_data ON tenant.tv_contract USING GIN(data);
```

**Generated JSONB Structure** (`tv_contract.data`):
```json
{
  "contract_number": "CT-2025-001",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "total_amount": "150000.00",
  "status": "active",
  "customer_org": {
    "id": "uuid-123",
    "name": "Acme Corp",
    "code": "ACME",
    "identifier": "ORG-ACME",
    "... all other Organization fields ..."
  },
  "provider_org": {
    "... all Organization fields ..."
  },
  "currency": {
    "iso_code": "USD",
    "symbol": "$",
    "name": "US Dollar",
    "decimal_places": 2
  }
}
```

### Performance Characteristics

**Storage**: ~20x increase (JSONB duplication vs normalized FKs)
- Normalized: ~100 bytes/row
- Denormalized: ~2 KB/row

**Query Speed**: ~50% faster (pre-composed data, no runtime JOINs)
- Normalized: 20ms (multiple JOINs)
- Denormalized: 10ms (single table scan)

**Refresh Time**: Depends on row count and include depth
- 10K rows: ~1 second
- 100K rows: ~10 seconds
- 1M rows: Consider incremental refresh

**Tradeoff**: Use table views when reads >> writes (10:1 ratio or higher).

### Best Practices

**1. Start with Wildcards**:
```yaml
# ✅ Good: Zero maintenance
include_relations:
  - Organization:
      fields: ["*"]

# ⚠️  Premature optimization
include_relations:
  - Organization:
      fields: [id, name]  # Why only these? Profile first!
```

**2. Use Extra Filter Columns for Hot Paths**:
```yaml
# Analyze query patterns first
extra_filter_columns:
  - name: status  # Frequent WHERE clause
  - name: created_at  # Date range queries
```

**3. Limit Nesting Depth**:
```yaml
# ✅ Good: 2-3 levels
include_relations:
  - Book:
      include_relations:
        - Publisher:  # Stop here

# ❌ Avoid: 4+ levels (diminishing returns)
include_relations:
  - Book:
      include_relations:
        - Publisher:
            include_relations:
              - Country:
                  include_relations:
                    - Continent:  # Rarely needed
```

**4. Filter Sensitive Data**:
```yaml
# ❌ Don't use wildcard if entity has PII
include_relations:
  - User:
      fields: ["*"]  # May include password_hash, ssn!

# ✅ Use explicit list to exclude sensitive fields
include_relations:
  - User:
      fields: [id, name, email, department]
```

### Troubleshooting

**Issue**: "Entity not found in include_relations"
- **Cause**: Missing schema declaration in field definition
- **Fix**: Add `schema: management` to field definition

**Issue**: Refresh function slow (>10s for 100K rows)
- **Cause**: Missing FK indexes, too many includes, or deep nesting
- **Fix**: Add indexes on FK columns, reduce include count/depth

**Issue**: Wildcard includes sensitive data
- **Cause**: Source entity has PII fields in tv_ table
- **Fix**: Use explicit fields or filter sensitive fields in source entity's table_views

### See Also
- **Complete Guide**: [Table Views Composition Guide](../guides/table-views-composition.md)
- **Architecture**: [CQRS Implementation](../architecture/CQRS_TABLE_VIEWS_IMPLEMENTATION.md)
- **Examples**: [Cross-Schema Contract](../../entities/examples/contract_cross_schema.yaml)

---

## 7. Advanced Features

### Hierarchical Entities
See: `docs/guides/hierarchical-entities.md`

Enables tree structures with parent-child relationships.

```yaml
entity: Category
schema: catalog
hierarchical: true
fields:
  name: text
  parent: ref(Category)?
```

Generates:
- `identifier` as hierarchical path (e.g., `electronics/computers/laptops`)
- Helper functions for tree operations
- Recursive queries

### Multi-Tenancy
See: `docs/guides/multi-tenancy.md`

Automatic `tenant_id` for multi-tenant schemas.

**Configuration**: `registry/domain_registry.yaml`
```yaml
domains:
  crm:
    type: multi_tenant  # Adds tenant_id to all tables
  catalog:
    type: shared        # No tenant_id
```

**Effect**:
```sql
CREATE TABLE crm.tb_contact (
  id INTEGER PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES common.tb_tenant(id),
  -- ... other fields
);
```

### Stdlib Imports
See: `stdlib/` directory

Reusable entity templates.

```yaml
# entities/contact.yaml
import: stdlib/crm/contact
schema: crm  # Override schema
fields:
  # Additional fields beyond stdlib
  custom_field: text
```

## 8. Auto-Generated Features

### Trinity Pattern
Every entity automatically gets:
- `id` - INTEGER primary key (main identifier)
- `pk_<entity>` - UUID unique identifier (stable external reference)
- `identifier` - TEXT unique identifier (human-readable slug)

**Don't include these in YAML** - they're always generated.

### Audit Fields
Automatically added to all entities:
- `created_at` - TIMESTAMP WITH TIME ZONE
- `created_by` - UUID (references user)
- `updated_at` - TIMESTAMP WITH TIME ZONE
- `updated_by` - UUID
- `deleted_at` - TIMESTAMP WITH TIME ZONE (NULL unless soft-deleted)
- `deleted_by` - UUID

### Indexes
Automatically created for:
- Foreign key columns: `idx_tb_<entity>_<field>`
- Enum fields: `idx_tb_<entity>_<field>`
- `tenant_id`: `idx_tb_<entity>_tenant_id`
- JSONB fields: GIN index

### Helper Functions
Generated in `db/schema/20_helpers/`:
- `<schema>.<entity>_pk(uuid)` - Get INTEGER id from UUID
- `<schema>.<entity>_id(integer)` - Get INTEGER id from identifier
- `<schema>.<entity>_identifier(text)` - Get INTEGER id from identifier

### Naming Conventions
**Tables**: `tb_<entity>` (lowercase, snake_case)
**Views**: `tv_<entity>` (table views)
**Foreign Keys**: `fk_tb_<entity>_<field>`
**Indexes**: `idx_tb_<entity>_<field>`
**Functions**: `<schema>.<action_name>`
**Wrappers**: `app.<action_name>` (GraphQL entry point)

---

## Examples Section

### Complete Minimal Example
```yaml
entity: Contact
schema: crm
fields:
  email: text
  name: text
```

### Complete Rich Example
```yaml
entity: Order
schema: commerce
description: "Customer purchase orders"
organization:
  table_code: "042001"
  domain: "Commerce"
  subdomain: "Orders"
fields:
  order_number: text
  customer: ref(Customer)
  status: enum(draft, confirmed, shipped, delivered, cancelled)
  total_amount: money
  shipping_address: json
  notes: text?
  delivered_at: timestamp?
actions:
  - name: confirm_order
    description: "Confirm a draft order"
    impacts:
      write: [Order]
      read: [Customer, Product]
    steps:
      - validate: status = 'draft'
      - validate: total_amount.amount > 0
      - update: Order SET status = 'confirmed', confirmed_at = NOW()
      - notify: order_confirmed WITH {order_id: :id}

  - name: ship_order
    description: "Mark order as shipped"
    impacts:
      write: [Order, OrderLine, Product]
    steps:
      - validate: status = 'confirmed'
      - foreach: line IN (SELECT * FROM commerce.tb_order_line WHERE order_id = :id)
        do:
          - update: Product SET stock = stock - :line.quantity WHERE id = :line.product_id
      - update: Order SET status = 'shipped', shipped_at = NOW()
      - call: notifications.send_tracking_email(order_id: :id)
```

---

## Reference

### Related Documentation
- **Guides**: `docs/guides/` - How-to tutorials
- **Architecture**: `docs/architecture/` - Technical design
- **CLI Reference**: `docs/reference/cli-reference.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`

### External References
- PostgreSQL Data Types: https://www.postgresql.org/docs/current/datatype.html
- SQL Syntax: https://www.postgresql.org/docs/current/sql.html
- GraphQL: https://graphql.org/

---

## Validation Checklist

Before finalizing this reference:
- [ ] All field types documented with examples
- [ ] All action step types explained
- [ ] Organization section clearly marked as optional/advanced
- [ ] Auto-generated features explicitly listed
- [ ] Common gotchas addressed (e.g., text vs string)
- [ ] Examples are copy-paste ready
- [ ] Links to related docs work
- [ ] Table of contents is accurate