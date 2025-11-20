"""Common logic for all reverse engineering commands."""

import fnmatch
from pathlib import Path
from typing import Any, Protocol

import click
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Imports are done at function level to avoid circular import issues


class ParserProtocol(Protocol):
    """Protocol for parsers used in reverse engineering."""

    def parse_file(self, file_path: str) -> Any:
        """Parse a file and return parsed result."""
        ...


class MapperProtocol(Protocol):
    """Protocol for mappers that convert parsed results to SpecQL."""

    def map_to_specql(self, parsed_result: Any) -> str:
        """Map parsed result to SpecQL YAML string."""
        ...


class ReverseEngineeringCLI:
    """Common logic for all reverse engineering commands."""

    @staticmethod
    def discover_source_files(
        input_path: str, language: str, exclude_patterns: list[str] | None = None
    ) -> list[Path]:
        """Discover all source files in a directory"""
        path = Path(input_path)

        if path.is_file():
            return [path]

        # Directory: recursively find source files
        extension_map = {
            "rust": ["*.rs"],
            "typescript": ["*.ts", "*.tsx", "*.prisma"],
            "python": ["*.py"],
            "java": ["*.java"],
            "sql": ["*.sql"],
        }

        patterns = extension_map.get(language, ["*.*"])
        files = []

        for pattern in patterns:
            files.extend(path.rglob(pattern))

        # Apply exclusions
        if exclude_patterns:
            files = [
                f
                for f in files
                if not any(fnmatch.fnmatch(str(f), pat) for pat in exclude_patterns)
            ]

        return files

    @staticmethod
    def process_project(
        input_path: str,
        framework: str | None,
        with_patterns: bool,
        output_dir: str,
        exclude: list[str] | None = None,
        preview: bool = False,
        language: str = "auto",
        use_cache: bool = True,
        incremental: bool = False,
        validate_output: bool = False,
        keep_invalid: bool = True,
        fail_fast: bool = False,
        verbose: bool = False,
    ):
        """Process an entire project directory"""

        # For now, use simple framework detection
        if not framework or framework == "auto":
            # Simple detection based on file extensions in the directory
            from pathlib import Path

            path = Path(input_path)
            if any(path.rglob("*.rs")):
                framework = "rust"
            elif any(path.rglob("*.py")):
                framework = "python"
            elif any(path.rglob("*.sql")):
                framework = "sql"
            else:
                click.echo("❌ Could not detect framework from project structure")
                return

        # Simple language mapping
        language_map = {
            "diesel": "rust",
            "seaorm": "rust",
            "sqlalchemy": "python",
            "django": "python",
            "sql": "sql",
            "rust": "rust",
            "python": "python",
        }

        detected_language = language_map.get(framework, framework)

        # Discover source files
        source_files = ReverseEngineeringCLI.discover_source_files(
            input_path,
            detected_language,
            exclude,
        )

        click.echo(f"📂 Discovered {len(source_files)} source files")

        # Filter for incremental mode
        tracker = None
        if incremental:
            from .incremental_tracker import IncrementalTracker

            tracker = IncrementalTracker(output_dir)
            changed_files = tracker.get_changed_files(source_files)

            unchanged_count = len(source_files) - len(changed_files)
            click.echo(f"📂 Found {len(changed_files)} changed files ({unchanged_count} unchanged)")

            source_files = changed_files

        # Process each file
        results = []
        from .error_handler import ErrorHandler

        for file_path in source_files:
            try:
                result = ReverseEngineeringCLI.process_single_file(
                    file_path,
                    framework,
                    with_patterns,
                    output_dir,
                    preview,
                    use_cache,
                    validate_output,
                    keep_invalid,
                )
                results.append(result)

                if tracker:
                    tracker.mark_processed(file_path, result)

            except Exception as e:
                from .error_handler import MappingError, ParsingError, ValidationError

                # Convert to appropriate error type
                if "parsing" in str(e).lower():
                    error = ParsingError(str(e))
                elif "mapping" in str(e).lower():
                    error = MappingError(str(e))
                elif "validation" in str(e).lower():
                    error = ValidationError(str(e))
                else:
                    error = e

                should_continue = ErrorHandler.handle_error(
                    error, str(file_path), fail_fast, verbose
                )
                results.append({"file": str(file_path), "status": "error", "error": str(e)})

                if not should_continue:
                    break

        click.echo(f"\n✓ Processed {len(results)} files")
        return results

    @staticmethod
    def process_single_file(
        file_path: Path,
        framework: str,
        with_patterns: bool,
        output_dir: str,
        preview: bool,
        use_cache: bool = True,
        validate_output: bool = False,
        keep_invalid: bool = True,
    ):
        """Process a single file with optional pattern detection, caching, and validation support"""
        from .cache_manager import CacheManager

        cache_manager = CacheManager()
        options = {
            "framework": framework,
            "with_patterns": with_patterns,
            "preview": preview,
            "validate_output": validate_output,
        }

        # Check cache
        if use_cache:
            cached_result = cache_manager.get_cached(str(file_path), options)
            if cached_result:
                click.echo(f"  ⚡ Using cached result for {file_path.name}")
                return cached_result["result"]

        click.echo(f"🔄 Processing {file_path}...")

        try:
            # Import here to avoid circular imports
            if framework == "python":
                # This would need to be adapted to work with the new interface
                # For now, return a placeholder
                result = {"file": str(file_path), "status": "processed"}
            elif framework == "sql":
                # Similar adaptation needed
                result = {"file": str(file_path), "status": "processed"}
            else:
                click.echo(f"⚠️ Framework {framework} processing not yet implemented")
                result = {"file": str(file_path), "status": "skipped"}

            # Validate output if requested
            if validate_output and result.get("status") == "processed":
                is_valid, errors = ReverseEngineeringCLI.validate_output(output_dir, file_path)
                if not is_valid:
                    click.echo(f"  ✗ Validation failed for {file_path.name}:")
                    for error in errors:
                        click.echo(f"    - {error}")
                    if not keep_invalid:
                        # Remove invalid output
                        pass  # Would need to implement file cleanup
                    result["validation_errors"] = str(errors)

            # Cache result
            if use_cache:
                cache_manager.set_cached(str(file_path), options, result)

            return result

        except Exception as e:
            click.echo(f"❌ Failed to process {file_path}: {e}")
            result = {"file": str(file_path), "status": "error", "error": str(e)}

            # Don't cache errors
            return result

        except Exception as e:
            click.echo(f"❌ Failed to process {file_path}: {e}")
            result = {"file": str(file_path), "status": "error", "error": str(e)}

            # Don't cache errors
            return result

    @staticmethod
    def process_project_with_progress(input_path: str, **kwargs):
        """Process project with progress bar"""

        source_files = ReverseEngineeringCLI.discover_source_files(
            kwargs.get("input_path", input_path),
            kwargs.get("language", "auto"),
            kwargs.get("exclude"),
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(
                f"Processing {len(source_files)} files...", total=len(source_files)
            )

            results = []
            for file_path in source_files:
                progress.update(task, description=f"Processing {file_path.name}...")
                result = ReverseEngineeringCLI.process_single_file(
                    file_path,
                    kwargs.get("framework", "auto"),
                    kwargs.get("with_patterns", False),
                    kwargs.get("output_dir", "."),
                    kwargs.get("preview", False),
                    kwargs.get("use_cache", True),
                )
                results.append(result)
                progress.advance(task)

        return results

    @staticmethod
    def validate_output(output_dir: str, source_file: Path) -> tuple[bool, list]:
        """Validate generated SpecQL YAML"""
        from core.specql_parser import SpecQLParser

        # Find the corresponding output file
        entity_name = source_file.stem  # Assume filename matches entity name
        output_path = Path(output_dir) / f"{entity_name}.yaml"

        if not output_path.exists():
            return False, [f"Output file {output_path} not found"]

        try:
            parser = SpecQLParser()
            content = output_path.read_text()
            entity_def = parser.parse(content)

            errors = []

            # Basic validation
            if not entity_def.name:
                errors.append("Missing entity name")

            if not entity_def.schema:
                errors.append("No schema specified")

            # Field validation
            for field_name, field in entity_def.fields.items():
                if not field.type_name:
                    errors.append(f"Field {field_name} missing type")

            if errors:
                return False, errors

            return True, []

        except Exception as e:
            return False, [f"Validation error: {e}"]

    @staticmethod
    def process_files(
        input_files: list[str],
        output_dir: str | None,
        parser: ParserProtocol,
        mapper: MapperProtocol,
        preview: bool = False,
    ) -> None:
        """Generic file processing pipeline for reverse engineering."""
        for file_path in input_files:
            click.echo(f"🔄 Processing {file_path}...")

            try:
                # Parse the file
                ast_result = parser.parse_file(file_path)

                # Map to SpecQL YAML
                specql_yaml = mapper.map_to_specql(ast_result)

                if preview:
                    click.echo(specql_yaml)
                else:
                    # Determine output path
                    if output_dir:
                        output_path = Path(output_dir) / f"{ast_result.entity_name}.yaml"
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        # Default to current directory
                        output_path = Path(f"{ast_result.entity_name}.yaml")

                    # Write the YAML file
                    output_path.write_text(specql_yaml)
                    click.echo(f"✅ Generated {output_path}")

            except Exception as e:
                click.echo(f"❌ Failed to process {file_path}: {e}")
                continue
