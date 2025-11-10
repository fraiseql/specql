# SpecQL Documentation

## Getting Started
- [Installation](getting-started/installation.md)
- [Your First Entity](getting-started/your-first-entity.md)
- [Your First Action](getting-started/your-first-action.md)

## User Guides
- [Migration Guide](guides/migration-guide.md) - Migrate existing databases
- [Actions Guide](guides/actions-guide.md) - Write business logic
- [Multi-Tenancy](guides/multi-tenancy.md) - Multi-tenant architecture
- [Troubleshooting](guides/troubleshooting.md) - Common issues

## Reference
- [YAML Reference](reference/yaml-reference.md) - Complete syntax
- [CLI Reference](reference/cli-reference.md) - Command-line tools
- [Scalar Types](reference/scalar-types.md) - Field types
- [Generated SQL](reference/generated-sql.md) - What SpecQL produces

## Architecture
- [Business Logic Spec](architecture/SPECQL_BUSINESS_LOGIC_REFINED.md)
- [Integration Proposal](architecture/INTEGRATION_PROPOSAL.md)
- [Team Structure](architecture/TEAM_STRUCTURE.md)

## Contributing
- [Contributing Guide](contributing/CONTRIBUTING.md)
- [Development Setup](contributing/development-setup.md)
- [Testing Guide](contributing/testing.md)

## Quick Reference
- [Quick Reference](QUICK_REFERENCE.md) - Cheat sheet for common patterns

---

## Overview

SpecQL is a code generation tool that transforms YAML entity definitions into complete PostgreSQL schemas with GraphQL integration.

### Key Features
- **YAML-first**: Define entities in clean, readable YAML
- **Complete schemas**: Generates tables, indexes, functions, and GraphQL wrappers
- **Business logic**: Declarative actions replace stored procedures
- **Multi-tenant ready**: Built-in tenant isolation
- **Migration friendly**: Preserves existing table codes and structure

### Getting Started in 5 Minutes

1. **Install SpecQL**:
   ```bash
   uv add specql-generator
   ```

2. **Create your first entity**:
   ```yaml
   # entities/contact.yaml
   entity: Contact
   schema: crm
   fields:
     email: text
     name: text
   ```

3. **Generate schema**:
   ```bash
   specql generate entities/contact.yaml
   ```

4. **Apply to database**:
   ```bash
   psql mydb -f db/schema/10_tables/contact.sql
   ```

That's it! You now have a fully functional PostgreSQL table with GraphQL integration.

### Next Steps

- **Add relationships**: Use `ref(Entity)` for foreign keys
- **Add business logic**: Define `actions` for complex operations
- **Migrate existing data**: Follow the [Migration Guide](guides/migration-guide.md)
- **Set up multi-tenancy**: Configure the domain registry

### Support

- **Issues**: https://github.com/fraiseql/specql/issues
- **Discussions**: https://github.com/fraiseql/specql/discussions
- **Documentation**: You're reading it! 🎉