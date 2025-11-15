# CLI Command Reference

**Complete SpecQL command-line interface** - All commands, flags, and options

This reference documents every SpecQL CLI command with all available options, verified against the actual implementation.

## 🎯 Command Overview

SpecQL provides a comprehensive CLI for code generation, validation, and project management.

## 🔧 specql generate

**Generate code from YAML entities**

```bash
specql generate ENTITY_FILES... [OPTIONS]
```

**Description**: Transform YAML entity definitions into production-ready PostgreSQL + GraphQL code.

### Core Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output-dir` | PATH | `migrations` | Output directory for generated files |
| `--foundation-only` | FLAG | `false` | Generate only app foundation (no entities) |
| `--include-tv` | FLAG | `false` | Generate table views |
| `--framework` | CHOICE | `fraiseql` | Target framework (`fraiseql`, `django`, `rails`, `prisma`) |
| `--target` | CHOICE | `postgresql` | Target language (`postgresql`, `python_django`, `python_sqlalchemy`) |
| `--use-registry` | FLAG | `true` | Use hexadecimal registry for file paths |
| `--no-use-registry` | FLAG | `false` | Disable registry-based paths |
| `--output-format` | CHOICE | `hierarchical` | Output format (`hierarchical`, `confiture`) |
| `--hierarchical` | FLAG | `true` | Use hierarchical file structure |
| `--flat` | FLAG | `false` | Use flat file structure |
| `--dry-run` | FLAG | `false` | Preview generation without writing files |
| `--with-impacts` | FLAG | `false` | Generate mutation impacts JSON |
| `--output-frontend` | PATH | `none` | Generate frontend code (TypeScript types, hooks) |
| `--with-query-patterns` | FLAG | `false` | Generate SQL views from query patterns |
| `--with-audit-cascade` | FLAG | `false` | Integrate cascade with audit trail |
| `--with-outbox` | FLAG | `false` | Generate CDC outbox table |
| `--dev` | FLAG | `false` | Development mode (flat structure in `db/schema/`) |
| `--no-tv` | FLAG | `false` | Skip table view generation |
| `--verbose`, `-v` | FLAG | `false` | Show detailed progress information |

### Usage Examples

**Basic generation with hierarchical structure:**
```bash
specql generate entities/*.yaml
```

**Development mode with flat structure:**
```bash
specql generate entities/*.yaml --dev
```

**Generate with frontend code:**
```bash
specql generate entities/*.yaml --with-impacts --output-frontend=src/generated
```

**Preview generation:**
```bash
specql generate entities/*.yaml --dry-run --verbose
```

**Full-featured generation:**
```bash
specql generate entities/*.yaml \
  --with-impacts \
  --with-query-patterns \
  --with-audit-cascade \
  --with-outbox \
  --output-frontend=src/generated \
  --verbose
```

### Output Structure

#### Hierarchical (Default)
```
migrations/
├── 01_write_side/
│   ├── 012_crm/
│   │   └── 0123_customer/
│   │       └── 01236_contact/
│   │           ├── 012361_tb_contact.sql
│   │           ├── 012362_fn_qualify_lead.sql
│   │           └── 012363_fn_create_contact.sql
└── 02_query_side/
    └── 022_crm/
        └── 0223_customer/
            └── 0220310_tv_contact.sql
```

#### Flat (--dev)
```
db/schema/
├── 10_tables/
│   └── contact.sql
├── 20_views/
│   └── contact_view.sql
└── 30_functions/
    └── qualify_lead.sql
```

## 🔍 specql validate

**Validate YAML syntax and semantics**

```bash
specql validate ENTITY_FILES... [OPTIONS]
```

**Description**: Check YAML files for syntax errors, semantic issues, and best practices violations.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--strict` | FLAG | `false` | Treat warnings as errors |
| `--schema-only` | FLAG | `false` | Validate only schema structure |
| `--rules` | LIST | `all` | Specific validation rules to run |
| `--verbose`, `-v` | FLAG | `false` | Show detailed validation output |

### Usage Examples

**Basic validation:**
```bash
specql validate entities/*.yaml
```

**Strict validation:**
```bash
specql validate entities/*.yaml --strict
```

**Validate specific rules:**
```bash
specql validate entities/*.yaml --rules naming,types,references
```

## 🔄 specql diff

**Compare schemas and generate migrations**

```bash
specql diff SOURCE TARGET [OPTIONS]
```

**Description**: Compare two schema states and generate migration scripts.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | PATH | `migrations` | Output directory for migration files |
| `--type` | CHOICE | `incremental` | Migration type (`incremental`, `full`) |
| `--safe` | FLAG | `true` | Generate only safe migrations |
| `--verbose`, `-v` | FLAG | `false` | Show detailed diff information |

### Usage Examples

**Compare current vs target:**
```bash
specql diff current_schema/ target_schema/
```

**Generate full migration:**
```bash
specql diff old_version/ new_version/ --type full
```

## 📚 specql docs

**Generate documentation**

```bash
specql docs ENTITY_FILES... [OPTIONS]
```

**Description**: Generate HTML/PDF documentation from YAML entities.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | PATH | `docs` | Output directory for documentation |
| `--format` | CHOICE | `html` | Output format (`html`, `pdf`, `markdown`) |
| `--template` | PATH | `default` | Documentation template |
| `--include-diagrams` | FLAG | `true` | Generate schema diagrams |
| `--verbose`, `-v` | FLAG | `false` | Show documentation generation progress |

### Usage Examples

**Generate HTML docs:**
```bash
specql docs entities/*.yaml --output docs/
```

**Generate PDF documentation:**
```bash
specql docs entities/*.yaml --format pdf --output specql-docs.pdf
```

## 📊 specql diagram

**Generate schema diagrams**

```bash
specql diagram ENTITY_FILES... [OPTIONS]
```

**Description**: Create visual diagrams of entity relationships and schemas.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | PATH | `diagrams` | Output directory for diagrams |
| `--format` | CHOICE | `png` | Diagram format (`png`, `svg`, `pdf`) |
| `--type` | CHOICE | `erd` | Diagram type (`erd`, `uml`, `flow`) |
| `--include-fields` | FLAG | `true` | Show field details |
| `--include-actions` | FLAG | `false` | Show action relationships |

### Usage Examples

**Generate ERD diagram:**
```bash
specql diagram entities/*.yaml --type erd --output diagrams/
```

**Generate UML class diagram:**
```bash
specql diagram entities/*.yaml --type uml --format svg
```

## 🔄 specql reverse

**Reverse engineer from database**

```bash
specql reverse [OPTIONS]
```

**Description**: Import existing PostgreSQL schema into SpecQL YAML.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--connection` | STRING | `env` | Database connection string |
| `--schema` | STRING | `public` | Database schema to import |
| `--output` | PATH | `entities` | Output directory for YAML files |
| `--include-data` | FLAG | `false` | Include sample data |
| `--exclude-tables` | LIST | `none` | Tables to exclude |
| `--verbose`, `-v` | FLAG | `false` | Show reverse engineering progress |

### Usage Examples

**Reverse engineer schema:**
```bash
specql reverse --schema crm --output entities/
```

**Import with sample data:**
```bash
specql reverse --include-data --exclude-tables audit_log,backup_*
```

## 🏷️ specql registry

**Manage domain registry**

```bash
specql registry COMMAND [OPTIONS]
```

**Description**: Manage the hexadecimal registry system for entity organization.

### Commands

#### list
```bash
specql registry list [OPTIONS]
```

**Options**:
- `--domain` - Filter by domain
- `--format` - Output format (`table`, `json`, `csv`)

#### add
```bash
specql registry add DOMAIN ENTITY [OPTIONS]
```

**Options**:
- `--code` - Specific hexadecimal code
- `--description` - Entity description

#### remove
```bash
specql registry remove DOMAIN ENTITY
```

#### update
```bash
specql registry update DOMAIN ENTITY [OPTIONS]
```

**Options**:
- `--description` - Update description
- `--code` - Update code

### Usage Examples

**List registry:**
```bash
specql registry list
```

**Add entity:**
```bash
specql registry add crm Contact --description "Customer contacts"
```

**Update entity:**
```bash
specql registry update crm Contact --description "Updated description"
```

## 🔄 specql cicd

**Generate CI/CD configurations**

```bash
specql cicd [OPTIONS]
```

**Description**: Generate CI/CD pipeline configurations for various platforms.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--platform` | CHOICE | `github` | CI/CD platform (`github`, `gitlab`, `jenkins`, `circleci`) |
| `--output` | PATH | `.github` | Output directory |
| `--include` | LIST | `all` | Components to include (`lint`, `test`, `build`, `deploy`) |
| `--database` | STRING | `postgres` | Database for testing |
| `--node-version` | STRING | `18` | Node.js version for builds |

### Usage Examples

**Generate GitHub Actions:**
```bash
specql cicd --platform github --output .github/
```

**Generate GitLab CI:**
```bash
specql cicd --platform gitlab --output .gitlab-ci.yml
```

## 📡 specql cdc

**Configure Change Data Capture**

```bash
specql cdc [OPTIONS]
```

**Description**: Set up CDC (Change Data Capture) for real-time data streaming.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | PATH | `cdc` | Output directory |
| `--format` | CHOICE | `debezium` | CDC format (`debezium`, `maxwell`, `custom`) |
| `--include-tables` | LIST | `all` | Tables to include in CDC |
| `--exclude-tables` | LIST | `none` | Tables to exclude from CDC |
| `--topic-prefix` | STRING | `specql` | Kafka topic prefix |

### Usage Examples

**Setup Debezium CDC:**
```bash
specql cdc --format debezium --output cdc/
```

**Custom CDC configuration:**
```bash
specql cdc --format custom --include-tables user,order --topic-prefix myapp
```

## ⚡ specql performance

**Performance analysis and optimization**

```bash
specql performance [OPTIONS]
```

**Description**: Analyze and optimize SpecQL-generated database performance.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--analyze` | FLAG | `true` | Run performance analysis |
| `--optimize` | FLAG | `false` | Generate optimization scripts |
| `--output` | PATH | `performance` | Output directory |
| `--connection` | STRING | `env` | Database connection for analysis |
| `--verbose`, `-v` | FLAG | `false` | Show detailed analysis |

### Usage Examples

**Performance analysis:**
```bash
specql performance --analyze --connection "postgresql://..."
```

**Generate optimizations:**
```bash
specql performance --optimize --output optimizations/
```

## 🧠 specql embeddings

**Generate embeddings for search**

```bash
specql embeddings [OPTIONS]
```

**Description**: Generate vector embeddings for semantic search capabilities.

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | PATH | `embeddings` | Output directory |
| `--model` | STRING | `text-embedding-ada-002` | Embedding model |
| `--fields` | LIST | `description,name` | Fields to embed |
| `--batch-size` | INT | `100` | Processing batch size |
| `--verbose`, `-v` | FLAG | `false` | Show embedding progress |

### Usage Examples

**Generate embeddings:**
```bash
specql embeddings --output embeddings/ --fields description,name,notes
```

**Use custom model:**
```bash
specql embeddings --model custom-model --batch-size 50
```

## 🎯 Global Options

These options work with all commands:

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--help` | `-h` | FLAG | `false` | Show help information |
| `--version` | `-V` | FLAG | `false` | Show version information |
| `--verbose` | `-v` | FLAG | `false` | Enable verbose output |
| `--quiet` | `-q` | FLAG | `false` | Suppress non-error output |
| `--config` | `-c` | PATH | `~/.specql/config.yaml` | Configuration file path |
| `--log-level` | | CHOICE | `info` | Logging level (`debug`, `info`, `warn`, `error`) |
| `--no-color` | | FLAG | `false` | Disable colored output |

## 📋 Configuration File

SpecQL can be configured via `~/.specql/config.yaml`:

```yaml
# Default settings
output_dir: "migrations"
framework: "fraiseql"
use_registry: true

# Database connections
databases:
  default:
    host: "localhost"
    port: 5432
    database: "specql"
    user: "specql"

# Generation preferences
generation:
  include_views: true
  frontend_output: "src/generated"
  with_impacts: true

# CLI preferences
cli:
  verbose: false
  color: true
```

## 🚀 Command Chaining

Commands can be chained using `&&` for complex workflows:

```bash
# Validate, generate, and test
specql validate entities/*.yaml && \
specql generate entities/*.yaml --with-impacts && \
npm test
```

## 📊 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Validation failed |
| 3 | Generation failed |
| 4 | Database connection failed |
| 5 | Configuration error |

## 🔍 Troubleshooting

### Common Issues

**"Command not found"**
- Ensure SpecQL is installed: `pip install specql-generator`
- Check PATH: `which specql`

**"Permission denied"**
- Check file permissions on output directories
- Ensure database user has necessary privileges

**"Connection refused"**
- Verify database is running
- Check connection string and credentials
- Ensure correct port (default: 5432)

**"Invalid YAML"**
- Use `specql validate` to check syntax
- Common issues: indentation, quotes, colons

### Debug Mode

Enable detailed logging:

```bash
specql generate entities/*.yaml --verbose --log-level debug
```

### Getting Help

```bash
# General help
specql --help

# Command-specific help
specql generate --help
specql validate --help
```

## 📚 Related Topics

- **[Workflows Guide](../../02_guides/WORKFLOWS.md)** - Development and migration workflows
- **[Troubleshooting Guide](../../../08_troubleshooting/)** - Common issues and solutions