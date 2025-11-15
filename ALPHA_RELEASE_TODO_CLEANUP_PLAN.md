# SpecQL v0.4.0-alpha TODO Cleanup Plan

**Total TODO/FIXME Comments Found**: 131
**Date**: 2025-11-15
**Status**: Ready for Execution

Based on analysis of the codebase, here's the organized plan for cleaning up TODO comments before the alpha release.

---

## 📊 Summary Statistics

| Category | Count | Action | Time Estimate |
|----------|-------|--------|---------------|
| **Critical (Fix Now)** | ~8 | Fix immediately | 2-3 hours |
| **Important (Create Issues)** | ~85 | Create GitHub issues | 4-5 hours |
| **Remove (Outdated)** | ~25 | Delete comments | 1-2 hours |
| **Keep (Deferred)** | ~13 | Update format | 30 minutes |
| **Total** | **131** | | **7-10 hours** |

---

## 🚨 Critical (Fix Now) - 8 items

These are actual blockers that prevent core functionality from working properly.

### Core Generator Issues
- [ ] `src/generators/actions/action_orchestrator.py:75` - Support multiple actions per entity
  - **Impact**: Core functionality gap
  - **Action**: Implement multiple action support
  - **Estimated**: 30 minutes

- [ ] `src/generators/actions/step_compilers/insert_compiler.py:53` - Schema lookup for table names
  - **Impact**: Incorrect table references in generated SQL
  - **Action**: Implement proper schema resolution
  - **Estimated**: 15 minutes

- [ ] `src/generators/actions/impact_metadata_compiler.py:126` - Cross-schema support
  - **Impact**: Cannot generate code for multi-schema databases
  - **Action**: Add cross-schema relationship support
  - **Estimated**: 45 minutes

### Parser Issues
- [ ] `src/parsers/plpgsql/function_analyzer.py:64` - Table impact analysis
  - **Impact**: Incorrect dependency tracking
  - **Action**: Implement table impact analysis for functions
  - **Estimated**: 30 minutes

- [ ] `src/parsers/plpgsql/function_analyzer.py:214` - DELETE statement parsing
  - **Impact**: Cannot reverse engineer DELETE operations
  - **Action**: Add DELETE parsing support
  - **Estimated**: 45 minutes

### CLI Issues
- [ ] `src/cli/generate.py:48` - Convert impact dict to ActionImpact
  - **Impact**: Type safety issues in CLI
  - **Action**: Implement proper type conversion
  - **Estimated**: 15 minutes

### Security/API Key Issues
- [ ] `src/cicd/llm_recommendations.py:35` - Hardcoded API key placeholder
  - **Impact**: Security vulnerability
  - **Action**: Remove hardcoded key, use environment variables
  - **Estimated**: 10 minutes

---

## 🔧 Important (Create Issues) - 85 items

These are valuable enhancements that should be tracked as GitHub issues for post-alpha development.

### Action/Step Compilation (15 items)
- [ ] `src/generators/actions/action_orchestrator.py:94` - Compile validation steps
- [ ] `src/generators/actions/action_orchestrator.py:356` - Dynamic action type mapping
- [ ] `src/generators/actions/action_orchestrator.py:432` - Add other fields to insert
- [ ] `src/generators/actions/action_orchestrator.py:438` - Map input fields
- [ ] `src/generators/actions/action_orchestrator.py:461` - Add other fields to update
- [ ] `src/generators/actions/action_orchestrator.py:468` - Map input fields
- [ ] `src/generators/actions/action_orchestrator.py:508` - Map update fields
- [ ] `src/generators/actions/action_orchestrator.py:530` - Foreach compilation
- [ ] `src/generators/actions/action_orchestrator.py:544` - Function call compilation
- [ ] `src/generators/actions/action_orchestrator.py:558` - Notification compilation
- [ ] `src/generators/actions/callback_generator.py:148` - Insert step in callback
- [ ] `src/generators/actions/callback_generator.py:153` - Delete step in callback
- [ ] `src/generators/actions/step_compilers/update_compiler.py:79` - Handle commas in strings
- [ ] `src/generators/actions/success_response_generator.py:62` - Implement relationship handling
- [ ] `src/generators/core_logic_generator.py:412` - Proper call compilation

### Java/Spring Boot Generation (8 items)
- [ ] `src/generators/java/service_generator.py:121` - Add field setters
- [ ] `src/generators/java/service_generator.py:184` - Implement various step types
- [ ] `src/generators/java/service_generator.py:191` - Validation step without expression
- [ ] `src/generators/java/service_generator.py:210` - Update step without fields
- [ ] `tests/unit/generators/java/test_coverage_completion.py:45-166` - Multiple TODO assertions in tests

### Rust/Diesel Generation (5 items)
- [ ] `src/generators/rust/rust_generator_orchestrator.py:108` - Multiple entities support
- [ ] `src/parsers/rust/diesel_parser.py:238` - Convert actions
- [ ] `src/reverse_engineering/rust_parser.py:394` - Accept source code via stdin
- [ ] `src/reverse_engineering/rust_action_parser.py:154` - Mapping logic implementation
- [ ] `tests/integration/rust/test_integration_basic.py:55` - Default value parsing

### TypeScript/Prisma Generation (3 items)
- [ ] `src/generators/frontend/apollo_hooks_generator.py:234` - Job status polling/subscription
- [ ] `tests/integration/rust/test_performance.py:81` - Full serialization/deserialization

### Parser Improvements (10 items)
- [ ] `src/parsers/plpgsql/function_analyzer.py:253` - Complex expression inversions
- [ ] `src/parsers/plpgsql/plpgsql_parser.py:211` - Debug print cleanup
- [ ] `src/reverse_engineering/ast_to_specql_mapper.py:343` - Robust CTE parsing
- [ ] `src/reverse_engineering/ast_to_specql_mapper.py:430` - Expression extraction
- [ ] `src/reverse_engineering/ast_to_specql_mapper.py:440` - Type inference implementation
- [ ] `tests/integration/plpgsql/test_parser_integration.py:70` - Reference target parsing
- [ ] `tests/integration/fraiseql/test_mutation_annotations_e2e.py:87` - Mutation annotations
- [ ] `tests/integration/fraiseql/test_rich_type_autodiscovery.py:22` - Impact dict conversion

### CLI Enhancements (12 items)
- [ ] `src/cli/cicd.py:40` - Pipeline loading from YAML
- [ ] `src/cli/commands/check_codes.py:52` - Implement CLI command
- [ ] `src/cli/generate.py:850` - Metadata generation
- [ ] `src/cli/domain.py:31` - Add subdomain count to DTO
- [ ] `src/cli/domain.py:57` - Subdomain listing
- [ ] `src/cli/domain.py:94` - Re-implement with service layer
- [ ] `src/presentation/cli/domain.py:62` - Subdomain listing
- [ ] `src/presentation/graphql/resolvers.py:46` - Add createdAt to DTO

### CI/CD Pipeline Generation (8 items)
- [ ] `src/cicd/universal_pipeline_schema.py:58` - Platform-specific setup actions
- [ ] `src/cicd/universal_pipeline_schema.py:178` - GitHub Actions conversion
- [ ] `src/cicd/universal_pipeline_schema.py:183` - GitLab CI conversion
- [ ] `src/cicd/universal_pipeline_schema.py:188` - CircleCI conversion
- [ ] `src/cicd/universal_pipeline_schema.py:194` - GitHub Actions parsing
- [ ] `src/cicd/universal_pipeline_schema.py:200` - GitLab CI parsing

### Infrastructure & Performance (8 items)
- [ ] `src/infrastructure/repositories/postgresql_pattern_repository.py:176` - Filtering support
- [ ] `src/pattern_library/api.py:592` - Intelligent field merging
- [ ] `src/generators/core_logic_generator.py:832` - Find dependent entities
- [ ] `src/generators/function_generator.py:60` - Custom actions in core layer
- [ ] `src/generators/actions/function_scaffolding.py:84` - Action parameters support
- [ ] `tests/performance/test_parsing_performance.py:68-69` - Pattern detection stats
- [ ] `tests/unit/generators/test_composite_type_generator.py:374` - Step analysis for referenced fields

### Testing & Integration (8 items)
- [ ] `tests/integration/actions/test_database_roundtrip.py:386` - Core delete function parameters
- [ ] `tests/integration/actions/test_mutations_with_tv_refresh.py:237` - Success response generation
- [ ] `tests/integration/test_hex_hierarchical_generation.py:89` - Implement test
- [ ] `tests/integration/test_hex_hierarchical_generation.py:98` - Implement test
- [ ] `tests/integration/test_pattern_discovery.py:225` - Re-enable FraiseQL server test
- [ ] `tests/integration/test_team_b_integration.py:75` - Core logic for custom actions
- [ ] `tests/integration/test_team_b_integration.py:112` - Core logic for custom actions
- [ ] `tests/unit/infrastructure/test_semantic_search.py:14` - Update to use PatternEmbeddingService

---

## 🗑️ Remove (Outdated) - 25 items

These are debug prints, old TODOs, or comments that are no longer relevant.

### Debug Print Statements (18 items)
All of these should be removed as they're debug output that shouldn't be in production code:

- [ ] `src/cli/confiture_extensions.py:217-220` - DEBUG print statements
- [ ] `src/cli/orchestrator.py:48,162,189,193,196,216,218,252,264,268,270,274,557,782,784,818,830,834,836,840` - Multiple DEBUG prints
- [ ] `src/generators/app_schema_generator.py:16-21` - DEBUG print statements
- [ ] `src/generators/core_logic_generator.py:258` - DEBUG print
- [ ] `src/patterns/pattern_loader.py:115` - DEBUG print
- [ ] `tests/integration/actions/test_switch_return_early_compilation.py:83-95` - DEBUG prints
- [ ] `tests/integration/test_cascade_helpers_e2e.py:113-142` - DEBUG prints
- [ ] `tests/integration/test_e2e_new_development.py:235` - DEBUG print

### Outdated TODOs (7 items)
- [ ] `src/generators/schema/jobs_schema_generator.py:3` - Python 3.8 support drop (already done)
- [ ] `src/core/logging_config.py:14` - This is just a docstring, not a TODO
- [ ] `scripts/migrate_patterns_to_postgresql.py:226` - Debug logging, not a TODO

---

## 🔄 Keep (Deferred) - 13 items

These are legitimate future enhancements that should be clearly marked as post-alpha.

### Future Features (13 items)
- [ ] `src/cli/generate.py:850` - Metadata generation (nice-to-have)
- [ ] `src/generators/actions/action_orchestrator.py:356` - Dynamic action types (future enhancement)
- [ ] `src/generators/rust/rust_generator_orchestrator.py:108` - Multiple entities (future feature)
- [ ] `src/infrastructure/repositories/postgresql_pattern_repository.py:176` - Advanced filtering (performance optimization)
- [ ] `src/pattern_library/api.py:592` - Intelligent merging (future enhancement)
- [ ] `src/reverse_engineering/ast_to_specql_mapper.py:343,430,440` - Parser robustness (future improvement)
- [ ] `tests/integration/test_hex_hierarchical_generation.py:89,98` - Missing tests (can be added later)
- [ ] `tests/integration/rust/test_integration_basic.py:74` - Code generation tests (future integration)
- [ ] `tests/integration/test_pattern_discovery.py:225` - FraiseQL integration (marked as #alpha-followup)

---

## 🎯 Execution Plan

### Phase 1: Critical Fixes (2-3 hours)
1. Fix the 8 critical TODOs that block functionality
2. Test each fix to ensure it works
3. Commit with descriptive messages

### Phase 2: Issue Creation (4-5 hours)
1. Create GitHub issues for the 85 important TODOs
2. Use batch creation script for efficiency
3. Update TODO comments to reference issue numbers

### Phase 3: Cleanup (1-2 hours)
1. Remove all 25 outdated debug prints and old TODOs
2. Test that removals don't break functionality

### Phase 4: Documentation (30 minutes)
1. Update the 13 deferred TODOs with clearer post-alpha wording
2. Add issue references where applicable

---

## 📈 Success Criteria

- [ ] All critical TODOs fixed and tested
- [ ] GitHub issues created for important enhancements
- [ ] No debug prints in production code
- [ ] All remaining TODOs clearly marked as deferred
- [ ] Tests still pass after all changes
- [ ] Code quality checks still pass

---

## 🚀 Post-Cleanup Benefits

1. **Clean Release**: Alpha release with professional code quality
2. **Clear Roadmap**: GitHub issues provide transparent development roadmap
3. **Community Ready**: No confusing debug output or outdated comments
4. **Maintainable**: Clear distinction between current functionality and future plans

---

## 📋 GitHub Issue Template

When creating issues for the "Important" category, use this template:

```markdown
**Location**: src/file.py:123
**Current TODO**: [paste the TODO comment]
**Description**: [brief description of the enhancement]
**Priority**: Low/Medium/High
**Component**: [Core/Generators/Parsers/CLI/Tests/etc.]
**Version**: Post-alpha
**Effort**: [Small/Medium/Large]
```

---

**Total Estimated Time**: 7-10 hours
**Priority Order**: Critical → Remove → Issues → Deferred
**Risk Level**: Low (mostly mechanical work)