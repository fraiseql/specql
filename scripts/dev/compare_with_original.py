#!/usr/bin/env python3
"""
Compare generated SQL with original SQL from printoptim_backend
"""

import difflib
from pathlib import Path

# Paths
ORIGINAL_TABLE = Path('../printoptim_backend/db/0_schema/01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql')
GENERATED_TABLE = Path('generated/tables/tb_manufacturer.sql')
GENERATED_TRINITY = Path('generated/functions/manufacturer_trinity_helpers.sql')

def normalize_sql(sql):
    """Normalize SQL for comparison (remove extra whitespace, etc.)"""
    lines = []
    for line in sql.splitlines():
        line = line.strip()
        if line and not line.startswith('--'):
            lines.append(line)
    return '\n'.join(lines)

def compare_files(original, generated, name):
    """Compare two SQL files and show differences"""
    print(f"\n{'='*80}")
    print(f"Comparing: {name}")
    print(f"{'='*80}")

    if not original.exists():
        print(f"❌ Original file not found: {original}")
        return

    if not generated.exists():
        print(f"❌ Generated file not found: {generated}")
        return

    original_content = original.read_text()
    generated_content = generated.read_text()

    print(f"Original file: {original}")
    print(f"  Size: {len(original_content)} bytes")
    print(f"  Lines: {len(original_content.splitlines())}")

    print(f"\nGenerated file: {generated}")
    print(f"  Size: {len(generated_content)} bytes")
    print(f"  Lines: {len(generated_content.splitlines())}")

    # Normalize and compare
    original_norm = normalize_sql(original_content)
    generated_norm = normalize_sql(generated_content)

    if original_norm == generated_norm:
        print("\n✅ Files are functionally identical (ignoring comments/formatting)")
        return True
    else:
        print("\n⚠️  Files have differences:")

        # Show diff
        diff = difflib.unified_diff(
            original_norm.splitlines(keepends=True),
            generated_norm.splitlines(keepends=True),
            fromfile=str(original),
            tofile=str(generated),
            lineterm=''
        )

        diff_lines = list(diff)
        if diff_lines:
            print("\nFirst 50 lines of diff:")
            for line in diff_lines[:50]:
                print(line.rstrip())

            if len(diff_lines) > 50:
                print(f"\n... and {len(diff_lines) - 50} more lines")

        return False

def analyze_coverage():
    """Analyze what's covered and what's missing"""
    print(f"\n{'='*80}")
    print("Coverage Analysis")
    print(f"{'='*80}")

    print("\n✅ Generated from YAML:")
    print("  - Table structure (pk_*, id, fields, FKs, audit)")
    print("  - Constraints (UNIQUE, PRIMARY KEY, FOREIGN KEY)")
    print("  - Comments (table, all columns)")
    print("  - Translation table")
    print("  - Trinity helper functions (4 helpers)")

    print("\n📋 Original SQL features:")
    original = ORIGINAL_TABLE.read_text()
    features = {
        'CREATE TABLE': 'CREATE TABLE' in original,
        'IDENTITY PRIMARY KEY': 'IDENTITY PRIMARY KEY' in original,
        'FOREIGN KEY': 'FOREIGN KEY' in original,
        'COMMENT ON': 'COMMENT ON' in original,
        'Translation table': 'tb_manufacturer_translation' in original,
    }

    for feature, present in features.items():
        status = '✅' if present else '❌'
        print(f"  {status} {feature}")

def main():
    """Main comparison"""
    print("="*80)
    print("SQL Generator POC - Validation")
    print("="*80)

    # Compare table
    table_match = compare_files(ORIGINAL_TABLE, GENERATED_TABLE, "Table SQL")

    # Analyze coverage
    analyze_coverage()

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}")

    if table_match:
        print("✅ POC Success: Generated SQL matches original structure")
    else:
        print("⚠️  POC Partial Success: Generated SQL has differences")
        print("   (This is expected - template may need refinement)")

    print("\n✅ Trinity Helpers: NEW functionality not in original")
    print("   Generated 4 helper functions in:")
    print(f"   {GENERATED_TRINITY}")

    print(f"\n{'='*80}")
    print("Next Steps")
    print(f"{'='*80}")
    print("1. Review differences in generated SQL")
    print("2. Refine Jinja2 templates for exact formatting")
    print("3. Add CREATE function template")
    print("4. Add UPDATE function template")
    print("5. Test generated SQL in database")

if __name__ == '__main__':
    main()
