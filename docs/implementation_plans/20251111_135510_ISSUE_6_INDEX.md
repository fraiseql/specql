# Issue #6: Subdomain Parsing Bug - Documentation Index

**Issue**: [#6 - Hierarchical generator incorrectly parses table_code subdomain](https://github.com/evoludigit/specql/issues/6)
**Status**: Ready for Implementation
**Priority**: HIGH
**Created**: 2025-11-11

---

## Quick Links

### For Developers

1. **[Quick Reference Card](./issue_6_quick_reference.md)** ⚡
   - One-page cheat sheet
   - Code examples
   - TDD workflow
   - Common pitfalls
   - **Start here for fast implementation**

2. **[Snake_case Conversion Examples](./issue_6_snake_case_examples.md)** 🔤 **NEW**
   - How entity names convert (ColorMode → color_mode)
   - Real-world PrintOptim examples
   - Edge cases (Product2B → product_2_b)
   - Why snake_case?
   - **Essential for Phase 4.5**

3. **[Visual Guide](./issue_6_visual_guide.md)** 📊
   - Diagrams and visualizations
   - Before/after comparisons
   - Code diff highlights
   - Directory structure examples
   - **Best for visual learners**

### For Planning

4. **[Executive Summary](./issue_6_executive_summary.md)** 📋
   - 30-second problem statement
   - Solution overview
   - Risk assessment
   - Success criteria
   - **For managers and stakeholders**

5. **[Phase 4.5: Snake_case Detailed Plan](./issue_6_phase_4_5_naming.md)** 🔧 **NEW**
   - Complete TDD cycles for naming conversion
   - Utility function implementation
   - Test cases and validation
   - **Required for Phase 4.5 implementation**

6. **[Full Implementation Plan](./issue_6_subdomain_parsing_fix.md)** 📚
   - Complete 6-phase TDD approach
   - Detailed RED/GREEN/REFACTOR cycles
   - Test cases and validation
   - Documentation updates
   - **For detailed implementation**

---

## The Bug in 30 Seconds

```
❌ Current:  subdomain = table_code[3:5]  # "013111"[3:5] = "11"
✅ Correct:  subdomain = table_code[3]    # "013111"[3] = "1"
```

**Impact**: Directory structure wrong (generic names, split entities)
**Fix**: 3 files, ~80 lines, 6 TDD phases
**Risk**: LOW (no SQL changes)

---

## Document Overview

### 1. Quick Reference (1 page)
**Use when**: You're ready to code and need quick lookup
```
├── The Bug (code snippet)
├── Table Code Format
├── Files to Change (with code)
├── Test Examples
├── TDD Workflow
└── Validation Checklist
```

### 2. Visual Guide (diagrams)
**Use when**: You need to understand the structure visually
```
├── Table Code Breakdown (diagram)
├── Current vs Correct Parsing (side-by-side)
├── Directory Structure (tree view)
├── Code Changes (diff view)
├── Registry Lookup Flow
└── Phase-by-Phase Visual
```

### 3. Executive Summary (2 pages)
**Use when**: You need to explain the issue to others
```
├── Problem Statement
├── Root Cause
├── Impact Analysis
├── Solution Overview
├── 6-Phase Summary
├── Risk Mitigation
└── Success Criteria
```

### 4. Implementation Plan (15 pages)
**Use when**: You're implementing the fix step-by-step
```
├── Executive Summary
├── Table Code Format Analysis
├── Domain Registry Structure
├── Phase 1: Fix Parser
├── Phase 2: Fix Path Generation
├── Phase 3: Fix Registration
├── Phase 4: Integration Testing
├── Phase 5: Backward Compatibility
├── Phase 6: Documentation
├── Testing Strategy
└── Timeline Estimate
```

---

## Implementation Workflow

### Step 1: Understand the Problem
1. Read **[Executive Summary](./issue_6_executive_summary.md)** (5 min)
2. Review **[Visual Guide](./issue_6_visual_guide.md)** (10 min)
3. Understand table code format and directory structure

### Step 2: Plan Your Approach
1. Read **[Full Implementation Plan](./issue_6_subdomain_parsing_fix.md)** (30 min)
2. Review all 6 phases
3. Understand TDD cycles

### Step 3: Implement
1. Keep **[Quick Reference](./issue_6_quick_reference.md)** open (constant)
2. Follow phases 1-6 in order
3. Use TDD workflow: RED → GREEN → REFACTOR → QA
4. Check validation checklist after each phase

### Step 4: Validate
1. Run full test suite
2. Verify success criteria
3. Test with PrintOptim scenario
4. Update documentation

---

## File Map

```
docs/implementation_plans/
├── ISSUE_6_INDEX.md                     ← You are here
├── issue_6_executive_summary.md         ← 2-page overview
├── issue_6_quick_reference.md           ← 1-page cheat sheet
├── issue_6_visual_guide.md              ← Diagrams & visuals
└── issue_6_subdomain_parsing_fix.md     ← Full 15-page plan
```

---

## Key Files to Change

### Source Code (3 files)
1. `src/numbering/numbering_parser.py` (~20 lines)
   - Add `subdomain_code` field
   - Add `entity_sequence` field
   - Use new field names

2. `src/generators/schema/naming_conventions.py` (~30 lines)
   - Fix `generate_file_path()` subdomain extraction
   - Fix `register_entity_auto()` subdomain code
   - Look up subdomain names from registry

### Tests (3 files)
3. `tests/unit/numbering/test_numbering_parser.py` (add tests)
4. `tests/unit/registry/test_naming_conventions.py` (add tests)
5. `tests/integration/test_issue_6_subdomain_parsing.py` (new file)

### Documentation (3 files)
6. `docs/architecture/NUMBERING_SYSTEMS_VERIFICATION.md` (update)
7. `docs/migration/issue_6_subdomain_fix.md` (new)
8. `README.md` (update examples)

---

## Testing Commands

```bash
# Phase 1: Parser tests
uv run pytest tests/unit/numbering/test_numbering_parser.py -v

# Phase 2: Path generation tests
uv run pytest tests/unit/registry/test_naming_conventions.py -v

# Phase 4: Integration tests
uv run pytest tests/integration/test_issue_6_subdomain_parsing.py -v

# Full suite
uv run pytest --tb=short
```

---

## Success Criteria Checklist

### Must Have ✅
- [ ] Parser extracts single-digit subdomain
- [ ] Path generation uses 4-digit subdomain directory
- [ ] Subdomain names from registry (not generic)
- [ ] Same-subdomain entities share directory
- [ ] All tests pass
- [ ] No SQL changes (backward compatible)

### Nice to Have 📋
- [ ] Deprecation warnings for old field names
- [ ] Migration guide published
- [ ] Documentation updated
- [ ] CLI help text improved

---

## Timeline

| Phase | Time | Status |
|-------|------|--------|
| Phase 1: Parser | 1-2 hours | ⏳ Pending |
| Phase 2: Path Gen | 2-3 hours | ⏳ Pending |
| Phase 3: Registration | 1-2 hours | ⏳ Pending |
| Phase 4: Integration | 2-3 hours | ⏳ Pending |
| Phase 5: Compatibility | 1-2 hours | ⏳ Pending |
| Phase 6: Documentation | 2-3 hours | ⏳ Pending |
| **Total** | **9-15 hours** | |

---

## Questions & Answers

**Q: Will this break my existing database?**
A: No - SQL generation is unchanged. Only directory structure is affected.

**Q: Do I need to migrate existing code?**
A: Only if you're using `--output-format hierarchical`. Confiture format is unaffected.



**Q: When will this be fixed?**
A: Target: v0.2.1 release. Implementation ready, awaiting execution.

**Q: Can I help?**
A: Yes! Follow the implementation plan and submit a PR.

---

## Related Issues

- [Issue #1: Hex hierarchical generation with explicit codes](https://github.com/evoludigit/specql/issues/1) - Related registry validation
- [Issue #2: Hierarchical output CLI flag](https://github.com/evoludigit/specql/issues/2) - Original feature request

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-11 | 1.0 | Initial documentation created |

---

## Support

- **GitHub Issue**: https://github.com/evoludigit/specql/issues/6
- **Full Context**: See PrintOptim migration analysis in issue
- **Questions**: Comment on the GitHub issue

---

**Status**: 📝 Documentation Complete, ⏳ Implementation Pending
**Last Updated**: 2025-11-11
**Next Step**: Begin Phase 1 (Parser Fix)

---

*Choose your path:*
- 🚀 **Quick Start**: [Quick Reference](./issue_6_quick_reference.md)
- 📊 **Understand Visually**: [Visual Guide](./issue_6_visual_guide.md)
- 📋 **Brief Overview**: [Executive Summary](./issue_6_executive_summary.md)
- 📚 **Full Details**: [Implementation Plan](./issue_6_subdomain_parsing_fix.md)
