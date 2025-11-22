"""
Reverse TypeScript subcommand - Convert Prisma/TypeORM schemas to SpecQL YAML.

Integrates with:
- PrismaSchemaParser: Parses .prisma schema files using tree-sitter
- TypeScriptParser: Extracts Express/Fastify/Next.js routes
"""

from pathlib import Path

import click
import yaml

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _is_prisma_file(file_path: Path) -> bool:
    """Check if file is a Prisma schema."""
    return file_path.suffix == ".prisma"


def _detect_typescript_framework(source_code: str, file_path: str) -> str:
    """Auto-detect TypeScript framework from imports and patterns."""
    if "express" in source_code.lower():
        return "express"
    if "fastify" in source_code.lower():
        return "fastify"
    if "/pages/api/" in file_path or "pages/api" in file_path:
        return "nextjs-pages"
    if "route.ts" in file_path or "route.js" in file_path:
        return "nextjs-app"
    if "'use server'" in source_code or '"use server"' in source_code:
        return "nextjs-server-actions"
    return "unknown"


def _map_prisma_type_to_specql(prisma_type: str) -> str:
    """Map Prisma types to SpecQL types.

    Note: PrismaSchemaParser already maps types in its _convert_field_to_legacy method.
    This function handles both raw Prisma types and already-mapped types.
    """
    # Strip array notation for mapping
    base_type = prisma_type.replace("[]", "")

    # Prisma -> SpecQL type mapping
    type_map = {
        "String": "text",
        "Int": "integer",
        "BigInt": "bigint",
        "Float": "decimal",
        "Decimal": "decimal",
        "Boolean": "boolean",
        "DateTime": "timestamp",
        "Json": "jsonb",
        "Bytes": "bytea",
    }

    # Already-mapped SpecQL types (pass through)
    specql_types = {
        "text",
        "integer",
        "bigint",
        "decimal",
        "boolean",
        "timestamp",
        "jsonb",
        "bytea",
        "enum",
    }

    if base_type in specql_types:
        return base_type

    return type_map.get(base_type, "text")


def _generate_yaml_from_prisma_entity(entity, enums: dict) -> str:
    """Generate SpecQL YAML from PrismaEntity."""
    yaml_dict = {
        "entity": entity.name,
        "schema": "public",
        "description": f"Auto-generated from Prisma model {entity.name}",
        "fields": {},
        "_metadata": {
            "source_language": "prisma",
            "source_table": entity.table_name,
            "generated_by": "specql-reverse-typescript",
        },
    }

    # Convert fields
    for field in entity.fields:
        # Skip relation fields that are just arrays (handled via FK)
        if field.is_list and field.is_relation:
            continue

        # Determine field type - priority: enum > relation > primitive
        if field.enum_values:
            # Field has inline enum values (from parser)
            enum_str = ", ".join(field.enum_values)
            field_type = f"enum({enum_str})"
        elif field.type == "enum" and field.related_entity and field.related_entity in enums:
            # Enum type reference
            enum_str = ", ".join(enums[field.related_entity])
            field_type = f"enum({enum_str})"
        elif field.type in enums:
            # Field type is an enum name
            enum_str = ", ".join(enums[field.type])
            field_type = f"enum({enum_str})"
        elif field.is_relation and field.related_entity and field.related_entity not in enums:
            # True relation (not enum)
            field_type = f"ref({field.related_entity})"
        else:
            field_type = _map_prisma_type_to_specql(field.type)

        # Add optional marker
        if field.is_optional:
            field_type = f"{field_type}?"

        yaml_dict["fields"][field.name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


def _generate_yaml_from_routes(routes: list, source_file: str) -> str | None:
    """Generate SpecQL YAML from extracted routes (as actions)."""
    if not routes:
        return None

    # Group routes by resource (extract from path)
    resources = {}
    for route in routes:
        # Extract resource name from path (e.g., /contacts -> contacts)
        path_parts = route.path.strip("/").split("/")
        if path_parts:
            resource = path_parts[0]
            if resource not in resources:
                resources[resource] = []
            resources[resource].append(route)

    if not resources:
        return None

    # For now, just document the routes as metadata
    # Future: convert to SpecQL actions
    yaml_dict = {
        "_routes": {
            "source_file": source_file,
            "endpoints": [
                {"method": r.method, "path": r.path, "framework": r.framework} for r in routes
            ],
        },
        "_metadata": {
            "source_language": "typescript",
            "generated_by": "specql-reverse-typescript",
            "note": "Routes extracted - manual action definition required",
        },
    }

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework",
    type=click.Choice(["prisma", "typeorm", "sequelize", "express", "fastify", "nextjs"]),
    help="Framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def typescript(files, output_dir, framework, preview, verbose, quiet, **kwargs):
    """Reverse engineer TypeScript/Prisma to SpecQL YAML.

    Supports Prisma schemas, Express routes, Fastify routes, and Next.js.

    Examples:

        specql reverse typescript prisma/schema.prisma -o entities/

        specql reverse typescript src/routes/*.ts -o entities/

        specql reverse typescript app/api/**/route.ts -o entities/ --preview
    """
    with handle_cli_error():
        # Configure output settings
        from cli.utils.output import set_output_config

        set_output_config(verbose=verbose, quiet=quiet)

        output.info(f"Reversing {len(files)} TypeScript/Prisma file(s)")

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Track all parsed content
        all_entities = []  # (entity, enums, source_file)
        all_routes = []  # (routes, source_file)

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            if _is_prisma_file(path):
                # Parse Prisma schema
                _parse_prisma_file(path, all_entities, framework)
            else:
                # Parse TypeScript routes
                _parse_typescript_file(path, all_routes, framework)

        # Summary
        entity_count = len(all_entities)
        route_count = sum(len(routes) for routes, _ in all_routes)
        output.info(f"  Found {entity_count} model(s), {route_count} route(s)")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for entity, _, source_file in all_entities:
                output.info(f"    {entity.name.lower()}.yaml (from {source_file})")
            for routes, source_file in all_routes:
                if routes:
                    output.info(f"    {Path(source_file).stem}_routes.yaml (from {source_file})")
            return

        # Generate YAML files
        generated_files = []

        # Generate YAML for Prisma entities
        for entity, enums, source_file in all_entities:
            yaml_content = _generate_yaml_from_prisma_entity(entity, enums)
            yaml_path = output_path / f"{entity.name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        # Generate YAML for routes (as documentation/actions)
        for routes, source_file in all_routes:
            if routes:
                yaml_content = _generate_yaml_from_routes(routes, source_file)
                if yaml_content:
                    route_name = Path(source_file).stem
                    yaml_path = output_path / f"{route_name}_routes.yaml"
                    yaml_path.write_text(yaml_content)
                    generated_files.append(yaml_path.name)
                    output.success(f"    Created: {yaml_path.name} (routes)")

        output.success(f"Generated {len(generated_files)} file(s)")


def _parse_prisma_file(path: Path, all_entities: list, framework: str | None):
    """Parse a Prisma schema file and add entities to the list."""
    try:
        from reverse_engineering.prisma_parser import PrismaSchemaParser
    except ImportError as e:
        output.warning(f"    Prisma parser not available: {e}")
        output.info("    Install with: pip install specql[reverse]")
        return

    try:
        parser = PrismaSchemaParser()
        source_code = path.read_text()
        entities = parser.parse_schema(source_code)

        # Get enums for type mapping
        enums = parser.enums

        output.info(f"    Detected: Prisma schema ({len(entities)} models)")

        for entity in entities:
            all_entities.append((entity, enums, path.name))

    except Exception as e:
        output.warning(f"    Failed to parse Prisma schema: {e}")


def _parse_typescript_file(path: Path, all_routes: list, framework: str | None):
    """Parse a TypeScript file for routes and add to the list."""
    try:
        from reverse_engineering.typescript_parser import TypeScriptParser
    except ImportError as e:
        output.warning(f"    TypeScript parser not available: {e}")
        return

    try:
        parser = TypeScriptParser()
        source_code = path.read_text()
        file_path_str = str(path)

        # Detect framework
        detected_framework = framework or _detect_typescript_framework(source_code, file_path_str)
        output.info(f"    Detected: {detected_framework}")

        routes = []

        # Extract routes based on framework
        if detected_framework in ("express", "fastify", "unknown"):
            routes.extend(parser.extract_routes(source_code))

        # Next.js App Router
        if (
            detected_framework == "nextjs-app"
            or "route.ts" in file_path_str
            or "route.js" in file_path_str
        ):
            routes.extend(parser.extract_nextjs_app_routes(source_code, file_path_str))

        # Next.js Pages Router
        if detected_framework == "nextjs-pages" or "/pages/api/" in file_path_str:
            routes.extend(parser.extract_nextjs_pages_routes(source_code, file_path_str))

        # Server Actions
        if detected_framework == "nextjs-server-actions":
            actions = parser.extract_server_actions(source_code)
            output.info(f"    Found {len(actions)} server action(s)")

        if routes:
            output.info(f"    Found {len(routes)} route(s)")
            all_routes.append((routes, path.name))
        else:
            output.info("    No routes found")

    except Exception as e:
        output.warning(f"    Failed to parse TypeScript: {e}")
