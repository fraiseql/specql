# CRM Entities: Customer Relationship Management

> **Production-ready CRM entities for managing contacts, organizations, and business relationships**

## Overview

The CRM (Customer Relationship Management) stdlib provides entities for managing:
- **Individual contacts** with communication details and roles
- **Organizations** with hierarchy and legal information
- **Relationships** between contacts and organizations
- **Classification** of organization types

These entities are extracted from production CRM systems and generalized for universal reuse.

## Entities

### Contact

**Individual contact information linked to organizations**

```yaml
import:
  - stdlib/crm/contact
```

**Key Features**:
- Personal information (name, email, phone)
- Job title and organizational position
- Multi-language support (language, locale, timezone)
- External handles (LinkedIn, etc.)
- Optional authentication (password_hash for system users)
- Organization relationship

**Fields**:
```yaml
fields:
  # Personal
  first_name: text
  last_name: text
  email_address: email!

  # Contact methods
  office_phone: phone
  mobile_phone: phone

  # Professional
  job_title: text
  position: text

  # Localization
  lang: text           # e.g., 'en', 'fr', 'de'
  locale: text         # e.g., 'en-US', 'fr-FR'
  timezone: text       # e.g., 'America/New_York'

  # External
  handles: json        # {'linkedin': 'url', 'twitter': '@handle'}

  # Authentication
  password_hash: text

  # Relationships
  customer_org: ref(Organization)
  genre: ref(Genre)
```

**Built-in Actions**:
- `create_contact` - Create new contact
- `update_contact` - Update contact information
- `delete_contact` - Soft delete contact
- `activate_contact` - Mark contact as active
- `deactivate_contact` - Mark contact as inactive
- `change_email_address` - Update email with validation
- `change_office_phone` - Update office phone
- `change_mobile_phone` - Update mobile phone
- `update_job_title` - Change job title
- `update_position` - Change organizational position
- `change_timezone` - Update timezone preference
- `update_password` - Change authentication password

**Example Usage**:
```yaml
import:
  - stdlib/crm/contact

# Use as-is for standard CRM
```

**Extended Example**:
```yaml
import:
  - stdlib/crm/contact

# Extend for sales CRM
entity: SalesContact
extends:
  from: stdlib/crm/contact
fields:
  lead_score: integer(0, 100)
  lead_source: enum(website, referral, cold_call, event, partner)
  status: enum(new, contacted, qualified, proposal, negotiation, closed_won, closed_lost)
  last_contact_date: date
  next_follow_up: date
  assigned_to: ref(SalesRep)

actions:
  - name: convert_to_customer
    steps:
      - validate: status IN ('qualified', 'negotiation')
      - update: SalesContact SET status = 'closed_won', converted_at = now()
      - call: create_customer_account
      - notify: sales_conversion_completed
```

---

### Organization

**Hierarchical organization/company management with legal identifiers**

```yaml
import:
  - stdlib/crm/organization
```

**Key Features**:
- Hierarchical structure (parent-child relationships)
- Legal identifiers (company registration, VAT number)
- Domain management (company website domains)
- Industry classification
- Stock/inventory location tracking

**Fields**:
```yaml
fields:
  # Identity
  name: text!
  domain_name: text          # e.g., 'acme-corp'
  domain_tld: text           # e.g., '.com', '.co.uk'

  # Legal
  legal_identifier_type: text     # e.g., 'SIRET', 'EIN', 'Company Number'
  legal_identifier: text          # e.g., '123 456 789 00011'
  vat_identifier: text            # e.g., 'FR12345678901'

  # Logistics
  stock_location_ids: json   # Array of UUID references

  # Classification
  industry: ref(Industry)
  organization_type: ref(OrganizationType)

  # Hierarchy
  parent: ref(Organization)  # Self-referencing for hierarchy
```

**Built-in Actions**:
- `create_organization` - Create new organization
- `update_organization` - Update organization details
- `delete_organization` - Soft delete organization
- `activate_organization` - Mark as active
- `deactivate_organization` - Mark as inactive
- `change_domain` - Update domain information
- `update_legal_info` - Change legal identifiers
- `change_industry` - Update industry classification
- `update_vat_identifier` - Change VAT number
- `add_stock_location` - Add inventory location
- `remove_stock_location` - Remove inventory location

**Hierarchical Support**:
```sql
-- Auto-generated queries for hierarchy
SELECT * FROM get_organization_hierarchy('parent-org-id');
SELECT * FROM get_organization_descendants('org-id');
SELECT * FROM get_organization_path('leaf-org-id');  -- Full path to root
```

**Example Usage**:
```yaml
import:
  - stdlib/crm/organization

# Multi-level company structure
# ACME Corp (parent)
#   ├── ACME North America (child)
#   │   ├── ACME USA (grandchild)
#   │   └── ACME Canada (grandchild)
#   └── ACME Europe (child)
#       ├── ACME UK (grandchild)
#       └── ACME France (grandchild)
```

**Extended Example (B2B Platform)**:
```yaml
import:
  - stdlib/crm/organization

entity: EnterpriseClient
extends:
  from: stdlib/crm/organization
fields:
  # Contract info
  contract_start_date: date!
  contract_end_date: date!
  contract_value: money!
  payment_terms: integer  # Days

  # Service level
  sla_tier: enum(basic, professional, enterprise, premium)
  max_users: integer
  storage_quota_gb: integer

  # Account management
  account_manager: ref(Employee)
  technical_contact: ref(Contact)
  billing_contact: ref(Contact)

  # Usage tracking
  monthly_active_users: integer
  storage_used_gb: numeric
  api_calls_this_month: integer

actions:
  - name: renew_contract
    steps:
      - validate: contract_end_date > now()
      - validate: payment_status = 'current'
      - update: EnterpriseClient SET
          contract_end_date = contract_end_date + interval '1 year',
          renewed_at = now()
      - call: generate_renewal_invoice
      - notify: contract_renewed
```

---

### OrganizationType

**Classification of organization types**

```yaml
import:
  - stdlib/crm/organization_type
```

**Purpose**: Classify organizations by type (client, vendor, partner, internal department, etc.)

**Fields**:
```yaml
fields:
  name: text!
  code: text!          # e.g., 'CLIENT', 'VENDOR', 'PARTNER'
  description: text
  is_internal: boolean # Internal departments vs external entities
```

**Common Types**:
- `CLIENT` - Customer organizations
- `VENDOR` - Supplier organizations
- `PARTNER` - Partner/reseller organizations
- `DEPARTMENT` - Internal departments
- `SUBSIDIARY` - Company subsidiaries
- `COMPETITOR` - Competitor tracking

**Example Usage**:
```yaml
import:
  - stdlib/crm/organization
  - stdlib/crm/organization_type

# Automatically link organization to type
# Organization table will have: organization_type: ref(OrganizationType)
```

---

## Common Patterns

### Multi-Tenant CRM

```yaml
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/crm/organization_type

# All entities auto-get tenant_id
# RLS policies auto-applied for tenant isolation
```

### Contact-Organization Relationship

```yaml
# One contact can belong to one organization
# One organization can have many contacts

# Query all contacts for an organization:
SELECT * FROM crm.contact WHERE customer_org_id = organization_id('acme-corp');

# Query organization for a contact:
SELECT * FROM crm.organization WHERE id = (
  SELECT customer_org_id FROM crm.contact WHERE id = contact_id('john-doe')
);
```

### Hierarchical Organizations

```yaml
# Parent-child organization structure
import:
  - stdlib/crm/organization

# ACME Corp
organization:
  name: "ACME Corporation"
  parent: null  # Root organization

# ACME North America (child of ACME Corp)
organization:
  name: "ACME North America"
  parent: ref(ACME Corporation)

# ACME USA (child of ACME North America)
organization:
  name: "ACME USA"
  parent: ref(ACME North America)
```

### Localized Contacts

```yaml
import:
  - stdlib/crm/contact

# Contacts with localization
contact:
  first_name: "Jean"
  last_name: "Dupont"
  email_address: "jean.dupont@example.fr"
  lang: "fr"
  locale: "fr-FR"
  timezone: "Europe/Paris"

contact:
  first_name: "John"
  last_name: "Doe"
  email_address: "john.doe@example.com"
  lang: "en"
  locale: "en-US"
  timezone: "America/New_York"
```

---

## Integration Examples

### CRM + Geographic

```yaml
import:
  - stdlib/crm/organization
  - stdlib/geo/public_address

entity: OrganizationWithAddress
extends:
  from: stdlib/crm/organization
fields:
  headquarters: ref(PublicAddress)
  billing_address: ref(PublicAddress)
  shipping_addresses: list(ref(PublicAddress))
```

### CRM + Commerce

```yaml
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/commerce/contract

entity: ServiceContract
extends:
  from: stdlib/commerce/contract
fields:
  client_organization: ref(Organization)!
  primary_contact: ref(Contact)!
  billing_contact: ref(Contact)
```

### CRM + i18n

```yaml
import:
  - stdlib/crm/organization
  - stdlib/i18n/country
  - stdlib/i18n/currency
  - stdlib/i18n/language

entity: InternationalClient
extends:
  from: stdlib/crm/organization
fields:
  headquarters_country: ref(Country)!
  billing_currency: ref(Currency)!
  preferred_language: ref(Language)!
  supported_languages: list(ref(Language))
```

---

## Database Schema

### Contact Table
```sql
CREATE TABLE crm.tb_contact (
  -- Trinity Pattern
  pk_contact SERIAL PRIMARY KEY,
  id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT UNIQUE,

  -- Fields
  first_name TEXT,
  last_name TEXT,
  email_address TEXT NOT NULL CHECK (email_address ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
  office_phone TEXT CHECK (office_phone ~ '^\+[1-9]\d{1,14}$'),
  mobile_phone TEXT CHECK (mobile_phone ~ '^\+[1-9]\d{1,14}$'),
  job_title TEXT,
  position TEXT,
  lang TEXT,
  locale TEXT,
  timezone TEXT,
  handles JSONB,
  password_hash TEXT,

  -- Relationships
  customer_org_id UUID REFERENCES crm.tb_organization(id),

  -- Audit
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP,

  -- Multi-tenant
  tenant_id UUID NOT NULL
);

-- Indexes
CREATE INDEX idx_tb_contact_email ON crm.tb_contact(email_address);
CREATE INDEX idx_tb_contact_customer_org ON crm.tb_contact(customer_org_id);
CREATE INDEX idx_tb_contact_tenant ON crm.tb_contact(tenant_id);
```

### Organization Table
```sql
CREATE TABLE crm.tb_organization (
  -- Trinity Pattern
  pk_organization SERIAL PRIMARY KEY,
  id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT UNIQUE,

  -- Fields
  name TEXT NOT NULL,
  domain_name TEXT,
  domain_tld TEXT,
  legal_identifier_type TEXT,
  legal_identifier TEXT,
  vat_identifier TEXT,
  stock_location_ids JSONB,

  -- Relationships
  industry_id UUID REFERENCES common.tb_industry(id),
  organization_type_id UUID REFERENCES crm.tb_organization_type(id),
  parent_id UUID REFERENCES crm.tb_organization(id),  -- Self-referencing

  -- Audit
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  deleted_at TIMESTAMP,

  -- Multi-tenant
  tenant_id UUID NOT NULL,

  -- Hierarchy constraint
  CHECK (parent_id != id)  -- No self-parenting
);

-- Indexes
CREATE INDEX idx_tb_organization_parent ON crm.tb_organization(parent_id);
CREATE INDEX idx_tb_organization_type ON crm.tb_organization(organization_type_id);
CREATE INDEX idx_tb_organization_tenant ON crm.tb_organization(tenant_id);
```

---

## Next Steps

- [Geographic Entities](../geo/index.md) - Add address management
- [Commerce Entities](../commerce/index.md) - Add orders and contracts
- [Extending stdlib](../../07_advanced/extending-stdlib.md) - Customize for your needs
- [Multi-tenancy Guide](../../05_guides/multi-tenancy.md) - Tenant isolation patterns

---

**CRM entities provide the foundation for customer management. Extend them to match your business, but never rebuild them from scratch.**
