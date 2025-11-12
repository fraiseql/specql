# Implementation Plan: Add `--output-format hierarchical` CLI Flag

**Issue**: #2 - Request for `--output-format hierarchical` CLI option
**Date**: 2025-11-10
**Status**: Ready for Implementation
**Estimated Time**: ~30 minutes

---

## 📊 Context

**Current State**:
- Hierarchical generation code already exists in `CLIOrchestrator`
- Currently hardcoded to `output_format="confiture"` in `confiture_extensions.py:29`
- Registry-based hierarchical structure fully implemented but not accessible via CLI

**Goal**: Expose existing hierarchical output functionality through CLI flag

---

## 🎯 Complexity Assessment

**Classification**: **SIMPLE** - Single file modification, adding CLI parameter

**Rationale**:
- No new architecture needed - code already exists
- Single file change (`src/cli/confiture_extensions.py`)
- Existing test coverage for underlying functionality
- Low risk - defaults to current behavior

**Approach**: Direct implementation (no phased TDD needed)

---

## 📝 Implementation Steps

### Step 1: Add CLI Options (5 minutes)

**File**: `src/cli/confiture_extensions.py`

**Changes**:
```python
@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option("--env", default="local", help="Confiture environment to use")
@click.option(
    "--output-format",
    type=click.Choice(["confiture", "hierarchical"], case_sensitive=False),
    default="confiture",
    help="Output format: confiture (flat) or hierarchical (hex directories)",
)
@click.option(
    "--output-dir",
    default=None,  # Will be set based on output_format
    help="Output directory (defaults: db/schema for confiture, migrations/ for hierarchical)",
)
def generate(entity_files, foundation_only, include_tv, env, output_format, output_dir):
    """Generate PostgreSQL schema from SpecQL YAML files"""
```

### Step 2: Update Orchestrator Instantiation (5 minutes)

**File**: `src/cli/confiture_extensions.py`

**Changes**:
```python
def generate(entity_files, foundation_only, include_tv, env, output_format, output_dir):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    # Determine default output directory
    if output_dir is None:
        output_dir = "db/schema" if output_format == "confiture" else "migrations"

    # Use registry when hierarchical format requested
    use_registry = (output_format == "hierarchical")

    # Create orchestrator with requested format
    orchestrator = CLIOrchestrator(
        use_registry=use_registry,
        output_format=output_format
    )

    # Generate schema
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir=output_dir,
        foundation_only=foundation_only,
        include_tv=include_tv,
    )
```

### Step 3: Update Success Messages (5 minutes)

**File**: `src/cli/confiture_extensions.py`

**Changes**:
```python
    # Success messaging
    click.secho(f"✅ Generated {len(result.migrations)} schema file(s)", fg="green")

    # Confiture build (only for confiture format)
    if output_format == "confiture" and not foundation_only:
        click.echo("\nBuilding final migration with Confiture...")
        try:
            from confiture.core.builder import SchemaBuilder
            builder = SchemaBuilder(env=env)
            builder.build()

            output_path = Path(f"db/generated/schema_{env}.sql")
            click.secho(f"✅ Complete! Migration written to: {output_path}", fg="green", bold=True)
            click.echo("\nNext steps:")
            click.echo(f"  1. Review: cat {output_path}")
            click.echo(f"  2. Apply: confiture migrate up --env {env}")
            click.echo("  3. Status: confiture migrate status")
        except ImportError:
            click.secho("⚠️  Confiture not available, generated schema files only", fg="yellow")
        except Exception as e:
            click.secho(f"❌ Confiture build failed: {e}", fg="red")
            return 1

    elif output_format == "hierarchical":
        click.secho(f"\n📁 Hierarchical output written to: {output_dir}/", fg="blue", bold=True)
        click.echo("\nStructure:")
        click.echo("  migrations/")
        click.echo("    └── 01_write_side/")
        click.echo("        └── [domain]/")
        click.echo("            └── [subdomain]/")
        click.echo("                └── [entity]/")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review structure: tree {output_dir}/")
        click.echo(f"  2. Apply manually or integrate with custom migration tool")
        if use_registry:
            click.echo(f"  3. Check registry: cat registry/domain_registry.yaml")

    return 0
```

---

## ✅ Success Criteria

1. **CLI flag works correctly**:
   ```bash
   # Default (confiture) - should work as before
   ./specql-generate entities/tenant/machine.yaml

   # Hierarchical output
   ./specql-generate entities/tenant/machine.yaml --output-format hierarchical

   # Custom output directory
   ./specql-generate entities/**/*.yaml --output-format hierarchical --output-dir reference/
   ```

2. **Output structure correct**:
   - Confiture: Flat structure in `db/schema/10_tables/`, `30_functions/`, etc.
   - Hierarchical: Nested structure using hex codes

3. **Backward compatibility maintained**:
   - Existing commands work unchanged
   - Default behavior unchanged

4. **Error handling**:
   - Clear error if registry not found (hierarchical mode)
   - Helpful messages for each mode

---

## 🧪 Testing Strategy

### Manual Testing
```bash
# Test 1: Default behavior (should work as before)
./specql-generate entities/tenant/machine.yaml
ls db/schema/10_tables/

# Test 2: Hierarchical output
./specql-generate entities/tenant/machine.yaml --output-format hierarchical
tree migrations/

# Test 3: Custom output directory
./specql-generate entities/tenant/machine.yaml --output-format hierarchical --output-dir test_output/
tree test_output/

# Test 4: Multiple entities
./specql-generate entities/**/*.yaml --output-format hierarchical
```

### Integration Test (Optional)
Add test to `tests/integration/test_confiture_integration.py`:
```python
def test_hierarchical_output_format(tmp_path):
    """Test --output-format hierarchical generates correct structure"""
    # Test implementation
```

---

## 📦 Deliverables

1. **Modified File**: `src/cli/confiture_extensions.py` (3 sections changed)
2. **Updated Help Text**: `./specql-generate --help` shows new options
3. **Documentation**: Usage examples in help text

---

## ⚡ Estimated Time

- **Implementation**: 15 minutes
- **Testing**: 10 minutes
- **Documentation review**: 5 minutes
- **Total**: ~30 minutes

---

## 🎯 Benefits

1. **Low Risk**: Uses existing, tested code
2. **High Value**: Enables PrintOptim migration validation workflow
3. **User Choice**: Doesn't change defaults, opt-in via flag
4. **Extensible**: Easy to add more formats later if needed

---

## 🚀 Use Case: PrintOptim Migration

**Context**: Migrating PrintOptim backend (74 entities with explicit table codes) to SpecQL

**Current Workflow**:
```bash
# Generates flat structure in db/schema/10_tables/
./specql-generate entities/**/*.yaml
# Output: 429 files in flat Confiture structure
```

**Desired Workflow**:
```bash
# Generate hierarchical structure matching backend
./specql-generate entities/**/*.yaml --output-format hierarchical --output-dir reference_comparison/

# Compare with backend
diff -r reference_sql/0_schema/ reference_comparison/
```

**Benefits**:
1. **Validation**: Verify generated SQL matches backend structure
2. **Migration**: Easier to map generated files to original backend files
3. **Organization**: Logical grouping by domain (CRM, Catalog, etc.)
4. **Traceability**: Table codes visible in directory hierarchy

---

## 📋 Implementation Checklist

- [ ] Add `--output-format` CLI option
- [ ] Add `--output-dir` CLI option with smart defaults
- [ ] Update orchestrator instantiation logic
- [ ] Update success messages for hierarchical mode
- [ ] Test default (confiture) mode still works
- [ ] Test hierarchical mode generates correct structure
- [ ] Test custom output directory
- [ ] Update `--help` text
- [ ] Run existing test suite to ensure no regressions

---

**Last Updated**: 2025-11-10
**Ready for Implementation**: Yes
**Blocked By**: None
