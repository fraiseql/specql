"""
Reverse project subcommand - Auto-detect and process entire projects.
"""

from pathlib import Path

import click

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
    return "unknown"


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

        if preview:
            output.info("🔍 Preview mode: no files will be written")
            return

        # TODO: Integrate with existing project reverse engineering
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Simulate processing based on project type
        if project_type == "django":
            output.info("🐍 Processing Django models...")
            # Look for models.py files
            models_files = list(project_path.rglob("models.py"))
            output.info(f"  📄 Found {len(models_files)} models.py files")

        elif project_type == "rust":
            output.info("🦀 Processing Rust schemas...")
            # Look for schema.rs files
            schema_files = list(project_path.rglob("schema.rs"))
            output.info(f"  📄 Found {len(schema_files)} schema.rs files")

        elif project_type in ["prisma", "typescript"]:
            output.info("📘 Processing TypeScript schemas...")
            # Look for schema files
            schema_files = list(project_path.rglob("*.prisma")) + list(project_path.rglob("*.ts"))
            output.info(f"  📄 Found {len(schema_files)} schema files")

        else:
            output.info("🔍 Processing generic project...")
            # Generic file discovery
            code_files = (
                list(project_path.rglob("*.py"))
                + list(project_path.rglob("*.rs"))
                + list(project_path.rglob("*.ts"))
            )
            output.info(f"  📄 Found {len(code_files)} potential code files")

        output.success(f"Phase 3 reverse project command analyzed {project_type} project")
        output.warning("Full project reverse engineering integration pending in Phase 4")
