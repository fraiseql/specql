# SpecQL - PostgreSQL Code Generator

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

## Quick Start

```bash
pip install specql-generator
cd your-project
specql generate entities/*.yaml
```

## Current Features (Production Ready)

### Core Generation
- **Database**: PostgreSQL with Trinity pattern
- **Backend**: Java/Spring Boot with JPA entities (97% coverage, Lombok support)
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

- 🔜 **Multi-Language**: Rust, TypeScript, Go backends
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
- [SaaS Multi-Tenant](examples/saas-multi-tenant/) - Enterprise patterns
- [Simple Blog](examples/simple-blog/) - CRUD basics

## Community

- [Discord](link) - Get help, share ideas
- [GitHub Discussions](link) - Questions and answers
- [GitHub Issues](link) - Bug reports and feature requests

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and workflow.

## License

MIT License - see [LICENSE](LICENSE)

---

**Current Status**: Production ready for PostgreSQL + GraphQL + Java/Spring Boot
**Python**: 3.10+
**PostgreSQL**: 14+
**Java**: 17+ (Spring Boot 3.x, JPA/Hibernate)
**Total Source**: 359 Python files, 25+ step compilers, comprehensive test suite