# Contributing to SpecQL

Welcome! This guide explains how to contribute to the SpecQL project, whether you're fixing bugs, adding features, improving documentation, or helping with testing.

## Ways to Contribute

### 🐛 Bug Reports
Found a bug? Help us fix it!

1. **Check existing issues** - Search [GitHub Issues](https://github.com/your-org/specql/issues) first
2. **Create a minimal reproduction** - Provide the smallest possible example that demonstrates the issue
3. **Include environment details** - Python version, OS, SpecQL version
4. **Describe expected vs actual behavior**

### ✨ Feature Requests
Have an idea for a new feature?

1. **Check the roadmap** - Review [ROADMAP.md](../../ROADMAP.md) and [implementation plans](../../docs/implementation_plans/)
2. **Start a discussion** - Open a [GitHub Discussion](https://github.com/your-org/specql/discussions) to gather feedback
3. **Create an issue** - Use the "Feature Request" template

### 📖 Documentation
Help improve our documentation!

1. **Fix typos and errors** - Every fix helps
2. **Add examples** - More examples make SpecQL easier to learn
3. **Improve guides** - Share your experience and insights
4. **Translate documentation** - Help make SpecQL accessible globally

### 🧪 Testing
Help ensure SpecQL works correctly!

1. **Write tests** - Add unit, integration, or E2E tests
2. **Test on different platforms** - Windows, macOS, Linux
3. **Performance testing** - Help benchmark and optimize
4. **Compatibility testing** - Test with different PostgreSQL versions

### 💻 Code Contributions
Ready to write code?

1. **Fix bugs** - Look for issues labeled "good first issue" or "help wanted"
2. **Add features** - Implement features from the roadmap
3. **Refactor code** - Improve code quality and maintainability
4. **Add integrations** - Support new frameworks or databases

## Development Setup

### Prerequisites

- **Python 3.9+** - Required for development
- **PostgreSQL** - For testing generated SQL
- **Git** - Version control
- **uv** - Fast Python package manager (recommended)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/specql.git
cd specql

# Install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install

# Run tests to verify setup
uv run pytest tests/unit/ -x
```

### Development Workflow

We follow a disciplined TDD (Test-Driven Development) approach with phases:

#### 🔴 RED Phase - Write Failing Tests
```bash
# Write test first
uv run pytest tests/unit/test_my_feature.py::test_new_functionality -v
# Expected: Test fails (functionality not implemented yet)
```

#### 🟢 GREEN Phase - Implement Minimal Code
```bash
# Implement just enough code to make the test pass
uv run pytest tests/unit/test_my_feature.py::test_new_functionality -v
# Expected: Test passes
```

#### 🔧 REFACTOR Phase - Clean and Optimize
```bash
# Improve code quality while keeping tests passing
uv run pytest tests/unit/test_my_feature.py -v
uv run ruff check src/
uv run mypy src/
```

#### ✅ QA Phase - Comprehensive Testing
```bash
# Run full test suite
uv run pytest

# Performance testing
uv run pytest tests/performance/

# Integration testing
uv run pytest tests/integration/
```

## Code Standards

### Python Code Style

We use modern Python practices:

```python
# ✅ Good: Type hints, descriptive names, docstrings
def calculate_total(items: List[Dict[str, Any]], tax_rate: Decimal) -> Decimal:
    """Calculate total amount including tax.

    Args:
        items: List of items with price and quantity
        tax_rate: Tax rate as decimal (e.g., Decimal('0.08'))

    Returns:
        Total amount including tax
    """
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    return subtotal * (1 + tax_rate)

# ❌ Bad: No type hints, unclear names, no docstring
def calc(items, tax):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total * (1 + tax)
```

### Key Standards

- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions
- **Naming**: Use descriptive names (e.g., `calculate_total` not `calc`)
- **Imports**: Group imports (stdlib, third-party, local) with blank lines
- **Line Length**: Keep lines under 88 characters (Black default)
- **Error Handling**: Use specific exceptions, provide helpful error messages

### Code Quality Tools

We use automated tools to maintain quality:

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Import sorting
uv run isort src/ tests/

# Security checks
uv run bandit src/

# All quality checks
uv run pre-commit run --all-files
```

## Testing Guidelines

### Test Categories

#### Unit Tests
Test individual functions and classes in isolation:

```python
# tests/unit/generators/test_sql_generator.py
def test_generate_simple_table():
    """Test generating a simple table without relations."""
    entity = {
        "name": "User",
        "fields": [
            {"name": "id", "type": "uuid", "primary_key": True},
            {"name": "email", "type": "text", "required": True}
        ]
    }

    generator = SQLGenerator()
    sql = generator.generate_table(entity)

    assert "CREATE TABLE app.tb_user" in sql
    assert "id UUID PRIMARY KEY" in sql
    assert "email TEXT NOT NULL" in sql
```

#### Integration Tests
Test component interactions:

```python
# tests/integration/test_entity_generation.py
def test_generate_complete_entity():
    """Test generating a complete entity with patterns."""
    yaml_content = """
    entity: Contact
    patterns:
      - audit_trail
      - state_machine
    fields:
      name: text
      email: text
    """

    # Generate for all targets
    results = generate_entity(yaml_content, targets=['postgresql', 'django'])

    # Verify PostgreSQL generation
    assert 'CREATE TABLE' in results['postgresql']
    assert 'state' in results['postgresql']
    assert 'created_at' in results['postgresql']

    # Verify Django generation
    assert 'class Contact(models.Model)' in results['django']
    assert 'state' in results['django']
```

#### E2E Tests
Test complete user workflows:

```python
# tests/e2e/test_crm_workflow.py
def test_crm_contact_lifecycle():
    """Test complete CRM contact lifecycle."""
    # Create contact
    contact = create_contact({
        'name': 'John Doe',
        'email': 'john@example.com'
    })

    # Update contact
    update_contact(contact.id, {'name': 'Jane Doe'})

    # Verify audit trail
    history = get_contact_history(contact.id)
    assert len(history) == 2  # create + update

    # Delete contact (soft delete)
    delete_contact(contact.id)
    assert contact_is_deleted(contact.id)
```

### Test Best Practices

1. **Descriptive Names**: `test_calculate_total_with_tax` not `test_calc`
2. **One Assertion Per Test**: Keep tests focused
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Reuse test data setup
5. **Mock External Dependencies**: Isolate unit tests
6. **Test Edge Cases**: Don't just test happy paths

### Performance Testing

```python
# tests/performance/test_generation_speed.py
def test_generation_performance():
    """Test that entity generation is fast enough."""
    entity_yaml = load_complex_entity()

    start_time = time.time()
    sql = generate_schema(entity_yaml, target='postgresql')
    duration = time.time() - start_time

    # Should generate in under 500ms
    assert duration < 0.5

    # Generated SQL should be valid
    assert is_valid_postgresql(sql)
```

## Submitting Changes

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/add-user-preferences

# Or create bug fix branch
git checkout -b fix/validation-error-message
```

### 2. Make Changes

Follow the TDD cycle:
- Write failing test
- Implement minimal code
- Refactor and clean up
- Run full test suite

### 3. Run Quality Checks

```bash
# Run all pre-commit checks
uv run pre-commit run --all-files

# Run tests
uv run pytest

# Run performance tests
uv run pytest tests/performance/
```

### 4. Update Documentation

If your changes affect users:

```bash
# Update relevant documentation
vim docs/guides/entity_definition.md

# Add examples if needed
vim docs/examples/new_feature_example.yaml
```

### 5. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add user preferences functionality

- Add user preferences table
- Add preference management functions
- Add validation for preference values
- Add tests for preference operations

Closes #123"
```

### 6. Create Pull Request

```bash
# Push your branch
git push origin feature/add-user-preferences

# Create PR on GitHub
# - Use descriptive title
# - Fill out PR template
# - Link related issues
# - Request review from maintainers
```

## Pull Request Guidelines

### PR Title Format
```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Examples:
- feat(auth): add OAuth2 login support
- fix(validation): correct email regex pattern
- docs(api): update CLI reference
- test(performance): add benchmark for large entities
```

### PR Description Template
```markdown
## Description
Brief description of the changes and why they're needed.

## Changes Made
- Change 1 with impact
- Change 2 with impact
- Change 3 with impact

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Performance tests pass
- [ ] Manual testing completed

## Breaking Changes
- [ ] None
- [ ] List any breaking changes

## Screenshots/Examples
If UI changes, include screenshots.

## Related Issues
Closes #123, #124
```

### Review Process

1. **Automated Checks**: CI runs tests, linting, type checking
2. **Code Review**: Maintainers review code quality and design
3. **Testing Review**: Ensure adequate test coverage
4. **Documentation Review**: Verify docs are updated
5. **Approval**: At least one maintainer approval required
6. **Merge**: Squash merge with descriptive commit message

## Issue Tracking

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation changes
- `good first issue`: Good for newcomers
- `help wanted`: Community contribution welcome
- `question`: Question or discussion
- `wontfix`: Will not be implemented

### Issue Templates

We use issue templates for:
- Bug reports (with reproduction steps)
- Feature requests (with use cases)
- Documentation issues
- Performance issues
- Security issues

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn
- Maintain professional communication

### Getting Help
- **Documentation**: Check [docs.specql.dev](https://docs.specql.dev)
- **Discussions**: Use [GitHub Discussions](https://github.com/your-org/specql/discussions) for questions
- **Discord**: Join our community server for real-time help
- **Issues**: Use issues for bugs and feature requests

### Recognition
Contributors are recognized through:
- GitHub contributor statistics
- Mention in release notes
- Contributor spotlight in newsletters
- Invitation to become maintainer

## Advanced Contributing

### Becoming a Maintainer

Maintainers have write access and can:
- Review and merge pull requests
- Manage issues and milestones
- Release new versions
- Make architectural decisions

Requirements:
- Consistent quality contributions
- Good understanding of SpecQL architecture
- Active participation in reviews
- Commitment to project goals

### Working on Core Features

For larger features:
1. **Discuss Design**: Open RFC (Request for Comments) issue
2. **Create Implementation Plan**: Break down into manageable tasks
3. **Get Early Feedback**: Share design with maintainers
4. **Iterative Development**: Implement in small, reviewable chunks
5. **Comprehensive Testing**: Ensure thorough test coverage

### Performance Contributions

For performance improvements:
1. **Benchmark First**: Establish baseline performance
2. **Profile Code**: Identify bottlenecks
3. **Optimize Carefully**: Measure impact of changes
4. **Regression Testing**: Ensure no performance regressions

## Resources

- [Architecture Overview](../../docs/architecture/)
- [Testing Guide](../../TESTING.md)
- [Reference Documentation](../../reference/)
- [Development Roadmap](../../ROADMAP.md)
- [Discord Community](https://discord.gg/specql)

---

Thank you for contributing to SpecQL! Your contributions help make business logic specification more powerful and accessible for everyone. 🚀