# Contributing to SpecQL Generator

Welcome! This guide will help you contribute effectively to the SpecQL Generator project.

## 🎯 Project Organization

We use a **team-based parallelization strategy** with 5 independent work streams:

- **Team A**: Core Parser (`src/core/`)
- **Team B**: SQL Generators (`src/generators/`)
- **Team C**: Numbering System (`src/numbering/`)
- **Team D**: Integration Layer (`src/integration/`)
- **Team E**: CLI & Tooling (`src/cli/`)

See [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) for full details.

## 🚀 Getting Started

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repo-url>
cd specql

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
make install

# Install pre-commit hooks
uv pip install pre-commit
pre-commit install

# Verify setup
make test
```

### 2. Choose Your Team

Pick a team based on your skills:

- **Python + YAML + Parsing** → Team A (Core Parser)
- **PostgreSQL + Jinja2 + SQL** → Team B (SQL Generators)
- **Algorithms + File Systems** → Team C (Numbering System)
- **GraphQL + FraiseQL + TypeScript** → Team D (Integration)
- **CLI + DevOps + Documentation** → Team E (Tooling)

### 3. Pick an Issue

Check the project board for issues tagged with your team:
- `teamA/`, `teamB/`, `teamC/`, `teamD/`, `teamE/`

## 📋 Development Workflow (TDD)

We follow **strict TDD** (Test-Driven Development):

### RED → GREEN → REFACTOR → QA Cycle

#### 🔴 RED Phase: Write Failing Test

```python
# tests/unit/core/test_specql_parser.py
import pytest
from src.core.specql_parser import SpecQLParser

def test_parse_simple_entity():
    """Test parsing basic entity"""
    yaml_content = """
entity: Contact
  fields:
    email: text
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.name == 'Contact'
    assert 'email' in entity.fields
```

**Run test (should fail):**
```bash
uv run pytest tests/unit/core/test_specql_parser.py::test_parse_simple_entity -v
# Expected: FAILED - SpecQLParser not found
```

#### 🟢 GREEN Phase: Minimal Implementation

```python
# src/core/specql_parser.py
class SpecQLParser:
    def parse(self, yaml_content: str):
        # Minimal implementation to make test pass
        import yaml
        data = yaml.safe_load(yaml_content)
        # ... minimal code
        return Entity(name=data['entity']['name'], fields=...)
```

**Run test (should pass):**
```bash
uv run pytest tests/unit/core/test_specql_parser.py::test_parse_simple_entity -v
# Expected: PASSED
```

#### 🔧 REFACTOR Phase: Clean Up

```python
# src/core/specql_parser.py
class SpecQLParser:
    """Parse SpecQL YAML into AST with comprehensive validation"""

    def parse(self, yaml_content: str) -> Entity:
        """
        Parse YAML content into Entity AST

        Args:
            yaml_content: YAML string to parse

        Returns:
            Entity AST

        Raises:
            ParseError: If YAML is invalid
        """
        # Better implementation with error handling
        # Extract methods, add docstrings, etc.
```

**Run all tests:**
```bash
uv run pytest tests/unit/core/ -v
# All tests should still pass
```

#### ✅ QA Phase: Verify Quality

```bash
# Run linting
make lint

# Run type checking
make typecheck

# Check coverage
make coverage

# Run pre-commit checks
pre-commit run --all-files

# All checks should pass before committing
```

**Note**: Pre-commit hooks will automatically run these checks on `git commit`. To run manually: `pre-commit run --all-files`

## 🌿 Git Workflow

### Branch Naming Convention

```
<team>/<feature-name>

Examples:
- teamA/specql-parser
- teamB/table-generator
- teamC/numbering-system
- teamD/fraiseql-adapter
- teamE/cli-generate
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code refactoring
- test: Adding tests
- docs: Documentation
- chore: Maintenance

Examples:
- feat(core): implement SpecQL parser
- fix(generators): handle nullable fields
- test(numbering): add topological sort tests
- docs(guides): add SpecQL DSL reference
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b teamA/specql-parser
   ```

2. **Write tests + implementation** (TDD cycle)

3. **Ensure all checks pass**
   ```bash
   make test
   make lint
   make typecheck
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat(core): implement SpecQL parser"
   ```

5. **Push to GitHub**
   ```bash
   git push origin teamA/specql-parser
   ```

6. **Create Pull Request**
   ```bash
   gh pr create --title "SpecQL Parser Implementation" --body "Implements entity parsing with validation"
   ```

7. **Address review comments**

8. **Merge when approved**

## 🧪 Testing Guidelines

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests
│   ├── core/
│   ├── generators/
│   └── ...
├── integration/       # Slower, end-to-end tests
└── benchmarks/        # Performance tests
```

### Writing Good Tests

#### ✅ DO

```python
@pytest.mark.unit
def test_parse_simple_entity():
    """Test parsing basic entity with minimal fields"""
    # Arrange
    yaml_content = """
entity: Contact
  fields:
    email: text
"""

    # Act
    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Assert
    assert entity.name == 'Contact'
    assert len(entity.fields) == 1
    assert entity.fields['email'].type == 'text'
```

#### ❌ DON'T

```python
def test_everything():  # Too broad, hard to debug
    # Test 10 different things in one test
    # No clear arrange/act/assert
    # No descriptive name
```

### Test Coverage Requirements

- **Unit tests**: > 90% coverage
- **Integration tests**: > 80% coverage
- **Critical paths**: 100% coverage

```bash
# Check coverage
make coverage

# View HTML report
open htmlcov/index.html
```

## 📚 Documentation

### Code Documentation

```python
def parse_field_spec(self, name: str, spec: Any) -> FieldDefinition:
    """
    Parse individual field specification

    Formats:
    - field_name: text
    - field_name: ref(Entity)
    - field_name: enum(val1, val2)

    Args:
        name: Field name
        spec: Field specification (string or dict)

    Returns:
        Parsed FieldDefinition

    Raises:
        ParseError: If specification is invalid

    Examples:
        >>> parser.parse_field_spec('email', 'text')
        FieldDefinition(name='email', type='text')

        >>> parser.parse_field_spec('status', 'enum(lead, qualified)')
        FieldDefinition(name='status', type='enum', values=['lead', 'qualified'])
    """
```

### README Updates

When adding features, update relevant READMEs:
- `README.md` - Main project README
- `docs/guides/` - User guides
- Component READMEs in `src/*/README.md`

## 🔍 Code Review Guidelines

### As an Author

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Self-reviewed the diff

### As a Reviewer

- [ ] Code follows project patterns
- [ ] Tests are comprehensive
- [ ] Error handling is robust
- [ ] Edge cases are covered
- [ ] Documentation is clear
- [ ] Performance is acceptable

## 🚨 Common Pitfalls

### 1. Skipping Tests
❌ **Don't**: Write code first, tests later
✅ **Do**: Always write failing test first (RED → GREEN → REFACTOR)

### 2. Large PRs
❌ **Don't**: 2000+ line PRs
✅ **Do**: Small, focused PRs (< 500 lines)

### 3. Breaking Interfaces
❌ **Don't**: Change interfaces without team coordination
✅ **Do**: Discuss interface changes in team channel first

### 4. Ignoring CI Failures
❌ **Don't**: Merge with failing tests
✅ **Do**: Fix all CI failures before merge

## 🎯 Team Communication

### Daily Standup (Async)

Post in team channel:
```
**Yesterday**: Implemented SpecQL parser for simple entities
**Today**: Adding support for complex action steps
**Blockers**: Waiting for Team B to finalize GeneratedFile interface
```

### Integration Points

When your work depends on another team:
1. Check interface contract in `REPOSITORY_STRUCTURE.md`
2. Use mock data (see `tests/conftest.py`)
3. Coordinate in #integration channel

### Asking for Help

Good question format:
```
**Context**: Implementing SpecQL expression parser (Team A)
**Problem**: How to handle nested function calls in expressions?
**What I tried**: Recursive regex, but gets complex
**Code**: https://github.com/.../blob/main/src/core/expression_parser.py#L42
```

## 📊 Performance Guidelines

### Benchmarking

```bash
# Run benchmarks
uv run pytest tests/benchmarks/ -v

# Profile code
uv run python -m cProfile -o profile.stats src/cli/generate.py
uv run python -m pstats profile.stats
```

### Performance Targets

- **Parse 100 entities**: < 5 seconds
- **Generate SQL for 1 entity**: < 100ms
- **Full pipeline (1 entity)**: < 500ms

## 🎓 Learning Resources

### SpecQL Concepts
- [SpecQL DSL Reference](docs/guides/specql-dsl-reference.md)
- [Business Logic Patterns](docs/SPECQL_BUSINESS_LOGIC_REFINED.md)

### PostgreSQL
- [Trinity Pattern Guide](docs/guides/trinity-pattern.md)
- [Group Leader Pattern](docs/INTEGRATION_PROPOSAL.md)

### Python Best Practices
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md (per release)
- README.md (top contributors)
- Monthly team shoutouts

## 📞 Getting Help

- **General questions**: #specql-general
- **Team A**: #team-parser
- **Team B**: #team-generators
- **Team C**: #team-numbering
- **Team D**: #team-integration
- **Team E**: #team-tooling
- **Urgent blockers**: @mention tech-leads

---

**Thank you for contributing!** 🚀
