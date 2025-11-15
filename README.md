# SpecQL - PostgreSQL Code Generator

> **🚧 ALPHA RELEASE (v0.4.0-alpha)**: SpecQL is in active development. APIs may change.
> Production use is not recommended yet. [Report issues](https://github.com/fraiseql/specql/issues).

**20 lines YAML → 2000+ lines production code (100x leverage)**

[Badges: Build Status, Coverage, Version, License]

## What is SpecQL?

SpecQL transforms business-domain YAML into production-ready PostgreSQL + GraphQL:

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

**Auto-generates**:
- ✅ PostgreSQL tables (Trinity pattern: pk_*, id, identifier)
- ✅ Foreign keys, indexes, constraints, audit fields
- ✅ PL/pgSQL functions (`crm.qualify_lead`, `app.qualify_lead`)
- ✅ FraiseQL metadata for GraphQL auto-discovery
- ✅ TypeScript types + Apollo React hooks
- ✅ Test files (pgTAP + pytest)

**Result**: 2000+ lines from 15 lines (133x leverage)

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

## Current Features (Production Ready)

### Core Generation
- **Database**: PostgreSQL with Trinity pattern
- **Backend**: Java/Spring Boot with JPA entities (97% coverage, Lombok support)
- **Backend**: TypeScript/Prisma with schema generation (96% coverage, round-trip validation)
- **Actions**: PL/pgSQL functions with type safety
- **Frontend**: TypeScript types, GraphQL schema, Apollo hooks
- **Testing**: pgTAP SQL tests + pytest Python tests

### Advanced Features
- **Pattern Library**: 100+ reusable query/action patterns
- **Reverse Engineering**: PostgreSQL → SpecQL YAML
- **Interactive CLI**: Live preview with syntax highlighting
- **CI/CD**: Generate GitHub Actions/GitLab CI workflows
- **Registry System**: Hexadecimal domain/entity codes for organization

## Roadmap Features (Coming Soon)

- 🔜 **Multi-Language**: Rust, Go backends (TypeScript ✅ Complete)
- 🔜 **Frontend**: React, Vue, Angular component generation
- 🔜 **Full Stack**: Complete apps from single YAML spec
- 🔜 **Universal CI/CD**: Platform-agnostic pipeline definition
- 🔜 **Infrastructure**: Universal cloud deployment spec

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