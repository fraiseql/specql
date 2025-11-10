# SpecQL Documentation

Welcome to the comprehensive documentation for SpecQL, a powerful framework for building business logic libraries with automatic test generation and CLI tools.

## 🎯 What is SpecQL?

SpecQL is a code generation framework that transforms YAML entity definitions into:
- **27 Reusable Mutation Patterns** for common business logic operations
- **Automatic Test Generation** for pgTAP and pytest
- **Complete CLI Tooling** for development workflows

## 🚀 Quick Start

New to SpecQL? Get started in 5 minutes:

1. **[Install SpecQL](getting-started/installation.md)**
2. **[Create Your First Entity](getting-started/first-entity.md)**
3. **[Use Your First Pattern](getting-started/first-pattern.md)**
4. **[Generate Your First Tests](getting-started/first-tests.md)**

## 📚 Documentation Sections

### Getting Started
- **[Installation Guide](getting-started/installation.md)** - Set up SpecQL in your environment
- **[First Entity](getting-started/first-entity.md)** - Define your first business entity
- **[First Pattern](getting-started/first-pattern.md)** - Use a mutation pattern
- **[First Tests](getting-started/first-tests.md)** - Generate automatic tests

### Guides
- **[Mutation Patterns](guides/mutation-patterns/)** - Complete library of 27 reusable patterns
  - [State Machines](guides/mutation-patterns/state-machines.md) - Workflow management
  - [Multi-Entity Operations](guides/mutation-patterns/multi-entity.md) - Cross-entity logic
  - [Batch Operations](guides/mutation-patterns/batch-operations.md) - Bulk processing
  - [Validation](guides/mutation-patterns/validation.md) - Data validation patterns
  - [Composing Patterns](guides/mutation-patterns/composing-patterns.md) - Advanced combinations

- **[Test Generation](guides/test-generation/)** - Automatic testing capabilities
  - [pgTAP Tests](guides/test-generation/pgtap-tests.md) - PostgreSQL native testing
  - [pytest Tests](guides/test-generation/pytest-tests.md) - Python integration testing
  - [Performance Testing](guides/test-generation/performance-tests.md) - Benchmarking
  - [CI/CD Integration](guides/test-generation/ci-cd-integration.md) - Automated pipelines

- **[CLI Tools](guides/cli/)** - Command-line interface
  - [Generate Commands](guides/cli/generate.md) - Code generation
  - [Validate Commands](guides/cli/validate.md) - Schema validation
  - [Test Commands](guides/cli/test.md) - Test execution
  - [Performance Commands](guides/cli/performance.md) - Benchmarking
  - [Common Workflows](guides/cli/workflows.md) - Development patterns

### Reference
- **[CLI Reference](reference/cli-reference.md)** - Complete command reference
- **[Pattern Library API](reference/pattern-library-api.md)** - All 27 patterns documented
- **[Test Generation API](reference/test-generation-api.md)** - Testing framework details
- **[YAML Schema](reference/yaml-schema.md)** - Entity definition format
- **[Error Codes](reference/error-codes.md)** - Troubleshooting reference

### Examples
- **[Basic Examples](examples/basic/)** - Simple use cases
  - [Simple CRUD](examples/basic/simple-crud.md)
  - [State Machine](examples/basic/state-machine.md)
  - [Validation](examples/basic/validation.md)

- **[Intermediate Examples](examples/intermediate/)** - Real-world scenarios
  - [Multi-Entity Operations](examples/intermediate/multi-entity.md)
  - [Batch Processing](examples/intermediate/batch-operations.md)
  - [Business Workflows](examples/intermediate/workflows.md)

- **[Advanced Examples](examples/advanced/)** - Complex patterns
  - [Saga Pattern](examples/advanced/saga-pattern.md)
  - [Event-Driven Architecture](examples/advanced/event-driven.md)
  - [Performance Tuning](examples/advanced/performance-tuning.md)

### Tutorials
- **[01: Hello SpecQL](tutorials/01-hello-specql.md)** - 5-minute introduction
- **[02: Building a CRM](tutorials/02-building-crm.md)** - Complete application (30 min)
- **[03: State Machines](tutorials/03-state-machines.md)** - Workflow implementation (45 min)
- **[04: Testing](tutorials/04-testing.md)** - Test generation and execution (30 min)
- **[05: Production](tutorials/05-production.md)** - Deployment and monitoring (60 min)

### Best Practices
- **[Pattern Selection](best-practices/pattern-selection.md)** - Choosing the right patterns
- **[Entity Design](best-practices/entity-design.md)** - Designing effective entities
- **[Testing Strategy](best-practices/testing-strategy.md)** - Comprehensive testing approaches
- **[Performance](best-practices/performance.md)** - Optimization techniques
- **[Security](best-practices/security.md)** - Security considerations

### Troubleshooting
- **[Common Issues](troubleshooting/common-issues.md)** - Frequently encountered problems
- **[Pattern Errors](troubleshooting/pattern-errors.md)** - Pattern-specific issues
- **[Test Generation Errors](troubleshooting/test-generation-errors.md)** - Testing problems
- **[Debugging](troubleshooting/debugging.md)** - Debugging techniques

## 💡 Key Concepts

### YAML Specifications
SpecQL uses simple YAML files to define your data models and business logic:

```yaml
# Example entity with patterns
name: order
fields:
  id: uuid
  status: string
  total: decimal
patterns:
  - name: state_machine
    states: [pending, confirmed, shipped, delivered]
    transitions:
      - from: pending
        to: confirmed
        trigger: confirm
```

### Generated Output
From this simple spec, SpecQL generates:
- **Database Schema** - Tables, constraints, indexes
- **Business Logic** - Functions, triggers, views
- **Tests** - Comprehensive test coverage
- **Documentation** - API docs and guides

## 🎯 Who Should Use SpecQL?

### ✅ Perfect For
- **Startups** - Rapid prototyping and MVP development
- **Enterprises** - Consistent, scalable business logic
- **Developers** - Focus on business logic, not boilerplate
- **Teams** - Standardized patterns across projects

### 🚀 Use Cases
- **E-commerce** - Order management, inventory, payments
- **SaaS Applications** - User management, subscriptions, billing
- **Financial Systems** - Account management, transactions, compliance
- **Workflow Applications** - Approval processes, state machines

## 🔧 Installation

```bash
# Install via pip (recommended)
pip install specql

# Or install from source
git clone https://github.com/your-org/specql
cd specql
pip install -e .
```

## 📈 Why SpecQL?

### ⚡ Productivity
- **10x faster** development with patterns
- **Zero-effort testing** with auto-generation
- **Consistent architecture** across projects

### 🛡️ Quality
- **Battle-tested patterns** from real applications
- **Comprehensive testing** out of the box
- **Performance optimized** SQL generation

### 🔧 Maintainability
- **YAML specifications** are easy to read and modify
- **Version control friendly** - text-based specs
- **Documentation auto-generated** from code

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) for details.

### Documentation Contributions
- Found an error? [Open an issue](https://github.com/your-org/specql/issues)
- Have an example? [Submit a PR](https://github.com/your-org/specql/pulls)
- Need help? [Join our Discord](https://discord.gg/specql)

## 📄 License

SpecQL is open source software licensed under the MIT License.

---

## 🎯 Next Steps

1. **[Get Started](getting-started/)** - Install and create your first entity
2. **[Explore Patterns](guides/mutation-patterns/)** - See what's possible
3. **[Try Examples](examples/)** - Learn by doing
4. **[Join Community](https://discord.gg/specql)** - Get help and share ideas

**Ready to build something amazing? Let's get started! 🚀**