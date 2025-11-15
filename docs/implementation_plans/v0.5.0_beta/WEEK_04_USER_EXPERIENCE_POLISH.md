# Week 4: User Experience Polish

**Goal**: Improve error messages, add helpful features, and make SpecQL delightful to use.

**Estimated Time**: 35-40 hours (1 week full-time)

**Prerequisites**:
- Week 3 completed (PyPI live)
- Initial user feedback collected
- Common pain points identified

---

## Overview

Based on Week 3 feedback, improve the user experience. Focus on:
- Better error messages
- Helpful CLI features
- Quick-start templates
- Validation with suggestions

---

## Day 1: Error Message Improvements (8 hours)

### Task 1.1: Audit Current Error Messages (2 hours)

**Collect all error scenarios**:

```python
# scripts/audit_errors.py
"""Find all error/exception raising in codebase."""

import ast
import sys
from pathlib import Path

class ErrorCollector(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Raise(self, node):
        if isinstance(node.exc, ast.Call):
            if hasattr(node.exc.func, 'id'):
                error_type = node.exc.func.id
                # Try to get error message
                if node.exc.args and isinstance(node.exc.args[0], ast.Constant):
                    message = node.exc.args[0].value
                    self.errors.append((error_type, message))
        self.generic_visit(node)

# Scan all Python files
for py_file in Path('src').rglob('*.py'):
    with open(py_file) as f:
        tree = ast.parse(f.read())
    collector = ErrorCollector()
    collector.visit(tree)

    for error_type, message in collector.errors:
        print(f"{py_file}: {error_type}: {message}")
```

**Categorize errors**:
```markdown
# Error Message Audit

## Parser Errors
- Invalid YAML syntax
- Missing required fields
- Invalid field types
- Unknown entity references

## Validation Errors
- Circular dependencies
- Invalid enum values
- Constraint conflicts

## Generator Errors
- Unsupported features
- Invalid configurations

## I/O Errors
- File not found
- Permission denied
- Write failures

## Current Issues
- [ ] Generic messages: "Error in field" → "Field 'email' in entity 'Contact' has invalid type 'unknown_type'. Valid types: text, integer, ..."
- [ ] No suggestions: "Invalid enum" → "Invalid enum value 'ACTIV'. Did you mean 'active'?"
- [ ] No context: Just "ValidationError" → Show line number, field, entity
```

### Task 1.2: Create Error Message Framework (3 hours)

**Design helpful error structure**:

```python
# src/core/errors.py
"""Enhanced error handling with helpful messages."""

from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ErrorContext:
    """Context about where error occurred."""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    entity_name: Optional[str] = None
    field_name: Optional[str] = None
    action_name: Optional[str] = None

class SpecQLError(Exception):
    """Base exception for SpecQL with enhanced messaging."""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        suggestion: Optional[str] = None,
        docs_link: Optional[str] = None,
    ):
        self.message = message
        self.context = context
        self.suggestion = suggestion
        self.docs_link = docs_link
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error with context and suggestions."""
        parts = []

        # Main error
        parts.append(f"❌ {self.message}")

        # Context
        if self.context:
            ctx_parts = []
            if self.context.file_path:
                ctx_parts.append(f"File: {self.context.file_path}")
            if self.context.line_number:
                ctx_parts.append(f"Line: {self.context.line_number}")
            if self.context.entity_name:
                ctx_parts.append(f"Entity: {self.context.entity_name}")
            if self.context.field_name:
                ctx_parts.append(f"Field: {self.context.field_name}")
            if self.context.action_name:
                ctx_parts.append(f"Action: {self.context.action_name}")

            if ctx_parts:
                parts.append("  " + " | ".join(ctx_parts))

        # Suggestion
        if self.suggestion:
            parts.append(f"  💡 Suggestion: {self.suggestion}")

        # Documentation
        if self.docs_link:
            parts.append(f"  📚 Docs: {self.docs_link}")

        return "\n".join(parts)


class InvalidFieldTypeError(SpecQLError):
    """Raised when field has invalid type."""

    def __init__(self, field_type: str, valid_types: List[str], context: ErrorContext):
        super().__init__(
            message=f"Invalid field type: '{field_type}'",
            context=context,
            suggestion=f"Valid types: {', '.join(valid_types[:10])}{'...' if len(valid_types) > 10 else ''}",
            docs_link="https://github.com/fraiseql/specql/blob/main/docs/03_reference/FIELD_TYPES.md",
        )


# Example usage:
def validate_field_type(field_type: str, entity_name: str, field_name: str, file_path: str):
    valid_types = ["text", "integer", "decimal", "boolean", "timestamp", "date", "time", "json", "enum", "ref"]

    if field_type not in valid_types:
        raise InvalidFieldTypeError(
            field_type=field_type,
            valid_types=valid_types,
            context=ErrorContext(
                file_path=file_path,
                entity_name=entity_name,
                field_name=field_name,
            ),
        )
```

### Task 1.3: Implement Better Errors (3 hours)

Update key error points:

```python
# src/core/specql_parser.py
from src.core.errors import InvalidFieldTypeError, ErrorContext

class SpecQLParser:
    def parse_field(self, field_data: dict, entity_name: str, file_path: str):
        field_type = field_data.get('type')

        try:
            self.validate_field_type(field_type)
        except ValueError:
            # Instead of generic ValueError
            raise InvalidFieldTypeError(
                field_type=field_type,
                valid_types=VALID_FIELD_TYPES,
                context=ErrorContext(
                    file_path=file_path,
                    entity_name=entity_name,
                    field_name=field_data['name'],
                ),
            )
```

Test the improved errors:
```bash
# Create test case with bad field
cat > test_error.yaml << 'EOF'
entity: Test
schema: test
fields:
  bad_field: unknown_type
EOF

specql generate test_error.yaml

# Should now show:
# ❌ Invalid field type: 'unknown_type'
#   File: test_error.yaml | Entity: Test | Field: bad_field
#   💡 Suggestion: Valid types: text, integer, decimal, boolean, ...
#   📚 Docs: https://github.com/fraiseql/specql/blob/main/docs/03_reference/FIELD_TYPES.md
```

---

## Day 2: `specql init` Command (8 hours)

### Task 2.1: Design Init Command (2 hours)

**Feature spec**:
```markdown
# specql init Command Specification

## Purpose
Scaffold a new SpecQL project with templates and best practices.

## Usage
```bash
specql init [project-name] [--template=blog|crm|ecommerce|minimal]
```

## Behavior
1. Create project directory
2. Generate project structure
3. Add example entities
4. Create README with next steps
5. Initialize git repository (optional)

## Templates

### minimal
- Basic structure
- One example entity
- Minimal documentation

### blog
- Post, Author, Comment, Tag entities
- Complete blog system
- Example queries

### crm
- Contact, Company, Deal, Activity
- Full CRM system
- Business logic examples

### ecommerce
- Product, Order, Customer, Inventory
- E-commerce workflows
- Payment integration examples

## Output Structure
```
my-project/
├── entities/
│   ├── domain1/
│   │   └── entity1.yaml
│   └── domain2/
│       └── entity2.yaml
├── output/           (generated code goes here)
├── README.md
├── .gitignore
└── specql.yaml       (project configuration)
```
```

### Task 2.2: Implement Init Command (4 hours)

```python
# src/cli/commands/init.py
"""Initialize new SpecQL project."""

import click
from pathlib import Path
from typing import Literal

TEMPLATES = {
    "minimal": {
        "description": "Minimal project with one example entity",
        "entities": {
            "example/contact.yaml": """entity: Contact
schema: example

fields:
  name: text
  email: email
  phone: text
"""
        }
    },
    "blog": {
        "description": "Blog platform with posts, authors, comments",
        "entities": {
            "blog/author.yaml": """entity: Author
schema: blog

fields:
  username: text
  email: email
  bio: text
  avatar_url: url

indexes:
  - fields: [username]
    unique: true
""",
            "blog/post.yaml": """entity: Post
schema: blog

fields:
  title: text
  slug: text
  content: text
  author: ref(Author)
  published_at: timestamp
  status: enum(draft, published, archived)

indexes:
  - fields: [slug]
    unique: true

actions:
  - name: publish
    steps:
      - validate: status = 'draft'
      - update: Post SET status = 'published', published_at = NOW()
"""
        }
    },
    # Add more templates...
}

@click.command()
@click.argument('project_name')
@click.option('--template', default='minimal', type=click.Choice(['minimal', 'blog', 'crm', 'ecommerce']))
@click.option('--no-git', is_flag=True, help="Don't initialize git repository")
def init(project_name: str, template: str, no_git: bool):
    """Initialize a new SpecQL project."""

    project_path = Path(project_name)

    # Check if directory exists
    if project_path.exists():
        click.echo(f"❌ Directory '{project_name}' already exists!")
        raise click.Abort()

    # Create project structure
    click.echo(f"Creating SpecQL project: {project_name}")
    click.echo(f"Template: {template}")

    project_path.mkdir()
    (project_path / "entities").mkdir()
    (project_path / "output").mkdir()

    # Create entities from template
    template_data = TEMPLATES[template]
    for entity_file, content in template_data["entities"].items():
        entity_path = project_path / "entities" / entity_file
        entity_path.parent.mkdir(parents=True, exist_ok=True)
        entity_path.write_text(content)
        click.echo(f"  ✓ Created {entity_file}")

    # Create README
    readme_content = f"""# {project_name}

A SpecQL project.

## Getting Started

1. Review entities in `entities/` directory
2. Generate code:
   ```bash
   specql generate entities/**/*.yaml
   ```
3. Check output in `output/` directory

## What's Included

{template_data['description']}

## Next Steps

- Modify entities to match your needs
- Add more entities in `entities/` directory
- Generate code for different targets:
  - `specql generate entities/**/*.yaml --target postgresql`
  - `specql generate entities/**/*.yaml --target java`
  - `specql generate entities/**/*.yaml --target rust`
  - `specql generate entities/**/*.yaml --target typescript`

## Documentation

- [SpecQL Docs](https://github.com/fraiseql/specql/tree/main/docs)
- [Field Types Reference](https://github.com/fraiseql/specql/blob/main/docs/03_reference/FIELD_TYPES.md)
- [Actions Guide](https://github.com/fraiseql/specql/blob/main/docs/02_guides/ACTIONS.md)

## Help

```bash
specql --help
```
"""
    (project_path / "README.md").write_text(readme_content)
    click.echo("  ✓ Created README.md")

    # Create .gitignore
    gitignore_content = """# SpecQL generated output
output/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
"""
    (project_path / ".gitignore").write_text(gitignore_content)
    click.echo("  ✓ Created .gitignore")

    # Initialize git
    if not no_git:
        import subprocess
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from specql init"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            click.echo("  ✓ Initialized git repository")
        except subprocess.CalledProcessError:
            click.echo("  ⚠️  Could not initialize git (is git installed?)")

    # Success message
    click.echo(f"\n✅ Project '{project_name}' created successfully!")
    click.echo(f"\nNext steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  specql generate entities/**/*.yaml")
    click.echo(f"\nHappy coding! 🚀")
```

Register command:
```python
# src/cli/confiture_extensions.py
from src.cli.commands.init import init

@click.group()
def specql():
    """SpecQL code generator."""
    pass

specql.add_command(init)
```

### Task 2.3: Test Init Command (2 hours)

```bash
# Test all templates
cd /tmp

specql init test-minimal --template=minimal
cd test-minimal
specql generate entities/**/*.yaml
cd ..

specql init test-blog --template=blog
cd test-blog
specql generate entities/**/*.yaml
cd ..

# Verify all work correctly
```

---

## Day 3: Validation with Suggestions (8 hours)

### Task 3.1: Fuzzy Matching for Typos (3 hours)

Add suggestion for misspelled values:

```python
# src/utils/suggestions.py
"""Provide helpful suggestions for user errors."""

from difflib import get_close_matches
from typing import List, Optional

def suggest_correction(
    invalid_value: str,
    valid_values: List[str],
    max_suggestions: int = 3,
    cutoff: float = 0.6,
) -> Optional[List[str]]:
    """
    Suggest corrections for misspelled values.

    Args:
        invalid_value: The invalid input
        valid_values: List of valid options
        max_suggestions: Maximum number of suggestions
        cutoff: Similarity threshold (0-1)

    Returns:
        List of suggestions or None
    """
    matches = get_close_matches(
        invalid_value,
        valid_values,
        n=max_suggestions,
        cutoff=cutoff,
    )
    return matches if matches else None


# Example usage
def validate_enum_value(value: str, allowed_values: List[str]):
    if value not in allowed_values:
        suggestions = suggest_correction(value, allowed_values)
        if suggestions:
            raise ValueError(
                f"Invalid enum value: '{value}'. "
                f"Did you mean: {', '.join(suggestions)}?"
            )
        else:
            raise ValueError(
                f"Invalid enum value: '{value}'. "
                f"Valid values: {', '.join(allowed_values)}"
            )
```

### Task 3.2: Add Pre-Generation Validation (3 hours)

```python
# src/cli/commands/validate.py
"""Validate SpecQL files without generating code."""

import click
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.core.validator import SpecQLValidator

@click.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--strict', is_flag=True, help="Fail on warnings")
def validate(files, strict):
    """Validate SpecQL YAML files."""

    if not files:
        click.echo("❌ No files specified")
        return

    parser = SpecQLParser()
    validator = SpecQLValidator()

    errors = []
    warnings = []

    for file_path in files:
        click.echo(f"Validating {file_path}...")

        try:
            # Parse
            entity = parser.parse_file(file_path)

            # Validate
            validation_result = validator.validate(entity)

            if validation_result.errors:
                errors.extend(validation_result.errors)
            if validation_result.warnings:
                warnings.extend(validation_result.warnings)

            if not validation_result.errors:
                click.echo(f"  ✅ {file_path} is valid")

        except Exception as e:
            errors.append(str(e))
            click.echo(f"  ❌ {file_path}: {e}")

    # Summary
    click.echo("\n" + "=" * 50)
    if errors:
        click.echo(f"❌ {len(errors)} error(s) found")
        for error in errors:
            click.echo(f"  - {error}")

    if warnings:
        click.echo(f"⚠️  {len(warnings)} warning(s) found")
        for warning in warnings:
            click.echo(f"  - {warning}")

    if not errors and not warnings:
        click.echo("✅ All files valid!")

    # Exit code
    if errors or (strict and warnings):
        raise click.Abort()
```

### Task 3.3: Implement CI-Friendly Validation (2 hours)

Add GitHub Action validation:

```yaml
# .github/workflows/validate-entities.yml
name: Validate SpecQL Entities

on:
  push:
    paths:
      - 'entities/**/*.yaml'
  pull_request:
    paths:
      - 'entities/**/*.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install SpecQL
        run: pip install specql-generator

      - name: Validate entities
        run: specql validate entities/**/*.yaml --strict
```

Document in `docs/02_guides/CI_VALIDATION.md`.

---

## Day 4: Progress Indicators & Better UX (8 hours)

### Task 4.1: Add Progress Bars (3 hours)

Use `rich` library for better progress:

```python
# src/cli/commands/generate.py
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

def generate_code(entities, output_dir):
    """Generate code with progress bar."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:

        # Overall progress
        task = progress.add_task(
            "[cyan]Generating code...",
            total=len(entities)
        )

        for entity in entities:
            progress.update(task, description=f"[cyan]Generating {entity.name}...")

            # Generate code
            generated = generator.generate(entity)

            progress.update(task, advance=1)

        progress.update(task, description="[green]✓ Generation complete!")
```

### Task 4.2: Interactive Mode Improvements (3 hours)

Enhance existing interactive CLI:

- Add entity preview before generation
- Confirm destructive operations
- Show estimated file count/size
- Preview generated filenames

### Task 4.3: Add `--dry-run` Flag (2 hours)

```python
@click.option('--dry-run', is_flag=True, help="Show what would be generated without writing files")
def generate(files, output_dir, dry_run):
    """Generate code."""

    if dry_run:
        click.echo("🔍 DRY RUN - No files will be written\n")

    # Generate
    result = generator.generate_all(files)

    if dry_run:
        click.echo("Would generate the following files:")
        for file_path in result.file_paths:
            file_size = len(result.get_content(file_path))
            click.echo(f"  - {file_path} ({file_size} bytes)")
        click.echo(f"\nTotal: {len(result.file_paths)} files, {result.total_size()} bytes")
        click.echo("\nRun without --dry-run to write files.")
    else:
        # Actually write files
        result.write_all(output_dir)
        click.echo(f"✅ Generated {len(result.file_paths)} files")
```

---

## Day 5: Quick Reference & Help (8 hours)

### Task 5.1: Add `specql examples` Command (3 hours)

```python
# src/cli/commands/examples.py
@click.command()
@click.argument('example_name', required=False)
@click.option('--list', is_flag=True, help="List all available examples")
def examples(example_name, list):
    """Show example code and usage."""

    EXAMPLES = {
        "simple-entity": {
            "description": "Simple entity with basic fields",
            "yaml": """entity: Contact
schema: crm
fields:
  name: text
  email: email
  phone: text"""
        },
        "with-relationships": {
            "description": "Entity with foreign key relationships",
            "yaml": """entity: Contact
schema: crm
fields:
  name: text
  email: email
  company: ref(Company)  # Foreign key to Company"""
        },
        "with-actions": {
            "description": "Entity with business logic actions",
            "yaml": """entity: Contact
schema: crm
fields:
  name: text
  status: enum(lead, customer)
actions:
  - name: convert_to_customer
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'customer'"""
        },
        # Add more examples...
    }

    if list:
        click.echo("Available examples:\n")
        for name, data in EXAMPLES.items():
            click.echo(f"  {name}: {data['description']}")
        click.echo("\nUsage: specql examples <example-name>")
        return

    if not example_name:
        click.echo("Specify an example name or use --list")
        return

    if example_name not in EXAMPLES:
        click.echo(f"❌ Unknown example: {example_name}")
        click.echo("Use --list to see available examples")
        return

    example = EXAMPLES[example_name]
    click.echo(f"Example: {example_name}")
    click.echo(f"Description: {example['description']}\n")
    click.echo("YAML:")
    click.echo(example['yaml'])
```

### Task 5.2: Improve `--help` Output (2 hours)

Make help more beginner-friendly:

```python
@click.command(help="""
Generate multi-language backend code from YAML specifications.

EXAMPLES:

  # Generate PostgreSQL from all entities
  specql generate entities/**/*.yaml

  # Generate Java code
  specql generate entities/**/*.yaml --target java

  # Specific entity
  specql generate entities/crm/contact.yaml

  # Dry run (see what would be generated)
  specql generate entities/**/*.yaml --dry-run

DOCUMENTATION:

  Getting Started: https://github.com/fraiseql/specql/docs/00_getting_started
  Examples: specql examples --list
  Field Types: https://github.com/fraiseql/specql/docs/03_reference/FIELD_TYPES.md
""")
def generate(...):
    ...
```

### Task 5.3: Create Troubleshooting Guide (3 hours)

Update `docs/08_troubleshooting/COMMON_ISSUES.md`:

```markdown
# Common Issues & Solutions

## Installation Issues

### `pip install specql-generator` fails

**Symptoms**: Error during installation

**Solutions**:
1. Check Python version: `python --version` (need 3.11+)
2. Upgrade pip: `pip install --upgrade pip`
3. Try: `pip install --no-cache-dir specql-generator`

### `specql: command not found`

**Symptoms**: Command not in PATH

**Solutions**:
1. Check if installed: `pip show specql-generator`
2. Find location: `python -m site --user-base`
3. Add to PATH: Add `~/.local/bin` to PATH

## Usage Issues

### "Invalid field type"

**Symptoms**:
```
❌ Invalid field type: 'string'
```

**Solution**: Use `text` instead of `string`
Valid types: text, integer, decimal, boolean, timestamp, ...
[Full list](../03_reference/FIELD_TYPES.md)

### "Circular dependency detected"

**Symptoms**: Entities reference each other

**Solution**: SpecQL supports circular references, but ensure:
- Both entities exist
- Reference is valid: `ref(EntityName)`

[More issues...]
```

---

## Week 4 Deliverables

### Features Added
- [ ] Enhanced error messages with context
- [ ] `specql init` command with templates
- [ ] `specql validate` command
- [ ] `specql examples` command
- [ ] Progress bars and better UX
- [ ] `--dry-run` flag

### Documentation
- [ ] Troubleshooting guide updated
- [ ] Help text improved
- [ ] Examples documented

### Testing
- [ ] All new commands tested
- [ ] Error messages validated
- [ ] Templates work correctly

---

**Next Week**: [Week 5 - Marketing Content Creation](WEEK_05_MARKETING_CONTENT.md)
