# SpecQL

Business logic to production PostgreSQL + GraphQL generator.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

SpecQL generates production-ready PostgreSQL schema and PL/pgSQL functions from YAML business logic definitions. Write business rules in 20 lines of YAML, get 2000+ lines of tested SQL.

**Three-Tier Architecture**: Primitives → Domain Patterns → Entity Templates
- **15 Domain Patterns**: Reusable business logic (state machines, audit trails, validation, etc.)
- **22 Entity Templates**: Ready-to-use business entities (CRM Contact, E-Commerce Product, etc.)
- **Pattern Composition**: Combine patterns for complex business logic

Define entities, fields, and actions in YAML; get tested SQL output with automatic audit trails, indexes, and GraphQL integration.

## 🏗️ Three-Tier Architecture

SpecQL uses a composable three-tier architecture:

### Tier 1: Primitives (35 actions)
Atomic building blocks like `query`, `update`, `validate`, `call_function`

### Tier 2: Domain Patterns (15 patterns)
Reusable business logic patterns:
- **State Machine**: Workflow management with transitions
- **Audit Trail**: Automatic tracking of changes
- **Soft Delete**: Safe record deletion
- **Validation Chain**: Business rule validation
- **Approval Workflow**: Multi-stage approvals
- And 10 more patterns...

### Tier 3: Entity Templates (22 templates)
Ready-to-use business entities:
- **CRM**: Contact, Lead, Opportunity, Account
- **E-Commerce**: Product, Order, Cart, Customer
- **Healthcare**: Patient, Appointment, Prescription
- **Project Management**: Project, Task, Milestone
- **HR**: Employee, Position, Department
- **Finance**: Invoice, Payment, Transaction

**Example**: `extends: crm.contact_template` gives you a complete contact entity with state machine, audit trail, and 15+ pre-built actions.

## 🧠 Pattern Library (NEW!)

SpecQL includes an intelligent **Pattern Library** that automatically discovers, stores, and reuses business logic patterns using PostgreSQL + vector search + Grok LLM.

### Features

- **🤖 Pattern Discovery**: Automatically finds reusable patterns in your legacy SQL
- **🔍 Intelligent Search**: Semantic search using vector embeddings (pgvector)
- **📝 Natural Language Generation**: Create patterns from plain English descriptions
- **👥 Human Review Workflow**: Approve/reject pattern suggestions
- **⚡ Fast Retrieval**: <50ms search using HNSW indexes
- **💰 Zero Cost**: Free Grok LLM, local PostgreSQL

### Quick Start

```bash
# 1. Setup pattern library database
export SPECQL_DB_URL="postgresql://user:password@localhost:5432/specql_patterns"
./scripts/setup_database.sh
psql $SPECQL_DB_URL -f database/pattern_library_schema.sql
psql $SPECQL_DB_URL -f database/seed_patterns.sql

# 2. Generate embeddings
specql embeddings generate

# 3. Discover patterns from SQL
specql reverse --discover-patterns complex_function.sql

# 4. Review suggestions
specql patterns review-suggestions
specql patterns approve 1

# 5. Generate patterns from text
specql patterns create-from-description \
  --description "Multi-step approval workflow with audit logging" \
  --category workflow

# 6. Search patterns
specql patterns search "approval process"
```

### Pattern Categories

- **Workflow**: Approval processes, state machines, validation chains
- **Audit**: Change tracking, audit trails, compliance logging
- **Data**: Hierarchical structures, temporal data, reference data
- **Custom**: Your domain-specific patterns

### Architecture

```
PostgreSQL + pgvector + HNSW indexes
    ↓
Pattern Discovery (AI analysis of SQL)
    ↓
Vector Embeddings (384-dim sentence-transformers)
    ↓
Semantic Search (<50ms retrieval)
    ↓
Human Review → Pattern Library
```

See [Pattern Library User Guide](docs/pattern_library/USER_GUIDE.md) for complete documentation.

## 📚 Documentation

- **[Domain Pattern Catalog](docs/patterns/domain_pattern_catalog.md)** - All 15 domain patterns
- **[Entity Template Catalog](docs/patterns/entity_template_catalog.md)** - All 22 entity templates
- **[Pattern Composition Guide](docs/patterns/pattern_composition_guide.md)** - Combining patterns
- **[Template Customization Guide](docs/patterns/template_customization_guide.md)** - Extending templates

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

### Optional: Java Development Kit (JDK)

**Required for**: Java/JPA reverse engineering (optional feature)

If you want to reverse engineer Java JPA entities, you'll need JDK 11+:

```bash
# Ubuntu/Debian
sudo apt install openjdk-17-jdk

# macOS
brew install openjdk@17

# Windows
choco install temurin17

# Verify setup
./scripts/verify_java_setup.sh
```

**Note**: SpecQL works fine without JDK - it only affects Java parsing. All other features (schema generation, actions, CLI) work normally. See [docs/JAVA_SETUP.md](docs/JAVA_SETUP.md) for detailed instructions.

## Quick Example

**Option 1: Use Entity Templates (Recommended)**

Input (YAML):
```yaml
entity: Contact
extends: crm.contact_template
fields:
  custom_field: text  # Add custom fields
```

**Option 2: Manual Definition**

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

SpecQL provides an intelligent CLI with production-ready defaults, framework-aware generation, and pattern library management.

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

### Pattern Library Commands

```bash
# Pattern Management
specql patterns review-suggestions          # List pending pattern suggestions
specql patterns show <id>                   # Show pattern suggestion details
specql patterns approve <id>                # Approve pattern suggestion
specql patterns reject <id> --reason "..."  # Reject pattern suggestion
specql patterns list [--category <cat>]     # List approved patterns
specql patterns search <query>              # Search patterns semantically
specql patterns create-from-description     # Generate pattern from text

# Embeddings Management
specql embeddings generate                  # Generate embeddings for all patterns
specql embeddings test-retrieval <query>    # Test similarity search

# Reverse Engineering with Discovery
specql reverse <file> --discover-patterns    # Analyze SQL with pattern discovery
```

## Key Features

- **Convention-based**: Trinity pattern, audit fields, indexes generated automatically
- **Business logic**: Define actions in YAML, get PL/pgSQL functions
- **FraiseQL integration**: GraphQL metadata generation
- **Type-safe**: PostgreSQL composite types, automatic validation
- **Visual documentation**: Automatic ER diagram generation (Graphviz, Mermaid, HTML)
- **Tested**: Comprehensive test coverage, generated test fixtures

## Documentation

- [FAQ](docs/FAQ.md) - Frequently asked questions (SpecQL vs transpilers, ORMs, etc.)
- [Getting Started](GETTING_STARTED.md) - Quick start guide
- [Java Setup](docs/JAVA_SETUP.md) - JDK installation for Java reverse engineering (optional)
- [CLI Guide](docs/guides/CLI_GUIDE.md) - Comprehensive CLI usage guide
- [Pattern Library User Guide](docs/pattern_library/USER_GUIDE.md) - Pattern library usage
- [Pattern Library Developer Guide](docs/pattern_library/DEVELOPER_GUIDE.md) - Extending patterns
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