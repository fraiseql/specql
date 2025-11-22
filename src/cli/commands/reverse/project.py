"""
Reverse project subcommand - Auto-detect and process entire projects.
"""

from pathlib import Path

import click
from click.testing import CliRunner

from cli.main import app
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def detect_project_type(directory: Path) -> str:
    """Auto-detect project type from files."""
    if (directory / "manage.py").exists():
        return "django"
    if (directory / "Cargo.toml").exists():
        return "rust"
    if (directory / "package.json").exists():
        pkg = Path(directory / "package.json")
        try:
            import json

            with open(pkg) as f:
                data = json.load(f)
            if "prisma" in data.get("dependencies", {}):
                return "prisma"
            return "typescript"
        except Exception:
            return "typescript"
    if (directory / "requirements.txt").exists():
        return "python"

    # Check for SQL-based projects (FraiseQL, raw SQL schemas)
    sql_dirs = ["db", "schema", "sql", "database"]
    for sql_dir in sql_dirs:
        sql_path = directory / sql_dir
        if sql_path.exists() and sql_path.is_dir():
            sql_files = list(sql_path.glob("**/*.sql"))
            if sql_files:
                return "sql"

    # Also check for SQL files in root
    root_sql_files = list(directory.glob("*.sql"))
    if root_sql_files:
        return "sql"

    return "unknown"


# Files and directories to exclude from processing
EXCLUDE_PATTERNS = {
    "__pycache__",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "env",
    "target",  # Rust build directory
    "dist",
    "build",
    ".next",
    ".nuxt",
    "migrations",  # Django migrations
    "alembic",  # Alembic migrations
}

FRAMEWORK_HANDLERS = {
    "django": {
        "pattern": "**/models.py",
        "handler": "python",
    },
    "python": {
        "pattern": "**/*.py",
        "handler": "python",
    },
    "rust": {
        "pattern": "**/schema.rs",
        "handler": "rust",
    },
    "prisma": {
        "pattern": "**/*.prisma",
        "handler": "typescript",
    },
    "typescript": {
        "pattern": "**/*.ts",
        "handler": "typescript",
    },
    "sql": {
        "pattern": "**/*.sql",
        "handler": "sql",
    },
}


def _should_exclude_path(path: Path, directory: Path) -> bool:
    """Check if a path should be excluded from processing."""
    # Check if any parent directory is in exclude patterns
    for part in path.relative_to(directory).parts:
        if part in EXCLUDE_PATTERNS:
            return True
    return False


def process_project(
    directory: Path, framework: str, output_dir: Path, preview: bool = False
) -> list[Path]:
    """Process all relevant files in a project."""
    handler_config = FRAMEWORK_HANDLERS.get(framework)
    if not handler_config:
        raise ValueError(f"Unknown framework: {framework}")

    # Find all matching files, excluding unwanted directories
    all_files = list(directory.glob(handler_config["pattern"]))
    files = [f for f in all_files if not _should_exclude_path(f, directory)]

    if len(all_files) != len(files):
        excluded_count = len(all_files) - len(files)
        output.info(f"Excluded {excluded_count} files in ignored directories")

    if preview:
        output.info(f"Would process {len(files)} files:")
        for f in files:
            output.info(f"  - {f.relative_to(directory)}")
        return []

    # Process each file with progress reporting
    generated = []
    runner = CliRunner()
    processed_count = 0

    for file in files:
        try:
            processed_count += 1
            if len(files) > 5:  # Show progress for larger projects
                output.info(f"Processing {processed_count}/{len(files)}: {file.name}")

            result = runner.invoke(
                app, ["reverse", handler_config["handler"], str(file), "-o", str(output_dir)]
            )

            if result.exit_code == 0:
                # Find generated YAML files (search recursively for hierarchical output)
                yaml_files = list(output_dir.glob("**/*.yaml"))
                generated.extend(yaml_files)
                for yaml_file in yaml_files:
                    output.info(f"  📄 {file.name} → {yaml_file.name}")
            else:
                output.warning(f"Warning: Failed to process {file}: {result.output}")

        except Exception as e:
            output.warning(f"Warning: Failed to process {file}: {str(e)}")

    # Deduplicate entities if same entity found in multiple files
    if len(generated) > len(set(generated)):
        output.info("Deduping entities found in multiple files...")
        seen_entities = set()
        deduped = []

        for yaml_file in generated:
            entity_name = yaml_file.stem  # filename without .yaml
            if entity_name not in seen_entities:
                seen_entities.add(entity_name)
                deduped.append(yaml_file)
            else:
                output.info(f"  Skipping duplicate entity: {entity_name}")

        generated = deduped

    return generated


@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option("--framework", help="Override auto-detection")
@click.option("--preview", is_flag=True, help="Preview without writing")
def project(directory, output_dir, framework, preview, **kwargs):
    """Reverse engineer an entire project to SpecQL YAML.

    Auto-detects project type (Django, FastAPI, Rust/Diesel, Prisma, etc.)
    and processes all relevant files.

    Examples:

        specql reverse project ./my-django-app -o entities/
        specql reverse project . --framework=diesel -o entities/
    """
    with handle_cli_error():
        project_path = Path(directory)
        output.info(f"🔍 Analyzing project: {project_path.absolute()}")

        # Detect project type
        project_type = framework or detect_project_type(project_path)
        output.info(f"📋 Detected project type: {project_type}")

        if project_type == "unknown":
            output.warning("Could not detect project type. Use --framework to specify explicitly.")
            output.info("Supported frameworks: django, python, rust, prisma, typescript, sql")
            raise click.ClickException("Unknown project type")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if preview:
            output.info("🔍 Preview mode: no files will be written")

        # Process the project (preview mode will just list files)
        generated_files = process_project(project_path, project_type, output_path, preview)

        if not preview:
            output.success(f"Successfully processed {project_type} project")
            output.info(f"Generated {len(generated_files)} YAML file(s) to {output_path}")
        else:
            output.info("Preview complete")
