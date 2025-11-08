# Testing & Seed Generation - Implementation Plans

**Project**: SpecQL Testing Infrastructure
**Status**: Planning Complete - Ready for Implementation
**Timeline**: Weeks 2-7 (6 weeks, parallel with Teams B/C/D)

---

## 📚 Documentation Index

Read the implementation plans in this order:

### 1. [Overview](00_OVERVIEW.md) - **START HERE**
High-level architecture, vision, and integration timeline for the testing infrastructure.

**Key Topics**:
- 150x code leverage (YAML → SQL + Tests + Seed)
- UUID encoding for traceability
- Group leader pattern for consistency
- Multi-layer testing strategy

### 2. [Team T-Meta: Test Metadata](01_TEAM_T_META.md)
PostgreSQL schema and generators for test metadata (the "control plane" for testing).

**Deliverables**:
- `test_metadata` schema (3 tables)
- Metadata generator from SpecQL AST
- Group leader detection
- Query API functions

**Timeline**: Week 2 (5 days)

### 3. [Team T-Seed: Seed Data Generation](02_TEAM_T_SEED.md)
Realistic, traceable seed data generation with UUID encoding.

**Deliverables**:
- UUID generator utility
- Field value generators (Faker integration)
- FK resolver + group leader executor
- SQL file generator

**Timeline**: Week 3 (5 days)

### 4. [Team T-Test: Test Suite Generation](03_TEAM_T_TEST.md)
Auto-generate pgTAP and Pytest test suites from SpecQL definitions.

**Deliverables**:
- pgTAP test generator (structure, CRUD, actions, constraints)
- Pytest integration test generator
- Test templates for all scenarios

**Timeline**: Week 4 (5 days)

### 5. [Team T-Prop: Property-Based Testing](04_TEAM_T_PROP.md)
Hypothesis-powered property tests to find edge cases automatically.

**Deliverables**:
- Hypothesis strategies for all field types
- Idempotency property tests
- Constraint property tests
- State machine tests

**Timeline**: Week 5 (5 days)

### 6. [Integration Plan](05_INTEGRATION.md)
How Team T integrates with existing Teams A-E, CLI extensions, and complete workflow.

**Deliverables**:
- Extended CLI with `--with-tests`, `--with-seed` flags
- Docker Compose test database
- End-to-end example workflow
- Makefile commands

**Timeline**: Week 6-7 (10 days)

---

## 🎯 Quick Reference

### Key Innovations

| Innovation | Inspiration | Benefit |
|------------|-------------|---------|
| **UUID Encoding** | PrintOptim Backend | Every test record traceable to entity/scenario/instance |
| **Group Leader Pattern** | TestFoundry | Related fields (address, location) stay consistent |
| **Metadata-Driven** | TestFoundry | Single source → multiple test/seed outputs |
| **Multi-Layer Testing** | SpecQL Philosophy | pgTAP + Pytest + Property tests auto-generated |

### Architecture at a Glance

```
SpecQL YAML (20 lines)
    ↓
Team A: Parse → AST
    ↓
Team T-Meta: AST → Test Metadata (PostgreSQL)
    ↓
    ├─► Team T-Seed → Seed SQL (100s of records)
    ├─► Team T-Test → pgTAP Tests (50+ tests)
    ├─► Team T-Test → Pytest Tests (10+ tests)
    └─► Team T-Prop → Hypothesis Tests (edge cases)
    ↓
Result: 2000+ lines SQL + 500+ lines tests + unlimited seed data
```

### UUID Encoding Pattern

```
EEEEETTF-FFFF-0SSS-TTTT-00000000IIII
│      ││ │    │    │    │
│      ││ │    │    │    └─ Instance (1, 2, 3...)
│      ││ │    │    └────── Test case number
│      ││ │    └─────────── Scenario (0=default, 1000=dedup, etc.)
│      ││ └──────────────── Function number (0000 for seed)
│      │└─────────────────── Function last digit
│      └──────────────────── Test type (21=seed, 22=mutation, 23=query)
└─────────────────────────── Entity code (012321 = Contact)
```

**Example**: `01232121-0000-0001-0001-000000000005`
- Entity: Contact (012321)
- Test type: General seed (21)
- Scenario: 1000 (deduplication test)
- Instance: 5

### Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Code Leverage** | 150x (20 YAML → 3000+ total) | Planning |
| **Test Coverage** | Auto-generate 50+ tests per entity | Planning |
| **Seed Data** | 100 realistic records in < 1 sec | Planning |
| **Integration** | YAML → SQL + Tests + Seed in single command | Planning |
| **Traceability** | 100% of test records have encoded UUIDs | Planning |

---

## 🚀 Getting Started

### For Developers

1. **Read the overview first**: [00_OVERVIEW.md](00_OVERVIEW.md)
2. **Pick a team based on your skills**:
   - Database/SQL → Team T-Meta
   - Data generation/Faker → Team T-Seed
   - Testing frameworks → Team T-Test
   - Advanced testing → Team T-Prop
3. **Follow TDD discipline**: RED → GREEN → REFACTOR → QA
4. **Run tests frequently**: `make test-meta`, `make test-seed`, etc.

### For Project Managers

- **Week 2**: Team T-Meta (foundation) - CRITICAL PATH
- **Week 3**: Team T-Seed (can start once T-Meta has basic schema)
- **Week 4**: Team T-Test (depends on T-Meta + T-Seed)
- **Week 5**: Team T-Prop (can run in parallel with Week 4)
- **Week 6-7**: Integration and polish

### For Users

Once implemented, you'll be able to:

```bash
# Generate everything from one YAML file
specql generate contact.yaml --with-tests --with-seed

# Output:
# ✓ migrations/001_contact.sql (schema + functions)
# ✓ test_metadata/001_contact_metadata.sql (test config)
# ✓ seed/contact_scenario_0.sql (100 realistic records)
# ✓ tests/pgtap/contact_test.sql (52 pgTAP tests)
# ✓ tests/pytest/test_contact.py (12 integration tests)
# ✓ tests/property/test_contact_properties.py (edge case tests)

# Apply to database
psql < migrations/001_contact.sql
psql < seed/contact_scenario_0.sql

# Run tests
docker-compose run pgtap
uv run pytest tests/pytest/
```

---

## 📖 Additional Resources

### Related Documentation
- [Main SpecQL README](../../../README.md)
- [Main Project CLAUDE.md](../../../.claude/CLAUDE.md)
- [Team A-E Implementation Status](../)

### Inspirations
- **TestFoundry** (`~/code/testfoundry`): Metadata-driven testing, group leader pattern
- **PrintOptim Backend** (`../printoptim_backend/db/2_seed_backend`): UUID encoding, seed organization
- **SpecQL Philosophy**: Convention over configuration, 100x code leverage

### External Tools
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [Faker](https://faker.readthedocs.io/) - Realistic data generation
- [pgTAP](https://pgtap.org/) - PostgreSQL testing framework
- [Pytest](https://pytest.org/) - Python testing framework

---

## 🎓 Key Learnings

### What We're Building
A **testing and seed data generation system** that:
1. Automatically generates test metadata from SpecQL YAML
2. Creates realistic, traceable seed data using UUID encoding
3. Auto-generates comprehensive test suites (pgTAP + Pytest + Property)
4. Integrates seamlessly with existing SpecQL code generation pipeline

### Why It Matters
- **Confidence**: Every generated function has auto-generated tests
- **Speed**: No manual test writing, no manual seed data creation
- **Quality**: Property-based testing finds edge cases humans miss
- **Traceability**: UUID encoding makes debugging trivial
- **Consistency**: Group leader pattern prevents data mismatches

### What's Different
- **Not a testing framework**: We generate tests, not run them
- **Not a mock library**: We generate real data, not mocks
- **Not a test runner**: We output pgTAP/Pytest that you run
- **Not a seed generator**: We're metadata-driven, not hardcoded

---

## ❓ FAQ

**Q: Why PostgreSQL-specific testing?**
A: SpecQL generates PostgreSQL functions. We test at the database layer to validate business logic, constraints, and triggers.

**Q: Why UUID encoding instead of sequential IDs?**
A: Traceability. Decode any UUID to see which entity/scenario/test created it. Critical for debugging.

**Q: Why group leader pattern?**
A: Consistency. Ensures related fields (country + postal + city) come from same record, avoiding mismatches.

**Q: Why auto-generate tests instead of writing them?**
A: Scalability. With 100s of entities, manual testing doesn't scale. Auto-generation ensures every entity gets comprehensive coverage.

**Q: Can I customize generated tests?**
A: Yes! Generated tests are starting points. You can extend them, or add custom scenarios to test metadata.

**Q: What if I don't want tests/seed?**
A: Optional. Use `specql generate contact.yaml` without flags to get only schema/functions.

---

## 📞 Contact

Questions about implementation plans? See:
- Main project docs: [CLAUDE.md](../../../.claude/CLAUDE.md)
- Team coordination: Check project board
- Technical questions: Open GitHub issue

---

**Status**: ✅ All implementation plans complete - Ready to begin Week 2 development!

**Next Step**: Start with [Team T-Meta](01_TEAM_T_META.md) - Foundation for all testing infrastructure.
