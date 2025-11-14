# Entities Guide

**Define your business objects** - The foundation of your SpecQL application

Entities are the core business objects in your SpecQL application. They define what data you store and what operations you can perform on that data.

## 🎯 Entity Structure

Every entity follows this structure:

```yaml
entity: Contact                    # Required: PascalCase name
schema: crm                        # Required: Database schema
description: "Customer contacts"   # Optional: Human-readable description
organization: customer             # Optional: Business domain grouping

fields:                            # Required: Data structure
  # Field definitions

actions:                           # Optional: Business logic
  # Action definitions
```

## 📋 Required Properties

### entity
**Type**: String (PascalCase)
**Required**: Yes

The entity name defines your business object. It must be:
- PascalCase (start with capital letter)
- Singular noun (Contact, not Contacts)
- Unique within your schema

```yaml
entity: Contact          # ✅ Good
entity: contact          # ❌ lowercase
entity: Contacts         # ❌ plural
entity: contact_info     # ❌ snake_case
```

### schema
**Type**: String (lowercase)
**Required**: Yes

Database schema for organization. Common patterns:
- `crm` - Customer relationship management
- `sales` - Sales operations
- `inventory` - Product inventory
- `finance` - Financial data
- `admin` - Administrative data

```yaml
schema: crm             # ✅ Good
schema: CRM             # ❌ uppercase
schema: customer_rm     # ❌ underscores
```

## 📝 Optional Properties

### description
**Type**: String
**Required**: No

Human-readable description of the entity. Used for:
- Documentation generation
- API descriptions
- Developer understanding

```yaml
description: "Customer contact information with lead status"
```

### organization
**Type**: String
**Required**: No

Business domain grouping. Used for:
- Registry system organization
- Migration file paths
- Logical grouping of related entities

```yaml
organization: customer   # Groups with other customer-related entities
```

## 🗄️ Database Impact

SpecQL generates database objects with consistent naming:

### Table Names
```
{schema}.tb_{entity}
crm.tb_contact          # Contact entity in crm schema
sales.tb_opportunity    # Opportunity entity in sales schema
```

### Function Names
```
{schema}.{action_name}
crm.qualify_lead        # Action in Contact entity
sales.close_deal        # Action in Opportunity entity
```

### GraphQL Names
```
app.{action_name}       # GraphQL wrapper functions
app.qualify_lead
app.create_contact
```

## 📊 Complete Entity Example

```yaml
entity: Contact
schema: crm
description: "Customer contact information and lead management"
organization: customer

fields:
  email: text
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)
  phone: text
  notes: text

actions:
  - name: qualify_lead
    description: "Convert lead to qualified prospect"
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'

  - name: create_contact
    description: "Create new contact with validation"
    steps:
      - validate: email IS NOT NULL
      - insert: Contact
```

## 🏗️ Entity Design Patterns

### Core Business Entities
Central to your business domain:

```yaml
# Customer management
entity: Customer
schema: crm
description: "Primary customer records"

entity: Contact
schema: crm
description: "Contact persons at customer organizations"
```

### Transaction Entities
Business transactions and events:

```yaml
# Sales process
entity: Opportunity
schema: sales
description: "Sales opportunities and deals"

entity: Quote
schema: sales
description: "Price quotes for opportunities"
```

### Reference Entities
Lookup tables and classifications:

```yaml
# Product catalog
entity: Product
schema: inventory
description: "Product catalog items"

entity: Category
schema: inventory
description: "Product categories"
```

## 🔗 Entity Relationships

Entities reference each other using `ref()`:

```yaml
entity: Contact
schema: crm
fields:
  customer: ref(Customer)    # References Customer entity
  manager: ref(User)         # References User entity
```

SpecQL automatically generates:
- Foreign key constraints
- JOIN queries in views
- Type-safe references

## 📈 Entity Evolution

Entities can evolve over time:

```yaml
entity: Contact
schema: crm
fields:
  # Original fields
  email: text
  first_name: text

  # Added later
  last_name: text
  phone: text
  status: enum(lead, qualified, customer)
```

Generated migrations are **idempotent** - safe to run multiple times.

## 🎯 Best Practices

### Naming Conventions
- Use clear, descriptive names
- Follow PascalCase for entities
- Use lowercase for schemas
- Be consistent across your application

### Schema Organization
- Group related entities in same schema
- Use schemas to separate concerns
- Consider team ownership boundaries

### Description Quality
- Write descriptions for other developers
- Include business context
- Explain entity purpose and scope

### Field Organization
- Put required fields first
- Group related fields together
- Use consistent naming patterns

## 🔍 Common Patterns

### User Management
```yaml
entity: User
schema: admin
description: "System users and authentication"
organization: security

entity: Role
schema: admin
description: "User roles and permissions"
organization: security
```

### Content Management
```yaml
entity: Article
schema: content
description: "Blog posts and articles"
organization: marketing

entity: Category
schema: content
description: "Content categorization"
organization: marketing
```

### E-commerce
```yaml
entity: Product
schema: catalog
description: "Product catalog"
organization: commerce

entity: Order
schema: sales
description: "Customer orders"
organization: commerce
```

## 🚀 Next Steps

- **[Fields Guide](fields.md)** - Define your data structure
- **[Relationships Guide](relationships.md)** - Connect entities together
- **[Actions Guide](../actions/overview.md)** - Add business logic
- **[Trinity Pattern Guide](trinity_pattern.md)** - Understand data access patterns

## 📚 Related Topics

- **[YAML Reference](../../03_reference/yaml/entity_schema.md)** - Complete entity syntax
- **[Database Schema](../../03_reference/generated/postgresql_schema.md)** - Generated table structures
- **[Migration Guide](../../02_guides/deployment/migrations.md)** - Database deployment