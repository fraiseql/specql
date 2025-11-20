# Troubleshooting Guide

> **Status**: 🚧 Documentation in Progress
>
> This page is planned but not yet complete. Check back soon!

## Overview

This guide will provide solutions to common problems encountered when using SpecQL, from installation issues to runtime errors.

## Coming Soon

This documentation will cover:
- [ ] Installation and setup issues
- [ ] Code generation errors
- [ ] Database connection problems
- [ ] Schema migration failures
- [ ] Runtime validation errors
- [ ] Performance issues
- [ ] GraphQL integration problems
- [ ] Common error messages and solutions

## Related Documentation

- [Error Handling](error-handling.md) - Error handling patterns
- [Getting Started](../01_getting-started/index.md) - Setup guide
- [CLI Commands](../06_reference/cli-commands.md) - Command reference

## Common Issues (Interim)

### Installation Issues

#### Error: "command not found: specql"

**Solution**: The package may not be in your PATH.

```bash
# Try running with python -m
python -m specql --version

# Or install in user space
pip install --user specql

# Or use pipx
pipx install specql
```

#### Error: "No module named 'specql'"

**Solution**: Ensure you're using the correct Python environment.

```bash
# Check Python version
python --version  # Should be 3.11+

# Install in current environment
pip install specql

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install specql
```

### Code Generation Issues

#### Error: "Schema not found: crm"

**Solution**: Create the schema first in your database.

```sql
CREATE SCHEMA IF NOT EXISTS crm;
```

#### Error: "Referenced entity not found: Company"

**Solution**: Generate all entities together or ensure referenced entities are generated first.

```bash
# Generate all entities at once
specql generate entities/*.yaml

# Or generate in dependency order
specql generate entities/company.yaml entities/contact.yaml
```

#### Error: "Invalid field type: xyz"

**Solution**: Check the field type against supported rich types.

Valid types: `text`, `integer`, `boolean`, `date`, `datetime`, `email`, `url`, `phoneNumber`, `money`, `ref(Entity)`, `enum(...)`, `list(type)`

### Database Issues

#### Error: "permission denied for schema"

**Solution**: Grant proper permissions to your database user.

```sql
GRANT USAGE ON SCHEMA crm TO myuser;
GRANT ALL ON ALL TABLES IN SCHEMA crm TO myuser;
GRANT ALL ON ALL SEQUENCES IN SCHEMA crm TO myuser;
```

#### Error: "relation does not exist"

**Solution**: Ensure tables are created in dependency order.

```bash
# Run framework schemas first
psql -f db/schema/00_framework/app_schema.sql

# Then tables in order
psql -f db/schema/10_tables/*.sql
psql -f db/schema/20_helpers/*.sql
```

### Validation Errors

#### Error: "check constraint violated"

**Solution**: Ensure data meets validation rules (email format, enum values, etc.).

```yaml
# Check your enum values
status: enum(lead, qualified, customer)

# Ensure input matches one of these values
INSERT INTO crm.tb_contact (status) VALUES ('lead');  -- OK
INSERT INTO crm.tb_contact (status) VALUES ('pending');  -- ERROR
```

#### Error: "foreign key constraint violated"

**Solution**: Ensure referenced entities exist.

```bash
# Create Company first
INSERT INTO crm.tb_company (name) VALUES ('Acme Corp') RETURNING pk_company;

# Then use that pk in Contact
INSERT INTO crm.tb_contact (fk_company, ...) VALUES (1, ...);
```

## Getting Help

If you can't find a solution:
1. **Search GitHub Issues**: [github.com/fraiseql/specql/issues](https://github.com/fraiseql/specql/issues)
2. **Open a New Issue**: Include error messages, YAML files, and steps to reproduce
3. **Check the Docs**: Browse [Core Concepts](../03_core-concepts/business-yaml.md)
4. **Community**: Join our Discord/Slack for real-time help

## Questions?

If you encounter an issue not covered here:
- Check [Error Handling Guide](error-handling.md)
- Review [Getting Started](../01_getting-started/index.md)
- Open an issue with detailed error information
- Ask in community discussions

---

*Last Updated*: 2025-11-20
