# Testing & Seed Generation - Implementation Overview

**Status**: Planning Phase
**Created**: 2025-11-08
**Integration Timeline**: Weeks 2-6 (parallel with Team B/C/D development)

---

## 🎯 Vision

**Transform SpecQL YAML into production-ready database + auto-generated tests + realistic seed data**

```
20 lines SpecQL YAML
    ↓
2000+ lines SQL (schema + functions)
    ↓
500+ lines test metadata
    ↓
1000+ lines pgTAP tests
    ↓
Unlimited seed data records
```

**Result**: 150x total code leverage including testing infrastructure

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  SpecQL YAML (Business Logic)                                   │
│  - Entity definitions                                           │
│  - Actions & validations                                        │
│  - Testing hints (optional)                                     │
└─────────────┬───────────────────────────────────────────────────┘
              │
    ┌─────────┴──────────────┐
    │                        │
    ▼                        ▼
┌──────────────┐      ┌─────────────────────────┐
│ Existing     │      │ NEW: Team T             │
│ Teams A-E    │      │ (Testing Infrastructure)│
│              │      │                         │
│ - Parser     │◄─────┤ - Test metadata gen    │
│ - Schema     │      │ - Seed data gen        │
│ - Actions    │      │ - pgTAP test gen       │
│ - FraiseQL   │      │ - UUID encoding        │
│ - CLI        │      │ - Group leaders        │
└──────┬───────┘      └───────┬─────────────────┘
       │                      │
       │                      │
       ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                             │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ App Schemas    │  │ test_metadata    │  │ testfoundry     │ │
│  │ - crm         │  │ - entity_config  │  │ - random_*()    │ │
│  │ - projects    │  │ - field_gen      │  │ - generate_*()  │ │
│  │ - catalog     │  │ - scenarios      │  │ (optional)      │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├─────────────┬──────────────┬──────────────┐
         ▼             ▼              ▼              ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
    │ Seed    │  │ pgTAP    │  │ Pytest   │  │ Property  │
    │ SQL     │  │ Tests    │  │ Tests    │  │ Tests     │
    │ Files   │  │          │  │          │  │ (Hypothesis)│
    └─────────┘  └──────────┘  └──────────┘  └───────────┘
```

---

## 👥 Team Structure

### **Team T: Testing Infrastructure** (NEW)

**Mission**: Auto-generate comprehensive tests and realistic seed data from SpecQL definitions

**Sub-teams**:
- **Team T-Meta**: Test metadata schema and generators
- **Team T-Seed**: Seed data generation with UUID encoding
- **Team T-Test**: Test suite generation (pgTAP + Pytest)
- **Team T-Prop**: Property-based testing framework

**Integration Points**:
- Consumes: Team A's AST models
- Coordinates: Team B (schema), Team C (actions), Team D (FraiseQL)
- Extends: Team E (CLI commands)

---

## 🔑 Key Innovations

### 1. **UUID Encoding for Traceability**

Adapted from PrintOptim Backend's proven pattern:

```
EEEEETTF-FFFF-0SSS-TTTT-00000000IIII
```

- **EEEEEE**: Entity code (e.g., `012321` = Contact)
- **TT**: Test type (21=seed, 22=mutation, 23=query)
- **F**: Function number last digit
- **FFFF**: Full function number
- **SSS**: Scenario code (0=default, 1000=dedup, etc.)
- **TTTT**: Test case number
- **IIII**: Instance sequence (1, 2, 3...)

**Example**:
```
01232022-3201-0001-0001-000000000001
│      ││ │    │    │    │
│      ││ │    │    │    └─ Instance #1
│      ││ │    │    └────── Test case #1
│      ││ │    └─────────── Scenario #1000 (dedup test)
│      ││ └──────────────── Function 33201 (create_contact)
│      │└─────────────────── Function last digit = 1
│      └──────────────────── Test type = 22 (mutation test)
└─────────────────────────── Entity code = 012321 (Contact)
```

**Benefits**:
- **Traceability**: Every UUID reveals its origin
- **Isolation**: Each scenario has unique UUID range
- **Debugging**: Decode UUID to find which test created the record
- **Consistency**: Same pattern across all entities

### 2. **Group Leader Pattern**

Borrowed from TestFoundry - ensures related fields stay consistent:

```
┌──────────────────────┐
│  Group Leader Field  │ ─── Executes ONE query ──► Database
│  (country_code)      │                             Returns:
└──────────────────────┘                             - country: "FR"
         │                                           - postal: "75001"
         │                                           - city: "PAR"
         ▼
┌──────────────────────┐
│ Dependent Fields     │ ◄─── All fields from one record
│ - postal_code        │
│ - city_code          │
└──────────────────────┘
```

**Problems Solved**:
- ❌ **Bad**: Random country + random postal = mismatch (e.g., "US" + "75001")
- ✅ **Good**: Country + postal + city from same address record = consistent

### 3. **Metadata-Driven Everything**

Single source of truth → multiple outputs:

```
SpecQL YAML
    ↓
Test Metadata Tables
    ├─► Seed Data Generator
    ├─► pgTAP Test Generator
    ├─► Pytest Generator
    └─► Property-Based Test Generator
```

### 4. **Multi-Layer Testing**

| Layer | Tool | Purpose | Auto-Generated? |
|-------|------|---------|-----------------|
| Database | pgTAP | Constraints, triggers, functions | ✅ Yes |
| Integration | Pytest | Python client, end-to-end flows | ✅ Yes |
| Property | Hypothesis | Edge cases, fuzzing | ✅ Yes |
| GraphQL | Custom | Query validation, cache invalidation | 🔄 Future |

---

## 📊 Integration Timeline

### **Week 2: Foundation** (Team T-Meta + Team T-Seed start)
- Design test metadata schema
- Implement UUID generator utility
- Basic seed generator for simple entities
- **Parallel**: Team B finishing schema generation

### **Week 3: Seed Generation** (Team T-Seed focus)
- Group leader pattern implementation
- FK resolution with dependencies
- Realistic data with Faker integration
- **Parallel**: Team C action compiler

### **Week 4: Test Generation** (Team T-Test starts)
- pgTAP test generator for CRUD
- pgTAP test generator for actions
- Pytest integration test generator
- **Parallel**: Team C action compiler continues

### **Week 5: Advanced Features** (Team T-Prop starts)
- Property-based testing framework
- Advanced scenarios (dedup, validation)
- Performance seed data (1000s of records)
- **Parallel**: Team D FraiseQL metadata

### **Week 6: CLI Integration** (All teams converge)
- CLI commands for test/seed generation
- End-to-end integration tests
- Documentation and examples
- **Parallel**: Team E orchestration

---

## 🎯 Success Criteria

### **Must Have (Week 6)**
- ✅ Auto-generate test metadata from SpecQL
- ✅ Auto-generate realistic seed data (10-100 records per entity)
- ✅ Auto-generate pgTAP tests for CRUD operations
- ✅ Auto-generate pgTAP tests for custom actions
- ✅ UUID encoding working for all entities
- ✅ Group leader pattern for address/location fields
- ✅ CLI: `specql generate --with-tests --with-seed`

### **Should Have (Week 7-8)**
- ✅ Pytest integration tests auto-generated
- ✅ Property-based tests for edge cases
- ✅ Snapshot testing for SQL generation
- ✅ Performance seed data (10K+ records)
- ✅ Test validation against live database

### **Nice to Have (Future)**
- 🔄 GraphQL query test generation
- 🔄 Mutation testing (validate test quality)
- 🔄 Visual regression testing
- 🔄 ML-based seed data from production patterns

---

## 📁 Repository Structure

```
src/
├── testing/                    # NEW: Team T code
│   ├── metadata/
│   │   ├── schema_generator.py          # Generate test_metadata schema
│   │   ├── metadata_populator.py        # Populate from SpecQL AST
│   │   └── group_leader_resolver.py     # Group leader pattern logic
│   │
│   ├── seed/
│   │   ├── uuid_generator.py            # UUID encoding utility
│   │   ├── seed_data_generator.py       # Main seed generator
│   │   ├── field_generators.py          # Field-specific generators
│   │   └── faker_integration.py         # Faker wrapper
│   │
│   ├── pgtap/
│   │   ├── pgtap_generator.py           # pgTAP test generator
│   │   ├── crud_test_templates.py       # CRUD test templates
│   │   └── action_test_templates.py     # Action test templates
│   │
│   ├── pytest/
│   │   ├── pytest_generator.py          # Pytest test generator
│   │   └── integration_test_templates.py
│   │
│   └── property/
│       ├── hypothesis_generator.py      # Property test generator
│       └── strategies.py                # Custom Hypothesis strategies
│
├── core/                       # Existing Team A
├── generators/                 # Existing Teams B/C/D
└── cli/                        # Existing Team E (extended)

tests/
├── fixtures/
│   ├── entities/               # YAML fixture library
│   ├── expected_sql/           # Expected output snapshots
│   └── seed_data/              # Pre-generated seed files
│
├── unit/
│   └── testing/                # NEW: Team T unit tests
│       ├── test_uuid_generator.py
│       ├── test_seed_generator.py
│       └── test_pgtap_generator.py
│
└── integration/
    └── testing/                # NEW: Team T integration tests
        ├── test_end_to_end_seed_generation.py
        └── test_pgtap_execution.py

migrations/
└── test_metadata_schema.sql    # NEW: Test metadata schema

generated/
├── seed/                       # NEW: Generated seed files
│   ├── contact_scenario_0.sql
│   └── contact_scenario_1000.sql
│
└── tests/                      # NEW: Generated tests
    ├── pgtap/
    │   └── contact_test.sql
    └── pytest/
        └── test_contact.py

docs/
└── implementation-plans/
    └── testing-and-seed-generation/
        ├── 00_OVERVIEW.md      # This file
        ├── 01_TEAM_T_META.md
        ├── 02_TEAM_T_SEED.md
        ├── 03_TEAM_T_TEST.md
        ├── 04_TEAM_T_PROP.md
        └── 05_INTEGRATION.md
```

---

## 🔗 Dependencies

### **External**
- `Faker` - Realistic data generation
- `Hypothesis` - Property-based testing
- `pgTAP` - PostgreSQL testing framework
- `pytest` - Python testing framework

### **Internal**
- Team A: AST models (Entity, FieldDefinition, Action)
- Team B: Schema generation patterns
- Team C: Action compilation patterns
- Team E: CLI orchestration

---

## 📖 Documentation Plan

Each team plan includes:

1. **Mission & Goals**: Clear objectives
2. **Architecture**: Component design
3. **Data Models**: Schemas, classes, types
4. **Implementation Phases**: RED → GREEN → REFACTOR → QA cycles
5. **Test Strategy**: Unit + integration tests
6. **Integration Points**: How team connects to others
7. **Examples**: Complete working examples
8. **Success Criteria**: Definition of done

---

## 🚀 Getting Started

Read the team-specific plans in order:

1. **[Team T-Meta](01_TEAM_T_META.md)** - Test metadata schema (start here)
2. **[Team T-Seed](02_TEAM_T_SEED.md)** - Seed data generation
3. **[Team T-Test](03_TEAM_T_TEST.md)** - Test suite generation
4. **[Team T-Prop](04_TEAM_T_PROP.md)** - Property-based testing
5. **[Integration Plan](05_INTEGRATION.md)** - How everything connects

---

## 🎓 Key Learnings from Inspirations

### From **TestFoundry**:
✅ Metadata-driven test generation
✅ Group leader pattern for consistency
✅ Declarative field generator mapping
✅ pgTAP integration patterns

### From **PrintOptim Backend**:
✅ UUID encoding for traceability
✅ Scenario-based test organization
✅ Domain-based numbering system
✅ Multi-layer seed data structure

### From **SpecQL Philosophy**:
✅ Convention over configuration
✅ 100x code leverage principle
✅ Single source of truth
✅ Business domain focus

---

**Next**: Read [Team T-Meta Implementation Plan](01_TEAM_T_META.md) to begin.
