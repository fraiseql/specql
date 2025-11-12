# Issue #9: SpecQL CLI "No Brainer" Improvements

**Created**: 2025-11-12
**Issue**: https://github.com/fraiseql/specql/issues/9
**Status**: Planning
**Complexity**: Medium - UX improvements with backward compatibility

---

## Executive Summary

Transform the SpecQL CLI from "powerful but requires expertise" to "powerful AND intuitive" by:
1. **Framework-aware defaults** - FraiseQL as default framework with sensible patterns
2. Making hierarchical output the default (production-ready by default)
3. **Generating table views (tv_*) by default** for FraiseQL GraphQL integration
4. Adding **rich progress output** with real-time feedback using the `rich` library
5. Adding comprehensive, educational help documentation
6. Eliminating the need for wrapper scripts
7. **Extensible architecture** for future frameworks (Django, Rails, Prisma)

**Key Innovation**: Framework-specific defaults ensure tv_* views are generated for FraiseQL (needs GraphQL), but not for Django/Rails (ORM-based). Single `--framework` flag controls all related patterns.

**Impact**: 95% reduction in script complexity, 99% reduction in time to first success (from 2 hours to 30 seconds based on PrintOptim case study with 74 entities, 507 files).

---

## Problem Analysis

### Current Pain Points

1. **Non-obvious defaults hurt production workflows**
   - Users expect production-ready output, get development structure
   - Flat confiture structure is default, but hierarchical is needed for large projects
   - Output directory defaults don't align with migration workflows

2. **Users write wrapper scripts**
   - PrintOptim migration required 30-line bash wrapper
   - Must understand internal module structure (`src.cli.confiture_extensions`)
   - Can't use simple `specql generate` command

3. **Inadequate help documentation**
   - Help output doesn't explain concepts (confiture environment, hierarchical structure)
   - No examples of common workflows
   - Missing "what gets generated" overview

4. **Output structure confusion**
   - Difference between confiture (flat) and hierarchical (organized) not explained
   - Large projects (507 files) need organized structure, not flat chaos

---

## Solution Design

### Core Philosophy
- **Make the right thing easy**: Production defaults
- **Make the wrong thing hard**: Require flags for non-production
- **Document everything**: Self-documenting CLI
- **Provide helpful feedback**: Show what happened and next steps

### Proposed Changes

#### 1. Framework-Aware Smart Defaults

**Key Design Principle**: Different frameworks have different production requirements. SpecQL should have sensible defaults per framework.

##### Framework Detection & Defaults

**New flag**: `--framework` (default: `fraiseql`)
- Specifies target framework for generation
- Each framework has its own default pattern set
- Currently supported: `fraiseql` (PostgreSQL + FraiseQL GraphQL)
- Future: `django`, `rails`, `prisma`, etc.

##### FraiseQL Framework Defaults (Current Primary Framework)

| Flag | Current Default | New Default | Rationale |
|------|----------------|-------------|-----------|
| `--framework` | (implicit) | **`fraiseql`** | FraiseQL is primary framework |
| `--output-format` | `hierarchical` | `hierarchical` | ✅ Already correct |
| `--output-dir` | `migrations` | `migrations` | ✅ Already correct |
| `--use-registry` | `False` | **`True`** | Production-ready by default |
| `--include-tv` | `False` | **`True`** | FraiseQL requires tv_* views for GraphQL |

**Framework-specific patterns for FraiseQL**:
- ✅ Table views (tv_*) - GraphQL query interface
- ✅ Trinity pattern (pk_*, id, identifier) - Multi-key access
- ✅ Audit fields - Temporal tracking
- ✅ FraiseQL annotations - GraphQL metadata
- ✅ Helper functions - Type-safe access patterns

##### Future Framework Defaults (Examples)

**Django Framework** (future):
```yaml
framework: django
defaults:
  include_tv: false        # Django ORM doesn't need tv_*
  include_models: true     # Generate models.py
  include_admin: true      # Generate admin.py
  trinity_pattern: false   # Django uses single PK
```

**Rails Framework** (future):
```yaml
framework: rails
defaults:
  include_tv: false        # ActiveRecord doesn't need tv_*
  include_models: true     # Generate model classes
  include_migrations: true # Generate Rails migrations
  trinity_pattern: false   # Rails uses single PK
```

**New flags**:
- `--dev` (development mode): Sets `--use-registry=False`, `--output-format=confiture`, `--output-dir=db/schema`, `--include-tv=False`
- `--no-tv` (opt-out): Disables table view generation even for FraiseQL
- `--framework=<name>`: Explicitly set target framework (default: fraiseql)

**Framework registry location**: `src/cli/framework_defaults.py`

```python
# Framework-specific default configurations
FRAMEWORK_DEFAULTS = {
    "fraiseql": {
        "include_tv": True,
        "trinity_pattern": True,
        "audit_fields": True,
        "fraiseql_annotations": True,
        "helper_functions": True,
        "description": "PostgreSQL + FraiseQL GraphQL (full-stack)",
    },
    "django": {
        "include_tv": False,
        "trinity_pattern": False,
        "include_models": True,
        "include_admin": True,
        "description": "Django ORM models and admin",
    },
    # ... more frameworks
}
```

**Rationale for framework-aware defaults**:
- ✅ Different frameworks have different production patterns
- ✅ FraiseQL needs tv_* for GraphQL, Django/Rails don't
- ✅ Trinity pattern is FraiseQL-specific
- ✅ Extensible architecture for future frameworks
- ✅ Single `--framework` flag controls all related defaults

#### 2. Enhanced Help Documentation

Transform help from "list of flags" to "educational guide":

```bash
$ specql generate --help

Usage: specql generate [OPTIONS] ENTITY_FILES...

  Generate production-ready PostgreSQL schema from SpecQL YAML entity definitions.

  By default, generates hierarchical directory structure with db/schema/ prefix,
  ready for migration deployment.

COMMON EXAMPLES:

  # Generate all entities (FraiseQL framework, production-ready)
  specql generate entities/**/*.yaml
  # → Uses FraiseQL defaults: tv_* views, Trinity pattern, audit fields

  # Generate for specific framework
  specql generate entities/**/*.yaml --framework django
  # → Uses Django defaults: models.py, admin.py, no tv_*

  # Generate specific entities
  specql generate entities/catalog/*.yaml

  # Custom output directory
  specql generate entities/**/*.yaml --output migrations/v2/

  # Development mode (flat structure for confiture)
  specql generate entities/**/*.yaml --dev

  # List available frameworks
  specql list-frameworks

OUTPUT FORMATS:

  hierarchical (default)
    Organized directory structure matching domain/subdomain/entity hierarchy.
    Best for: Production migrations, large codebases, team collaboration

    Structure:
      migrations/
        ├── 000_app_foundation.sql
        └── 01_write_side/
            ├── 013_catalog/
            │   └── 0132_manufacturer/
            │       └── 01321_manufacturer/
            │           ├── 013211_tb_manufacturer.sql
            │           └── 013211_fn_manufacturer_*.sql

  flat (--dev or --format=confiture)
    Flat directory structure grouped by object type.
    Best for: Development with confiture, simple projects

    Structure:
      db/schema/
        ├── 10_tables/manufacturer.sql
        ├── 20_helpers/manufacturer_helpers.sql
        └── 30_functions/create_manufacturer.sql

GENERATED ARTIFACTS:

  For each entity, SpecQL generates:
    • Table definition (tb_*) with Trinity pattern (id, pk_*, identifier)
    • Table view (tv_*) for GraphQL queries (default, use --no-tv to skip)
    • Audit fields (created_at, updated_at, deleted_at, etc.)
    • Foreign key constraints and indexes
    • Helper functions (get_by_id, get_by_identifier, etc.)
    • CRUD actions (create_*, update_*, delete_*)
    • Business action functions (as defined in YAML)
    • GraphQL metadata (FraiseQL @comments)

OPTIONS:

  --framework [fraiseql|django|rails]  Target framework (default: fraiseql)
  --format [hierarchical|flat]         Output format (default: hierarchical)
  --output DIRECTORY                   Output directory (default: migrations/)
  --dev                                Development mode: flat format in db/schema/
  --no-tv                              Skip table view (tv_*) generation
  --foundation-only                    Generate only app foundation
  --verbose, -v                        Show detailed generation progress
  --dry-run                            Show what would be generated without writing
  --help                               Show this help message

FRAMEWORK-SPECIFIC DEFAULTS:

  FraiseQL (default):
    • Table views (tv_*) for GraphQL queries
    • Trinity pattern (pk_*, id, identifier)
    • Audit fields (created_at, updated_at, etc.)
    • FraiseQL GraphQL annotations
    • Helper functions for type-safe access

  Django (future):
    • models.py with Django ORM models
    • admin.py for Django admin interface
    • Standard Django migrations
    • Single primary key (id)

  Rails (future):
    • ActiveRecord model classes
    • Rails migration files
    • Standard Rails conventions
    • Single primary key (id)

TABLE VIEWS (tv_*) - FraiseQL Specific:

  For FraiseQL framework, table views are generated by default.
  Table views provide:
    • GraphQL-friendly views with FraiseQL annotations
    • Simplified query interface for frontend applications
    • Automatic JOIN resolution for relationships
    • Essential for full-stack FraiseQL deployments

  Use --no-tv to skip table view generation if not needed.

MORE HELP:

  Documentation:  https://github.com/fraiseql/specql/docs
  Examples:       https://github.com/fraiseql/specql/examples

Report issues: https://github.com/fraiseql/specql/issues
```

#### 3. Rich Progress Output (CRITICAL REQUIREMENT)

**Current (minimal)**:
```
✅ Generated 507 schema file(s)
```

**This is inadequate!** Users need visibility into what's happening, especially for large projects with 74+ entities and 500+ files.

**Proposed (rich, informative)**:
```bash
🔍 Scanning entity files...
   Found 74 entities in 4 schemas

📊 Entity Breakdown:
   common schema:      23 entities
   tenant schema:      24 entities
   catalog schema:     26 entities
   management schema:   1 entity

⚙️  Generating database schema...
   [████████████████████] 74/74 entities

✅ Generation complete! (45.2 seconds)

📁 Output: migrations/01_write_side/
   ├── 011_core/        (23 entities, 92 files)
   ├── 013_catalog/     (26 entities, 208 files)
   └── 014_projects/    (25 entities, 207 files)

📈 Statistics:
   Total files:        507 SQL files
   Total SQL:          ~50,000 lines
   Tables (tb_*):      74
   Table views (tv_*): 74
   CRUD actions:       222
   Business actions:   182

🎯 Next Steps:
   1. Review:    tree migrations/01_write_side/
   2. Apply:     psql -f migrations/000_app_foundation.sql
   3. Migrate:   Apply entity files in 01_write_side/ subdirectories

📚 Learn more: specql generate --help
```

**Note**: This output will use the `rich` library for:
- ✅ **Progress bars** - Real-time visual feedback with `rich.progress`
- ✅ **Tables** - Structured entity breakdown with `rich.table`
- ✅ **Panels** - Boxed statistics with `rich.panel`
- ✅ **Colors** - Syntax highlighting with `rich.console`
- ✅ **Tree views** - Directory structure preview
- ✅ **Graceful fallback** - Basic click output if rich unavailable

#### 4. Backward Compatibility Strategy

**Phase 1: Current Release (0.4.x)** - Add warnings
- Keep current defaults
- Add deprecation warning when `--use-registry=False` (implicit)
- Recommend `--use-registry=True` for production

**Phase 2: Next Major Release (1.0)** - Change defaults
- Change `--use-registry` default to `True`
- Add `--dev` flag for development mode
- Maintain backward compatibility with explicit flags

**Phase 3: Documentation** - Update all examples
- Update README.md with new defaults
- Update GETTING_STARTED.md
- Update all documentation examples

---

## Implementation Plan

### Phase 1: Rich Progress Output & Enhanced Help (HIGHEST PRIORITY)

**Priority**: CRITICAL - This is the most visible improvement users will see

**Files to modify**:
- `src/cli/generate.py` - Enhanced help text
- `src/cli/orchestrator.py` - **Rich progress tracking system**
- New file: `src/cli/progress.py` - Progress bar and statistics tracking
- New file: `src/cli/help_text.py` - Centralized help documentation
- `pyproject.toml` - Add `rich` dependency

**Changes (Rich Progress)**:
1. **Pre-scan phase**: Show entity file discovery with count
2. **Schema breakdown**: Group by schema, show entity counts
3. **Real-time progress bar**: Visual progress with percentage (e.g., `[████████████████████] 74/74 entities`)
4. **Per-entity feedback**: Show current entity being processed
5. **Timing**: Show elapsed time and estimated time remaining
6. **Summary statistics**: Total files, lines, tables, actions
7. **Output location**: Clear path to generated files with tree preview
8. **Next steps**: Actionable guidance on what to do next

**Implementation approach**:
```python
# src/cli/progress.py
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

class SpecQLProgress:
    """Rich progress tracker for SpecQL generation"""

    def __init__(self):
        self.console = Console()

    def scan_phase(self, total_files: int):
        """Show entity scanning phase"""
        self.console.print("🔍 [bold blue]Scanning entity files...[/bold blue]")
        self.console.print(f"   Found [bold]{total_files}[/bold] entity files")

    def schema_breakdown(self, schema_stats: dict):
        """Show entity breakdown by schema"""
        table = Table(title="📊 Entity Breakdown", show_header=True)
        table.add_column("Schema", style="cyan")
        table.add_column("Entities", justify="right", style="green")

        for schema, count in schema_stats.items():
            table.add_row(schema, str(count))

        self.console.print(table)

    def generation_progress(self, entities: list):
        """Show progress bar during generation"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "⚙️  Generating database schema...",
                total=len(entities)
            )

            for entity in entities:
                # Yield control to caller for actual generation
                yield entity, lambda: progress.update(task, advance=1)

    def summary(self, stats: dict, output_dir: str, elapsed: float):
        """Show final summary with statistics"""
        self.console.print(f"\n✅ [bold green]Generation complete![/bold green] ({elapsed:.1f} seconds)\n")

        # Output location with tree structure
        self.console.print(f"📁 [bold]Output:[/bold] {output_dir}")

        # Statistics
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="dim")
        stats_table.add_column("Value", style="bold")

        stats_table.add_row("Total files:", f"{stats['total_files']} SQL files")
        stats_table.add_row("Total SQL:", f"~{stats['total_lines']:,} lines")
        stats_table.add_row("Tables:", str(stats['tables']))
        stats_table.add_row("CRUD actions:", str(stats['crud_actions']))
        stats_table.add_row("Business actions:", str(stats['business_actions']))

        self.console.print(Panel(stats_table, title="📈 Statistics", border_style="blue"))

        # Next steps
        self.console.print("\n🎯 [bold]Next Steps:[/bold]")
        self.console.print(f"   1. Review:    tree {output_dir}")
        self.console.print(f"   2. Apply:     psql -f {output_dir}/000_app_foundation.sql")
        self.console.print(f"   3. Migrate:   Apply entity files in subdirectories")
        self.console.print("\n📚 Learn more: [dim]specql generate --help[/dim]")
```

**Fallback for environments without `rich`**:
```python
# Graceful degradation
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Use basic click output
```

**Tests**:
- `tests/unit/cli/test_generate_help.py` - Verify help text completeness
- `tests/unit/cli/test_progress_output.py` - Verify rich progress output
- `tests/unit/cli/test_progress_statistics.py` - Verify statistics calculation
- `tests/unit/cli/test_progress_fallback.py` - Verify fallback when rich unavailable

### Phase 2: Framework-Aware Defaults System (Medium Risk)

**Priority**: HIGH - Enables future multi-framework support

**Files to create**:
- `src/cli/framework_defaults.py` - Framework-specific default configurations
- `src/cli/framework_registry.py` - Framework detection and selection logic

**Files to modify**:
- `src/cli/generate.py` - Add `--framework` flag, `--dev` flag, `--no-tv` flag
- `src/cli/orchestrator.py` - Framework-aware default behavior

**Changes**:
1. **Create framework defaults registry**:
   ```python
   # src/cli/framework_defaults.py
   FRAMEWORK_DEFAULTS = {
       "fraiseql": {
           "include_tv": True,
           "trinity_pattern": True,
           "audit_fields": True,
           "fraiseql_annotations": True,
           "helper_functions": True,
       },
       "django": {...},  # Future
       "rails": {...},   # Future
   }
   ```

2. **Add `--framework` flag** (default: `fraiseql`)
   - Selects framework-specific defaults
   - Validates against registered frameworks
   - Shows available frameworks with `specql list-frameworks`

3. **Add `--dev` flag** (development mode)
   - Combines: `--use-registry=False`, `--output-format=confiture`, `--include-tv=False`
   - Framework-agnostic quick development mode

4. **Add `--no-tv` flag** (opt-out of table views)
   - Overrides framework default for tv_ generation
   - Useful when FraiseQL default isn't needed

5. **Framework-aware include_tv default**:
   - FraiseQL: `include_tv=True` (GraphQL requires tv_*)
   - Django/Rails: `include_tv=False` (ORM doesn't need tv_*)

6. **Add deprecation warnings**:
   - Warn when `--use-registry=False` is implicit
   - Recommend explicit `--framework` flag

**Rationale for framework-aware approach**:
- ✅ Different frameworks need different patterns
- ✅ FraiseQL is first-class but not only framework
- ✅ Extensible for future Django, Rails, Prisma support
- ✅ Single `--framework` flag controls all defaults
- ✅ Explicit is better than implicit

**Tests**:
- `tests/unit/cli/test_framework_defaults.py` - Verify framework registry
- `tests/unit/cli/test_framework_detection.py` - Verify framework selection
- `tests/unit/cli/test_fraiseql_defaults.py` - Verify FraiseQL defaults (tv_=True)
- `tests/unit/cli/test_dev_flag.py` - Verify `--dev` behavior
- `tests/unit/cli/test_no_tv_flag.py` - Verify `--no-tv` override
- `tests/integration/test_backwards_compatibility.py` - Ensure no breaking changes

### Phase 3: Change Defaults (Breaking Change - v1.0)

**Files to modify**:
- `src/cli/generate.py` - Change defaults: `framework=fraiseql`, `use_registry=True`
- `src/cli/orchestrator.py` - Framework-aware default behavior
- `src/cli/framework_defaults.py` - Enable FraiseQL defaults
- Documentation updates

**Changes**:
1. Change `--framework` default to `fraiseql` (explicit, not implicit)
2. Change `--use-registry` default from `False` to `True`
3. FraiseQL framework defaults apply automatically:
   - `include_tv=True` (table views for GraphQL)
   - `trinity_pattern=True` (pk_*, id, identifier)
   - `audit_fields=True` (temporal tracking)
4. Update all documentation with new defaults
5. Add migration guide for existing users

**Default behavior in v1.0**:
```bash
# This command (no flags)
specql generate entities/**/*.yaml

# Equivalent to:
specql generate entities/**/*.yaml --framework fraiseql --use-registry

# Will generate (FraiseQL defaults):
# - Hierarchical directory structure (--use-registry=True)
# - In migrations/ directory
# - With table views tv_* (FraiseQL default: include_tv=True)
# - Trinity pattern (pk_*, id, identifier)
# - Audit fields (created_at, updated_at, etc.)
# - FraiseQL GraphQL annotations
# - Helper functions
# - Production-ready output
```

**Override framework defaults**:
```bash
# Skip tv_* generation even with FraiseQL
specql generate entities/**/*.yaml --no-tv

# Use different framework (when available)
specql generate entities/**/*.yaml --framework django

# Development mode (disables all framework-specific features)
specql generate entities/**/*.yaml --dev
```

**Tests**:
- Update all existing tests for new framework-aware defaults
- Add tests for FraiseQL framework defaults
- Add tests for framework override flags (`--no-tv`)
- Add tests for legacy behavior with explicit flags

### Phase 4: Documentation Overhaul

**Files to create/modify**:
- `docs/guides/CLI_GUIDE.md` - Comprehensive CLI guide
- `docs/guides/MIGRATION_TO_V1.md` - Migration guide
- `README.md` - Update quick start
- `GETTING_STARTED.md` - Update examples

**Content**:
1. CLI usage patterns
2. Output format comparison
3. When to use hierarchical vs flat
4. Production deployment workflows
5. Migration guide from 0.x to 1.0

---

## Testing Strategy

### Unit Tests

1. **Help Text Validation** (`tests/unit/cli/test_help_text.py`)
   - Verify all sections present
   - Verify examples are valid
   - Verify formatting consistency

2. **Progress Output** (`tests/unit/cli/test_progress_output.py`)
   - Mock generation, verify output
   - Test different entity counts
   - Test timing information

3. **Flag Behavior** (`tests/unit/cli/test_flag_behavior.py`)
   - Test `--dev` flag combinations
   - Test explicit flag overrides
   - Test deprecation warnings

### Integration Tests

1. **Real World Scenarios** (`tests/integration/cli/test_real_world_scenarios.py`)
   - Small project (5 entities)
   - Medium project (25 entities)
   - Large project (74 entities - PrintOptim scale)

2. **Backward Compatibility** (`tests/integration/cli/test_backwards_compatibility.py`)
   - Verify old flag combinations still work
   - Verify output structure unchanged with explicit flags

3. **Output Validation** (`tests/integration/cli/test_output_validation.py`)
   - Verify file structure matches expectations
   - Verify SQL content correctness
   - Verify registry updates

---

## Migration Path for Users

### For New Users (v1.0+)
```bash
# Just works - production ready
specql generate entities/**/*.yaml
```

### For Existing Users (Upgrading from 0.x)

**Option 1: Embrace new defaults**
```bash
# Remove wrapper scripts, use defaults
specql generate entities/**/*.yaml
```

**Option 2: Keep old behavior**
```bash
# Add --dev flag to maintain flat structure
specql generate entities/**/*.yaml --dev
```

**Option 3: Explicit control**
```bash
# Explicitly set all options
specql generate entities/**/*.yaml \
  --use-registry=false \
  --output-format=confiture \
  --output-dir=db/schema
```

---

## Success Metrics

### Quantitative
- ✅ 95% reduction in wrapper script complexity (30 lines → 1 command)
- ✅ 99% reduction in time to first success (2 hours → 30 seconds)
- ✅ 100% reduction in internal knowledge required
- ✅ Table views (tv_*) generated by default for GraphQL readiness
- ✅ Rich progress output for all projects (with graceful fallback)
- ✅ Help text covers all common use cases
- ✅ All existing tests pass with backward compatibility

### Qualitative
- ✅ New users can generate production-ready output without documentation
- ✅ Help text answers "what gets generated?" question
- ✅ Rich progress output provides visibility and confidence
- ✅ Progress bars and statistics show real-time feedback
- ✅ No wrapper scripts needed for large projects
- ✅ GraphQL integration works out-of-the-box with tv_* views
- ✅ Confiture integration still works for development (`--dev` flag)

---

## Implementation Phases & Timeline

### Phase 1: Enhanced Help & Progress (Week 1)
- **Day 1-2**: Create `help_text.py` with comprehensive documentation
- **Day 3-4**: Add progress tracking to orchestrator
- **Day 5**: Write tests and validate output

### Phase 2: Smart Defaults & Warnings (Week 2)
- **Day 1-2**: Implement `--dev` flag
- **Day 3-4**: Add deprecation warnings
- **Day 5**: Write tests and validate backward compatibility

### Phase 3: Documentation Update (Week 3)
- **Day 1-2**: Create CLI guide
- **Day 3-4**: Update all examples in docs
- **Day 5**: Create migration guide

### Phase 4: Release & Monitor (Week 4)
- **Day 1**: Release 0.5.0 with enhanced help and deprecation warnings
- **Day 2-5**: Monitor community feedback, address issues
- **Week 8**: Release 1.0.0 with changed defaults

---

## Dependencies

### Internal
- ✅ `SchemaOrchestrator` - Already supports both formats
- ✅ `NamingConventions` - Already supports registry
- ✅ Registry system - Already implemented
- ✅ `src/adapters/registry.py` - Already has adapter registry system
- 🆕 `src/cli/framework_defaults.py` - NEW: Framework-specific defaults
- 🆕 `src/cli/framework_registry.py` - NEW: Framework detection logic

### External
- **`rich`** library - For beautiful CLI progress bars, tables, and formatting
  - Install: `pip install rich` or `uv add rich`
  - Fallback: Basic `click` output if `rich` not available
  - Benefits: Progress bars, colored output, tables, tree views
  - Examples: Used by modern CLI tools like `poetry`, `httpie`, `pytest`

### Integration with Existing Universal System
The existing `src/adapters/registry.py` already has adapter infrastructure. The new framework defaults system will:
- Leverage existing adapter registry for backend detection
- Add CLI-level defaults on top of adapter capabilities
- Keep adapter system focused on code generation
- Keep framework defaults focused on user-facing CLI behavior

---

## Risk Assessment

### Low Risk
- ✅ Enhanced help text - additive only
- ✅ Improved progress output - additive only
- ✅ `--dev` flag - new feature, no breaking changes

### Medium Risk
- ⚠️ Deprecation warnings - may surprise users
- ⚠️ Documentation updates - requires coordination

### High Risk (Mitigated)
- ⚠️ Changing defaults in v1.0 - **Mitigated by**:
  - 6-month deprecation period
  - Major version bump (semantic versioning)
  - Comprehensive migration guide
  - Backward compatibility with explicit flags

---

## Open Questions

1. **Deprecation Timeline**: 6 months sufficient for migration?
   - **Recommendation**: Yes, with clear warnings and migration guide

2. **Default `--use-registry`**: True for all projects or size-based?
   - **Recommendation**: True for all - simplifies mental model

3. **Progress Output**: Always show or only with `--verbose`?
   - **Recommendation**: Always show summary, details with `--verbose`

4. **Help Text Length**: Too long? Add `--help-full` for complete version?
   - **Recommendation**: Keep comprehensive - users can scroll

---

## Related Issues

- **Issue #6**: Naming conventions and subdomain parsing (already implemented)
- **Issue #1**: Hex hierarchical table codes (already implemented)
- **Issue #2**: Hierarchical output CLI flag (already implemented)

This plan builds on existing infrastructure to improve UX.

---

## Appendix: Real-World Impact

### PrintOptim Case Study (74 entities, 507 files)

**Before (Current - v0.4.x)**:
```bash
# User must write wrapper script (generate_hex.sh - 30 lines)
#!/bin/bash
REPO_DIR="$(pwd)"
SPECQL_DIR="/home/lionel/code/specql"
ENTITIES=$(find "$REPO_DIR/entities" -name "*.yaml" -exec grep -L "^import:" {} \;)
ENTITY_PATHS=$(echo "$ENTITIES" | tr '\n' ' ')

cd "$SPECQL_DIR"
.venv/bin/python -m src.cli.confiture_extensions generate $ENTITY_PATHS \
  --output-format hierarchical \
  --output-dir "$REPO_DIR/generated/migrations"

# Time to first success: ~2 hours (trial and error)
# Knowledge required: Internal module structure, registry system
```

**After (Proposed - v1.0)**:
```bash
# One command, just works
specql generate entities/**/*.yaml

# Time to first success: ~30 seconds
# Knowledge required: None
```

**Impact**:
- **Developer Experience**: From "complex" to "delightful"
- **Documentation Burden**: From "extensive" to "self-documenting"
- **Maintenance**: From "wrapper scripts" to "single command"
- **Onboarding**: From "2 hours" to "30 seconds"

---

## Next Steps

1. **Review & Approve**: Get stakeholder feedback on this plan
2. **Create Tasks**: Break down into implementable units
3. **Phase 1 Implementation**: Start with enhanced help & progress
4. **Community Feedback**: Release 0.5.0, gather feedback
5. **Phase 2-3 Implementation**: Deprecation warnings & docs
6. **v1.0 Release**: Changed defaults with migration guide

---

**Status**: Ready for implementation
**Priority**: High - Significantly improves developer experience
**Estimated Effort**: 3-4 weeks (phased approach)
