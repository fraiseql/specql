"""Common logic for all reverse engineering commands."""

from pathlib import Path
from typing import Any, Protocol
import click


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
