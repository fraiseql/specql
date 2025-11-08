# Claude Code Instructions - SpecQL → PostgreSQL → GraphQL Generator

**Project**: Lightweight Business DSL → Production Database + Auto-GraphQL API
**Status**: 🚧 Active Development - Parallel Team Execution
**Context Window Optimization**: This file provides instant project context for AI assistants

---

## 🎯 Project Vision

**Transform 20 lines of business-focused YAML into production-ready PostgreSQL + GraphQL API.**

### Core Principle: **Business Domain ONLY in YAML**

Users write **ONLY** business logic. Framework handles ALL technical details automatically.

**Example Input** (20 lines):
```yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)          # Framework auto-creates FK
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

**Auto-Generated Output** (2000+ lines):
- ✅ PostgreSQL table with Trinity pattern (pk_*, id, identifier)
- ✅ Auto-generated foreign keys and indexes
- ✅ PL/pgSQL function for `qualify_lead` action
- ✅ FraiseQL metadata comments for GraphQL
- ✅ Complete GraphQL API (queries, mutations, types)

**Result**: **100x code leverage** - Business logic in YAML, framework handles implementation.

---

## 🏗️ Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  LIGHTWEIGHT SpecQL (Business Only - 20 lines)              │
│  - Entities & relationships                                  │
│  - Business actions & validations                            │
│  - NO infrastructure details                                 │
└──────────────────┬───────────────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │  TEAM A: SpecQL Parser      │
    │  Parse DSL → Business AST   │
    └──────────────┬──────────────┘
                   │
                   ▼
    ┌────────────────────────────────────┐
    │   Business Entity AST               │
    │   (No infrastructure details)       │
    └──────────────┬─────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ TEAM B  │  │ TEAM C  │  │  TEAM D      │
│ Schema  │  │ Action  │  │  FraiseQL    │
│ Gen     │  │ Compiler│  │  Metadata    │
└────┬────┘  └────┬────┘  └──────┬───────┘
     │            │               │
     └────────────┼───────────────┘
                  │
                  ▼
    ┌──────────────────────────┐
    │  TEAM E: Orchestrator    │
    │  Combine → Migration SQL │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  PostgreSQL Database             │
    │  - Tables (Trinity pattern)      │
    │  - Functions (business actions)  │
    │  - FraiseQL metadata comments    │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  FraiseQL Auto-Discovery         │
    │  (External tool - introspects)   │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  GraphQL API (Auto-Generated)    │
    │  - Types, Queries, Mutations     │
    └──────────────────────────────────┘
```

---

## 👥 TEAM STRUCTURE (5 Teams, Clear Separation of Concerns)

### 🔵 Team A: SpecQL Parser (Business DSL)
**Mission**: Parse lightweight business YAML → Business AST (NO infrastructure details)

**Parses**:
- ✅ Entity name, schema, description
- ✅ Fields: name, type (text, integer, ref, enum, list)
- ✅ Actions: name, steps (validate, if/then, insert, update, call, notify)
- ✅ Business validation rules
- ✅ AI agent definitions

**Does NOT Parse** (Framework handles):
- ❌ Trinity pattern syntax (pk_*, id, identifier) - Auto-generated by Team B
- ❌ Foreign key syntax (fk_*, REFERENCES) - Inferred from ref(Entity)
- ❌ Index definitions - Auto-generated by Team B
- ❌ Constraint details - Inferred from types
- ❌ GraphQL metadata - Generated by Team D

**Status**: ✅ **90% Complete** (Current implementation is correct!)
**Location**: `src/core/`
**Test Command**: `make teamA-test`

---

### 🟢 Team B: Schema Generator (Convention-Based DDL)
**Mission**: Business AST → PostgreSQL DDL with **automatic framework conventions**

**Input**: Business Entity AST (from Team A)

**Applies Conventions** (Automatically):
1. **Trinity Pattern**: Every table gets `pk_*`, `id`, `identifier`
2. **Naming**: `tb_{entity}` tables, `fk_{entity}` foreign keys
3. **Audit Fields**: `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`
4. **Auto-Indexes**: FK columns, enum fields, common query patterns
5. **Constraints**: NOT NULL inference, CHECK for enums, UNIQUE where appropriate

**Example Transformation**:
```yaml
# Input (SpecQL)
fields:
  company: ref(Company)
  status: enum(lead, qualified)
```

```sql
-- Output (Auto-generated DDL)
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern (AUTO)
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,

    -- Business fields + AUTO conventions
    fk_company INTEGER REFERENCES management.tb_company(pk_company),  -- AUTO FK
    status TEXT CHECK (status IN ('lead', 'qualified')),              -- AUTO CHECK

    -- Audit fields (AUTO)
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-generated indexes
CREATE INDEX idx_contact_company ON crm.tb_contact(fk_company);
CREATE INDEX idx_contact_status ON crm.tb_contact(status);
```

**Status**: 🔴 Not Started (Week 2 focus)
**Location**: `src/generators/schema/`
**Test Command**: `make teamB-test`

---

### 🟠 Team C: Action Compiler (Business Logic → PL/pgSQL)
**Mission**: SpecQL action steps → PostgreSQL functions with framework conventions

**Input**: Action definitions from AST

**Generates**: PL/pgSQL functions with:
1. **Standard Signature**: UUID inputs, jsonb output
2. **Trinity Resolution**: Auto-convert UUID → INTEGER for queries
3. **Audit Updates**: Auto-update `updated_at`, `updated_by`
4. **Event Emission**: Auto-emit events on state changes
5. **Error Handling**: Standard exception patterns

**Example Transformation**:
```yaml
# Input (SpecQL)
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

```sql
-- Output (Auto-generated Function)
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
    v_status TEXT;
BEGIN
    -- Trinity resolution (AUTO)
    v_pk := crm.contact_pk(p_contact_id);

    -- Validation (from SpecQL)
    SELECT status INTO v_status FROM crm.tb_contact WHERE pk_contact = v_pk;
    IF v_status != 'lead' THEN
        RAISE EXCEPTION 'validation_failed';
    END IF;

    -- Update (from SpecQL + AUTO audit)
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk;

    -- Event emission (AUTO)
    PERFORM core.emit_event('contact.qualified', jsonb_build_object('id', p_contact_id));

    -- Return (AUTO format)
    RETURN jsonb_build_object('success', true, 'contact_id', p_contact_id);
END;
$$ LANGUAGE plpgsql;
```

**Status**: 🔴 Not Started (Week 3 focus)
**Location**: `src/generators/actions/`
**Test Command**: `make teamC-test`

---

### 🟣 Team D: FraiseQL Metadata Generator
**Mission**: Generate `@fraiseql:*` COMMENT annotations for GraphQL auto-discovery

**Input**: Entity AST + Generated SQL (from Teams B & C)

**Output**: SQL COMMENT statements
```sql
-- Table metadata
COMMENT ON TABLE crm.tb_contact IS
  '@fraiseql:type name=Contact,schema=crm';

-- Field metadata
COMMENT ON COLUMN crm.tb_contact.email IS
  '@fraiseql:field name=email,type=String!';
COMMENT ON COLUMN crm.tb_contact.fk_company IS
  '@fraiseql:field name=company,type=Company,relation=many-to-one';
COMMENT ON COLUMN crm.tb_contact.status IS
  '@fraiseql:field name=status,type=ContactStatus,enum=true';

-- Mutation metadata
COMMENT ON FUNCTION crm.qualify_lead IS
  '@fraiseql:mutation name=qualifyLead,input=QualifyLeadInput,output=Contact';
```

**FraiseQL Then**:
- Introspects these comments
- Auto-generates GraphQL schema
- Maps functions → mutations
- Creates types, queries, filters

**Status**: 🔴 Not Started (Week 5 focus)
**Location**: `src/generators/fraiseql/`
**Test Command**: `make teamD-test`

---

### 🔴 Team E: CLI & Orchestration
**Mission**: Developer tools + pipeline orchestration

**CLI Commands**:
```bash
# Generate complete migration from SpecQL
specql generate entities/contact.yaml
# Output: migrations/001_contact.sql (schema + functions + metadata)

# Validate SpecQL syntax
specql validate entities/*.yaml

# Show what would change
specql diff entities/contact.yaml
```

**Orchestration**: Coordinates Teams B + C + D:
```python
def generate(yaml_file):
    # Team A: Parse
    entity = SpecQLParser().parse(yaml_file)

    # Team B: Generate schema
    schema_sql = SchemaGenerator().generate(entity)

    # Team C: Compile actions
    action_sql = ActionCompiler().compile(entity.actions)

    # Team D: Add FraiseQL metadata
    metadata_sql = FraiseQLAnnotator().annotate(entity)

    # Combine into migration
    migration = combine(schema_sql, action_sql, metadata_sql)
    write_migration(migration)
```

**Status**: 🔴 Not Started (Week 7 focus)
**Location**: `src/cli/`
**Test Command**: `make teamE-test`

---

## 📊 TEAM PROGRESS DASHBOARD

### Overall Project: 10% Complete (Week 1 of 10)

| Team | Focus | Week 1 Goal | Progress | Status |
|------|-------|-------------|----------|--------|
| **Team A** | SpecQL Parser | Parse lightweight DSL | **90%** | ✅ ON TRACK |
| **Team B** | Schema Gen | Not started yet | **0%** | ⏸️ WAITING |
| **Team C** | Action Compiler | Not started yet | **0%** | ⏸️ WAITING |
| **Team D** | FraiseQL Meta | Not started yet | **0%** | ⏸️ WAITING |
| **Team E** | CLI Tools | Not started yet | **0%** | ⏸️ WAITING |

### Week-by-Week Plan

**Week 1** (Current): Team A - SpecQL Parser
- ✅ Parse entity definitions (DONE)
- ✅ Parse field types (DONE)
- ✅ Parse actions and steps (DONE)
- 🚧 Minor refinements (in progress)

**Week 2**: Team B - Schema Generator
- Convention-based DDL generation
- Trinity pattern application
- Auto FK and index generation

**Week 3**: Team C - Action Compiler
- Basic step compilation (validate, insert, update)
- Conditional logic (if/then/else)
- Function scaffolding

**Week 4**: Integration Testing
- End-to-end: SpecQL → SQL → Database
- Performance testing
- Bug fixes

**Week 5-6**: Team D - FraiseQL Integration
- Metadata annotation generation
- GraphQL schema validation
- End-to-end with FraiseQL

**Week 7-8**: Team E - CLI & Developer Experience
- Command-line tools
- Migration management
- Documentation

**Week 9-10**: Production Readiness
- Advanced features
- Security hardening
- Performance optimization

---

## 🎯 CRITICAL: What Makes SpecQL "Lightweight"

### Users Write (Business Domain)
```yaml
entity: Contact
fields:
  email: text
  company: ref(Company)  # Just say "ref" - framework figures out FK
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Total: 12 lines**

### Framework Auto-Generates (Technical Implementation)
- ✅ Trinity pattern (pk_contact, id, identifier)
- ✅ Foreign key: `fk_company INTEGER REFERENCES tb_company(pk_company)`
- ✅ Enum constraint: `CHECK (status IN ('lead', 'qualified'))`
- ✅ Indexes on fk_company, status, email
- ✅ Audit fields (created_at, updated_at, etc.)
- ✅ Helper functions (contact_pk, contact_id, contact_identifier)
- ✅ PL/pgSQL function for qualify_lead with:
  - Trinity resolution
  - Validation logic
  - Audit updates
  - Event emission
  - Error handling
- ✅ FraiseQL comments for GraphQL auto-discovery
- ✅ GraphQL types, queries, mutations

**Total: 2000+ lines auto-generated**

### What Users DON'T Write
- ❌ No SQL DDL syntax
- ❌ No foreign key syntax
- ❌ No index definitions
- ❌ No constraint syntax
- ❌ No PL/pgSQL code
- ❌ No GraphQL schema
- ❌ No resolver functions
- ❌ No type definitions

**Result**: 99% less code, 100% production-ready

---

## 📁 Repository Structure

```
src/
├── core/              # Team A: SpecQL Parser
│   ├── ast_models.py       # ✅ Business Entity AST
│   ├── specql_parser.py    # ✅ YAML → AST parser
│   └── README.md
│
├── generators/
│   ├── schema/        # Team B: Schema Generator
│   │   ├── schema_generator.py
│   │   ├── trinity_pattern.py
│   │   ├── naming_conventions.py
│   │   └── index_strategy.py
│   │
│   ├── actions/       # Team C: Action Compiler
│   │   ├── action_compiler.py
│   │   ├── expression_to_sql.py
│   │   └── step_generators/
│   │
│   └── fraiseql/      # Team D: FraiseQL Metadata
│       ├── annotator.py
│       ├── graphql_mapper.py
│       └── metadata_gen.py
│
├── cli/               # Team E: CLI & Orchestration
│   ├── generate.py
│   ├── validate.py
│   └── orchestrator.py
│
└── templates/
    ├── sql/           # DDL templates
    └── plpgsql/       # Function templates

tests/
├── unit/
│   ├── core/          # Team A tests ✅
│   ├── schema/        # Team B tests
│   ├── actions/       # Team C tests
│   ├── fraiseql/      # Team D tests
│   └── cli/           # Team E tests
│
└── integration/       # End-to-end tests

entities/
└── examples/
    ├── contact.yaml   # Simple example
    └── machine_item.yaml  # Complex example
```

---

## 🧪 Testing Strategy

### TDD Discipline (Mandatory)

Every feature follows: **RED → GREEN → REFACTOR → QA**

```bash
# RED: Write failing test
vim tests/unit/schema/test_schema_generator.py
uv run pytest tests/unit/schema/ -v  # Should fail

# GREEN: Minimal implementation
vim src/generators/schema/schema_generator.py
uv run pytest tests/unit/schema/ -v  # Should pass

# REFACTOR: Clean up
vim src/generators/schema/schema_generator.py
uv run pytest tests/unit/schema/ -v  # Still pass

# QA: Quality checks
make lint && make typecheck && make test
```

### Team-Specific Test Commands

```bash
make teamA-test  # Core parser tests
make teamB-test  # Schema generator tests
make teamC-test  # Action compiler tests
make teamD-test  # FraiseQL metadata tests
make teamE-test  # CLI tests

make test        # All tests
make integration # Integration tests
make coverage    # Coverage report (target: 90%+)
```

---

## 🚀 Getting Started (For AI Assistants)

### When Asked About Progress
1. Check **TEAM PROGRESS DASHBOARD** above
2. Report current week and focus
3. Identify what's blocking next steps

### When Asked to Help a Specific Team
1. Read team's section above for mission and focus
2. Check `src/{team}/README.md` for detailed specs
3. Follow **TDD cycle**: RED → GREEN → REFACTOR → QA
4. Use templates from `templates/` directory

### When Suggesting Work
1. **Prioritize current week's focus** (Week 1 = Team A only)
2. **Follow sequential team dependencies**:
   - Team A must finish before B/C/D start
   - Teams B/C/D can work in parallel (Week 2-6)
   - Team E orchestrates in Week 7+
3. **One team-specific task at a time**
4. **Test-first always** (write test before implementation)

---

## 💡 Example: Complete SpecQL → GraphQL Flow

### Step 1: User Writes SpecQL (20 lines)
```yaml
# entities/contact.yaml
entity: Contact
schema: crm

fields:
  email: text
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

### Step 2: Run Generator
```bash
specql generate entities/contact.yaml

# Output:
# ✓ Parsing SpecQL...
# ✓ Generating schema (Team B)...
#   - tb_contact table (Trinity pattern)
#   - 3 auto-indexes
#   - 4 helper functions
# ✓ Compiling actions (Team C)...
#   - qualify_lead() function
# ✓ Adding FraiseQL metadata (Team D)...
#   - 8 COMMENT annotations
# ✓ Writing: migrations/001_contact.sql (1,847 lines)
# ✓ Complete!
```

### Step 3: Apply to Database
```bash
psql < migrations/001_contact.sql
# Contact table created with Trinity pattern
# Functions created
# FraiseQL metadata attached
```

### Step 4: FraiseQL Auto-Discovery
```bash
# FraiseQL introspects database
# Finds @fraiseql:* comments
# Auto-generates GraphQL schema
```

### Step 5: GraphQL API Ready!
```graphql
# Auto-generated types
type Contact {
  id: UUID!
  email: String!
  company: Company
  status: ContactStatus!
}

# Auto-generated queries
query {
  contact(id: "...") { email, company { name } }
  contacts(filter: {status: LEAD}) { id, email }
}

# Auto-generated mutations (from qualify_lead function)
mutation {
  qualifyLead(contactId: "...") {
    success
    contact { id, status }
  }
}
```

**Total User Code**: 20 lines YAML
**Total Generated Code**: 2000+ lines (SQL + GraphQL)
**Code Leverage**: **100x**

---

## 🎯 Key Principles for AI Assistants

### 1. **Lightweight SpecQL Above All**
- If implementation requires users to write SQL/DDL → ❌ Wrong
- If implementation requires users to write GraphQL → ❌ Wrong
- Users write ONLY business domain → ✅ Correct

### 2. **Convention Over Configuration**
- Trinity pattern is ALWAYS applied → Not configurable
- Naming conventions are ALWAYS applied → Not configurable
- Audit fields are ALWAYS added → Not configurable
- Users specify business logic, framework handles the rest

### 3. **Test-Driven Development is Mandatory**
- Every feature starts with a failing test
- No implementation without tests
- 90%+ coverage target

### 4. **Clear Team Boundaries**
- Team A: Parse business DSL (NO infrastructure details)
- Team B: Apply DDL conventions (Trinity, indexes, constraints)
- Team C: Compile business actions to PL/pgSQL
- Team D: Add FraiseQL metadata
- Team E: Orchestrate everything

### 5. **Sequential Team Dependencies**
- Week 1: Team A only (parse SpecQL)
- Week 2+: Teams B/C/D (need Team A's AST)
- Week 7+: Team E (needs B/C/D output)

---

## 📚 Essential Documentation

### For Team A (SpecQL Parser)
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Lightweight DSL spec
- `src/core/README.md` - Parser implementation guide

### For Team B (Schema Generator)
- `docs/analysis/POC_RESULTS.md` - Trinity pattern examples
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Conventions to apply

### For Team C (Action Compiler)
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Action step syntax
- Examples in `entities/examples/`

### For Team D (FraiseQL)
- `docs/analysis/FRAISEQL_INTEGRATION_REQUIREMENTS.md` - Metadata format
- FraiseQL documentation (external)

### For Team E (CLI)
- `CONTRIBUTING.md` - CLI workflow
- `docs/guides/` - User-facing docs (to be written)

---

## 🚨 Common Mistakes to Avoid

### ❌ Don't Parse Infrastructure Details in Team A
```yaml
# ❌ BAD - Don't parse this in SpecQL
foreign_keys:
  fk_company:
    references: tb_company
    on: pk_company
```
**Why**: Team B infers FKs from `ref(Company)` automatically

### ❌ Don't Make Users Write SQL Syntax
```yaml
# ❌ BAD - Don't require SQL syntax
fields:
  status: "TEXT CHECK (status IN ('lead', 'qualified'))"
```
```yaml
# ✅ GOOD - Simple business domain
fields:
  status: enum(lead, qualified)
```

### ❌ Don't Make Trinity Pattern Configurable
```yaml
# ❌ BAD - Don't let users configure Trinity
trinity_pattern:
  pk_field: custom_pk  # NO!
  id_field: custom_id  # NO!
```
**Why**: Consistency across all tables is critical

### ❌ Don't Skip Tests
```python
# ❌ BAD - Writing code without tests first
def generate_schema(entity):
    # Implementation without test
```

```python
# ✅ GOOD - Test-first development
def test_generate_schema_with_trinity_pattern():
    entity = Entity(name='Contact', ...)
    sql = SchemaGenerator().generate(entity)
    assert 'pk_contact' in sql
    assert 'id UUID' in sql
```

---

## 📞 Questions for AI to Ask

When uncertain, AI should ask:

### About Requirements
- "Does this feature belong in SpecQL (business), or is it a framework convention?"
- "Should this be auto-generated, or user-specified?"
- "Is this simplifying the user's YAML, or making it more complex?"

### About Implementation
- "Which team owns this functionality?"
- "Does Team A's AST support this, or do we need to extend it?"
- "Can we infer this from existing data, or must user specify?"

### About Testing
- "What's the failing test for this feature?"
- "Have we covered edge cases in tests?"
- "Does this maintain 90%+ coverage?"

---

**Last Updated**: 2025-11-08 (Post-Architecture Revision)
**Project Phase**: Week 1 - Team A (SpecQL Parser)
**Overall Progress**: 10% (1 of 10 weeks)
**Next Milestone**: Week 2 - Team B starts Schema Generation

---

## 🤖 AI Quick Reference Card

**Project Goal**: 20 lines YAML → 2000 lines production code (100x leverage)

**Current Focus**: Week 1 - Team A - SpecQL Parser (90% done)

**Key Principle**: Users write business domain ONLY, framework handles ALL technical details

**Critical Path**: Team A → Teams B/C/D → Team E → FraiseQL

**Test Command**: `make test`

**When in Doubt**: Keep SpecQL lightweight, move complexity to framework
