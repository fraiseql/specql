# SpecQL - Universal Code Generation Platform

**20 lines YAML → 2000+ lines production code (100x leverage)**

[//]: # (Badges will be added when CI/CD is set up)
[//]: # (![Build Status](https://img.shields.io/github/actions/workflow/status/specql/specql/ci.yml))
[//]: # (![Coverage](https://img.shields.io/codecov/c/github/specql/specql))
[//]: # (![Version](https://img.shields.io/pypi/v/specql))
[//]: # (![License](https://img.shields.io/github/license/specql/specql))

## What is SpecQL?

SpecQL transforms business-domain YAML into production-ready code:

```yaml
# input.yaml (12 lines)
entity: Contact
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

Generates:
- ✅ PostgreSQL tables with Trinity pattern
- ✅ Foreign keys, indexes, constraints
- ✅ PL/pgSQL business logic functions
- ✅ GraphQL schema + TypeScript types
- ✅ Apollo React hooks

**Result**: 99% less code, 100% production-ready

## Quick Start

```bash
pip install specql
specql init my-project
cd my-project
specql generate entities/*.yaml
```

## Features

- **100x Code Leverage**: Write 20 lines, get 2000+
- **Production Ready**: Battle-tested patterns
- **Type Safe**: Full TypeScript integration
- **Multi-Language**: Python, Java, Rust, TypeScript, Go (roadmap)
- **Full Stack**: Backend + Frontend + CI/CD + Infrastructure (roadmap)

## Documentation

- 📚 [Getting Started](docs/00_getting_started/)
- 🎓 [Tutorials](docs/01_tutorials/)
- 📖 [Guides](docs/02_guides/)
- 🔧 [Reference](docs/03_reference/)
- 🏗️ [Architecture](docs/04_architecture/)
- 🔮 [Vision & Roadmap](docs/05_vision/)

## Examples

- [Simple Blog](docs/06_examples/simple_blog/) - CRUD basics
- [CRM System](docs/06_examples/crm_system/) - Complex business logic
- [E-Commerce](docs/06_examples/ecommerce/) - Orders & payments
- [SaaS Multi-Tenant](docs/06_examples/saas_multi_tenant/) - Enterprise patterns

## Community

- [Discord](https://discord.gg/specql) - Chat with the community
- [GitHub Discussions](https://github.com/specql/specql/discussions) - Ask questions
- [Twitter](https://twitter.com/specql) - Follow for updates
- [Blog](https://blog.specql.io) - Technical deep dives

## Contributing

We love contributions! See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE)