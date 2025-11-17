# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[unreleased]: https://github.com/fraiseql/specql/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fraiseql/specql/releases/tag/v0.1.0
