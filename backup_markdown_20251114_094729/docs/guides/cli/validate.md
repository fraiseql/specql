# Validate Commands - YAML Validation and Checking

The `specql validate` command checks your YAML entity specifications for syntax errors, consistency issues, and best practices. This guide covers validation options, error types, and fixing common issues.

## 🎯 What You'll Learn

- YAML syntax validation
- Entity consistency checking
- Impact declaration validation
- Table code uniqueness verification
- Error types and resolution
- Integration with development workflows

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- [Entity specifications created](../getting-started/first-entity.md)
- Understanding of YAML syntax

## 💡 Validation Overview

### What Gets Validated

**SpecQL validates:**
- ✅ **YAML Syntax** - Proper YAML formatting and structure
- ✅ **Entity Schema** - Required fields, data types, constraints
- ✅ **Pattern Configuration** - Pattern parameters and compatibility
- ✅ **Impact Declarations** - Mutation side effects and dependencies
- ✅ **Table Codes** - Uniqueness across all entities
- ✅ **Cross-References** - Entity relationships and foreign keys

### Validation Pipeline

```mermaid
graph LR
    A[YAML Files] --> B[Syntax Check]
    B --> C[Schema Validation]
    C --> D[Pattern Validation]
    D --> E[Impact Validation]
    E --> F[Cross-Reference Check]
    F --> G[Table Code Check]
    G --> H[Validation Report]
```

## 🚀 Basic Validation

### Validate Single Entity

```bash
# Validate one entity file
specql validate entities/user.yaml

# Expected output (success):
# ✅ entities/user.yaml: Valid

# Expected output (errors):
# ❌ entities/user.yaml: Validation error
#   Line 12: Unknown field type 'string' (use 'text')
```

### Validate Multiple Entities

```bash
# Validate specific files
specql validate entities/user.yaml entities/company.yaml

# Validate all entities in directory
specql validate entities/*.yaml

# Validate recursively
specql validate entities/**/*.yaml
```

### Verbose Validation

```bash
# Show detailed validation output
specql validate entities/user.yaml --verbose

# Example verbose output:
# ✅ entities/user.yaml: Valid
#   ✓ YAML syntax
#   ✓ Entity schema
#   ✓ Pattern configuration
#   ✓ Impact declarations
#   ✓ Cross-references
```

## 🔍 Advanced Validation

### Impact Validation

```bash
# Validate impact declarations
specql validate entities/user.yaml --check-impacts

# Validates:
# - All entities in 'write:' exist
# - All entities in 'read:' exist
# - No circular dependencies
# - Complete impact declarations
```

### Table Code Checking

```bash
# Check table code uniqueness
specql check-codes entities/*.yaml

# Example output:
# 📊 Table Code Report
#
# ✅ All codes are unique
#
# Entities with table codes:
#   • 012311 - Contact (entities/crm/contact.yaml)
#   • 012312 - Company (entities/crm/company.yaml)
#   • 042001 - Order (entities/commerce/order.yaml)
```

### Schema Comparison

```bash
# Compare YAML with existing database schema
specql diff entities/user.yaml --compare db/schema/10_tables/user.sql

# Example output:
# Comparing: entities/user.yaml → db/schema/10_tables/user.sql
#
# --- Generated
# +++ Existing
# @@ -12,6 +12,7 @@
#    company INTEGER NOT NULL REFERENCES crm.tb_company(id),
#    status TEXT NOT NULL CHECK (status IN ('lead', 'qualified', 'customer')),
# +  priority TEXT,  -- Added in existing, not in YAML
#
# ✅ 1 file compared
# ⚠️  1 difference found
```

## 📊 Understanding Validation Errors

### YAML Syntax Errors

**Error:**
```
❌ entities/user.yaml: Parse error
  Line 5: mapping values are not allowed here
```

**Cause:** Invalid YAML indentation or structure

**Fix:**
```yaml
# Incorrect
name: user
fields:
  id: uuid
    email: string  # Wrong indentation

# Correct
name: user
fields:
  id: uuid
  email: string
```

### Schema Validation Errors

**Error:**
```
❌ entities/user.yaml: Validation error
  Field 'email': Unknown type 'string' (use 'text', 'uuid', etc.)
```

**Cause:** Invalid field type

**Fix:**
```yaml
# Incorrect
fields:
  email: string

# Correct
fields:
  email: text
```

### Pattern Configuration Errors

**Error:**
```
❌ entities/user.yaml: Validation error
  Pattern 'state_machine': Missing required field 'initial_state'
```

**Cause:** Incomplete pattern configuration

**Fix:**
```yaml
# Incorrect
patterns:
  - name: state_machine
    states: [active, inactive]

# Correct
patterns:
  - name: state_machine
    initial_state: inactive
    states: [active, inactive]
    transitions:
      - from: inactive
        to: active
        trigger: activate
```

### Impact Declaration Errors

**Error:**
```
❌ entities/order.yaml: Impact validation error
  Mutation 'create_order': References undefined entity 'Shipment'
```

**Cause:** Impact declaration references non-existent entity

**Fix:**
```yaml
# In order.yaml
patterns:
  - name: mutation
    mutations:
      create_order:
        impacts:
          write: [Order]  # ✅ Order exists
          read: [Product]  # ✅ Product exists
          # Remove reference to undefined Shipment
```

### Cross-Reference Errors

**Error:**
```
❌ entities/order.yaml: Cross-reference error
  Field 'customer_id': References undefined entity 'Customer'
```

**Cause:** Foreign key references non-existent entity

**Fix:**
```yaml
# Ensure Customer entity exists, or fix reference
fields:
  customer_id: uuid  # References customer.id
  # Either create entities/customer.yaml or change to:
  # customer_id: uuid  # References user.id (if that's correct)
```

### Table Code Conflicts

**Error:**
```
❌ Duplicate table codes found

⚠️  Code 012311 assigned to multiple entities:
  • Contact (entities/crm/contact.yaml)
  • Customer (entities/crm/customer.yaml)
```

**Cause:** Multiple entities have the same table code

**Fix:**
```yaml
# In contact.yaml
table_code: 012311

# In customer.yaml - change to unique code
table_code: 012312
```

## 🛠️ Validation Configuration

### Validation Rules

**SpecQL validates against these rules:**

| Rule Category | Examples |
|---------------|----------|
| **YAML Syntax** | Valid YAML, proper indentation |
| **Entity Schema** | Required fields, valid types |
| **Field Types** | text, uuid, integer, decimal, boolean, timestamp |
| **Pattern Config** | Pattern-specific requirements |
| **Relationships** | Foreign key references exist |
| **Table Codes** | Unique 6-digit codes |
| **Impact Declarations** | All referenced entities exist |

### Custom Validation Rules

```yaml
# In confiture.yaml
validation:
  strict: true
  custom_rules:
    - name: require_descriptions
      pattern: "description"
      message: "All entities must have descriptions"

    - name: max_field_count
      max_fields: 20
      message: "Entities should not have more than 20 fields"
```

## 🔧 Validation Workflows

### Development Workflow

```bash
# 1. Edit entity
vim entities/user.yaml

# 2. Validate immediately
specql validate entities/user.yaml

# 3. Fix any errors
# (edit file)

# 4. Re-validate
specql validate entities/user.yaml

# 5. Continue development
specql generate schema entities/user.yaml
```

### Pre-commit Validation

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Validate all changed YAML files
for file in $(git diff --cached --name-only | grep '\.yaml$'); do
    if [[ $file == entities/* ]]; then
        specql validate "$file"
        if [ $? -ne 0 ]; then
            echo "❌ Validation failed for $file"
            exit 1
        fi
    fi
done

echo "✅ All YAML files validated"
```

### CI/CD Validation

```yaml
# .github/workflows/validate.yml
name: Validate Entities

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install SpecQL
        run: pip install specql

      - name: Validate entities
        run: specql validate entities/**/*.yaml --verbose

      - name: Check table codes
        run: specql check-codes entities/**/*.yaml

      - name: Validate impacts
        run: specql validate entities/**/*.yaml --check-impacts
```

## 📋 Validation Best Practices

### Error Prevention
- **Validate early** - Check YAML as you write
- **Use IDE validation** - Set up real-time checking
- **Follow conventions** - Use consistent naming and structure
- **Review patterns** - Double-check complex pattern configurations

### Error Resolution
- **Read error messages** - They contain specific guidance
- **Check line numbers** - Go directly to the problem
- **Use --verbose** - Get detailed validation output
- **Test fixes** - Re-validate after making changes

### Quality Assurance
- **Consistent formatting** - Use YAML formatters
- **Documentation** - Add descriptions to entities and fields
- **Version control** - Commit only validated YAML
- **Code reviews** - Have others review entity specifications

## 🆘 Troubleshooting

### "Validation succeeds locally but fails in CI"

**Possible causes:**
- Different SpecQL versions
- Environment-specific configuration
- File encoding issues
- Path differences

**Debug steps:**
```bash
# Check SpecQL version
specql --version

# Validate with verbose output
specql validate entities/user.yaml --verbose

# Check file encoding
file entities/user.yaml

# Test with absolute paths
specql validate /full/path/to/entities/user.yaml
```

### "Impact validation errors"

**Common issues:**
- Missing entity definitions
- Incorrect entity names
- Circular dependencies
- Incomplete impact declarations

**Resolution:**
```bash
# List all entities
ls entities/*.yaml

# Check entity names match
grep "name:" entities/*.yaml

# Validate individual impacts
specql validate entities/user.yaml --check-impacts
```

### "Table code conflicts"

**Resolution:**
```bash
# See current codes
specql check-codes entities/*.yaml --format json

# Find conflicts
specql check-codes entities/*.yaml | grep "assigned to multiple"

# Update conflicting codes
vim entities/customer.yaml  # Change table_code
```

### "Schema diff shows unexpected changes"

**Possible causes:**
- Manual database modifications
- Different generation environments
- Cached or stale schema files

**Resolution:**
```bash
# Regenerate schema
specql generate schema entities/user.yaml --force

# Check database state
psql $DATABASE_URL -c "\d user"

# Compare with fresh generation
specql diff entities/user.yaml --compare db/schema/10_tables/user.sql
```

## 📊 Validation Metrics

### Quality Metrics
- **Validation success rate**: >99% of commits
- **Error resolution time**: <5 minutes average
- **Most common errors**: Track and address patterns
- **Validation coverage**: 100% of YAML files

### Process Metrics
- **Validation frequency**: Multiple times per development session
- **CI/CD failure rate**: <1% due to validation issues
- **Time to fix**: <10 minutes for typical errors
- **Prevention effectiveness**: >90% of errors caught before commit

## 🎉 Summary

The `specql validate` command provides:
- ✅ **Comprehensive validation** - Syntax, schema, patterns, impacts
- ✅ **Clear error messages** - Specific guidance for fixes
- ✅ **Multiple validation modes** - Basic, verbose, impact checking
- ✅ **CI/CD integration** - Automated validation in pipelines
- ✅ **Table code management** - Uniqueness verification
- ✅ **Schema comparison** - Diff against existing database

## 🚀 What's Next?

- **[Generate Commands](generate.md)** - Schema and test generation
- **[Test Commands](test.md)** - Running and managing tests
- **[Performance Commands](performance.md)** - Benchmarking and optimization
- **[Workflows](workflows.md)** - Common development patterns

**Ready to ensure YAML quality? Let's explore more commands! 🚀**