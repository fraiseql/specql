# Core Concepts: SpecQL Fundamentals

🏠 [Home](../INDEX.md) > Core Concepts

> **Master the four pillars of SpecQL: Actions, YAML-first design, Rich Types, and the Trinity Pattern**

## Overview

SpecQL's **core concepts** are the foundational principles that make it different from traditional frameworks. These four concepts work together to eliminate infrastructure complexity while keeping your focus on business logic.

## The Four Core Concepts

### 🎯 [Actions: Declarative Business Logic](actions.md)
**Write business workflows in YAML, get production PL/pgSQL functions**

Actions are SpecQL's **declarative business logic engine**. Instead of writing imperative code, you describe **what** should happen using steps, and SpecQL generates the **how** as optimized PL/pgSQL functions.

- **Validation chains** for multi-rule business logic
- **Transactional workflows** with automatic rollback
- **Error handling** built into the database layer
- **GraphQL mutations** auto-generated

### 📝 [Business YAML: Logic in YAML, Code for Infrastructure](business-yaml.md)
**Why SpecQL uses YAML for business logic and code for infrastructure**

SpecQL inverts traditional development: **define business domains in YAML, SpecQL generates all technical infrastructure**. This separation lets you focus on what matters—your business logic—while SpecQL handles production system complexity.

- **YAML for business rules** (what your app does)
- **Generated code for infrastructure** (how it works)
- **Version control friendly** business logic
- **Framework agnostic** backend generation

### 🔒 [Rich Types: Automatic Validation & Proper PostgreSQL Types](rich-types.md)
**SpecQL's type system: 49 scalar types + 15 composite types with automatic validation**

SpecQL includes **64 rich types** that automatically generate PostgreSQL CHECK constraints, range validation, proper data types, GraphQL scalars, and frontend input hints. No validation code needed in your application—it's all built into the database.

- **Email, phone, URL validation** with regex constraints
- **Numeric ranges** (age, percentage, coordinates)
- **Temporal types** (dates, times, durations)
- **Business types** (currency, tax IDs, postal codes)

### 🏗️ [Trinity Pattern: Three Ways to Reference Entities](trinity-pattern.md)
**SpecQL's core convention for entity identification**

The **Trinity Pattern** is SpecQL's convention for entity identification. Every entity table has three identity columns, each optimized for different use cases: primary key for performance, UUID for security, and human-readable identifier for usability.

- **Primary Key (pk_)**: Integer for joins and performance
- **UUID (id)**: Secure external references
- **Identifier**: Human-readable names/slugs

## How They Work Together

```yaml
# Example: Complete entity with all core concepts
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: email!              # Rich Type: auto-validates email
  first_name: text!          # Required field
  last_name: text!           # Required field
  status: enum(lead, qualified, customer)  # Business constraint

actions:
  - name: create_contact     # Action: auto-generates CRUD
  - name: qualify_lead       # Action: custom business logic
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified', qualified_at = now()
      - return: "Lead qualified successfully"
```

This YAML generates:
- ✅ PostgreSQL table with constraints (Trinity Pattern + Rich Types)
- ✅ PL/pgSQL functions with validation (Actions)
- ✅ GraphQL schema and resolvers
- ✅ TypeScript types for frontend
- ✅ Migration scripts and rollback

## Learning Path

### Start Here
1. **[Actions](actions.md)** - Understand declarative business logic
2. **[Rich Types](rich-types.md)** - Master the type system
3. **[Business YAML](business-yaml.md)** - Learn the YAML-first approach
4. **[Trinity Pattern](trinity-pattern.md)** - Entity identification fundamentals

### Next Steps
- **[Getting Started](../01_getting-started/index.md)** - Build your first backend
- **[Migration Guide](../02_migration/index.md)** - Import existing systems
- **[Guides](../05_guides/index.md)** - Practical implementation guides
- **[Reference](../06_reference/index.md)** - Complete API documentation

## Need Help?

- **Questions?** Open an [issue](https://github.com/fraiseql/specql/issues)
- **Community** Join our [Discord/Slack]


---

**Time to read: 10 minutes. Concepts covered: 4 foundational principles.**</content>
</xai:function_call
</xai:function_call name="read">
<parameter name="filePath">docs/05_guides/actions.md
