# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Automatic GraphQL Cascade Support**: SpecQL now automatically generates cascade data
  in `mutation_result.extra_metadata._cascade` for all actions with impact metadata.
  This enables FraiseQL to automatically update GraphQL client caches.
  - Zero configuration required
  - Works with all existing actions that have impact metadata
  - Includes primary entity and all side effects
  - Backward compatible
  - PostgreSQL helper functions: `app.cascade_entity()`, `app.cascade_deleted()`
- Production-ready example with CRM entities
- Comprehensive test suite with >95% coverage
- CI/CD pipeline with GitHub Actions
- Structured logging support
- Custom exception classes with helpful error messages
- Semantic versioning setup

### Changed
- Documentation updated to use flexible metrics
- Repository cleaned to <50MB
- Improved error handling and logging infrastructure

### Fixed
- Missing `faker` test dependency
- Test collection errors

## [0.2.0] - 2025-11-11

### Changed
- First public PyPI release
- Repository cleaned for public consumption
- Documentation updated for PyPI users

### Added
- PyPI metadata and classifiers
- Installation instructions via pip/uv

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

[unreleased]: https://github.com/fraiseql/specql/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/fraiseql/specql/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fraiseql/specql/releases/tag/v0.1.0
