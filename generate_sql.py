#!/usr/bin/env python3
"""
SQL Generation Engine - Trinity Pattern
Generates PostgreSQL tables and functions from YAML entity definitions
"""

from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader
import sys


class SQLGenerator:
    """Generate SQL from YAML entity definitions using Jinja2 templates"""

    def __init__(self, templates_dir='templates', entities_dir='entities', output_dir='generated'):
        self.templates_dir = Path(templates_dir)
        self.entities_dir = Path(entities_dir)
        self.output_dir = Path(output_dir)

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Ensure output directories exist
        (self.output_dir / 'tables').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'functions').mkdir(parents=True, exist_ok=True)

    def load_entity(self, entity_file):
        """Load entity definition from YAML file"""
        with open(entity_file, 'r') as f:
            data = yaml.safe_load(f)
        return data['entity']

    def generate_table(self, entity):
        """Generate CREATE TABLE statement from template"""
        template = self.env.get_template('table.sql.j2')
        return template.render(entity=entity)

    def generate_trinity_helpers(self, entity):
        """Generate core.*_pk(), core.*_id() helper functions"""
        if not entity.get('trinity_helpers', {}).get('generate'):
            return None

        template = self.env.get_template('trinity_helpers.sql.j2')
        return template.render(entity=entity)

    def generate_entity(self, entity_file):
        """Generate all SQL for a single entity"""
        print(f"\n{'='*80}")
        print(f"Processing: {entity_file.name}")
        print(f"{'='*80}")

        # Load entity definition
        entity = self.load_entity(entity_file)
        entity_name = entity['name']

        print(f"Entity: {entity['schema']}.{entity_name}")
        print(f"Description: {entity['description']}")

        results = {}

        # Generate table SQL
        print(f"\n[1/2] Generating table SQL...")
        table_sql = self.generate_table(entity)
        results['table'] = table_sql

        # Write table SQL
        table_file = self.output_dir / 'tables' / f'tb_{entity_name}.sql'
        table_file.write_text(table_sql)
        print(f"      ✓ Written: {table_file}")
        print(f"        Size: {len(table_sql)} bytes")
        print(f"        Lines: {len(table_sql.splitlines())}")

        # Generate trinity helpers if enabled
        if entity.get('trinity_helpers', {}).get('generate'):
            print(f"\n[2/2] Generating trinity helper functions...")
            trinity_sql = self.generate_trinity_helpers(entity)
            results['trinity'] = trinity_sql

            # Write trinity helpers
            trinity_file = self.output_dir / 'functions' / f'{entity_name}_trinity_helpers.sql'
            trinity_file.write_text(trinity_sql)
            print(f"      ✓ Written: {trinity_file}")
            print(f"        Size: {len(trinity_sql)} bytes")
            print(f"        Lines: {len(trinity_sql.splitlines())}")
        else:
            print(f"\n[2/2] Skipping trinity helpers (not enabled)")

        return results

    def generate_all(self):
        """Generate SQL for all entities in entities/ directory"""
        entity_files = sorted(self.entities_dir.glob('*.yaml'))

        if not entity_files:
            print(f"❌ No entity YAML files found in {self.entities_dir}")
            return

        print(f"\n{'='*80}")
        print(f"SQL Generator - Trinity Pattern")
        print(f"{'='*80}")
        print(f"Entities directory: {self.entities_dir}")
        print(f"Templates directory: {self.templates_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Found {len(entity_files)} entity definition(s)")

        for entity_file in entity_files:
            try:
                self.generate_entity(entity_file)
            except Exception as e:
                print(f"\n❌ Error processing {entity_file.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n{'='*80}")
        print(f"✅ Generation complete!")
        print(f"{'='*80}")
        print(f"Output:")
        print(f"  Tables: {self.output_dir / 'tables'}")
        print(f"  Functions: {self.output_dir / 'functions'}")
        print(f"\nNext steps:")
        print(f"  1. Review generated SQL in {self.output_dir}")
        print(f"  2. Compare with existing SQL")
        print(f"  3. Test in database")


def main():
    """Main entry point"""
    generator = SQLGenerator()
    generator.generate_all()


if __name__ == '__main__':
    main()
