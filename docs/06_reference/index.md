# Reference: Complete API Documentation

🏠 [Home](../INDEX.md) > Reference

> **Comprehensive reference for SpecQL's YAML syntax, CLI commands, and type system**

## Overview

The **reference** section provides complete, detailed documentation for all SpecQL features, APIs, and syntax. Use this section when you need precise technical information.

## YAML Syntax & Schema

### 📝 [YAML Syntax Reference](yaml-syntax.md)
**Complete reference for SpecQL's declarative YAML syntax**

- Entity definition syntax
- Field types and constraints
- Action declarations
- Import and extension patterns
- Schema organization

### 🎯 [Action Steps Reference](action-steps-reference.md)
**Detailed reference for action step types and syntax**

- Validation steps and conditions
- Update and insert operations
- Control flow (loops, conditionals)
- Error handling and rollback
- Advanced step patterns

### 🔧 [Action Steps Guide](action-steps.md)
**Practical guide to writing action steps with examples**

- Common action patterns
- Step sequencing and dependencies
- Business logic implementation
- Testing and debugging actions

## Type System

### 🎨 [Rich Types Reference](rich-types-reference.md)
**Quick lookup for all 49 scalar types + 15 composite types**

- Contact and communication types
- Geographic and location types
- Financial and business types
- Temporal and scheduling types
- Validation rules and constraints

### 📊 [Scalar Types Guide](scalar-types.md)
**Detailed guide to scalar types with examples**

- Type categories and use cases
- Validation patterns and regex
- Database constraints generated
- GraphQL scalar mappings

## Command Line Interface

### 💻 [CLI Commands Reference](cli-commands.md)
**Complete reference for the `specql` command-line interface**

- Installation and setup
- Code generation commands
- Migration and deployment tools
- Validation and testing utilities
- Configuration options

### 🔄 [CLI Migration Guide](cli-migration.md)
**Using SpecQL CLI for database migrations and schema updates**

- Migration workflow
- Schema versioning
- Rollback procedures
- Migration best practices
- Troubleshooting migrations

## Database & Schema

### 🗄️ [Schema Registry](schema-registry.md)
**Understanding SpecQL's schema organization and registry system**

- Schema naming conventions
- Entity registration
- Cross-schema relationships
- Schema versioning
- Registry management

## Quick Reference Tables

### Type Quick Reference
| Category | Types | Use Case |
|----------|-------|----------|
| **Contact** | `email`, `phone`, `url` | User communication |
| **Identity** | `uuid`, `tax_id`, `ssn` | Personal identification |
| **Financial** | `currency`, `percentage`, `money` | Business transactions |
| **Temporal** | `date`, `datetime`, `duration` | Time-based data |
| **Geographic** | `country`, `postal_code`, `coordinates` | Location data |

### Action Step Quick Reference
| Step Type | Purpose | Example |
|-----------|---------|---------|
| `validate` | Check conditions | `validate: status = 'active'` |
| `update` | Modify data | `update: User SET last_login = now()` |
| `insert` | Create records | `insert: AuditLog VALUES (...)` |
| `return` | End action | `return: "Success message"` |

### CLI Command Quick Reference
```bash
# Generate code from YAML
specql generate entity.yaml

# Validate YAML syntax
specql validate entity.yaml

# Create migration
specql migrate create "add user table"

# Run migrations
specql migrate up

# Generate types only
specql generate --types entity.yaml
```

## Navigation

### By Task
- **Writing YAML** → [YAML Syntax](yaml-syntax.md)
- **Defining Actions** → [Action Steps](action-steps.md)
- **Choosing Types** → [Rich Types](rich-types-reference.md)
- **Running Commands** → [CLI Reference](cli-commands.md)
- **Database Schema** → [Schema Registry](schema-registry.md)

### By Experience Level
- **Beginner** → [YAML Syntax](yaml-syntax.md), [CLI Commands](cli-commands.md)
- **Intermediate** → [Action Steps](action-steps.md), [Rich Types](rich-types-reference.md)
- **Advanced** → [Action Steps Reference](action-steps-reference.md), [Schema Registry](schema-registry.md)

## Related Documentation

- **[Core Concepts](../03_core-concepts/index.md)** - Understanding SpecQL fundamentals
- **[Guides](../05_guides/index.md)** - Practical implementation tutorials
- **[Advanced Topics](../07_advanced/index.md)** - Performance and customization
- **[Standard Library](../04_stdlib/index.md)** - Pre-built entities

## Need Help?


- **Bug Reports?** Open an [issue](https://github.com/fraiseql/specql/issues)
- **Feature Requests?** Start a [discussion](https://github.com/fraiseql/specql/discussions)
- **Community** Join our [Discord/Slack]

---

**Reference pages: 8 | Last updated: Documentation cleanup in progress**</content>
</xai:function_call
</xai:function_call name="list">
<parameter name="path">docs/07_advanced
