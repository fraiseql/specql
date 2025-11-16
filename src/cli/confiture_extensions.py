#!/usr/bin/env python3
"""
SpecQL Confiture Extensions
Extend Confiture CLI with SpecQL-specific commands
"""

from pathlib import Path

import click

from src.cli.orchestrator import CLIOrchestrator
from src.cli.help_text import get_generate_help_text
from src.cli.framework_registry import get_framework_registry
from src.cli.registry import registry
from src.core.specql_parser import SpecQLParser


@click.group()
def specql():
    """
    SpecQL - Multi-Language Backend Code Generator

    Generate PostgreSQL, Java, Rust, and TypeScript from YAML specifications.

    Code Generation:
      generate       - Generate code from entities
      generate-java  - Generate Spring Boot Java code

    Testing:
      generate-tests - Generate pgTAP and pytest tests
      reverse-tests  - Import existing tests to TestSpec

    Reverse Engineering:
      reverse        - Reverse engineer PostgreSQL to entities
      reverse-python - Reverse engineer Python to entities
      parse-plpgsql  - Parse PostgreSQL DDL to entities

    Utilities:
      validate       - Validate entity definitions
      examples       - Show example entity definitions
      diagram        - Generate entity relationship diagrams
      interactive    - Interactive CLI mode

    Get help on any command:
      specql <command> --help

    Documentation:
      https://github.com/fraiseql/specql/blob/main/docs/
    """
    pass


@specql.command(help=get_generate_help_text())
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
@click.option("--verbose", "-v", is_flag=True, help="Show detailed generation progress")
@click.option(
    "--framework",
    type=click.Choice(["fraiseql", "django", "rails", "prisma"]),
    default="fraiseql",
    help="Target framework (default: fraiseql)",
)
@click.option(
    "--target",
    type=click.Choice(["postgresql", "python_django", "python_sqlalchemy", "rust"]),
    help="Target language for pattern-based code generation",
)
@click.option(
    "--with-handlers", is_flag=True, help="Generate HTTP handlers (Rust only)"
)
@click.option(
    "--with-routes", is_flag=True, help="Generate route configuration (Rust only)"
)
@click.option("--dev", is_flag=True, help="Development mode: flat format in db/schema/")
@click.option("--no-tv", is_flag=True, help="Skip table view (tv_*) generation")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be generated without writing files"
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Interactive mode with previews and confirmations",
)
def generate(
    entity_files,
    foundation_only,
    include_tv,
    env,
    output_format,
    output_dir,
    verbose,
    framework,
    target,
    with_handlers,
    with_routes,
    dev,
    no_tv,
    dry_run,
    interactive,
):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    # Handle pattern-based multi-language generation
    if target:
        from tests.integration.test_pattern_library_multilang import (
            MultiLanguageGenerator,
        )

        click.secho(
            f"🔧 Generating {target} code using pattern library...",
            fg="blue",
            bold=True,
        )

        parser = SpecQLParser()
        generator = MultiLanguageGenerator()

        for entity_file in entity_files:
            with open(entity_file) as f:
                yaml_content = f.read()
            entity_def = parser.parse(yaml_content)

            if target == "postgresql":
                code = generator.generate_postgresql(entity_def)
            elif target == "python_django":
                code = generator.generate_django(entity_def)
            elif target == "python_sqlalchemy":
                code = generator.generate_sqlalchemy(entity_def)
            elif target == "rust":
                from src.generators.rust.rust_generator_orchestrator import (
                    RustGeneratorOrchestrator,
                )

                orchestrator = RustGeneratorOrchestrator()
                orchestrator.generate(
                    entity_files=[Path(entity_file)],
                    output_dir=Path(output_dir or "generated"),
                    with_handlers=with_handlers,
                    with_routes=with_routes,
                )
                click.secho(
                    f"✅ Rust backend generated in {output_dir or 'generated'}",
                    fg="green",
                )
                return
            else:
                raise click.ClickException(f"Unsupported target: {target}")

            # Write to output file
            output_path = Path(output_dir or "generated")
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = (
                output_path / f"{entity_def.name.lower()}_{target}.sql"
                if target == "postgresql"
                else f"{entity_def.name.lower()}_{target}.py"
            )

            with open(output_file, "w") as f:
                f.write(code)
            click.secho(f"✅ Generated {output_file}", fg="green")

        return

    # Get framework registry
    registry = get_framework_registry()

    # Resolve framework (explicit > auto-detect > default)
    resolved_framework = registry.resolve_framework(
        explicit_framework=framework, dev_mode=dev, auto_detect=True
    )

    # Get effective defaults for the resolved framework
    effective_defaults = registry.get_effective_defaults(
        framework=resolved_framework,
        dev_mode=dev,
        no_tv=no_tv,
        custom_output_dir=output_dir,
    )

    # Apply framework-aware defaults (Phase 3: production-ready defaults)
    use_registry = effective_defaults.get(
        "use_registry", True
    )  # CHANGED: Default to True
    output_format = effective_defaults.get(
        "output_format", "hierarchical"
    )  # CHANGED: Default to hierarchical
    include_tv = (
        effective_defaults.get("include_tv", True) if not include_tv else include_tv
    )  # CHANGED: Default to True for FraiseQL
    output_dir = effective_defaults.get("output_dir", "migrations")

    # Show framework selection if different from default
    if resolved_framework != "fraiseql" or framework != "fraiseql":
        click.echo(f"🎯 Using {resolved_framework} framework defaults")

    # Check for compatibility warnings
    warnings = registry.validate_framework_compatibility(
        resolved_framework,
        {
            "include_tv": include_tv,
            "dev_mode": dev,
            "no_tv": no_tv,
        },
    )

    for warning_type, warning_msg in warnings.items():
        click.secho(f"⚠️  {warning_msg}", fg="yellow")

    # Deprecation warnings for old behavior
    if output_format == "confiture" and not dev and resolved_framework == "fraiseql":
        click.secho(
            "⚠️  Using 'confiture' format with FraiseQL framework. "
            "Consider using 'hierarchical' format for better organization, "
            "or use --dev for development mode.",
            fg="yellow",
        )

    if not use_registry and resolved_framework == "fraiseql" and not dev:
        click.secho(
            "⚠️  Registry disabled for FraiseQL framework. "
            "Table codes and hierarchical paths will not be generated. "
            "Use --dev for development mode or specify --framework explicitly.",
            fg="yellow",
        )

    # Create orchestrator with framework-aware settings
    orchestrator = CLIOrchestrator(
        use_registry=use_registry,
        output_format=output_format,
        verbose=verbose,
        framework=resolved_framework,
    )

    # Interactive mode
    if interactive:
        click.echo("🔍 Interactive mode: Analyzing entities...")
        # Parse entities for preview
        parser = SpecQLParser()
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                click.secho(f"❌ Failed to parse {entity_file}: {e}", fg="red")
                return 1

        # Show entity preview
        click.echo(f"\n📋 Found {len(entity_defs)} entities:")
        for entity_def in entity_defs[:5]:  # Show first 5
            click.echo(f"  • {entity_def.name}")
        if len(entity_defs) > 5:
            click.echo(f"  ... and {len(entity_defs) - 5} more")

        # Estimate output
        estimated_files = (
            len(entity_defs) * 3
        )  # Rough estimate: table + helpers + mutations
        estimated_size = estimated_files * 2048  # Rough estimate: 2KB per file
        click.echo(
            f"\n📊 Estimated output: ~{estimated_files} files, ~{estimated_size // 1024}KB"
        )

        # Show output directory
        click.echo(f"📁 Output directory: {output_dir}")

        # Confirm generation
        if not click.confirm("\n🚀 Proceed with generation?", default=True):
            click.echo("❌ Generation cancelled")
            return 0

    # Dry run notification
    if dry_run:
        click.secho(
            "🔍 DRY RUN MODE - No files will be written", fg="yellow", bold=True
        )
        click.echo()

    # Generate schema
    try:
        result = orchestrator.generate_from_files(
            entity_files=list(entity_files),
            output_dir=output_dir,
            foundation_only=foundation_only,
            include_tv=include_tv,
            dry_run=dry_run,
        )
    except Exception:
        import traceback

        traceback.print_exc()
        return 1

    if result and result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red")
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    # Success messaging
    if dry_run:
        click.secho(
            f"🔍 Would generate {len(result.migrations)} schema file(s)", fg="cyan"
        )
        click.echo()
        click.echo("💡 Run without --dry-run to actually generate files:")
        click.secho(f"  specql generate {' '.join(entity_files)}", fg="green")
    else:
        click.secho(f"✅ Generated {len(result.migrations)} schema file(s)", fg="green")

    # Confiture build (only for confiture format)
    if output_format == "confiture" and not foundation_only:
        click.echo("\nBuilding final migration with Confiture...")
        try:
            from confiture.core.builder import SchemaBuilder

            builder = SchemaBuilder(env=env)
            builder.build()

            output_path = Path(f"db/generated/schema_{env}.sql")
            click.secho(
                f"✅ Complete! Migration written to: {output_path}",
                fg="green",
                bold=True,
            )
            click.echo("\nNext steps:")
            click.echo(f"  1. Review: cat {output_path}")
            click.echo(f"  2. Apply: confiture migrate up --env {env}")
            click.echo("  3. Status: confiture migrate status")
        except ImportError:
            click.secho(
                "⚠️  Confiture not available, generated schema files only", fg="yellow"
            )
        except Exception as e:
            click.secho(f"❌ Confiture build failed: {e}", fg="red")
            return 1

    elif output_format == "hierarchical":
        click.secho(
            f"\n📁 Hierarchical output written to: {output_dir}/", fg="blue", bold=True
        )
        click.echo("\nStructure:")
        click.echo("  migrations/")
        click.echo("    └── 01_write_side/")
        click.echo("        └── [domain]/")
        click.echo("            └── [subdomain]/")
        click.echo("                └── [entity]/")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review structure: tree {output_dir}/")
        click.echo("  2. Apply manually or integrate with custom migration tool")
        if use_registry:
            click.echo("  3. Check registry: cat registry/domain_registry.yaml")

    return 0


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option(
    "--check-references", is_flag=True, help="Validate cross-entity references"
)
@click.option("--check-naming", is_flag=True, help="Validate naming conventions")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "junit"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation")
def validate(
    entity_files,
    check_impacts,
    check_references,
    check_naming,
    strict,
    output_format,
    output,
    verbose,
):
    """Validate SpecQL entity files with comprehensive checks

    Performs thorough validation including:
    - YAML syntax and structure
    - Entity and field definitions
    - Type validation and constraints
    - Cross-entity references
    - Naming conventions
    - Action and impact validation

    Examples:
        specql validate entities/*.yaml
        specql validate entities/ --check-references --format json
        specql validate entities/ --strict --output validation.json
    """


@specql.command()
@click.argument(
    "template",
    type=click.Choice(["minimal", "blog", "crm", "ecommerce", "saas", "production"]),
)
@click.argument("project_name", required=True)
@click.option(
    "--output-dir",
    default=".",
    help="Parent directory for the new project (default: current directory)",
)
@click.option("--force", is_flag=True, help="Overwrite existing directory")
def init(template, project_name, output_dir, force):
    """Create a new SpecQL project from a template.

    TEMPLATE: Project template to use
    PROJECT_NAME: Name of the project directory to create

    Templates:
      minimal    - Single entity example
      blog       - Blog system (Post, Author, Comment)
      crm        - CRM system (Contact, Company, Deal)
      ecommerce  - E-commerce platform
      saas       - Multi-tenant SaaS application
      production - Production-ready template

    Examples:
        specql init blog myblog
        specql init minimal myproject --output-dir ~/projects
        specql init crm mycrm --force
    """
    import shutil
    from pathlib import Path

    # Template mappings
    template_dirs = {
        "minimal": "simple-blog",  # Use simple-blog as minimal for now
        "blog": "simple-blog",
        "crm": "crm",
        "ecommerce": "ecommerce",
        "saas": "saas-multi-tenant",
        "production": "production-ready",
    }

    template_dir = template_dirs[template]
    # Get the specql root directory (where this file is located)
    specql_root = Path(__file__).parent.parent.parent
    source_dir = specql_root / "examples" / template_dir

    if not source_dir.exists():
        click.secho(f"❌ Template '{template}' not found", fg="red")
        return 1

    # Create output directory
    output_path = Path(output_dir) / project_name

    # Check if directory exists and is not empty
    if output_path.exists() and not force:
        if list(output_path.iterdir()):
            click.secho(
                f"❌ Directory {output_path} already exists and is not empty. Use --force to overwrite.",
                fg="red",
            )
            return 1
    else:
        # Create the directory
        output_path.mkdir(parents=True, exist_ok=True)

    click.secho(
        f"🚀 Initializing {template} project: {project_name}", fg="blue", bold=True
    )

    # Copy template files
    entities_dir = output_path / "entities"
    entities_dir.mkdir(exist_ok=True)

    copied_files = 0
    source_entities = source_dir / "entities"

    if source_entities.exists():
        for yaml_file in source_entities.glob("*.yaml"):
            dest_file = entities_dir / yaml_file.name
            shutil.copy2(yaml_file, dest_file)
            copied_files += 1
            click.echo(f"  📄 {dest_file.relative_to(output_path)}")

    # Create additional project files
    project_files = {
        "README.md": f"""# {project_name}

A SpecQL {template} project.

## Getting Started

1. Review the entities in the `entities/` directory
2. Generate database schema:
   ```bash
   specql generate entities/*.yaml
   ```

3. Customize entities as needed
4. Regenerate and apply migrations

## Project Structure

- `entities/` - SpecQL entity definitions
- `migrations/` - Generated database migrations (after running specql generate)

## Commands

- Generate schema: `specql generate entities/*.yaml`
- Validate entities: `specql validate entities/*.yaml`
- Check table codes: `specql check-codes entities/`
""",
        ".gitignore": """# SpecQL generated files
migrations/
db/generated/
*.sql

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
        "specql.yaml": f"""# SpecQL Project Configuration
project:
  name: {project_name}
  template: {template}
  version: "1.0.0"

# Framework configuration (uncomment and modify as needed)
# framework: fraiseql
# database: postgresql

# Custom settings
# settings:
#   table_prefix: "app_"
#   schema: "public"
""",
    }

    for filename, content in project_files.items():
        file_path = output_path / filename
        if not file_path.exists() or force:
            with open(file_path, "w") as f:
                f.write(content)
            click.echo(f"  📄 {filename}")

    click.secho("\n✅ Project initialized successfully!", fg="green", bold=True)
    click.echo(f"📁 Created in: {output_path.absolute()}")
    click.echo(f"📊 {copied_files} entity files copied")

    click.echo("\n🚀 Next steps:")
    click.echo(f"  cd {output_path.name}")
    click.echo("  specql validate entities/*.yaml")
    click.echo("  specql generate entities/*.yaml")

    return 0

    click.secho(
        f"🚀 Initializing {template} project: {project_name}", fg="blue", bold=True
    )

    # Copy template files
    entities_dir = output_path / "entities"
    entities_dir.mkdir(exist_ok=True)

    copied_files = 0
    source_entities = source_dir / "entities"

    if source_entities.exists():
        for yaml_file in source_entities.glob("*.yaml"):
            dest_file = entities_dir / yaml_file.name
            shutil.copy2(yaml_file, dest_file)
            copied_files += 1
            click.echo(f"  📄 {dest_file.relative_to(output_path)}")

    # Create additional project files
    project_files = {
        "README.md": f"""# {project_name}

A SpecQL {template} project.

## Getting Started

1. Review the entities in the `entities/` directory
2. Generate database schema:
   ```bash
   specql generate entities/*.yaml
   ```

3. Customize entities as needed
4. Regenerate and apply migrations

## Project Structure

- `entities/` - SpecQL entity definitions
- `migrations/` - Generated database migrations (after running specql generate)

## Commands

- Generate schema: `specql generate entities/*.yaml`
- Validate entities: `specql validate entities/*.yaml`
- Check table codes: `specql check-codes entities/`
""",
        ".gitignore": """# SpecQL generated files
migrations/
db/generated/
*.sql

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
        "specql.yaml": f"""# SpecQL Project Configuration
project:
  name: {project_name}
  template: {template}
  version: "1.0.0"

# Framework configuration (uncomment and modify as needed)
# framework: fraiseql
# database: postgresql

# Custom settings
# settings:
#   table_prefix: "app_"
#   schema: "public"
""",
    }

    for filename, content in project_files.items():
        file_path = output_path / filename
        if not file_path.exists() or force:
            with open(file_path, "w") as f:
                f.write(content)
            click.echo(f"  📄 {filename}")

    click.secho("\n✅ Project initialized successfully!", fg="green", bold=True)
    click.echo(f"📁 Created in: {output_path.absolute()}")
    click.echo(f"📊 {copied_files} entity files copied")

    click.echo("\n🚀 Next steps:")
    click.echo(f"  cd {output_path.name}")
    click.echo("  specql validate entities/*.yaml")
    click.echo("  specql generate entities/*.yaml")

    return 0


@specql.command()
@click.argument("template_name", required=True)
@click.argument("entity_name", required=True)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (default: stdout)"
)
@click.option(
    "--custom-fields", type=click.Path(exists=True), help="YAML file with custom fields"
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="YAML file with configuration overrides",
)
def instantiate(template_name, entity_name, output, custom_fields, config):
    """Instantiate an entity template

    TEMPLATE_NAME: Name of the template to instantiate (e.g., crm.contact)
    ENTITY_NAME: Name for the new entity

    Examples:
        specql instantiate crm.contact MyContact
        specql instantiate crm.contact MyContact --output entities/my_contact.yaml
        specql instantiate crm.contact MyContact --custom-fields custom.yaml
    """
    import yaml
    from src.pattern_library.api import PatternLibrary

    try:
        # Initialize pattern library with persistent database
        import os

        db_path = os.path.expanduser("~/.specql/pattern_library.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        library = PatternLibrary(db_path)

        # Parse namespace.template format
        if "." in template_name:
            namespace, template = template_name.split(".", 1)
        else:
            template = template_name

        # Load custom fields if provided
        custom_fields_data = {}
        if custom_fields:
            with open(custom_fields, "r") as f:
                custom_fields_data = yaml.safe_load(f) or {}

        # Load config overrides if provided
        custom_config = {}
        if config:
            with open(config, "r") as f:
                custom_config = yaml.safe_load(f) or {}

        # Instantiate template
        result = library.instantiate_entity_template(
            template,
            entity_name,
            custom_fields=custom_fields_data,
            custom_config=custom_config,
        )

        # Convert to YAML
        yaml_output = yaml.dump(result, default_flow_style=False, sort_keys=False)

        if output:
            # Write to file
            with open(output, "w") as f:
                f.write(yaml_output)
            click.secho(f"✅ Entity instantiated: {output}", fg="green")
        else:
            # Output to stdout
            click.echo(yaml_output)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        return 1

    return 0


@specql.command()
@click.option("--force", is_flag=True, help="Force reseed even if templates exist")
def seed_templates(force):
    """Seed entity templates into the pattern library

    This command populates the pattern library with pre-built entity templates
    for CRM, E-commerce, Healthcare, Project Management, HR, and Finance domains.

    Examples:
        specql seed-templates
        specql seed-templates --force  # Reseed even if templates exist
    """
    import os
    from src.pattern_library.api import PatternLibrary
    from src.pattern_library.seed_entity_templates import seed_all_templates

    try:
        # Initialize pattern library with persistent database
        db_path = os.path.expanduser("~/.specql/pattern_library.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        library = PatternLibrary(db_path)

        # Check if templates already exist
        existing_count = len(library.get_all_entity_templates())
        if existing_count > 0 and not force:
            click.secho(
                f"⚠️  {existing_count} templates already exist. Use --force to reseed.",
                fg="yellow",
            )
            return 0

        # Seed all templates
        click.echo("🌱 Seeding entity templates...")
        seed_all_templates(library)

        # Show summary
        total_count = len(library.get_all_entity_templates())
        click.secho(
            f"✅ Seeded {total_count} entity templates across 6 domains:", fg="green"
        )

        # Show breakdown by domain
        domains = {}
        for template in library.get_all_entity_templates():
            domain = template["template_namespace"]
            domains[domain] = domains.get(domain, 0) + 1

        for domain, count in sorted(domains.items()):
            click.echo(f"  • {domain}: {count} templates")

        click.echo("\n📚 Available templates:")
        for template in library.get_all_entity_templates():
            click.echo(
                f"  • {template['template_namespace']}.{template['template_name']}: {template['description'][:60]}..."
            )

    except Exception as e:
        click.secho(f"❌ Error seeding templates: {e}", fg="red")
        return 1

    return 0


@specql.command()
def list_frameworks():
    """List all available target frameworks"""
    registry = get_framework_registry()
    frameworks = registry.list_frameworks()

    click.secho("Available frameworks:", fg="blue", bold=True)
    for name, description in sorted(frameworks.items()):
        click.echo(f"  • {name}: {description}")

    click.echo("\nUse: specql generate --framework <name> entities/**/*.yaml")
    return 0


# Add registry management commands
specql.add_command(registry, name="registry")

# Add domain management commands (PostgreSQL primary)
from src.presentation.cli.domain import domain  # noqa: E402

specql.add_command(domain, name="domain")

# Add reverse engineering command
from src.cli.reverse import reverse  # noqa: E402

specql.add_command(reverse)

# Add Python reverse engineering command
from src.cli.reverse_python import reverse_python

specql.add_command(reverse_python, name="reverse-python")

# Add test generation command
from src.cli.generate_tests import generate_tests

specql.add_command(generate_tests, name="generate-tests")

# Add test reverse engineering command
# from src.cli.reverse_tests import reverse_tests
#
# specql.add_command(reverse_tests, name="reverse-tests")

# Add embeddings command
# from src.cli.embeddings import embeddings_cli
# specql.add_command(embeddings_cli)

# Add patterns command
from src.cli.patterns import patterns_cli

specql.add_command(patterns_cli)

# Add templates command
from src.cli.templates import templates

specql.add_command(templates)

# Interactive CLI
from src.cli.interactive import interactive
from src.cli.commands.examples import examples

specql.add_command(interactive)
specql.add_command(examples)

# Diagram generation
from src.cli.diagram import diagram

specql.add_command(diagram)

# CI/CD pipeline management
from src.cli.cicd import cicd

specql.add_command(cicd, name="cicd")

# Infrastructure operations
from src.cli.infrastructure import infrastructure

specql.add_command(infrastructure, name="infrastructure")


@specql.command()
@click.argument("entity_file", type=click.Path(exists=True))
@click.option("--output-dir", default="generated/java", help="Output directory")
def generate_java(entity_file: str, output_dir: str):
    """Generate Spring Boot Java code from SpecQL entity"""
    from src.core.specql_parser import SpecQLParser
    from src.generators.java.java_generator_orchestrator import (
        JavaGeneratorOrchestrator,
    )

    click.secho("☕ Generating Spring Boot Java code...", fg="blue", bold=True)

    # Parse SpecQL
    parser = SpecQLParser()
    with open(entity_file) as f:
        entity = parser.parse_universal(f.read())

    # Generate Java code
    orchestrator = JavaGeneratorOrchestrator(output_dir)
    files = orchestrator.generate_all(entity)
    orchestrator.write_files(files)

    click.echo(f"✅ Generated {len(files)} Java files in {output_dir}")
    for file in files:
        click.echo(f"  - {file.path}")

    return 0


@specql.command()
@click.argument("input", nargs=-1)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    help="Output directory (default: current directory)",
)
@click.option(
    "--connection-string",
    "-c",
    help="PostgreSQL connection string for database parsing",
)
@click.option(
    "--schemas",
    "-s",
    multiple=True,
    help="Database schemas to parse (default: all user schemas)",
)
@click.option(
    "--include-functions/--no-functions",
    default=True,
    help="Include PL/pgSQL functions as actions",
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.70,
    help="Minimum confidence threshold (0.0-1.0)",
)
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed parsing progress")
def parse_plpgsql(
    input,
    output_dir,
    connection_string,
    schemas,
    include_functions,
    confidence_threshold,
    preview,
    verbose,
):
    """
    Parse PostgreSQL DDL or live database to SpecQL entities

    Examples:
        # Parse DDL file
        specql parse-plpgsql schema.sql -o entities/

        # Parse live database
        specql parse-plpgsql --connection-string "postgresql://user:pass@host/db" --schemas public crm

        # Parse with custom confidence threshold
        specql parse-plpgsql schema.sql --confidence-threshold 0.8

        # Preview parsing without writing files
        specql parse-plpgsql schema.sql --preview --verbose
    """
    from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser

    if not input and not connection_string:
        click.secho(
            "❌ Must specify either input files or --connection-string", fg="red"
        )
        return 1

    if input and connection_string:
        click.secho(
            "❌ Cannot specify both input files and --connection-string", fg="red"
        )
        return 1

    # Initialize parser
    parser = PLpgSQLParser(confidence_threshold=confidence_threshold)

    entities = []
    total_files = 0
    total_entities = 0

    try:
        if connection_string:
            # Parse live database
            if verbose:
                click.echo("🔌 Connecting to database...")

            parsed_entities = parser.parse_database(
                connection_string,
                schemas=list(schemas) if schemas else None,
                include_functions=include_functions,
            )

            entities.extend(parsed_entities)
            total_entities = len(parsed_entities)

            if verbose:
                click.echo(f"📋 Found {len(parsed_entities)} entities")
                for entity in parsed_entities:
                    click.echo(f"  • {entity.name} ({entity.schema})")

        else:
            # Parse DDL files
            for input_file in input:
                if verbose:
                    click.echo(f"📄 Processing {input_file}...")

                try:
                    parsed_entities = parser.parse_ddl_file(input_file)
                    entities.extend(parsed_entities)
                    total_files += 1

                    if verbose:
                        click.echo(f"  📋 Found {len(parsed_entities)} entities")
                        for entity in parsed_entities:
                            click.echo(f"    • {entity.name}")

                except Exception as e:
                    click.secho(f"❌ Failed to parse {input_file}: {e}", fg="red")
                    continue

            total_entities = len(entities)

        # Filter by confidence
        high_confidence_entities = [
            e
            for e in entities
            if not hasattr(e, "confidence") or e.confidence >= confidence_threshold
        ]

        # Summary
        click.echo("\n📊 Parsing Summary:")
        click.echo(f"  Files processed: {total_files}")
        click.echo(f"  Total entities: {total_entities}")
        click.echo(f"  High confidence: {len(high_confidence_entities)}")
        click.echo(f"  Filtered out: {total_entities - len(high_confidence_entities)}")

        if high_confidence_entities and output_dir and not preview:
            # Write YAML files
            from pathlib import Path

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for entity in high_confidence_entities:
                # Convert entity to YAML
                yaml_content = _entity_to_yaml(entity)

                # Write to file
                filename = f"{entity.name}.yaml"
                file_path = output_path / filename
                with open(file_path, "w") as f:
                    f.write(yaml_content)

                click.echo(f"💾 Written {entity.name} to {file_path}")

        elif preview:
            # Show preview
            click.echo("\n👀 Preview:")
            for entity in high_confidence_entities[:5]:  # Show first 5
                click.echo(f"  • {entity.name} ({entity.schema})")
                click.echo(f"    Fields: {len(entity.fields)}")
                if entity.actions:
                    click.echo(f"    Actions: {len(entity.actions)}")
            if len(high_confidence_entities) > 5:
                click.echo(f"  ... and {len(high_confidence_entities) - 5} more")

        return 0

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        return 1


def _entity_to_yaml(entity) -> str:
    """Convert UniversalEntity to YAML string"""
    import yaml

    entity_dict = {
        "entity": entity.name,
        "schema": entity.schema,
        "description": getattr(entity, "description", None),
    }

    # Add fields
    if entity.fields:
        entity_dict["fields"] = {}
        for field in entity.fields:
            field_dict = {"type": field.type.value}
            if not field.required:
                field_dict["nullable"] = True
            if field.unique:
                field_dict["unique"] = True
            if field.default is not None:
                field_dict["default"] = str(field.default)

            entity_dict["fields"][field.name] = field_dict

    # Add actions
    if entity.actions:
        entity_dict["actions"] = []
        for action in entity.actions:
            action_dict = {"name": action.name, "steps": []}

            for step in action.steps:
                step_dict = {
                    "type": step.type.value,
                }
                if hasattr(step, "entity") and step.entity:
                    step_dict["entity"] = step.entity
                if hasattr(step, "expression") and step.expression:
                    step_dict["expression"] = step.expression
                if hasattr(step, "fields") and step.fields:
                    step_dict["fields"] = step.fields

                action_dict["steps"].append(step_dict)

            entity_dict["actions"].append(action_dict)

    return yaml.dump(entity_dict, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    specql()
# ruff: noqa: E402
