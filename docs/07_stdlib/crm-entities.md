# CRM Entities: Production-Ready Customer Management

> **Three battle-tested entities that power enterprise CRM systems**

## Overview

SpecQL's CRM stdlib provides **production-ready entities** extracted from real-world systems and generalized for universal use. These entities handle customer relationship management, contact tracking, and organizational hierarchies.

**Entities**:
- **Contact** - Individual contact management with authentication
- **Organization** - Hierarchical company/organization records
- **OrganizationType** - Business entity classifications

**Origin**: Extracted from PrintOptim production system (proven in real businesses)

---

## Contact Entity

### Purpose

Individual contact information for CRM systems, including:
- Personal details (name, email, phone)
- Job role and position
- Localization (language, timezone)
- Authentication (password hash for portal access)
- External handles (LinkedIn, Twitter, etc.)

### Schema Location

**Multi-tenant**: `tenant` schema (isolated per customer)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | text | No | First name of the contact |
| `last_name` | text | No | Last name of the contact |
| `email_address` | email | **Yes** | Primary email (unique, validated) |
| `office_phone` | phone | No | Landline/office phone (validated) |
| `mobile_phone` | phone | No | Mobile phone (validated) |
| `job_title` | text | No | Job title (e.g., "Purchasing Manager") |
| `position` | text | No | Organizational position (e.g., "Director") |
| `lang` | text | No | Preferred language code (ISO 639) |
| `locale` | text | No | Locale for formatting (BCP 47) |
| `timezone` | text | No | IANA timezone (e.g., "Europe/Paris") |
| `handles` | json | No | External handles (social media, etc.) |
| `password_hash` | text | No | Hashed password for portal access |

### Relationships

| Field | References | Description |
|-------|------------|-------------|
| `customer_org` | Organization | Company/organization affiliation |
| `genre` | Genre | Gender/honorific (from `stdlib/common`) |

### Automatic Fields (Trinity Pattern)

Every Contact automatically includes:

```sql
pk_contact      INTEGER PRIMARY KEY  -- Internal DB key
id              UUID UNIQUE          -- External API identifier
identifier      TEXT UNIQUE          -- Human-readable (email)
tenant_id       UUID NOT NULL        -- Multi-tenant isolation
created_at      TIMESTAMP            -- Auto-set on insert
updated_at      TIMESTAMP            -- Auto-update on change
deleted_at      TIMESTAMP            -- Soft delete support
created_by      UUID                 -- Audit trail
updated_by      UUID                 -- Audit trail
```

### Pre-built Actions

```yaml
# CRUD Operations
- create_contact
- update_contact
- delete_contact

# Business Logic
- activate_contact       # Enable contact
- deactivate_contact     # Disable contact
- change_email_address   # Update email with validation
- change_office_phone    # Update office phone
- change_mobile_phone    # Update mobile phone
- update_job_title       # Change job title
- update_position        # Change organizational position
- change_timezone        # Update timezone preference
- update_password        # Change password hash
```

### Usage Example

#### Import As-Is

```yaml
from: stdlib/crm/contact.yaml

# That's it! Full contact management ready.
```

**Generated**:
- PostgreSQL table with 20+ fields
- Email/phone validation constraints
- Audit trail triggers
- GraphQL queries/mutations
- TypeScript types

#### Extend with Custom Fields

```yaml
from: stdlib/crm/contact.yaml

extend: Contact
  custom_fields:
    # Business-specific additions
    loyalty_tier: enum(bronze, silver, gold, platinum)
    lifetime_value: money
    marketing_consent: boolean
    internal_notes: richtext
    last_contacted_at: timestamp
    lead_source: enum(website, referral, event, cold_call)
```

#### Add Custom Actions

```yaml
from: stdlib/crm/contact.yaml

action: qualify_lead
  entity: Contact
  steps:
    - validate: email_address IS NOT NULL
    - validate: customer_org IS NOT NULL
    - update: Contact SET status = 'qualified', qualified_at = NOW()
    - notify: sales_team

action: upgrade_loyalty_tier
  entity: Contact
  steps:
    - if: lifetime_value > 10000
      - update: Contact SET loyalty_tier = 'platinum'
    - if: lifetime_value > 5000 AND lifetime_value <= 10000
      - update: Contact SET loyalty_tier = 'gold'
```

---

## Organization Entity

### Purpose

Hierarchical organization/company management with:
- Company identity (name, domain, legal info)
- Parent-child hierarchy support
- Industry classification
- Compliance identifiers (VAT, legal IDs)
- Stock location management

### Schema Location

**Shared**: `management` schema (shared across tenants for reference data)

### Hierarchical Support

Organizations can form **parent-child hierarchies**:

```yaml
# Example: Corporate structure
- Acme Corp (parent)
  - Acme Europe (child)
    - Acme France (grandchild)
    - Acme Germany (grandchild)
  - Acme Americas (child)
```

**Enabled by**: `hierarchical: true`

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | text | Yes | Organization name |
| `domain_name` | text | No | Primary domain (e.g., "acme") |
| `domain_tld` | text | No | Top-level domain (e.g., "com") |
| `legal_identifier_type` | text | No | Type of legal ID (SIRET, EIN, etc.) |
| `legal_identifier` | text | No | Legal registration number |
| `vat_identifier` | text | No | VAT/tax identification number |
| `stock_location_ids` | json | No | Array of warehouse/location UUIDs |

### Relationships

| Field | References | Description |
|-------|------------|-------------|
| `industry` | Industry | Business sector classification |
| `organization_type` | OrganizationType | Prospect/client/provider |
| `parent` | Organization | Parent organization (self-reference) |

### Pre-built Actions

```yaml
# CRUD Operations
- create_organization
- update_organization
- delete_organization

# Business Logic
- activate_organization      # Enable organization
- deactivate_organization    # Disable organization
- change_domain              # Update domain name/TLD
- update_legal_info          # Change legal identifiers
- change_industry            # Reclassify industry
- update_vat_identifier      # Update VAT number
- add_stock_location         # Link warehouse location
- remove_stock_location      # Unlink warehouse location
```

### Usage Example

#### Corporate Hierarchy

```yaml
from: stdlib/crm/organization.yaml

# Parent company
action: create_parent_org
  steps:
    - insert: Organization
      values:
        name: "Acme Corporation"
        domain_name: "acme"
        domain_tld: "com"
        legal_identifier_type: "EIN"
        legal_identifier: "12-3456789"
        vat_identifier: "US123456789"

# Child subsidiary
action: create_subsidiary
  steps:
    - insert: Organization
      values:
        name: "Acme Europe"
        parent: ref(Organization[identifier='acme-corporation'])
        domain_name: "acme-europe"
        domain_tld: "eu"
```

**Generated SQL**:

```sql
-- Automatic self-referencing foreign key
ALTER TABLE management.tb_organization
  ADD CONSTRAINT fk_organization_parent
  FOREIGN KEY (parent) REFERENCES management.tb_organization(pk_organization);

-- Hierarchy queries supported
SELECT * FROM management.tb_organization
WHERE parent = organization_pk('Acme Corporation');
```

#### Multi-Location Management

```yaml
action: setup_warehouse_network
  entity: Organization
  steps:
    - update: Organization
      values:
        stock_location_ids: '[
          "550e8400-e29b-41d4-a716-446655440001",
          "550e8400-e29b-41d4-a716-446655440002"
        ]'
```

---

## OrganizationType Entity

### Purpose

Classification of organizations into business categories:
- **Prospect** - Potential customer
- **Client** - Active customer
- **Provider** - Supplier/vendor
- Custom types (Partner, Distributor, etc.)

### Schema Location

**Shared**: `management` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | text | Yes | Type name (e.g., "Client", "Provider") |

### Translation Support

**Multi-language**: Automatic translations enabled for `name` field.

```yaml
translations:
  enabled: true
  fields: [name]
```

**Result**: Organizations types are translatable across languages.

### Pre-built Actions

```yaml
# CRUD Operations
- create_organization_type
- update_organization_type
- delete_organization_type

# Business Logic
- activate_type          # Enable type
- deactivate_type        # Disable type
- update_description     # Change description
```

### Usage Example

```yaml
from: stdlib/crm/organization_type.yaml

# Seed data: Standard organization types
action: seed_org_types
  steps:
    - insert: OrganizationType VALUES (name: 'Prospect')
    - insert: OrganizationType VALUES (name: 'Client')
    - insert: OrganizationType VALUES (name: 'Provider')
    - insert: OrganizationType VALUES (name: 'Partner')
```

**Translations**:

```sql
-- French translations
INSERT INTO management.tb_organization_type_i18n (organization_type, lang, name)
VALUES
  (organization_type_pk('Prospect'), 'fr', 'Prospect'),
  (organization_type_pk('Client'), 'fr', 'Client'),
  (organization_type_pk('Provider'), 'fr', 'Fournisseur');
```

---

## Complete CRM Example

### Scenario: Building a B2B CRM

```yaml
# File: entities/b2b_crm.yaml

# Import CRM entities
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
from: stdlib/crm/organization_type.yaml
from: stdlib/common/industry.yaml
from: stdlib/common/genre.yaml

# Extend Contact for sales pipeline
extend: Contact
  custom_fields:
    lead_status: enum(new, contacted, qualified, proposal, negotiation, closed_won, closed_lost)
    lead_score: integer(0, 100)
    deal_value: money
    next_followup_date: date
    sales_notes: richtext

# Extend Organization for account management
extend: Organization
  custom_fields:
    account_tier: enum(bronze, silver, gold, platinum)
    annual_contract_value: money
    renewal_date: date
    health_score: integer(0, 100)

# Custom actions
action: qualify_lead
  entity: Contact
  steps:
    - validate: email_address IS NOT NULL
    - validate: customer_org IS NOT NULL
    - validate: lead_status = 'contacted'
    - update: Contact
      SET lead_status = 'qualified',
          lead_score = LEAST(lead_score + 20, 100),
          qualified_at = NOW()
    - notify: sales_manager

action: create_proposal
  entity: Contact
  steps:
    - validate: lead_status = 'qualified'
    - update: Contact SET lead_status = 'proposal'
    - insert: Proposal
      VALUES (contact: $contact_id, created_at: NOW())
    - notify: sales_team

action: win_deal
  entity: Contact
  steps:
    - validate: lead_status IN ('proposal', 'negotiation')
    - update: Contact SET lead_status = 'closed_won', won_at = NOW()
    - update: Organization
      SET account_tier = 'silver'  # Promote to active customer
    - notify: customer_success_team
```

### Generated Output

```bash
specql generate entities/b2b_crm.yaml --output db/schema/

# Generated files:
# db/schema/10_tables/contact.sql (150 lines)
# db/schema/10_tables/organization.sql (120 lines)
# db/schema/10_tables/organization_type.sql (60 lines)
# db/schema/20_functions/qualify_lead.sql (80 lines)
# db/schema/20_functions/create_proposal.sql (90 lines)
# db/schema/20_functions/win_deal.sql (100 lines)
# db/schema/30_fraiseql/mutations.sql (200 lines)
# frontend/types/crm.ts (300 lines)
# frontend/mutations/useMutations.ts (250 lines)

# Total: ~1,350 lines generated from 80 lines YAML
# Ratio: 17x code generation leverage
```

---

## Integration with Other stdlib Modules

### CRM + Geographic

```yaml
from: stdlib/crm/organization.yaml
from: stdlib/geo/public_address.yaml

extend: Organization
  custom_fields:
    billing_address: ref(PublicAddress)
    shipping_address: ref(PublicAddress)
```

**Use Case**: E-commerce with shipping management

---

### CRM + Commerce

```yaml
from: stdlib/crm/contact.yaml
from: stdlib/commerce/order.yaml
from: stdlib/commerce/price.yaml

extend: Contact
  custom_fields:
    orders: list(ref(Order))
    lifetime_value: money
```

**Use Case**: Customer order history tracking

---

### CRM + i18n

```yaml
from: stdlib/crm/contact.yaml
from: stdlib/i18n/language.yaml
from: stdlib/i18n/currency.yaml

extend: Contact
  custom_fields:
    preferred_language: ref(Language)
    preferred_currency: ref(Currency)
```

**Use Case**: International CRM with localization

---

## Performance Considerations

### Automatic Indexes

SpecQL automatically creates indexes on:

```sql
-- Foreign keys
CREATE INDEX idx_tb_contact_customer_org ON tenant.tb_contact(customer_org);
CREATE INDEX idx_tb_organization_parent ON management.tb_organization(parent);

-- Unique constraints
CREATE UNIQUE INDEX idx_tb_contact_email ON tenant.tb_contact(email_address);

-- Tenant isolation
CREATE INDEX idx_tb_contact_tenant ON tenant.tb_contact(tenant_id);
```

### Query Optimization Tips

**DO**: Use helper functions for lookups

```sql
-- ✅ GOOD: Uses integer PK
SELECT * FROM tenant.tb_contact
WHERE pk_contact = contact_pk('john.doe@acme.com');
```

**DON'T**: Direct UUID queries

```sql
-- ❌ SLOW: UUID comparison
SELECT * FROM tenant.tb_contact
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## Security Best Practices

### Row-Level Security (RLS)

Contact entities are **tenant-isolated**:

```sql
-- Auto-generated RLS policy
CREATE POLICY tenant_isolation ON tenant.tb_contact
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

**Result**: Users can only see contacts in their tenant.

---

### Password Handling

**NEVER** store plaintext passwords:

```yaml
# ✅ GOOD: Hash before storing
action: set_contact_password
  steps:
    - update: Contact
      SET password_hash = crypt($plaintext_password, gen_salt('bf'))
```

**Use**: PostgreSQL `pgcrypto` extension for bcrypt hashing.

---

## Migration from Existing Systems

### From Django CRM

**Before** (Django models.py - 200 lines):

```python
class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    office_phone = PhoneNumberField(blank=True)
    mobile_phone = PhoneNumberField(blank=True)
    job_title = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization)
    # ... 15 more fields
    # ... Meta class
    # ... Custom methods

class Organization(models.Model):
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=100)
    # ... 20 more fields
```

**After** (SpecQL - 2 lines):

```yaml
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
```

**Savings**: 198 lines eliminated, 99% reduction.

---

### From TypeScript + Prisma

**Before** (Prisma schema - 150 lines):

```typescript
model Contact {
  id            String   @id @default(uuid())
  firstName     String?
  lastName      String?
  email         String   @unique
  officePhone   String?
  mobilePhone   String?
  jobTitle      String?
  organizationId String
  organization  Organization @relation(fields: [organizationId])
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
  // ... many more fields
}

model Organization {
  id       String @id @default(uuid())
  name     String
  domain   String?
  contacts Contact[]
  // ... many more fields
}
```

**After** (SpecQL - 2 lines):

```yaml
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
```

**Savings**: 148 lines eliminated, plus automatic GraphQL schema.

---

## Versioning & Updates

stdlib entities are **versioned** (current: v1.1.0):

```yaml
# Contact entity header
# Version: 1.1.0
```

**When you import**: You get the latest stable version.

**Updates**: New versions add fields/actions without breaking changes.

**Best Practice**: Import (don't copy) to receive automatic updates.

---

## Testing stdlib Entities

```bash
# Generate test database
specql generate stdlib/crm/*.yaml --output test/schema/

# Run integration tests
psql test_db < test/schema/contact.sql
psql test_db -c "SELECT app.create_contact(...)"

# Verify constraints
psql test_db -c "INSERT INTO tenant.tb_contact (email_address) VALUES ('invalid-email')"
# ERROR: Email validation failed (expected)
```

---

## Troubleshooting

### Error: "Cannot extend stdlib entity"

**Problem**: Trying to modify stdlib entity directly.

**Solution**: Use `extend` instead of modifying:

```yaml
# ❌ BAD
entity: Contact
  fields:
    custom_field: text

# ✅ GOOD
from: stdlib/crm/contact.yaml
extend: Contact
  custom_fields:
    custom_field: text
```

---

### Error: "Duplicate identifier"

**Problem**: Contact `identifier` conflicts with email uniqueness.

**Solution**: SpecQL uses `email_address` as natural identifier:

```sql
-- Auto-generated
identifier = COALESCE(email_address, 'contact-' || pk_contact)
```

---

## Learn More

- [Geographic Entities](geo-entities.md) - Add address management
- [Commerce Entities](commerce-entities.md) - Add order tracking
- [i18n Entities](i18n-entities.md) - Add multi-language support
- [Action Patterns](action-patterns.md) - Pre-built business logic

---

## Key Takeaways

1. **Production-Ready**: stdlib/crm entities are battle-tested in real systems
2. **99% Code Reduction**: 2 lines of YAML vs 200 lines of Python/TypeScript
3. **Extensible**: Import + extend, never modify stdlib directly
4. **Composable**: Combine with geo, commerce, i18n modules
5. **Automatic Best Practices**: Validation, indexes, RLS, audit trails

**Start with stdlib/crm, customize for your business, ship in minutes.** ⚡

---

*Last updated: 2025-11-19*
