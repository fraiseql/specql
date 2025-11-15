import click
from pathlib import Path
from typing import List
import yaml

from src.reverse_engineering.python_ast_parser import PythonASTParser
from src.reverse_engineering.universal_ast_mapper import UniversalASTMapper

@click.command()
@click.argument('python_files', nargs=-1, type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), default='entities/',
              help='Output directory for SpecQL YAML files')
@click.option('--discover-patterns', is_flag=True,
              help='Discover and save patterns to pattern library')
@click.option('--dry-run', is_flag=True,
              help='Show what would be generated without writing files')
def reverse_python(python_files, output_dir, discover_patterns, dry_run):
    """
    Reverse engineer Python code to SpecQL YAML

    Examples:
        # Single file
        specql reverse python src/models/contact.py

        # Multiple files
        specql reverse python src/models/*.py

        # With pattern discovery
        specql reverse python src/models/*.py --discover-patterns

        # Dry run
        specql reverse python src/models/contact.py --dry-run
    """
    click.echo("🐍 Python → SpecQL Reverse Engineering\n")

    parser = PythonASTParser()
    mapper = UniversalASTMapper()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []

    for file_path in python_files:
        click.echo(f"📄 Processing: {file_path}")

        try:
            # Read Python file
            source_code = Path(file_path).read_text()

            # Parse to ParsedEntity
            entity = parser.parse_entity(source_code, file_path)

            # Map to SpecQL
            specql_dict = mapper.map_entity_to_specql(entity)

            # Generate output file name
            output_file = output_path / f"{entity.entity_name.lower()}.yaml"

            if dry_run:
                click.echo(f"  Would write: {output_file}")
                click.echo(f"  Entity: {entity.entity_name}")
                click.echo(f"  Fields: {len(entity.fields)}")
                click.echo(f"  Actions: {len(entity.methods)}")

                if discover_patterns:
                    patterns = parser.detect_patterns(entity)
                    click.echo(f"  Patterns: {', '.join(patterns)}")
            else:
                # Write YAML file
                with open(output_file, 'w') as f:
                    yaml.dump(specql_dict, f, default_flow_style=False, sort_keys=False)

                click.echo(f"  ✅ Written: {output_file}")

                # Pattern discovery
                if discover_patterns:
                    patterns = parser.detect_patterns(entity)
                    if patterns:
                        click.echo(f"  🔍 Patterns detected: {', '.join(patterns)}")
                        _save_patterns_to_library(entity, patterns)

            results.append({
                'file': file_path,
                'entity': entity.entity_name,
                'output': str(output_file),
                'success': True
            })

        except Exception as e:
            click.echo(f"  ❌ Error: {e}", err=True)
            results.append({
                'file': file_path,
                'entity': None,
                'output': None,
                'success': False,
                'error': str(e)
            })

    # Summary
    click.echo("\n📊 Summary:")
    successful = sum(1 for r in results if r['success'])
    click.echo(f"  ✅ Successful: {successful}/{len(results)}")

    if not dry_run:
        click.echo(f"  📁 Output directory: {output_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review generated YAML: ls {output_dir}")
        click.echo(f"  2. Validate: specql validate {output_dir}/*.yaml")
        click.echo(f"  3. Generate schema: specql generate {output_dir}/*.yaml")

def _save_patterns_to_library(entity, patterns: List[str]):
    """Save detected patterns to pattern library"""
    from src.pattern_library.api import PatternLibraryAPI

    api = PatternLibraryAPI()

    for pattern_name in patterns:
        # Create pattern from entity
        pattern_data = {
            'name': f"{entity.entity_name.lower()}_{pattern_name}",
            'type': 'entity_pattern',
            'description': f"{pattern_name} pattern detected in {entity.entity_name}",
            'source_language': 'python',
            'fields': [
                {'name': f.field_name, 'type': f.field_type}
                for f in entity.fields
            ],
        }

        try:
            api.create_pattern(pattern_data)
        except Exception:
            # Pattern might already exist
            pass