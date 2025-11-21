"""
Reverse Python subcommand - Convert Django/FastAPI/SQLAlchemy models to SpecQL YAML.

Integrates with:
- PythonASTParser: Parses Python classes using ast module
- Supports: Django, Pydantic, SQLAlchemy, Dataclasses
"""

from pathlib import Path

import click
import yaml

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _detect_framework(source_code: str) -> str:
    """Auto-detect Python framework from imports and patterns."""
    if "from django" in source_code or "import django" in source_code:
        return "django"
    if "from pydantic" in source_code or "BaseModel" in source_code:
        return "pydantic"
    if "from sqlalchemy" in source_code or "declarative_base" in source_code:
        return "sqlalchemy"
    if "@dataclass" in source_code:
        return "dataclass"
    return "unknown"


def _generate_yaml_from_entity(entity, detected_patterns: list[str]) -> str:
    """Generate SpecQL YAML from ParsedEntity."""
    yaml_dict = {
        "entity": entity.entity_name,
        "schema": entity.namespace or "public",
        "description": entity.docstring or f"Auto-generated from {entity.entity_name}",
        "fields": {},
        "_metadata": {
            "source_language": "python",
            "patterns": detected_patterns,
            "generated_by": "specql-reverse-python",
        },
    }

    # Convert fields
    for field in entity.fields:
        field_type = field.field_type
        if not field.required:
            field_type = f"{field_type}?"
        if field.is_foreign_key and field.foreign_key_target:
            field_type = f"ref({field.foreign_key_target})"
        yaml_dict["fields"][field.field_name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework",
    type=click.Choice(["django", "fastapi", "flask", "sqlalchemy", "pydantic", "dataclass"]),
    help="Framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
def python(files, output_dir, framework, preview, **kwargs):
    """Reverse engineer Python models to SpecQL YAML.

    Supports Django, FastAPI, Flask-SQLAlchemy, SQLAlchemy, Pydantic, and dataclasses.

    Examples:

        specql reverse python src/models.py -o entities/

        specql reverse python app/models/ -o entities/ --framework=django

        specql reverse python schemas/*.py -o entities/ --preview
    """
    with handle_cli_error():
        output.info(f"Reversing {len(files)} Python file(s)")

        # Import parser - add project root to path if needed
        import sys
        from pathlib import Path as PathLib

        # Find project root (where reverse_engineering lives)
        current = PathLib(__file__).resolve()
        for parent in current.parents:
            if (parent / "reverse_engineering").exists():
                if str(parent) not in sys.path:
                    sys.path.insert(0, str(parent))
                break

        try:
            from reverse_engineering.python_ast_parser import PythonASTParser
        except ImportError as e:
            output.error(f"Python parser not available: {e}")
            raise click.Abort() from e

        parser = PythonASTParser()

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_entities = []

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            try:
                source_code = path.read_text()
            except Exception as e:
                output.warning(f"    Failed to read file: {e}")
                continue

            # Detect or use specified framework
            detected_framework = framework or _detect_framework(source_code)
            output.info(f"    Framework: {detected_framework}")

            # Parse entities
            try:
                entities = parser.parse(source_code, str(path))

                for entity in entities:
                    # Detect patterns
                    patterns = parser.detect_patterns(entity)
                    all_entities.append((entity, patterns, path.name))

            except SyntaxError as e:
                output.warning(f"    Syntax error: {e}")
                continue
            except Exception as e:
                output.warning(f"    Failed to parse: {e}")
                continue

        output.info(f"Found {len(all_entities)} entity/entities")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for entity, patterns, source_file in all_entities:
                output.info(f"    {entity.entity_name}.yaml (from {source_file})")
            return

        # Generate YAML files
        generated_files = []
        for entity, patterns, source_file in all_entities:
            yaml_content = _generate_yaml_from_entity(entity, patterns)

            yaml_path = output_path / f"{entity.entity_name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        output.success(f"Generated {len(generated_files)} file(s)")
