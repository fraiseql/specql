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
| | project | Beta | 2 | Auto-detection |
| **patterns** | detect | Stable | 3 | Pattern detection |
| | apply | Beta | 2 | Pattern application |
| **init** | project | Beta | 2 | Project scaffolding |
| | entity | Beta | 2 | Entity templates |
| | registry | Beta | 2 | Registry templates |
| **workflow** | migrate | Beta | 12 | Full pipeline |
| | sync | Beta | 5 | Incremental sync |
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

### `specql reverse typescript|rust|project`

**Status**: Beta

Commands accept arguments and options but have limited backend integration. Full reverse engineering logic exists in `reverse_engineering/` module but CLI integration is partial.

### `specql patterns`

**Status**: Beta (detect) / Beta (apply)

Pattern detection works with mock output. Full pattern detector exists in `reverse_engineering/universal_pattern_detector.py`.

### `specql init`

**Status**: Beta

Template generation is functional but with limited customization options.

### `specql workflow`

**Status**: Beta

Multi-step automation works but relies on other commands' integration levels.

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

**Total CLI tests**: 92 passing

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
