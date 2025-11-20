# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation
- **Comprehensive Documentation Cleanup** - Zero broken links achieved
  - **Phase 1-2**: Audited and categorized 63+ broken links across 13 files
  - **Phase 3-4**: Consolidated duplicate directories, removed obsolete content
  - **Phase 5**: Fixed critical navigation links in root documentation files
  - **Phase 6-7**: Archived historical documentation, updated active references
  - **Phase 8**: Created 4 missing index.md files, added consistent breadcrumbs
  - **Phase 9**: Enhanced 6+ Related Documentation sections with 90+ cross-references
  - **Phase 10**: Achieved 100% link integrity (660 links validated across 218 files)
  - **Result**: Production-ready documentation with comprehensive navigation

## [0.8.0] - 2025-11-20

### Fixed
- **Critical Issue #1**: Package installation completely broken - FIXED
  - Resolved import path issues (`from src.cli.*` → `from cli.*`)
  - Updated pyproject.toml package structure
  - CLI commands now work after `pip install specql`

- **Critical Issue #2**: Missing fields in reverse engineering - FIXED
  - All Django field types now extracted (IntegerField, PositiveIntegerField, etc.)
  - Reserved framework fields properly filtered out (created_at, updated_at, etc.)
  - Comprehensive field type mapping for Django models

- **Critical Issue #3**: Multiple models not detected - FIXED
  - AST traversal now processes ALL classes in a file
  - Multi-model Django files generate separate YAML files
  - Improved class filtering logic

- **Critical Issue #4**: Pattern detection completely fails - FIXED
  - Audit trail pattern detection working (created_at/updated_at)
  - State machine pattern detection functional
  - Soft delete pattern recognition implemented

- **Critical Issue #5**: Validation errors on generated YAML - FIXED
  - Generated SpecQL YAML now passes validation
  - Action step formats corrected
  - Schema compatibility ensured

- **Critical Issue #6**: Code generation completely broken - FIXED
  - Template packaging resolved
  - SQL generation works for valid entities
  - Foundation and entity schemas generate correctly

- **Critical Issue #7**: Pattern import error - FIXED
  - Related to package structure fixes
  - All imports work correctly after installation

### Added
- **Reserved Field Filtering**: Reverse engineering automatically excludes framework-reserved fields
- **Rich Metadata**: Generated YAML includes source language, file path, generation timestamp, and pattern detection results
- **Enhanced CLI Output**: Progress indicators and clear success/error messaging

### Changed
- **Version**: Bumped to 0.8.0 for production release
- **Package Structure**: Flattened import paths for better packaging

## [0.6.0] - 2025-11-17

### Added
- **FraiseQL Compatibility**: Complete migration from single-line to YAML comment format
  - All PostgreSQL comments now use `@fraiseql:` YAML annotations
  - Composite types: `@fraiseql:composite` with YAML metadata
  - Functions: `@fraiseql:mutation` with input/output type specifications
  - Fields: `@fraiseql:field` with GraphQL type mappings
  - Enables automatic GraphQL schema generation from database metadata

### Changed
- **Delete Actions**: Now generate input types with `id` field for consistent API
- **App Wrappers**: All actions use composite types for JSONB → Typed conversion
- **Schema Generation**: Unified YAML comment format across all generated SQL

### Fixed
- **Input Type Generation**: Delete actions now properly generate `app.type_*_input` types
- **App Wrapper Logic**: Correct parameter passing for delete operations
- **Test Coverage**: Updated unit tests to reflect new delete action behavior

## [0.5.0] - 2025-11-17

### Changed
- **BREAKING**: Renamed PyPI package from `specql-generator` to `specql`
  - Old: `pip install specql-generator`
  - New: `pip install specql`
  - Migration: `pip uninstall specql-generator && pip install specql`
  - The `specql-generator` package is deprecated and will not receive updates
  - Rationale: Simpler installation, aligns with CLI command name, better branding

### Fixed
- **Frontend Generation** - Resolved `UnboundLocalError` in CLI generate command due to duplicate Path import
- **Database Integration Tests** - Enhanced test fixture to automatically deploy schema and functions
- **Test Suite** - Achieved 100% test pass rate (1127 passed, 0 failed)

### Changed
- **Test Infrastructure** - Improved database fixture to check for function existence, not just schema
- **Documentation** - Updated TEST_FAILURE_FIX_PLAN.md with comprehensive fix details

### Summary
This stable release fixes all remaining test failures from v0.5.0b1, achieving production-ready quality with:
- ✅ 100% test pass rate (1127/1127 tests passing)
- ✅ All code quality checks passing
- ✅ Comprehensive security test suite
- ✅ Production-ready PostgreSQL + GraphQL code generation

## [0.5.0b1] - 2025-11-17

### Added
- **Security Test Suite** - Comprehensive security testing for SQL injection, SSRF, and template injection
- **Performance Monitoring** - Performance monitoring in code generation pipeline
- **Logging Framework** - Comprehensive logging across all modules
- **CLI Test Coverage** - Increased CLI test coverage to 97%+

### Fixed
- MyPy type errors with None iteration issues
- Variable name conflicts in type annotations
- Pre-commit configuration to use specific type stubs

### Added (from v0.1.0)
- Initial SemVer and GitHub versioning system

## [0.1.0] - 2025-11-10

### Added
- ✅ **Team A: SpecQL Parser** - Complete YAML to AST parsing
  - Entity definitions with fields (text, integer, ref, enum, list, rich types)
  - Action definitions with multi-step business logic
  - Impact declarations for mutation side effects
  - Table views and hierarchical identifiers

- ✅ **Team B: Schema Generator** - PostgreSQL DDL generation
  - Trinity Pattern: `pk_*` (INTEGER PK), `id` (UUID), `identifier` (TEXT)
  - Automatic naming conventions: `tb_{entity}`, `fk_{entity}`
  - Audit fields: `created_at`, `updated_at`, `deleted_at`
  - Auto-indexes for FK columns, enums, tenant_id
  - Composite type support for rich types (money, dimensions, contact_info)
  - Multi-tenant schema registry with configurable tiers

- ✅ **Team C: Action Compiler** - PL/pgSQL function generation
  - FraiseQL Standard: Returns `app.mutation_result` type
  - Trinity resolution: Auto-convert UUID → INTEGER
  - Audit updates: Auto-update `updated_at`, `updated_by`
  - Full object returns with complete entity data
  - Impact metadata with runtime `_meta` tracking
  - Step compilers: validate, if/then, insert, update, call, notify, foreach

- ✅ **Team D: FraiseQL Metadata** - GraphQL discovery support
  - SQL comments with `@fraiseql:*` annotations
  - Mutation impact metadata JSON for frontends
  - TypeScript type definitions
  - Apollo hooks generation
  - Auto-generated documentation

- ✅ **Team E: CLI & Orchestration** - Confiture integration
  - `specql generate` - Generate schema from YAML
  - `specql validate` - Validate YAML syntax
  - `specql diff` - Show schema differences
  - Full test suite: 439 passing tests

### Core Features
- **100x Leverage**: 20 lines YAML → 2000+ lines production code
- **Zero Boilerplate**: Users write ONLY business domain
- **Production Ready**: Complete PostgreSQL + GraphQL API generation
- **Type Safe**: Full TypeScript integration
- **Test Coverage**: Comprehensive unit and integration tests

### Documentation
- Complete architecture documentation
- Getting started guide
- Team-by-team implementation guide
- Integration proposal with FraiseQL conventions

[unreleased]: https://github.com/fraiseql/specql/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/fraiseql/specql/releases/tag/v0.5.0
[0.5.0b1]: https://github.com/fraiseql/specql/releases/tag/v0.5.0b1
[0.1.0]: https://github.com/fraiseql/specql/releases/tag/v0.1.0
