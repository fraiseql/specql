# Business Logic Library - Documentation

**Status**: 📋 Planning Complete - Ready for Implementation
**Created**: 2025-11-10
**Related GitHub Issue**: https://github.com/fraiseql/specql/issues/4

---

## 📚 Documentation Overview

This directory contains the complete implementation plan for a **domain-agnostic business logic pattern library** for SpecQL, inspired by the PrintOptim backend reference implementation.

### Documents in This Directory

1. **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** 🎯 **START HERE**
   - **Type**: Strategy Document (NEW)
   - **Audience**: All Stakeholders, Decision Makers
   - **Contents**:
     - Reconciles Business Logic Library plan with Issue #4 plan
     - Hybrid phased approach (best of both)
     - Immediate value (Week 4) + Long-term value (Week 20)
     - Decision points and flexibility
     - **Recommendation**: Read this first to understand the unified strategy

2. **[BUSINESS_LOGIC_LIBRARY.md](BUSINESS_LOGIC_LIBRARY.md)** ⭐ **EXECUTIVE SUMMARY**
   - **Type**: Executive Summary (15 pages)
   - **Audience**: Stakeholders, Product Managers, Decision Makers
   - **Contents**:
     - Vision and problem statement
     - Before/After comparisons
     - ROI analysis (180% return in Year 1)
     - Financial projections ($1.54M 3-year value)
     - Success criteria
     - Next steps

3. **[BUSINESS_LOGIC_LIBRARY_PLAN.md](BUSINESS_LOGIC_LIBRARY_PLAN.md)**
   - **Type**: Detailed Implementation Plan (70+ pages)
   - **Audience**: Developers, Architects, Team Leads
   - **Contents**:
     - Complete architecture (3-layer system)
     - 27 pattern definitions with examples
     - 6-phase implementation roadmap (20 weeks)
     - Pattern definition schemas
     - SQL generation templates
     - Testing strategy (800+ tests)
     - Team assignments and responsibilities
     - Success metrics and KPIs

4. **[BUSINESS_LOGIC_LIBRARY_ROADMAP.md](BUSINESS_LOGIC_LIBRARY_ROADMAP.md)**
   - **Type**: Visual Roadmap (35+ pages)
   - **Audience**: Project Managers, Developers, Stakeholders
   - **Contents**:
     - 20-week visual timeline
     - Pattern catalog overview (27 patterns)
     - Key milestones and deliverables
     - Before/After code comparisons
     - Success metrics dashboard
     - ROI projection charts
     - Quick start guide (post-launch)

5. **[mutation_pattern_library_proposal.md](mutation_pattern_library_proposal.md)**
   - **Type**: GitHub Issue Content
   - **Audience**: SpecQL Framework Developers
   - **Contents**:
     - Current state analysis
     - 6 critical gaps identified
     - Detailed examples for each gap
     - Proposed YAML syntax
     - Implementation recommendations
     - **Posted to**: https://github.com/fraiseql/specql/issues/4

---

## 🎯 Quick Summary

### The Problem

**177 business functions** in PrintOptim backend, totaling **~38,000 lines of manual SQL**:
- Inconsistent patterns across entities
- 2-4 hours per business action
- Easy to miss edge cases
- High maintenance burden
- Slow developer onboarding (2+ weeks)

### The Solution

**Pattern Library**: 27 reusable patterns covering 95%+ of business logic

```
stdlib/patterns/
├── core/           # CRUD enhancements (4 patterns)
├── state_machine/  # State transitions (3 patterns)
├── multi_entity/   # Cross-entity ops (4 patterns)
├── validation/     # Validation chains (3 patterns)
├── batch/          # Bulk operations (3 patterns)
├── conditional/    # If-then-else (3 patterns)
├── temporal/       # Time-based ops (3 patterns)
└── common/         # Utilities (4 patterns)
```

### The Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Code per action** | 150-400 lines SQL | 10-20 lines YAML | **95% reduction** |
| **Time per action** | 2-4 hours | 15-30 minutes | **10-20x faster** |
| **Onboarding** | 2+ weeks | 2 hours | **40x faster** |
| **Consistency** | Manual (varies) | 100% consistent | **Perfect** |

### The ROI

- **Investment**: $260K (54 person-weeks)
- **Year 1 Return**: $600K (5,000 hours saved)
- **Net Profit**: $340K (180% ROI)
- **Break-even**: Week 5 of usage (~50 new actions)
- **3-Year Value**: $1.54M

---

## 📖 Reading Guide

### For Decision Makers (45 minutes) 🎯

1. Read **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** (15 min)
   - Understand the hybrid phased approach
   - See immediate value (Week 4) vs long-term value (Week 20)
   - Review decision points and flexibility

2. Read **[BUSINESS_LOGIC_LIBRARY.md](BUSINESS_LOGIC_LIBRARY.md)** (20 min)
   - Understand vision and ROI
   - Review financial projections
   - Check success criteria

3. **Decision**: Approve hybrid approach and Phase 0 budget? (10 min)

### For Project Managers (2.5 hours)

1. Read **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** (30 min)
   - Understand phased approach
   - Note decision points (Week 4, Week 13)
   - Review unified timeline

2. Read **[BUSINESS_LOGIC_LIBRARY.md](BUSINESS_LOGIC_LIBRARY.md)** (30 min)
   - Overall vision and goals
   - Success metrics

3. Review **[BUSINESS_LOGIC_LIBRARY_ROADMAP.md](BUSINESS_LOGIC_LIBRARY_ROADMAP.md)** (60 min)
   - Detailed timeline and milestones
   - Phase deliverables

4. **Action**: Plan Phase 0 (CRUD gaps) team and resources (30 min)

### For Developers (5 hours)

1. Read **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** (30 min)
   - Understand why Phase 0 comes first
   - See how it leads to pattern library

2. Read **[mutation_pattern_library_proposal.md](mutation_pattern_library_proposal.md)** (60 min)
   - Understand the 6 critical CRUD gaps
   - Study reference SQL examples
   - Review proposed solutions

3. Study **[BUSINESS_LOGIC_LIBRARY_PLAN.md](BUSINESS_LOGIC_LIBRARY_PLAN.md)** Phase 0-2 (2 hours)
   - Phase 0: CRUD gap implementations
   - Phase 1: Pattern infrastructure
   - Phase 2: Core patterns

4. Review relevant code (90 min)
   - Current SpecQL action compilers
   - Reference SQL examples
   - Test infrastructure

5. **Action**: Prepare for Phase 0 implementation

### For Architects (10 hours)

1. Read **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** (60 min)
   - Full understanding of hybrid approach
   - Technical rationale for phasing
   - Architecture evolution

2. Read all main documents (4 hours)
   - Executive summary
   - Complete plan
   - Visual roadmap

3. Deep dive into architecture (3 hours)
   - Three-layer system
   - Pattern definition schemas
   - SQL generation templates
   - Pattern dependencies

4. Evaluate approach (2 hours)
   - Technical feasibility
   - Risk assessment
   - Alternative approaches
   - Recommendations

5. **Action**: Technical review and sign-off

### For SpecQL Framework Developers (3 hours) ⚡

1. **START**: Read **[IMPLEMENTATION_PLAN_RECONCILIATION.md](IMPLEMENTATION_PLAN_RECONCILIATION.md)** (20 min)
   - Understand Phase 0 priority
   - See how Issue #4 fits into larger vision

2. Read **[mutation_pattern_library_proposal.md](mutation_pattern_library_proposal.md)** (60 min)
   - The 6 critical gaps from Issue #4
   - Detailed reference SQL examples
   - Proposed YAML syntax

3. Review **GitHub Issue #4**: https://github.com/fraiseql/specql/issues/4 (20 min)
   - Community discussion
   - PrintOptim team needs
   - Timeline expectations

4. Study current codebase (60 min)
   - `src/generators/actions/` - Action compilers
   - `src/generators/actions/step_compilers/` - Step compilers
   - `src/generators/actions/identifier_recalc_generator.py` - Exists!
   - `src/generators/actions/step_compilers/refresh_table_view_compiler.py` - Exists!

5. **Action**: Begin Phase 0 Week 1 (Partial Updates)

---

## 🏗️ Architecture Overview

### Three-Layer System

```
┌──────────────────────────────────────────────────┐
│  LAYER 1: Business Logic (YAML)                  │
│  - entities/tenant/machine.yaml                  │
│  - Declares business operations                  │
│  - References pattern library                    │
└──────────────────────────────────────────────────┘
                    ▼
┌──────────────────────────────────────────────────┐
│  LAYER 2: Pattern Library (YAML + Templates)     │
│  - stdlib/patterns/{category}/{pattern}.yaml     │
│  - Reusable pattern abstractions                 │
│  - SQL generation templates (Jinja2)             │
└──────────────────────────────────────────────────┘
                    ▼
┌──────────────────────────────────────────────────┐
│  LAYER 3: Code Generator (Python)                │
│  - Team C implementation                         │
│  - Parses YAML + patterns                        │
│  - Generates PL/pgSQL                            │
└──────────────────────────────────────────────────┘
                    ▼
              PostgreSQL Functions
```

---

## 🗓️ Implementation Timeline

### 20-Week Roadmap

```
Phase 1 (Weeks 1-4):   Core CRUD Enhancements
                       ✅ Closes Priority 1 gaps

Phase 2 (Weeks 5-7):   State Machine Patterns
                       ✅ Business workflows declarative

Phase 3 (Weeks 8-10):  Multi-Entity Patterns
                       ✅ Complex operations simplified

Phase 4 (Weeks 11-13): Validation & Batch Patterns
                       ✅ All CRUD scenarios covered

Phase 5 (Weeks 14-16): Advanced Patterns
                       ✅ Full pattern library

Phase 6 (Weeks 17-20): Migration & Optimization
                       ✅ Production ready
```

**Key Milestones**:
- Week 4: Core CRUD complete (Priority 1 gaps closed)
- Week 7: State machines ready
- Week 10: Multi-entity working
- Week 16: All patterns implemented
- Week 20: Production deployment

---

## 📊 Pattern Catalog Preview

### Core Patterns (Priority 1)

1. **partial_update** - Update only fields in payload (CASE expressions)
2. **duplicate_check** - Business uniqueness validation before INSERT
3. **identifier_recalc** - Auto-calculate business identifiers
4. **projection_refresh** - Sync GraphQL materialized views

### State Machine Patterns (Priority 2)

5. **simple_transition** - State changes with guards and side effects
6. **multi_step_workflow** - Orchestrate multi-step operations
7. **guarded_transition** - Complex guard conditions

### Multi-Entity Patterns (Priority 2)

8. **coordinated_update** - Update multiple entities in transaction
9. **parent_child_cascade** - Cascade operations to children
10. **get_or_create** - Get existing or create if missing
11. **transactional_group** - Group operations in transaction

### Validation Patterns (Priority 3)

12. **validation_chain** - Chain multiple validation rules
13. **dependency_check** - Check referential integrity
14. **business_rule** - Custom business logic validation

### Batch Patterns (Priority 3)

15. **bulk_operation** - Process multiple records efficiently
16. **batch_import** - Import data with error handling
17. **error_handling** - Consistent error management

### Advanced Patterns (Priority 4)

18-27. Conditional, temporal, and utility patterns

**Total**: 27 patterns covering 95%+ of business logic

---

## 💡 Example: Machine Decommissioning

### Before (Manual SQL)

```sql
-- reference_sql/.../decommission_machine.sql
-- 150+ lines of PL/pgSQL
CREATE OR REPLACE FUNCTION core.decommission_machine(...)
RETURNS app.mutation_result AS $$
DECLARE
    v_machine tenant.tb_machine%ROWTYPE;
    v_active_allocations INTEGER;
    -- ... 20+ more variables ...
BEGIN
    -- Load current machine (10+ lines)
    -- Check current status (15+ lines)
    -- Check for active allocations (20+ lines)
    -- Update machine status (10+ lines)
    -- Archive related data (15+ lines)
    -- Log event (10+ lines)
    -- Refresh projection (10+ lines)
    -- Return result (20+ lines)
END;
$$;
```

**Total**: ~150 lines | **Time**: 2-4 hours | **Tests**: Manual (1-2 hours)

### After (Pattern Library)

```yaml
# entities/tenant/machine.yaml
actions:
  - name: decommission_machine
    pattern: stdlib/patterns/state_machine/simple_transition
    from_states: [active, maintenance]
    to_state: decommissioned

    validations:
      - type: dependency_check
        entity: Allocation
        field: machine
        condition: "status = 'active'"
        error_code: "has_active_allocations"
        error_message: "Cannot decommission machine with active allocations"

    side_effects:
      - type: update_field
        field: decommission_date
        value: now()
      - type: update_related
        entity: MachineItem
        relationship: machine
        updates: {status: archived}
      - type: insert_event
        entity: MachineEvent
        event_data: {event_type: decommissioned}

    input_fields:
      decommission_date: {type: date, required: true}
      decommission_reason: {type: text, required: true}
```

**Total**: ~20 lines YAML | **Time**: 15-30 minutes | **Tests**: Auto-generated

**Result**: 87% code reduction, 87% time savings, 100% consistent

---

## 🎯 Success Metrics

### Quantitative Targets

- **Code Reduction**: 95% (38K lines → 2K lines)
- **Pattern Coverage**: 95% (business logic expressible)
- **Migration Complete**: 100% (all entities)
- **Test Coverage**: 90%+ (pattern library)
- **Performance**: No regression vs reference SQL
- **Query Performance**: <50ms p95
- **Throughput**: 100+ TPS

### Qualitative Goals

- Developers express business logic without writing SQL
- New patterns added without breaking existing code
- Generated SQL readable and debuggable
- Error messages clear and actionable
- Documentation comprehensive and current
- Pattern library intuitive to use
- Onboarding: 2 days → 2 hours

---

## 🚀 Getting Started (Post-Implementation)

When the pattern library is ready (Week 20+):

```bash
# 1. Read pattern catalog
open docs/patterns/pattern_catalog.md

# 2. Watch quick start video
open docs/videos/pattern_library_quickstart.mp4

# 3. Try example
cd examples/migration/
./migrate_simple_entity.sh

# 4. Implement first action
# Edit entities/tenant/my_entity.yaml

# 5. Generate and test
specql generate entities/tenant/my_entity.yaml
specql test entities/tenant/my_entity.yaml
```

---

## 📞 Support & Resources

### Documentation

All documentation in this directory:
- Executive summary (this directory)
- Implementation plan (this directory)
- Visual roadmap (this directory)
- GitHub issue (SpecQL repo)

### Related Resources

**SpecQL Framework**:
- Repository: https://github.com/fraiseql/specql
- Enhancement Issue: https://github.com/fraiseql/specql/issues/4
- Documentation: See SpecQL docs/

**PrintOptim Context**:
- Reference SQL: `../../../reference_sql/0_schema/03_functions/`
- Current entities: `../../../entities/`
- Analysis docs: `../../../docs/mutation_*`

### Questions?

- **Technical**: pattern-library@printoptim.com
- **Business**: Contact project stakeholders
- **GitHub**: https://github.com/fraiseql/specql/issues/4

---

## ✅ Next Steps

### For Stakeholders

1. Review **BUSINESS_LOGIC_LIBRARY.md**
2. Evaluate ROI and financial projections
3. Approve budget (~$260K) and timeline (20 weeks)
4. Assign Team C developers (2-3 people)

### For Project Managers

1. Review **BUSINESS_LOGIC_LIBRARY_ROADMAP.md**
2. Plan team assignments
3. Set up project infrastructure
4. Schedule kickoff meeting

### For Developers

1. Study **BUSINESS_LOGIC_LIBRARY_PLAN.md** (Phase 1)
2. Understand pattern architecture
3. Review reference SQL examples
4. Prepare development environment

### For Everyone

Stay tuned for updates as implementation progresses!

---

**Status**: 📋 **Planning Complete** - Ready for Implementation Review
**Created**: 2025-11-10
**Next Review**: [TBD]
