# CLI Commands Reference

> **Complete reference for the `specql` command-line interface**

## Installation

```bash
pip install specql
```

## Core Commands

### `specql generate`

Generate PostgreSQL, GraphQL, and TypeScript code from SpecQL YAML.

```bash
specql generate <files...> [options]
```

**Arguments**:
- `<files...>` - One or more SpecQL YAML files or glob patterns

**Options**:
- `--output DIR` - Output directory for generated files (default: `./generated`)
- `--schema-registry FILE` - Path to schema registry YAML (default: `registry/domain_registry.yaml`)
- `--with-frontend` - Generate frontend TypeScript types and hooks
- `--with-tests` - Generate test fixtures and validation tests
- `--with-impacts` - Generate mutation impact metadata
- `--format FORMAT` - Output format: `sql`, `graphql`, `typescript`, or `all` (default: `all`)

**Examples**:

```bash
# Generate from single file
specql generate entities/contact.yaml

# Generate from multiple files
specql generate entities/contact.yaml entities/organization.yaml

# Generate from glob pattern
specql generate entities/*.yaml

# Generate with all features
specql generate entities/*.yaml --with-frontend --with-tests --with-impacts

# Generate only SQL
specql generate entities/*.yaml --format sql --output database/schema/
```

**Output Structure**:
```
generated/
├── schema/
│   ├── 00_framework/
│   ├── 10_tables/
│   ├── 20_functions/
│   └── 30_views/
├── graphql/
│   └── schema.graphql
└── typescript/
    ├── types/
    └── hooks/
```

---

### `specql validate`

Validate SpecQL YAML syntax and business logic.

```bash
specql validate <files...> [options]
```

**Options**:
- `--strict` - Enable strict validation (warns become errors)
- `--schema-registry FILE` - Schema registry for cross-entity validation

**Examples**:

```bash
# Validate single file
specql validate entities/contact.yaml

# Validate all entities
specql validate entities/*.yaml

# Strict validation
specql validate entities/*.yaml --strict
```

**Validation Checks**:
- ✅ YAML syntax correctness
- ✅ Entity field types
- ✅ Action step syntax
- ✅ Cross-entity references
- ✅ Rich type validations
- ✅ Naming conventions
- ✅ Business logic consistency

---

### `specql reverse`

Reverse engineer existing code to SpecQL YAML.

```bash
specql reverse --source <type> --path <path> [options]
```

**Options**:
- `--source TYPE` - Source type: `sql`, `python`, `typescript`, `rust`, `java`
- `--path PATH` - Path to source code directory
- `--output DIR` - Output directory for SpecQL files (default: `./entities`)
- `--include PATTERN` - Include only files matching pattern
- `--exclude PATTERN` - Exclude files matching pattern
- `--detect-patterns` - Auto-detect business patterns (audit, soft-delete, etc.)

**Examples**:

```bash
# Reverse from SQL
specql reverse --source sql --path ./database/functions/ --output entities/

# Reverse from Python (Django)
specql reverse --source python --path ./myapp/models/ --output entities/

# Reverse from TypeScript (Prisma)
specql reverse --source typescript --path ./prisma/schema.prisma --output entities/

# Reverse from Rust (Diesel)
specql reverse --source rust --path ./src/models/ --output entities/

# With pattern detection
specql reverse --source sql --path ./database/ --detect-patterns
```

**Supported Frameworks**:

**Python**:
- Django models
- SQLAlchemy models
- Flask-SQLAlchemy
- Pydantic models

**TypeScript**:
- Prisma schemas
- TypeORM entities
- Sequelize models
- Express routes

**Rust**:
- Diesel schemas
- SeaORM entities
- SQLx queries
- Actix-web/Axum handlers

**Java**:
- JPA/Hibernate entities
- Spring Data repositories
- MyBatis mappers

---

### `specql diff`

Show differences between SpecQL and existing schema.

```bash
specql diff [options]
```

**Options**:
- `--old FILE` - Existing schema file
- `--new FILE` - New generated schema file
- `--format FORMAT` - Output format: `text`, `json`, `html` (default: `text`)
- `--ignore-comments` - Ignore comment differences
- `--ignore-whitespace` - Ignore whitespace changes

**Examples**:

```bash
# Compare schemas
specql diff --old database/schema.sql --new generated/schema.sql

# JSON output for CI/CD
specql diff --old schema.sql --new generated/schema.sql --format json

# Ignore cosmetic differences
specql diff --old schema.sql --new generated/schema.sql --ignore-comments --ignore-whitespace
```

---

### `specql analyze`

Analyze codebase and generate migration report.

```bash
specql analyze --source <type> --path <path> [options]
```

**Options**:
- `--source TYPE` - Source type: `sql`, `python`, `typescript`, `rust`, `java`
- `--path PATH` - Path to analyze
- `--report FILE` - Output report file (default: `migration-report.md`)
- `--metrics` - Include detailed metrics

**Examples**:

```bash
# Analyze Python codebase
specql analyze --source python --path ./myapp/ --report migration-plan.md

# Analyze with metrics
specql analyze --source sql --path ./database/ --metrics
```

**Report Contents**:
- Entity count and complexity
- Action complexity scores
- Detected patterns
- Recommended migration order
- Estimated effort (hours)
- Risk assessment

---

### `specql test`

Test generated code against fixtures.

```bash
specql test [options]
```

**Options**:
- `--entities DIR` - SpecQL entity directory
- `--fixtures DIR` - Test fixture directory
- `--validate-actions` - Test action logic
- `--validate-equivalence` - Compare with original system

**Examples**:

```bash
# Test generated code
specql test --entities entities/ --fixtures test-data/

# Validate action logic
specql test --entities entities/ --validate-actions

# Compare with legacy system
specql test --entities entities/ --validate-equivalence
```

---

### `specql docs`

Generate documentation from SpecQL entities.

```bash
specql docs <files...> [options]
```

**Options**:
- `--output DIR` - Output directory (default: `./docs/generated`)
- `--format FORMAT` - Format: `markdown`, `html`, `pdf` (default: `markdown`)
- `--include-examples` - Include usage examples
- `--include-schema` - Include generated schema

**Examples**:

```bash
# Generate markdown docs
specql docs entities/*.yaml --output docs/api/

# Generate with examples
specql docs entities/*.yaml --include-examples --include-schema

# Generate HTML docs
specql docs entities/*.yaml --format html --output docs/html/
```

---

## Global Options

Available for all commands:

```bash
--verbose, -v       Verbose output
--quiet, -q         Suppress non-error output
--version          Show version number
--help, -h         Show help message
--config FILE      Load configuration from file
--log-level LEVEL  Set log level: debug, info, warn, error
```

---

## Configuration File

Create `.specqlrc.yaml` or `specql.config.yaml`:

```yaml
# Schema registry
schema_registry: registry/domain_registry.yaml

# Output directories
output:
  sql: generated/schema/
  graphql: generated/graphql/
  typescript: generated/frontend/

# Generation options
generate:
  with_frontend: true
  with_tests: true
  with_impacts: true

# Validation options
validate:
  strict: true
  check_references: true

# Reverse engineering
reverse:
  detect_patterns: true
  output: entities/
```

**Use config**:
```bash
specql generate entities/*.yaml --config specql.config.yaml
```

---

## Environment Variables

```bash
# Schema registry location
export SPECQL_SCHEMA_REGISTRY=registry/domain_registry.yaml

# Default output directory
export SPECQL_OUTPUT_DIR=generated/

# Log level
export SPECQL_LOG_LEVEL=debug

# Enable metrics
export SPECQL_METRICS=true
```

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Validation error
- `3` - File not found
- `4` - Parsing error
- `5` - Generation error

---

## Examples by Use Case

### Initial Setup

```bash
# Install SpecQL
pip install specql

# Validate installation
specql --version

# Generate from first entity
specql generate entities/contact.yaml --output generated/
```

### Development Workflow

```bash
# Validate changes
specql validate entities/*.yaml --strict

# Generate code
specql generate entities/*.yaml --with-frontend --with-tests

# Run tests
specql test --entities entities/ --validate-actions

# Generate docs
specql docs entities/*.yaml --include-examples
```

### Migration Workflow

```bash
# Analyze existing codebase
specql analyze --source python --path ./myapp/ --report plan.md

# Reverse engineer
specql reverse --source python --path ./myapp/models/ --detect-patterns

# Review generated YAML (manual step)
# Edit entities/*.yaml as needed

# Validate migration
specql diff --old database/schema.sql --new generated/schema.sql

# Test equivalence
specql test --entities entities/ --validate-equivalence
```

### CI/CD Integration

```bash
#!/bin/bash
# .github/workflows/specql.yml

# Validate entities
specql validate entities/*.yaml --strict || exit 1

# Generate code
specql generate entities/*.yaml --with-frontend --with-tests

# Run tests
specql test --entities entities/ --validate-actions || exit 1

# Compare with baseline
specql diff --old baseline/schema.sql --new generated/schema.sql --format json > diff.json

# Deploy if no breaking changes
if [ -s diff.json ]; then
  echo "Schema changes detected - review required"
  exit 1
fi
```

---

## Debugging

### Verbose Mode

```bash
# Show detailed generation steps
specql generate entities/*.yaml --verbose

# Show debug logs
specql generate entities/*.yaml --log-level debug
```

### Validation Errors

```bash
# Strict validation with full error messages
specql validate entities/*.yaml --strict --verbose
```

### Generation Errors

```bash
# Test single entity in isolation
specql generate entities/problematic.yaml --verbose

# Check schema registry
specql validate --schema-registry registry/domain_registry.yaml
```

---

## Performance

### Large Projects

```bash
# Generate in parallel (automatic)
specql generate entities/*.yaml

# Limit memory usage
SPECQL_MAX_MEMORY=512M specql generate entities/*.yaml

# Use incremental generation
specql generate entities/*.yaml --incremental --cache .specql-cache/
```

### Benchmarking

```bash
# Measure generation time
time specql generate entities/*.yaml

# Profile with metrics
specql generate entities/*.yaml --metrics > metrics.json
```

---

## Troubleshooting

### Common Issues

**Issue**: `Entity not found in schema registry`
```bash
# Solution: Add entity to registry
# Edit registry/domain_registry.yaml
# Add schema mapping
```

**Issue**: `Validation failed: unknown field type`
```bash
# Solution: Check rich type spelling
# See: docs/reference/rich-types.md
```

**Issue**: `Circular reference detected`
```bash
# Solution: Review entity relationships
specql validate entities/*.yaml --verbose
# Fix circular refs in YAML
```

---

## Next Steps

- [YAML Syntax Reference](yaml-syntax.md) - Complete syntax guide
- [Rich Types Reference](../03_core-concepts/rich-types.md) - All 49 types
- [Action Steps Reference](action-steps-reference.md) - All action step types
- [Migration Guide](../02_migration/index.md) - Migration workflows

---

**The `specql` CLI is your gateway to declarative backend development. Master these commands to unlock 100x productivity.**
