# Using the SpecQL Standard Library

**30 production-ready entities you can import and use immediately** 📚

## Overview

The SpecQL standard library provides battle-tested entity definitions extracted from production systems. Instead of building common entities from scratch, import them and focus on your unique business logic.

**What you get:**
- ✅ Production-quality schemas with proper constraints
- ✅ Rich type validation (email, phone, coordinates, etc.)
- ✅ Standard naming conventions
- ✅ Audit trails and security built-in
- ✅ GraphQL-ready with FraiseQL annotations

## Library Categories

### 🌍 **i18n** - Internationalization (6 entities)
Reference data for global applications:

```yaml
# Countries with ISO codes
import: stdlib/i18n/country

# Currencies with ISO 4217 codes
import: stdlib/i18n/currency

# Languages with ISO 639 codes
import: stdlib/i18n/language

# Timezones and locales
import: stdlib/i18n/locale
```

### 📍 **geo** - Geography & Addresses (9 entities)
Location and address management:

```yaml
# Public addresses with validation
import: stdlib/geo/public_address

# Geographic locations with coordinates
import: stdlib/geo/location

# Administrative divisions (states, provinces)
import: stdlib/geo/administrative_unit
```

### 👥 **crm** - Customer Relationship Management (3 entities)
Contact and organization management:

```yaml
# Individual contacts
import: stdlib/crm/contact

# Organizations/companies
import: stdlib/crm/organization

# Organization types (customer, vendor, partner)
import: stdlib/crm/organization_type
```

### 🏢 **org** - Organizational Structure (2 entities)
Internal organization management:

```yaml
# Organizational units/departments
import: stdlib/org/organizational_unit

# Hierarchy levels (division, department, team)
import: stdlib/org/organizational_unit_level
```

### 💰 **commerce** - Business Commerce (3 entities)
Financial and commercial entities:

```yaml
# Contracts and agreements
import: stdlib/commerce/contract

# Orders and transactions
import: stdlib/commerce/order

# Pricing structures
import: stdlib/commerce/price
```

### 💻 **tech** - Technology Reference (2 entities)
Technical reference data:

```yaml
# Operating systems
import: stdlib/tech/operating_system

# OS platforms (desktop, mobile, server)
import: stdlib/tech/operating_system_platform
```

### ⏰ **time** - Temporal Entities (1 entity)
Time-related reference data:

```yaml
# Calendar systems and fiscal years
import: stdlib/time/calendar
```

### 🔧 **common** - Common Reference Data (2 entities)
Generic reference entities:

```yaml
# Industry classifications
import: stdlib/common/industry

# Content genres/categories
import: stdlib/common/genre
```

## Quick Start

### Method 1: Import As-Is

```bash
# Copy stdlib entities to your project
cp stdlib/crm/contact.yaml entities/
cp stdlib/crm/organization.yaml entities/

# Generate everything
specql generate entities/*.yaml
```

### Method 2: Import in YAML

```yaml
# entities/my_app.yaml
import: stdlib/crm/contact
import: stdlib/crm/organization

entity: MyCustomEntity
schema: app
fields:
  name: text!
  contact: ref(Contact)  # Reference imported entity
```

### Method 3: Extend and Customize

```yaml
# entities/extended_contact.yaml
entity: ExtendedContact
extends:
  from: stdlib/crm/contact
schema: tenant

# Add your custom fields
fields:
  employee_id: text
  department: text
  hire_date: date

# Add custom actions
actions:
  - name: promote_employee
    steps:
      - validate: department IS NOT NULL
      - update: ExtendedContact SET department = ?
```

## Rich Types Showcase

stdlib entities demonstrate best practices for SpecQL's 49 rich scalar types:

### Communication
```yaml
# Email with automatic validation
email_address: email

# Phone numbers (E.164 format)
office_phone: phone
mobile_phone: phone

# URLs with validation
website: url
linkedin_profile: url
```

### Geographic
```yaml
# Geographic coordinates (PostgreSQL POINT)
coordinates: coordinates

# Addresses with validation
street_address: text
postal_code: text
city: text
country: ref(Country)
```

### Financial
```yaml
# Monetary amounts with precision
salary: money
budget: money

# Percentages (0-100)
commission_rate: percentage
tax_rate: percentage
```

### Content
```yaml
# Formatted content
bio: markdown
terms_and_conditions: html

# URLs and identifiers
website: url
social_media_handle: text
```

## Schema Patterns

### Multi-Tenant Entities (`schema: tenant`)
Most business entities use the `tenant` schema for automatic multi-tenancy:

```yaml
entity: Contact
schema: tenant  # Automatic tenant_id + RLS policies
```

**Generated automatically:**
- `tenant_id UUID` foreign key
- Row Level Security policies
- Tenant isolation
- Cross-tenant relationship validation

### Common Reference Data (`schema: common`)
Reference data shared across tenants:

```yaml
entity: Country
schema: common  # No tenant isolation
```

**Use for:**
- Countries, currencies, languages
- Industry classifications
- System-wide reference data

## Real-World Examples

### CRM System
```bash
# Import core CRM entities
cp stdlib/crm/*.yaml entities/
cp stdlib/i18n/country.yaml entities/
cp stdlib/geo/public_address.yaml entities/

# Generate complete CRM backend
specql generate entities/*.yaml
```

**What you get:**
- Contact management with email/phone validation
- Organization hierarchy
- Address management with geocoding support
- Country/currency reference data
- Automatic audit trails and soft deletes

### E-commerce Platform
```bash
# Import commerce entities
cp stdlib/commerce/*.yaml entities/
cp stdlib/crm/contact.yaml entities/
cp stdlib/i18n/currency.yaml entities/

# Add your custom entities
# ... your product, inventory, etc.
```

**What you get:**
- Order management with pricing
- Contract handling
- Customer contact integration
- Multi-currency support
- Financial audit trails

### SaaS Application
```bash
# Import organization structure
cp stdlib/org/*.yaml entities/
cp stdlib/crm/*.yaml entities/
cp stdlib/i18n/*.yaml entities/

# All entities automatically multi-tenant
specql generate entities/*.yaml
```

**What you get:**
- Multi-tenant organization structure
- User management and contacts
- Internationalization support
- Automatic tenant isolation

## Extending stdlib Entities

### Adding Fields
```yaml
entity: ExtendedContact
extends:
  from: stdlib/crm/contact
fields:
  # Add custom fields
  employee_number: text
  hire_date: date
  manager: ref(ExtendedContact)  # Self-reference
```

### Adding Actions
```yaml
entity: ExtendedContact
extends:
  from: stdlib/crm/contact
actions:
  # Add custom business logic
  - name: promote_employee
    description: "Promote employee to new position"
    steps:
      - validate: manager IS NOT NULL
      - update: ExtendedContact SET job_title = ?
      - notify: hr_team "Employee promotion"

  - name: transfer_employee
    description: "Transfer to different department"
    steps:
      - validate: new_department IS NOT NULL
      - update: ExtendedContact SET department = ?
```

### Customizing Schema
```yaml
entity: CustomOrganization
extends:
  from: stdlib/crm/organization
schema: custom_tenant  # Override schema
fields:
  # Override existing fields
  name:
    type: text
    nullable: false
    description: "Custom organization name validation"
```

## Best Practices

### 1. Start with stdlib
```yaml
# Don't reinvent - extend
entity: MyContact
extends:
  from: stdlib/crm/contact
fields:
  custom_field: text  # Only add what's unique to your business
```

### 2. Use Appropriate Schemas
```yaml
# Multi-tenant business data
entity: Customer
schema: tenant

# Shared reference data
entity: Industry
schema: common
```

### 3. Leverage Rich Types
```yaml
# Use semantic types over generic text
email: email!        # Not: email: text
phone: phone         # Not: phone: text
website: url         # Not: website: text
budget: money        # Not: budget: numeric
```

### 4. Import Related Entities
```yaml
# When importing Contact, also import Organization
import: stdlib/crm/contact
import: stdlib/crm/organization  # Contact references Organization
```

## Troubleshooting

### "Entity not found" Error
```bash
# Make sure to import dependencies
cp stdlib/crm/organization.yaml entities/  # Contact needs this
cp stdlib/crm/contact.yaml entities/
```

### Schema Conflicts
```yaml
# Override schema if needed
entity: MyContact
extends:
  from: stdlib/crm/contact
schema: my_schema  # Override the default 'tenant' schema
```

### Rich Type Validation Issues
```bash
# Check data matches rich type format
# email: must be valid email address
# phone: must be E.164 format (+33123456789)
# url: must be valid URL
```

## Complete Entity List

| Category | Entity | Description | Schema |
|----------|--------|-------------|--------|
| **crm** | contact | Individual contacts | tenant |
| **crm** | organization | Companies/organizations | tenant |
| **crm** | organization_type | Customer/vendor/partner types | common |
| **i18n** | country | Countries with ISO codes | common |
| **i18n** | currency | Currencies with ISO codes | common |
| **i18n** | language | Languages with ISO codes | common |
| **i18n** | locale | Locale settings | common |
| **i18n** | continent | World continents | common |
| **geo** | public_address | Address with validation | tenant |
| **geo** | location | Geographic locations | tenant |
| **geo** | administrative_unit | States/provinces/regions | common |
| **geo** | postal_code | Postal codes | common |
| **org** | organizational_unit | Departments/teams | tenant |
| **org** | organizational_unit_level | Hierarchy levels | common |
| **commerce** | contract | Contracts/agreements | tenant |
| **commerce** | order | Orders/transactions | tenant |
| **commerce** | price | Pricing structures | tenant |
| **tech** | operating_system | OS reference | common |
| **tech** | operating_system_platform | OS platforms | common |
| **time** | calendar | Calendar systems | common |
| **common** | industry | Industry classifications | common |
| **common** | genre | Content categories | common |

## Next Steps

- **Browse Examples**: See `examples/` for complete applications
- **Read Rich Types Guide**: Learn about all 49 scalar types in `docs/guides/rich-types-guide.md`
- **Check Actions Guide**: Understand business logic patterns in `docs/guides/actions-guide.md`
- **Explore Tests**: See `tests/integration/` for usage patterns

---

**Ready to build? Start with stdlib entities and customize as needed.** 🚀