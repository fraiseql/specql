# Implementation Plans - Missing Patterns from PrintOptim Backend

## 📚 Quick Navigation

### Start Here: [PATTERNS_IMPLEMENTATION_ROADMAP.md](./PATTERNS_IMPLEMENTATION_ROADMAP.md)
**Master roadmap** with 6-week timeline, testing strategy, and getting started guide.

### Implementation Details: [MISSING_PATTERNS_IMPLEMENTATION.md](./MISSING_PATTERNS_IMPLEMENTATION.md)
**Complete phased TDD plans** for all three patterns with RED → GREEN → REFACTOR → QA cycles.

### Production Examples: [IDENTIFIER_CALCULATION_PATTERNS.md](./IDENTIFIER_CALCULATION_PATTERNS.md)
**Real-world analysis** from PrintOptim backend showing how identifiers are actually calculated.

---

## 🎯 Three Missing Patterns

### 1️⃣ Identifier Recalculation (recalcid functions)
**What**: Auto-calculate human-readable, hierarchical identifiers with deduplication
**Example**: `toulouse|legal.001-headquarters.002-building-a#2`
**Why**: Consistent, meaningful identifiers across related entities

### 2️⃣ LTREE Hierarchical Data
**What**: PostgreSQL LTREE paths for efficient tree queries
**Example**: `WHERE path <@ 'USA.California'` (all CA descendants)
**Why**: Fast ancestor/descendant queries without recursive CTEs

### 3️⃣ Node + Info Two-Table Split
**What**: Separate structure (node) from attributes (info) for hierarchical entities
**Example**: `tb_location` (pk, path, parent) + `tb_location_info` (name, type, address)
**Why**: Reusable tree logic, clean separation of concerns

---

## 🚀 Quick Start

### 1. Read the Roadmap
Start with [PATTERNS_IMPLEMENTATION_ROADMAP.md](./PATTERNS_IMPLEMENTATION_ROADMAP.md) for:
- 6-week timeline
- How patterns integrate
- Testing strategy
- Week 1, Day 1 tasks

### 2. Review Implementation Plans
Read [MISSING_PATTERNS_IMPLEMENTATION.md](./MISSING_PATTERNS_IMPLEMENTATION.md) for:
- Detailed TDD cycles
- Test specifications
- Code examples
- Quality gates

### 3. Study Production Patterns
Read [IDENTIFIER_CALCULATION_PATTERNS.md](./IDENTIFIER_CALCULATION_PATTERNS.md) for:
- Real-world examples from PrintOptim
- Slug-based identifiers
- Deduplication logic
- SpecQL integration proposals

### 4. Begin Implementation
Follow Week 1 tasks from roadmap:
- Create migration 000
- Add foundation types
- Write tests
- Start coding!

---

## 📊 Timeline Summary

| Week | Pattern | Deliverable |
|------|---------|-------------|
| 1-2 | Identifier Recalculation | `recalcid_{entity}()` functions working |
| 3-4 | LTREE Hierarchical Data | Hierarchical queries with LTREE |
| 5-6 | Node + Info Split | Two-table pattern for hierarchies |

**Total**: 6 weeks to production-ready implementation

---

## 🎓 For Each Team

### Team A (SpecQL Parser)
**Focus**: Parse new YAML sections
- `hierarchical: true`
- `metadata_split: true`
- `identifier:` configuration

**Documents**: ROADMAP (Team A section), IMPLEMENTATION (Phase 2)

### Team B (Schema Generator)
**Focus**: Generate tables, indexes, triggers
- LTREE columns and indexes
- Node + info table split
- Identifier fields
- Helper functions

**Documents**: ROADMAP (Team B section), IMPLEMENTATION (Pattern 2 & 3)

### Team C (Action Compiler)
**Focus**: Generate recalcid functions
- Hierarchical slug calculation
- Deduplication logic
- Two-table updates
- Cascade integration

**Documents**: IDENTIFIER_PATTERNS (all sections), IMPLEMENTATION (Pattern 1)

---

## ✅ Success Criteria

**Can I use it?**
- ✅ Write 20 lines of YAML
- ✅ Run `specql generate`
- ✅ Get 2000+ lines of SQL
- ✅ Load into PostgreSQL
- ✅ Query with GraphQL (FraiseQL)

**Does it work?**
- ✅ Location hierarchy with 3+ levels
- ✅ Identifiers auto-calculated on changes
- ✅ LTREE queries: "find all descendants"
- ✅ Node+info split with convenience view
- ✅ All tests pass (90%+ coverage)

---

## 📞 Questions?

1. **What are these patterns?** → Read ROADMAP introduction
2. **How do I implement them?** → Follow IMPLEMENTATION plans
3. **What do production examples look like?** → Study IDENTIFIER_PATTERNS
4. **Where do I start?** → ROADMAP "Getting Started" section
5. **How long will it take?** → 6 weeks (see timeline)

---

## 🔗 Related Documentation

- Main project: [/docs/architecture/CLAUDE.md](../../.claude/CLAUDE.md)
- Integration plans: [/docs/architecture/UPDATED_TEAM_PLANS_POST_FRAISEQL_RESPONSE.md](../architecture/UPDATED_TEAM_PLANS_POST_FRAISEQL_RESPONSE.md)
- PrintOptim analysis: [/docs/analysis/POC_RESULTS.md](../analysis/POC_RESULTS.md)

---

**Ready to implement? Start with the [ROADMAP](./PATTERNS_IMPLEMENTATION_ROADMAP.md)! 🚀**
