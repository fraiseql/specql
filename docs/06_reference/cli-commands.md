# CLI Commands Reference

> **Complete reference for the `specql` command-line interface**

## Installation

```bash
pip install specql
# or
uv pip install specql
```

## Command Overview

| Command | Status | Description |
|---------|--------|-------------|
| `generate` | Stable | Generate SQL from SpecQL YAML |
| `validate` | Stable | Validate SpecQL YAML syntax |
| `reverse` | Stable | Reverse engineer to YAML |
| `patterns` | Stable | Pattern detection and application |
| `init` | Stable | Scaffolding for new projects |
| `workflow` | Stable | Multi-step automation |
| `test` | Stable | Testing tools: seed data, test generation, reverse engineering |
| `diff` | Planned | Schema diffing |
| `docs` | Planned | Documentation generation |
| `analyze` | Planned | Migration analysis |

---

## Core Commands

### `specql generate`

Generate PostgreSQL schema and functions from SpecQL YAML.

```bash
specql generate <files...> [options]
```

**Arguments**:
- `<files...>` - One or more SpecQL YAML files or glob patterns

**Options**:
- `-o, --output-dir DIR` - Output directory (default: `./migrations`)
- `--foundation-only` - Generate only app foundation types
- `--actions-only` - Generate only action functions
- `--include-tv` - Include table views
- `--frontend PATH` - Generate frontend code to directory
- `--tests` - Generate test fixtures
- `--with-impacts` - Generate mutation impacts JSON
- `--use-registry` - Use hexadecimal registry for table codes
- `--output-format FORMAT` - Output format: `hierarchical` or `confiture` (default: `hierarchical`)
- `--dry-run` - Preview without writing files
- `--performance` - Enable performance monitoring
- `--performance-output PATH` - Write performance metrics to file

**Examples**:

```bash
# Generate from single file
specql generate entities/contact.yaml

# Generate from multiple files
specql generate entities/contact.yaml entities/organization.yaml

# Generate from glob pattern
specql generate entities/*.yaml

# Generate with frontend code
specql generate entities/*.yaml --frontend src/generated/

# Generate with mutation impacts
specql generate entities/*.yaml --with-impacts

# Preview mode (no files written)
specql generate entities/*.yaml --dry-run

# Use Confiture directory structure
specql generate entities/*.yaml --output-format confiture
```

**Output Structure** (hierarchical):
```
db/schema/
├── 00_foundation/
│   └── 000_app_foundation.sql
├── 10_tables/
│   └── {entity}.sql
├── 20_helpers/
│   └── {entity}_helpers.sql
└── 30_functions/
    └── {action}.sql
```

---

### `specql validate`

Validate SpecQL YAML syntax and business logic.

```bash
specql validate <files...> [options]
```

**Options**:
- `--strict` - Treat warnings as errors
- `--schema-registry FILE` - Schema registry for cross-entity validation
- `-v, --verbose` - Show detailed output with entity names

**Examples**:

```bash
# Validate single file
specql validate entities/contact.yaml

# Validate all entities
specql validate entities/*.yaml

# Strict validation (warnings become errors)
specql validate entities/*.yaml --strict

# Verbose output
specql validate entities/*.yaml --verbose
```

**Validation Checks**:
- YAML syntax correctness
- Entity field types
- Action step syntax
- Rich type validations
- Naming conventions (warns on camelCase)
- Schema presence (warns on default 'public')

---

### `specql reverse <language>`

Reverse engineer existing code to SpecQL YAML.

```bash
specql reverse <language> <files...> [options]
```

**Subcommands**:
- `sql` - Reverse engineer SQL DDL and functions
- `python` - Reverse engineer Python models (Django, SQLAlchemy)
- `typescript` - Reverse engineer TypeScript (Prisma, TypeORM)
- `rust` - Reverse engineer Rust (Diesel, SeaORM)
- `project` - Auto-detect project type and process

#### `specql reverse sql`

```bash
specql reverse sql <files...> -o <output-dir> [options]
```

**Options**:
- `-o, --output-dir DIR` - Output directory (required)
- `--min-confidence FLOAT` - Minimum confidence threshold (default: 0.80)
- `--no-ai` - Skip AI enhancement
- `--merge-translations/--no-merge-translations` - Merge translation tables
- `--preview` - Preview without writing
- `--with-patterns` - Auto-detect and apply patterns

**Examples**:

```bash
# Reverse engineer SQL tables
specql reverse sql db/tables/*.sql -o entities/

# Reverse engineer without AI
specql reverse sql functions.sql -o entities/ --no-ai

# Preview mode
specql reverse sql db/*.sql -o entities/ --preview

# With pattern detection
specql reverse sql db/ -o entities/ --with-patterns
```

#### `specql reverse python`

```bash
specql reverse python <files...> -o <output-dir> [options]
```

**Options**:
- `-o, --output-dir DIR` - Output directory (required)
- `--framework FRAMEWORK` - Framework: `django`, `sqlalchemy`, `fastapi`
- `--preview` - Preview without writing

**Examples**:

```bash
# Reverse engineer Django models
specql reverse python myapp/models.py -o entities/

# Specify framework
specql reverse python src/models/ -o entities/ --framework sqlalchemy
```

#### `specql reverse project`

Auto-detect project type and process entire directory.

```bash
specql reverse project <directory> -o <output-dir> [options]
```

**Examples**:

```bash
# Auto-detect and reverse engineer
specql reverse project ./my-django-app -o entities/

# With specific framework override
specql reverse project . -o entities/ --framework diesel
```

**Supported Frameworks**:

| Language | Frameworks |
|----------|------------|
| Python | Django, SQLAlchemy, FastAPI |
| TypeScript | Prisma, TypeORM, Sequelize |
| Rust | Diesel, SeaORM, SQLx |

---

### `specql patterns`

Pattern detection and application.

#### `specql patterns detect`

```bash
specql patterns detect <files...> [options]
```

**Options**:
- `--min-confidence FLOAT` - Minimum confidence (0.0-1.0, default: 0.75)
- `--patterns TEXT` - Specific patterns to detect (multiple)
- `--format FORMAT` - Output format: `text`, `json`, `yaml`
- `-o, --output PATH` - Write output to file

**Examples**:

```bash
# Detect patterns in SQL files
specql patterns detect db/*.sql

# JSON output
specql patterns detect src/ --format json

# Specific patterns only
specql patterns detect . --patterns audit-trail --patterns soft-delete
```

**Detectable Patterns**:
- `audit-trail` - created_at/updated_at/by fields
- `soft-delete` - deleted_at field
- `multi-tenant` - tenant_id column
- `state-machine` - status enum fields
- `hierarchical` - parent_id self-reference
- `versioning` - version number tracking

#### `specql patterns apply`

```bash
specql patterns apply <pattern> <file> [options]
```

**Examples**:

```bash
# Apply audit trail pattern
specql patterns apply audit-trail entities/contact.yaml
```

---

### `specql init`

Scaffolding for new projects and entities.

#### `specql init project`

```bash
specql init project [name] [options]
```

Create a new SpecQL project structure.

#### `specql init entity`

```bash
specql init entity <name> [options]
```

**Options**:
- `--schema SCHEMA` - Database schema (default: `public`)
- `--field FIELD:TYPE` - Add field (multiple)
- `-o, --output-dir DIR` - Output directory (default: `entities/`)

**Examples**:

```bash
# Create entity template
specql init entity Contact --schema crm

# With fields
specql init entity Order --field total:decimal --field status:enum
```

#### `specql init registry`

```bash
specql init registry [options]
```

Create a schema registry template.

---

### `specql workflow`

Multi-step automation commands.

#### `specql workflow migrate`

Full migration pipeline: reverse -> validate -> generate.

```bash
specql workflow migrate <project-dir> -o <output-dir> [options]
```

**Options**:
- `-o, --output-dir DIR` - Output directory (required)
- `--skip-validate` - Skip validation step
- `--skip-generate` - Skip generation step
- `--dry-run` - Preview without writing files

**Examples**:

```bash
# Full migration workflow
specql workflow migrate ./my-django-app -o migration/

# Skip generation (reverse + validate only)
specql workflow migrate . -o output/ --skip-generate
```

#### `specql workflow sync`

Incremental synchronization for existing SpecQL projects.

```bash
specql workflow sync [options]
```

---

### `specql test`

Testing tools: seed data, test generation, and reverse engineering.

#### `specql test seed`

Generate seed data SQL for testing.

```bash
specql test seed <entities...> [options]
```

**Arguments**:
- `<entities...>` - One or more SpecQL YAML entity files

**Options**:
- `-o, --output DIR` - Output directory (default: `seeds/`)
- `-n, --count N` - Records per entity (default: 10)
- `-s, --scenario N` - Test scenario number (affects UUIDs, default: 0)
- `--deterministic` - Use fixed seed for reproducible output
- `--format FORMAT` - Output format: sql, json, csv (default: sql)
- `--dry-run` - Preview without writing files

**Examples**:

```bash
# Generate 10 records per entity
specql test seed entities/*.yaml -o seeds/

# Generate 100 records with fixed seed
specql test seed contact.yaml -n 100 --deterministic

# JSON format for API testing
specql test seed order.yaml --format json
```

#### `specql test generate`

Auto-generate test files from SpecQL entities.

```bash
specql test generate <entities...> [options]
```

**Arguments**:
- `<entities...>` - One or more SpecQL YAML entity files

**Options**:
- `-o, --output DIR` - Output directory (default: `tests/`)
- `--type TYPE` - Test type: pgtap, pytest, both (default: both)
- `--include-crud/--no-crud` - Include CRUD tests (default: true)
- `--include-actions/--no-actions` - Include action tests (default: true)
- `--include-constraints/--no-constraints` - Include constraint tests (default: true)
- `--with-seed` - Generate seed data alongside tests
- `--dry-run` - Preview without writing files

**Examples**:

```bash
# Generate both pgTAP and pytest tests
specql test generate entities/*.yaml -o tests/

# Only pgTAP tests
specql test generate contact.yaml --type pgtap

# Tests with seed data
specql test generate entities/*.yaml --with-seed
```

#### `specql test reverse`

Reverse engineer existing tests to SpecQL test specs.

```bash
specql test reverse <test-files...> [options]
```

**Arguments**:
- `<test-files...>` - One or more existing test files

**Options**:
- `-o, --output DIR` - Output directory (default: `test-specs/`)
- `--type TYPE` - Source type: pgtap, pytest, jest, auto (default: auto)
- `--preview` - Preview without writing files

**Examples**:

```bash
# Auto-detect and reverse engineer
specql test reverse tests/*.sql -o specs/

# Specify test type
specql test reverse tests/*.py --type pytest

# Preview without writing
specql test reverse tests/ --preview
```

---

## Planned Commands

The following commands are planned but not yet implemented:

### `specql diff` (Planned)

Compare SpecQL-generated schema with existing schema.

### `specql docs` (Planned)

Generate documentation from SpecQL entities.

### `specql analyze` (Planned)

Analyze codebase and generate migration report.

---

## Global Options

Available for all commands:

```bash
-v, --verbose      Verbose output
-q, --quiet        Suppress non-error output
-o, --output-dir   Output directory
--version          Show version number
--help, -h         Show help message
```

---

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Validation error

---

## Quick Start Examples

### Basic Generation

```bash
# Generate schema from YAML
specql generate entities/*.yaml

# Validate before generating
specql validate entities/*.yaml && specql generate entities/*.yaml
```

### Migration from Existing Project

```bash
# Option 1: Full workflow
specql workflow migrate ./my-project -o migration/

# Option 2: Step by step
specql reverse sql db/*.sql -o entities/
specql validate entities/*.yaml
specql generate entities/*.yaml
```

### CI/CD Integration

```bash
#!/bin/bash
# Validate entities
specql validate entities/*.yaml --strict || exit 1

# Generate code
specql generate entities/*.yaml -o generated/

echo "Generation successful"
```

---

## See Also

- [YAML Syntax Reference](yaml-syntax.md) - Complete syntax guide
- [Rich Types Reference](../03_core-concepts/rich-types.md) - All rich types
- [Action Steps Reference](action-steps-reference.md) - All action step types
- [CLI Status](cli-status.md) - Command implementation status

---

**Last Updated**: 2025-11-21
