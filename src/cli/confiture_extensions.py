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


@click.group()
def specql():
    """SpecQL commands for Confiture"""
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
@click.option("--dev", is_flag=True, help="Development mode: flat format in db/schema/")
@click.option("--no-tv", is_flag=True, help="Skip table view (tv_*) generation")
def generate(
    entity_files,
    foundation_only,
    include_tv,
    env,
    output_format,
    output_dir,
    verbose,
    framework,
    dev,
    no_tv,
):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    # Get framework registry
    registry = get_framework_registry()

    # Resolve framework (explicit > auto-detect > default)
    resolved_framework = registry.resolve_framework(
        explicit_framework=framework,
        dev_mode=dev,
        auto_detect=True
    )

    # Get effective defaults for the resolved framework
    effective_defaults = registry.get_effective_defaults(
        framework=resolved_framework,
        dev_mode=dev,
        no_tv=no_tv,
        custom_output_dir=output_dir
    )

    # Apply framework-aware defaults (Phase 3: production-ready defaults)
    use_registry = effective_defaults.get("use_registry", True)  # CHANGED: Default to True
    output_format = effective_defaults.get("output_format", "hierarchical")  # CHANGED: Default to hierarchical
    include_tv = effective_defaults.get("include_tv", True) if not include_tv else include_tv  # CHANGED: Default to True for FraiseQL
    output_dir = effective_defaults.get("output_dir", "migrations")

    # Show framework selection if different from default
    if resolved_framework != "fraiseql" or framework != "fraiseql":
        click.echo(f"🎯 Using {resolved_framework} framework defaults")

    # Check for compatibility warnings
    warnings = registry.validate_framework_compatibility(resolved_framework, {
        "include_tv": include_tv,
        "dev_mode": dev,
        "no_tv": no_tv,
    })

    for warning_type, warning_msg in warnings.items():
        click.secho(f"⚠️  {warning_msg}", fg="yellow")

    # Deprecation warnings for old behavior
    if output_format == "confiture" and not dev and resolved_framework == "fraiseql":
        click.secho(
            "⚠️  Using 'confiture' format with FraiseQL framework. "
            "Consider using 'hierarchical' format for better organization, "
            "or use --dev for development mode.",
            fg="yellow"
        )

    if not use_registry and resolved_framework == "fraiseql" and not dev:
        click.secho(
            "⚠️  Registry disabled for FraiseQL framework. "
            "Table codes and hierarchical paths will not be generated. "
            "Use --dev for development mode or specify --framework explicitly.",
            fg="yellow"
        )

    # Create orchestrator with framework-aware settings
    orchestrator = CLIOrchestrator(
        use_registry=use_registry,
        output_format=output_format,
        verbose=verbose,
        framework=resolved_framework
    )

    # Generate schema
    try:
        result = orchestrator.generate_from_files(
            entity_files=list(entity_files),
            output_dir=output_dir,
            foundation_only=foundation_only,
            include_tv=include_tv,
        )
        print(f"DEBUG: result = {result}")
        print(f"DEBUG: result type = {type(result)}")
    except Exception as e:
        print(f"DEBUG: Exception in generate_from_files: {e}")
        import traceback
        traceback.print_exc()
        return 1

    if result and result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red")
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

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
        click.echo("  2. Apply manually or integrate with custom migration tool")
        if use_registry:
            click.echo("  3. Check registry: cat registry/domain_registry.yaml")

    return 0


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option("--verbose", "-v", is_flag=True)
def validate(entity_files, check_impacts, verbose):
    """Validate SpecQL entity files"""
    # Reuse existing validate.py logic by running it as a subprocess
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "src.cli.validate"] + list(entity_files)
    if check_impacts:
        cmd.append("--check-impacts")
    if verbose:
        cmd.append("--verbose")

    result = subprocess.run(cmd)
    return result.returncode


@specql.command("check-codes")
@click.argument("entity_files", nargs=-1, required=True)
@click.option(
    "--format", type=click.Choice(["text", "json", "csv"]), default="text", help="Output format"
)
@click.option("--export", type=click.Path(), help="Export results to file")
@click.pass_context
def check_codes(ctx, entity_files, format, export):
    """Check uniqueness of table codes across entity files.

    ENTITY_FILES can be file paths or glob patterns (e.g., entities/*.yaml, entities/**/*.yaml)

    Examples:
        specql check-codes entities/*.yaml
        specql check-codes entities/**/*.yaml --format json
        specql check-codes entities/ --export results.json
    """
    import csv
    import glob
    import json
    from pathlib import Path

    from src.cli.commands.check_codes import check_table_code_uniqueness

    # Expand glob patterns and convert to Path objects
    file_paths = []
    for pattern in entity_files:
        if "*" in pattern or "?" in pattern:
            # It's a glob pattern
            matches = glob.glob(pattern, recursive=True)
            file_paths.extend(Path(f) for f in matches if f.endswith(".yaml") or f.endswith(".yml"))
        else:
            # It's a direct path
            path = Path(pattern)
            if path.is_file() and (path.suffix in [".yaml", ".yml"]):
                file_paths.append(path)
            elif path.is_dir():
                # If it's a directory, find all YAML files in it
                file_paths.extend(path.glob("**/*.yaml"))
                file_paths.extend(path.glob("**/*.yml"))

    # Filter to only existing files
    file_paths = [f for f in file_paths if f.exists()]

    if not file_paths:
        click.secho("❌ No YAML files found", fg="red")
        ctx.exit(1)

    duplicates = check_table_code_uniqueness(file_paths)

    # Calculate total unique codes found
    all_codes = set()
    for entity_file in file_paths:
        try:
            from src.core.specql_parser import SpecQLParser

            parser = SpecQLParser()
            content = entity_file.read_text()
            entity_def = parser.parse(content)
            if entity_def.organization and entity_def.organization.table_code:
                all_codes.add(entity_def.organization.table_code)
        except Exception:
            pass  # Skip files that can't be parsed

    # Prepare results
    results = {
        "total_files": len(file_paths),
        "total_codes": len(all_codes),
        "duplicates": duplicates,
        "success": len(duplicates) == 0,
    }

    # Display results
    if format == "json":
        click.echo(json.dumps(results, indent=2))
    elif format == "csv":
        writer = csv.writer(click.get_text_stream("stdout"))
        writer.writerow(["code", "entity"])
        for code, entities in duplicates.items():
            for entity in entities:
                writer.writerow([code, entity])
    else:  # text format
        if duplicates:
            click.secho("❌ Table code uniqueness check FAILED", fg="red", bold=True)
            click.secho("\n🔴 Duplicate Codes:", fg="red", bold=True)

            for code, entities in duplicates.items():
                click.secho(f"\n  Code: {code}", fg="red")
                for entity in entities:
                    click.echo(f"    - {entity}")

            click.secho("\n❌ Fix duplicates before running 'specql generate'", fg="red")
            ctx.exit(1)
        else:
            click.secho("✅ Table code uniqueness check PASSED", fg="green", bold=True)
            click.secho("\n📊 Summary:", fg="blue")
            click.echo(f"   Total files scanned: {results['total_files']}")
            click.echo(f"   Unique codes found: {results['total_codes']}")
            click.echo(f"   Duplicate codes: {len(duplicates)}")
            click.secho("\nAll table codes are unique! 🎉", fg="green")
            ctx.exit(0)

    # Export if requested (only for non-text formats)
    if export:
        export_path = Path(export)
        if format == "json":
            with open(export_path, "w") as f:
                json.dump(results, f, indent=2)
        elif format == "csv":
            with open(export_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["code", "entity"])
                for code, entities in duplicates.items():
                    for entity in entities:
                        writer.writerow([code, entity])
        click.echo(f"📄 Results exported to: {export_path}")


@specql.command()
@click.argument("template_name", required=True)
@click.argument("entity_name", required=True)
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--custom-fields", type=click.Path(exists=True), help="YAML file with custom fields")
@click.option("--config", type=click.Path(exists=True), help="YAML file with configuration overrides")
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
            namespace = None
            template = template_name

        # Load custom fields if provided
        custom_fields_data = {}
        if custom_fields:
            with open(custom_fields, 'r') as f:
                custom_fields_data = yaml.safe_load(f) or {}

        # Load config overrides if provided
        custom_config = {}
        if config:
            with open(config, 'r') as f:
                custom_config = yaml.safe_load(f) or {}

        # Instantiate template
        result = library.instantiate_entity_template(
            template,
            entity_name,
            custom_fields=custom_fields_data,
            custom_config=custom_config
        )

        # Convert to YAML
        yaml_output = yaml.dump(result, default_flow_style=False, sort_keys=False)

        if output:
            # Write to file
            with open(output, 'w') as f:
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
            click.secho(f"⚠️  {existing_count} templates already exist. Use --force to reseed.", fg="yellow")
            return 0

        # Seed all templates
        click.echo("🌱 Seeding entity templates...")
        seed_all_templates(library)

        # Show summary
        total_count = len(library.get_all_entity_templates())
        click.secho(f"✅ Seeded {total_count} entity templates across 6 domains:", fg="green")

        # Show breakdown by domain
        domains = {}
        for template in library.get_all_entity_templates():
            domain = template["template_namespace"]
            domains[domain] = domains.get(domain, 0) + 1

        for domain, count in sorted(domains.items()):
            click.echo(f"  • {domain}: {count} templates")

        click.echo("\n📚 Available templates:")
        for template in library.get_all_entity_templates():
            click.echo(f"  • {template['template_namespace']}.{template['template_name']}: {template['description'][:60]}...")

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
from src.presentation.cli.domain import domain
specql.add_command(domain, name="domain")

# Add reverse engineering command
from src.cli.reverse import reverse
specql.add_command(reverse)

# Add Python reverse engineering command
from src.cli.reverse_python import reverse_python
specql.add_command(reverse_python, name="reverse-python")

# Add test reverse engineering command
from src.cli.reverse_tests import reverse_tests
specql.add_command(reverse_tests, name="reverse-tests")

# Add embeddings command
from src.cli.embeddings import embeddings_cli
specql.add_command(embeddings_cli)

# Add patterns command
from src.cli.patterns import patterns_cli
specql.add_command(patterns_cli)

# Add templates command
from src.cli.templates import templates
specql.add_command(templates)

# Interactive CLI
from src.cli.interactive import interactive
specql.add_command(interactive)

# Diagram generation
from src.cli.diagram import diagram
specql.add_command(diagram)


if __name__ == "__main__":
    specql()
