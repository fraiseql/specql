# SpecQL Dependency Strategy

## Core Dependencies (Always Installed)
- **pyyaml**: YAML parsing (core feature)
- **jinja2**: Template generation (core feature)
- **click**: CLI framework (core feature)
- **rich**: Terminal UI (core feature)
- **psycopg**: PostgreSQL client (core feature)
- **fraiseql-confiture**: Confiture integration (core feature)

## Optional Dependencies

### `specql[reverse]` - Reverse Engineering
- **pglast**: SQL AST parsing for reverse engineering existing schemas
- **tree-sitter-***: Multi-language parsing (Rust, TypeScript, Prisma)
- **tree-sitter-prisma**: Local Prisma grammar for tree-sitter
- **Use Case**: Converting existing databases to SpecQL

### `specql[testing]` - Test Data Generation
- **faker**: Realistic test data generation
- **Use Case**: Seed databases with realistic data for testing

### `specql[dev]` - Development Tools
- **pytest**: Testing framework
- **ruff**: Linting
- **mypy**: Type checking

### `specql[all]` - Everything
- All of the above

## Installation Examples

```bash
# Core only (most users)
pip install specql

# With reverse engineering
pip install specql[reverse]

# Development
pip install specql[dev,reverse,testing]

# Everything
pip install specql[all]
```

## Why Optional Dependencies?

1. **Reduced install time**: Core install is fast (< 10s)
2. **Smaller footprint**: No unnecessary packages
3. **Clear feature boundaries**: Users know what they're getting
4. **Better error messages**: Can guide users to install [reverse] if needed</content>
</xai:function_call">Now I need to update the pyproject.toml to reorganize the dependencies according to the strategy. Let me mark the documentation task as complete and move to updating pyproject.toml.

I'll need to:
1. Move faker to testing optional dependencies
2. Move pglast, tree-sitter packages to reverse optional dependencies
3. Add tree-sitter-prisma as a local dependency
4. Update the all group to include all optional dependencies
5. Fix the version conflicts (there were two pglast entries with different versions)

Let me update the pyproject.toml:

<xai:function_call name="todowrite">
<parameter name="todos">[{"content":"Day 1 Morning: Document dependency rationale in DEPENDENCY_STRATEGY.md","status":"completed","priority":"high","id":"day1_morning_dependency_documentation"},{"content":"Day 1 Morning: Update pyproject.toml with organized optional dependencies","status":"in_progress","priority":"high","id":"day1_morning_update_pyproject"}]
