# CLI Command Status

> **Implementation status for all SpecQL CLI commands**

## Status Legend

| Status | Meaning |
|--------|---------|
| Stable | Fully implemented and tested |
| Beta | Implemented but may have limited functionality |
| Planned | Documented but not yet implemented |

---

## Command Status Matrix

| Command | Subcommand | Status | Tests | Notes |
|---------|------------|--------|-------|-------|
| **generate** | - | Stable | 6 | Full orchestrator integration |
| **validate** | - | Stable | 16 | YAML syntax + semantic checks |
| **reverse** | sql | Stable | 23 | Full pglast integration |
| | python | Stable | 19 | Django/Pydantic/SQLAlchemy/Dataclass |
| | typescript | Beta | 2 | Prisma/TypeORM |
| | rust | Beta | 2 | Diesel/SeaORM |
| | project | Stable | 8 | Auto-detection |
| **patterns** | detect | Stable | 6 | Pattern detection |
| | apply | Stable | 6 | Pattern application |
| **init** | project | Beta | 2 | Project scaffolding |
| | entity | Beta | 2 | Entity templates |
| | registry | Beta | 2 | Registry templates |
| **workflow** | migrate | Stable | 12 | Full pipeline |
| | sync | Stable | 5 | Incremental sync |
| **diff** | - | Stable | 6 | Schema comparison |
| **docs** | - | Planned | 0 | Documentation generation |
| **analyze** | - | Planned | 0 | Migration analysis |
| **test** | - | Planned | 0 | Testing framework |
| **cache** | - | Planned | 0 | Cache management |

---

## Stable Commands

### `specql generate`

**Status**: Stable

- Full integration with CLIOrchestrator
- Generates SQL tables, functions, helpers
- Supports Confiture directory structure
- Performance monitoring available

**Test count**: 6 unit tests

### `specql validate`

**Status**: Stable

- YAML syntax validation via parser
- Entity field type validation
- Action step syntax validation
- Naming convention warnings (camelCase, snake_case)
- Schema presence warnings

**Test count**: 16 unit tests

### `specql diff`

**Status**: Stable

- Compares SpecQL YAML with existing SQL schema
- Supports text and JSON output formats
- Can ignore comment differences
- Uses unified diff format for clear comparison

**Test count**: 6 unit tests

---

## Beta Commands

### `specql reverse sql`

**Status**: Stable

Full integration with pglast-based SQL parser:
- Parses CREATE TABLE statements
- Detects Trinity pattern automatically
- Detects audit trail pattern
- Handles foreign key relationships (ALTER TABLE)
- Generates SpecQL YAML with correct field types
- Preview mode with `--preview`
- Confidence threshold with `--min-confidence`

**Test count**: 17 unit tests

### `specql reverse python`

**Status**: Stable

Full integration with PythonASTParser:
- Parses Django models (CharField, ForeignKey, etc.)
- Parses Pydantic models (BaseModel)
- Parses SQLAlchemy models (declarative_base)
- Parses dataclasses (@dataclass)
- Auto-detects framework from imports
- Framework override with `--framework`
- Preview mode with `--preview`
- Generates SpecQL YAML with metadata

**Test count**: 19 unit tests

### `specql reverse project`

**Status**: Stable

Full project-level reverse engineering:
- Auto-detects Django, Rust, Prisma, TypeScript, Python projects
- Processes all relevant files in project structure
- Framework override with --framework option
- Preview mode without file generation
- Error handling for individual file failures
- Deduplication of entities found in multiple files

**Test count**: 8 unit tests

### `specql patterns detect`

**Status**: Stable

Full integration with UniversalPatternDetector:
- Detects audit-trail, multi-tenant, soft-delete, state-machine patterns
- Confidence scoring for pattern matches
- JSON/YAML output formats
- Minimum confidence threshold filtering

**Test count**: 6 unit tests

### `specql patterns apply`

**Status**: Stable

Full integration with PatternApplicator:
- Applies audit-trail, multi-tenant, soft-delete patterns
- Modifies YAML files with pattern requirements
- Preview mode without file modification
- Error handling for unknown patterns

**Test count**: 6 unit tests

### `specql init`

**Status**: Beta

Template generation is functional but with limited customization options.

### `specql workflow migrate`

**Status**: Stable

Full integration with reverse, validate, and generate commands:
- Real pipeline orchestration (not simulation)
- Supports SQL, Python, TypeScript, Rust source files
- Dry-run and preview modes
- Error handling with continue-on-error option
- Progress reporting

**Test count**: 12 unit + 5 integration tests

### `specql workflow sync`

**Status**: Stable

Real change detection and incremental regeneration:
- File hash-based change detection
- State persistence across runs
- Force regeneration option
- Exclude patterns support
- Pattern detection integration
- Parallel processing support

**Test count**: 8 unit + 5 integration tests

---

## Planned Commands

### `specql docs`

Generate documentation from SpecQL entities. Will support:
- Markdown output
- HTML output
- Entity relationship diagrams

### `specql analyze`

Analyze existing codebase and generate migration report. Will include:
- Complexity scores
- Migration recommendations
- Effort estimates

### `specql test`

Testing framework for SpecQL entities. Will support:
- Fixture-based testing
- Equivalence validation
- Action logic testing

### `specql cache`

Cache management for faster regeneration. Planned features:
- `specql cache stats` - Show cache statistics
- `specql cache clear` - Clear the cache

---

## Test Coverage

```bash
# Run all CLI tests
uv run pytest tests/unit/cli/ -v

# Run specific command tests
uv run pytest tests/unit/cli/commands/test_generate.py -v
uv run pytest tests/unit/cli/commands/test_validate.py -v
uv run pytest tests/unit/cli/commands/test_reverse.py -v
```

**Total CLI tests**: 197 passing

---

## Recent Changes

### 2025-11-21 (Phase 3 - Python Reverse Engineering)

- Integrated `specql reverse python` with PythonASTParser
- Full support for Django, Pydantic, SQLAlchemy, and dataclass models
- Auto-detection of framework from imports
- 19 unit tests added
- Updated Python reverse status from Beta to Stable

### 2025-11-21 (Phase 2)

- Integrated `specql reverse sql` with real pglast parsers
- Full Trinity pattern detection
- Foreign key relationship handling
- 17 tests for reverse sql command
- Updated status from Beta to Stable
- Implemented `specql diff` command for schema comparison
- 6 tests for diff command
- Updated diff status from Planned to Stable
- Updated reverse sql to use standardized --output option
- Added 6 integration tests for reverse sql real parsing
- Total reverse sql tests: 23

### 2025-11-21 (Phase 1)

- Implemented `specql validate` command
- Connected `specql generate` to CLIOrchestrator
- Updated cli-commands.md documentation
- Created cli-status.md (this file)

---

## Contributing

To implement a planned command:

1. Create command file in `src/cli/commands/`
2. Register in `src/cli/main.py`
3. Add tests in `tests/unit/cli/commands/`
4. Update this status document
5. Update cli-commands.md documentation

---

**Last Updated**: 2025-11-21
