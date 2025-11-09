#!/usr/bin/env python3
"""
SpecQL Generate CLI
Generate SQL migrations from SpecQL entity definitions
"""

import click
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.core.ast_models import Entity, Action, EntityDefinition


def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )  # TODO: Convert impact dict to ActionImpact
        actions.append(action)

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )

    return entity


@click.group()
def cli():
    """SpecQL Generator CLI"""
    pass


@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="migrations", help="Output directory for migrations")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation migration")
@click.option("--include-tv", is_flag=True, help="Generate tv_ table views after entities")
def entities(entity_files, output_dir, foundation_only, include_tv):
    """Generate SQL migrations from SpecQL entity files"""

    if foundation_only:
        # Generate only the app foundation
        orchestrator = SchemaOrchestrator()
        foundation_sql = orchestrator.generate_app_foundation_only()

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        foundation_file = output_path / "000_app_foundation.sql"
        foundation_file.write_text(foundation_sql)

        click.echo(f"✅ Generated app foundation: {foundation_file}")
        click.echo(f"   Size: {len(foundation_sql)} bytes")
        return

    if not entity_files:
        click.echo("❌ No entity files specified. Use --foundation-only or provide entity files.")
        return

    parser = SpecQLParser()
    orchestrator = SchemaOrchestrator()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate app foundation first (only once)
    foundation_sql = orchestrator.generate_app_foundation_only()
    if foundation_sql:
        foundation_file = output_path / "000_app_foundation.sql"
        foundation_file.write_text(foundation_sql)
        click.echo(f"✅ Generated app foundation: {foundation_file}")

    # Collect all entities for tv_ generation if needed
    all_entity_defs = []

    # Generate entity migrations
    for i, entity_file in enumerate(entity_files, start=100):
        entity_path = Path(entity_file)

        try:
            # Parse entity
            specql_content = entity_path.read_text()
            entity_def = parser.parse(specql_content)

            # Collect for tv_ generation
            all_entity_defs.append(entity_def)

            # Convert to Entity for orchestrator
            entity = convert_entity_definition_to_entity(entity_def)

            # Generate complete schema
            migration_sql = orchestrator.generate_complete_schema(entity)

            # Write migration file
            migration_file = output_path / f"{i:02d}_{entity.name.lower()}.sql"
            migration_file.write_text(migration_sql)

            click.echo(f"✅ Generated migration: {migration_file}")
            click.echo(f"   Entity: {entity.schema}.{entity.name}")
            click.echo(f"   Size: {len(migration_sql)} bytes")

        except Exception as e:
            click.echo(f"❌ Error processing {entity_file}: {e}", err=True)
            continue

    # Generate tv_ tables if requested
    if include_tv and all_entity_defs:
        try:
            tv_sql = orchestrator.generate_table_views(all_entity_defs)
            if tv_sql:
                tv_file = output_path / "200_table_views.sql"
                tv_file.write_text(tv_sql)
                click.echo(f"✅ Generated tv_ tables: {tv_file}")
                click.echo(f"   Size: {len(tv_sql)} bytes")
        except Exception as e:
            click.echo(f"❌ Error generating tv_ tables: {e}", err=True)

    click.echo(f"\n🎉 Generation complete! Migrations in {output_dir}/")


def main():
    """Entry point for specql generate command"""
    cli()


if __name__ == "__main__":
    main()
