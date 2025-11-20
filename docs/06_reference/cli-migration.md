# CLI Migration Commands Reference

> **Complete reference for migrating existing codebases to SpecQL using the CLI**

## Overview

The SpecQL CLI provides powerful reverse engineering capabilities to migrate from existing frameworks (SQL, Python, TypeScript, Rust, Java) to SpecQL YAML. This reference covers all migration-related commands and workflows.

---

## Quick Start

```bash
# 1. Analyze codebase (generate migration report)
specql analyze --source python --path ./myapp/models/ --report migration-plan.md

# 2. Reverse engineer to SpecQL
specql reverse --source python --path ./myapp/models/ --output entities/

# 3. Review generated YAML
cat entities/*.yaml

# 4. Generate SQL and test
specql generate entities/*.yaml --output generated/
```

---

## Core Migration Commands

### `specql analyze`

Analyze existing codebase and generate migration complexity report.

```bash
specql analyze --source <TYPE> --path <PATH> [options]
```

**Options**:
- `--source TYPE` - Source type: `sql`, `python`, `typescript`, `rust`, `java`
- `--path PATH` - Path to source code directory or file
- `--framework FRAMEWORK` - Specific framework (e.g., `django`, `prisma`, `diesel`)
- `--report FILE` - Generate markdown migration report (default: stdout)
- `--json` - Output as JSON for programmatic use
- `--verbose` - Show detailed analysis

**Examples**:

```bash
# Analyze Django models
specql analyze --source python \
  --framework django \
  --path ./myapp/models/ \
  --report migration-plan.md

# Analyze Prisma schema
specql analyze --source typescript \
  --framework prisma \
  --path ./prisma/schema.prisma \
  --json > analysis.json

# Analyze SQL functions
specql analyze --source sql \
  --path ./database/functions/ \
  --verbose
```

**Output** (migration-plan.md):
```markdown
# Migration Analysis Report

**Source**: Python (Django)
**Path**: ./myapp/models/
**Entities Found**: 12
**Actions Detected**: 34
**Estimated Complexity**: Medium

## Entities to Migrate

### Contact (complexity: Low, confidence: 85%)
- Fields: 8
- Relationships: 2
- Validators: 3
- Estimated effort: 2 hours

### Order (complexity: High, confidence: 65%)
- Fields: 12
- Relationships: 5
- Business logic: Complex state machine
- Estimated effort: 8 hours

## Recommended Migration Order
1. Company (no dependencies)
2. Contact (depends on Company)
3. Product (no dependencies)
4. Order (depends on Contact, Product)
...
```

---

### `specql reverse`

Reverse engineer existing code to SpecQL YAML.

```bash
specql reverse --source <TYPE> --path <PATH> [options]
```

**Options**:
- `--source TYPE` - Source type: `sql`, `python`, `typescript`, `rust`, `java` (required)
- `--path PATH` - Path to source code (required)
- `--output DIR` - Output directory for SpecQL files (default: `./entities`)
- `--framework FRAMEWORK` - Specific framework
- `--include PATTERN` - Include only files matching glob pattern
- `--exclude PATTERN` - Exclude files matching glob pattern
- `--detect-patterns` - Auto-detect business patterns
- `--merge-with-schema` - Merge with existing SpecQL entities
- `--confidence-threshold PERCENT` - Minimum confidence level (default: 50%)
- `--preview` - Show what would be generated without writing files

**Examples**:

```bash
# SQL/PL/pgSQL Migration
specql reverse --source sql \
  --path ./database/functions/ \
  --output entities/ \
  --detect-patterns

# Django Migration
specql reverse --source python \
  --framework django \
  --path ./myapp/models/ \
  --output entities/ \
  --confidence-threshold 70

# Prisma Migration
specql reverse --source typescript \
  --framework prisma \
  --path ./prisma/schema.prisma \
  --output entities/

# Diesel Migration
specql reverse --source rust \
  --framework diesel \
  --path ./src/schema.rs \
  --output entities/

# JPA/Hibernate Migration
specql reverse --source java \
  --framework jpa \
  --path ./src/main/java/com/example/entity/ \
  --output entities/ \
  --confidence-threshold 40  # Lower threshold for Java

# Preview without writing
specql reverse --source python \
  --path ./models/ \
  --preview
```

**Output**:
```
✅ Analyzing source files...
   Found 12 entities, 34 actions

✅ Extracting models...
   Contact (confidence: 87%) ✅
   Company (confidence: 92%) ✅
   Order (confidence: 73%) ⚠️
   Payment (confidence: 45%) ⚠️  # Low confidence

✅ Detecting patterns...
   audit_trail: 8 entities
   soft_delete: 5 entities
   multi_tenant: 3 entities

✅ Generating SpecQL YAML...
   entities/contact.yaml (247 lines → 18 lines)
   entities/company.yaml (156 lines → 12 lines)
   entities/order.yaml (423 lines → 34 lines)

⚠️  Manual review recommended for:
   - entities/payment.yaml (low confidence: 45%)
   - entities/order.yaml (complex state machine detected)

✨ Migration complete! Review generated files in: entities/
```

---

### `specql diff`

Compare SpecQL-generated schema with existing database.

```bash
specql diff --old <OLD> --new <NEW> [options]
```

**Options**:
- `--old FILE` - Existing schema SQL file or database URL
- `--new FILE` - SpecQL-generated schema SQL file or YAML entities
- `--ignore-comments` - Ignore SQL comment differences
- `--ignore-order` - Ignore statement order
- `--format FORMAT` - Output format: `text`, `json`, `html` (default: `text`)

**Examples**:

```bash
# Compare SQL files
specql diff \
  --old database/schema.sql \
  --new generated/schema.sql

# Compare against live database
specql diff \
  --old postgresql://user:pass@localhost/db \
  --new entities/*.yaml

# Generate HTML diff report
specql diff \
  --old schema.sql \
  --new generated/schema.sql \
  --format html > diff-report.html
```

**Output**:
```diff
Schema Differences:

Tables:
  ✅ tb_contact: No changes
  ✅ tb_company: No changes
  ⚠️  tb_order: Column type changed
    - total: DECIMAL(10,2)
    + total: NUMERIC(19,4)  # SpecQL uses higher precision

Functions:
  ✅ crm.qualify_lead: Equivalent
  ⚠️  sales.process_payment: Logic differs
    - Manual transaction handling
    + Automatic transaction with better error handling

Indexes:
  + idx_tb_contact_email (NEW - performance improvement)
  + idx_tb_order_customer_status (NEW - compound index)

Summary:
  Compatible: 85%
  Manual review needed: 3 items
```

---

### `specql test`

Test migration equivalence and validate generated code.

```bash
specql test --validate-equivalence [options]
```

**Options**:
- `--original PATH` - Path to original code
- `--generated PATH` - Path to SpecQL-generated code
- `--database URL` - Test database connection
- `--fixtures PATH` - Test data fixtures
- `--coverage` - Generate test coverage report

**Examples**:

```bash
# Test SQL equivalence
specql test --validate-equivalence \
  --original database/functions/ \
  --generated generated/functions/ \
  --database postgresql://localhost/test_db

# Test with fixtures
specql test --validate-equivalence \
  --original ./django_app/ \
  --generated ./entities/ \
  --fixtures ./test_data/ \
  --coverage
```

**Output**:
```
Running equivalence tests...

SQL Function Tests:
  ✅ qualify_lead: Output matches (100%)
  ✅ process_payment: Output matches (100%)
  ⚠️  calculate_discount: Minor difference in rounding

Business Logic Tests:
  ✅ Order state transitions: Equivalent
  ✅ Validation rules: Equivalent
  ✅ Error handling: Equivalent

Coverage Report:
  Entities: 12/12 (100%)
  Actions: 32/34 (94%)
  Edge cases: 87/92 (95%)

Overall Equivalence: 96% ✅
```

---

## Migration Workflows by Source

### SQL/PostgreSQL Migration

```bash
# Step 1: Dump existing schema
pg_dump -s -h localhost -U user -d database > schema.sql

# Step 2: Analyze
specql analyze --source sql --path ./database/functions/ --report report.md

# Step 3: Reverse engineer
specql reverse --source sql \
  --path ./database/ \
  --output entities/ \
  --detect-patterns

# Step 4: Generate and compare
specql generate entities/*.yaml --output generated/
specql diff --old schema.sql --new generated/schema.sql

# Step 5: Test equivalence
specql test --validate-equivalence \
  --original database/ \
  --generated generated/ \
  --database postgresql://localhost/test_db
```

---

### Python (Django/SQLAlchemy) Migration

```bash
# Step 1: Analyze Django models
specql analyze --source python \
  --framework django \
  --path ./myapp/models/ \
  --report migration-plan.md

# Step 2: Reverse engineer
specql reverse --source python \
  --framework django \
  --path ./myapp/ \
  --output entities/ \
  --confidence-threshold 70

# Step 3: Review low-confidence entities
cat entities/*.yaml | grep -B5 "confidence: [0-6][0-9]%"

# Step 4: Generate and test
specql generate entities/*.yaml --output generated/ --with-tests
python manage.py sqlmigrate myapp 0001 > django_schema.sql
specql diff --old django_schema.sql --new generated/schema.sql
```

---

### TypeScript (Prisma/TypeORM) Migration

```bash
# Step 1: Analyze Prisma schema
specql analyze --source typescript \
  --framework prisma \
  --path ./prisma/schema.prisma

# Step 2: Reverse engineer
specql reverse --source typescript \
  --framework prisma \
  --path ./prisma/schema.prisma \
  --output entities/

# Step 3: Generate with frontend types
specql generate entities/*.yaml \
  --with-frontend \
  --with-tests \
  --output generated/

# Step 4: Compare migrations
npx prisma migrate diff \
  --from-migrations ./prisma/migrations \
  --to-schema-datamodel generated/schema.sql
```

---

### Rust (Diesel/SeaORM) Migration

```bash
# Step 1: Analyze Diesel schema
specql analyze --source rust \
  --framework diesel \
  --path ./src/schema.rs \
  --verbose

# Step 2: Reverse engineer
specql reverse --source rust \
  --framework diesel \
  --path ./src/ \
  --output entities/ \
  --include "**/*.rs"

# Step 3: Review and generate
specql generate entities/*.yaml --output generated/

# Step 4: Compare
diesel migration generate specql_comparison
specql diff --old migrations/ --new generated/
```

---

### Java (JPA/Hibernate) Migration

```bash
# Step 1: Analyze JPA entities
specql analyze --source java \
  --framework jpa \
  --path ./src/main/java/com/example/entity/ \
  --report report.md

# Step 2: Reverse engineer (with low confidence threshold)
specql reverse --source java \
  --framework jpa \
  --path ./src/main/java/com/example/entity/ \
  --output entities/ \
  --confidence-threshold 40  # Java reverse engineering is early-stage

# Step 3: MANUALLY REVIEW ALL FILES (Java extraction has limitations)
# Check each generated YAML file carefully

# Step 4: Generate and test
specql generate entities/*.yaml --output generated/
# Compare with Hibernate DDL output
```

---

## Pattern Detection

Auto-detect common database patterns during reverse engineering.

**Supported Patterns**:

| Pattern | Detection | Auto-Applied |
|---------|-----------|--------------|
| `audit_trail` | `created_at`, `updated_at`, `created_by`, `updated_by` | ✅ Auto-generated fields |
| `soft_delete` | `deleted_at`, `is_deleted` | ✅ Soft delete support |
| `multi_tenant` | `tenant_id`, `organization_id` | ✅ RLS policies |
| `state_machine` | Status enum with transition constraints | ⚠️ Documented, manual review |
| `versioning` | `version`, optimistic locking | ✅ Optimistic locking |
| `hierarchical` | `parent_id`, recursive relationships | ✅ Recursive queries |

**Example**:

```bash
# Enable pattern detection
specql reverse --source sql \
  --path ./database/ \
  --detect-patterns \
  --output entities/
```

**Output** (entities/contact.yaml):
```yaml
# Generated from: database/tables/contact.sql
# Patterns detected: audit_trail, soft_delete

entity: Contact
schema: crm

fields:
  email: email!
  first_name: text!
  last_name: text!

# Audit trail detected - these fields are auto-generated:
# - created_at: timestamp
# - updated_at: timestamp
# - created_by: ref(User)
# - updated_by: ref(User)

# Soft delete detected - this field is auto-generated:
# - deleted_at: timestamp
```

---

## Confidence Levels

Reverse engineering assigns confidence scores to indicate quality:

| Confidence | Meaning | Action |
|------------|---------|--------|
| **90-100%** | ✅ High confidence | Use as-is |
| **70-89%** | ✅ Good confidence | Quick review |
| **50-69%** | ⚠️ Medium confidence | Manual review required |
| **30-49%** | ⚠️ Low confidence | Significant manual work |
| **0-29%** | ❌ Very low | Manual rewrite recommended |

**By Language**:

| Language | Typical Confidence | Production Ready |
|----------|-------------------|------------------|
| **SQL (PL/pgSQL)** | 85%+ | ✅ Yes |
| **Python (Django)** | 70%+ | ✅ Yes (with review) |
| **Python (SQLAlchemy)** | 70%+ | ✅ Yes (with review) |
| **TypeScript (Prisma)** | 75%+ | ✅ Yes |
| **TypeScript (TypeORM)** | 70%+ | ✅ Yes (with review) |
| **Rust (Diesel)** | 60%+ | ⚠️ Manual review required |
| **Rust (SeaORM)** | 65%+ | ⚠️ Manual review required |
| **Java (JPA)** | 40%+ | ⚠️ Early stage, heavy review |

---

## Migration Best Practices

### 1. Start with Analysis

Always run `specql analyze` first to understand:
- Migration complexity
- Estimated effort
- Potential issues
- Recommended migration order

### 2. Use Confidence Thresholds

```bash
# Strict: Only migrate high-confidence entities
specql reverse --source python --path ./models/ --confidence-threshold 80

# Permissive: Migrate everything, flag low confidence
specql reverse --source python --path ./models/ --confidence-threshold 30
```

### 3. Incremental Migration

Migrate in phases:
```bash
# Phase 1: Simple entities
specql reverse --source python --include "**/user.py" "**/company.py"

# Phase 2: Medium complexity
specql reverse --source python --include "**/order.py" "**/product.py"

# Phase 3: Complex business logic
specql reverse --source python --include "**/payment.py" "**/workflow.py"
```

### 4. Always Test Equivalence

```bash
# Generate test database
createdb migration_test
psql migration_test < generated/schema.sql

# Run equivalence tests
specql test --validate-equivalence \
  --original ./original/ \
  --generated ./generated/ \
  --database postgresql://localhost/migration_test
```

### 5. Review Low-Confidence Files

```bash
# Find low-confidence entities
grep -r "confidence: [0-6][0-9]%" entities/

# Review manually
vim entities/payment.yaml  # Confidence: 45%
vim entities/order.yaml     # Confidence: 62%
```

---

## Troubleshooting

### Issue: Low Confidence Scores

**Cause**: Complex business logic, custom types, or framework-specific features

**Solution**:
1. Review generated YAML carefully
2. Add manual validation steps
3. Test thoroughly before deployment
4. Consider hybrid approach (keep complex logic in original framework)

### Issue: Missing Relationships

**Cause**: Implicit relationships not detected

**Solution**:
```yaml
# Add relationships manually
entity: Order
fields:
  customer: ref(Customer)!  # Add if not detected
```

### Issue: Incorrect Field Types

**Cause**: Type inference limitations

**Solution**:
```yaml
# Before (auto-detected)
fields:
  amount: decimal

# After (manual correction)
fields:
  amount: money!
```

### Issue: Complex Validation Logic

**Cause**: Custom validators not translatable

**Solution**:
```yaml
# Create custom validation function
actions:
  - name: create_order
    steps:
      - validate: call(custom_order_validation, $order_data)
      - insert: Order FROM $order_data
```

---

## Next Steps

- **Migration Guides**:
  - [SQL Migration](../02_migration/reverse-engineering/sql.md)
  - [Python Migration](../02_migration/reverse-engineering/python.md)
  - [TypeScript Migration](../02_migration/reverse-engineering/typescript.md)
  - [Rust Migration](../02_migration/reverse-engineering/rust.md)
  - [Java Migration](../02_migration/reverse-engineering/java.md)

- **Reference**:
  - [CLI Commands](cli-commands.md) - Full CLI reference
  - [YAML Syntax](yaml-syntax.md) - SpecQL YAML syntax

- **Guides**:
  - [Actions Guide](../05_guides/actions.md) - Business logic patterns
  - [Multi-Tenancy](../05_guides/multi-tenancy.md) - SaaS patterns

---

**Successful migrations require analysis, testing, and validation—use these CLI tools to ensure a smooth transition.**
