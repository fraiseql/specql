"""
Init project subcommand - Create new SpecQL project structure.
"""

from pathlib import Path

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


@click.command()
@click.argument("name")
@click.option("--path", "-p", default=".", help="Parent directory for new project")
@click.option(
    "--template",
    type=click.Choice(["basic", "full", "minimal"]),
    default="basic",
    help="Project template",
)
def project(name, path, template, **kwargs):
    """Create a new SpecQL project with proper directory structure.

    Sets up a complete SpecQL project with:
    - entities/ directory for YAML definitions
    - migrations/ directory for generated SQL
    - confiture.yaml configuration file
    - Basic entity examples and documentation

    Templates:
    - basic: Standard project structure with examples
    - full: Complete setup with CI/CD, docs, and advanced config
    - minimal: Bare-bones structure for custom setup

    Examples:

        specql init project my-app
        specql init project ecommerce --template=full --path=~/projects
    """
    with handle_cli_error():
        parent_path = Path(path)
        project_path = parent_path / name

        output.info(f"🏗️  Creating SpecQL project: {name}")
        output.info(f"📁 Location: {project_path.absolute()}")

        if project_path.exists():
            from cli.utils.error_handler import CLIError

            raise CLIError(f"Directory already exists: {project_path}")

        # Create directory structure
        dirs = ["entities", "migrations", "docs", "tests", ".github/workflows"]

        if template == "full":
            dirs.extend(["infrastructure", "scripts", "docs/api", "docs/architecture"])

        for dir_name in dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Create configuration files
        confiture_content = f"""# SpecQL Configuration for {name}
project:
  name: {name}
  version: "1.0.0"

database:
  default_schema: public
  migrations_dir: migrations

registry:
  enabled: true
  domain_registry: entities/domain_registry.yaml

patterns:
  audit_trail: true
  soft_delete: false
  multi_tenant: false
"""

        (project_path / "confiture.yaml").write_text(confiture_content)

        # Create sample entity
        sample_entity = f"""entity: Contact
schema: public
description: Sample contact entity for {name} project

fields:
  id:
    type: uuid
    primary_key: true
    default: gen_random_uuid()

  email:
    type: text
    unique: true
    description: Primary email address

  name:
    type: text
    description: Full display name

  created_at:
    type: timestamptz
    default: now()
    description: Record creation timestamp

actions:
  - name: create_contact
    description: Create a new contact
    steps:
      - insert: Contact

  - name: update_contact
    description: Update contact information
    steps:
      - update: Contact SET email = :email, name = :name WHERE id = :id
"""

        (project_path / "entities" / "contact.yaml").write_text(sample_entity)

        # Create README
        readme_content = f"""# {name}

A SpecQL project for business-focused database schema generation.

## Quick Start

1. Define your entities in the `entities/` directory
2. Generate SQL migrations:
   ```bash
   specql generate entities/*.yaml
   ```

3. Apply migrations to your database

## Project Structure

- `entities/` - SpecQL YAML entity definitions
- `migrations/` - Generated SQL migration files
- `docs/` - Project documentation
- `tests/` - Test files and fixtures
- `confiture.yaml` - Project configuration

## Development

- Edit entity definitions in `entities/`
- Run `specql generate` to update migrations
- Use `specql validate` to check entity definitions
- Apply patterns with `specql patterns detect` and `specql patterns apply`
"""

        (project_path / "README.md").write_text(readme_content)

        # Template-specific files
        if template == "full":
            # Create GitHub Actions workflow
            workflow_content = """name: SpecQL CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install SpecQL
      run: pip install specql
    - name: Validate entities
      run: specql validate entities/*.yaml
    - name: Generate migrations
      run: specql generate entities/*.yaml --dry-run
"""

            (project_path / ".github" / "workflows" / "ci.yml").write_text(workflow_content)

        output.success(f"✅ SpecQL project '{name}' created successfully!")
        output.info(f"📂 Project location: {project_path}")
        output.info("🚀 Next steps:")
        output.info("  1. cd " + str(project_path))
        output.info("  2. Edit entities/contact.yaml")
        output.info("  3. Run: specql generate entities/*.yaml")
