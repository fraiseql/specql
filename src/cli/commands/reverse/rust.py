"""
Reverse Rust subcommand - Convert Diesel/SeaORM schemas to SpecQL YAML.

Integrates with:
- RustParser: Parses Rust structs, Diesel tables, and route handlers
- SeaORMParser: Extracts SeaORM entity models
- RustReverseEngineeringService: Coordinates all Rust reverse engineering
"""

from pathlib import Path

import click
import yaml

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _detect_rust_orm(source_code: str) -> str:
    """Auto-detect Rust ORM from imports and patterns."""
    if "use sea_orm" in source_code or "DeriveEntityModel" in source_code:
        return "seaorm"
    if "use diesel" in source_code or "diesel::table!" in source_code or "#[table_name" in source_code:
        return "diesel"
    if "use sqlx" in source_code:
        return "sqlx"
    return "unknown"


def _detect_rust_web_framework(source_code: str) -> str | None:
    """Detect Rust web framework from imports."""
    if "use actix_web" in source_code or "#[get(" in source_code or "#[post(" in source_code:
        return "actix"
    if "use rocket::" in source_code:
        return "rocket"
    if "use axum::" in source_code:
        return "axum"
    if "use warp::" in source_code:
        return "warp"
    if "use tide::" in source_code:
        return "tide"
    return None


def _map_rust_type_to_specql(rust_type: str) -> str:
    """Map Rust types to SpecQL types."""
    # Handle Option<T>
    if rust_type.startswith("Option<"):
        inner = rust_type[7:-1]
        return _map_rust_type_to_specql(inner)

    type_map = {
        "i8": "smallint",
        "i16": "smallint",
        "i32": "integer",
        "i64": "bigint",
        "u8": "smallint",
        "u16": "smallint",
        "u32": "integer",
        "u64": "bigint",
        "f32": "real",
        "f64": "double_precision",
        "bool": "boolean",
        "String": "text",
        "str": "text",
        "&str": "text",
        "NaiveDateTime": "timestamp",
        "DateTime": "timestamp",
        "NaiveDate": "date",
        "NaiveTime": "time",
        "Uuid": "uuid",
    }
    return type_map.get(rust_type, "text")


def _generate_yaml_from_entity(entity) -> str:
    """Generate SpecQL YAML from Entity."""
    yaml_dict = {
        "entity": entity.name,
        "schema": entity.schema or "public",
        "description": entity.description or f"Auto-generated from {entity.name}",
        "fields": {},
        "_metadata": {
            "source_language": "rust",
            "source_table": entity.table,
            "generated_by": "specql-reverse-rust",
        },
    }

    # Convert fields
    for field_name, field in entity.fields.items():
        field_type = field.type_name

        # Handle references
        if field.reference_entity:
            field_type = f"ref({field.reference_entity})"

        # Add optional marker
        if field.nullable:
            field_type = f"{field_type}?"

        yaml_dict["fields"][field_name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


def _generate_yaml_from_seaorm_entity(entity) -> str:
    """Generate SpecQL YAML from SeaORMEntity."""
    yaml_dict = {
        "entity": entity.name,
        "schema": "public",
        "description": f"Auto-generated from SeaORM entity {entity.name}",
        "fields": {},
        "_metadata": {
            "source_language": "rust",
            "source_table": entity.table_name,
            "orm": "seaorm",
            "generated_by": "specql-reverse-rust",
        },
    }

    # Convert fields
    for field in entity.fields:
        field_type = _map_rust_type_to_specql(field.type_name)

        # Handle foreign keys
        if field.name.endswith("_id"):
            ref_name = "".join(word.capitalize() for word in field.name[:-3].split("_"))
            field_type = f"ref({ref_name})"

        # Add optional marker
        if field.is_nullable:
            field_type = f"{field_type}?"

        yaml_dict["fields"][field.name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


def _generate_yaml_from_routes(routes: list, source_file: str, framework: str) -> str | None:
    """Generate SpecQL YAML from extracted routes."""
    if not routes:
        return None

    yaml_dict = {
        "_routes": {
            "source_file": source_file,
            "framework": framework,
            "endpoints": [
                {
                    "method": r.method,
                    "path": r.path,
                    "handler": r.function_name,
                    "async": r.is_async,
                }
                for r in routes
            ],
        },
        "_metadata": {
            "source_language": "rust",
            "generated_by": "specql-reverse-rust",
            "note": "Routes extracted - manual action definition required",
        },
    }

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework",
    type=click.Choice(["diesel", "seaorm", "sqlx"]),
    help="ORM framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def rust(files, output_dir, framework, preview, verbose, quiet, **kwargs):
    """Reverse engineer Rust schemas to SpecQL YAML.

    Supports Diesel, SeaORM, and SQLx schemas. Also extracts routes from
    Actix-web, Rocket, Axum, Warp, and Tide.

    Examples:

        specql reverse rust src/schema.rs -o entities/

        specql reverse rust src/models/ -o entities/ --framework=diesel

        specql reverse rust src/entity/ -o entities/ --framework=seaorm
    """
    with handle_cli_error():
        # Configure output settings
        from cli.utils.output import set_output_config

        set_output_config(verbose=verbose, quiet=quiet)

        output.info(f"Reversing {len(files)} Rust file(s)")

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Track all parsed content
        all_entities = []  # (entity, orm_type, source_file)
        all_seaorm_entities = []  # (seaorm_entity, source_file)
        all_routes = []  # (routes, framework, source_file)

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            source_code = path.read_text()

            # Detect ORM type
            detected_orm = framework or _detect_rust_orm(source_code)
            output.info(f"    Detected ORM: {detected_orm}")

            # Detect web framework
            web_framework = _detect_rust_web_framework(source_code)
            if web_framework:
                output.info(f"    Detected Web: {web_framework}")

            # Parse based on ORM type
            if detected_orm == "seaorm":
                _parse_seaorm_file(path, source_code, all_seaorm_entities)
            elif detected_orm == "diesel":
                _parse_diesel_file(path, all_entities, detected_orm)
            else:
                # Try both approaches
                _parse_diesel_file(path, all_entities, detected_orm)
                _parse_seaorm_file(path, source_code, all_seaorm_entities)

            # Extract routes if web framework detected
            if web_framework:
                _parse_routes(path, source_code, all_routes, web_framework)

        # Summary
        entity_count = len(all_entities) + len(all_seaorm_entities)
        route_count = sum(len(routes) for routes, _, _ in all_routes)
        output.info(f"  Found {entity_count} entity/entities, {route_count} route(s)")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for entity, _, source_file in all_entities:
                output.info(f"    {entity.name.lower()}.yaml (from {source_file})")
            for entity, source_file in all_seaorm_entities:
                output.info(f"    {entity.name.lower()}.yaml (from {source_file})")
            for routes, fw, source_file in all_routes:
                if routes:
                    output.info(f"    {Path(source_file).stem}_routes.yaml (from {source_file})")
            return

        # Generate YAML files
        generated_files = []

        # Generate YAML for regular entities (from RustReverseEngineeringService)
        for entity, orm_type, source_file in all_entities:
            yaml_content = _generate_yaml_from_entity(entity)
            yaml_path = output_path / f"{entity.name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        # Generate YAML for SeaORM entities
        for entity, source_file in all_seaorm_entities:
            yaml_content = _generate_yaml_from_seaorm_entity(entity)
            yaml_path = output_path / f"{entity.name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        # Generate YAML for routes
        for routes, fw, source_file in all_routes:
            if routes:
                yaml_content = _generate_yaml_from_routes(routes, source_file, fw)
                if yaml_content:
                    route_name = Path(source_file).stem
                    yaml_path = output_path / f"{route_name}_routes.yaml"
                    yaml_path.write_text(yaml_content)
                    generated_files.append(yaml_path.name)
                    output.success(f"    Created: {yaml_path.name} (routes)")

        output.success(f"Generated {len(generated_files)} file(s)")


def _parse_seaorm_file(path: Path, source_code: str, all_seaorm_entities: list):
    """Parse a SeaORM entity file."""
    try:
        from reverse_engineering.seaorm_parser import SeaORMParser
    except ImportError as e:
        output.warning(f"    SeaORM parser not available: {e}")
        return

    try:
        parser = SeaORMParser()
        entities = parser.extract_entities(source_code)

        if entities:
            output.info(f"    Found {len(entities)} SeaORM entity/entities")
            for entity in entities:
                all_seaorm_entities.append((entity, path.name))

    except Exception as e:
        output.warning(f"    Failed to parse SeaORM: {e}")


def _parse_diesel_file(path: Path, all_entities: list, orm_type: str):
    """Parse a Diesel file using RustReverseEngineeringService."""
    try:
        from reverse_engineering.rust_parser import RustReverseEngineeringService
    except ImportError as e:
        output.warning(f"    Rust parser not available: {e}")
        return

    try:
        service = RustReverseEngineeringService()
        entities = service.reverse_engineer_file(path)

        if entities:
            output.info(f"    Found {len(entities)} Diesel entity/entities")
            for entity in entities:
                all_entities.append((entity, orm_type, path.name))

    except Exception as e:
        output.warning(f"    Failed to parse Diesel: {e}")


def _parse_routes(path: Path, source_code: str, all_routes: list, framework: str):
    """Parse route handlers from a Rust file."""
    try:
        from reverse_engineering.rust_parser import RustParser
    except ImportError as e:
        output.warning(f"    Rust parser not available: {e}")
        return

    try:
        parser = RustParser()
        _, _, _, _, _, routes = parser.parse_file(path)

        if routes:
            output.info(f"    Found {len(routes)} route(s)")
            all_routes.append((routes, framework, path.name))

    except Exception as e:
        output.warning(f"    Failed to parse routes: {e}")
