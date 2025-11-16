# SpecQL - Multi-Language Backend Code Generator

[![PyPI version](https://badge.fury.io/py/specql-generator.svg)](https://pypi.org/project/specql-generator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/specql-generator.svg)](https://pypi.org/project/specql-generator/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/specql-generator.svg)](https://pypistats.org/packages/specql-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **🚧 v0.4.0-alpha**: Production-ready for backend generation. APIs stable. [Report issues](https://github.com/fraiseql/specql/issues).

**One YAML spec → PostgreSQL + Java + Rust + TypeScript** (100x code leverage)

SpecQL generates production-ready backends from business-domain YAML. Write your data model once, deploy across 4 languages.

## Quick Example

15 lines of YAML:
```yaml
entity: Contact
schema: crm

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner
```

**Auto-generates** 2000+ lines across 4 languages:
- ✅ **PostgreSQL**: Tables, indexes, constraints, audit fields, PL/pgSQL functions
- ✅ **Java/Spring Boot**: JPA entities, repositories, services, controllers
- ✅ **Rust/Diesel**: Models, schemas, queries, Actix-web handlers
- ✅ **TypeScript/Prisma**: Schema, interfaces, type-safe client

Plus: FraiseQL GraphQL metadata, tests, CI/CD workflows.

**[Try it now](#installation)** | **[Read the guide](docs/00_getting_started/README.md)**

## See It In Action

### Installation
![Installation Demo](docs/demos/installation.gif)

### Quick Start
![Quick Start Demo](docs/demos/quickstart_demo.gif)

### Multi-Language Generation
![Multi-Language Demo](docs/demos/multi_language_demo.gif)

### Reverse Engineering
![Reverse Engineering Demo](docs/demos/reverse_engineering.gif)

## What is SpecQL?

SpecQL transforms business-domain YAML into production-ready multi-language backend code:

```yaml
# contact.yaml (15 lines - from actual example)
entity: Contact
schema: crm

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Auto-generates** (from this single YAML):

**PostgreSQL**:
- ✅ Tables with Trinity pattern (pk_*, id, identifier)
- ✅ Foreign keys, indexes, constraints, audit fields
- ✅ PL/pgSQL functions with full business logic

**Java/Spring Boot**:
- ✅ JPA entities with Lombok annotations
- ✅ Repository interfaces (JpaRepository)
- ✅ Service classes with business logic
- ✅ REST controllers with validation

**Rust/Diesel**:
- ✅ Model structs with Diesel derives
- ✅ Schema definitions (schema.rs)
- ✅ Query builders and repositories
- ✅ Actix-web HTTP handlers

**TypeScript/Prisma**:
- ✅ Prisma schema with relations
- ✅ TypeScript interfaces and types
- ✅ Type-safe client generation

**Plus**:
- ✅ FraiseQL metadata for GraphQL auto-discovery
- ✅ **70+ automated tests** (pgTAP SQL + pytest integration)
- ✅ CI/CD workflows (GitHub Actions, GitLab CI)

**Result**: 2000+ lines across 4 languages **+ 70+ tests** from 15 lines YAML (140x leverage)

## Automated Testing

SpecQL automatically generates comprehensive test suites for your entities:

### Generate Tests

```bash
# Generate both pgTAP and pytest tests
specql generate-tests entities/contact.yaml

# Generate only pgTAP (PostgreSQL unit tests)
specql generate-tests entities/*.yaml --type pgtap

# Generate only pytest (Python integration tests)
specql generate-tests entities/*.yaml --type pytest --output-dir tests/integration/
```

### What Tests Are Generated?

From a single Contact entity (15 lines of YAML), SpecQL generates **70+ comprehensive tests**:

**pgTAP Tests** (PostgreSQL unit tests):
- ✅ **Structure validation** (10+ tests): Tables, columns, constraints, indexes
- ✅ **CRUD operations** (15+ tests): Create, read, update, delete with happy/error paths
- ✅ **Constraint validation** (8+ tests): NOT NULL, foreign keys, unique constraints
- ✅ **Business logic** (12+ tests): Action execution, state transitions, validations

**pytest Tests** (Python integration tests):
- ✅ **Integration tests** (10+ tests): End-to-end CRUD workflows
- ✅ **Action tests** (8+ tests): Business action execution
- ✅ **Error handling** (6+ tests): Duplicate detection, validation errors
- ✅ **Edge cases** (5+ tests): Boundary conditions, state machine paths

### Example: Contact Entity

```yaml
# contact.yaml (15 lines)
entity: Contact
schema: crm

fields:
  email: email
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Generates**:
```sql
-- test_contact_structure.sql (50+ lines)
SELECT has_table('crm', 'tb_contact', 'Contact table exists');
SELECT has_column('crm', 'tb_contact', 'email', 'Has email column');
SELECT col_is_pk('crm', 'tb_contact', 'pk_contact', 'PK constraint');
-- ... 7 more structure tests

-- test_contact_crud.sql (100+ lines)
SELECT lives_ok(
  $$SELECT app.create_contact('test@example.com')$$,
  'Create contact succeeds'
);
-- ... 14 more CRUD tests

-- test_contact_actions.sql (80+ lines)
SELECT ok(
  (SELECT app.qualify_lead(contact_id)).status = 'success',
  'Qualify lead action succeeds'
);
-- ... 11 more action tests
```

```python
# test_contact_integration.py (150+ lines)
class TestContactIntegration:
    def test_create_contact_happy_path(self, clean_db):
        result = execute("SELECT app.create_contact('test@example.com')")
        assert result['status'] == 'success'

    def test_qualify_lead_action(self, clean_db):
        # ... 9 more integration tests
```

### Reverse Engineer Existing Tests

Import your existing pgTAP or pytest tests into universal TestSpec format:

```bash
# Parse pgTAP tests
specql reverse-tests tests/test_contact.sql

# Parse pytest tests with coverage analysis
specql reverse-tests tests/test_*.py --analyze-coverage

# Convert to universal YAML format
specql reverse-tests test.sql --entity=Contact --output-dir=specs/ --format=yaml
```

**Use cases**:
- 📊 **Coverage analysis** - Find missing test scenarios
- 🔄 **Framework migration** - Convert between test frameworks
- 📚 **Documentation** - Generate test documentation from code
- 🎯 **Gap detection** - Identify untested business logic

## Installation

### From Source (Required for v0.4.0-alpha)

```bash
# Prerequisites: Python 3.11+, uv
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh

git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

### Verify Installation

```bash
# Check CLI is available
specql --help

# Generate a test example
specql generate entities/examples/contact_lightweight.yaml --dry-run

# You should see generation output without errors
```

**Coming soon**: PyPI package (`pip install specql-generator`) in v0.5.0-beta

### Prerequisites

- **Python**: 3.11 or higher
- **uv**: [Installation guide](https://github.com/astral-sh/uv)
- **PostgreSQL** (optional): For testing generated schemas
- **Java JDK 11+** (optional): For Java reverse engineering

**Troubleshooting**: See [Installation Guide](docs/00_getting_started/INSTALLATION.md)

## CLI Commands

SpecQL provides a comprehensive CLI for all development workflows:

### `specql init` - Project Scaffolding
Create new projects from templates:
```bash
specql init blog myblog        # Blog platform (Post, Author, Comment)
specql init minimal myproject  # Single entity example
```

### `specql generate` - Code Generation
Generate multi-language code from YAML:
```bash
specql generate entities/*.yaml                    # All languages
specql generate contact.yaml --target postgresql  # PostgreSQL only
specql generate entities/ --dry-run               # Preview without writing
```

### `specql validate` - Pre-flight Validation
Validate entities before generation:
```bash
specql validate entities/*.yaml           # Basic validation
specql validate entities/ --strict        # Fail on warnings
specql validate entities/ --format json   # JSON output for CI
```

### `specql examples` - Built-in Examples
Learn from working examples:
```bash
specql examples --list                    # List all examples
specql examples with-actions             # Show specific example
specql examples blog-post > post.yaml    # Save to file
```

### Complete Command Reference
See [CLI Commands Reference](docs/02_guides/CLI_COMMANDS.md) for all options and examples.

## Architecture

![SpecQL Architecture](docs/04_architecture/diagrams/high_level_overview.png)

[See detailed architecture documentation →](docs/04_architecture/ARCHITECTURE_VISUAL.md)

## Features

### Multi-Language Code Generation ✅
Generate production-ready code from single YAML specification:

#### PostgreSQL (Verified ✅)
- Database schema with Trinity pattern (pk_*, id, identifier)
- Foreign keys, indexes, constraints, audit fields
- PL/pgSQL functions with business logic
- Test coverage: 96%+
- Example: [See PostgreSQL Generator](docs/03_reference/generators/POSTGRESQL.md)

#### Java/Spring Boot (Verified ✅)
- JPA entities with Lombok annotations
- Repository interfaces (JpaRepository)
- Service classes with business logic
- REST controllers with validation
- Test coverage: 97%
- Performance: 1,461 entities/sec
- Example: [See Java Generator](docs/03_reference/generators/JAVA.md)

#### Rust/Diesel (Verified ✅)
- Model structs with Diesel derives
- Schema definitions (schema.rs)
- Query builders and repositories
- Actix-web HTTP handlers
- Test pass rate: 100%
- Example: [See Rust Generator](docs/03_reference/generators/RUST.md)

#### TypeScript/Prisma (Verified ✅)
- Prisma schema with relations
- TypeScript interfaces and types
- Type-safe client generation
- Test coverage: 96%
- Performance: 37,233 entities/sec
- Example: [See TypeScript Generator](docs/03_reference/generators/TYPESCRIPT.md)

### Reverse Engineering (Partial 🔄)
Transform existing code back to SpecQL YAML:
- **PostgreSQL** → SpecQL (schema introspection)
- **Python** → SpecQL (dataclass and Pydantic parsing)
- **Java/Rust/TypeScript** → SpecQL (in development)

### Developer Tools (Partial 🔄)
- **Interactive CLI** - Live preview with syntax highlighting
- **Pattern Library** - Reusable patterns with semantic search
- **Visual Diagrams** - Graphviz/Mermaid schema generation
- **CI/CD Generation** - GitHub Actions, GitLab CI, CircleCI support
- **Infrastructure as Code** - Terraform, Kubernetes, Docker Compose
- **Automated Test Generation** - 70+ pgTAP SQL tests + pytest integration tests per entity

### FraiseQL Integration (Partial 🔄)
- Automatic GraphQL metadata generation
- Vector search support via pgvector
- Auto-discovery for instant GraphQL APIs
- [FraiseQL Integration Guide](docs/02_guides/FRAISEQL_INTEGRATION.md)

### Testing & Quality ✅
- **Automated Test Generation** - Generate 70+ comprehensive tests per entity (pgTAP + pytest)
- **96%+ Coverage** - Comprehensive test suite across 389 Python files (2937 tests)
- **Performance Benchmarks** - 1,461 Java entities/sec, 37,233 TypeScript entities/sec
- **Security** - SQL injection prevention, comprehensive security audit

## Roadmap (Coming Soon)

- 🔜 **Go Backend** - Go structs, GORM, HTTP handlers
- 🔜 **Frontend** - React, Vue, Angular component generation
- 🔜 **Infrastructure as Code** - Complete Terraform/Pulumi/CloudFormation
- 🔜 **Full-Stack Deployment** - Single-command deployment to cloud
- 🔜 **PyPI Package** - Install via `pip install specql`

See [VISION.md](VISION.md) and [roadmap](docs/05_vision/roadmap.md)

## Documentation

- 📚 [Getting Started](docs/00_getting_started/) - 5-minute quick start
- 🎓 [Tutorials](docs/01_tutorials/) - Step-by-step guides
- 📖 [Guides](docs/02_guides/) - Complete feature documentation
- 🔧 [Reference](docs/03_reference/) - YAML syntax reference
- 🏗️ [Architecture](docs/04_architecture/) - How SpecQL works
- 🔮 [Vision](docs/05_vision/) - Future roadmap

## Real Examples

All from `examples/` and `entities/examples/`:

- [Contact Manager](examples/crm/) - Simple CRM
- [E-Commerce](examples/ecommerce/) - Orders, payments, inventory
- [Java/Spring Boot](examples/java/) - JPA entities with Lombok support
- [TypeScript/Prisma](examples/typescript/) - Prisma schemas with TypeScript interfaces
- [SaaS Multi-Tenant](examples/saas-multi-tenant/) - Enterprise patterns
- [Simple Blog](examples/simple-blog/) - CRUD basics

## Community & Support

**Alpha Release**: SpecQL is in early alpha. We're building in public!

- 📖 [Documentation](docs/) - Complete guides and references
- 🐛 [Report Bugs](https://github.com/fraiseql/specql/issues) - Help us improve
- 💡 [Feature Requests](https://github.com/fraiseql/specql/issues) - Share your ideas
- 📦 [Examples](examples/) - Working code examples
- 📝 [Changelog](CHANGELOG.md) - See what's new

**Coming Soon**: Discord community and GitHub Discussions

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and workflow.

## License

MIT License - see [LICENSE](LICENSE)

---

## Current Status

**Release**: 🚧 **Alpha (v0.4.0-alpha)** - Multi-language backend generation
**Languages**: PostgreSQL + Java + Rust + TypeScript
**Test Coverage**: 96%+ across 389 Python files (2937 tests)
**Stability**: Pre-release - APIs subject to change

### Supported Technologies
- **PostgreSQL**: 14+ with Trinity pattern (pk_*, id, identifier)
- **Java**: 17+ (Spring Boot 3.x, JPA/Hibernate, Lombok)
- **Rust**: 1.70+ (Diesel 2.x, Actix-web)
- **TypeScript**: 4.9+ (Prisma Client, type-safe interfaces)

### Known Limitations
- Frontend generation not yet implemented
- Infrastructure as Code partial (Terraform/Pulumi in progress)
- Not published to PyPI (install from source only)
- Discord and GitHub Discussions not yet available