# Contributing to SpecQL

Thank you for your interest in contributing to SpecQL! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites
- Python 3.11 or higher
- `uv` package manager
- Git
- PostgreSQL (for testing database features)

### Development Setup

1. **Fork and Clone**
    ```bash
    git clone https://github.com/YOUR_USERNAME/specql.git
    cd specql
    ```

2. **Install Dependencies**
    ```bash
    uv sync
    uv pip install -e ".[dev]"
    ```

3. **Verify Installation**
    ```bash
    # Run tests
    uv run pytest

    # Check linting
    uv run ruff check src/

    # Check type hints
    uv run mypy src/
    ```

4. **Create a Branch**
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/issue-number-description
    ```

## Making Changes

### Project Structure

```
specql/
├── src/
│   ├── core/           # Core parsing and AST
│   ├── generators/     # Code generators (PostgreSQL, Java, etc.)
│   ├── parsers/        # Language parsers
│   ├── reverse_engineering/  # Reverse engineering tools
│   ├── cli/            # CLI interface
│   └── utils/          # Utilities
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data
├── docs/               # Documentation
└── examples/           # Example projects
```

### Types of Contributions

#### 🐛 Bug Fixes
1. Check if issue exists, if not create one
2. Reference issue number in branch name: `fix/123-description`
3. Add test that reproduces the bug
4. Fix the bug
5. Ensure test passes

#### ✨ New Features
1. Discuss in GitHub issue first (for major features)
2. Create feature branch: `feature/description`
3. Implement with tests
4. Update documentation
5. Add example if applicable

#### 📝 Documentation
1. Create branch: `docs/what-you-are-documenting`
2. Update relevant docs in `docs/`
3. Test all code examples work
4. Check links aren't broken

#### 🎨 Code Quality
1. Run linter: `uv run ruff check src/`
2. Run formatter: `uv run black src/`
3. Run type checker: `uv run mypy src/`
4. Fix any issues

## Submitting Changes

### Before Submitting

**Checklist**:
- [ ] All tests pass (`uv run pytest`)
- [ ] No linting errors (`uv run ruff check src/`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (for notable changes)
- [ ] Commit messages are clear and descriptive

### Commit Messages

Follow conventional commits format:

```
type(scope): Short description

Longer explanation if needed.

Fixes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples**:
```
feat(generators): Add Go/GORM generator

Implements code generation for Go with GORM ORM support.
Includes models, repositories, and HTTP handlers.

Closes #45

---

fix(parser): Handle null values in YAML fields

Previously crashed on null field values.
Now treats null as optional field.

Fixes #123

---

docs(guides): Add reverse engineering tutorial

Created complete guide for reverse engineering PostgreSQL schemas.
```

### Pull Request Process

1. **Push Your Branch**
    ```bash
    git push origin feature/your-feature-name
    ```

2. **Create Pull Request**
    - Go to GitHub repository
    - Click "New Pull Request"
    - Select your branch
    - Fill in PR template

3. **PR Template**
    ```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Tested manually with examples

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented in CHANGELOG)

## Related Issues
Fixes #(issue number)
```

4. **Code Review**
    - Maintainers will review your PR
    - Address feedback by pushing new commits
    - Once approved, it will be merged

## Coding Standards

### Python Style

We follow **PEP 8** with some modifications:

```python
# Good: Clear, typed, documented
def generate_entity(
    entity_name: str,
    fields: list[Field],
    output_dir: Path
) -> GeneratedCode:
    """
    Generate code for an entity.

    Args:
        entity_name: Name of the entity
        fields: List of field definitions
        output_dir: Directory for generated files

    Returns:
        GeneratedCode object with file paths

    Raises:
        ValidationError: If entity_name is invalid
    """
    if not entity_name:
        raise ValidationError("Entity name required")

    # Implementation...
    return GeneratedCode(files=[...])


# Bad: No types, unclear names
def gen(name, flds, dir):
    if not name:
        raise Exception("bad")
    # ...
```

### Key Principles

1. **Type Hints**: Always use type hints
    ```python
    # Good
    def process_field(field: Field) -> str:
        ...

    # Bad
    def process_field(field):
        ...
    ```

2. **Docstrings**: Document public functions
    ```python
    def public_function(arg: str) -> int:
        """
        One-line summary.

        More detailed explanation if needed.

        Args:
            arg: Description

        Returns:
            Description

        Raises:
            ErrorType: When this happens
        """
    ```

3. **Error Handling**: Use specific exceptions
    ```python
    # Good
    raise ValidationError(f"Invalid field type: {field_type}")

    # Bad
    raise Exception("error")
    ```

4. **Naming Conventions**:
    - Classes: `PascalCase`
    - Functions/variables: `snake_case`
    - Constants: `UPPER_SNAKE_CASE`
    - Private: `_leading_underscore`

## Testing

### Writing Tests

**Test structure**:
```python
# tests/unit/generators/test_postgresql_generator.py

import pytest
from src.generators.postgresql import PostgreSQLGenerator
from src.core.models import Entity, Field

class TestPostgreSQLGenerator:
    """Tests for PostgreSQL code generator."""

    def test_generate_simple_table(self):
        """Should generate table with basic fields."""
        # Arrange
        entity = Entity(
            name="Contact",
            fields=[
                Field(name="email", type="text"),
                Field(name="name", type="text"),
            ]
        )
        generator = PostgreSQLGenerator()

        # Act
        result = generator.generate(entity)

        # Assert
        assert "CREATE TABLE" in result
        assert "email TEXT" in result
        assert "name TEXT" in result

    def test_generate_with_relationships(self):
        """Should generate foreign key for ref fields."""
        # Arrange
        entity = Entity(
            name="Contact",
            fields=[
                Field(name="company", type="ref(Company)"),
            ]
        )
        generator = PostgreSQLGenerator()

        # Act
        result = generator.generate(entity)

        # Assert
        assert "FOREIGN KEY" in result
        assert "REFERENCES tb_company" in result

    def test_invalid_field_type_raises_error(self):
        """Should raise ValidationError for unknown field type."""
        # Arrange
        entity = Entity(
            name="Contact",
            fields=[Field(name="bad", type="unknown_type")]
        )
        generator = PostgreSQLGenerator()

        # Act & Assert
        with pytest.raises(ValidationError):
            generator.generate(entity)
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/generators/test_postgresql_generator.py

# Run specific test
uv run pytest tests/unit/generators/test_postgresql_generator.py::TestPostgreSQLGenerator::test_generate_simple_table

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only fast tests (skip slow integration tests)
uv run pytest -m "not slow"
```

### Test Coverage

- Aim for **>90% coverage** for new code
- All bug fixes must include regression test
- Integration tests for critical paths
- Unit tests for individual functions

## Documentation

### What to Document

1. **Public APIs**: All public functions/classes
2. **Guides**: How to use new features
3. **Examples**: Working code samples
4. **CHANGELOG**: Notable changes

### Documentation Structure

```
docs/
├── 00_getting_started/    # Installation, quickstart
├── 01_tutorials/          # Step-by-step tutorials
├── 02_guides/             # How-to guides
├── 03_reference/          # API reference
├── 06_examples/           # Complete examples
└── 08_troubleshooting/    # Common issues
```

### Adding a New Feature Guide

1. Create file: `docs/02_guides/YOUR_FEATURE.md`
2. Follow template:
    ```markdown
# Feature Name

**Complexity**: Beginner/Intermediate/Advanced
**Time**: X minutes

## What You'll Learn
- Bullet point list

## Prerequisites
- What user needs

## Step 1: ...
[Clear, tested instructions]

## Step 2: ...
[Continue...]

## Troubleshooting
Common issues and solutions

## Next Steps
Related guides
```
3. Add link in `docs/README.md`
4. Test all code examples

## Release Process

### For Maintainers

1. **Update Version**
    ```bash
    # In pyproject.toml
    version = "0.5.0"
    ```

2. **Update CHANGELOG.md**
    ```markdown
## [0.5.0] - 2025-12-XX

### Added
- New feature descriptions

### Changed
- Breaking changes

### Fixed
- Bug fixes
```

3. **Create Release**
    ```bash
    git tag -a v0.5.0 -m "Release v0.5.0"
    git push origin v0.5.0
    ```

4. **Publish to PyPI**
    ```bash
    uv run python -m build
    uv run twine upload dist/*
    ```

## Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports, feature requests
- **Discussions**: Questions, ideas
- **Discord**: (if exists) Real-time chat

### Questions?
- Check [Troubleshooting Guide](docs/08_troubleshooting/README.md)
- Search [existing issues](https://github.com/fraiseql/specql/issues)
- Ask in [Discussions](https://github.com/fraiseql/specql/discussions)

## Recognition

Contributors are recognized in:
- CHANGELOG.md for their contributions
- GitHub contributors page
- Release notes

Thank you for contributing to SpecQL! 🎉