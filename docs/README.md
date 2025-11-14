# SpecQL Documentation

**Universal Code Generation Platform** - PostgreSQL + GraphQL Today, Multi-Language Tomorrow

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/sst/specql)
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

- **[Quick Start](00_getting_started/quickstart.md)** - Generate your first schema in 5 minutes
- **[Installation](00_getting_started/installation.md)** - Setup and prerequisites
- **[First Project](00_getting_started/first_project.md)** - Build a complete CRM system
- **[Core Concepts](00_getting_started/core_concepts.md)** - Trinity pattern, schemas, actions
- **[FAQ](00_getting_started/faq.md)** - Common questions answered

### 🎓 Tutorials (Learning path)
**Step-by-step guides** - Learn by doing

#### Beginner
- **[Contact Manager](01_tutorials/beginner/contact_manager.md)** - Simple CRUD operations
- **[Blog Platform](01_tutorials/beginner/blog_platform.md)** - Content management
- **[Task Tracker](01_tutorials/beginner/task_tracker.md)** - Project management basics

#### Intermediate
- **[SaaS Multi-Tenant](01_tutorials/intermediate/saas_multi_tenant.md)** - Enterprise patterns
- **[E-commerce Platform](01_tutorials/intermediate/ecommerce_platform.md)** - Complex business logic
- **[Pattern Library Usage](01_tutorials/intermediate/pattern_library_usage.md)** - Reusable patterns

#### Advanced
- **[Custom Patterns](01_tutorials/advanced/custom_patterns.md)** - Create your own patterns
- **[Reverse Engineering](01_tutorials/advanced/reverse_engineering.md)** - Import existing databases
- **[Test Generation](01_tutorials/advanced/test_generation.md)** - Comprehensive testing

### 📖 Guides (Complete features)
**In-depth explanations** - Master specific topics

#### Database Design
- **[Entities](02_guides/database/entities.md)** - Entity definition and schemas
- **[Fields](02_guides/database/fields.md)** - Complete field type reference
- **[Relationships](02_guides/database/relationships.md)** - Foreign keys and references
- **[Actions](02_guides/database/actions.md)** - Business logic overview
- **[Trinity Pattern](02_guides/database/trinity_pattern.md)** - pk_*, id, identifier explained
- **[Rich Types](02_guides/database/rich_types.md)** - money, dimensions, contact_info, etc.

#### Actions & Business Logic
- **[Action Overview](02_guides/actions/overview.md)** - Action system architecture
- **[All Step Types](02_guides/actions/all_step_types.md)** - Complete 25+ step reference
- **[Validation](02_guides/actions/validation.md)** - Data validation patterns
- **[Conditionals](02_guides/actions/conditionals.md)** - if/switch logic
- **[Data Manipulation](02_guides/actions/data_manipulation.md)** - CRUD operations
- **[Error Handling](02_guides/actions/error_handling.md)** - Exception management

#### Advanced Features
- **[Pattern Library](02_guides/patterns/overview.md)** - Reusable query/action patterns
- **[Frontend Integration](02_guides/frontend/graphql_integration.md)** - GraphQL + TypeScript
- **[CLI Usage](02_guides/cli/generate_command.md)** - Command-line interface
- **[Reverse Engineering](02_guides/advanced/reverse_engineering.md)** - Database import
- **[CI/CD Generation](02_guides/advanced/cicd_generation.md)** - Pipeline automation

### 🔧 Reference (Complete specifications)
**Technical details** - Look up syntax and APIs

#### YAML Specification
- **[Complete Reference](03_reference/yaml/complete_reference.md)** - Full YAML syntax
- **[Entity Schema](03_reference/yaml/entity_schema.md)** - Entity definitions
- **[Field Types](03_reference/yaml/field_types.md)** - All supported types
- **[Action Schema](03_reference/yaml/action_schema.md)** - Action definitions
- **[Step Types](03_reference/yaml/step_types.md)** - All 25+ step types

#### Generated Code
- **[PostgreSQL Schema](03_reference/generated/postgresql_schema.md)** - Table/view structures
- **[PL/pgSQL Functions](03_reference/generated/plpgsql_functions.md)** - Function signatures
- **[GraphQL Schema](03_reference/generated/graphql_schema.md)** - GraphQL API
- **[TypeScript Types](03_reference/generated/typescript_types.md)** - Type definitions

#### CLI Reference
- **[Command Reference](03_reference/cli/command_reference.md)** - All commands
- **[Generate Flags](03_reference/cli/generate_flags.md)** - Generation options
- **[Configuration](03_reference/cli/configuration.md)** - Config files

### 🏗️ Architecture (How it works)
**System internals** - Understand the codebase

- **[Overview](04_architecture/overview.md)** - High-level architecture
- **[Source Structure](04_architecture/source_structure.md)** - 24-directory codebase
- **[Parser Architecture](04_architecture/parser_architecture.md)** - YAML processing
- **[Generator System](04_architecture/schema_generator.md)** - Code generation
- **[Team Model](04_architecture/team_model.md)** - Development organization
- **[Universal AST](04_architecture/universal_ast.md)** - Cross-language abstraction

### 🔮 Vision & Roadmap (Future)
**Strategic direction** - What's coming next

- **[Current State](05_vision/current_state.md)** - Production-ready features
- **[Multi-Language](05_vision/multi_language.md)** - Java, Rust, TypeScript, Go
- **[Frontend Generation](05_vision/frontend_generation.md)** - React, Vue, Angular
- **[Universal CI/CD](05_vision/universal_cicd.md)** - Platform-agnostic pipelines
- **[Roadmap](05_vision/roadmap.md)** - 50-week development plan

### 💡 Examples (Real code)
**Working examples** - Copy and modify

- **[Simple Contact](06_examples/simple_contact/)** - Basic entity with actions
- **[E-commerce Order](06_examples/ecommerce_order/)** - Complex business logic
- **[CRM System](06_examples/crm_system/)** - Complete business application
- **[Simple Blog](06_examples/simple_blog/)** - Content management
- **[SaaS Multi-Tenant](06_examples/saas_multi_tenant/)** - Enterprise patterns

### 🤝 Contributing (Join the project)
**Development workflow** - How to contribute

- **[Getting Started](07_contributing/getting_started.md)** - Development setup
- **[Workflow](07_contributing/development_workflow.md)** - Git flow and processes
- **[Adding Features](07_contributing/adding_features.md)** - Feature development
- **[Writing Tests](07_contributing/writing_tests.md)** - Testing guidelines
- **[Code Style](07_contributing/code_style.md)** - Coding standards

### 🔍 Troubleshooting (Get help)
**Problem solving** - Common issues and solutions

- **[Common Errors](08_troubleshooting/common_errors.md)** - Error messages explained
- **[Debugging Guide](08_troubleshooting/debugging_guide.md)** - Debug techniques
- **[Performance Issues](08_troubleshooting/performance_issues.md)** - Optimization tips
- **[Getting Help](08_troubleshooting/getting_help.md)** - Community support

### 📚 API Reference (Developer docs)
**Technical APIs** - For extending SpecQL

- **[Python API](09_api_reference/python_api/)** - Internal APIs
- **[Generated API](09_api_reference/generated_api/)** - Generated code APIs

## Quick Navigation

| I want to... | Go to... |
|-------------|----------|
| Get started quickly | [Quick Start](00_getting_started/quickstart.md) |
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