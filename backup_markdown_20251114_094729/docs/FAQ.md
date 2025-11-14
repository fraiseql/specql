# SpecQL Frequently Asked Questions (FAQ)

## General Questions

### What is SpecQL?

SpecQL is a **business logic compiler** that generates complete production systems from declarative YAML specifications. You write business domain definitions in 20 lines of YAML, and SpecQL generates 2,000+ lines of production-ready code including database schema, business logic functions, GraphQL API, TypeScript types, and tests.

### How is SpecQL different from traditional ORMs?

Traditional ORMs (like Django ORM, ActiveRecord, Prisma) help you **write code** to interact with databases. SpecQL **generates the complete system** from specifications.

| Feature | Traditional ORM | SpecQL |
|---------|----------------|--------|
| **You Write** | Classes, models, methods | Business domain YAML |
| **Framework Generates** | Query builders | Complete system architecture |
| **Code Volume** | 50-200 lines per entity | 20 lines YAML → 2,000+ lines generated |
| **Conventions** | Manual configuration | Automatic (Trinity, audit, indexes) |
| **Multi-language** | Single language | PostgreSQL + Python + TypeScript + Ruby |

---

## Comparison with Other Tools

### Is SpecQL a transpiler like Haxe?

**Short answer**: SpecQL **includes transpiler functionality** but is much more than a transpiler.

**Long answer**: SpecQL has three distinct capabilities:

#### 1. Universal Transpiler (Layer 1)

Like Haxe, SpecQL can translate business logic across multiple languages:

```
SpecQL YAML → Universal AST → [PostgreSQL, Python, TypeScript, Ruby]
```

**Example**: Define a state machine once, generate implementations in 4+ languages.

#### 2. Pattern System (Layer 2)

Unlike transpilers, SpecQL includes a **pattern library** with:
- **35 primitive patterns** (validate, query, update, etc.)
- **15 domain patterns** (state machines, audit trails, approvals)
- **22 entity templates** (CRM Contact, E-Commerce Product, etc.)

#### 3. Framework Conventions (Layer 3)

SpecQL auto-generates infrastructure code:
- Trinity pattern (pk_*, id, identifier)
- Audit fields (created_at, updated_at, deleted_at)
- Indexes and foreign keys
- GraphQL metadata
- TypeScript types
- Tests and documentation

#### Visual Comparison

**Haxe (Transpiler Model)**:
```
Haxe Code → [Transpiler] → Target Language Code
(50 lines)                   (50 lines equivalent)

You write:  Classes + methods + validation + DB + API
You get:    Same code in different syntax
```

**SpecQL (Generation Platform)**:
```
YAML Spec → [SpecQL Platform] → Full Production System
(20 lines)                       (2,000+ lines)

You write:  Entity + fields + business rules
You get:    DB + API + Types + Tests + Docs
```

### What about reverse engineering?

SpecQL includes **bidirectional transpilation**:

```
PostgreSQL SQL → SpecQL AST → SpecQL YAML → Any Language
```

**Example workflow**:
```bash
# 1. Extract patterns from existing SQL
specql reverse legacy_function.sql --discover-patterns

# 2. Get SpecQL YAML representation
specql reverse legacy_function.sql

# 3. Compile to ANY target language
specql compile contact.yaml --target=python
specql compile contact.yaml --target=typescript
specql compile contact.yaml --target=ruby
```

This means you can:
- **Migrate** PostgreSQL → Django/Rails/Prisma
- **Extract patterns** from legacy SQL
- **Standardize** across technology stacks

### How is SpecQL different from code generators like Rails scaffolding?

| Feature | Rails Scaffolding | SpecQL |
|---------|------------------|--------|
| **Abstraction Level** | Code templates | Business domain specifications |
| **Customization** | Edit generated code | Extend via YAML |
| **Evolution** | Manual updates | Regenerate from spec |
| **Patterns** | Basic CRUD | 48 business patterns |
| **Multi-language** | Ruby only | 4+ languages |
| **Testing** | Manual | Auto-generated |

**Rails scaffolding**: One-time code generation (edit after)
**SpecQL**: Living specification (regenerate anytime)

### Can SpecQL replace my existing ORM?

SpecQL can **complement or replace** your ORM depending on use case:

**Complement** (hybrid approach):
- Use SpecQL for complex business logic
- Use ORM for simple CRUD operations
- Both can coexist in the same application

**Replace** (full SpecQL):
- Generate complete data layer from SpecQL
- Use generated types/hooks in your application
- ORM becomes unnecessary

**Best for replacement**:
- New projects
- Microservices
- Business-logic-heavy applications

**Complement if**:
- Existing large codebase
- Team unfamiliar with SpecQL
- Need ORM-specific features

---

## Technical Questions

### What languages does SpecQL support?

**Current** (v0.2.0):
- PostgreSQL (production-ready)
- GraphQL metadata (FraiseQL integration)
- TypeScript types (generated)

**Roadmap** (see [master plan](implementation_plans/00_master_plan/)):
- Python/Django (Month 3)
- TypeScript/Prisma (Month 3)
- Ruby/Rails (Q2 2025)
- Java/Spring (Q2 2025)

### Does SpecQL support multi-tenant applications?

Yes! SpecQL has **built-in multi-tenancy**:

```yaml
entity: Contact
schema: crm  # Multi-tenant schema
fields:
  email: text
  # tenant_id automatically added by framework
```

Framework automatically:
- Adds `tenant_id UUID NOT NULL` to all tables
- Creates RLS (Row-Level Security) policies
- Adds tenant_id to all indexes
- Handles tenant context in functions

### What's the "Trinity pattern"?

SpecQL automatically applies the **Trinity pattern** to all entities:

```sql
-- Every table gets three identifiers:
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,  -- Internal: fast joins
    id UUID UNIQUE NOT NULL,         -- External: stable public API
    identifier TEXT UNIQUE NOT NULL  -- Human: readable (e.g., "CONT-2024-001")
);
```

**Why three?**
- `pk_*`: Fast integer joins (internal)
- `id`: Stable UUID for APIs (external)
- `identifier`: Human-readable reference (UX)

Helper functions auto-generated:
```sql
SELECT contact_pk(uuid_value);        -- UUID → INTEGER
SELECT contact_id(integer_value);     -- INTEGER → UUID
SELECT contact_identifier(uuid_value); -- UUID → TEXT
```

### Can I customize the generated code?

**Yes, at multiple levels**:

#### 1. YAML Extensions
```yaml
entity: Contact
extends: crm.contact_template  # Base template
fields:
  custom_field: text            # Add custom fields
patterns:
  - audit_trail: {}             # Add patterns
```

#### 2. Pattern Composition
```yaml
patterns:
  - state_machine:
      states: [lead, qualified, customer]
  - audit_trail: {}
  - soft_delete: {}
```

#### 3. Custom Actions
```yaml
actions:
  - name: custom_qualification_logic
    steps:
      - validate: custom_rule
      - call: external_api()
      - update: Contact
```

#### 4. Framework Configuration
```yaml
# .specql.yaml
framework: fraiseql
conventions:
  trinity: true
  audit_fields: true
  table_prefix: "tb_"
```

**Note**: Don't edit generated SQL directly - extend via YAML to preserve regeneration capability.

### What databases does SpecQL support?

**Current**:
- PostgreSQL 12+ (production-ready)

**Roadmap**:
- MySQL/MariaDB (via pattern library)
- SQLite (via pattern library)
- MongoDB (Q3 2025)

PostgreSQL is the primary target due to:
- Advanced features (composite types, CTEs, window functions)
- FraiseQL GraphQL integration
- PL/pgSQL for business logic
- JSONB for flexibility

### How does SpecQL handle migrations?

SpecQL generates **migration-ready SQL**:

**Production mode** (hierarchical):
```bash
specql generate entities/**/*.yaml

# Output:
migrations/
├── 000_app_foundation.sql
└── 01_write_side/
    └── 011_crm/
        └── 011001_contact/
            └── 011001_tb_contact.sql
```

**Development mode** (flat):
```bash
specql generate entities/**/*.yaml --dev

# Output:
db/schema/
├── 10_tables/contact.sql
└── 20_helpers/contact_helpers.sql
```

Apply with migration tools:
```bash
# Flyway
flyway migrate

# Alembic (Python)
alembic upgrade head

# Rails
rails db:migrate

# Custom
psql $DATABASE_URL -f migrations/*.sql
```

**Schema changes**: Regenerate from YAML, framework handles ALTER TABLE statements.

---

## Usage Questions

### When should I use SpecQL vs write SQL directly?

**Use SpecQL when**:
- Building business-logic-heavy applications
- Need consistency across entities
- Want automatic testing
- Planning multi-language support
- Rapid prototyping (MVP in days)

**Write SQL directly when**:
- One-off analytics queries
- Complex data transformations
- Database-specific optimizations
- Learning SQL fundamentals

**Hybrid approach**: Use SpecQL for business logic, raw SQL for reporting.

### Can I mix SpecQL with hand-written SQL?

**Yes!** SpecQL plays well with custom SQL:

```yaml
actions:
  - name: complex_report
    steps:
      # Call your custom SQL function
      - call: custom_analytics_function($input)
      - return: result
```

SpecQL-generated code is standard SQL - you can:
- Reference generated tables in custom queries
- Call generated functions from custom code
- Extend with custom triggers/views
- Mix in ORMs (Django, Rails, Prisma)

### How do I test SpecQL-generated code?

SpecQL **auto-generates tests**:

```bash
# Generate tests with schema
specql generate entities/**/*.yaml --with-tests

# Output includes:
tests/
├── pgtap/          # PostgreSQL native tests
│   └── test_contact.sql
├── pytest/         # Python integration tests
│   └── test_contact.py
└── fixtures/       # Test data
    └── contact_fixtures.sql
```

**Run tests**:
```bash
# PostgreSQL (pgTAP)
make test-pgtap

# Python (pytest)
make test-pytest

# All tests
make test
```

**Test coverage**:
- Schema validation
- Business logic functions
- Constraint enforcement
- Edge cases
- Performance benchmarks

### How do I deploy SpecQL applications?

SpecQL generates **standard SQL and code** - deploy like any application:

#### 1. Generate Production Assets
```bash
specql generate entities/**/*.yaml --output=migrations/
```

#### 2. Apply Migrations
```bash
# Choose your tool:
flyway migrate              # Java
alembic upgrade head        # Python
rails db:migrate            # Ruby
prisma migrate deploy       # TypeScript
```

#### 3. Deploy Application
Standard deployment for your stack:
- Django: `gunicorn myapp.wsgi`
- Rails: `puma -C config/puma.rb`
- Node.js: `node dist/server.js`

#### 4. Infrastructure
Works with:
- Docker/Kubernetes
- AWS RDS + ECS/Lambda
- Google Cloud SQL + Cloud Run
- Heroku/Render/Railway

**Production considerations**:
- SpecQL generates optimized SQL (indexes, constraints)
- Tests validate correctness
- Monitoring: Standard PostgreSQL metrics
- Backup: Standard PostgreSQL tools (pg_dump, WAL archiving)

---

## Advanced Topics

### What's the pattern library?

The **pattern library** is SpecQL's intelligence layer:

**Features**:
- **Pattern Discovery**: Extract patterns from legacy SQL
- **Semantic Search**: Find patterns by description (pgvector)
- **LLM Generation**: Create patterns from natural language (Grok)
- **Human Review**: Approve/reject pattern suggestions

**Example workflow**:
```bash
# 1. Discover patterns in legacy code
specql reverse complex_function.sql --discover-patterns

# 2. Review suggestions
specql patterns review-suggestions

# 3. Approve pattern
specql patterns approve 1

# 4. Use pattern in new entities
```yaml
entity: Order
patterns:
  - approval_workflow:  # Pattern discovered from legacy code
      stages: [pending, approved, rejected]
```

See [Pattern Library User Guide](pattern_library/USER_GUIDE.md) for details.

### Can SpecQL generate frontend code?

**Yes**, SpecQL generates frontend-ready artifacts:

**TypeScript Types** (generated):
```typescript
interface Contact {
  id: string;
  email: string;
  status: 'lead' | 'qualified' | 'customer';
}

type QualifyLeadInput = {
  contactId: string;
};
```

**GraphQL Operations** (generated):
```typescript
import { useQualifyLeadMutation } from './generated/graphql';

const { mutate } = useQualifyLeadMutation();
await mutate({ contactId: '...' });
```

**Apollo Hooks** (generated):
```typescript
const { data, loading, error } = useContactQuery({
  variables: { id: contactId }
});
```

**Roadmap** (Q2 2025):
- React component generation
- Vue.js component generation
- Form validation hooks
- Optimistic updates

### How does SpecQL handle performance?

SpecQL generates **optimized SQL**:

**Automatic optimizations**:
- Indexes on foreign keys
- Indexes on enum fields
- Indexes on tenant_id
- Composite indexes for common queries
- HNSW indexes for vector search (pattern library)

**Example**:
```yaml
entity: Contact
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)
```

**Generates**:
```sql
CREATE INDEX idx_tb_contact_fk_company ON tb_contact(fk_company);
CREATE INDEX idx_tb_contact_status ON tb_contact(status);
-- Composite for common queries:
CREATE INDEX idx_tb_contact_status_company ON tb_contact(status, fk_company);
```

**Performance features**:
- Batch operations for bulk inserts
- CTEs for complex queries
- Materialized views for aggregations
- Query plan analysis in tests

### Can I use SpecQL with existing databases?

**Yes**, via **reverse engineering**:

```bash
# 1. Extract SpecQL YAML from existing SQL
specql reverse existing_schema.sql

# Output: entities/contact.yaml

# 2. Modify YAML as needed
# 3. Regenerate with improvements
specql generate entities/contact.yaml

# 4. Compare changes
specql diff entities/contact.yaml --compare existing_schema.sql
```

**Migration strategy**:
1. **Phase 1**: Extract existing schema to YAML
2. **Phase 2**: Add patterns and conventions
3. **Phase 3**: Regenerate improved schema
4. **Phase 4**: Test and deploy gradually

**Supports**:
- PostgreSQL DDL
- Python/Django models (planned)
- Java/Spring JPA entities (in progress)
- TypeScript/Prisma (planned)

---

## Community & Support

### Where can I get help?

- **Documentation**: [docs/](./docs/)
- **Examples**: [examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/fraiseql/specql/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fraiseql/specql/discussions)
- **Email**: lionel.hamayon@evolution-digitale.fr

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code contributions
- Pattern submissions
- Documentation improvements
- Bug reports

**Popular contributions**:
- New domain patterns
- Entity templates
- Language targets
- Test cases

### What's the roadmap?

See [Master Plan](implementation_plans/00_master_plan/20251112_THREE_MONTH_MASTER_PLAN.md) for detailed roadmap:

**Month 1-3** (Current):
- Hierarchical file generation ✅
- Pattern library (in progress)
- Multi-language foundation

**Q2 2025**:
- Python/Django generation
- TypeScript/Prisma generation
- Ruby/Rails generation
- 50+ business patterns

**Q3 2025**:
- Frontend component generation
- Cloud deployment automation
- Monitoring and observability
- Enterprise features

**Q4 2025**:
- SaaS offering
- Team collaboration
- CI/CD integration
- Marketplace for patterns

### Is SpecQL production-ready?

**Current status** (v0.2.0):
- **Core Features**: ✅ Production-ready
  - Schema generation
  - Business logic compilation
  - GraphQL integration
  - Test generation

- **Stability**: Beta
  - API may evolve
  - 1,185 tests passing
  - >95% code coverage

- **Best for**:
  - New projects
  - Microservices
  - MVP/prototypes
  - Evaluation

- **Use with caution**:
  - Mission-critical systems (test thoroughly)
  - Large teams (API changes may occur)
  - Complex legacy migrations

**v1.0 target**: Q3 2025

---

## Comparison Summary

| Tool | SpecQL | Haxe | Rails | Django ORM | Prisma |
|------|--------|------|-------|-----------|--------|
| **Type** | Business Logic Compiler | Transpiler | Framework | ORM | ORM/Schema Tool |
| **Input** | YAML specs | Haxe code | Ruby code | Python classes | Prisma schema |
| **Output** | Full stack | Multi-lang code | Rails app | DB queries | TS types + client |
| **Abstraction** | Very High | Medium | High | Medium | Medium |
| **Multi-language** | ✅ 4+ | ✅ 9+ | ❌ Ruby only | ❌ Python only | ❌ JS/TS only |
| **Patterns** | ✅ 48 built-in | ❌ Manual | ⚠️ Basic | ❌ Manual | ❌ Manual |
| **Reverse Eng** | ✅ Yes | ❌ No | ⚠️ Limited | ⚠️ Limited | ⚠️ introspection |
| **Testing** | ✅ Auto-generated | ❌ Manual | ⚠️ Framework | ❌ Manual | ❌ Manual |
| **Conventions** | ✅ Built-in | ❌ None | ✅ Strong | ⚠️ Some | ⚠️ Some |
| **GraphQL** | ✅ Native | ❌ No | ⚠️ Gem | ⚠️ Library | ✅ Yes |
| **Use Case** | Business apps | Cross-platform | Web apps | Web apps | Modern web |

**Key Insight**: SpecQL = Transpiler + Framework + Pattern System + Reverse Engineering

---

## Quick Decision Guide

### Choose SpecQL if you want:
- 🚀 100x leverage (20 lines → 2,000 lines)
- 🎯 Business logic focus (not infrastructure code)
- 🔄 Multi-language support
- 📦 Reusable patterns
- 🧪 Auto-generated tests
- 📝 Living documentation
- 🔀 Legacy migration paths

### Use something else if you need:
- Full control over every line of code → Write SQL/ORM code directly
- NoSQL database → SpecQL is PostgreSQL-focused (for now)
- Simple CRUD only → Standard ORM may be simpler
- Existing large codebase → Gradual adoption may be complex

### Best combo (hybrid):
- SpecQL for **business logic** (complex workflows)
- ORM for **simple CRUD** (quick queries)
- Raw SQL for **analytics** (complex reports)

---

**Still have questions?** [Open an issue](https://github.com/fraiseql/specql/issues) or [start a discussion](https://github.com/fraiseql/specql/discussions)!
