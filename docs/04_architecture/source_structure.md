# Source Code Structure

**SpecQL's 24-directory architecture** - Organized for maintainability and extensibility

SpecQL's source code is organized into a clean, modular architecture that separates concerns while maintaining clear boundaries between components. This document provides a comprehensive overview of the codebase structure.

## 📊 High-Level Overview

```
src/
├── agents/                    # AI/ML agents for enhanced functionality
├── application/               # Application services and business logic
├── domain/                    # Domain models and business rules
├── generators/                # Code generation engines
├── parsers/                   # Language-specific parsers
├── patterns/                  # Reusable pattern library
├── registry/                  # Service registration system
├── reverse_engineering/       # Import from existing codebases
├── testing/                   # Test generation and utilities
└── utils/                     # Shared utilities
```

**Total**: 9 top-level directories, 24+ subdirectories, 100+ Python files

## 🤖 agents/

**AI/ML-powered enhancements**

```
agents/
├── __init__.py
```

**Purpose**: AI agents for intelligent code analysis, pattern recognition, and automated enhancements.

**Current Status**: Framework for future AI integrations
**Future Plans**: Code review agents, pattern suggestion, optimization recommendations

## 🏢 application/

**Application services and business logic**

```
application/
├── dtos/                      # Data Transfer Objects
│   ├── __init__.py
│   ├── domain_dto.py         # Domain data structures
├── services/                  # Business service layer
│   ├── domain_service.py     # Domain operations
│   ├── domain_service_factory.py
│   ├── pattern_deduplicator.py
│   ├── pattern_matcher.py    # Pattern matching logic
│   ├── pattern_service.py    # Pattern management
│   ├── pattern_service_factory.py
│   ├── subdomain_service.py  # Subdomain handling
│   └── template_service.py   # Template processing
├── __init__.py
└── exceptions.py              # Application exceptions
```

**Purpose**: Business logic services that orchestrate domain operations and pattern applications.

**Key Components**:
- **Domain Services**: Core business operations
- **Pattern Services**: Pattern matching and application
- **DTOs**: Data transfer between layers

## 🎯 domain/

**Domain models and business rules**

```
domain/
├── entities/                  # Domain entities
│   ├── __init__.py
│   ├── domain.py             # Domain model
│   ├── entity_template.py    # Entity templates
│   └── pattern.py            # Pattern definitions
├── repositories/              # Data access layer
│   ├── __init__.py
│   ├── domain_repository.py  # Domain data access
│   ├── entity_template_repository.py
│   └── pattern_repository.py # Pattern storage
├── value_objects/             # Value objects
│   └── __init__.py
└── __init__.py
```

**Purpose**: Domain-driven design implementation with entities, value objects, and repositories.

**Architecture**: Clean Architecture with domain at the center
**Pattern**: Repository pattern for data access abstraction

## ⚙️ generators/

**Code generation engines**

```
generators/
├── diagrams/                  # Visual diagram generation
│   ├── dependency_graph.py   # Dependency visualization
│   ├── graphviz_generator.py # GraphViz output
│   ├── html_viewer_generator.py
│   ├── mermaid_generator.py  # Mermaid diagrams
│   └── relationship_extractor.py
├── fraiseql/                  # GraphQL generation
│   ├── __init__.py
│   ├── compatibility_checker.py
│   ├── fraiseql_annotator.py # GraphQL annotations
│   ├── mutation_annotator.py # Mutation metadata
│   └── table_view_annotator.py
├── __init__.py
├── app_schema_generator.py   # Application schema generation
├── core_logic_generator.py   # Business logic generation
└── sql_utils.py              # SQL generation utilities
```

**Purpose**: Multi-language, multi-framework code generation.

**Supported Outputs**:
- **PostgreSQL**: Tables, functions, views
- **GraphQL**: Schemas, resolvers, metadata
- **TypeScript**: Types, hooks, utilities
- **Diagrams**: ERDs, dependency graphs

## 📝 parsers/

**Language-specific parsers**

```
parsers/
├── java/                      # Java parsing
│   ├── __init__.py
│   └── spring_boot_parser.py # Spring Boot code parsing
└── __init__.py
```

**Purpose**: Parse existing codebases for reverse engineering and migration.

**Supported Languages**:
- **Java**: Spring Boot applications
- **Future**: Python Django, Ruby on Rails, etc.

## 🎨 patterns/

**Reusable pattern library**

```
patterns/
├── aggregation/               # Data aggregation patterns
│   ├── boolean_flags.py      # Boolean flag aggregations
│   ├── count_aggregation.py  # Count operations
│   ├── hierarchical_count.py # Tree counting
│   └── utils.py
├── assembly/                  # Object assembly patterns
│   ├── __init__.py
│   ├── simple_aggregation.py
│   └── tree_builder.py
├── hierarchical/              # Hierarchical data patterns
│   ├── __init__.py
│   ├── flattener.py          # Tree flattening
│   ├── path_expander.py      # Path expansion
│   └── utils.py
├── localization/              # Internationalization
│   ├── __init__.py
│   └── translation_utils.py
├── metrics/                   # KPI and metrics patterns
│   ├── __init__.py
│   ├── kpi_builder.py
│   └── kpi_calculator.py
├── polymorphic/               # Polymorphic associations
│   ├── __init__.py
│   └── type_resolver.py
├── security/                  # Security patterns
│   ├── __init__.py
│   └── permission_checker.py
├── temporal/                  # Time-based patterns
│   ├── __init__.py
│   └── temporal_utils.py
├── wrapper/                   # Wrapper/decorator patterns
│   ├── __init__.py
│   ├── complete_set.py
│   ├── mv_refresh.py         # Materialized view refresh
│   └── utils.py
├── __init__.py
├── analytics.py              # Analytics patterns
├── migration_analyzer.py     # Migration analysis
├── migration_cli.py          # Migration CLI tools
├── pattern_loader.py         # Pattern loading system
├── pattern_models.py         # Pattern data models
└── pattern_registry.py       # Pattern registration
```

**Purpose**: Comprehensive library of reusable business logic patterns.

**Pattern Categories**:
- **CRUD**: Create, Read, Update, Delete operations
- **State Machines**: Status transitions and workflows
- **Queries**: Common data access patterns
- **Aggregations**: Data summarization and analytics
- **Hierarchical**: Tree structures and relationships
- **Temporal**: Time-based operations
- **Security**: Authorization and permission patterns

## 📋 registry/

**Service registration system**

```
registry/
├── __init__.py
└── service_registry.py        # Service registration
```

**Purpose**: Dependency injection and service location system.

**Features**:
- Service registration and discovery
- Factory pattern implementation
- Plugin system support

## 🔄 reverse_engineering/

**Import from existing codebases**

```
reverse_engineering/
├── java/                      # Java reverse engineering
│   └── jpa_visitor.py        # JPA entity analysis
├── tests/                     # Test parsing
│   ├── pgtap_test_parser.py  # pgTAP test analysis
│   └── pytest_test_parser.py # pytest analysis
├── __init__.py
├── ai_enhancer.py            # AI-powered enhancements
├── grok_provider.py          # Grok AI integration
├── python_ast_parser.py      # Python AST parsing
├── python_statement_analyzer.py
└── python_to_specql_mapper.py # Python to SpecQL mapping
```

**Purpose**: Import existing applications into SpecQL YAML format.

**Supported Sources**:
- **Java**: JPA entities, Spring Boot applications
- **Python**: Django models, SQLAlchemy
- **Tests**: pgTAP, pytest test analysis
- **AI**: Enhanced reverse engineering with AI

## 🧪 testing/

**Test generation and utilities**

```
testing/
├── metadata/                  # Test metadata generation
│   ├── __init__.py
│   ├── group_leader_detector.py
│   └── metadata_generator.py
├── pytest/                    # pytest generation
│   ├── __init__.py
│   └── pytest_generator.py
├── seed/                      # Test data generation
│   ├── __init__.py
│   ├── field_generators.py   # Field value generation
│   ├── fk_resolver.py        # Foreign key resolution
│   ├── seed_generator.py     # Test data seeding
│   ├── sql_generator.py      # SQL test data
│   └── uuid_generator.py     # UUID generation
├── __init__.py
└── performance_benchmark.py  # Performance testing
```

**Purpose**: Comprehensive test generation for generated code.

**Test Types**:
- **pgTAP**: PostgreSQL native tests
- **pytest**: Python integration tests
- **Performance**: Load and stress testing
- **Data Seeding**: Realistic test data generation

## 🛠️ utils/

**Shared utilities**

```
utils/
├── __init__.py
└── safe_slug.py               # URL-safe slug generation
```

**Purpose**: Common utility functions used across the codebase.

**Current Utilities**:
- **Slug Generation**: URL-safe identifier creation
- **Future**: String processing, validation helpers, etc.

## 📊 Code Metrics

### File Count by Directory

| Directory | Files | Description |
|-----------|-------|-------------|
| `patterns/` | 25+ | Most complex - comprehensive pattern library |
| `generators/` | 12 | Code generation engines |
| `testing/` | 10 | Test generation system |
| `reverse_engineering/` | 8 | Import functionality |
| `application/` | 9 | Business logic services |
| `domain/` | 7 | Domain models |
| `parsers/` | 3 | Language parsers |
| `agents/` | 1 | AI framework |
| `registry/` | 1 | Service registry |
| `utils/` | 1 | Utilities |

### Key Architecture Principles

#### 1. Separation of Concerns
Each directory has a single, well-defined responsibility:
- **Domain**: Business rules and models
- **Application**: Use case orchestration
- **Infrastructure**: External concerns (parsing, generation)

#### 2. Dependency Direction
Dependencies flow inward toward the domain:
```
Infrastructure → Application → Domain
```

#### 3. Plugin Architecture
Extensible systems for:
- New language parsers
- Additional generators
- Custom patterns
- Framework adapters

#### 4. Testability
Every component designed for easy testing:
- Dependency injection
- Interface-based design
- Mock-friendly architecture

## 🚀 Extensibility Points

### Adding New Generators
1. Create new directory under `generators/`
2. Implement generator interface
3. Register in service registry
4. Add CLI support

### Adding New Patterns
1. Create pattern file in appropriate `patterns/` subdirectory
2. Implement pattern interface
3. Register in pattern registry
4. Add to pattern loader

### Adding New Parsers
1. Create parser directory under `parsers/`
2. Implement parser interface
3. Add reverse engineering support
4. Update CLI commands

## 🔧 Development Workflow

### Adding New Features
1. **Domain First**: Define domain concepts
2. **Application Logic**: Implement use cases
3. **Infrastructure**: Add external integrations
4. **Tests**: Comprehensive test coverage
5. **Documentation**: Update architecture docs

### Code Organization Rules
- **One Responsibility**: Each file/class has single purpose
- **Clear Naming**: Descriptive names for all components
- **Interface Segregation**: Small, focused interfaces
- **Dependency Injection**: Constructor injection pattern

## 📈 Evolution History

### Phase 1: Core Generation
- Basic PostgreSQL + GraphQL generation
- Simple YAML parsing
- File-based output

### Phase 2: Pattern Library
- Comprehensive pattern system
- Plugin architecture
- Enhanced testing

### Phase 3: Multi-Language
- Universal AST implementation
- Java/Spring Boot support
- Reverse engineering capabilities

### Phase 4: AI Enhancement (Current)
- AI-powered reverse engineering
- Intelligent pattern matching
- Automated optimization

### Phase 5: Universal Platform (Future)
- Full multi-language support
- Universal CI/CD generation
- Infrastructure as code

## 🎯 Quality Standards

### Code Quality
- **Type Hints**: 100% Python type coverage
- **Documentation**: Comprehensive docstrings
- **Linting**: Ruff compliance
- **Testing**: 90%+ coverage

### Architecture Quality
- **SOLID Principles**: Single responsibility, open/closed, etc.
- **Clean Architecture**: Dependency direction
- **Domain-Driven Design**: Business-focused modeling
- **Test-Driven Development**: Tests guide design

---

**SpecQL Source Structure**: 24 directories, 100+ files, infinitely extensible.