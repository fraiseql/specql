"""
Reverse Java subcommand - Convert JPA/Hibernate entities to SpecQL YAML.

Integrates with:
- JavaParser: Parses Java files and extracts JPA entities
- JPAToSpecQLConverter: Converts JPA entities to SpecQL format
- JDTBridge: Uses Eclipse JDT for parsing (falls back to regex-based mock)
"""

from pathlib import Path

import click
import yaml

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _detect_java_orm(source_code: str) -> str:
    """Auto-detect Java ORM from imports and annotations."""
    if "jakarta.persistence" in source_code:
        return "hibernate"
    if "javax.persistence" in source_code:
        return "jpa"
    if "org.springframework.data" in source_code:
        return "spring-data"
    return "unknown"


def _map_java_type_to_specql(java_type: str) -> str:
    """Map Java types to SpecQL types."""
    type_map = {
        # Primitives
        "int": "integer",
        "long": "integer",
        "short": "integer",
        "byte": "integer",
        "float": "decimal",
        "double": "decimal",
        "boolean": "boolean",
        # Wrappers
        "Integer": "integer",
        "Long": "integer",
        "Short": "integer",
        "Byte": "integer",
        "Float": "decimal",
        "Double": "decimal",
        "Boolean": "boolean",
        "BigDecimal": "decimal",
        "BigInteger": "integer",
        # String
        "String": "text",
        "char": "text",
        "Character": "text",
        # Date/Time
        "LocalDate": "date",
        "LocalDateTime": "timestamp",
        "LocalTime": "time",
        "Instant": "timestamp",
        "ZonedDateTime": "timestamp",
        "Date": "timestamp",
        "Timestamp": "timestamp",
        # UUID
        "UUID": "uuid",
        # Binary
        "byte[]": "blob",
        "Byte[]": "blob",
    }
    return type_map.get(java_type, "text")


def _generate_yaml_from_entity(entity) -> str:
    """Generate SpecQL YAML from Entity (from core.ast_models)."""
    yaml_dict = {
        "entity": entity.name,
        "schema": entity.schema or "public",
        "description": f"Auto-generated from JPA entity {entity.name}",
        "fields": {},
        "_metadata": {
            "source_language": "java",
            "source_table": entity.table,
            "generated_by": "specql-reverse-java",
        },
    }

    # Convert fields
    for field_name, field in entity.fields.items():
        field_type = field.type_name

        # Handle references
        if field.reference_entity:
            field_type = f"ref({field.reference_entity})"
        elif field.item_type:
            # OneToMany relationship
            field_type = f"list({field.item_type})"

        # Add optional marker
        if field.nullable:
            field_type = f"{field_type}?"

        yaml_dict["fields"][field_name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--orm",
    type=click.Choice(["jpa", "hibernate", "spring-data"]),
    help="ORM framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def java(files, output_dir, orm, preview, verbose, quiet, **kwargs):
    """Reverse engineer Java JPA/Hibernate entities to SpecQL YAML.

    Supports JPA, Hibernate (jakarta.persistence), and Spring Data entities.

    Examples:

        specql reverse java src/main/java/model/Contact.java -o entities/

        specql reverse java src/main/java/model/*.java -o entities/

        specql reverse java entity/ -o entities/ --orm=hibernate --preview
    """
    with handle_cli_error():
        # Configure output settings
        from cli.utils.output import set_output_config

        set_output_config(verbose=verbose, quiet=quiet)

        output.info(f"Reversing {len(files)} Java file(s)")

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Track all parsed entities
        all_entities = []  # (entity, orm_type, source_file)

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            try:
                source_code = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                output.warning(f"    Could not read file (encoding error): {path.name}")
                continue

            if not source_code.strip():
                output.info("    Empty file, skipping")
                continue

            # Detect ORM type
            detected_orm = orm or _detect_java_orm(source_code)
            if detected_orm != "unknown":
                output.info(f"    Detected ORM: {detected_orm}")

            # Parse Java file
            _parse_java_file(path, all_entities, detected_orm)

        # Summary
        output.info(f"  Found {len(all_entities)} entity/entities")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for entity, _, source_file in all_entities:
                output.info(f"    {entity.name.lower()}.yaml (from {source_file})")
            return

        # Generate YAML files
        generated_files = []
        for entity, orm_type, source_file in all_entities:
            yaml_content = _generate_yaml_from_entity(entity)
            yaml_path = output_path / f"{entity.name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        output.success(f"Generated {len(generated_files)} file(s)")


def _parse_java_file(path: Path, all_entities: list, orm_type: str):
    """Parse a Java file using JavaParser."""
    try:
        from reverse_engineering.java.java_parser import JavaParser
    except ImportError as e:
        output.warning(f"    Java parser not available: {e}")
        return

    try:
        parser = JavaParser()
        result = parser.parse_file(str(path))

        if result.errors:
            for error in result.errors:
                output.warning(f"    {error}")

        if result.entities:
            output.info(f"    Found {len(result.entities)} JPA entity/entities")
            for entity in result.entities:
                all_entities.append((entity, orm_type, path.name))

    except Exception as e:
        output.warning(f"    Failed to parse Java file: {e}")
