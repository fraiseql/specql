# SpecQL Documentation

**Universal Code Generation Platform** - PostgreSQL + GraphQL Today, Multi-Language Tomorrow

[![Version](https://img.shields.io/badge/version-0.4.0--alpha-blue.svg)](https://github.com/fraiseql/specql)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## What is SpecQL?

SpecQL transforms business-domain YAML into production-ready code:

```yaml
# 15 lines YAML → 2000+ lines production code (133x leverage)
entity: Contact
schema: crm

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Auto-generates**:
- ✅ PostgreSQL tables (Trinity pattern: pk_*, id, identifier)
- ✅ PL/pgSQL functions with type safety
- ✅ GraphQL schema + TypeScript types
- ✅ React Apollo hooks
- ✅ Test files (pgTAP + pytest)

## Documentation Structure

### 🚀 Getting Started (5-minute win)
**For new users** - Get productive immediately

- **[Quick Start Guide](00_getting_started/QUICKSTART.md)** - Install SpecQL and generate your first multi-language backend
- **[CRM System Example](06_examples/CRM_SYSTEM_COMPLETE.md)** - Complete customer relationship management system
- **[E-commerce Example](06_examples/ECOMMERCE_SYSTEM.md)** - Full online store with inventory and orders
- **[Simple Blog Example](06_examples/SIMPLE_BLOG.md)** - Content management system
- **[User Authentication Example](06_examples/USER_AUTHENTICATION.md)** - Complete auth system with permissions
- **[Multi-Tenant SaaS Example](06_examples/MULTI_TENANT_SAAS.md)** - Enterprise multi-tenant platform

### 🎓 Tutorials (Learning path)
**Step-by-step guides** - Learn by doing

#### Beginner
- **[Contact Manager](01_tutorials/beginner/contact_manager.md)** - Simple CRUD operations

#### Intermediate
- **[CRM System Example](06_examples/CRM_SYSTEM_COMPLETE.md)** - Complete customer relationship management
- **[E-commerce Example](06_examples/ECOMMERCE_SYSTEM.md)** - Full online store with inventory

#### Advanced
- **[Multi-Tenant SaaS Example](06_examples/MULTI_TENANT_SAAS.md)** - Enterprise patterns and tenant isolation

### 📖 Guides (Complete features)
**In-depth explanations** - Master specific topics

#### Database Design
- **[Entities](02_guides/database/entities.md)** - Entity definition and schemas
- **[Fields](02_guides/database/fields.md)** - Complete field type reference

#### Actions & Business Logic
- **[Action Overview](02_guides/actions/overview.md)** - Action system architecture
- **[All Step Types](02_guides/actions/all_step_types.md)** - Complete 25+ step reference

#### Testing & Quality Assurance
- **[Test Generation Guide](02_guides/TEST_GENERATION.md)** - Generate comprehensive test suites
- **[Test Reverse Engineering](02_guides/TEST_REVERSE_ENGINEERING.md)** - Analyze existing tests
- **[CI/CD Integration](02_guides/CI_CD_INTEGRATION.md)** - Automate testing in pipelines

#### Migration Guides
- **[Java Migration Guide](guides/JAVA_MIGRATION_GUIDE.md)** - Migrating Java projects to SpecQL
- **[Rust Migration Guide](guides/RUST_MIGRATION_GUIDE.md)** - Migrating Rust projects to SpecQL
- **[TypeScript Migration Guide](guides/TYPESCRIPT_MIGRATION_GUIDE.md)** - Migrating TypeScript projects to SpecQL

### 🔧 Reference (Complete specifications)
**Technical details** - Look up syntax and APIs

#### YAML Specification
- **[Complete Reference](03_reference/yaml/complete_reference.md)** - Full YAML syntax

#### CLI Reference
- **[Command Reference](03_reference/cli/command_reference.md)** - All commands

### 🏗️ Architecture (How it works)
**System internals** - Understand the codebase

- **[Overview](04_architecture/overview.md)** - High-level architecture
- **[Source Structure](04_architecture/source_structure.md)** - Codebase organization
- **[TypeScript Parser Reference](04_architecture/typescript_parser_reference.md)** - TypeScript parsing details
- **[TypeScript Prisma Migration Guide](04_architecture/typescript_prisma_migration_guide.md)** - Migration guidance

### 💡 Examples (Real code)
**Working examples** - Copy and modify

- **[Simple Contact](06_examples/simple_contact/)** - Basic entity with actions
- **[CRM System](06_examples/CRM_SYSTEM_COMPLETE.md)** - Complete customer relationship management
- **[E-commerce System](06_examples/ECOMMERCE_SYSTEM.md)** - Full online store with inventory
- **[Simple Blog](06_examples/SIMPLE_BLOG.md)** - Content management system
- **[User Authentication](06_examples/USER_AUTHENTICATION.md)** - Complete auth system
- **[Multi-Tenant SaaS](06_examples/MULTI_TENANT_SAAS.md)** - Enterprise multi-tenant platform

## Quick Navigation

| I want to... | Go to... |
|-------------|----------|
| Get started quickly | [Quick Start](00_getting_started/QUICKSTART.md) |
| Learn step-by-step | [Tutorials](01_tutorials/) |
| Understand features | [Guides](02_guides/) |
| Look up syntax | [Reference](03_reference/) |
| See examples | [Examples](06_examples/) |
| Contribute code | [Contributing](07_contributing/) |
| Get help | [Troubleshooting](08_troubleshooting/) |

## Current Status

**✅ Production Ready**:
- PostgreSQL table generation with Trinity pattern
- PL/pgSQL action compilation
- GraphQL schema + TypeScript types
- React Apollo hooks
- Pattern library system
- Reverse engineering (PostgreSQL → SpecQL)
- Test generation (pgTAP + pytest)
- CI/CD generation capabilities

**🔜 Coming Soon**:
- Multi-language backend (Java, Rust, TypeScript, Go)
- Frontend generation (React, Vue, Angular)
- Universal CI/CD expression
- Universal infrastructure expression

## Community

- **Discord**: Real-time help and discussion
- **GitHub Discussions**: Questions and answers
- **GitHub Issues**: Bug reports and feature requests
- **Contributing**: See [Contributing Guide](07_contributing/)

---

**SpecQL**: From business requirements to production code in minutes, not months.