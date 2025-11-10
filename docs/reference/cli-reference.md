# SpecQL CLI Reference

This guide covers the essential SpecQL command-line interface commands for generating schemas, validating specifications, and running tests.

## 🎯 Quick Start Commands

### Installation
```bash
# Install SpecQL
pip install specql

# Verify installation
specql --version
```

### Basic Workflow
```bash
# 1. Validate your YAML
specql validate entities/user.yaml

# 2. Generate database schema
specql generate schema entities/user.yaml

# 3. Generate tests
specql generate tests entities/user.yaml

# 4. Run tests
specql test run --type pgtap entities/user.yaml
specql test run --type pytest entities/user.yaml
```

## 📋 Command Reference

### `specql generate`

Generate database schemas, functions, and tests from YAML specifications.

#### Generate Schema
```bash
specql generate schema [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Generate schema for one entity
specql generate schema entities/user.yaml

# Generate schema for multiple entities
specql generate schema entities/user.yaml entities/company.yaml

# Generate schema for all entities in directory
specql generate schema entities/*.yaml
```

#### Generate Tests
```bash
specql generate tests [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Generate all test types
specql generate tests entities/user.yaml

# Generate only pgTAP tests
specql generate tests --type pgtap entities/user.yaml

# Generate only pytest tests
specql generate tests --type pytest entities/user.yaml
```

**Options:**
- `--type [pgtap|pytest|performance]` - Test type to generate (default: all)

### `specql validate`

Validate YAML entity specifications for syntax errors and consistency.

```bash
specql validate [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Validate single file
specql validate entities/user.yaml

# Validate multiple files
specql validate entities/user.yaml entities/company.yaml

# Validate all entities
specql validate entities/*.yaml

# Verbose output
specql validate entities/*.yaml --verbose
```

**Exit Codes:**
- `0` - All files valid
- `1` - Validation errors found

### `specql test run`

Execute generated tests against your database.

```bash
specql test run --type TYPE [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Run pgTAP tests
specql test run --type pgtap entities/user.yaml

# Run pytest tests
specql test run --type pytest entities/user.yaml

# Run all test types
specql test run entities/user.yaml

# Run tests for multiple entities
specql test run entities/*.yaml
```

**Test Types:**
- `pgtap` - PostgreSQL native tests (fast, database-only)
- `pytest` - Python integration tests (comprehensive, slower)
- `performance` - Benchmarking tests (measure performance)

### `specql test coverage`

Generate test coverage reports.

```bash
specql test coverage [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Generate coverage report
specql test coverage entities/user.yaml

# Export to HTML
specql test coverage entities/user.yaml --format html --output coverage.html
```

## ⚙️ Global Options

### Environment
- `--env TEXT` - Environment to use (default: local)
- `--config PATH` - Path to config file (default: confiture.yaml)

### Output
- `--verbose, -v` - Verbose output
- `--quiet, -q` - Suppress output
- `--output PATH` - Output directory

### Database
- `--database-url URL` - Database connection URL
- Uses `DATABASE_URL` environment variable if not specified

## 🔧 Common Workflows

### Development Cycle
```bash
# Edit your YAML
vim entities/user.yaml

# Validate changes
specql validate entities/user.yaml

# Generate updated schema
specql generate schema entities/user.yaml

# Apply to database
psql $DATABASE_URL -f db/schema/10_tables/user.sql

# Generate and run tests
specql generate tests entities/user.yaml
specql test run entities/user.yaml
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install SpecQL
        run: pip install specql

      - name: Validate Entities
        run: specql validate entities/*.yaml

      - name: Generate Schema
        run: specql generate schema entities/*.yaml

      - name: Apply Schema
        run: |
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/00_foundation/*.sql
          psql postgresql://postgres:postgres@localhost:5432/postgres -f db/schema/10_tables/*.sql

      - name: Generate Tests
        run: specql generate tests entities/*.yaml

      - name: Run pgTAP Tests
        run: specql test run --type pgtap entities/*.yaml

      - name: Run pytest Tests
        run: specql test run --type pytest entities/*.yaml
```

### Multi-Environment Setup
```bash
# Local development
export DATABASE_URL="postgresql://localhost/specql_dev"
specql generate schema entities/*.yaml --env local

# Staging deployment
export DATABASE_URL="postgresql://staging-db/specql_staging"
specql generate schema entities/*.yaml --env staging

# Production deployment
export DATABASE_URL="postgresql://prod-db/specql_prod"
specql generate schema entities/*.yaml --env production
```

## 🆘 Troubleshooting

### "Command not found: specql"
```bash
# Check if installed
pip list | grep specql

# Reinstall
pip install --upgrade specql

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "Database connection failed"
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
```

### "Validation errors"
```bash
# Get detailed error information
specql validate entities/user.yaml --verbose

# Common issues:
# - Invalid YAML syntax
# - Unknown field types
# - Missing required fields
# - Invalid pattern configuration
```

### "Tests failing"
```bash
# Check test output
specql test run entities/user.yaml --verbose

# Common issues:
# - Schema not applied to database
# - Test data conflicts
# - Environment differences
# - Database permissions
```

### "Permission denied"
```bash
# Grant database permissions
psql $DATABASE_URL -c "GRANT ALL ON SCHEMA public TO specql_user;"

# Check file permissions
ls -la entities/
```

## 📚 Related Documentation

- **[Getting Started](../getting-started/)** - Step-by-step tutorials
- **[YAML Schema](yaml-schema.md)** - Entity specification format
- **[Troubleshooting](../troubleshooting/)** - Common issues and solutions
- **[Best Practices](../best-practices/)** - Recommended patterns

## 🎯 Next Steps

- **[Explore Patterns](../guides/mutation-patterns/)** - Learn about business logic patterns
- **[Test Generation](../guides/test-generation/)** - Advanced testing features
- **[CI/CD Integration](../guides/test-generation/ci-cd-integration.md)** - Production deployment

**Ready to build more complex applications? Check out the guides! 🚀**

---

## `specql generate`

Generate PostgreSQL schema and functions from SpecQL YAML files.

### Syntax
```bash
specql generate [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - One or more YAML entity files or glob patterns

### Options

#### `--foundation-only`
Generate only the app foundation SQL (types, schemas).

**Use case**: Initialize database before adding entities.

**Example**:
```bash
specql generate entities/contact.yaml --foundation-only
```

**Output**: `db/schema/00_foundation/000_app_foundation.sql`

#### `--include-tv`
Generate table views (CQRS read-side).

**Use case**: Enable read-optimized views for queries.

**Example**:
```bash
specql generate entities/**/*.yaml --include-tv
```

**Output**:
- `db/schema/10_tables/` - Tables
- `db/schema/10_tables/views/` - Table views

#### `--env TEXT`
Specify Confiture environment (default: `local`).

**Use case**: Generate for different environments (local, staging, prod).

**Example**:
```bash
specql generate entities/**/*.yaml --env staging
```

**Config**: Uses `confiture.yaml` environment settings.

#### `--with-impacts`
Generate FraiseQL impact metadata (JSON).

**Use case**: Frontend integration, GraphQL client codegen.

**Example**:
```bash
specql generate entities/**/*.yaml --with-impacts
```

**Output**: `db/metadata/mutation_impacts.json`

#### `--output-frontend PATH`
Generate frontend code (TypeScript types, Apollo hooks).

**Use case**: Full-stack codegen from YAML.

**Example**:
```bash
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated
```

**Output**:
- `src/generated/types.ts` - TypeScript types
- `src/generated/mutations.ts` - Apollo hooks
- `src/generated/docs/` - Markdown documentation

#### `--output-format [flat|hierarchical]`
Control output directory structure.

**Use case**: Organize generated files by domain/subdomain.

**Options**:
- `flat` (default): All files in single directory
- `hierarchical`: Organize by `organization.domain` / `organization.subdomain`

**Example**:
```bash
specql generate entities/**/*.yaml --output-format hierarchical
```

**Output (flat)**:
```
db/schema/10_tables/
├── contact.sql
├── company.sql
└── order.sql
```

**Output (hierarchical)**:
```
db/schema/10_tables/
├── CRM/
│   ├── Customer/
│   │   └── 012311_contact.sql
│   └── Account/
│       └── 012312_company.sql
└── Commerce/
    └── Orders/
        └── 042001_order.sql
```

### Examples

#### Single Entity
```bash
specql generate entities/contact.yaml
```

#### Multiple Entities
```bash
specql generate entities/contact.yaml entities/company.yaml
```

#### All Entities in Directory
```bash
specql generate entities/**/*.yaml
```

#### Specific Schema
```bash
specql generate entities/crm/*.yaml
```

#### Foundation Only
```bash
specql generate entities/contact.yaml --foundation-only
```

#### With Frontend Codegen
```bash
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated
```

### Output Structure

```
db/schema/
├── 00_foundation/
│   └── 000_app_foundation.sql  # Types, schemas
├── 10_tables/
│   ├── contact.sql             # Table DDL
│   └── company.sql
├── 20_helpers/
│   ├── contact_helpers.sql     # Helper functions
│   └── company_helpers.sql
├── 30_functions/
│   ├── qualify_lead.sql        # Business actions
│   └── create_company.sql
└── 40_metadata/
    ├── contact_metadata.sql    # FraiseQL annotations
    └── company_metadata.sql
```

---

## `specql validate`

Validate SpecQL YAML entity files for syntax errors and consistency.

### Syntax
```bash
specql validate [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - One or more YAML files or glob patterns

### Options

#### `-v, --verbose`
Show detailed validation output.

**Example**:
```bash
specql validate entities/**/*.yaml --verbose
```

#### `--check-impacts`
Validate impact declarations are complete and consistent.

**Use case**: Ensure mutations declare all side effects.

**Example**:
```bash
specql validate entities/**/*.yaml --check-impacts
```

**Checks**:
- All entities in `write:` exist
- All entities in `read:` exist
- No circular dependencies
- No missing declarations

### Examples

#### Single File
```bash
specql validate entities/contact.yaml
```

#### All Entities
```bash
specql validate entities/**/*.yaml
```

#### With Impact Checking
```bash
specql validate entities/**/*.yaml --check-impacts
```

### Exit Codes
- `0` - All files valid
- `1` - Validation errors found

### Example Output

**Success**:
```
✅ entities/contact.yaml: Valid
✅ entities/company.yaml: Valid
✅ All 2 entities validated successfully
```

**Errors**:
```
❌ entities/contact.yaml: Parse error
  Line 5: Unknown field type 'string' (use 'text')

❌ entities/order.yaml: Validation error
  Action 'ship_order': References undefined entity 'Shipment'

❌ 2 files have errors
```

---

## `specql check-codes`

Verify uniqueness of table codes across all entities.

### Syntax
```bash
specql check-codes [OPTIONS] ENTITY_FILES...
```

### Arguments
- `ENTITY_FILES...` - YAML files or directories

### Options

#### `--format [text|json|csv]`
Output format (default: `text`).

**Example**:
```bash
specql check-codes entities/ --format json
```

#### `--export PATH`
Export results to file.

**Example**:
```bash
specql check-codes entities/ --format csv --export codes.csv
```

### Examples

#### Check All Entities
```bash
specql check-codes entities/**/*.yaml
```

#### Export to JSON
```bash
specql check-codes entities/ --format json --export table_codes.json
```

#### Export to CSV
```bash
specql check-codes entities/ --format csv --export codes.csv
```

### Output

**Text Format**:
```
📊 Table Code Report

✅ All codes are unique

Entities with table codes:
  • 012311 - Contact (entities/crm/contact.yaml)
  • 012312 - Company (entities/crm/company.yaml)
  • 042001 - Order (entities/commerce/order.yaml)

📈 Summary:
  Total entities: 15
  With table codes: 3
  Without table codes: 12
```

**JSON Format**:
```json
{
  "valid": true,
  "codes": [
    {
      "code": "012311",
      "entity": "Contact",
      "file": "entities/crm/contact.yaml"
    }
  ],
  "duplicates": [],
  "summary": {
    "total": 15,
    "with_codes": 3,
    "without_codes": 12
  }
}
```

**Error (Duplicates)**:
```
❌ Duplicate table codes found

⚠️  Code 012311 assigned to multiple entities:
  • Contact (entities/crm/contact.yaml)
  • Customer (entities/crm/customer.yaml)

❌ 1 duplicate code(s) found
```

---

## `specql diff`

Compare generated SQL with existing schema files.

### Syntax
```bash
specql diff [OPTIONS] ENTITY_FILES...
```

### Options

#### `--compare PATH`
Path to existing SQL file(s) to compare against.

**Example**:
```bash
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql
```

#### `--ignore-whitespace`
Ignore whitespace differences.

#### `--ignore-comments`
Ignore SQL comment differences.

### Examples

#### Compare Single Entity
```bash
specql diff entities/contact.yaml \
  --compare db/schema/10_tables/contact.sql
```

#### Compare All Entities
```bash
specql diff entities/**/*.yaml \
  --compare db/schema/10_tables/
```

### Output
```diff
Comparing: entities/contact.yaml → db/schema/10_tables/contact.sql

--- Generated
+++ Existing
@@ -12,6 +12,7 @@
   company INTEGER NOT NULL REFERENCES crm.tb_company(id),
   status TEXT NOT NULL CHECK (status IN ('lead', 'qualified', 'customer')),
+  priority TEXT,  -- Added in existing, not in YAML

✅ 1 file compared
⚠️  1 difference found
```

---

## `specql docs`

Generate documentation from entity files.

### Syntax
```bash
specql docs [OPTIONS] ENTITY_FILES...
```

### Options

#### `--output-dir PATH`
Output directory for docs (default: `docs/generated`).

**Example**:
```bash
specql docs entities/**/*.yaml --output-dir docs/entities
```

#### `--format [markdown|html]`
Documentation format (default: `markdown`).

### Examples

#### Generate Entity Docs
```bash
specql docs entities/**/*.yaml
```

#### Output to Custom Directory
```bash
specql docs entities/ --output-dir docs/entities
```

### Output
```
docs/generated/
├── entities/
│   ├── contact.md
│   ├── company.md
│   └── order.md
└── index.md
```

---

## Configuration

### `confiture.yaml`

SpecQL uses Confiture for configuration.

**Location**: Project root (`confiture.yaml`)

**Example**:
```yaml
schema_dirs:
  - path: db/schema/00_foundation
    order: 0
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/20_helpers
    order: 20
  - path: db/schema/30_functions
    order: 30
  - path: db/schema/40_metadata
    order: 40

environments:
  local:
    database_url: postgresql://localhost:5432/myapp_dev
    migrations_dir: db/migrations

  staging:
    database_url: ${DATABASE_URL}
    migrations_dir: db/migrations

  production:
    database_url: ${DATABASE_URL}
    migrations_dir: db/migrations
```

### Environment Variables

#### `DATABASE_URL`
PostgreSQL connection string.

**Format**: `postgresql://user:password@host:port/database`

**Example**:
```bash
export DATABASE_URL="postgresql://localhost:5432/myapp"
```

#### `SPECQL_ENV`
Override environment (overrides `--env` flag).

**Example**:
```bash
export SPECQL_ENV=staging
specql generate entities/**/*.yaml
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (validation, parse, etc.) |
| `2` | File not found |
| `3` | Configuration error |

---

## Common Workflows

### Initial Setup
```bash
# 1. Install
uv add specql-generator

# 2. Verify
specql --version

# 3. Create first entity
mkdir -p entities
cat > entities/contact.yaml << 'EOF'
entity: Contact
schema: crm
fields:
  email: text
  name: text
EOF

# 4. Generate foundation
specql generate entities/contact.yaml --foundation-only

# 5. Generate tables
specql generate entities/contact.yaml
```

### Development Loop
```bash
# 1. Edit YAML
vim entities/contact.yaml

# 2. Validate
specql validate entities/contact.yaml

# 3. Generate
specql generate entities/contact.yaml

# 4. Apply to DB
psql myapp -f db/schema/10_tables/contact.sql

# 5. Test
psql myapp -c "SELECT * FROM crm.tb_contact;"
```

### Full Codegen (Backend + Frontend)
```bash
# Generate everything
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated

# Output:
# - db/schema/ (PostgreSQL)
# - db/metadata/ (GraphQL metadata)
# - src/generated/types.ts (TypeScript)
# - src/generated/mutations.ts (Apollo hooks)
```

### CI/CD Pipeline
```bash
#!/bin/bash
# .github/workflows/generate-schema.yml

# 1. Validate all entities
specql validate entities/**/*.yaml || exit 1

# 2. Check table codes
specql check-codes entities/**/*.yaml || exit 1

# 3. Generate schema
specql generate entities/**/*.yaml --env production

# 4. Run migrations
confiture migrate up --env production
```

---

## Troubleshooting

See: `docs/guides/troubleshooting.md`

### Common Issues

#### "Command not found: specql"
**Solution**:
```bash
# Ensure UV environment is activated
uv sync
uv run specql --version
```

#### "No such file or directory"
**Solution**: Use absolute paths or run from project root
```bash
cd /path/to/project
specql generate entities/contact.yaml
```

#### "Confiture build failed"
**Solution**: Install Confiture
```bash
uv add fraiseql-confiture
```

---

## Reference

### Related Documentation
- **YAML Reference**: `docs/reference/yaml-reference.md`
- **Migration Guide**: `docs/guides/migration-guide.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`
- **Examples**: `examples/entities/`

### External Tools
- **UV**: https://github.com/astral-sh/uv
- **Confiture**: https://github.com/fraiseql/confiture
- **PostgreSQL**: https://www.postgresql.org/docs/