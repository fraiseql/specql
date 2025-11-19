# SpecQL Standard Library: 30+ Battle-Tested Entities

> **Production-proven business entities ready to import and use**

## Overview

The SpecQL **standard library (stdlib)** provides **30+ pre-built entities** extracted from production systems and generalized for universal reuse. These are not toy examples—they're battle-tested components from real businesses.

**Use as-is or extend with your custom fields.** Zero configuration required.

## Why Use stdlib?

### ❌ Traditional Approach: Build Everything

```yaml
# Write 500 lines defining Contact entity
# Write 300 lines for Organization
# Write 400 lines for Address
# Write 200 lines for Country
# Total: 1400+ lines of repetitive YAML
```

### ✅ stdlib Approach: Import and Extend

```yaml
# Import pre-built entities
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/geo/public_address
  - stdlib/i18n/country

# Add custom fields only
entity: MyContact
extends:
  from: stdlib/crm/contact
fields:
  loyalty_points: integer
  preferred_payment: enum(credit_card, paypal, crypto)
```

**Result**: 10 lines instead of 1400. Production-ready in minutes.

## What's Included

### 🏢 CRM Entities (Customer Relationship Management)
Pre-built entities for managing contacts, organizations, and relationships.

- **Contact**: Individual contact with email, phone, job title, localization
- **Organization**: Companies with hierarchy, legal identifiers, VAT numbers
- **OrganizationType**: Classification of organization types

[View CRM entities →](crm/index.md)

### 🌍 Geographic Entities (Location & Address Management)
Comprehensive address and location data with international support.

- **PublicAddress**: Multi-line addresses with postal codes and geolocation
- **Location**: Hierarchical locations (country → state → city → district)
- **PostalCode**: Postal code database with city mapping
- **AdministrativeUnit**: Governmental/administrative boundaries

[View geographic entities →](geo/index.md)

### 💰 Commerce Entities (Business Transactions)
E-commerce and contract management building blocks.

- **Contract**: Business contracts with dates, amounts, and parties
- **Order**: Purchase orders with status tracking
- **Price**: Multi-currency pricing with effective dates

[View commerce entities →](commerce/index.md)

### 🌐 Internationalization (i18n) Entities
Localization and multi-language support.

- **Country**: ISO 3166 country codes and names
- **Currency**: ISO 4217 currency codes with symbols
- **Language**: ISO 639 language codes
- **Locale**: Locale configurations (language + region)

[View i18n entities →](i18n/index.md)

### ⏰ Time & Scheduling Entities
Temporal data and scheduling support.

- **Calendar**: Business calendar with holidays
- **Timezone**: IANA timezone database
- **DateRange**: Time periods with validation

[View time entities →](time/index.md)

### 🏛️ Organizational Entities
Internal organization structure and hierarchy.

- **Department**: Organizational departments with hierarchy
- **Team**: Working groups and teams
- **Role**: Job roles and permissions

[View org entities →](org/index.md)

### 🔧 Technical Entities
System-level entities for technical infrastructure.

- **User**: System users with authentication
- **ApiKey**: API key management with scopes
- **AuditLog**: Change tracking and compliance

[View tech entities →](tech/index.md)

## How to Use stdlib

### Import As-Is

```yaml
# Just import and use
import:
  - stdlib/crm/contact
  - stdlib/crm/organization

# Contact and Organization are now available
# with all fields and actions pre-defined
```

### Extend with Custom Fields

```yaml
# Import base entity
import:
  - stdlib/crm/contact

# Extend with your custom fields
entity: CustomerContact
extends:
  from: stdlib/crm/contact
fields:
  customer_since: date!
  lifetime_value: money
  segment: enum(bronze, silver, gold, platinum)
  preferences: json
```

### Override Fields

```yaml
# Import and customize
import:
  - stdlib/crm/organization

entity: Vendor
extends:
  from: stdlib/crm/organization
fields:
  # Override base field with different type
  domain_name: url!  # Was optional text, now required URL

  # Add vendor-specific fields
  payment_terms: integer  # Days
  discount_percentage: percentage
  preferred_vendor: boolean
```

### Add Custom Actions

```yaml
import:
  - stdlib/crm/contact

entity: SalesContact
extends:
  from: stdlib/crm/contact
actions:
  # Inherit all base actions (create, update, etc.)

  # Add custom actions
  - name: convert_to_customer
    steps:
      - validate: status = 'lead'
      - update: SalesContact SET status = 'customer', converted_at = now()
      - call: create_customer_account
      - notify: conversion_completed
```

## Quick Start: Build a CRM in 10 Lines

Here's a complete CRM system using stdlib:

```yaml
# import-crm.yaml
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/crm/organization_type
  - stdlib/geo/public_address
  - stdlib/i18n/country
  - stdlib/i18n/language

# That's it! You now have:
# - Contact management with email, phone, job titles
# - Organization hierarchy with legal identifiers
# - Address management with geocoding
# - Multi-language support
# - 20+ pre-built actions
# - All Trinity patterns, indexes, and validations
```

**Generate the complete system**:
```bash
specql generate import-crm.yaml
```

**What you get** (auto-generated):
- 6 PostgreSQL tables with Trinity pattern
- 50+ PL/pgSQL functions for CRUD and business logic
- GraphQL schema with mutations
- TypeScript types for frontend
- Test fixtures and validation

**Total time**: 2 minutes

## stdlib Entity Structure

Every stdlib entity follows consistent patterns:

### Metadata Header

```yaml
# SpecQL stdlib Entity: Contact
# Category: crm
# Version: 1.1.0
# Description: Individual contact information for CRM
#
# Usage:
#   import: stdlib/crm/contact
#   extends: { from: stdlib/crm/contact }
```

### Standard Fields

- **Identifiers**: Trinity pattern (pk_*, id, identifier) auto-added
- **Audit**: created_at, updated_at, deleted_at auto-added
- **Tenant**: tenant_id auto-added for multi-tenant schemas

### Built-in Actions

Every entity includes standard CRUD actions:
- `create_*` - Create new record
- `update_*` - Modify existing record
- `delete_*` - Soft delete (sets deleted_at)
- `activate_*` / `deactivate_*` - Status management

Plus domain-specific actions based on entity type.

## Best Practices

### ✅ DO: Start with stdlib, Extend as Needed

```yaml
# Import foundation
import:
  - stdlib/crm/contact

# Add only what's unique to your business
entity: RealEstateContact
extends:
  from: stdlib/crm/contact
fields:
  property_interests: json
  budget_range: enum(under_500k, 500k_1m, 1m_5m, over_5m)
  viewing_history: json
```

### ✅ DO: Combine Multiple stdlib Entities

```yaml
# Build complex systems from components
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/commerce/contract
  - stdlib/geo/public_address

# Link them together
entity: ServiceContract
extends:
  from: stdlib/commerce/contract
fields:
  service_provider: ref(Organization)
  primary_contact: ref(Contact)
  service_location: ref(PublicAddress)
```

### ❌ DON'T: Reinvent What stdlib Provides

```yaml
# ❌ Bad: Redefining what stdlib already has
entity: MyContact
fields:
  email: email!
  phone: phone
  first_name: text
  last_name: text
  # ... 20 more fields that stdlib already defines

# ✅ Good: Just import it
import:
  - stdlib/crm/contact
```

### ✅ DO: Use stdlib for Production Patterns

```yaml
# stdlib entities include production patterns
import:
  - stdlib/crm/organization  # Includes hierarchical support

# Automatically get:
# - parent: ref(Organization) for hierarchy
# - Recursive queries for tree navigation
# - Business validations (no circular references)
```

## Versioning

stdlib entities follow semantic versioning:
- **Major version** (1.x.x → 2.x.x): Breaking changes to schema
- **Minor version** (x.1.x → x.2.x): New fields or actions (backwards compatible)
- **Patch version** (x.x.1 → x.x.2): Bug fixes, documentation

**Lock your version** for production:
```yaml
import:
  - stdlib/crm/contact@1.1.0  # Lock to specific version
```

## Performance Characteristics

stdlib entities are optimized for production:

- **Indexes**: All foreign keys, common query fields auto-indexed
- **Constraints**: Rich type validations at database level
- **Queries**: Optimized JOIN paths and materialized views where appropriate
- **Caching**: Query planning hints for PostgreSQL

**Benchmarks** (Contact entity):
- INSERT: ~1ms
- UPDATE: ~0.8ms
- SELECT by id: ~0.3ms
- Complex JOIN: ~2-5ms

## Migration from Custom Entities

Already have custom entities? Gradually migrate to stdlib:

```yaml
# Step 1: Import stdlib alongside custom
import:
  - stdlib/crm/contact as StdContact

entity: MyCustomContact
# Keep your existing fields
# Use StdContact as reference

# Step 2: Migrate data
actions:
  - name: migrate_to_stdlib
    steps:
      - insert: Contact FROM MyCustomContact
      - update: MyCustomContact SET migrated = true

# Step 3: Switch to stdlib
# Replace MyCustomContact references with Contact
```

## Contributing to stdlib

Found a pattern that should be in stdlib? [Contribute it!](../../07_contributing/stdlib-contributions.md)

**Criteria for stdlib entities**:
1. **Universal applicability**: Used across multiple industries
2. **Production-proven**: Extracted from real systems
3. **Well-documented**: Clear use cases and examples
4. **Tested**: Comprehensive test coverage
5. **Versioned**: Semantic versioning with migration guides

## Showcase: Real-World Systems Built with stdlib

### Startup CRM (10 lines → Full system)

```yaml
import:
  - stdlib/crm/contact
  - stdlib/crm/organization
  - stdlib/geo/public_address

# Extend with custom sales fields
entity: Lead
extends:
  from: stdlib/crm/contact
fields:
  lead_score: integer(0, 100)
  source: enum(website, referral, cold_call, event)
  status: enum(new, qualified, proposal, closed_won, closed_lost)
```

### E-commerce Platform (15 lines → Multi-tenant system)

```yaml
import:
  - stdlib/commerce/order
  - stdlib/commerce/price
  - stdlib/crm/contact
  - stdlib/geo/public_address
  - stdlib/i18n/currency

entity: CustomerOrder
extends:
  from: stdlib/commerce/order
fields:
  customer: ref(Contact)
  shipping_address: ref(PublicAddress)
  billing_address: ref(PublicAddress)
  payment_currency: ref(Currency)
```

### Global SaaS Platform (20 lines → Multi-region, multi-language)

```yaml
import:
  - stdlib/crm/organization
  - stdlib/crm/contact
  - stdlib/i18n/country
  - stdlib/i18n/language
  - stdlib/i18n/locale
  - stdlib/time/timezone

# Multi-tenant with full i18n
entity: TenantOrganization
extends:
  from: stdlib/crm/organization
fields:
  default_language: ref(Language)!
  default_timezone: ref(Timezone)!
  supported_locales: list(ref(Locale))
  billing_country: ref(Country)!
```

## Next Steps

- [CRM Entities](crm/index.md) - Contact, Organization
- [Geographic Entities](geo/index.md) - Address, Location
- [Commerce Entities](commerce/index.md) - Order, Contract, Price
- [i18n Entities](i18n/index.md) - Country, Currency, Language
- [Extending stdlib](../05_guides/extending-stdlib.md) - Advanced customization

---

**stdlib eliminates months of schema design. Focus on what makes your business unique, not reinventing CRM for the 1000th time.**
