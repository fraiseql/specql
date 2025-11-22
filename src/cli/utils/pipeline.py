"""
Shared pipeline utilities for CLI workflow commands.

Provides common orchestration logic for multi-phase operations like
migrate, sync, and other workflow commands.
"""

import os
from collections.abc import Callable
from pathlib import Path

from click.testing import CliRunner

from cli.utils.output import output


class PipelineOrchestrator:
    """Orchestrates multi-phase CLI operations with consistent error handling and progress reporting."""

    def __init__(self):
        self.runner = CliRunner()

    def execute_reverse_phase(
        self,
        files: list[Path],
        reverse_from: str,
        output_dir: Path,
        continue_on_error: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[Path]:
        """Execute reverse engineering phase."""
        from cli.main import app

        if progress_callback:
            progress_callback("🔄 Phase 1: Reverse engineering")

        reversed_files = []

        for file_path in files:
            try:
                # Use CliRunner to call the reverse command
                runner = CliRunner()
                result = runner.invoke(
                    app, ["reverse", reverse_from, str(file_path), "-o", str(output_dir)]
                )

                if result.exit_code == 0:
                    # Find generated YAML files (search recursively, excluding project.yaml and registry)
                    yaml_files = list(output_dir.glob("**/*.yaml"))
                    # Filter out project.yaml and registry files
                    entity_files = [
                        f
                        for f in yaml_files
                        if f.name != "project.yaml"
                        and "registry" not in f.parts
                        and "domain_registry" not in f.name
                    ]
                    reversed_files.extend(entity_files)
                    for yaml_file in entity_files:
                        output.info(f"  📄 {file_path.name} → {yaml_file.name}")
                else:
                    error_msg = f"Failed to reverse {file_path.name}: {result.output}"
                    if continue_on_error:
                        output.warning(f"  ⚠️  {error_msg}")
                    else:
                        output.error(f"  ❌ {error_msg}")
                        raise Exception(error_msg)

            except Exception as e:
                error_msg = f"Error reversing {file_path.name}: {str(e)}"
                if continue_on_error:
                    output.warning(f"  ⚠️  {error_msg}")
                else:
                    output.error(f"  ❌ {error_msg}")
                    raise

        return reversed_files

    def execute_validate_phase(
        self,
        yaml_files: list[Path],
        strict: bool = False,
        continue_on_error: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[list[Path], list[str]]:
        """Execute validation phase."""
        from cli.main import app

        if progress_callback:
            progress_callback("✅ Phase 2: Validation")

        valid_files = []
        errors = []

        for yaml_file in yaml_files:
            try:
                runner = CliRunner()
                args = ["validate", str(yaml_file)]
                if strict:
                    args.append("--strict")
                result = runner.invoke(app, args)

                if result.exit_code == 0:
                    valid_files.append(yaml_file)
                else:
                    error_msg = f"{yaml_file.name}: Validation failed"
                    errors.append(error_msg)
                    if continue_on_error:
                        output.warning(f"  ⚠️  {error_msg}")
                    else:
                        output.error(f"  ❌ {error_msg}")

            except Exception as e:
                error_msg = f"{yaml_file.name}: {str(e)}"
                errors.append(error_msg)
                if continue_on_error:
                    output.warning(f"  ⚠️  {error_msg}")
                else:
                    output.error(f"  ❌ {error_msg}")

        if not errors:
            output.success("✅ Validation passed")
        elif continue_on_error:
            output.warning(f"⚠️  Validation completed with {len(errors)} warning(s)")
        else:
            output.error(f"❌ Validation failed with {len(errors)} error(s)")

        return valid_files, errors

    def execute_generate_phase(
        self,
        yaml_files: list[Path],
        output_dir: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[Path]:
        """Execute code generation phase."""
        from cli.main import app

        if progress_callback:
            progress_callback("🔧 Phase 3: Code generation")

        generated_files = []
        old_cwd = os.getcwd()

        try:
            # Change to output directory so generate command creates files there
            os.chdir(output_dir)

            for yaml_file in yaml_files:
                try:
                    runner = CliRunner()
                    result = runner.invoke(app, ["generate", str(yaml_file)])

                    if result.exit_code == 0:
                        # Find generated files recursively
                        sql_files = list(output_dir.glob("**/*.sql"))
                        gql_files = list(output_dir.glob("**/*.graphql"))

                        # Remove duplicates and filter to only files created in this run
                        all_files = list(set(sql_files + gql_files))
                        generated_files.extend(all_files)

                        for gen_file in all_files:
                            rel_path = gen_file.relative_to(output_dir)
                            output.info(f"  📝 {yaml_file.name} → {rel_path}")
                    else:
                        output.error(
                            f"  ❌ Failed to generate from {yaml_file.name}: {result.output}"
                        )

                except Exception as e:
                    output.error(f"  ❌ Error generating from {yaml_file.name}: {str(e)}")

        finally:
            os.chdir(old_cwd)

        return generated_files

    def run_pipeline(
        self,
        files: list[Path],
        reverse_from: str | None = None,
        output_dir: Path | None = None,
        validate_only: bool = False,
        generate_only: bool = False,
        continue_on_error: bool = False,
        strict_validation: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> dict:
        """
        Run the complete migration pipeline.

        Returns:
            dict with 'success', 'generated_files', 'errors', etc.
        """
        result = {"success": False, "generated_files": [], "errors": [], "phases_completed": []}

        try:
            # Set defaults
            if output_dir is None:
                output_dir = Path("generated")
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Phase 1: Reverse engineering (if not generate-only)
            yaml_files = []
            if not generate_only:
                if progress_callback:
                    progress_callback("🔄 Phase 1: Reverse engineering")

                entities_dir = output_dir / "entities"
                entities_dir.mkdir(exist_ok=True)

                if reverse_from:
                    yaml_files = self.execute_reverse_phase(
                        files,
                        reverse_from,
                        entities_dir,
                        continue_on_error,
                        None,  # Don't show progress again
                    )
                else:
                    # Assume files are already YAML
                    yaml_files = files
                    output.info(f"  ✅ Using existing YAML files: {len(yaml_files)}")

                result["phases_completed"].append("reverse")
            else:
                yaml_files = files
                output.info("⏭️  Skipping reverse phase (--generate-only)")

            # Phase 2: Validation
            valid_files, validation_errors = self.execute_validate_phase(
                yaml_files, strict_validation, continue_on_error, progress_callback
            )
            result["phases_completed"].append("validate")

            if validation_errors and not continue_on_error:
                result["errors"].extend(validation_errors)
                return result

            if validate_only:
                output.info("🛑 Stopping after validation (--validate-only)")
                result["phases_completed"].append("validate_only")
                result["success"] = True
                return result

            # Phase 3: Generation
            output_dir_gen = output_dir / "output"
            output_dir_gen.mkdir(exist_ok=True)

            generated_files = self.execute_generate_phase(
                valid_files, output_dir_gen, progress_callback
            )
            result["phases_completed"].append("generate")
            result["generated_files"] = generated_files

            output.success("✅ Migration pipeline completed successfully")
            output.info(f"📁 Generated {len(generated_files)} file(s) to {output_dir}")
            result["success"] = True

        except Exception as e:
            result["errors"].append(str(e))
            output.error(f"❌ Pipeline failed: {str(e)}")

        return result
