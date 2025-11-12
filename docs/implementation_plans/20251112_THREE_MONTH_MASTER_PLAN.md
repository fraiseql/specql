# SpecQL 3-Month Master Plan: Universal Generation Platform

**Date**: 2025-11-12
**Timeline**: Week 1 → Week 12 (3 months)
**Team Size**: 1-2 developers
**Objective**: Transform SpecQL from PostgreSQL generator to universal architectural code generation platform

---

## 🎯 **Executive Summary**

### **Vision**
Build a **universal code generation platform** where:
1. Business logic is written ONCE in SpecQL YAML
2. Architectural patterns are declared, not coded
3. Code generates for ANY language/framework
4. System architectures generate from templates

### **Timeline Overview**

| Month | Focus | Deliverable |
|-------|-------|------------|
| **Month 1** | Complete hierarchical generation | Production-ready file organization |
| **Month 2** | Pattern library + SQL expansion | 35 primitives + 10 domain patterns |
| **Month 3** | Multi-language + architecture | Python/TypeScript + system templates |

### **Success Metrics**

| Metric | Current | Month 1 | Month 2 | Month 3 |
|--------|---------|---------|---------|---------|
| SQL Coverage | 21% | 30% | 60% | 95% |
| Patterns | 0 | 0 | 35 primitives | 45 + domain |
| Languages | 1 (PgSQL) | 1 | 1 | 3 (Pg, Py, TS) |
| Test Coverage | ~85% | 90% | 92% | 95% |
| Codebase Size | 193 files | 210 files | 260 files | 320 files |

---

## 📊 **Current State Assessment**

### **What We Have** ✅
- **193 source files**, **233 test files**
- Production-ready core (Teams A-E)
- Write-side hierarchical generation (100%)
- Read-side foundation (60%):
  - Code parsing ✅
  - Path generation ✅
  - Registry integration ✅
  - File object generation ✅
  - File writing ❌ (missing)

### **Technical Debt**
- Mock codes in TableViewFileGenerator
- Hardcoded domain/subdomain mappings
- No integration tests for hierarchical generation
- CLI missing `--hierarchical` flag

### **Dependencies**
- Existing: `uv` (package manager), `pytest`, `click`, `jinja2`, `pyyaml`
- New (Month 2): `sqlite3` (stdlib), `jsonschema`
- New (Month 3): `black`, `ruff`, `mypy` for multi-language output

---

## 🗓️ **MONTH 1: Complete Hierarchical Generation**

**Goal**: Production-ready hierarchical file structure for both write-side and read-side

**Theme**: "Foundation Completion"

---

### **WEEK 1: Unified File Writer** (Nov 12-18)

#### **Sprint Goals**
- Create reusable file writer for both write/read sides
- Replace mock codes with registry integration
- 100% test coverage for file writing

#### **Monday-Tuesday: Core Infrastructure**

**Task 1.1: HierarchicalFileWriter (Day 1)**
```python
# src/generators/schema/hierarchical_file_writer.py
- FileSpec dataclass (code, name, content, layer)
- PathGenerator protocol
- HierarchicalFileWriter class
- write_files() method
- write_single_file() method

Lines: ~150
Tests: 8 tests
Time: 6 hours
```

**Deliverables**:
- [ ] `hierarchical_file_writer.py` implemented
- [ ] Protocol-based design for flexibility
- [ ] Tests: write_tv_files, write_table_files, dry_run, error_handling

**Task 1.2: Path Generator Wrappers (Day 2)**
```python
# src/generators/schema/write_side_path_generator.py
- Wrapper around naming_conventions.generate_file_path()
- Implements PathGenerator protocol

# Update: read_side_path_generator.py
- Ensure implements PathGenerator protocol

Lines: ~80
Tests: 4 tests
Time: 4 hours
```

**Deliverables**:
- [ ] Write-side wrapper implements protocol
- [ ] Read-side implements protocol
- [ ] Both tested with HierarchicalFileWriter

#### **Wednesday: Registry Integration**

**Task 1.3: Remove Mock Codes (Day 3)**
```python
# src/generators/schema/table_view_file_generator.py
- Remove _MOCK_CODES dictionary
- Integrate with DomainRegistry.assign_read_entity_code()
- Add subdomain detection logic

Lines: ~50 (modifications)
Tests: Update 7 existing tests
Time: 6 hours
```

**Challenges**:
- Need subdomain information in EntityDefinition
- Decision: Add optional `subdomain` field to YAML

```yaml
entity: Contact
schema: crm
subdomain: customer  # NEW (optional, inferred from domain if not provided)
fields:
  email: text
```

**Deliverables**:
- [ ] Mock codes removed
- [ ] Real registry codes used
- [ ] Tests pass with dynamic codes

#### **Thursday: TableViewFileGenerator Integration**

**Task 1.4: Add write_files_to_disk() (Day 4)**
```python
# src/generators/schema/table_view_file_generator.py
- Add write_files_to_disk() method
- Integrate HierarchicalFileWriter
- Add dry_run support

Lines: ~40
Tests: 3 new tests
Time: 4 hours
```

**Deliverables**:
- [ ] write_files_to_disk() implemented
- [ ] Tests verify actual file creation
- [ ] Dry-run mode works

#### **Friday: Week 1 Wrap-up**

**Task 1.5: Documentation & Code Review (Day 5)**
- Update CLAUDE.md with hierarchical generation
- Document FileSpec and PathGenerator protocols
- Code review and refactoring
- Run full test suite

**Deliverables**:
- [ ] Documentation complete
- [ ] All tests passing
- [ ] Code reviewed

**Week 1 Metrics**:
- New files: 2 (hierarchical_file_writer, write_side_path_generator)
- Modified files: 2 (table_view_file_generator, read_side_path_generator)
- Tests added: 15
- Test coverage: 90%

---

### **WEEK 2: CLI Integration** (Nov 19-25)

#### **Sprint Goals**
- Add `--hierarchical` flag to CLI
- Wire up unified file writer
- Integration tests for full workflow

#### **Monday-Tuesday: CLI Orchestrator Updates**

**Task 2.1: Update CLIOrchestrator (Day 1-2)**
```python
# src/cli/orchestrator.py
- Update _generate_tv_file_path() to use HierarchicalFileWriter
- Add generate_hierarchical() method
- Add generate_write_side_hierarchical() method
- Unify write/read generation logic

Lines: ~120 (modifications)
Tests: 5 new tests
Time: 10 hours
```

**Deliverables**:
- [ ] Unified generation workflow
- [ ] Both write and read use HierarchicalFileWriter
- [ ] Tests verify correct paths

#### **Wednesday: CLI Command Integration**

**Task 2.2: Update generate.py (Day 3)**
```python
# src/cli/generate.py
- Add --hierarchical/--flat flag (default: hierarchical)
- Add --dry-run flag
- Update help text
- Add progress indicators

Lines: ~80 (modifications)
Tests: CLI integration tests
Time: 6 hours
```

**Example CLI Usage**:
```bash
# Hierarchical (default)
specql generate entities/*.yaml --output=0_schema/

# Flat (legacy)
specql generate entities/*.yaml --output=generated/ --flat

# Dry run
specql generate entities/*.yaml --dry-run --verbose

# Output:
# ✨ Would generate:
#   Write-side:
#     0_schema/01_write_side/012_crm/0123_customer/01236_contact/012361_tb_contact.sql
#   Read-side:
#     0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql
```

**Deliverables**:
- [ ] `--hierarchical` flag works
- [ ] `--dry-run` shows preview
- [ ] Backward compatible with `--flat`

#### **Thursday: Integration Tests**

**Task 2.3: End-to-End Integration Tests (Day 4)**
```python
# tests/integration/test_hierarchical_generation.py
- test_generate_hierarchical_structure_end_to_end()
- test_hierarchical_preserves_dependencies()
- test_hierarchical_handles_multiple_domains()
- test_flat_mode_backward_compatible()
- test_dry_run_shows_preview()

Lines: ~200
Tests: 5 integration tests
Time: 8 hours
```

**Deliverables**:
- [ ] E2E tests cover full workflow
- [ ] Tests verify file system output
- [ ] Dependency ordering validated

#### **Friday: Week 2 Wrap-up**

**Task 2.4: Performance & Polish (Day 5)**
- Performance testing (100+ entities)
- Memory profiling
- CLI output formatting
- Error handling improvements

**Deliverables**:
- [ ] Handles 100+ entities efficiently
- [ ] Clean error messages
- [ ] Progress indicators working

**Week 2 Metrics**:
- Modified files: 2 (orchestrator, generate)
- Tests added: 10
- CLI fully functional
- Integration tests: 5

---

### **WEEK 3: Domain/Subdomain Registry Integration** (Nov 26 - Dec 2)

#### **Sprint Goals**
- Replace hardcoded domain/subdomain mappings
- Make system data-driven from registry
- Add CLI for registry management

#### **Monday-Tuesday: Registry Schema Updates**

**Task 3.1: Enhance domain_registry.yaml (Day 1-2)**
```yaml
# registry/domain_registry.yaml

# Add comprehensive subdomain definitions
domains:
  '2':
    name: crm
    description: Customer Relationship Management
    subdomains:
      '01':
        name: core
        description: Core CRM entities (Company, Account)
        entities:
          Company:
            table_code: '012011'
            read_entities:
              tv_company:
                code: '0220110'
      '03':
        name: customer
        description: Customer-specific entities
        entities:
          Contact:
            table_code: '012361'
            read_entities:
              tv_contact:
                code: '0220310'
              v_contact_summary:
                code: '0220320'

  '3':
    name: catalog
    description: Product Catalog
    subdomains:
      '01':
        name: classification
        description: Product classification system
      '02':
        name: manufacturer
        description: Manufacturer and brand data
```

**Task 3.2: Update DomainRegistry class (Day 2)**
```python
# src/generators/schema/naming_conventions.py
- Add load_domain_mapping() method
- Add load_subdomain_mapping() method
- Replace hardcoded dicts with registry lookups
- Cache for performance

Lines: ~100
Tests: 8 tests
Time: 10 hours
```

**Deliverables**:
- [ ] Registry-driven domain/subdomain names
- [ ] No hardcoded mappings
- [ ] Tests verify registry lookup

#### **Wednesday-Thursday: Registry CLI**

**Task 3.3: Registry Management CLI (Day 3-4)**
```python
# src/cli/registry.py
- specql registry list-domains
- specql registry list-subdomains crm
- specql registry add-domain
- specql registry add-subdomain
- specql registry show-entity Contact

Lines: ~250
Tests: 6 CLI tests
Time: 12 hours
```

**CLI Examples**:
```bash
# List domains
specql registry list-domains
# Output:
#   2 - crm (Customer Relationship Management)
#   3 - catalog (Product Catalog)
#   4 - projects (Project Management)

# Show entity info
specql registry show-entity Contact
# Output:
#   Entity: Contact
#   Domain: crm (2)
#   Subdomain: customer (03)
#   Table Code: 012361
#   Read Entities:
#     - tv_contact (0220310)
#     - v_contact_summary (0220320)

# Add new domain
specql registry add-domain --code=7 --name=finance --desc="Financial Management"
```

**Deliverables**:
- [ ] Registry CLI commands working
- [ ] YAML file management
- [ ] Validation and error handling

#### **Friday: Week 3 Wrap-up**

**Task 3.4: Documentation & Testing (Day 5)**
- Update registry documentation
- Add registry usage examples
- Test full workflow with registry
- Performance validation

**Deliverables**:
- [ ] Registry docs complete
- [ ] Example workflows documented
- [ ] All tests passing

**Week 3 Metrics**:
- New files: 1 (registry.py CLI)
- Modified files: 2 (naming_conventions, domain_registry.yaml)
- Tests added: 14
- System fully data-driven

---

### **WEEK 4: Month 1 Finalization** (Dec 3-9)

#### **Sprint Goals**
- Polish and bug fixes
- Documentation
- Performance optimization
- Prepare for Month 2

#### **Monday-Tuesday: Bug Fixes & Edge Cases**

**Task 4.1: Edge Case Handling (Day 1-2)**
- Circular dependencies detection
- Missing subdomain handling
- Invalid code format handling
- Large file sets (500+ entities)

**Deliverables**:
- [ ] Edge cases handled gracefully
- [ ] Error messages clear and actionable

#### **Wednesday-Thursday: Documentation**

**Task 4.2: Comprehensive Documentation (Day 3-4)**

**Documents to Create/Update**:
1. **User Guide**: `docs/guides/HIERARCHICAL_GENERATION.md`
   - How to use `--hierarchical`
   - File structure explanation
   - Migration from flat to hierarchical

2. **Developer Guide**: `docs/development/HIERARCHICAL_ARCHITECTURE.md`
   - FileSpec protocol
   - PathGenerator protocol
   - Extending for new layers

3. **Registry Guide**: `docs/guides/DOMAIN_REGISTRY.md`
   - Registry structure
   - Adding domains/subdomains
   - Code assignment rules

4. **Update CLAUDE.md**
   - Hierarchical generation section
   - CLI examples
   - Best practices

**Deliverables**:
- [ ] 4 documentation files complete
- [ ] Examples and screenshots
- [ ] Clear migration path

#### **Friday: Month 1 Retrospective**

**Task 4.3: Retrospective & Planning (Day 5)**
- Review Month 1 achievements
- Measure against success criteria
- Plan Month 2 priorities
- Update project roadmap

**Month 1 Deliverables Checklist**:
- [ ] Hierarchical generation 100% complete
- [ ] Both write and read-side working
- [ ] Registry-driven (no hardcoded mappings)
- [ ] CLI fully functional
- [ ] 20+ integration tests passing
- [ ] Documentation complete
- [ ] Test coverage ≥ 90%

**Month 1 Metrics**:
- Files added: 5
- Files modified: 10
- Tests added: 50+
- Documentation pages: 4
- Code coverage: 90%

---

## 🗓️ **MONTH 2: Pattern Library + SQL Expansion**

**Goal**: Universal pattern system + expand SQL expressiveness from 21% to 60%

**Theme**: "Universal Abstraction"

---

### **WEEK 5: Pattern Library Foundation** (Dec 10-16)

#### **Sprint Goals**
- Create pattern_library.db
- Define Tier 1 primitives (35 patterns)
- Build pattern compiler infrastructure

#### **Monday-Tuesday: Database Schema**

**Task 5.1: Pattern Library Database (Day 1-2)**
```sql
-- database/pattern_library_schema.sql

CREATE TABLE primitive_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    yaml_syntax TEXT NOT NULL,
    sql_equivalent TEXT,
    complexity_score INTEGER,
    tier TEXT DEFAULT 'tier_1'
);

CREATE TABLE domain_patterns (
    pattern_id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    parameters_schema TEXT NOT NULL,
    implementation_template TEXT NOT NULL,
    example_usage TEXT,
    tier TEXT DEFAULT 'tier_2'
);

CREATE TABLE business_templates (
    template_id INTEGER PRIMARY KEY,
    domain TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    template_yaml TEXT NOT NULL,
    patterns_used TEXT NOT NULL,
    description TEXT,
    tier TEXT DEFAULT 'tier_3',
    UNIQUE(domain, entity_name)
);

CREATE TABLE language_implementations (
    implementation_id INTEGER PRIMARY KEY,
    pattern_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    ecosystem TEXT,
    implementation_template TEXT NOT NULL,
    example_code TEXT,
    FOREIGN KEY (pattern_id) REFERENCES primitive_patterns(pattern_id),
    UNIQUE(pattern_id, language)
);
```

**Task 5.2: Seed Tier 1 Primitives (Day 2)**
```python
# database/seed_pattern_library.py
- 35 primitive patterns
- Categories: variables, queries, control_flow, data_manipulation, functions

Lines: ~500 (data)
Time: 8 hours
```

**Patterns to Add**:
1. Variables (4): declare, assign, let, const
2. Queries (7): query, cte, aggregate, subquery, join, recursive_cte, lateral_join
3. Control Flow (6): if, switch, while, for_query, foreach, break
4. Data Manipulation (8): insert, update, delete, upsert, batch_insert, merge, truncate, copy
5. Functions (5): call_function, return, return_early, return_table, raise_exception
6. Advanced (5): json_build, array_build, transform, cursor, dynamic_sql

**Deliverables**:
- [ ] Database schema created
- [ ] 35 primitive patterns seeded
- [ ] Documentation for each pattern

#### **Wednesday-Thursday: Pattern Compiler**

**Task 5.3: PatternCompiler Core (Day 3-4)**
```python
# src/generators/patterns/pattern_compiler.py
- PatternCompiler class
- load_pattern() method
- compile_pattern() method
- validate_parameters() method

Lines: ~300
Tests: 10 tests
Time: 12 hours
```

**Deliverables**:
- [ ] PatternCompiler implemented
- [ ] Can load from database
- [ ] Can render templates
- [ ] Tests verify compilation

#### **Friday: Week 5 Wrap-up**

**Task 5.4: Pattern CLI (Day 5)**
```python
# src/cli/patterns.py
- specql patterns list
- specql patterns show <pattern>
- specql patterns validate <yaml>

Lines: ~150
Tests: 4 tests
Time: 6 hours
```

**Deliverables**:
- [ ] Pattern CLI working
- [ ] Can list and inspect patterns
- [ ] Validation command works

**Week 5 Metrics**:
- New files: 3 (schema, seed, compiler, CLI)
- Database: pattern_library.db
- Patterns defined: 35
- Tests added: 14

---

### **WEEK 6: SQL Expression Expansion (Tier 1)** (Dec 17-23)

#### **Sprint Goals**
- Implement 5 CRITICAL new step types
- Expand SQL coverage from 21% to 40%
- Update parser and compilers

#### **Monday: declare Step Type**

**Task 6.1: Declare Step (Day 1)**
```python
# src/core/ast_models.py
- Add DeclareStep dataclass
- Add to ActionStep union type

# src/core/specql_parser.py
- Add parse_declare_step()

# src/generators/actions/step_compilers/declare_step_compiler.py
- Compile declare → PL/pgSQL DECLARE

Lines: ~150
Tests: 8 tests
Time: 6 hours
```

**Example**:
```yaml
steps:
  - declare:
      total_amount: money
      item_count: integer = 0
      validation_result: jsonb
```

→
```sql
DECLARE
    total_amount app.money_amount;
    item_count INTEGER := 0;
    validation_result JSONB;
```

#### **Tuesday: query Step Type**

**Task 6.2: Query Step (Day 2)**
```python
# src/generators/actions/step_compilers/query_step_compiler.py
- Compile query → SELECT ... INTO

Lines: ~200
Tests: 10 tests
Time: 8 hours
```

**Example**:
```yaml
steps:
  - query:
      into: customer_data
      select: name, email, status
      from: tb_customer
      where: id = $input.customer_id
```

→
```sql
SELECT name, email, status
INTO customer_data
FROM crm.tb_customer
WHERE id = v_input.customer_id;
```

#### **Wednesday: cte Step Type**

**Task 6.3: CTE Step (Day 3)**
```python
# src/generators/actions/step_compilers/cte_step_compiler.py
- Compile cte → WITH clause

Lines: ~250
Tests: 12 tests
Time: 8 hours
```

**Example**:
```yaml
steps:
  - cte:
      name: recent_orders
      query:
        select: order_id, total
        from: tb_order
        where: created_at > now() - interval '30 days'

  - query:
      into: order_stats
      select: count(*), sum(total)
      from: recent_orders
```

→
```sql
WITH recent_orders AS (
    SELECT order_id, total
    FROM tb_order
    WHERE created_at > now() - interval '30 days'
)
SELECT count(*), sum(total)
INTO order_stats
FROM recent_orders;
```

#### **Thursday: aggregate Step Type**

**Task 6.4: Aggregate Step (Day 4)**
```python
# src/generators/actions/step_compilers/aggregate_step_compiler.py
- Compile aggregate → GROUP BY, array_agg, jsonb_agg

Lines: ~200
Tests: 10 tests
Time: 8 hours
```

**Example**:
```yaml
steps:
  - aggregate:
      into: category_stats
      select:
        - category
        - count: "*"
        - sum: amount
        - array_agg: product_name
      from: tb_order_item
      group_by: category
      having: count(*) > 5
```

→
```sql
SELECT
    category,
    count(*) as count,
    sum(amount) as sum,
    array_agg(product_name) as product_names
INTO category_stats
FROM tb_order_item
GROUP BY category
HAVING count(*) > 5;
```

#### **Friday: call_function Enhanced**

**Task 6.5: Enhanced Call Function (Day 5)**
```python
# src/generators/actions/step_compilers/call_function_step_compiler.py
- Add support for INTO
- Add support for named parameters
- Add support for OUT parameters

Lines: ~100 (enhancements)
Tests: 8 tests
Time: 6 hours
```

**Deliverables**:
- [ ] 5 new step types implemented
- [ ] Parser updated
- [ ] Compilers tested
- [ ] SQL coverage: 40%

**Week 6 Metrics**:
- New step types: 5
- New compilers: 4
- Tests added: 48
- SQL coverage: 21% → 40%

---

### **WEEK 7: Domain Patterns (Tier 2)** (Dec 24-30)

*Note: Adjust for holidays*

#### **Sprint Goals**
- Implement 5 domain patterns
- Pattern template system
- Pattern composition

#### **Monday-Tuesday: State Machine Pattern**

**Task 7.1: State Machine Implementation (Day 1-2)**
```python
# Add to database/seed_pattern_library.py
- state_machine pattern definition
- Parameters: states, transitions, guards
- Implementation template using Tier 1 primitives

# src/generators/patterns/domain_patterns/state_machine.py
- StateMachinePattern class
- compile_transitions() method
- generate_actions() method

Lines: ~400
Tests: 12 tests
Time: 12 hours
```

**Example Usage**:
```yaml
entity: Order
patterns:
  - state_machine:
      states: [pending, confirmed, shipped, delivered, cancelled]
      transitions:
        - [pending, confirmed]
        - [pending, cancelled]
        - [confirmed, shipped]
        - [shipped, delivered]
      guards:
        pending->confirmed: payment_received = true
        confirmed->shipped: items_packed = true

# Generates:
# - transition_order(order_id, target_state) action
# - validate_transition(order_id, from, to) function
# - get_valid_transitions(order_id) function
```

**Deliverables**:
- [ ] State machine pattern working
- [ ] Generates all transition logic
- [ ] Guards compiled correctly

#### **Wednesday: Approval Workflow Pattern**

**Task 7.2: Approval Workflow (Day 3)**
```python
# src/generators/patterns/domain_patterns/approval_workflow.py
- ApprovalWorkflowPattern class
- Generates request/approve/reject actions
- Audit trail generation

Lines: ~300
Tests: 10 tests
Time: 8 hours
```

**Deliverables**:
- [ ] Approval pattern working
- [ ] Generates 3 actions
- [ ] Audit trail included

#### **Thursday-Friday: Additional Patterns**

**Task 7.3: Three More Patterns (Day 4-5)**

1. **Hierarchy Navigation** (Day 4)
   - ancestor_path calculation
   - descendants query
   - siblings query

2. **Soft Delete** (Day 4)
   - delete action with deleted_at
   - restore action
   - permanent_delete action

3. **Audit Trail** (Day 5)
   - Auto-generate audit tables
   - Change tracking
   - History queries

**Deliverables**:
- [ ] 3 additional patterns implemented
- [ ] Total: 5 domain patterns
- [ ] Pattern composition tested

**Week 7 Metrics**:
- Domain patterns: 5
- Pattern templates: 5
- Tests added: 32
- Lines of code: ~1000

---

### **WEEK 8: Business Templates (Tier 3)** (Dec 31 - Jan 6)

#### **Sprint Goals**
- Create 5 business domain templates
- Template marketplace infrastructure
- Template CLI

#### **Monday-Tuesday: E-commerce Templates**

**Task 8.1: E-commerce Domain (Day 1-2)**

Templates to create:
1. **Order** - state_machine + approval_workflow
2. **Product** - hierarchy_navigation + soft_delete
3. **Cart** - soft_delete + audit_trail
4. **Customer** - audit_trail
5. **Payment** - state_machine + audit_trail

**Deliverables**:
- [ ] 5 e-commerce templates
- [ ] Each uses 2+ domain patterns
- [ ] Complete field definitions

#### **Wednesday: CRM Templates**

**Task 8.2: CRM Domain (Day 3)**

Templates:
1. **Contact** - audit_trail + soft_delete
2. **Company** - hierarchy_navigation + audit_trail
3. **Opportunity** - state_machine + approval_workflow

**Deliverables**:
- [ ] 3 CRM templates
- [ ] Realistic field sets
- [ ] Pattern composition

#### **Thursday: Template CLI**

**Task 8.3: Template Generation CLI (Day 4)**
```python
# src/cli/templates.py
- specql templates list
- specql templates show ecommerce.Order
- specql templates generate ecommerce.Order -o entities/

Lines: ~200
Tests: 8 tests
Time: 8 hours
```

**CLI Examples**:
```bash
# List templates
specql templates list
# Output:
#   E-commerce:
#     - Order (state_machine, approval_workflow)
#     - Product (hierarchy_navigation, soft_delete)
#     - Cart (soft_delete, audit_trail)
#
#   CRM:
#     - Contact (audit_trail, soft_delete)
#     - Company (hierarchy_navigation, audit_trail)

# Generate from template
specql templates generate ecommerce.Order -o entities/
# Creates: entities/order.yaml with all patterns applied

# Then compile to SQL
specql generate entities/order.yaml --hierarchical
```

**Deliverables**:
- [ ] Template CLI working
- [ ] Can list and preview templates
- [ ] Generation creates valid SpecQL

#### **Friday: Week 8 Wrap-up**

**Task 8.4: Template Documentation (Day 5)**
- Document all templates
- Usage examples
- Pattern combinations guide
- Best practices

**Deliverables**:
- [ ] Template catalog documented
- [ ] Examples for each template
- [ ] Pattern combination guide

**Week 8 Metrics**:
- Business templates: 8
- Domains covered: 2 (e-commerce, CRM)
- CLI commands: 6 new
- Tests added: 24

---

### **Month 2 Summary**

**Achievements**:
- ✅ Pattern library database with 35 primitives
- ✅ 5 domain patterns (Tier 2)
- ✅ 8 business templates (Tier 3)
- ✅ Pattern compiler working
- ✅ Template CLI functional
- ✅ SQL coverage: 60%

**Metrics**:
- New files: 20+
- Tests added: 150+
- Patterns: 35 + 5 + 8 = 48 total
- Code coverage: 92%

---

## 🗓️ **MONTH 3: Multi-Language + Architecture Generation**

**Goal**: Generate code for Python/TypeScript + system architecture templates

**Theme**: "Universal Platform"

---

### **WEEK 9: Multi-Language Foundation** (Jan 7-13)

#### **Sprint Goals**
- Language abstraction layer
- Python/Django code generation
- TypeScript/Prisma code generation

#### **Monday-Tuesday: Language Compiler**

**Task 9.1: LanguageCompiler Core (Day 1-2)**
```python
# src/generators/languages/language_compiler.py
- LanguageCompiler class
- Target language selection
- Template system

# src/generators/languages/base_generator.py
- BaseLanguageGenerator protocol
- Type mapping interface
- Expression compiler interface

Lines: ~300
Tests: 12 tests
Time: 12 hours
```

**Deliverables**:
- [ ] Language abstraction layer
- [ ] Plugin architecture for languages
- [ ] Type mapping system

#### **Wednesday-Thursday: Python/Django Generator**

**Task 9.2: Python Django Generator (Day 3-4)**
```python
# src/generators/languages/python_django_generator.py
- PythonDjangoGenerator class
- Entity → Django Model
- Action → Model method
- Type mapping (SpecQL → Python/Django)

Lines: ~500
Tests: 20 tests
Time: 14 hours
```

**Example**:
```yaml
# Input: entities/order.yaml
entity: Order
fields:
  customer: ref(Customer)
  total_amount: money
  state: enum(pending, confirmed, shipped)
patterns:
  - state_machine: [...]
```

→

```python
# Output: generated/python/models/order.py
from django.db import models
from decimal import Decimal

class OrderState(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    SHIPPED = 'shipped', 'Shipped'

class Order(models.Model):
    """Order entity - generated from SpecQL"""

    # Trinity pattern
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    identifier = models.CharField(max_length=255, unique=True)

    # Fields
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(max_length=20, choices=OrderState.choices)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tb_order'
        ordering = ['-created_at']

    def transition_order(self, target_state: OrderState) -> bool:
        """State machine: transition order state"""
        valid_transitions = {
            OrderState.PENDING: [OrderState.CONFIRMED, OrderState.CANCELLED],
            OrderState.CONFIRMED: [OrderState.SHIPPED, OrderState.CANCELLED],
            OrderState.SHIPPED: [OrderState.DELIVERED],
        }

        if target_state not in valid_transitions.get(self.state, []):
            raise ValueError(f"Invalid transition: {self.state} -> {target_state}")

        self.state = target_state
        self.save()
        return True
```

**Deliverables**:
- [ ] Python/Django generator working
- [ ] Models generate correctly
- [ ] Methods from actions
- [ ] Type mappings complete

#### **Friday: TypeScript/Prisma Generator**

**Task 9.3: TypeScript Prisma Generator (Day 5)**
```python
# src/generators/languages/typescript_prisma_generator.py
- TypeScriptPrismaGenerator class
- Entity → Prisma model
- Type mapping (SpecQL → Prisma)

Lines: ~400
Tests: 16 tests
Time: 8 hours
```

**Example**:
```yaml
# Input: entities/order.yaml (same as above)
```

→

```prisma
// Output: generated/typescript/prisma/schema.prisma
model Order {
  /// Trinity pattern
  id          String   @id @default(uuid())
  identifier  String   @unique

  /// Fields
  customerId  String
  customer    Customer @relation(fields: [customerId], references: [id])
  totalAmount Decimal  @db.Money
  state       OrderState

  /// Audit fields
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  deletedAt   DateTime?

  @@map("tb_order")
  @@index([customerId])
}

enum OrderState {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}
```

**Deliverables**:
- [ ] TypeScript/Prisma generator working
- [ ] Schema generates correctly
- [ ] Enums handled properly

**Week 9 Metrics**:
- Languages supported: 3 (PostgreSQL, Python, TypeScript)
- Generators: 2 new
- Tests added: 48
- Lines of code: ~1200

---

### **WEEK 10: Language Implementation Templates** (Jan 14-20)

#### **Sprint Goals**
- Populate language_implementations table
- Pattern → Python mapping
- Pattern → TypeScript mapping

#### **Monday-Tuesday: PostgreSQL Templates**

**Task 10.1: PostgreSQL Pattern Templates (Day 1-2)**
```python
# database/seed_language_implementations.py
- Add PostgreSQL templates for all 35 primitives
- Jinja2 templates for each pattern
- Example code for each

Lines: ~800 (data)
Time: 12 hours
```

**Example**:
```python
# Pattern: declare
# Language: PostgreSQL
{
    'implementation_template': '''
DECLARE
    {% for var_name, var_type in variables.items() %}
    {{ var_name }} {{ var_type }}{% if var_name in initial_values %} := {{ initial_values[var_name] }}{% endif %};
    {% endfor %}
''',
    'example_code': '''
DECLARE
    total_amount app.money_amount;
    item_count INTEGER := 0;
'''
}
```

**Deliverables**:
- [ ] 35 PostgreSQL templates
- [ ] All tested
- [ ] Examples provided

#### **Wednesday-Thursday: Python/Django Templates**

**Task 10.2: Python Pattern Templates (Day 3-4)**
```python
# Continue database/seed_language_implementations.py
- Add Python/Django templates for 35 primitives
- Handle differences (no declare in Python)
- Workarounds for unsupported patterns

Lines: ~1000 (data)
Time: 14 hours
```

**Example**:
```python
# Pattern: declare
# Language: Python
{
    'supported': True,
    'implementation_template': '''
# Variable declarations (Python doesn't require explicit declaration)
{% for var_name, var_type in variables.items() %}
{{ var_name }}: {{ python_type_map[var_type] }}{% if var_name in initial_values %} = {{ initial_values[var_name] }}{% endif %}
{% endfor %}
''',
    'example_code': '''
total_amount: Decimal
item_count: int = 0
validation_result: dict
'''
}
```

**Deliverables**:
- [ ] 35 Python templates
- [ ] Unsupported patterns documented
- [ ] Workarounds provided

#### **Friday: TypeScript Templates**

**Task 10.3: TypeScript Pattern Templates (Day 5)**
```python
# Continue database/seed_language_implementations.py
- Add TypeScript templates for 35 primitives
- Prisma-specific patterns
- Type safety considerations

Lines: ~800 (data)
Time: 8 hours
```

**Deliverables**:
- [ ] 35 TypeScript templates
- [ ] Prisma integration
- [ ] Type definitions

**Week 10 Metrics**:
- Language templates: 105 (35 × 3 languages)
- Database rows: 105
- Coverage matrix complete

---

### **WEEK 11: System Architecture Templates** (Jan 21-27)

#### **Sprint Goals**
- Architecture pattern database
- System architecture templates
- Infrastructure as Code generation

#### **Monday-Tuesday: Architecture Database**

**Task 11.1: Architecture Schema (Day 1-2)**
```sql
-- database/architecture_library_schema.sql

CREATE TABLE system_architectures (
    arch_id INTEGER PRIMARY KEY,
    arch_name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    components_template TEXT NOT NULL,
    deployment_template TEXT NOT NULL,
    tech_stack TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE architecture_components (
    component_id INTEGER PRIMARY KEY,
    arch_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL,
    patterns TEXT NOT NULL,
    config_template TEXT NOT NULL,
    FOREIGN KEY (arch_id) REFERENCES system_architectures(arch_id)
);

CREATE TABLE deployment_targets (
    target_id INTEGER PRIMARY KEY,
    target_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    config_template TEXT NOT NULL
);
```

**Seed Data**:
1. **Monolith** (Simple single-service)
2. **Microservices** (Multiple services)
3. **CQRS** (Command/Query separation)
4. **Event-Driven** (Event sourcing + projections)
5. **Serverless** (FaaS architecture)

**Deliverables**:
- [ ] Architecture database schema
- [ ] 5 architecture templates
- [ ] Component definitions

#### **Wednesday-Thursday: Architecture Compiler**

**Task 11.2: ArchitectureCompiler (Day 3-4)**
```python
# src/generators/architecture/architecture_compiler.py
- ArchitectureCompiler class
- System generation from templates
- Multi-service coordination

Lines: ~600
Tests: 20 tests
Time: 14 hours
```

**Example Usage**:
```bash
specql architecture generate \
  --template=microservices_cqrs \
  --domain=ecommerce \
  --services="order,inventory,payment" \
  --output=system/

# Generates:
# system/
#   services/
#     order-command/
#       entities/order.yaml
#       generated/postgresql/...
#     order-query/
#       entities/order_view.yaml
#       generated/postgresql/...
#     inventory-command/
#       entities/inventory.yaml
#     payment-command/
#       entities/payment.yaml
#   shared/
#     events/order_events.yaml
#   k8s/
#     order-command-deployment.yaml
#     order-query-deployment.yaml
#     ...
#   docker-compose.yml
#   .env.example
#   README.md
```

**Deliverables**:
- [ ] ArchitectureCompiler working
- [ ] Multi-service generation
- [ ] Infrastructure files

#### **Friday: Infrastructure as Code**

**Task 11.3: IaC Generation (Day 5)**
```python
# src/generators/architecture/iac_generator.py
- Kubernetes manifests
- Docker Compose
- Terraform (basic)

Lines: ~400
Tests: 12 tests
Time: 8 hours
```

**Deliverables**:
- [ ] K8s manifests generate
- [ ] Docker Compose generates
- [ ] Environment configs

**Week 11 Metrics**:
- Architecture templates: 5
- IaC generators: 3
- Tests added: 32
- Lines of code: ~1000

---

### **WEEK 12: Month 3 Finalization** (Jan 28 - Feb 3)

#### **Sprint Goals**
- Polish and optimization
- Documentation
- Marketing preparation
- Launch readiness

#### **Monday: Performance Optimization**

**Task 12.1: Performance Tuning (Day 1)**
- Profile pattern compilation
- Optimize database queries
- Cache improvements
- Parallel generation

**Deliverables**:
- [ ] 2x faster generation
- [ ] Memory optimized
- [ ] Benchmarks documented

#### **Tuesday-Wednesday: Documentation**

**Task 12.2: Comprehensive Documentation (Day 2-3)**

**Documentation Set**:
1. **User Guides** (10 docs)
   - Getting Started
   - Hierarchical Generation
   - Pattern Library
   - Business Templates
   - Multi-Language Generation
   - Architecture Generation
   - CLI Reference
   - Best Practices
   - Migration Guide
   - Troubleshooting

2. **Developer Guides** (5 docs)
   - Architecture Overview
   - Adding New Patterns
   - Adding New Languages
   - Adding Architecture Templates
   - Contributing Guide

3. **API Documentation**
   - Pattern Library API
   - LanguageCompiler API
   - ArchitectureCompiler API

**Deliverables**:
- [ ] 15 documentation files
- [ ] API docs complete
- [ ] Examples for everything

#### **Thursday: Examples & Showcase**

**Task 12.3: Example Projects (Day 4)**

Create complete example projects:
1. **E-commerce System** (microservices)
   - Order service
   - Inventory service
   - Payment service
   - All languages (PostgreSQL, Python, TypeScript)

2. **CRM System** (monolith)
   - Contact management
   - All patterns demonstrated
   - Single language (PostgreSQL)

3. **SaaS Platform** (CQRS)
   - Multi-tenant
   - Event sourcing
   - Complex patterns

**Deliverables**:
- [ ] 3 complete examples
- [ ] README for each
- [ ] Deployment instructions

#### **Friday: Launch Preparation**

**Task 12.4: Release Preparation (Day 5)**
- Version 1.0.0 tagging
- Changelog compilation
- Release notes
- GitHub release
- Marketing materials

**Deliverables**:
- [ ] Version 1.0.0 released
- [ ] Changelog complete
- [ ] Release notes published
- [ ] Marketing ready

**Week 12 Metrics**:
- Documentation: 15 files
- Examples: 3 complete projects
- Version: 1.0.0
- Ready for launch

---

## 📊 **3-Month Summary**

### **Quantitative Achievements**

| Metric | Start | End | Growth |
|--------|-------|-----|--------|
| Source Files | 193 | ~320 | +66% |
| Test Files | 233 | ~350 | +50% |
| Test Coverage | 85% | 95% | +10pp |
| SQL Coverage | 21% | 95% | +74pp |
| Patterns | 0 | 48 | ∞ |
| Languages | 1 | 3 | +200% |
| Templates | 0 | 13 | ∞ |
| Documentation | ~10 | ~30 | +200% |

### **Qualitative Achievements**

✅ **Month 1**: Production-ready hierarchical generation
✅ **Month 2**: Universal pattern library with 48 patterns
✅ **Month 3**: Multi-language + architecture generation

### **Platform Capabilities**

**Before (Current)**:
- PostgreSQL code generation
- Flat file structure
- Manual pattern implementation
- Single language

**After (Month 3)**:
- Universal code generation platform
- Hierarchical organization
- Pattern-driven development
- Multi-language (PostgreSQL, Python, TypeScript)
- Architecture templates
- Infrastructure as Code
- Business domain templates

---

## 🎯 **Success Criteria Validation**

### **Month 1**
- [x] Hierarchical generation complete
- [x] Registry-driven system
- [x] CLI functional
- [x] 90% test coverage
- [x] Documentation complete

### **Month 2**
- [x] 35 primitive patterns
- [x] 5 domain patterns
- [x] 8 business templates
- [x] Pattern compiler working
- [x] 60% SQL coverage

### **Month 3**
- [x] 3 languages supported
- [x] 5 architecture templates
- [x] IaC generation
- [x] 95% SQL coverage
- [x] Version 1.0.0 release

---

## 🚨 **Risk Assessment**

### **High Priority Risks**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Pattern complexity explosion | Medium | High | Strict pattern validation, tiered approach |
| Language mapping gaps | High | Medium | Document unsupported features, workarounds |
| Performance degradation | Low | High | Regular benchmarking, optimization sprints |
| Breaking changes | Medium | High | Version control, migration guides |

### **Medium Priority Risks**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | Medium | Strict sprint planning, MVP focus |
| Testing gaps | Low | Medium | TDD discipline, coverage monitoring |
| Documentation lag | Medium | Low | Documentation as deliverable |
| Database schema changes | Medium | Medium | Migration scripts, versioning |

---

## 📈 **Resource Allocation**

### **Developer Time**

| Month | Development | Testing | Documentation | Total |
|-------|-------------|---------|---------------|-------|
| Month 1 | 120h | 30h | 10h | 160h |
| Month 2 | 140h | 40h | 20h | 200h |
| Month 3 | 130h | 30h | 40h | 200h |
| **Total** | **390h** | **100h** | **70h** | **560h** |

### **Infrastructure**

- Development environment: Local
- Database: SQLite (included)
- CI/CD: GitHub Actions (free tier)
- Documentation: Markdown (free)
- Total cost: $0

---

## 🎓 **Learning Curve**

### **New Concepts to Master**

1. **Pattern-driven architecture** (Week 5-8)
2. **Multi-language code generation** (Week 9-10)
3. **Architecture as Code** (Week 11)
4. **Template systems** (ongoing)

### **Training Materials Needed**

- Pattern library usage guide
- Language generator API docs
- Architecture template guide
- Best practices handbook

---

## 🚀 **Post-Month 3 Roadmap**

### **Q2 2025**
- Additional languages (Ruby, Java, C#, Go)
- More architecture templates (10+)
- Pattern marketplace
- Visual pattern editor
- Community templates

### **Q3 2025**
- Cloud deployment automation (AWS, GCP, Azure)
- Monitoring and observability
- Security scanning
- Performance optimization
- Enterprise features

### **Q4 2025**
- SaaS offering
- Team collaboration features
- Version control integration
- CI/CD pipeline integration
- Enterprise support

---

## 📋 **Immediate Next Actions**

### **Week 1 Day 1 (Tomorrow)**
1. Create `src/generators/schema/hierarchical_file_writer.py`
2. Write FileSpec dataclass
3. Write PathGenerator protocol
4. Implement HierarchicalFileWriter class
5. Write 8 unit tests

**Time estimate**: 6 hours
**Deliverable**: Working file writer with tests

---

## 🎯 **Final Notes**

This plan is **aggressive but achievable** with:
- Disciplined TDD approach
- Clear sprint boundaries
- Regular retrospectives
- Scope discipline

The three-month timeline transforms SpecQL from a **PostgreSQL code generator** to a **universal architectural platform** - the foundation for a $100M+ opportunity.

**Ready to start Week 1, Day 1?**
