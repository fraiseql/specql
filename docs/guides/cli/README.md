# CLI Overview - SpecQL Command Line Interface

SpecQL provides a comprehensive command-line interface for generating schemas, validating specifications, running tests, and managing your data models. This guide introduces the CLI structure, common workflows, and available commands.

## 🎯 What You'll Learn

- CLI command structure and conventions
- Core workflows and use cases
- Command categories and purposes
- Getting help and troubleshooting
- Integration with development tools

## 📋 Prerequisites

- [SpecQL installed](../getting-started/installation.md)
- Basic understanding of YAML and database concepts
- Command-line familiarity

## 💡 CLI Fundamentals

### Command Structure

```bash
specql [OPTIONS] COMMAND [SUBCOMMAND] [ARGS]...
```

**Examples:**
```bash
# Generate schema from entities
specql generate schema entities/user.yaml

# Validate YAML files
specql validate entities/*.yaml

# Run tests
specql test run --type pgtap entities/user.yaml

# Get help
specql --help
specql generate --help
```

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `--help, -h` | Show help message | `specql --help` |
| `--version, -V` | Show version | `specql --version` |
| `--verbose, -v` | Verbose output | `specql validate --verbose` |
| `--quiet, -q` | Suppress output | `specql generate --quiet` |
| `--env TEXT` | Environment (default: local) | `specql generate --env staging` |
| `--config PATH` | Config file path | `specql --config custom.yaml` |

## 📊 Command Categories

### Core Commands

| Command | Purpose | Frequency |
|---------|---------|-----------|
| **`generate`** | Create database schemas and tests | Daily |
| **`validate`** | Check YAML syntax and consistency | Per change |
| **`test run`** | Execute generated tests | Per change |
| **`test coverage`** | Generate coverage reports | Per change |

### Utility Commands

| Command | Purpose | Use Case |
|---------|---------|----------|
| **`check-codes`** | Verify table code uniqueness | CI/CD |
| **`diff`** | Compare generated vs existing SQL | Schema changes |
| **`docs`** | Generate documentation | Documentation |

### Advanced Commands

| Command | Purpose | Advanced Use |
|---------|---------|--------------|
| **`generate`** with `--with-impacts` | Frontend codegen | Full-stack |
| **`test run`** with `--performance` | Benchmarking | Performance |
| **`generate`** with `--foundation-only` | Database setup | Infrastructure |

## 🚀 Common Workflows

### Development Cycle

```bash
# 1. Edit entity specification
vim entities/user.yaml

# 2. Validate changes
specql validate entities/user.yaml

# 3. Generate schema
specql generate schema entities/user.yaml

# 4. Apply to database
psql $DATABASE_URL -f db/schema/10_tables/user.sql

# 5. Generate tests
specql generate tests entities/user.yaml

# 6. Run tests
specql test run entities/user.yaml

# 7. Check coverage
specql test coverage entities/user.yaml
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
steps:
  - name: Validate
    run: specql validate entities/*.yaml

  - name: Generate Schema
    run: specql generate schema entities/*.yaml

  - name: Apply Schema
    run: psql $DATABASE_URL -f db/schema/**/*.sql

  - name: Generate Tests
    run: specql generate tests entities/*.yaml

  - name: Run Tests
    run: specql test run entities/*.yaml

  - name: Coverage Report
    run: specql test coverage entities/*.yaml --format html
```

### Multi-Entity Project

```bash
# Validate all entities
specql validate entities/**/*.yaml

# Generate complete schema
specql generate schema entities/**/*.yaml

# Generate all tests
specql generate tests entities/**/*.yaml

# Run parallel tests
specql test run --parallel entities/**/*.yaml

# Check table codes
specql check-codes entities/**/*.yaml
```

## 🛠️ Command Reference

### `specql generate`

**Generate database schemas, functions, and tests from YAML specifications.**

```bash
specql generate [OPTIONS] COMMAND [ARGS]...
```

**Subcommands:**
- `schema` - Generate PostgreSQL schema (tables, functions, constraints)
- `tests` - Generate test files (pgTAP, pytest, performance)

**Key Options:**
- `--type [pgtap|pytest|performance]` - Test type to generate
- `--with-impacts` - Generate GraphQL impact metadata
- `--output-frontend PATH` - Generate frontend TypeScript code
- `--env TEXT` - Target environment
- `--foundation-only` - Generate only database foundation

**Examples:**
```bash
# Basic schema generation
specql generate schema entities/user.yaml

# Full-stack codegen
specql generate entities/**/*.yaml --with-impacts --output-frontend src/generated

# Environment-specific
specql generate schema entities/**/*.yaml --env production
```

### `specql validate`

**Validate YAML entity specifications for syntax errors and consistency.**

```bash
specql validate [OPTIONS] ENTITY_FILES...
```

**Key Options:**
- `--verbose, -v` - Show detailed validation output
- `--check-impacts` - Validate impact declarations

**Examples:**
```bash
# Validate single file
specql validate entities/user.yaml

# Validate with verbose output
specql validate entities/user.yaml --verbose

# Validate all entities
specql validate entities/**/*.yaml
```

### `specql test run`

**Execute generated tests against your database.**

```bash
specql test run --type TYPE [OPTIONS] ENTITY_FILES...
```

**Test Types:**
- `pgtap` - PostgreSQL native tests (fast, database-level)
- `pytest` - Python integration tests (comprehensive, app-level)
- `performance` - Benchmarking tests (measure performance)

**Key Options:**
- `--type [pgtap|pytest|performance]` - Test type (required)
- `--verbose, -v` - Detailed test output
- `--parallel` - Run tests in parallel
- `--filter PATTERN` - Run specific tests
- `--timeout SECONDS` - Test timeout
- `--junit-xml PATH` - Export JUnit XML

**Examples:**
```bash
# Run pgTAP tests
specql test run --type pgtap entities/user.yaml

# Run with coverage
specql test run --type pytest entities/user.yaml --cov

# Run performance tests
specql test run --type performance entities/user.yaml

# Parallel execution
specql test run --type pgtap entities/*.yaml --parallel
```

### `specql test coverage`

**Generate test coverage reports.**

```bash
specql test coverage [OPTIONS] ENTITY_FILES...
```

**Key Options:**
- `--format [text|html|json|xml]` - Output format
- `--output PATH` - Output file path

**Examples:**
```bash
# Text coverage report
specql test coverage entities/user.yaml

# HTML coverage report
specql test coverage entities/user.yaml --format html --output coverage.html

# JSON for CI/CD
specql test coverage entities/user.yaml --format json --output coverage.json
```

### `specql check-codes`

**Verify uniqueness of table codes across all entities.**

```bash
specql check-codes [OPTIONS] ENTITY_FILES...
```

**Key Options:**
- `--format [text|json|csv]` - Output format
- `--export PATH` - Export results to file

**Examples:**
```bash
# Check all entities
specql check-codes entities/**/*.yaml

# Export as CSV
specql check-codes entities/ --format csv --export table_codes.csv
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SPECQL_ENV` | Environment override | `local` |
| `SPECQL_CONFIG` | Config file path | `confiture.yaml` |

**Example:**
```bash
export DATABASE_URL="postgresql://localhost:5432/myapp"
export SPECQL_ENV="staging"
```

### Config File (`confiture.yaml`)

```yaml
schema_dirs:
  - path: db/schema/00_foundation
    order: 0
  - path: db/schema/10_tables
    order: 10
  - path: db/schema/40_functions
    order: 40

environments:
  local:
    database_url: postgresql://localhost:5432/myapp_dev
  staging:
    database_url: ${DATABASE_URL}
  production:
    database_url: ${DATABASE_URL}
```

## 🔧 IDE Integration

### VS Code Tasks

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "SpecQL: Validate",
      "type": "shell",
      "command": "specql",
      "args": ["validate", "entities/*.yaml"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "silent",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "SpecQL: Generate Schema",
      "type": "shell",
      "command": "specql",
      "args": ["generate", "schema", "entities/*.yaml"],
      "group": "build"
    },
    {
      "label": "SpecQL: Generate Tests",
      "type": "shell",
      "command": "specql",
      "args": ["generate", "tests", "entities/*.yaml"],
      "group": "test"
    },
    {
      "label": "SpecQL: Run Tests",
      "type": "shell",
      "command": "specql",
      "args": ["test", "run", "entities/*.yaml"],
      "group": "test"
    }
  ]
}
```

### IntelliJ IDEA External Tools

**Settings → Tools → External Tools**

- **Name:** SpecQL Validate
- **Program:** `specql`
- **Arguments:** `validate entities/*.yaml`
- **Working directory:** `$ProjectFileDir$`

### Shell Aliases

```bash
# ~/.bashrc or ~/.zshrc
alias specql-validate='specql validate entities/*.yaml'
alias specql-generate='specql generate schema entities/*.yaml'
alias specql-tests='specql generate tests entities/*.yaml && specql test run entities/*.yaml'
alias specql-coverage='specql test coverage entities/*.yaml --format html --output coverage.html'
```

## 🚨 Error Handling

### Common Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Success | None |
| `1` | General error | Check error message |
| `2` | File not found | Verify file paths |
| `3` | Configuration error | Check config file |
| `4` | Validation error | Fix YAML syntax |
| `5` | Database error | Check connection |

### Debugging Commands

```bash
# Verbose output
specql validate entities/user.yaml --verbose

# Check database connection
psql $DATABASE_URL -c "SELECT 1;"

# Verify file permissions
ls -la entities/

# Check Python environment
python --version
pip list | grep specql
```

## 📊 CLI Analytics

### Usage Tracking

SpecQL can track command usage for analytics:

```bash
# Enable analytics
export SPECQL_ANALYTICS=true

# View usage stats
specql analytics show

# Export analytics
specql analytics export --format json --output usage.json
```

### Performance Monitoring

```bash
# Time command execution
time specql generate schema entities/*.yaml

# Profile memory usage
/usr/bin/time -v specql test run entities/*.yaml

# Check command history
history | grep specql
```

## 🎯 Best Practices

### Command Organization
- **Validate early** - Always validate before generating
- **Use wildcards** - `entities/*.yaml` for batch operations
- **Environment awareness** - Use `--env` for different deployments
- **Parallel execution** - Use `--parallel` for faster testing

### Workflow Optimization
- **Pre-commit hooks** - Automate validation and testing
- **IDE integration** - Set up tasks for common operations
- **Shell aliases** - Create shortcuts for frequent commands
- **CI/CD integration** - Automate in pipelines

### Error Prevention
- **Version control** - Commit tested YAML files
- **Backup databases** - Before applying schema changes
- **Test locally** - Verify commands work before CI/CD
- **Monitor resources** - Watch for long-running commands

## 🆘 Troubleshooting

### "Command not found: specql"
```bash
# Check installation
pip list | grep specql

# Reinstall
pip install --upgrade specql

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "Database connection failed"
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql
```

### "Validation errors"
```bash
# Get detailed errors
specql validate entities/user.yaml --verbose

# Common issues:
# - YAML syntax errors
# - Unknown field types
# - Missing required fields
# - Invalid pattern configuration
```

### "Tests failing"
```bash
# Run with verbose output
specql test run entities/user.yaml --verbose

# Check test generation
specql generate tests entities/user.yaml --force

# Verify database state
psql $DATABASE_URL -c "SELECT * FROM user LIMIT 5;"
```

### "Permission denied"
```bash
# Check file permissions
ls -la entities/

# Grant database permissions
psql $DATABASE_URL -c "GRANT ALL ON SCHEMA public TO specql_user;"

# Check user permissions
whoami
groups
```

## 📚 Related Documentation

- **[Getting Started](../getting-started/)** - Installation and basic usage
- **[YAML Reference](../reference/yaml-reference.md)** - Entity specification format
- **[CLI Reference](../reference/cli-reference.md)** - Complete command reference
- **[Troubleshooting](../troubleshooting/)** - Common issues and solutions

## 🎉 Summary

The SpecQL CLI provides:
- ✅ **Comprehensive tooling** - Generate, validate, test, and deploy
- ✅ **Developer-friendly** - Simple commands for complex operations
- ✅ **CI/CD ready** - Integrates with all major platforms
- ✅ **Extensible** - Supports custom workflows and integrations
- ✅ **Well-documented** - Complete help and examples

## 🚀 What's Next?

- **[Generate Commands](generate.md)** - Schema and test generation
- **[Validate Commands](validate.md)** - YAML validation and checking
- **[Test Commands](test.md)** - Running and managing tests
- **[Performance Commands](performance.md)** - Benchmarking and optimization
- **[Workflows](workflows.md)** - Common development patterns

**Ready to master the SpecQL CLI? Let's explore the commands! 🚀**