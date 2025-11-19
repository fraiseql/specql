# Standard Library (stdlib): Battle-Tested Entities & Actions

> **50+ production-ready entities and action patterns—the secret weapon that accelerates development by 10x**

## Overview

SpecQL's Standard Library (stdlib) is a comprehensive collection of **pre-built, battle-tested entities and actions** that handle common business patterns. Instead of starting from scratch, you import and customize proven components.

**Think of it as**: Rails scaffolding meets Django contrib, but for backend infrastructure.

## The Power of stdlib

### Without stdlib (Traditional Approach)

```yaml
# Build everything from scratch: 500+ lines
entity: Contact
fields:
  email: email!
  phone: phoneNumber
  # ... 20 more fields manually defined
  # ... validation logic
  # ... relationships
  # ... business rules

entity: Organization
fields:
  # ... another 30 fields
  # ... more relationships

# Repeat for Address, Location, Currency, etc.
```

**Time**: 2-3 days to build properly
**Lines**: 500+ lines of YAML
**Bugs**: High risk—easy to miss edge cases

### With stdlib (SpecQL Approach)

```yaml
# Import pre-built, extend as needed: 20 lines
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
from: stdlib/geo/public_address.yaml

# Customize only what's unique to your business
extend: Contact
  custom_fields:
    loyalty_tier: enum(bronze, silver, gold, platinum)
    internal_notes: richtext
```

**Time**: 30 minutes
**Lines**: 20 lines of YAML
**Bugs**: Minimal—stdlib is production-tested

**Result**: **10x faster development** with enterprise-grade reliability.

---

## stdlib Categories

### 🏢 CRM Entities (`stdlib/crm/`)

Pre-built entities for customer relationship management:

- **Contact** - Full contact management with 15+ fields
- **Organization** - Company/organization records
- **OrganizationType** - Business entity classifications

**Use Cases**:
- CRM systems
- B2B platforms
- Marketing automation
- Sales pipelines

**Example**:
```yaml
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml

# That's it! Full CRM foundation ready
```

[→ Complete CRM Guide](crm-entities.md)

---

### 🌍 Geographic Entities (`stdlib/geo/`)

International address and location management:

- **PublicAddress** - Structured addresses (ISO-compliant)
- **Location** - Geographic coordinates + metadata
- **AdministrativeUnit** - Countries, states, cities hierarchy
- **PostalCode** - Postal code validation and city mapping
- **LocationType** / **LocationLevel** - Location classification

**Standards-Based**:
- ISO 3166 (Country codes)
- PostGIS spatial queries

[→ Complete Geo Guide](geo-entities.md)

---

### 💰 Commerce Entities (`stdlib/commerce/`)

E-commerce and financial entities:

- **Price** - Multi-currency pricing with time-based rules
- **Order** - Order management and fulfillment
- **Contract** - Contract lifecycle management

**Features**:
- Multi-currency support
- Time-based pricing
- Order state machines

[→ Complete Commerce Guide](commerce-entities.md)

---

### 🌐 Internationalization (`stdlib/i18n/`)

Multi-language and localization support:

- **Country** - ISO 3166 country codes
- **Language** - ISO 639 language codes
- **Currency** - ISO 4217 currency codes
- **Locale** - BCP 47 locale identifiers

**Standards-Based**:
- ISO 3166 (Countries)
- ISO 639 (Languages)
- ISO 4217 (Currencies)
- BCP 47 (Locales)

[→ Complete i18n Guide](i18n-entities.md)

---

### 🏗️ Organization & Time Entities (`stdlib/org/`, `stdlib/time/`, `stdlib/tech/`, `stdlib/common/`)

Enterprise infrastructure entities:

**Organization** (`stdlib/org/`):
- **OrganizationalUnit** - Hierarchical org structures (departments, divisions)
- **OrganizationalUnitLevel** - Level definitions

**Time** (`stdlib/time/`):
- **Calendar** - Date dimension table for temporal analytics

**Technology** (`stdlib/tech/`):
- **OperatingSystem** - OS lifecycle management
- **OperatingSystemPlatform** - OS family classification

**Common Reference** (`stdlib/common/`):
- **Industry** - Hierarchical industry classification
- **Genre** - General-purpose categorization

**Use Cases**:
- HR systems (org hierarchies)
- Analytics dashboards (temporal analysis)
- IT asset management (OS tracking)
- Business categorization (industries)

[→ Complete Org/Time/Tech Guide](org-time-tech-entities.md)

---

### ⚡ Action Patterns (`stdlib/actions/`)

Pre-built business logic templates that generate production-ready PostgreSQL functions:

**CRUD Patterns**:
- `crud/create` - Enhanced entity creation with duplicate detection
- `crud/update` - Partial updates with field tracking
- `crud/delete` - Dependency-aware deletion

**State Machine Patterns**:
- `state_machine/transition` - Simple state transitions
- `state_machine/guarded_transition` - Complex transitions with business rules

**Validation Patterns**:
- `validation/validation_chain` - Multi-rule validation

**Batch Patterns**:
- `batch/bulk_operation` - Bulk processing with error handling

**Multi-Entity Patterns**:
- `multi_entity/coordinated_update` - Atomic multi-entity operations
- `multi_entity/saga_orchestrator` - Distributed transaction patterns

**Composite Patterns**:
- `composite/workflow_orchestrator` - Multi-step business processes
- `composite/conditional_workflow` - Branching workflows

**Key Benefit**: Transform 200 lines of PL/pgSQL into 20 lines of YAML.

[→ Complete Action Patterns Guide](action-patterns.md)

---

### Standards-Based Design

stdlib entities follow international standards wherever possible:
- ISO 3166 (Country codes)
- PostGIS integration for spatial queries
- Multi-language address support

**Use Cases**:
- E-commerce shipping
- Store locators
- Logistics platforms
- Geographic analytics

**Example**:
```yaml
from: stdlib/geo/public_address.yaml
from: stdlib/geo/location.yaml

entity: Store
  fields:
    name: text!
    address: ref(PublicAddress)
    location: ref(Location)  # For spatial queries
```

[→ Complete Geographic Guide](geo-entities.md)

---

### 💰 Commerce Entities (`stdlib/commerce/`)

E-commerce and transaction management:

- **Price** - Multi-currency pricing with tax rules
- **Order** - Order lifecycle management
- **Contract** - Business contracts and agreements

**Features**:
- ISO 4217 currency codes
- Tax calculation support
- Order state machines
- Multi-currency handling

**Use Cases**:
- E-commerce platforms
- SaaS billing
- Marketplace systems
- Subscription services

**Example**:
```yaml
from: stdlib/commerce/price.yaml
from: stdlib/commerce/order.yaml

entity: Product
  fields:
    name: text!
    base_price: ref(Price)
```

[→ Complete Commerce Guide](commerce-entities.md)

---

### 🌐 Internationalization (`stdlib/i18n/`)

Multi-language and localization support:

- **Country** - ISO 3166 country data
- **Continent** - Geographic continents
- **Language** - ISO 639 language codes
- **Locale** - BCP 47 locale identifiers
- **Currency** - ISO 4217 currency definitions
- **CountryLocale** - Country-specific locale preferences

**Standards-Based**:
- ISO 3166 (Countries)
- ISO 639 (Languages)
- BCP 47 (Locales)
- ISO 4217 (Currencies)

**Use Cases**:
- Multi-language platforms
- International e-commerce
- Localized content delivery
- Regional pricing

**Example**:
```yaml
from: stdlib/i18n/country.yaml
from: stdlib/i18n/language.yaml
from: stdlib/i18n/currency.yaml

entity: LocalizedProduct
  fields:
    title: text!
    language: ref(Language)
    currency: ref(Currency)
```

[→ Complete i18n Guide](i18n-entities.md)

---

### 🏛️ Organizational Structure (`stdlib/org/`)

Enterprise organizational hierarchy:

- **OrganizationalUnit** - Departments, teams, divisions
- **OrganizationalUnitLevel** - Hierarchy levels

**Features**:
- Self-referencing hierarchy
- Multi-level depth support
- Manager relationships
- Reporting structures

**Use Cases**:
- Enterprise HR systems
- Organizational charts
- Permission hierarchies
- Cost center tracking

**Example**:
```yaml
from: stdlib/org/organizational_unit.yaml

entity: Employee
  fields:
    name: text!
    department: ref(OrganizationalUnit)
    reports_to: ref(OrganizationalUnit)
```

[→ Complete Org Structure Guide](org-entities.md)

---

### ⏰ Time & Calendar (`stdlib/time/`)

Temporal and calendar management:

- **Calendar** - Calendar systems (Gregorian, Julian, etc.)

**Use Cases**:
- Scheduling systems
- Event management
- Multi-calendar support

---

### 💻 Technology Reference (`stdlib/tech/`)

Technology platform data:

- **OperatingSystem** - OS identifiers and versions
- **OperatingSystemPlatform** - Platform classifications

**Use Cases**:
- Device management
- Software compatibility
- System monitoring
- Analytics platforms

---

## 🎬 Action Patterns (`stdlib/actions/`)

Pre-built business logic patterns that handle common workflows.

### CRUD Operations (`stdlib/actions/crud/`)

Standard create, read, update, delete patterns:

```yaml
from: stdlib/actions/crud/create.yaml
from: stdlib/actions/crud/update.yaml
from: stdlib/actions/crud/delete.yaml

# Automatic soft-delete, audit trails, validation
```

**Features**:
- Automatic `deleted_at` handling (soft delete)
- Audit trail generation (`created_by`, `updated_by`)
- Input validation
- Optimistic locking support

---

### State Machines (`stdlib/actions/state_machine/`)

Workflow state transition patterns:

```yaml
from: stdlib/actions/state_machine/transition.yaml
from: stdlib/actions/state_machine/guarded_transition.yaml

# Example: Order workflow
action: process_order
  steps:
    - transition: Order.status
      from: pending
      to: processing
      guard: payment_confirmed = true
```

**Features**:
- Valid state transition enforcement
- Guard conditions
- Transition hooks
- Event logging

---

### Validation Patterns (`stdlib/actions/validation/`)

Complex validation workflows:

```yaml
from: stdlib/actions/validation/validation_chain.yaml
from: stdlib/actions/validation/recursive_dependency_validator.yaml
```

**Patterns**:
- Multi-step validation chains
- Circular dependency detection
- Recursive validation
- Custom business rules

---

### Batch Operations (`stdlib/actions/batch/`)

Bulk data processing:

```yaml
from: stdlib/actions/batch/bulk_operation.yaml

# Process thousands of records efficiently
action: bulk_update_prices
  batch_size: 100
  steps:
    - foreach: products
      - update: Price SET amount = amount * 1.1
```

**Features**:
- Chunked processing
- Progress tracking
- Error recovery
- Transaction management

---

### Multi-Entity Patterns (`stdlib/actions/multi_entity/`)

Complex cross-entity workflows:

```yaml
from: stdlib/actions/multi_entity/parent_child_cascade.yaml
from: stdlib/actions/multi_entity/coordinated_update.yaml
from: stdlib/actions/multi_entity/saga_orchestrator.yaml
```

**Patterns**:
- **Cascade**: Parent-child operations (delete order → delete line items)
- **Coordinated Update**: Update multiple entities atomically
- **Saga**: Distributed transaction orchestration
- **Event-Driven**: Event-based coordination

---

### Composite Workflows (`stdlib/actions/composite/`)

Multi-step business processes:

```yaml
from: stdlib/actions/composite/workflow_orchestrator.yaml
from: stdlib/actions/composite/conditional_workflow.yaml
from: stdlib/actions/composite/retry_orchestrator.yaml
```

**Features**:
- Multi-step workflows with rollback
- Conditional branching
- Automatic retry logic
- Error handling strategies

---

### Temporal Patterns (`stdlib/actions/temporal/`)

Time-based business logic:

```yaml
from: stdlib/actions/temporal/non_overlapping_daterange.yaml

# Ensure no conflicting reservations
action: book_resource
  steps:
    - validate: no overlapping dateranges for resource
    - insert: Booking
```

**Use Cases**:
- Booking systems
- Scheduling
- Resource allocation
- Time-series data

---

## 📐 Schema Patterns (`stdlib/schema/`)

Advanced database patterns:

### Temporal Schemas

```yaml
from: stdlib/schema/temporal/temporal_scd_type2_helper.yaml
from: stdlib/schema/temporal/temporal_non_overlapping_daterange.yaml
```

**Patterns**:
- **SCD Type 2**: Slowly changing dimensions (versioned history)
- **Non-Overlapping**: Date range constraint validation

### Aggregate Views

```yaml
from: stdlib/schema/aggregate_view.yaml

# Auto-generate materialized views for analytics
```

### Validation Templates

```yaml
from: stdlib/schema/validation/validation_template_inheritance.yaml

# Reusable validation logic across entities
```

---

## 🚀 Quick Start: Build a CRM in 10 Minutes

```yaml
# File: entities/my_crm.yaml

# Import pre-built CRM entities
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
from: stdlib/geo/public_address.yaml
from: stdlib/commerce/order.yaml
from: stdlib/i18n/currency.yaml
from: stdlib/i18n/country.yaml

# Extend with your custom fields
extend: Contact
  custom_fields:
    loyalty_tier: enum(bronze, silver, gold, platinum)
    lifetime_value: money
    marketing_consent: boolean
    preferences: jsonb

extend: Organization
  custom_fields:
    annual_revenue: money
    employee_count: integer(1, 1000000)
    industry_vertical: text

# Add custom actions
action: qualify_lead
  entity: Contact
  steps:
    - validate: status = 'lead'
    - validate: email IS NOT NULL
    - update: Contact SET status = 'qualified', qualified_at = NOW()
    - notify: sales_team

action: upgrade_tier
  entity: Contact
  steps:
    - validate: loyalty_tier != 'platinum'
    - if: lifetime_value > 10000
      - update: Contact SET loyalty_tier = 'platinum'
    - if: lifetime_value > 5000
      - update: Contact SET loyalty_tier = 'gold'
    - notify: customer_success_team
```

**Generate**:

```bash
specql generate entities/my_crm.yaml --output db/schema/

# Generated:
# - 8 PostgreSQL tables (Contact, Organization, Address, etc.)
# - 50+ database fields (all validated)
# - 12 foreign keys and indexes
# - 4 business logic functions
# - GraphQL schema with 15+ queries/mutations
# - TypeScript types (200+ lines)
```

**Result**: Production-ready CRM backend in 45 lines of YAML + 10 minutes.

---

## 🎯 Best Practices

### DO: Import and Extend

```yaml
# ✅ GOOD: Import stdlib, customize incrementally
from: stdlib/crm/contact.yaml

extend: Contact
  custom_fields:
    internal_notes: richtext
    account_manager: ref(Employee)
```

### DON'T: Copy-Paste stdlib

```yaml
# ❌ BAD: Copying stdlib code loses future updates
entity: Contact
  fields:
    # ... 50 lines copied from stdlib ...
```

**Why**: stdlib entities are versioned and improved over time. Importing keeps you up-to-date.

---

### DO: Compose Multiple stdlib Modules

```yaml
# ✅ GOOD: Combine stdlib entities for powerful results
from: stdlib/crm/contact.yaml
from: stdlib/geo/public_address.yaml
from: stdlib/commerce/order.yaml
from: stdlib/i18n/currency.yaml

# Full international e-commerce CRM ready!
```

---

### DO: Use stdlib Actions for Common Patterns

```yaml
# ✅ GOOD: Leverage pre-built state machines
from: stdlib/actions/state_machine/transition.yaml

action: ship_order
  steps:
    - transition: Order.status
      from: paid
      to: shipped
      guard: inventory_allocated = true
    - notify: customer
```

---

### DON'T: Reinvent Complex Patterns

```yaml
# ❌ BAD: Writing saga orchestration from scratch
action: complex_transaction
  steps:
    # 50+ lines of manual transaction management
    # Easy to get wrong, hard to maintain
```

**Instead**: Use `stdlib/actions/multi_entity/saga_orchestrator.yaml`

---

## 📊 stdlib Coverage

| Domain | Entities | Actions | Schema Patterns |
|--------|----------|---------|-----------------|
| CRM | 3 | 5 | 2 |
| Geographic | 10 | 3 | 1 |
| Commerce | 3 | 8 | 2 |
| i18n | 7 | 0 | 0 |
| Organization | 2 | 2 | 1 |
| Time | 1 | 2 | 3 |
| Technology | 2 | 0 | 0 |
| **TOTAL** | **28** | **20** | **9** |

**Coverage**: ~80% of common business application needs covered by stdlib.

---

## 🔄 Migration Path: Legacy Code → stdlib

If you have existing code, stdlib makes migration easier:

### From Django Models

```python
# Django: 100 lines
class Contact(models.Model):
    email = models.EmailField(unique=True)
    phone = PhoneNumberField()
    organization = models.ForeignKey(Organization)
    # ... 20 more fields
```

**Becomes**:

```yaml
# SpecQL: 2 lines
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
```

---

### From TypeScript + Prisma

```typescript
// Prisma schema: 150 lines
model Contact {
  id String @id @default(uuid())
  email String @unique
  phone String?
  organizationId String
  organization Organization @relation(fields: [organizationId])
  // ... 20 more fields
}

model Organization {
  // ... 30 more fields
}
```

**Becomes**:

```yaml
# SpecQL: 2 lines
from: stdlib/crm/contact.yaml
from: stdlib/crm/organization.yaml
```

---

## 🎁 Hidden Gems

### 1. **Recursive Dependency Validation**

```yaml
from: stdlib/actions/validation/recursive_dependency_validator.yaml

# Automatically detects circular dependencies in org charts
```

### 2. **Non-Overlapping Date Ranges**

```yaml
from: stdlib/actions/temporal/non_overlapping_daterange.yaml

# Prevents double-booking resources automatically
```

### 3. **Slowly Changing Dimensions (SCD Type 2)**

```yaml
from: stdlib/schema/temporal/temporal_scd_type2_helper.yaml

# Full version history tracking with time-travel queries
```

### 4. **Saga Orchestration**

```yaml
from: stdlib/actions/multi_entity/saga_orchestrator.yaml

# Distributed transaction patterns with rollback support
```

---

## 🔮 Future stdlib Additions

Planned for upcoming releases:

- **Finance**: Accounts, Ledgers, Transactions (double-entry accounting)
- **Healthcare**: Patients, Appointments, Medical Records (HIPAA-compliant)
- **Education**: Students, Courses, Enrollments
- **Logistics**: Shipments, Tracking, Warehouses
- **HR**: Employees, Payroll, Benefits

**Want to contribute?** See [Contributing stdlib Entities](../08_contributing/stdlib-development.md)

---

## 📚 Learn More

- [CRM Entities Guide](crm-entities.md) - Full contact management
- [Geographic Entities Guide](geo-entities.md) - Address and location handling
- [Commerce Entities Guide](commerce-entities.md) - E-commerce patterns
- [i18n Entities Guide](i18n-entities.md) - Internationalization support
- [Action Patterns Guide](action-patterns.md) - Pre-built business logic

---

## 💡 Key Takeaways

1. **stdlib = 10x faster development** - Pre-built entities save weeks of work
2. **Production-tested** - Used in real applications, edge cases handled
3. **Standards-compliant** - ISO codes, proper validation, international support
4. **Composable** - Mix and match entities to build complex systems
5. **Extensible** - Import and customize, don't reinvent

**SpecQL's stdlib is your secret weapon for building backends at light speed.** ⚡

---

*Last updated: 2025-11-19*
