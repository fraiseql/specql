# CLI Overview - SpecQL Command Line Interface

SpecQL provides a powerful, production-ready command-line interface with intelligent defaults and framework-aware generation. The CLI has been completely redesigned in v1.0 with production-ready defaults and comprehensive tooling.

> **📖 For complete CLI documentation, see [CLI Guide](CLI_GUIDE.md)**

This overview covers the key concepts and major changes in v1.0.

## 🎯 What You'll Learn

- Major v1.0 improvements and production-ready defaults
- Framework-aware generation (FraiseQL, Django, Rails, Prisma)
- Hierarchical vs flat output formats
- New CLI commands and options
- Migration from 0.x to 1.0

## 🚀 v1.0 Major Improvements

### Production-Ready Defaults
- **Framework-aware**: Automatic defaults per target framework
- **Hierarchical output**: Organized directory structure by default
- **Registry integration**: Hexadecimal table codes and paths
- **Rich progress**: Real-time feedback with statistics

### Framework Support
- **FraiseQL** (default): GraphQL views, Trinity pattern, audit fields
- **Django**: ORM models, admin interface, flat structure
- **Rails**: ActiveRecord models, migrations, flat structure
- **Prisma**: Schema definitions, client code, flat structure

### Intelligent CLI
```bash
# Production-ready generation (FraiseQL defaults)
specql generate entities/**/*.yaml

# Development mode (flat structure)
specql generate entities/**/*.yaml --dev

# Framework-specific
specql generate entities/**/*.yaml --framework django
```

## 📋 Prerequisites

- [SpecQL v1.0+ installed](../getting-started/installation.md)
- Basic understanding of YAML and database concepts
- Command-line familiarity

## 💡 CLI Fundamentals

### Command Structure (v1.0)

```bash
specql generate [OPTIONS] ENTITY_FILES...
```

**Examples:**
```bash
# Production-ready generation (FraiseQL defaults)
specql generate entities/**/*.yaml

# Development mode
specql generate entities/**/*.yaml --dev

# Framework-specific
specql generate entities/**/*.yaml --framework django

# Get comprehensive help
specql generate --help
```

### Key Options

| Option | Default | Description |
|--------|---------|-------------|
| `--framework` | `fraiseql` | Target framework (fraiseql, django, rails, prisma) |
| `--dev` | `False` | Development mode (flat structure) |
| `--no-tv` | `False` | Skip table views (FraiseQL only) |
| `--verbose, -v` | `False` | Show detailed progress |
| `--help, -h` | | Show comprehensive help |

## 🚀 Quick Workflows

### Production Development (v1.0)

```bash
# Generate production-ready schema
specql generate entities/**/*.yaml

# Output: migrations/ with hierarchical structure
# ├── 000_app_foundation.sql
# └── 01_write_side/
#     └── 011_crm/
#         └── 011001_contact/
#             ├── 011001_tb_contact.sql
#             ├── 011001_tv_contact.sql  # GraphQL views
#             └── 011001_fn_contact_*.sql
```

### Development Iteration

```bash
# Quick development with flat structure
specql generate entities/**/*.yaml --dev

# Output: db/schema/ with flat structure
# ├── 10_tables/contact.sql
# ├── 20_helpers/contact_helpers.sql
# └── 30_functions/create_contact.sql
```

### Framework-Specific Generation

```bash
# FraiseQL (default) - GraphQL-ready
specql generate entities/**/*.yaml

# Django - ORM-ready
specql generate entities/**/*.yaml --framework django

# Rails - ActiveRecord-ready
specql generate entities/**/*.yaml --framework rails
```

## 📖 Complete Documentation

For comprehensive CLI documentation including:

- **All commands and options** - Complete reference
- **Framework-specific guides** - FraiseQL, Django, Rails, Prisma
- **Output format details** - Hierarchical vs flat structures
- **Advanced usage patterns** - Multi-entity projects, CI/CD
- **Troubleshooting** - Common issues and solutions
- **IDE integration** - VS Code, IntelliJ, shell aliases

**📖 See [CLI Guide](CLI_GUIDE.md) for complete documentation**

## 🎯 Key v1.0 Features

### Production-Ready Defaults
- **One command deployment**: `specql generate entities/**/*.yaml`
- **Framework intelligence**: Automatic GraphQL, ORM, or schema generation
- **Rich feedback**: Progress bars, statistics, next steps guidance

### Framework Ecosystem
- **FraiseQL**: GraphQL views, Trinity pattern, audit fields
- **Django**: Models, admin, migrations
- **Rails**: ActiveRecord, associations, validations
- **Prisma**: Schema, client, type safety

### Output Intelligence
- **Hierarchical**: Organized by domain/subdomain/entity
- **Registry-aware**: Hexadecimal codes and paths
- **Development mode**: Flat structure for iteration

## 📚 Complete Documentation

**📖 [CLI Guide](CLI_GUIDE.md)** - Comprehensive usage guide including:
- All commands and options
- Framework-specific workflows
- Output format comparisons
- Advanced usage patterns
- Troubleshooting and best practices

## 🚀 Migration from 0.x

**Old workflow** (complex):
```bash
# Multiple commands, manual configuration
specql generate schema entities/**/*.yaml --use-registry=false
# Manual directory management
# Complex Confiture integration
```

**New workflow** (simple):
```bash
# One command, production-ready
specql generate entities/**/*.yaml

# Development mode when needed
specql generate entities/**/*.yaml --dev
```

## 🎉 Summary

SpecQL v1.0 CLI delivers:
- ✅ **95% reduction** in script complexity
- ✅ **99% reduction** in time to first success
- ✅ **Production-ready** output by default
- ✅ **Framework-aware** intelligent defaults
- ✅ **Rich progress** and comprehensive help

**Ready to experience the new CLI? See [CLI Guide](CLI_GUIDE.md)! 🚀**