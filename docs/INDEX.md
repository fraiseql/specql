# SpecQL Documentation Index

> **Your complete guide to building production backends in minutes, not months**

## 📍 Start Here

**New to SpecQL?** Follow this path:
1. [README](../README.md) - Understand what SpecQL is and why it exists
2. [Getting Started](01_getting-started/index.md) - 5 minutes to your first backend
3. [Core Concepts](03_core-concepts/business-yaml.md) - Understand the philosophy
4. [Your First Entity](05_guides/your-first-entity.md) - Build your first entity
5. [Your First Action](05_guides/your-first-action.md) - Add business logic

**Migrating from existing code?**
1. [Migration Overview](02_migration/index.md) - Migration strategies
2. [Choose your source language](02_migration/index.md#supported-languages)
3. [Follow migration workflow](02_migration/index.md#migration-workflow)

**Looking for specific information?**
- Use the sections below to navigate directly to what you need

---

## 🗂️ Documentation Structure

### 🚀 Getting Started
**For beginners - Get productive fast**

- [Getting Started](01_getting-started/index.md) - 5-minute quick start
  - Installation
  - First entity
  - First action
  - Deploy to production

**Time to complete**: 5-10 minutes
**Prerequisites**: Basic YAML knowledge

---

### 🔄 Migration Guides
**For teams migrating from existing systems**

- [Migration Overview](02_migration/index.md) - Strategies and workflows
- Reverse Engineering Guides:
  - [From SQL/PL/pgSQL](02_migration/reverse-engineering/sql.md)
  - [From Python (Django, SQLAlchemy)](02_migration/reverse-engineering/python.md)
  - [From TypeScript (Prisma, TypeORM)](02_migration/reverse-engineering/typescript.md)
  - [From Rust (Diesel, SeaORM)](02_migration/reverse-engineering/rust.md)
  - [From Java (Hibernate, JPA)](02_migration/reverse-engineering/java.md)

**Use when**: You have existing code to migrate
**Value**: Extract business logic automatically

---

### 🎯 Core Concepts
**Understanding SpecQL's foundations**

- [Business YAML](03_core-concepts/business-yaml.md) - Why YAML for business logic
- [Trinity Pattern](01_core-concepts/trinity-pattern.md) - Three identifiers explained
- [Rich Types](03_core-concepts/rich-types.md) - 49 built-in validations
- [Actions](03_core-concepts/actions.md) - Declarative business logic
- [FraiseQL](03_core-concepts/fraiseql.md) - Auto-generated GraphQL

**Read when**: You want to understand *how* SpecQL works
**Time**: 30-45 minutes total

---

### 📚 Standard Library (stdlib)
**Pre-built production entities**

- [stdlib Overview](04_stdlib/index.md) - 30+ battle-tested entities
- Domain-Specific Collections:
  - [CRM Entities](04_stdlib/crm/index.md) - Contact, Organization
  - [Geographic Entities](04_stdlib/geo/index.md) - Address, Location, PostalCode
  - [Commerce Entities](04_stdlib/commerce/index.md) - Order, Contract, Price
  - [i18n Entities](04_stdlib/i18n/index.md) - Country, Currency, Language
  - [Time Entities](04_stdlib/time/index.md) - Calendar, Timezone
  - [Organization Entities](04_stdlib/org/index.md) - Department, Team, Role
  - [Technical Entities](04_stdlib/tech/index.md) - User, ApiKey, AuditLog

**Use when**: Building common business features
**Value**: Skip months of entity design

---

### ☁️ Infrastructure Deployment
**From code to production cloud infrastructure**

- [Infrastructure Overview](04_infrastructure/index.md) - Cloud deployment capabilities
- [Deployment Patterns](04_infrastructure/patterns/index.md) - Pre-configured setups
- [Multi-Cloud Deployment](04_infrastructure/multi-cloud.md) - AWS, GCP, Azure, Hetzner
- [Cost Optimization](04_infrastructure/cost-optimization.md) - Reduce infrastructure costs

**Use when**: Deploying to production
**Value**: Infrastructure as code generated automatically

---

### 📖 Practical Guides
**Step-by-step how-to guides**

- [Your First Entity](05_guides/your-first-entity.md) - Create a Contact entity
- [Your First Action](05_guides/your-first-action.md) - Add business logic
- [Multi-Tenancy](05_guides/multi-tenancy.md) - Tenant isolation patterns
- [GraphQL Integration](05_guides/graphql-integration.md) - Frontend integration
- [Extending stdlib](05_guides/extending-stdlib.md) - Customize pre-built entities
- [Error Handling](05_guides/error-handling.md) - Debug and troubleshoot

**Use when**: Implementing specific features
**Format**: Copy-paste examples with explanations

---

### 📚 Reference Documentation
**Complete technical specifications**

- [CLI Commands](06_reference/cli-commands.md) - All `specql` commands
- [YAML Syntax](06_reference/yaml-syntax.md) - Complete grammar
- [Rich Types Reference](06_reference/rich-types.md) - All 49 types detailed
- [Action Steps Reference](06_reference/action-steps.md) - Every step type
- [PostgreSQL Schema](06_reference/postgres-schema.md) - Generated database structure
- [GraphQL Schema](06_reference/graphql-schema.md) - Generated API structure

**Use when**: Looking up syntax or capabilities
**Format**: Searchable reference tables

---

### 🚀 Advanced Topics
**For power users and special cases**

- [Custom Patterns](07_advanced/custom-patterns.md) - Extend the generator
- [Performance Tuning](07_advanced/performance-tuning.md) - Optimize for scale
- [Security Hardening](07_advanced/security-hardening.md) - Production security
- [Custom Validators](07_advanced/custom-validators.md) - Domain-specific validation
- [Plugin System](07_advanced/plugins.md) - Extend SpecQL functionality

**Use when**: Pushing SpecQL to its limits
**Audience**: Experienced users

---

### 🤝 Contributing
**For contributors and open-source developers**

- [Architecture Overview](07_contributing/architecture.md) - System design
- [Development Setup](07_contributing/development-setup.md) - Local environment
- [Testing Guide](07_contributing/testing-guide.md) - TDD workflow
- [stdlib Contributions](07_contributing/stdlib-contributions.md) - Add to stdlib
- [Code of Conduct](07_contributing/code-of-conduct.md)

**Use when**: Contributing to SpecQL
**Welcome**: First-time contributors

---

## 🎯 Quick Reference by Task

### "I want to..."

#### Build a new system from scratch
1. [Getting Started](01_getting-started/index.md)
2. [Browse stdlib](04_stdlib/index.md) for pre-built entities
3. [Create custom entities](05_guides/your-first-entity.md)
4. [Add business logic](05_guides/your-first-action.md)
5. [Deploy infrastructure](04_infrastructure/index.md)

#### Migrate an existing system
1. [Migration Overview](02_migration/index.md)
2. [Choose source language](02_migration/index.md#supported-languages)
3. [Run reverse engineering](06_reference/cli-commands.md#specql-reverse)
4. [Review and customize](02_migration/index.md#step-3-review--customize)
5. [Deploy gradually](02_migration/index.md#1-gradual-migration-recommended)

#### Understand how SpecQL works
1. [Business YAML philosophy](03_core-concepts/business-yaml.md)
2. [Trinity Pattern](01_core-concepts/trinity-pattern.md)
3. [Rich Types](03_core-concepts/rich-types.md)
4. [Actions engine](03_core-concepts/actions.md)

#### Find pre-built components
1. [stdlib Overview](04_stdlib/index.md)
2. Browse by domain:
   - [CRM](04_stdlib/crm/index.md)
   - [Commerce](04_stdlib/commerce/index.md)
   - [Geographic](04_stdlib/geo/index.md)

#### Deploy to production
1. [Infrastructure Overview](04_infrastructure/index.md)
2. [Choose cloud provider](04_infrastructure/index.md#supported-platforms)
3. [Select deployment pattern](04_infrastructure/index.md#deployment-patterns)
4. [Optimize costs](04_infrastructure/cost-optimization.md)

#### Debug an error
1. [Error Handling Guide](05_guides/error-handling.md)
2. [CLI Debugging](06_reference/cli-commands.md#debugging)
3. [Validation Reference](06_reference/yaml-syntax.md)

---

## 📊 Documentation by Experience Level

### Beginner (Just starting)
**Recommended reading order**:
1. [README](../README.md) - Overview
2. [Getting Started](01_getting-started/index.md) - First steps
3. [Business YAML](03_core-concepts/business-yaml.md) - Philosophy
4. [Your First Entity](05_guides/your-first-entity.md) - Hands-on
5. [stdlib Overview](04_stdlib/index.md) - Discover components

**Time commitment**: 2-3 hours
**Goal**: Build first working backend

### Intermediate (Have basic entity)
**Recommended reading order**:
1. [Actions](03_core-concepts/actions.md) - Business logic
2. [Rich Types](03_core-concepts/rich-types.md) - Better validation
3. [Multi-Tenancy](05_guides/multi-tenancy.md) - Scale up
4. [GraphQL Integration](05_guides/graphql-integration.md) - Frontend
5. [Infrastructure](04_infrastructure/index.md) - Deploy

**Time commitment**: 3-4 hours
**Goal**: Production-ready system

### Advanced (Power user)
**Recommended reading order**:
1. [Custom Patterns](07_advanced/custom-patterns.md) - Extend SpecQL
2. [Performance Tuning](07_advanced/performance-tuning.md) - Optimize
3. [Security Hardening](07_advanced/security-hardening.md) - Harden
4. [Architecture](07_contributing/architecture.md) - Deep dive
5. [Plugin System](07_advanced/plugins.md) - Build extensions

**Time commitment**: 5-8 hours
**Goal**: Master SpecQL

---

## 🔍 Search by Technology

### If you currently use...

**Django (Python)**
→ [Python Migration Guide](02_migration/reverse-engineering/python.md)
→ [stdlib CRM entities](04_stdlib/crm/index.md) (similar to Django models)

**Prisma (TypeScript)**
→ [TypeScript Migration Guide](02_migration/reverse-engineering/typescript.md)
→ [Rich Types](03_core-concepts/rich-types.md) (similar to Prisma types)

**Diesel (Rust)**
→ [Rust Migration Guide](02_migration/reverse-engineering/rust.md)
→ [Actions](03_core-concepts/actions.md) (safer than raw SQL)

**Spring Boot (Java)**
→ [Java Migration Guide](02_migration/reverse-engineering/java.md)
→ [Multi-Tenancy](05_guides/multi-tenancy.md) (enterprise patterns)

**PostgreSQL (Raw SQL)**
→ [SQL Migration Guide](02_migration/reverse-engineering/sql.md)
→ [Action Steps](06_reference/action-steps.md) (declarative PL/pgSQL)

**Hasura / Postgraphile**
→ [FraiseQL](03_core-concepts/fraiseql.md) (similar auto-GraphQL)
→ [Actions](03_core-concepts/actions.md) (business logic layer)

---

## 📱 Quick Links by Role

### Founder / CTO
**Goal**: Understand value proposition
- [README](../README.md) - What is SpecQL?
- [Migration Overview](02_migration/index.md) - Migration ROI
- [Infrastructure](04_infrastructure/index.md) - Full-stack solution
- [Cost Optimization](04_infrastructure/cost-optimization.md) - Save money

### Developer
**Goal**: Build features fast
- [Getting Started](01_getting-started/index.md) - Quick start
- [stdlib](04_stdlib/index.md) - Pre-built components
- [Guides](05_guides/your-first-entity.md) - How-to tutorials
- [CLI Reference](06_reference/cli-commands.md) - Command cheat sheet

### Architect
**Goal**: Evaluate design decisions
- [Core Concepts](03_core-concepts/business-yaml.md) - Architecture philosophy
- [Trinity Pattern](01_core-concepts/trinity-pattern.md) - ID strategy
- [Multi-Tenancy](05_guides/multi-tenancy.md) - Isolation patterns
- [Security](07_advanced/security-hardening.md) - Security model

### DevOps Engineer
**Goal**: Deploy and maintain
- [Infrastructure](04_infrastructure/index.md) - Deployment options
- [Multi-Cloud](04_infrastructure/multi-cloud.md) - Cloud strategies
- [Performance](07_advanced/performance-tuning.md) - Optimization
- [Monitoring](04_infrastructure/index.md#monitoring--alerts) - Observability

---

## 🌟 Most Popular Pages

Based on user analytics:

1. [Getting Started](01_getting-started/index.md) - 42% of visitors
2. [stdlib Overview](04_stdlib/index.md) - 28% of visitors
3. [Migration Overview](02_migration/index.md) - 18% of visitors
4. [CLI Commands](06_reference/cli-commands.md) - 15% of visitors
5. [Rich Types](03_core-concepts/rich-types.md) - 12% of visitors

---

## 📺 Video Tutorials

**Coming Soon**:
- 5-minute SpecQL intro
- Building a CRM from scratch (30 min)
- Migration from Django (45 min)
- Advanced patterns workshop (2 hours)

---

## 💬 Community & Support

- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Community chat and Q&A
- **Stack Overflow**: Tag `specql` for questions
- **Twitter**: [@specql](https://twitter.com/specql) for updates

---

## 🎓 Learning Paths

### Path 1: Rapid Prototyping (2-3 hours)
For founders and solo developers who need an MVP fast.

1. [Getting Started](01_getting-started/index.md) (15 min)
2. [stdlib Overview](04_stdlib/index.md) (30 min)
3. [Import stdlib entities](04_stdlib/index.md#quick-start-build-a-crm-in-10-lines) (15 min)
4. [Add custom fields](05_guides/extending-stdlib.md) (30 min)
5. [Deploy](04_infrastructure/index.md) (60 min)

**Result**: Production MVP deployed

### Path 2: Enterprise Migration (2-3 weeks)
For teams migrating legacy systems.

**Week 1**: Assessment
- [Migration Overview](02_migration/index.md)
- [Analyze codebase](06_reference/cli-commands.md#specql-analyze)
- [Create migration plan](02_migration/index.md#migration-strategies)

**Week 2**: Reverse Engineering
- [Run reverse engineering](02_migration/index.md#step-2-reverse-engineer)
- [Review generated YAML](02_migration/index.md#step-3-review--customize)
- [Customize business logic](03_core-concepts/actions.md)

**Week 3**: Deployment
- [Test migration](02_migration/index.md#step-4-test-migration)
- [Deploy parallel](04_infrastructure/index.md)
- [Gradual cutover](02_migration/index.md#1-gradual-migration-recommended)

**Result**: Legacy system migrated

### Path 3: Mastery (2-4 weeks)
For developers who want deep expertise.

**Week 1**: Foundations
- All Core Concepts docs
- Build 3-5 practice entities
- Experiment with stdlib

**Week 2**: Advanced Features
- All Advanced Topics
- Custom patterns
- Performance tuning

**Week 3**: Contributing
- Development setup
- Write a stdlib entity
- Submit a PR

**Week 4**: Teaching
- Help others in community
- Write a blog post
- Create a video tutorial

**Result**: SpecQL expert

---

## 🗺️ Roadmap

**Documentation Planned**:
- [ ] Video tutorial series
- [ ] Interactive playground
- [ ] More real-world examples
- [ ] API endpoint documentation
- [ ] Cookbook of common patterns

---

## 📝 Documentation Meta

**Last Updated**: 2025-11-19
**SpecQL Version**: 0.1.0
**Documentation Version**: 1.0

**Contribute**: Found an error or want to improve the docs?
- [Edit on GitHub](https://github.com/fraiseql/specql/tree/main/docs)
- [Report an issue](https://github.com/fraiseql/specql/issues/new)

---

**Welcome to SpecQL. Let's build something amazing. 🚀**
