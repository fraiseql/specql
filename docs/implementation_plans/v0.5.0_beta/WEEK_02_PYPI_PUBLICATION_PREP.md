# Week 2: PyPI Publication Preparation

**Goal**: Prepare SpecQL for PyPI publication with complete metadata, clean repository structure, and tested build process.

**Estimated Time**: 35-40 hours (1 week full-time)

**Prerequisites**:
- Week 1 completed (documentation polished)
- Git repository clean
- All tests passing
- Understanding of Python packaging

---

## Overview

This week prepares SpecQL for PyPI publication. By the end, you'll have:
- ✅ Complete PyPI metadata in `pyproject.toml`
- ✅ Clean repository structure (internal docs archived)
- ✅ Tested build process
- ✅ Package validated on TestPyPI
- ✅ Ready for PyPI upload (Week 3)

---

## Day 1: Repository Cleanup (8 hours)

### Morning: Audit Repository Structure (4 hours)

#### Task 1.1: Inventory Current Files (90 min)

**Objective**: Understand what's in the repository and what should be public vs internal.

```bash
# Create a complete file inventory
find . -type f -not -path "./.*" -not -path "./backup*" > /tmp/repo_inventory.txt

# Categorize files
cat > docs/implementation_plans/v0.5.0_beta/REPOSITORY_AUDIT.md << 'EOF'
# Repository Structure Audit

## Files to Keep (Public-Facing)
### Root Level
- [ ] README.md
- [ ] LICENSE
- [ ] CHANGELOG.md
- [ ] pyproject.toml
- [ ] .gitignore
- [ ] Makefile

### Source Code
- [ ] src/ (all files)
- [ ] tests/ (all files)

### Documentation (Public)
- [ ] docs/00_getting_started/
- [ ] docs/01_tutorials/
- [ ] docs/02_guides/
- [ ] docs/03_reference/
- [ ] docs/04_architecture/
- [ ] docs/06_examples/
- [ ] docs/07_contributing/
- [ ] docs/08_troubleshooting/

### Examples
- [ ] examples/ (all files)
- [ ] entities/examples/ (all files)

## Files to Archive (Internal/Planning)
### Planning Documents
- [ ] ALPHA_FEEDBACK_TRACKING.md → backup_internal/
- [ ] V0.5.0_BETA_PLANNING.md → backup_internal/
- [ ] ALPHA_RELEASE_IMPLEMENTATION_PLAN.md → backup_internal/
- [ ] README_REFINEMENT_PLAN.md → backup_internal/
- [ ] ALPHA_RELEASE_TODO_CLEANUP_PLAN.md → backup_internal/

### Implementation Plans
- [ ] docs/implementation_plans/ → backup_internal/planning/

### Internal Docs (if any exist)
- [ ] docs/internal/ → backup_internal/
- [ ] docs/planning/ → backup_internal/

## Files to Delete (Temporary/Obsolete)
- [ ] TODO files (if absorbed into tracking)
- [ ] Scratch notes
- [ ] Test outputs not in .gitignore

## Files to Add
- [ ] CONTRIBUTING.md
- [ ] CODE_OF_CONDUCT.md
- [ ] SECURITY.md
- [ ] .github/ISSUE_TEMPLATE/
- [ ] .github/PULL_REQUEST_TEMPLATE.md
EOF
```

**Review the inventory**:
1. Open `/tmp/repo_inventory.txt`
2. For each file, decide: Keep, Archive, or Delete
3. Mark in REPOSITORY_AUDIT.md

#### Task 1.2: Create Internal Archive Structure (30 min)

```bash
# Create archive directory (not tracked by git)
mkdir -p backup_internal/{planning,docs,notes}

# Update .gitignore to exclude it
cat >> .gitignore << 'EOF'

# Internal planning and archives (not for public repo)
backup_internal/
EOF
```

#### Task 1.3: Move Planning Documents (90 min)

**Carefully move internal planning docs**:

```bash
# Move alpha planning docs
mv ALPHA_FEEDBACK_TRACKING.md backup_internal/planning/
mv V0.5.0_BETA_PLANNING.md backup_internal/planning/
mv ALPHA_RELEASE_IMPLEMENTATION_PLAN.md backup_internal/planning/
mv README_REFINEMENT_PLAN.md backup_internal/planning/
mv ALPHA_RELEASE_TODO_CLEANUP_PLAN.md backup_internal/planning/

# Move implementation plans (these are useful internally but cluttered for users)
cp -r docs/implementation_plans/ backup_internal/planning/
# Keep only v0.5.0_beta plans in docs for current work
rm -rf docs/implementation_plans/complete_linear_plan/
rm -rf docs/implementation_plans/archive/

# Move any other internal docs
if [ -d "docs/internal" ]; then
  mv docs/internal/ backup_internal/docs/
fi

# Move backup markdown
if [ -d "backup_markdown_20251114_094729" ]; then
  mv backup_markdown_20251114_094729/ backup_internal/
fi

# Verify what's left
ls -la | grep -E "\.md$"
# Should only see: README.md, CHANGELOG.md, LICENSE (and maybe CONTRIBUTING.md)
```

#### Task 1.4: Verify Clean Repository (60 min)

```bash
# Check git status
git status

# Should see:
# - Deleted: planning markdown files
# - Modified: .gitignore
# - Untracked: backup_internal/ (which is gitignored)

# Check root directory is clean
ls -la
# Should have:
# - README.md
# - CHANGELOG.md
# - LICENSE
# - pyproject.toml
# - .gitignore
# - Makefile (if exists)
# - src/
# - tests/
# - docs/
# - examples/
# - entities/

# No planning docs, no TODO files, no scratch notes
```

**Create a summary**:
```bash
cat > backup_internal/ARCHIVE_SUMMARY.md << 'EOF'
# Repository Cleanup Summary

**Date**: YYYY-MM-DD
**Action**: Moved internal planning docs to backup_internal/

## Moved Files
- ALPHA_FEEDBACK_TRACKING.md
- V0.5.0_BETA_PLANNING.md
- ALPHA_RELEASE_IMPLEMENTATION_PLAN.md
- README_REFINEMENT_PLAN.md
- ALPHA_RELEASE_TODO_CLEANUP_PLAN.md
- docs/implementation_plans/complete_linear_plan/
- backup_markdown_20251114_094729/

## Kept Files
- All source code (src/)
- All tests (tests/)
- Public-facing docs (docs/00_getting_started/, etc.)
- Examples
- Standard files (README, LICENSE, CHANGELOG)

## Rationale
Users don't need to see internal planning documents.
Keeping repository clean and professional for PyPI publication.

## Recovery
All files preserved in backup_internal/
Can be restored if needed.
EOF
```

### Afternoon: Add Standard Files (4 hours)

#### Task 1.5: Create CONTRIBUTING.md (90 min)

Create: `CONTRIBUTING.md`

```markdown
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
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Code refactoring

   ## Testing
   - [ ] All existing tests pass
   - [ ] Added new tests for changes
   - [ ] Tested manually

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] No breaking changes (or documented)

   ## Related Issues
   Fixes #123
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
```

#### Task 1.6: Create CODE_OF_CONDUCT.md (30 min)

Create: `CODE_OF_CONDUCT.md`

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, caste, color, religion, or sexual
identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the overall
  community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or advances of
  any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email address,
  without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
[INSERT CONTACT METHOD - e.g., conduct@specql.dev].

All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.1, available at
[https://www.contributor-covenant.org/version/2/1/code_of_conduct.html][v2.1].

[homepage]: https://www.contributor-covenant.org
[v2.1]: https://www.contributor-covenant.org/version/2/1/code_of_conduct.html
```

#### Task 1.7: Create SECURITY.md (30 min)

Create: `SECURITY.md`

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to: **security@specql.dev** (or your actual email)

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Considerations

### SQL Injection

SpecQL generates SQL code from YAML specifications. While we use parameterized queries where possible, be aware:

- **Generated PL/pgSQL functions** may contain dynamic SQL
- **Always validate** YAML input from untrusted sources
- **Review generated code** before deploying to production

### Code Generation

Generated code should be:
- **Reviewed** before deployment
- **Tested** thoroughly
- **Scanned** with security tools appropriate to the target language

### Dependencies

SpecQL uses several dependencies. We:
- Monitor for security updates
- Update dependencies regularly
- Use tools like `pip-audit` to scan for vulnerabilities

You can check dependencies yourself:
```bash
pip-audit
```

## Security Best Practices

When using SpecQL:

1. **Validate Input**: Don't generate code from untrusted YAML
2. **Review Output**: Inspect generated code before deployment
3. **Use RLS**: Leverage PostgreSQL Row-Level Security
4. **Least Privilege**: Generated database users should have minimum permissions
5. **Keep Updated**: Use the latest SpecQL version

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

We will credit reporters in:
- Security advisory
- Release notes
- CHANGELOG.md

Unless you prefer to remain anonymous.
```

#### Task 1.8: Create GitHub Issue Templates (60 min)

Create directory and templates:

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

**Bug Report Template**: `.github/ISSUE_TEMPLATE/bug_report.md`
```markdown
---
name: Bug Report
about: Report a bug in SpecQL
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear description of the bug.

## To Reproduce
Steps to reproduce the behavior:
1. Create YAML file: '...'
2. Run command: '...'
3. See error: '...'

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- SpecQL Version: [e.g., 0.4.0-alpha]
- Python Version: [e.g., 3.11.5]
- OS: [e.g., macOS 14.0, Ubuntu 22.04]
- Installation Method: [source/PyPI]

## YAML Specification
```yaml
# Paste your YAML that triggers the bug
```

## Generated Code (if applicable)
```sql
-- Paste relevant generated code
```

## Error Message
```
Paste full error message and stack trace
```

## Additional Context
Any other information about the problem.
```

**Feature Request Template**: `.github/ISSUE_TEMPLATE/feature_request.md`
```markdown
---
name: Feature Request
about: Suggest a new feature
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description
Clear description of the feature you'd like.

## Use Case
Describe the problem this feature solves.

Example:
"I want to generate X because..."

## Proposed Solution
How you imagine this working.

## YAML Example
```yaml
# Show how you'd like to write it
entity: Example
# ...
```

## Expected Output
What code should be generated.

## Alternatives Considered
Other solutions you've thought about.

## Additional Context
Any other information about the feature.
```

**Pull Request Template**: `.github/PULL_REQUEST_TEMPLATE.md`
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

---

## Day 2: PyPI Metadata Configuration (8 hours)

### Morning: Update pyproject.toml (4 hours)

#### Task 2.1: Audit Current pyproject.toml (60 min)

**Read and understand current structure**:

```bash
# Review current file
cat pyproject.toml

# Check what's missing for PyPI
# Reference: https://packaging.python.org/specifications/declaring-project-metadata/
```

**Create audit checklist**:
```markdown
# pyproject.toml PyPI Compliance Checklist

## Required Fields
- [ ] name
- [ ] version
- [ ] description (or readme)
- [ ] requires-python
- [ ] license
- [ ] authors

## Recommended Fields
- [ ] readme
- [ ] keywords
- [ ] classifiers
- [ ] urls (homepage, repository, documentation, etc.)
- [ ] dependencies
- [ ] optional-dependencies
- [ ] scripts (CLI entry points)

## Build System
- [ ] build-system.requires
- [ ] build-system.build-backend

## Current Status
- ✅ Has: [list what exists]
- ❌ Missing: [list what's missing]
```

#### Task 2.2: Add Missing Metadata Fields (90 min)

**Update `pyproject.toml`**:

Open `pyproject.toml` and ensure it has complete metadata:

```toml
[project]
name = "specql-generator"
version = "0.4.0-alpha"
description = "Multi-language backend code generator from YAML specifications"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Lionel Hamayon", email = "lionel.hamayon@evolution-digitale.fr"}
]
keywords = [
    "postgresql",
    "code-generation",
    "backend",
    "multi-language",
    "java",
    "rust",
    "typescript",
    "python",
    "spring-boot",
    "diesel",
    "prisma",
    "graphql",
    "fraiseql",
    "orm",
    "database",
    "schema-generator",
    "reverse-engineering",
    "yaml",
    "plpgsql",
    "low-code",
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Code Generators",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: SQL",
    "Programming Language :: Java",
    "Programming Language :: Rust",
    "Operating System :: OS Independent",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/fraiseql/specql"
Repository = "https://github.com/fraiseql/specql"
Documentation = "https://github.com/fraiseql/specql/blob/main/docs/00_getting_started/README.md"
"Bug Tracker" = "https://github.com/fraiseql/specql/issues"
Changelog = "https://github.com/fraiseql/specql/blob/main/CHANGELOG.md"
"Getting Started" = "https://github.com/fraiseql/specql/blob/main/docs/00_getting_started/QUICKSTART.md"

# Keep existing dependencies section unchanged
[project.dependencies]
# ... existing dependencies ...

[project.optional-dependencies]
# ... existing optional dependencies ...

# Keep existing scripts
[project.scripts]
specql = "src.cli.confiture_extensions:specql"

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Hatch configuration
[tool.hatch.build.targets.wheel]
packages = ["src"]

# Exclude test files and internal docs from package
[tool.hatch.build.targets.wheel.force-include]
# Include only what's needed

[tool.hatch.build.targets.sdist]
exclude = [
    "/.github",
    "/tests",
    "/backup_internal",
    "/.git",
    "/.vscode",
    "/.idea",
]

# Keep existing tool configurations
[tool.pytest.ini_options]
# ... existing ...

[tool.ruff]
# ... if exists ...

[tool.mypy]
# ... if exists ...
```

#### Task 2.3: Verify PyPI Classifiers (30 min)

**Check classifier validity**:

```bash
# Install classifier validator
pip install trove-classifiers

# Check if classifiers are valid
python -c "
from trove_classifiers import classifiers
import tomli

with open('pyproject.toml', 'rb') as f:
    config = tomli.load(f)

project_classifiers = config['project']['classifiers']
valid_classifiers = set(classifiers)

for cls in project_classifiers:
    if cls not in valid_classifiers:
        print(f'❌ Invalid: {cls}')
    else:
        print(f'✅ Valid: {cls}')
"
```

**Reference**: https://pypi.org/classifiers/

#### Task 2.4: Add Long Description (60 min)

PyPI will use `README.md` as the long description. Ensure it's formatted correctly:

**Test README rendering**:

```bash
# Install readme renderer
pip install readme-renderer

# Check if README renders correctly
python -c "
from readme_renderer.markdown import render

with open('README.md', 'r') as f:
    content = f.read()

rendered = render(content)
if rendered is None:
    print('❌ README has rendering issues')
else:
    print('✅ README will render correctly on PyPI')
    print(f'Length: {len(rendered)} characters')
"
```

**If issues found**, fix README.md:
- Remove custom HTML that PyPI doesn't support
- Ensure all image links are absolute URLs
- Check markdown syntax is valid

### Afternoon: Package Configuration (4 hours)

#### Task 2.5: Configure Package Exclusions (90 min)

**Define what to include/exclude** in the package:

Update `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]

# Explicitly exclude development files
[tool.hatch.build.targets.sdist]
exclude = [
    "/.github",
    "/tests",
    "/backup_internal",
    "/docs/implementation_plans",  # Internal planning
    "/.git",
    "/.gitignore",
    "/.vscode",
    "/.idea",
    "*.pyc",
    "__pycache__",
    "*.egg-info",
]

# For wheel, only include source code
[tool.hatch.build.targets.wheel.force-include]
"src" = "src"
"README.md" = "README.md"
"LICENSE" = "LICENSE"
"CHANGELOG.md" = "CHANGELOG.md"
```

**Verify with build test**:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Test build
python -m build

# List contents of wheel
python -c "
import zipfile
with zipfile.ZipFile('dist/specql_generator-0.4.0a0-py3-none-any.whl', 'r') as z:
    for name in sorted(z.namelist()):
        print(name)
"

# Check:
# ✅ Should include: src/, README.md, LICENSE, CHANGELOG.md
# ❌ Should NOT include: tests/, .github/, backup_internal/, docs/implementation_plans/
```

#### Task 2.6: Add Package Metadata Files (60 min)

**Create `MANIFEST.in`** (if needed for sdist):

```
# MANIFEST.in
include README.md
include LICENSE
include CHANGELOG.md
include pyproject.toml

recursive-include src *.py
recursive-include src *.yaml
recursive-include src *.j2

recursive-exclude tests *
recursive-exclude backup_internal *
recursive-exclude .github *
```

**Note**: With modern `pyproject.toml` and hatchling, `MANIFEST.in` might not be needed. Test without it first.

#### Task 2.7: Version Management Setup (90 min)

**Decide on version strategy**:

**Option A: Manual version in pyproject.toml** (simplest for now)
```toml
[project]
version = "0.4.0-alpha"
```

**Option B: Dynamic version from git tags**
```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

**Recommendation for v0.4.0-alpha**: Use Option A (manual). Simpler for first release.

**Create version update script** for future:

```bash
cat > scripts/update_version.sh << 'EOF'
#!/bin/bash
# Update version in pyproject.toml and create git tag

if [ -z "$1" ]; then
    echo "Usage: ./update_version.sh <version>"
    echo "Example: ./update_version.sh 0.5.0"
    exit 1
fi

NEW_VERSION="$1"

# Update pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update CHANGELOG.md (add date)
TODAY=$(date +%Y-%m-%d)
sed -i.bak "s/\[Unreleased\]/[$NEW_VERSION] - $TODAY/" CHANGELOG.md
rm CHANGELOG.md.bak

echo "✅ Updated version to $NEW_VERSION"
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit: git commit -am 'chore: bump version to $NEW_VERSION'"
echo "  3. Tag: git tag -a v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "  4. Push: git push && git push --tags"
EOF

chmod +x scripts/update_version.sh
```

---

## Day 3: Build Testing & Validation (8 hours)

### Morning: Build Process Testing (4 hours)

#### Task 3.1: Install Build Tools (30 min)

```bash
# Install build tools
uv pip install build twine wheel

# Verify installations
python -m build --version
twine --version
```

#### Task 3.2: Clean Build Test (90 min)

**Perform a clean build**:

```bash
# Clean everything
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# Build package
python -m build

# Should create:
# dist/specql_generator-0.4.0a0-py3-none-any.whl
# dist/specql_generator-0.4.0a0.tar.gz
```

**Inspect build artifacts**:

```bash
# Check wheel contents
unzip -l dist/specql_generator-0.4.0a0-py3-none-any.whl

# Expected structure:
# src/
#   __init__.py
#   core/
#   generators/
#   parsers/
#   ...
# specql_generator-0.4.0a0.dist-info/
#   METADATA
#   WHEEL
#   entry_points.txt
#   ...
# README.md (or in METADATA)
# LICENSE

# Check metadata
unzip -p dist/specql_generator-0.4.0a0-py3-none-any.whl specql_generator-0.4.0a0.dist-info/METADATA

# Verify:
# - Name: specql-generator
# - Version: 0.4.0a0
# - Summary: (description)
# - Keywords: (keywords)
# - Classifiers: (classifiers)
# - Description: (README content)
```

**Check source distribution**:

```bash
tar -tzf dist/specql_generator-0.4.0a0.tar.gz | head -30

# Should include:
# - src/
# - README.md
# - LICENSE
# - pyproject.toml
# - CHANGELOG.md

# Should NOT include:
# - tests/
# - .github/
# - backup_internal/
```

#### Task 3.3: Validate with Twine (60 min)

```bash
# Check package for PyPI compliance
twine check dist/*

# Expected output:
# Checking dist/specql_generator-0.4.0a0-py3-none-any.whl: PASSED
# Checking dist/specql_generator-0.4.0a0.tar.gz: PASSED

# If WARNINGS or FAILED:
# - Read error messages carefully
# - Fix issues in pyproject.toml or README.md
# - Rebuild and check again
```

**Common issues and fixes**:

| Issue | Fix |
|-------|-----|
| `long_description has syntax errors` | Fix README.md markdown |
| `Missing required field: X` | Add to pyproject.toml |
| `Invalid classifier` | Check against https://pypi.org/classifiers/ |
| `README has rendering issues` | Test with `readme-renderer` |

### Afternoon: Installation Testing (4 hours)

#### Task 3.4: Test Clean Installation (90 min)

**Create fresh virtual environment**:

```bash
# Create test directory
mkdir -p /tmp/test-specql-install
cd /tmp/test-specql-install

# Create clean venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify clean Python
which python
# Should show: /tmp/test-specql-install/venv/bin/python

python -c "import sys; print(sys.path)"
# Should NOT include your dev specql directory
```

**Install from wheel**:

```bash
# Install from built wheel
pip install ~/code/specql/dist/specql_generator-0.4.0a0-py3-none-any.whl

# Check installation
pip show specql-generator
# Should show:
# Name: specql-generator
# Version: 0.4.0a0
# Summary: ...
# Location: /tmp/test-specql-install/venv/lib/python3.11/site-packages
```

**Test installed package**:

```bash
# Test CLI
specql --version
# Expected: 0.4.0-alpha

specql --help
# Should show help text

# Test Python import
python -c "
from src.core.specql_parser import SpecQLParser
from src.generators.postgresql import PostgreSQLGenerator
print('✅ Imports work')
"

# Test actual usage
mkdir test_project
cd test_project

# Create simple YAML
cat > contact.yaml << 'EOF'
entity: Contact
schema: test

fields:
  name: text
  email: email
EOF

# Generate code
specql generate contact.yaml

# Check output exists
ls -la output/
# Should have generated SQL files
```

**Test from source distribution**:

```bash
# New clean venv
cd /tmp
python -m venv venv-sdist
source venv-sdist/bin/activate

# Install from tar.gz
pip install ~/code/specql/dist/specql_generator-0.4.0a0.tar.gz

# Run same tests as above
specql --version
# ...
```

#### Task 3.5: Test Dependency Installation (90 min)

**Verify all dependencies install**:

```bash
# Clean venv
cd /tmp
python -m venv venv-deps
source venv-deps/bin/activate

# Install package
pip install ~/code/specql/dist/specql_generator-0.4.0a0-py3-none-any.whl

# Check all dependencies were installed
pip list | grep -E "(pyyaml|jinja2|click|rich|psycopg)"

# Should see all listed dependencies from pyproject.toml
```

**Test optional dependencies**:

```bash
# Test pattern library extra
pip install ~/code/specql/dist/specql_generator-0.4.0a0-py3-none-any.whl[patterns]

# Check pattern-specific deps installed
pip list | grep -E "(sentence-transformers|pgvector)"

# Test Java extra
pip install ~/code/specql/dist/specql_generator-0.4.0a0-py3-none-any.whl[java]
pip list | grep "py4j"

# Test dev extra
pip install ~/code/specql/dist/specql_generator-0.4.0a0-py3-none-any.whl[dev]
pip list | grep -E "(pytest|ruff|mypy)"
```

---

## Day 4: TestPyPI Upload (8 hours)

### Morning: TestPyPI Setup (4 hours)

#### Task 4.1: Create TestPyPI Account (30 min)

1. Go to https://test.pypi.org/account/register/
2. Fill in registration form
3. Verify email address
4. Set up two-factor authentication (recommended)

#### Task 4.2: Create API Token (30 min)

1. Go to https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. **Token name**: `specql-testpypi-upload`
4. **Scope**: "Entire account" (for first upload)
5. Copy the token (starts with `pypi-`)
6. **Important**: Save it securely, you won't see it again

#### Task 4.3: Configure Twine Credentials (30 min)

**Create `~/.pypirc`**:

```bash
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE-PLACEHOLDER-FOR-NOW
EOF

# Secure the file
chmod 600 ~/.pypirc
```

Replace `pypi-YOUR-TESTPYPI-TOKEN-HERE` with your actual token.

**Verify configuration**:

```bash
# Check file exists and is secure
ls -la ~/.pypirc
# Should show: -rw------- (only you can read/write)
```

#### Task 4.4: Pre-Upload Checklist (90 min)

**Create comprehensive checklist**:

```markdown
# TestPyPI Upload Checklist

## Pre-Upload Verification

### Code Quality
- [ ] All tests pass: `uv run pytest`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] Type checking passes: `uv run mypy src/`
- [ ] Coverage >90%: `uv run pytest --cov=src`

### Documentation
- [ ] README.md accurate and complete
- [ ] CHANGELOG.md updated
- [ ] All docs reviewed
- [ ] No broken links

### Repository
- [ ] All internal docs moved to backup_internal/
- [ ] Root directory clean
- [ ] .gitignore includes backup_internal/
- [ ] CONTRIBUTING.md exists
- [ ] CODE_OF_CONDUCT.md exists
- [ ] SECURITY.md exists
- [ ] Issue templates exist

### Package Configuration
- [ ] pyproject.toml has complete metadata
- [ ] Version is correct: 0.4.0-alpha
- [ ] All classifiers valid
- [ ] Keywords relevant
- [ ] URLs correct

### Build
- [ ] Clean build succeeds: `python -m build`
- [ ] Twine check passes: `twine check dist/*`
- [ ] Wheel contains correct files
- [ ] Source dist contains correct files
- [ ] No test files in wheel
- [ ] No internal docs in wheel

### Installation Testing
- [ ] Installs from wheel in clean venv
- [ ] CLI works after install
- [ ] Python imports work
- [ ] Can generate code
- [ ] All dependencies install correctly

### Git
- [ ] All changes committed
- [ ] Working directory clean: `git status`
- [ ] On correct branch
EOF
```

**Work through checklist**, fixing any issues found.

### Afternoon: Upload to TestPyPI (4 hours)

#### Task 4.5: Upload to TestPyPI (60 min)

**Ensure clean build**:

```bash
cd ~/code/specql

# Clean previous builds
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# Fresh build
python -m build

# Verify
twine check dist/*
# Must show: PASSED
```

**Upload to TestPyPI**:

```bash
# Upload
twine upload --repository testpypi dist/*

# You'll see:
# Uploading distributions to https://test.pypi.org/legacy/
# Uploading specql_generator-0.4.0a0-py3-none-any.whl
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 125.3/125.3 kB • 00:00 • 1.5 MB/s
# Uploading specql_generator-0.4.0a0.tar.gz
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 95.2/95.2 kB • 00:00 • 1.2 MB/s
#
# View at:
# https://test.pypi.org/project/specql-generator/0.4.0a0/

# If successful, you'll get a URL to view the package
```

**If errors occur**:
- Read error message carefully
- Common issues:
  - "File already exists" → Version already uploaded, increment version
  - "Invalid authentication" → Check ~/.pypirc token
  - "Invalid metadata" → Fix pyproject.toml, rebuild, try again

#### Task 4.6: Verify TestPyPI Page (90 min)

**Open the TestPyPI page**:

```bash
# URL from upload output or:
open https://test.pypi.org/project/specql-generator/
```

**Verify everything**:

Checklist:
```markdown
# TestPyPI Page Verification

## Project Page
- [ ] Project name correct: "specql-generator"
- [ ] Version shown: 0.4.0a0
- [ ] Description renders correctly (README.md content)
- [ ] No rendering errors in description
- [ ] Images load (if any absolute URLs in README)

## Meta Information
- [ ] License shows: MIT
- [ ] Author shows: Lionel Hamayon
- [ ] Classifiers all present
- [ ] Keywords all present
- [ ] Python version requirements correct: >=3.11

## Links
- [ ] Homepage link works
- [ ] Repository link works
- [ ] Documentation link works
- [ ] Bug Tracker link works
- [ ] Changelog link works

## Dependencies
- [ ] All dependencies listed
- [ ] Optional dependencies shown
- [ ] No unexpected dependencies

## Download Files
- [ ] Wheel file listed (.whl)
- [ ] Source distribution listed (.tar.gz)
- [ ] File sizes reasonable
- [ ] Can download files
EOF
```

**Screenshot issues** if any, for documentation.

#### Task 4.7: Test Installation from TestPyPI (90 min)

**Critical test - installing as a real user would**:

```bash
# Fresh machine simulation
cd /tmp
mkdir testpypi-install-test
cd testpypi-install-test

# Clean venv
python -m venv venv
source venv/bin/activate

# Install from TestPyPI
# Note: TestPyPI doesn't have all packages, so we need --extra-index-url for dependencies
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ specql-generator

# Watch the output:
# - Should download specql-generator from TestPyPI
# - Should download dependencies from PyPI
# - Should complete without errors
```

**Verify installation**:

```bash
# Check version
specql --version
# Should show: 0.4.0-alpha

# Check help
specql --help

# Test generation
mkdir test
cd test

cat > entity.yaml << 'EOF'
entity: TestEntity
schema: test
fields:
  name: text
  email: email
EOF

specql generate entity.yaml

# Check output
ls -la output/
cat output/test/01_tables.sql
# Should have generated SQL

# Test Python imports
python << 'EOF'
from src.core.specql_parser import SpecQLParser
from src.generators.postgresql import PostgreSQLGenerator
print("✅ All imports successful")
EOF
```

**Test optional dependencies**:

```bash
# Test with extras
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ specql-generator[patterns]

# Verify pattern library deps
python -c "import sentence_transformers; print('✅ Patterns extra works')"
```

**Document any issues**:

```markdown
# TestPyPI Installation Test Results

**Date**: YYYY-MM-DD
**Platform**: OS and version

## Installation
- [ ] Package found on TestPyPI
- [ ] Downloaded successfully
- [ ] Dependencies installed
- [ ] No errors during install

## Functionality
- [ ] CLI command works
- [ ] Help displays correctly
- [ ] Can generate code
- [ ] Python imports work
- [ ] Examples work

## Issues Found
1. [Issue description] - Severity: High/Medium/Low
2. [Issue description] - Severity: High/Medium/Low

## Resolution
- [How issues were fixed]

## Conclusion
✅ Ready for PyPI
❌ Needs fixes before PyPI
```

---

## Day 5: Documentation for Publication (8 hours)

### Task 5.1: Update README for PyPI (3 hours)

**Ensure README is PyPI-optimized**:

```markdown
# SpecQL - Multi-Language Backend Code Generator

[![PyPI version](https://img.shields.io/pypi/v/specql-generator.svg)](https://test.pypi.org/project/specql-generator/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **⚠️ Alpha Release**: v0.4.0-alpha is production-ready for backend generation. APIs may evolve. [Report issues](https://github.com/fraiseql/specql/issues).

**Generate PostgreSQL + Java + Rust + TypeScript from single YAML spec**

[Rest of README...]

## Installation

### From PyPI (Recommended)

```bash
pip install specql-generator
```

### From Source

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
pip install -e .
```

[Continue with quickstart...]
```

Update badges to point to TestPyPI for now.

### Task 5.2: Prepare Release Notes (2 hours)

**Update CHANGELOG.md**:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0-alpha] - 2025-11-XX

### Added
- Multi-language code generation (PostgreSQL, Java, Rust, TypeScript)
- Reverse engineering for PostgreSQL, Python, Java, Rust, TypeScript
- FraiseQL integration for GraphQL auto-discovery
- Pattern library with 100+ reusable patterns
- Interactive CLI with live preview
- Visual schema diagrams (Graphviz/Mermaid)
- CI/CD workflow generation (5 platforms)
- Infrastructure as Code generation (Terraform, K8s, Docker Compose)
- Test generation (pgTAP, pytest)
- Comprehensive documentation (100+ pages)
- 30+ working examples

### Changed
- First public alpha release
- Published to PyPI

### Technical Details
- 6,173 lines of code
- 96%+ test coverage
- 100x code leverage demonstrated
- Performance: 1,461 entities/sec (Java), 37,233 entities/sec (TypeScript)

## [0.3.0] - Internal
[Previous internal versions...]

[unreleased]: https://github.com/fraiseql/specql/compare/v0.4.0-alpha...HEAD
[0.4.0-alpha]: https://github.com/fraiseql/specql/releases/tag/v0.4.0-alpha
```

### Task 5.3: Create Migration Guide (1 hour)

For users of previous versions (if applicable):

Create: `docs/migration/TO_0.4.0_ALPHA.md`

### Task 5.4: Final Documentation Review (2 hours)

**Complete review checklist**:

```markdown
# Final Documentation Review

## Core Docs
- [ ] README.md optimized for PyPI
- [ ] CHANGELOG.md complete
- [ ] CONTRIBUTING.md clear
- [ ] LICENSE correct
- [ ] SECURITY.md appropriate

## Getting Started
- [ ] Installation instructions include PyPI
- [ ] Quickstart works end-to-end
- [ ] Prerequisites clearly listed

## Links
- [ ] All internal links work
- [ ] All external links work
- [ ] No broken references

## Content
- [ ] No TODOs left
- [ ] No placeholders
- [ ] No internal jargon
- [ ] Beginner-friendly language
```

---

## Week 2 Deliverables Checklist

At the end of Week 2, you should have:

### Repository Structure
- [ ] Clean root directory (only essential files)
- [ ] Internal docs moved to backup_internal/
- [ ] Standard files present (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY)
- [ ] GitHub templates created (.github/ISSUE_TEMPLATE/, PR template)

### PyPI Configuration
- [ ] pyproject.toml has complete metadata
- [ ] All PyPI classifiers valid
- [ ] Keywords optimized for discovery
- [ ] URLs all working
- [ ] Package excludes test files
- [ ] README renders correctly on PyPI

### Build & Test
- [ ] Clean build succeeds
- [ ] Twine check passes
- [ ] Installs in clean venv from wheel
- [ ] Installs in clean venv from source dist
- [ ] CLI works after install
- [ ] All functionality tested

### TestPyPI
- [ ] Package uploaded to TestPyPI
- [ ] TestPyPI page looks correct
- [ ] Can install from TestPyPI
- [ ] All features work when installed from TestPyPI
- [ ] No critical issues found

### Documentation
- [ ] README optimized for PyPI
- [ ] CHANGELOG updated for v0.4.0-alpha
- [ ] All links verified
- [ ] Installation instructions include PyPI

---

## Common Issues & Solutions

### Build Issues

**Issue**: `ModuleNotFoundError` during build
**Solution**: Ensure all imports use absolute imports from `src`

**Issue**: "Invalid classifier"
**Solution**: Check https://pypi.org/classifiers/ for valid classifiers

**Issue**: "README has rendering issues"
**Solution**: Test with `readme-renderer` and fix markdown syntax

### Upload Issues

**Issue**: "403 Forbidden" on upload
**Solution**: Check ~/.pypirc has correct token

**Issue**: "File already exists"
**Solution**: Increment version number, rebuild, try again

**Issue**: "Invalid metadata"
**Solution**: Run `twine check dist/*` for details, fix pyproject.toml

### Installation Issues

**Issue**: "No matching distribution found"
**Solution**: Check Python version requirement matches

**Issue**: "Dependency X not found"
**Solution**: Ensure --extra-index-url https://pypi.org/simple/ when installing from TestPyPI

---

## Next Steps

After Week 2:
- Week 3: Upload to production PyPI
- Week 4: User experience improvements
- Week 5: Marketing content creation
- Week 6: Community launch

**Next Week**: [Week 3 - PyPI Publication & Testing](WEEK_03_PYPI_PUBLICATION_TESTING.md)
