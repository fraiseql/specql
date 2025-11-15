# Frequently Asked Questions (FAQ)

## Table of Contents
- [General Questions](#general-questions)
- [Getting Started](#getting-started)
- [Using SpecQL](#using-specql)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Performance](#performance)

## General Questions

### What is SpecQL?
SpecQL is a multi-language backend code generator. Write your data model once in YAML, and SpecQL generates production-ready code for PostgreSQL, Java/Spring Boot, Rust/Diesel, and TypeScript/Prisma.

**Quick example**: 15 lines YAML → 2000+ lines across 4 languages (100x code leverage).

### Why should I use SpecQL?
Use SpecQL if you:
- Build backends in multiple languages
- Want to keep data models in sync across services
- Need complex business logic in your database
- Are tired of writing CRUD boilerplate
- Want 100x code leverage

### Is it production-ready?
**v0.4.0-alpha**: The core code generation is production-ready with 96%+ test coverage and 2,937 passing tests. However:
- ✅ Use for backend code generation
- ⚠️ APIs may evolve based on feedback
- ⚠️ Test thoroughly before production deployment

We're using it to migrate PrintOptim (real production SaaS).

### What's the difference between SpecQL and Prisma?
| Aspect | SpecQL | Prisma |
|--------|--------|--------|
| Languages | 4 (PostgreSQL, Java, Rust, TypeScript) | 1 (TypeScript) |
| Business Logic | Full support (compiles to PL/pgSQL) | Application-level only |
| Reverse Engineering | 5 languages (planned) | Database introspection only |
| Use Case | Multi-language backends | TypeScript backends |

**Choose SpecQL** for multi-language systems with complex business logic.
**Choose Prisma** for TypeScript-only backends with simpler requirements.

[Full comparison](../comparisons/SPECQL_VS_ALTERNATIVES.md)

### How does SpecQL compare to Hasura?
**Hasura**: Instant GraphQL API from database schema
**SpecQL**: Multi-language code generation including database schema

They solve different problems:
- Use Hasura if you want instant GraphQL from existing database
- Use SpecQL if you need to generate code across multiple languages

You can even use both: Generate schema with SpecQL, expose with Hasura.

### What's the license?
MIT License - free for commercial use, no restrictions.

### Who maintains SpecQL?
SpecQL is built and maintained by [Lionel Hamayon](https://github.com/lionelh) and open-source contributors.

---

## Getting Started

### How do I install SpecQL?
**v0.4.0-alpha** (current):
```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

**Coming soon** (v0.5.0-beta):
```bash
pip install specql-generator
```

[Installation guide](../00_getting_started/QUICKSTART.md)

### What are the prerequisites?
**Required**:
- Python 3.11 or higher
- `uv` package manager

**Optional**:
- PostgreSQL (for testing schemas)
- Java JDK 11+ (for Java reverse engineering - future)
- Rust toolchain (for Rust reverse engineering - future)

### How do I create my first entity?
```yaml
# contact.yaml
entity: Contact
schema: crm

fields:
  email: email
  name: text
  phone: text
```

Then generate:
```bash
specql generate contact.yaml
```

[Quickstart tutorial](../00_getting_started/QUICKSTART.md)

### Where can I find examples?
We have 5 complete examples:
- [Simple Blog](../06_examples/SIMPLE_BLOG.md)
- [CRM System](../06_examples/CRM_SYSTEM_COMPLETE.md)
- [E-commerce](../06_examples/ECOMMERCE_SYSTEM.md)
- [User Authentication](../06_examples/USER_AUTHENTICATION.md)
- [Multi-Tenant SaaS](../06_examples/MULTI_TENANT_SAAS.md)

Plus 20+ entity examples in `entities/examples/`

---

## Using SpecQL

### What field types are supported?
**Basic types**:
- `text` - String/varchar
- `integer` - Whole number
- `decimal` - Decimal number
- `boolean` - True/false
- `timestamp` - Date and time
- `date` - Date only
- `time` - Time only
- `json` - JSON data
- `uuid` - UUID

**Semantic types**:
- `email` - Email address
- `url` - URL
- `phone` - Phone number

**Relationships**:
- `ref(Entity)` - Foreign key
- `enum(val1, val2)` - Enumeration

[Complete field type reference](../03_reference/yaml/complete_reference.md#field-types)

### How do I define relationships?
```yaml
entity: Contact
schema: crm

fields:
  company: ref(Company)  # Foreign key to Company
```

This generates:
- PostgreSQL: `FOREIGN KEY (fk_company) REFERENCES crm.tb_company(pk_company)`
- Java: `@ManyToOne` relationship
- Rust: Diesel foreign key
- TypeScript: Prisma relation

### How do I add business logic?
Use actions:

```yaml
actions:
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: sales_team
```

This compiles to a PL/pgSQL function: `crm.fn_contact_qualify_lead()`

[Actions guide](../02_guides/ACTIONS.md)

### Can I customize generated code?
**Yes, three ways**:

1. **Edit templates** (advanced): Modify Jinja2 templates in `src/templates/`
2. **Post-generation edits**: Edit generated code directly
3. **Mix generated + manual**: Use generated code as foundation, add custom code

Generated code is meant to be a starting point or fully managed depending on your needs.

### Can I use SpecQL with an existing database?
**Yes!** Use reverse engineering (planned for v0.6.0):

```bash
# From PostgreSQL (coming soon)
specql reverse postgresql schema.sql --output entities/

# From Python (planned)
specql reverse python models.py --output entities/

# From Java (planned)
specql reverse java src/main/java/models/ --output entities/
```

**Current Status**: Reverse engineering parsers exist in codebase but not yet exposed via CLI.

[Reverse engineering guide](../02_guides/REVERSE_ENGINEERING.md)

### Does SpecQL support migrations?
**Currently**: Generate fresh schema, use external migration tool (Flyway, Liquibase, Alembic)

**Future** (v0.6.0): Built-in migration generation from YAML diffs

For now:
```bash
# Generate schema
specql generate entities/**/*.yaml

# Use your migration tool
flyway migrate
# or
alembic upgrade head
```

### Can I generate only specific targets?
**Yes**:

```bash
# PostgreSQL only
specql generate entities/**/*.yaml --target postgresql

# Java only
specql generate entities/**/*.yaml --target java

# Multiple targets
specql generate entities/**/*.yaml --target postgresql,java
```

---

## Troubleshooting

### Installation fails with "Python version not supported"
**Symptom**: Error during installation

**Solution**:
```bash
# Check Python version
python --version  # Need 3.11+

# If using older Python, install 3.11+
# macOS
brew install python@3.11

# Linux
sudo apt-get install python3.11
# or
sudo yum install python311

# Windows
# Download from python.org
```

### `specql` command not found after installation
**Symptom**: Command not in PATH

**Solution**:

```bash
# Check where uv installed it
python -m site --user-base

# Add to PATH
# macOS/Linux (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Windows
# Add %USERPROFILE%\.local\bin to PATH environment variable

# Restart terminal and try again
specql --version
```

### "Invalid field type" error
**Symptom**:
```
❌ Invalid field type: 'string'
```

**Solution**: Use `text` instead of `string`

Valid types: `text`, `integer`, `decimal`, `boolean`, `timestamp`, etc.

[Complete type list](../03_reference/yaml/complete_reference.md#field-types)

### "Circular dependency detected"
**Symptom**: Entities reference each other

**Solution**: This is OK! SpecQL supports circular references.

Ensure:
- Both entities exist
- Reference syntax is correct: `ref(EntityName)`
- Entity names match exactly (case-sensitive)

### Generated code doesn't compile
**Symptom**: Syntax errors in generated code

**Solution**:

1. **Check SpecQL version**:
   ```bash
   specql --version  # Should be 0.4.0-alpha or newer
   ```

2. **Update SpecQL**:
   ```bash
   cd ~/code/specql
   git pull origin main
   uv sync
   ```

3. **Report issue**:
   - Include YAML that caused issue
   - Include error message
   - [Open issue](https://github.com/fraiseql/specql/issues)

### Tests fail after generating code
**Symptom**: Integration tests break

**Possible causes**:
1. Database schema changed (run migrations)
2. Generated code conflicts with manual code
3. Test data needs updating

**Solution**:
```bash
# Regenerate test database
dropdb test_db && createdb test_db
psql test_db < output/postgresql/**/*.sql

# Run tests
pytest
```

### How do I enable debug logging?
```bash
# Verbose output
specql generate entities/**/*.yaml --verbose

# Debug mode (very detailed)
export SPECQL_LOG_LEVEL=DEBUG
specql generate entities/**/*.yaml
```

---

## Advanced Usage

### Can I extend SpecQL with custom generators?
**Yes!** SpecQL is designed to be extensible.

Create custom generator in `src/generators/your_language/`:
```python
from src.core.generator_base import GeneratorBase

class YourLanguageGenerator(GeneratorBase):
    def generate(self, entity):
        # Your generation logic
        pass
```

[Generator development guide](../07_contributing/GENERATOR_DEVELOPMENT.md)

### How do I contribute?
We welcome contributions!

1. Read [Contributing Guide](../../CONTRIBUTING.md)
2. Check [open issues](https://github.com/fraiseql/specql/issues)
3. Look for "good first issue" label
4. Join discussions on GitHub

### Is there a roadmap?
**Yes!**

- **v0.4.0-alpha** (current): Multi-language backend generation
- **v0.5.0-beta**: PyPI publication, UX improvements
- **v0.6.0**: Go/GORM support, migration generation
- **v1.0**: Stable APIs, production-hardened

[Full roadmap](https://github.com/fraiseql/specql/issues/17)

### Can I use this commercially?
**Yes!** MIT License allows commercial use with no restrictions.

### How can I get help?
- **Documentation**: [docs/](../)
- **GitHub Issues**: [Report bugs](https://github.com/fraiseql/specql/issues)
- **Discussions**: [Ask questions](https://github.com/fraiseql/specql/discussions)
- **Examples**: [docs/06_examples/](../06_examples/)

---

## Performance

### How fast is code generation?
**Benchmarks** (M1 MacBook Pro):
- TypeScript parsing: 37,233 entities/sec
- Java parsing: 1,461 entities/sec
- PostgreSQL generation: ~1,000 entities/sec
- 50-entity system: <2 seconds total

### Can SpecQL handle large systems?
**Yes!** We've tested with:
- 100+ entities
- Complex relationships
- Thousands of lines of generated code

Performance stays good even at scale.

### Does it support incremental generation?
**Currently**: Full regeneration recommended

**Future**: Incremental generation planned for v0.6.0

For now:
```bash
# Regenerate everything (fast anyway)
specql generate entities/**/*.yaml
```

---

## More Questions?

**Can't find your question?**

- Check [troubleshooting guide](TROUBLESHOOTING.md)
- Search [GitHub issues](https://github.com/fraiseql/specql/issues)
- Ask in [GitHub Discussions](https://github.com/fraiseql/specql/discussions)
- Look at [examples](../06_examples/)

**Found a bug?**
[Report it](https://github.com/fraiseql/specql/issues/new)

**Have a feature idea?**
[Suggest it](https://github.com/fraiseql/specql/issues/new)

---

**Last updated**: 2024-11-15