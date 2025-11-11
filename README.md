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

Output: PostgreSQL table with Trinity pattern, indexes, audit fields, helper functions.

```sql
CREATE TABLE crm.tb_contact (
  pk_contact INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,
  email TEXT,
  status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP,
  -- ... more audit fields
);
```

## Key Features

- **Convention-based**: Trinity pattern, audit fields, indexes generated automatically
- **Business logic**: Define actions in YAML, get PL/pgSQL functions
- **FraiseQL integration**: GraphQL metadata generation
- **Type-safe**: PostgreSQL composite types, automatic validation
- **Tested**: Comprehensive test coverage, generated test fixtures

## Documentation

- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [Architecture](docs/architecture/) - Technical implementation details
- [API Reference](docs/api/) - Complete API documentation
- [Examples](examples/) - Working examples
- [Guides](docs/guides/) - How-to guides

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