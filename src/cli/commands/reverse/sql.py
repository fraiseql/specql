"""
Reverse SQL subcommand - Convert SQL DDL and functions to SpecQL YAML.

Integrates with:
- SQLTableParser: Parses CREATE TABLE statements using pglast
- PatternDetectionOrchestrator: Detects Trinity, audit_trail, soft_delete patterns
- ForeignKeyDetector: Parses ALTER TABLE FOREIGN KEY statements
- EntityYAMLGenerator: Generates SpecQL YAML from parsed data
- AlgorithmicParser: Parses CREATE FUNCTION statements
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output as cli_output

if TYPE_CHECKING:
    from reverse_engineering.table_parser import ParsedTable


def _table_to_filename(table_name: str) -> str:
    """Convert table name to snake_case filename.

    Examples:
        tb_machine_contract_relationship → machine_contract_relationship.yaml
        tv_user_view → user_view.yaml
    """
    # Remove tb_ or tv_ prefix and keep snake_case
    name = table_name.removeprefix("tb_").removeprefix("tv_")
    return f"{name}.yaml"


def _extract_comments(content: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Extract COMMENT ON statements from SQL content.

    Returns:
        (table_comments, column_comments) where:
        - table_comments: {table_name: comment}
        - column_comments: {table_name: {column_name: comment}}
    """
    import re

    table_comments = {}
    column_comments = {}

    # Match: COMMENT ON TABLE schema.table IS 'comment';
    # Handle escaped quotes by matching until the final unescaped quote
    table_pattern = r"COMMENT\s+ON\s+TABLE\s+([\w.]+)\s+IS\s+'((?:[^']|'')*)'"
    for match in re.finditer(table_pattern, content, re.IGNORECASE):
        full_table_name = match.group(1)
        comment = match.group(2).replace("''", "'")  # Unescape quotes
        table_comments[full_table_name] = comment

    # Match: COMMENT ON COLUMN schema.table.column IS 'comment';
    # Handle escaped quotes by matching until the final unescaped quote
    column_pattern = r"COMMENT\s+ON\s+COLUMN\s+([\w.]+)\s+IS\s+'((?:[^']|'')*)'"
    for match in re.finditer(column_pattern, content, re.IGNORECASE):
        full_column_name = match.group(1)
        comment = match.group(2).replace("''", "'")  # Unescape quotes

        # Split schema.table.column into components
        parts = full_column_name.split(".")
        if len(parts) >= 3:
            table_name = f"{parts[-3]}.{parts[-2]}"  # schema.table
            column_name = parts[-1]

            if table_name not in column_comments:
                column_comments[table_name] = {}
            column_comments[table_name][column_name] = comment

    return table_comments, column_comments


@dataclass
class SourceFileInfo:
    """Metadata extracted from source file path."""

    full_path: Path
    prefix: str | None  # e.g., "010111"
    table_name: str  # e.g., "tb_language"
    parent_dirs: list[str]  # e.g., ["0_schema", "01_write_side", "010_i18n", ...]


def _parse_source_path(file_path: Path) -> SourceFileInfo:
    """Extract hierarchical numbering from source file path.

    Input: db/0_schema/01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql
    Output: SourceFileInfo(prefix="010111", table_name="tb_language", parent_dirs=[...])
    """
    import re

    filename = file_path.stem  # "010111_tb_language"
    match = re.match(r"^(\d+)_(.+)$", filename)

    if match:
        return SourceFileInfo(
            full_path=file_path,
            prefix=match.group(1),
            table_name=match.group(2),
            parent_dirs=[p.name for p in file_path.parents if p.name != "."],
        )
    else:
        return SourceFileInfo(
            full_path=file_path,
            prefix=None,
            table_name=filename,
            parent_dirs=[p.name for p in file_path.parents if p.name != "."],
        )


def _generate_hierarchical_path(
    source_info: SourceFileInfo, entity_name: str, table_name: str
) -> Path:
    """Generate hierarchical output path from source file info.

    Input: SourceFileInfo(prefix="010111", parent_dirs=["db", "0_schema", "01_write_side", "010_i18n", "0101_locale", "01011_language"])
    Output: entities/010_i18n/0101_locale/01011_language/010111_language.yaml
    """
    if not source_info.prefix:
        # No numbering, use flat structure with snake_case filename
        filename = _table_to_filename(table_name)
        return Path("entities") / filename

    # Filter out non-hierarchical directories
    hierarchical_dirs = [
        d
        for d in source_info.parent_dirs
        if d not in ["db", "0_schema", "01_write_side"] and d.startswith(("0", "1", "2"))
    ]

    # Sort directories by numeric prefix length (shortest first)
    hierarchical_dirs.sort(key=lambda x: len(x.split("_")[0]))

    # Construct path: entities/dir1/dir2/.../prefix_entity.yaml
    path_parts = (
        ["entities"] + hierarchical_dirs + [f"{source_info.prefix}_{entity_name.lower()}.yaml"]
    )
    return Path(*path_parts)


def _generate_project_yaml(
    all_tables: list[tuple[SourceFileInfo, "ParsedTable"]], output_dir: Path, source_file: str
):
    """Generate project.yaml and registry from reverse-engineered tables."""
    from core.project_config import ProjectConfig

    # Extract just the ParsedTable objects
    parsed_tables = [table for _, table in all_tables]

    # Create project config
    config = ProjectConfig.from_reverse_engineering(parsed_tables, source_file)

    # Write project.yaml
    project_path = output_dir / "project.yaml"
    project_path.write_text(config.to_yaml())

    # Generate and write registry
    registry_path = output_dir / "registry" / "domain_registry.yaml"
    registry_path.parent.mkdir(exist_ok=True)
    registry_path.write_text(config.generate_registry_yaml())

    from cli.utils.output import output

    output.success(f"    Created: {project_path.name}")
    output.success(f"    Created: {registry_path.relative_to(output_dir)}")


def _extract_statements(content: str) -> tuple[list[str], list[str], list[str]]:
    """
    Extract CREATE TABLE, CREATE FUNCTION, and ALTER TABLE statements from SQL.

    Returns:
        tuple of (create_tables, create_functions, alter_tables)
    """
    import re

    # Split content into statements (handle $$ blocks for functions)
    # Simple approach: split by semicolon but respect $$ blocks
    create_tables = []
    create_functions = []
    alter_tables = []

    # Find CREATE TABLE statements
    table_pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\w.]+\s*\([^;]+\);"
    for match in re.finditer(table_pattern, content, re.IGNORECASE | re.DOTALL):
        create_tables.append(match.group(0))

    # Find CREATE FUNCTION statements (with $$ delimited bodies)
    func_pattern = r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION[^$]+\$\$[^$]*\$\$[^;]*;"
    for match in re.finditer(func_pattern, content, re.IGNORECASE | re.DOTALL):
        create_functions.append(match.group(0))

    # Find ALTER TABLE ... FOREIGN KEY statements
    alter_pattern = r"ALTER\s+TABLE\s+[\w.]+\s+ADD\s+CONSTRAINT[^;]+FOREIGN\s+KEY[^;]+;"
    for match in re.finditer(alter_pattern, content, re.IGNORECASE | re.DOTALL):
        alter_tables.append(match.group(0))

    return create_tables, create_functions, alter_tables


def _parse_table_safe(parser, sql: str) -> "ParsedTable | None":
    """Parse a single CREATE TABLE statement, returning None on error."""
    try:
        return parser.parse_table(sql)
    except Exception as e:
        cli_output.warning(f"    Failed to parse table: {e}")
        return None


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output", required=True, type=click.Path(), help="Output directory")
@click.option("--min-confidence", default=0.80, type=float, help="Minimum confidence threshold")
@click.option("--no-ai", is_flag=True, help="Skip AI enhancement")
@click.option("--merge-translations/--no-merge-translations", default=True)
@click.option("--preview", is_flag=True, help="Preview without writing")
@click.option("--with-patterns", is_flag=True, help="Auto-detect and apply patterns")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def sql(
    files,
    output,
    min_confidence,
    no_ai,
    merge_translations,
    preview,
    with_patterns,
    verbose,
    quiet,
    **kwargs,
):
    """Reverse engineer SQL files to SpecQL YAML.

    Handles both table DDL and PL/pgSQL functions. Auto-detects
    Trinity pattern, foreign keys, audit fields, and more.

    Examples:

        specql reverse sql db/tables/*.sql -o entities/

        specql reverse sql functions.sql -o entities/ --no-ai

        specql reverse sql db/ -o entities/ --with-patterns
    """
    with handle_cli_error():
        # Configure output settings
        from cli.utils.output import set_output_config

        set_output_config(verbose=verbose, quiet=quiet)

        cli_output.info(f"Reversing {len(files)} SQL file(s)")

        # Import parsers (lazy to handle optional dependencies)
        try:
            from reverse_engineering.entity_generator import EntityYAMLGenerator
            from reverse_engineering.fk_detector import ForeignKeyDetector
            from reverse_engineering.pattern_orchestrator import PatternDetectionOrchestrator
            from reverse_engineering.table_parser import SQLTableParser
        except ImportError as e:
            cli_output.error(f"Missing reverse engineering dependency: {e}")
            cli_output.info("Install with: pip install specql[reverse]")
            raise click.Abort() from e

        # Initialize parsers
        try:
            table_parser = SQLTableParser()
        except ImportError as e:
            cli_output.error(f"pglast not available: {e}")
            cli_output.info("Install with: pip install specql[reverse]")
            raise click.Abort() from e

        pattern_detector = PatternDetectionOrchestrator()
        fk_detector = ForeignKeyDetector()
        yaml_generator = EntityYAMLGenerator()

        # Optionally load function parser
        func_parser = None
        if not no_ai:
            try:
                from reverse_engineering.algorithmic_parser import AlgorithmicParser

                func_parser = AlgorithmicParser(use_heuristics=True, use_ai=False)
            except ImportError:
                cli_output.warning("Function parser not available, skipping function parsing")

        # Prepare output directory
        cli_output_dir = Path(output)
        cli_output_dir.mkdir(parents=True, exist_ok=True)

        # Collect all statements from all files
        all_tables: list[tuple[SourceFileInfo, ParsedTable]] = []  # (source_info, parsed_table)
        all_functions: list[tuple[str, str]] = []  # (source_file, function_sql)
        all_alter_statements: list[str] = []
        skipped_count = 0

        for file_path in files:
            path = Path(file_path)
            cli_output.info(f"  Parsing: {path.name}")
            content = path.read_text()

            # Parse source file information
            source_info = _parse_source_path(path)

            create_tables, create_functions, alter_tables = _extract_statements(content)

            # Extract comments from full file content
            table_comments, column_comments = _extract_comments(content)

            # Parse tables
            for table_sql in create_tables:
                parsed = _parse_table_safe(table_parser, table_sql)
                if parsed:
                    # Associate comments with the parsed table
                    full_table_name = f"{parsed.schema}.{parsed.table_name}"
                    if full_table_name in table_comments:
                        parsed.table_comment = table_comments[full_table_name]
                    if full_table_name in column_comments:
                        parsed.column_comments = column_comments[full_table_name]

                    all_tables.append((source_info, parsed))
                else:
                    skipped_count += 1

            # Collect functions for later processing
            all_functions.extend((path.name, func_sql) for func_sql in create_functions)

            # Collect ALTER TABLE statements for FK detection
            all_alter_statements.extend(alter_tables)

        # Detect foreign keys across all ALTER TABLE statements
        # Note: FK detector needs a ParsedTable but we use it for regex parsing only
        fk_map: dict[str, list] = {}  # table_name -> list of FKs
        for alter_sql in all_alter_statements:
            # Extract table name from ALTER TABLE statement
            import re

            table_match = re.search(r"ALTER\s+TABLE\s+([\w.]+)", alter_sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1).split(".")[-1]  # Get just the table name
                fks = fk_detector._parse_alter_table_fk(alter_sql)
                if table_name not in fk_map:
                    fk_map[table_name] = []
                fk_map[table_name].extend(fks)

        # Summary
        cli_output.info(f"  Found {len(all_tables)} table(s), {len(all_functions)} function(s)")
        if skipped_count > 0:
            cli_output.warning(f"  Skipped {skipped_count} unparseable statement(s)")

        if preview:
            cli_output.info("Preview mode - showing what would be generated:")
            for source_info, table in all_tables:
                entity_name = yaml_generator._table_to_entity_name(table.table_name)
                output_path = _generate_hierarchical_path(
                    source_info, entity_name, table.table_name
                )
                cli_output.info(f"    {output_path} (from {source_info.full_path.name})")
            for source_file, func_sql in all_functions:
                import re

                func_match = re.search(r"FUNCTION\s+([\w.]+)", func_sql, re.IGNORECASE)
                if func_match:
                    cli_output.info(f"    {func_match.group(1)}.yaml (from {source_file})")
            return

        # Generate YAML for tables
        generated_files = []
        low_confidence_files = []

        for source_info, table in all_tables:
            # Detect patterns
            patterns = pattern_detector.detect_all(table)

            # Get foreign keys for this table
            table_fks = fk_map.get(table.table_name, [])

            # Generate YAML
            yaml_content = yaml_generator.generate(table, patterns, table_fks)

            # Check confidence threshold
            if patterns.confidence < min_confidence:
                low_confidence_files.append(
                    (table.table_name, patterns.confidence, patterns.patterns)
                )

            # Generate hierarchical path
            entity_name = yaml_generator._table_to_entity_name(table.table_name)
            relative_path = _generate_hierarchical_path(source_info, entity_name, table.table_name)
            yaml_path = cli_output_dir / relative_path

            # Create parent directories
            yaml_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            yaml_path.write_text(yaml_content)
            generated_files.append(str(relative_path))
            cli_output.success(f"    Created: {relative_path}")

            # Generate YAML for functions (if parser available)
            if func_parser and all_functions:
                for source_file, func_sql in all_functions:
                    try:
                        yaml_content = func_parser.parse_to_yaml(func_sql)
                        # Extract function name for filename
                        import re

                        func_match = re.search(r"FUNCTION\s+([\w.]+)", func_sql, re.IGNORECASE)
                        if func_match:
                            func_name = func_match.group(1).split(".")[-1]
                            yaml_path = cli_output_dir / f"{func_name}_action.yaml"
                            yaml_path.write_text(yaml_content)
                            generated_files.append(yaml_path.name)
                            cli_output.success(f"    Created: {yaml_path.name} (action)")
                    except Exception as e:
                        cli_output.warning(f"    Failed to parse function: {e}")

        # Generate project.yaml
        if all_tables:
            _generate_project_yaml(all_tables, cli_output_dir, files[0])

        cli_output.success(f"Generated {len(generated_files)} file(s)")

        if low_confidence_files:
            cli_output.warning(
                f"  {len(low_confidence_files)} file(s) below confidence threshold ({min_confidence:.0%}):"
            )
            for table_name, confidence, patterns in low_confidence_files:
                cli_output.warning(f"    {table_name}: {confidence:.0%} (patterns: {patterns})")
