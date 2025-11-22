"""Seed data generation command"""

import json
from pathlib import Path

import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output as cli_output
from cli.utils.output import set_output_config


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option("--count", "-n", default=10, help="Number of records per entity")
@click.option("--scenario", "-s", default=0, help="Test scenario number (affects UUIDs)")
@click.option("--deterministic", is_flag=True, help="Use fixed seed for reproducible output")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["sql", "json", "csv"]),
    default="sql",
    help="Output format",
)
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.pass_context
def seed(
    ctx, files, output, verbose, quiet, count, scenario, deterministic, output_format, dry_run
):
    """Generate seed data SQL for testing.

    Creates realistic test data based on entity field types.
    Supports deterministic mode for reproducible test fixtures.

    Examples:

        # Generate 10 records per entity
        specql test seed entities/*.yaml -o seeds/

        # Generate 100 records with fixed seed
        specql test seed contact.yaml -n 100 --deterministic

        # JSON format for API testing
        specql test seed order.yaml --format json
    """
    with handle_cli_error():
        validate_common_options(verbose=verbose, quiet=quiet)
        set_output_config(verbose=verbose, quiet=quiet)

        from core.specql_parser import SpecQLParser
        from testing.seed.seed_generator import EntitySeedGenerator
        from testing.seed.sql_generator import SeedSQLGenerator

        parser = SpecQLParser()
        seed_value = 42 if deterministic else None

        # Parse all entities
        entities = []
        for file_path in files:
            with open(file_path) as f:
                yaml_content = f.read()
            entity = parser.parse(yaml_content)
            entities.append((entity, file_path))

        # Sort by dependency order (entities with FKs come after their targets)
        entities = _sort_by_dependencies(entities)

        output_dir = Path(output) if output else Path("seeds")

        for entity, file_path in entities:
            entity_config = _build_entity_config(entity)
            field_mappings = _build_field_mappings(entity)

            generator = EntitySeedGenerator(
                entity_config=entity_config, field_mappings=field_mappings, seed=seed_value
            )

            records = generator.generate_batch(count=count, scenario=scenario)

            if output_format == "sql":
                sql_gen = SeedSQLGenerator(entity_config)
                content = sql_gen.generate_file(
                    entities=records, scenario=scenario, description=f"Generated {count} records"
                )
                filename = f"seed_{entity.name.lower()}.sql"
            elif output_format == "json":
                content = json.dumps(records, indent=2, default=str)
                filename = f"seed_{entity.name.lower()}.json"
            else:  # csv
                content = _to_csv(records)
                filename = f"seed_{entity.name.lower()}.csv"

            if dry_run:
                cli_output.info(f"\n--- {filename} ---")
                cli_output.info(content[:2000])  # Preview first 2000 chars
            else:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / filename
                output_file.write_text(content)
                cli_output.success(f"Generated {filename} ({count} records)")

        if not dry_run:
            cli_output.success(f"\nSeed data written to {output_dir}/")


def _sort_by_dependencies(entities: list) -> list:
    """Sort entities so FK targets come before FK sources"""
    # Simple topological sort based on ref() fields
    entity_names = {e.name for e, _ in entities}
    deps = {}

    for entity, path in entities:
        entity_deps = set()
        for field in entity.fields.values():
            if field.type_name.startswith("ref("):
                target = field.type_name[4:-1]
                if target in entity_names:
                    entity_deps.add(target)
        deps[entity.name] = entity_deps

    # Kahn's algorithm
    result = []
    no_deps = [e for e, _ in entities if not deps[e.name]]
    remaining = {e.name: (e, p) for e, p in entities if deps[e.name]}

    while no_deps:
        entity = no_deps.pop(0)
        result.append((entity, next(p for e, p in entities if e.name == entity.name)))

        for name, (e, p) in list(remaining.items()):
            deps[name].discard(entity.name)
            if not deps[name]:
                no_deps.append(e)
                del remaining[name]

    # Add any remaining (circular deps)
    result.extend(remaining.values())
    return result


def _build_entity_config(entity) -> dict:
    """Build entity config dict for EntitySeedGenerator"""
    return {
        "entity_name": entity.name,
        "schema_name": entity.schema or "public",
        "table_name": f"tb_{entity.name.lower()}",
        "base_uuid_prefix": entity.name[:6].upper(),
        "is_tenant_scoped": False,  # TODO: determine from entity metadata
        "default_tenant_id": "01232122-0000-0000-2000-000000000001",
    }


def _build_field_mappings(entity) -> list:
    """Build field mappings list for EntitySeedGenerator"""
    mappings = []
    priority = 10

    for name, field in entity.fields.items():
        mapping = {
            "field_name": name,
            "field_type": field.type_name,
            "nullable": field.nullable,
            "priority_order": priority,
        }

        if field.type_name.startswith("ref("):
            mapping["generator_type"] = "fk_resolve"
            priority = max(priority, 20)  # FKs need higher priority
        elif field.type_name.startswith("enum("):
            mapping["generator_type"] = "random"
            enum_values = field.type_name[5:-1].split(",")
            mapping["enum_values"] = [v.strip() for v in enum_values]
        else:
            mapping["generator_type"] = "random"

        mappings.append(mapping)
        priority += 1

    return sorted(mappings, key=lambda x: x["priority_order"])


def _to_csv(records: list) -> str:
    """Convert records to CSV format"""
    if not records:
        return ""

    import csv
    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()
