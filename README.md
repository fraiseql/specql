# SpecQL

Business logic to production PostgreSQL + GraphQL generator.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

SpecQL generates production-ready PostgreSQL schema and PL/pgSQL functions from YAML business logic definitions. Write business rules in 20 lines of YAML, get 2000+ lines of tested SQL.

Define entities, fields, and actions in YAML; get tested SQL output with automatic audit trails, indexes, and GraphQL integration.

## Installation

### From PyPI (Recommended)
```bash
pip install specql-generator
# or with uv
uv pip install specql-generator
```

### From Source
```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

## Quick Example

Input (YAML):
```yaml
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Generate production-ready schema** (FraiseQL defaults):
```bash
specql generate entities/contact.yaml
```

Output: Hierarchical directory structure with GraphQL-ready tables, Trinity pattern, audit fields, and helper functions.

```
migrations/
├── 000_app_foundation.sql
└── 01_write_side/
    └── 011_crm/
        └── 011001_contact/
            ├── 011001_tb_contact.sql    # Table with Trinity pattern
            ├── 011001_tv_contact.sql    # GraphQL view
            └── 011001_fn_contact_*.sql  # Business logic functions
```

**Development mode** (flat structure):
```bash
specql generate entities/contact.yaml --dev
```

Output: Simple flat structure for development iteration.

```
db/schema/
├── 10_tables/contact.sql
├── 20_helpers/contact_helpers.sql
└── 30_functions/qualify_lead.sql
```

## 🚀 GraphQL Cascade Support

SpecQL automatically generates GraphQL Cascade data for FraiseQL integration,
enabling automatic GraphQL client cache updates.

**Zero configuration required!** Just define impact metadata in your actions:

```yaml
actions:
  - name: create_post
    impact:
      primary:
        entity: Post
        operation: CREATE
```

SpecQL automatically includes cascade data in `mutation_result.extra_metadata._cascade`.

See [Automatic GraphQL Cascade](docs/features/AUTOMATIC_GRAPHQL_CASCADE.md) for details.

## CLI Usage

SpecQL provides an intelligent CLI with production-ready defaults and framework-aware generation.

### Production-Ready Generation (Default)

```bash
# Generate for FraiseQL (full-stack GraphQL)
specql generate entities/**/*.yaml
```

**Features**:
- ✅ Hierarchical directory structure
- ✅ Table views (tv_*) for GraphQL queries
- ✅ Trinity pattern (pk_*, id, identifier)
- ✅ Audit fields and helper functions
- ✅ Rich progress output and statistics

### Development Mode

```bash
# Quick development iteration
specql generate entities/**/*.yaml --dev
```

**Features**:
- ✅ Flat directory structure
- ✅ Fast generation for development
- ✅ Confiture-compatible output

### Framework-Specific Generation

```bash
# Generate for different frameworks
specql generate entities/**/*.yaml --framework django
specql generate entities/**/*.yaml --framework rails
specql generate entities/**/*.yaml --framework prisma
```

**Framework Defaults**:
- **FraiseQL**: GraphQL views, Trinity pattern, hierarchical output
- **Django**: ORM models, admin interface, flat output
- **Rails**: ActiveRecord models, migrations, flat output
- **Prisma**: Schema definitions, client code, flat output

See [CLI Guide](docs/guides/CLI_GUIDE.md) for comprehensive usage documentation.

## Key Features

- **Convention-based**: Trinity pattern, audit fields, indexes generated automatically
- **Business logic**: Define actions in YAML, get PL/pgSQL functions
- **FraiseQL integration**: GraphQL metadata generation
- **Type-safe**: PostgreSQL composite types, automatic validation
- **Tested**: Comprehensive test coverage, generated test fixtures

## Documentation

- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [CLI Guide](docs/guides/CLI_GUIDE.md) - Comprehensive CLI usage guide
- [Architecture](docs/architecture/) - Technical implementation details
- [API Reference](docs/api/) - Complete API documentation
- [Examples](examples/) - Working examples
- [Guides](docs/guides/) - How-to guides
- [CLI Reference](docs/reference/cli-reference.md) - Legacy CLI reference

## Project Status

- **Version**: 0.2.0 (Beta)
- **Tests**: Comprehensive test suite (1,185 tests, >95% coverage)
- **Coverage**: >95%
- **Stability**: Beta - Core features stable, API may evolve
- **Production Use**: Suitable for evaluation and testing

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Development

```bash
# Run tests
make test

# Run specific team tests
make teamA-test  # Parser
make teamB-test  # Schema
make teamC-test  # Actions

# Format code
make format
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Author

**Lionel Hamayon**
- Email: lionel.hamayon@evolution-digitale.fr
- GitHub: [@fraiseql](https://github.com/fraiseql)

## License

MIT License - Copyright (c) 2025 Lionel Hamayon

See [LICENSE](LICENSE) for full details.