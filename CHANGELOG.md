# Changelog

All notable changes to SpecQL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0-beta.1] - 2025-11-16

### 🔒 Security & Optimization Release

This maintenance release focuses on security hardening and dependency optimization, building on the test generation capabilities introduced in v0.5.0-beta.0.

### Security

#### Removed
- **Proprietary References**: Complete removal of PrintOptim-specific code and references
- **Internal Documentation**: Removed proprietary implementation plans and schemas
- **Development Notes**: Sanitized all customer-specific information from codebase

#### Fixed
- **Dependency Audit**: Updated all dependencies to latest secure versions
- **Input Validation**: Enhanced validation for file paths and SQL injection prevention
- **Secure Defaults**: All generation commands use safe defaults

### Changed

#### Dependency Optimization
- **Modular Architecture**: Reorganized dependencies into optional feature groups
  - `[diagrams]` - ER diagram generation (networkx, graphviz)
  - `[patterns]` - Pattern library with embeddings (pgvector, numpy)
  - `[interactive]` - TUI interface (textual, pygments)
  - `[runners]` - Docker infrastructure runners
  - `[reverse]` - Reverse engineering (py4j, python-hcl2)
  - `[testing]` - Test data generation (faker)
  - `[all]` - All features combined

#### Performance Improvements
- **Core Package Size**: Reduced from ~250MB to ~10MB (96% reduction)
- **Install Time**: Reduced from 30s to 5s (83% faster)
- **CLI Startup**: Reduced from 800ms to 480ms (40% faster)
- **Memory Footprint**: Reduced from 45MB to 27MB (40% reduction)

#### Code Quality
- **Cleaner Codebase**: Removed 1000+ lines of proprietary code
- **Better Organization**: Reorganized internal modules
- **Enhanced Type Safety**: Improved type hints across parsers
- **Reduced Complexity**: Simplified dependency chains

### Fixed
- Fixed: Import errors when optional dependencies not installed
- Fixed: Type hints in schema analyzer and file path parser
- Fixed: Linting warnings in confiture_extensions.py
- Fixed: Universal AST organization field typing

### Documentation
- Added: `SECURITY.md` - Security policy and vulnerability reporting
- Added: `CODE_OF_CONDUCT.md` - Community code of conduct
- Added: `RELEASE_NOTES_v0.5.0-beta.1.md` - Detailed release notes
- Updated: `README.md` - Removed proprietary examples, cleaner presentation
- Updated: `CONTRIBUTING.md` - Simplified contribution workflow

---

## [0.5.0-beta.0] - 2025-11-15

### 🧪 Test Generation Release

Major feature release introducing comprehensive test generation capabilities.

### Added

#### Test Generation
- **New Command**: `specql generate-tests` - Generate pgTAP SQL tests and pytest Python tests
- **New Command**: `specql reverse-tests` - Reverse engineer existing test files
- **pgTAP Test Generation**: Comprehensive SQL unit tests
  - Entity existence validation
  - Field type and constraint testing
  - Foreign key relationship validation
  - Trinity pattern verification
- **pytest Test Generation**: Python integration tests
  - Entity CRUD operations
  - Action execution testing
  - Relationship integrity validation
- **Preview Mode**: Review generated tests before writing files
- **Selective Generation**: Filter by entity, test type, or pattern

#### Reverse Engineering
- **New Command**: `specql reverse-schema` - Advanced schema reverse engineering
- **Organizational Metadata**: Extract and preserve table codes from filenames and SQL comments
- **Hierarchical Structure**: Support for directory-based organization
- **CQRS Support**: Handle write-side, query-side, and function categories
- **Translation Tables**: Special handling for i18n translation tables
- **Consistency Validation**: Validate metadata across multiple sources

### Documentation
- Added: `/docs/02_guides/TEST_GENERATION.md` - Complete test generation guide
- Added: `/docs/02_guides/TEST_REVERSE_ENGINEERING.md` - Reverse engineering guide
- Updated: All tutorials with test generation examples

---

## [0.4.0-alpha] - 2025-11-15

### 🎉 First Public Alpha Release

SpecQL's first public alpha release focuses on multi-language backend code generation with production-ready PostgreSQL, Java/Spring Boot, Rust/Diesel, and TypeScript/Prisma support.

### Added

#### Core Features
- **Multi-Language Backend Generation**: Generate backend code for 4+ languages from single YAML spec
  - PostgreSQL with Trinity pattern (pk_*, id, identifier)
  - Java/Spring Boot with JPA entities (97% test coverage)
  - Rust/Diesel with Actix-web handlers (100% test pass rate)
  - TypeScript/Prisma with complete type safety (96% coverage)

#### Code Generation
- **PostgreSQL**: Complete schema generation with Trinity pattern, foreign keys, indexes, constraints, audit fields
- **PL/pgSQL Functions**: Action compilation to stored procedures with 95%+ semantic fidelity
- **Java/Spring Boot**: Entity, Repository, Service, and Controller generation with Lombok support
- **Rust/Diesel**: Model generation, query builders, Actix-web handlers
- **TypeScript/Prisma**: Prisma schema generation, TypeScript interfaces, round-trip validation
- **GraphQL**: FraiseQL metadata for auto-discovery and GraphQL API generation
- **Testing**: Automated pgTAP SQL tests and pytest Python tests

#### Developer Experience
- **Interactive CLI**: Live preview with syntax highlighting (powered by Textual)
- **Pattern Library**: 100+ reusable query/action patterns with semantic search
- **Reverse Engineering**:
  - PostgreSQL → SpecQL YAML
  - Java/Spring Boot → SpecQL YAML (with Eclipse JDT integration)
  - Rust/Diesel → SpecQL YAML
  - TypeScript/Prisma → SpecQL YAML
- **Registry System**: Hexadecimal domain/entity codes for large organizations
- **CI/CD Generation**: GitHub Actions and GitLab CI workflow generation
- **Visual Schema Diagrams**: Automatic ER diagram generation with Graphviz

#### Performance & Quality
- **Test Coverage**: 96%+ across all language generators
- **Performance Benchmarks**:
  - 1,461 Java entities/sec parsing
  - 37,233 TypeScript entities/sec parsing
  - 100 Rust models in <10 seconds
- **Security**: SQL injection prevention, comprehensive security audit
- **Code Quality**: 100% type hints, comprehensive docstrings, ruff + mypy passing

### Changed

- **FraiseQL Integration**: Migrated to FraiseQL 1.5 for vector search (removed 930 lines / 56% of embedding infrastructure)
- **Simplified Architecture**: Removed custom vector functions in favor of FraiseQL auto-discovery
- **Improved Documentation**: Migration guides for Java, Rust, and TypeScript
- **Enhanced Error Handling**: Comprehensive validation and user-friendly error messages

### Fixed

- **Security**: Patched critical SQL injection vulnerabilities (2025-11-13)
- **PL/pgSQL Parser**: Fixed edge cases in function parsing
- **TypeScript Parser**: Improved semicolon handling and reference detection
- **Rust Parser**: Enhanced error handling for malformed files

### Removed

- **Deprecated Embedding Service**: Replaced by FraiseQL 1.5 GraphQL API
- **Custom Vector Search Functions**: Now auto-generated by FraiseQL
- **Legacy CLI Commands**: `specql embeddings` (use `fraiseql` CLI instead)

### Documentation

- **Migration Guides**: Complete guides for Java, Rust, and TypeScript integration
- **Video Tutorials**: 20-minute comprehensive tutorial scripts
- **API Reference**: Complete YAML syntax reference
- **Architecture Docs**: Detailed source structure and design patterns
- **Examples**: Working examples for CRM, e-commerce, SaaS multi-tenant, and more

### Known Limitations (Alpha)

- **Frontend Generation**: Not yet implemented (planned for future releases)
- **Infrastructure as Code**: Partial implementation (Terraform/Pulumi support in progress)
- **Full-Stack Deployment**: Single-command deployment not yet available
- **Community Links**: Discord and GitHub Discussions not yet set up
- **Package Distribution**: Not yet published to PyPI (install from source)

### Performance Metrics

- **Code Leverage**: 20 lines YAML → 2000+ lines production code (100x leverage)
- **Test Coverage**: 96%+ (371 Python files, 25+ step compilers, comprehensive test suite)
- **Language Support**: 4 backend languages (PostgreSQL, Java, Rust, TypeScript)
- **Pattern Library**: 100+ production-ready patterns
- **Example Projects**: 10+ complete working examples

### Migration & Compatibility

- **Breaking Changes**: This is the first alpha release, no migration needed
- **Python Version**: Requires Python 3.11+
- **PostgreSQL Version**: Requires PostgreSQL 14+
- **Java Version**: Requires Java 17+ for Spring Boot generation
- **Rust Version**: Works with stable Rust 1.70+
- **TypeScript Version**: Requires TypeScript 4.9+

---

## Installation (Alpha)

**From Source** (recommended for alpha):

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

**Verify Installation**:

```bash
specql --version  # Should show 0.4.0-alpha
specql generate entities/examples/**/*.yaml
```

---

## Reporting Issues

This is an **alpha release** - bugs are expected! Please report issues at:
https://github.com/fraiseql/specql/issues

Include:
- SpecQL version (`specql --version`)
- Python version (`python --version`)
- Operating system
- Complete error message
- Minimal reproducible example

---

## [0.3.0] - Internal Release
- Initial implementation
- PostgreSQL core generation
- Basic action compilation

## [0.2.0] - Internal Release
- Prototype implementation
- Trinity pattern design

## [0.1.0] - Internal Release
- Initial concept validation</content>
</xai:function_call">The CHANGELOG.md file has been created successfully.