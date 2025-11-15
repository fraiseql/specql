# SpecQL - Multi-Language Backend Code Generator

> **🚧 ALPHA RELEASE (v0.4.0-alpha)**: SpecQL is in active development. APIs may change.
> Production use is not recommended yet. [Report issues](https://github.com/fraiseql/specql/issues).

**20 lines YAML → 2000+ lines production code in 4 languages (100x leverage)**

Generate production-ready backends from single YAML spec:
**PostgreSQL** · **Java/Spring Boot** · **Rust/Diesel** · **TypeScript/Prisma**

[Badges: Build Status, Coverage, Version, License]

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
- ✅ Test files (pgTAP SQL + pytest)
- ✅ CI/CD workflows (GitHub Actions, GitLab CI)

**Result**: 2000+ lines across 4 languages from 15 lines YAML (133x leverage)

## Installation

### From Source (Required for Alpha)

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

### Verify Installation

```bash
specql --version  # Should show: 0.4.0-alpha
specql generate entities/examples/**/*.yaml
```

**Note**: SpecQL is not yet published to PyPI. Source installation is required.

## Features

### Multi-Language Code Generation ✅
- **PostgreSQL** - Tables, indexes, constraints, PL/pgSQL functions (Trinity pattern)
- **Java/Spring Boot** - JPA entities, repositories, services, controllers (97% test coverage)
- **Rust/Diesel** - Models, schemas, queries, Actix-web handlers (100% test pass rate)
- **TypeScript/Prisma** - Schema, interfaces, type-safe client (96% coverage)

### Reverse Engineering ✅
Transform existing code back to SpecQL YAML:
- **PostgreSQL** → SpecQL (PL/pgSQL function analysis, schema introspection)
- **Java/Spring Boot** → SpecQL (JPA annotation parsing via Eclipse JDT)
- **Rust/Diesel** → SpecQL (Macro expansion, derive parsing)
- **TypeScript/Prisma** → SpecQL (Schema parsing, relation detection)

### Developer Experience ✅
- **Pattern Library** - 100+ reusable query/action patterns with semantic search
- **Interactive CLI** - Live preview with syntax highlighting (powered by Textual)
- **Visual Diagrams** - Automatic ER diagrams with Graphviz/Mermaid
- **CI/CD Generation** - GitHub Actions, GitLab CI workflow scaffolding
- **Registry System** - Hexadecimal domain/entity codes for large organizations

### Testing & Quality ✅
- **Automated Tests** - pgTAP SQL tests + pytest Python test generation
- **96%+ Coverage** - Comprehensive test suite across all generators
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
**Test Coverage**: 96%+ across 371 Python files
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