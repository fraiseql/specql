#!/usr/bin/env python3
"""
SpecQL SQL Generation CLI
Generates complete PostgreSQL schema from YAML entity definitions
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition
from src.generators.schema_orchestrator import SchemaOrchestrator


class SpecQLGenerator:
    """Generate complete SQL from SpecQL YAML entity definitions"""

    def __init__(self, output_dir: str = "generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_entity_from_yaml(self, yaml_file: Path) -> Entity:
        """Load entity definition from YAML file and convert to SpecQL Entity"""
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        # Parse entity name, schema, description
        entity_info = data.get("entity")
        if isinstance(entity_info, dict):
            # Format: entity: {name: ..., schema: ..., description: ...}
            entity_name = entity_info.get("name")
            schema = entity_info.get("schema", "public")
            description = entity_info.get("description", "")
        else:
            # Format: entity: Name, schema: ..., description: ...
            entity_name = entity_info
            schema = data.get("schema", "public")
            description = data.get("description", "")

        if not entity_name:
            raise ValueError(f"Entity name not found in YAML file {yaml_file}")

        # Convert fields with type annotations
        fields = {}
        for field_name, type_annotation in data.get("fields", {}).items():
            field_def = self._parse_field_type(field_name, type_annotation)
            fields[field_name] = field_def

        # Convert actions
        actions = []
        for action_data in data.get("actions", []):
            steps = []
            for step_item in action_data.get("steps", []):
                # Handle different step formats
                if isinstance(step_item, str):
                    # Simple step like "validate: status = 'lead'"
                    step_type, expression = step_item.split(":", 1)
                    step = ActionStep(
                        type=step_type.strip(), expression=expression.strip()
                    )
                elif isinstance(step_item, dict):
                    # Complex step with additional properties
                    step = ActionStep(
                        type=step_item.get("type") or list(step_item.keys())[0],
                        expression=step_item.get("validate")
                        or step_item.get("expression"),
                        entity=step_item.get("entity"),
                        fields=step_item.get("fields"),
                    )
                else:
                    continue

                steps.append(step)

            actions.append(
                Action(
                    name=action_data["name"],
                    steps=steps,
                )
            )

        return Entity(
            name=entity_name,
            schema=schema,
            description=description,
            fields=fields,
            actions=actions,
        )

    def _parse_field_type(
        self, field_name: str, type_annotation: str
    ) -> FieldDefinition:
        """Parse SpecQL type annotation into FieldDefinition"""
        type_annotation = type_annotation.strip()

        # Handle ref(Type) syntax
        if type_annotation.startswith("ref(") and type_annotation.endswith(")"):
            ref_entity = type_annotation[4:-1]
            return FieldDefinition(
                name=field_name,
                type_name="ref",
                nullable=True,  # refs are typically nullable
                reference_entity=ref_entity,
            )

        # Handle enum(value1, value2, ...) syntax
        elif type_annotation.startswith("enum(") and type_annotation.endswith(")"):
            enum_values = [v.strip() for v in type_annotation[5:-1].split(",")]
            return FieldDefinition(
                name=field_name, type_name="enum", nullable=True, values=enum_values
            )

        # Simple types
        else:
            return FieldDefinition(
                name=field_name, type_name=type_annotation, nullable=True
            )

    def generate_entity_sql(self, entity: Entity) -> str:
        """Generate complete SQL for an entity using SchemaOrchestrator"""
        orchestrator = SchemaOrchestrator()
        return orchestrator.generate_complete_schema(entity)

    def generate_single_entity(self, yaml_file: Path) -> None:
        """Generate SQL for a single entity"""
        print(f"\n{'=' * 80}")
        print(f"Processing: {yaml_file.name}")
        print(f"{'=' * 80}")

        try:
            # Load and convert entity
            entity = self.load_entity_from_yaml(yaml_file)
            print(f"Entity: {entity.schema}.{entity.name}")
            print(f"Description: {entity.description}")
            print(f"Fields: {len(entity.fields)}")
            print(f"Actions: {len(entity.actions)}")

            # Generate complete SQL
            print("\nGenerating complete SQL schema...")
            sql = self.generate_entity_sql(entity)

            # Write output
            output_file = self.output_dir / f"{entity.schema}_{entity.name}.sql"
            output_file.write_text(sql)

            print(f"✓ Generated: {output_file}")
            print(f"  Size: {len(sql)} bytes")
            print(f"  Lines: {len(sql.splitlines())}")

        except Exception as e:
            print(f"❌ Error processing {yaml_file.name}: {e}")
            import traceback

            traceback.print_exc()

    def generate_all_entities(self, entities_dir: Path) -> None:
        """Generate SQL for all entities in directory"""
        yaml_files = sorted(entities_dir.glob("*.yaml"))

        if not yaml_files:
            print(f"❌ No YAML files found in {entities_dir}")
            return

        print(f"\n{'=' * 80}")
        print("SpecQL SQL Generator")
        print(f"{'=' * 80}")
        print(f"Entities directory: {entities_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Found {len(yaml_files)} entity definition(s)")

        for yaml_file in yaml_files:
            self.generate_single_entity(yaml_file)

        print(f"\n{'=' * 80}")
        print("✅ Generation complete!")
        print(f"{'=' * 80}")
        print(f"Output: {self.output_dir}")
        print("\nNext steps:")
        print("  1. Review generated SQL files")
        print("  2. Test in PostgreSQL database")
        print("  3. Apply migrations as needed")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SpecQL SQL Generator - Generate PostgreSQL schema from YAML entity definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate SQL for all entities
  python generate_sql.py

  # Generate SQL for specific entity
  python generate_sql.py entities/contact.yaml

  # Generate to custom output directory
  python generate_sql.py --output /tmp/sql
        """,
    )

    parser.add_argument(
        "entity_file", nargs="?", help="Specific YAML entity file to process (optional)"
    )

    parser.add_argument(
        "--entities-dir",
        default="entities",
        help="Directory containing YAML entity definitions (default: entities)",
    )

    parser.add_argument(
        "--output",
        default="generated",
        help="Output directory for generated SQL files (default: generated)",
    )

    args = parser.parse_args()

    generator = SpecQLGenerator(output_dir=args.output)

    if args.entity_file:
        # Generate single entity
        yaml_file = Path(args.entity_file)
        if not yaml_file.exists():
            print(f"❌ Entity file not found: {yaml_file}")
            sys.exit(1)
        generator.generate_single_entity(yaml_file)
    else:
        # Generate all entities
        entities_dir = Path(args.entities_dir)
        if not entities_dir.exists():
            print(f"❌ Entities directory not found: {entities_dir}")
            sys.exit(1)
        generator.generate_all_entities(entities_dir)


if __name__ == "__main__":
    main()
