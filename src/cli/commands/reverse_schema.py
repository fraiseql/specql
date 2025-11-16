"""
CLI command for reverse engineering SQL schemas to SpecQL YAML

Usage:
    specql reverse-schema path/to/schema/ --output-dir entities/
    specql reverse-schema db/0_schema/01_write_side --output-dir entities/ --recursive
"""

import click
from pathlib import Path
from typing import List, Tuple
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.core.specql_generator import SpecQLGenerator


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory for YAML files",
)
@click.option(
    "--recursive/--no-recursive", default=True, help="Recursively scan subdirectories"
)
@click.option(
    "--extract-table-codes/--no-extract-table-codes",
    default=True,
    help="Extract table codes from filenames and COMMENTs",
)
@click.option(
    "--preserve-hierarchy/--flatten",
    default=False,
    help="Preserve directory hierarchy in output (default: flatten to single dir)",
)
@click.option(
    "--filter-category",
    type=click.Choice(["write_side", "query_side", "functions", "all"]),
    default="all",
    help="Filter by category (default: all)",
)
@click.option(
    "--exclude-translations/--include-translations",
    default=True,
    help="Exclude translation tables (tl_*)",
)
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option(
    "--validate-consistency/--no-validate-consistency",
    default=True,
    help="Validate table code consistency between filename and COMMENT",
)
def reverse_schema(
    input_path: str,
    output_dir: str,
    recursive: bool,
    extract_table_codes: bool,
    preserve_hierarchy: bool,
    filter_category: str,
    exclude_translations: bool,
    preview: bool,
    validate_consistency: bool,
):
    """
    Reverse engineer PostgreSQL schema to SpecQL YAML entities

    Examples:
        # Convert entire PrintOptim schema
        specql reverse-schema ../printoptim_backend_migration/db/0_schema \\
            --output-dir entities/ --recursive

        # Only write-side tables, exclude translations
        specql reverse-schema db/0_schema/01_write_side \\
            --output-dir entities/ \\
            --filter-category write_side \\
            --exclude-translations

        # Preview mode (dry run)
        specql reverse-schema db/0_schema --output-dir entities/ --preview
    """

    input_path_obj = Path(input_path)
    output_path = Path(output_dir)

    click.echo(f"🔄 Scanning {input_path}...")

    # 1. Discover SQL files
    sql_files = _discover_sql_files(
        input_path_obj,
        recursive=recursive,
        filter_category=filter_category,
        exclude_translations=exclude_translations,
    )

    click.echo(f"📁 Found {len(sql_files)} SQL files")

    # 2. Process each file
    analyzer = SchemaAnalyzer()
    entities = []
    errors = []

    for sql_file in sql_files:
        try:
            click.echo(f"  Processing {sql_file.name}...")

            # Read SQL
            sql = sql_file.read_text()

            # Parse with metadata
            entity = analyzer.parse_create_table_with_metadata(
                ddl=sql, file_path=sql_file, root_dir=input_path_obj
            )

            # Validate consistency
            if validate_consistency and entity.organization:
                _validate_table_code_consistency(entity, sql_file)

            entities.append((entity, sql_file))

        except Exception as e:
            errors.append((sql_file, str(e)))
            click.echo(f"    ❌ Error: {e}")

    # 3. Generate YAML files
    if not preview:
        _write_yaml_files(entities, output_path, preserve_hierarchy, input_path_obj)
    else:
        _preview_yaml_files(entities)

    # 4. Summary
    _print_summary(entities, errors)


def _discover_sql_files(
    root: Path, recursive: bool, filter_category: str, exclude_translations: bool
) -> List[Path]:
    """Discover SQL files matching criteria"""

    pattern = "**/*.sql" if recursive else "*.sql"
    all_files = list(root.glob(pattern))

    # Filter by category
    if filter_category != "all":
        category_prefix = f"{_get_category_prefix(filter_category)}_"
        all_files = [
            f
            for f in all_files
            if any(category_prefix in str(part) for part in f.parts)
        ]

    # Exclude translations
    if exclude_translations:
        all_files = [
            f
            for f in all_files
            if not f.stem.split("_")[1] == "tl"  # {code}_tl_{name}
        ]

    # Only table files (tb_*, tl_*, not fn_*)
    all_files = [f for f in all_files if f.stem.split("_")[1] in ["tb", "tl"]]

    return sorted(all_files)


def _get_category_prefix(category: str) -> str:
    """Map category to directory prefix"""
    mapping = {"write_side": "01", "query_side": "02", "functions": "03"}
    return mapping.get(category, "")


def _validate_table_code_consistency(entity, file_path: Path):
    """Validate table code consistency between filename and COMMENT"""

    org = entity.organization or {}

    # Extract from filename
    filename_code = file_path.stem.split("_")[0]

    # Extract from organization
    comment_code = org.get("table_code", "")

    if comment_code and filename_code != comment_code:
        click.secho(
            f"    ⚠️  Warning: Table code mismatch - "
            f"filename={filename_code}, comment={comment_code}",
            fg="yellow",
        )


def _write_yaml_files(
    entities: List[Tuple], output_dir: Path, preserve_hierarchy: bool, root_dir: Path
):
    """Write entities to YAML files"""

    output_dir.mkdir(parents=True, exist_ok=True)

    for entity, source_file in entities:
        # Determine output path
        if preserve_hierarchy:
            # Recreate directory structure
            rel_path = source_file.relative_to(root_dir)
            output_path = output_dir / rel_path.parent / f"{entity.name}.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Flatten to output directory
            output_path = output_dir / f"{entity.name}.yaml"

        # Generate YAML
        yaml_content = _entity_to_yaml(entity)

        # Write file
        output_path.write_text(yaml_content)

        click.echo(f"    💾 Written to {output_path}")


def _entity_to_yaml(entity) -> str:
    """Convert UniversalEntity to SpecQL YAML"""


    generator = SpecQLGenerator()
    return generator.generate_yaml(entity)


def _preview_yaml_files(entities: List[Tuple]):
    """Preview YAML output without writing"""

    for entity, source_file in entities:
        click.echo(f"\n--- {entity.name}.yaml ---")
        yaml_content = _entity_to_yaml(entity)
        click.echo(yaml_content[:500])  # First 500 chars
        click.echo("...")


def _print_summary(entities: List[Tuple], errors: List[Tuple[Path, str]]):
    """Print processing summary"""

    click.echo("\n📊 Summary:")
    click.echo(f"  ✅ Successfully processed: {len(entities)}")
    click.echo(f"  ❌ Errors: {len(errors)}")

    if errors:
        click.echo("\n❌ Failed files:")
        for file_path, error in errors:
            click.echo(f"  • {file_path.name}: {error}")
