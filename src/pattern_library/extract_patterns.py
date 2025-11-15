"""
Extract patterns from existing step compilers for pattern library migration.

This script analyzes all step compilers to identify the 35 primitive patterns
that need to be converted to pattern library templates.
"""

import re
from pathlib import Path
from typing import Dict, List


def find_all_compilers() -> List[Path]:
    """Find all step compiler files"""
    compilers_dir = Path("src/generators/actions/step_compilers")
    return list(compilers_dir.glob("*.py"))


def extract_pattern_info(compiler_file: Path) -> Dict[str, str]:
    """Extract pattern information from a compiler file"""
    with open(compiler_file) as f:
        content = f.read()

    # Extract class name
    class_match = re.search(r'class (\w+Compiler)', content)
    if not class_match:
        return {}

    class_name = class_match.group(1)

    # Extract step type from docstring or comments
    step_type = None

    # Look for step type in docstring examples
    examples = re.findall(r"Example SpecQL:\s*\n\s*-\s*(\w+):", content, re.MULTILINE)
    if examples:
        step_type = examples[0]

    # Look for step type in comments
    if not step_type:
        type_matches = re.findall(r"step type\s*['\"]?(\w+)['\"]?", content)
        if type_matches:
            step_type = type_matches[0]

    # Look for step.type checks
    if not step_type:
        type_checks = re.findall(r"step\.type\s*!=?\s*['\"]?(\w+)['\"]?", content)
        if type_checks:
            step_type = type_checks[0]

    # Extract description from docstring
    description = ""
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if docstring_match:
        docstring = docstring_match.group(1).strip()
        # Take first line as description
        description = docstring.split('\n')[0].strip()

    return {
        'class_name': class_name,
        'step_type': step_type,
        'description': description,
        'file': str(compiler_file)
    }


def analyze_all_compilers() -> List[Dict[str, str]]:
    """Analyze all compilers and extract pattern information"""
    compilers = find_all_compilers()
    patterns = []

    for compiler_file in compilers:
        if compiler_file.name == '__init__.py' or compiler_file.name == 'base.py':
            continue

        pattern_info = extract_pattern_info(compiler_file)
        if pattern_info:
            patterns.append(pattern_info)

    return patterns


def categorize_patterns(patterns: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize patterns by type"""
    categories = {
        'primitive': [],
        'control_flow': [],
        'query': [],
        'data_transform': [],
        'database_ops': [],
        'other': []
    }

    # Known categorizations
    category_map = {
        'declare': 'primitive',
        'assign': 'primitive',
        'return': 'primitive',
        'return_early': 'primitive',
        'call': 'primitive',
        'call_function': 'primitive',
        'call_service': 'primitive',
        'if': 'control_flow',
        'foreach': 'control_flow',
        'for_query': 'control_flow',
        'while': 'control_flow',
        'switch': 'control_flow',
        'query': 'query',
        'subquery': 'query',
        'cte': 'query',
        'aggregate': 'data_transform',
        'json_build': 'data_transform',
        'insert': 'database_ops',
        'update': 'database_ops',
        'delete': 'database_ops',
        'partial_update': 'database_ops',
        'duplicate_check': 'database_ops',
        'validate': 'database_ops',
        'refresh_table_view': 'database_ops',
        'notify': 'database_ops',
        'exception_handling': 'control_flow'
    }

    for pattern in patterns:
        step_type = pattern['step_type']
        category = category_map.get(step_type, 'other')
        categories[category].append(pattern)

    return categories


def print_pattern_analysis():
    """Print comprehensive pattern analysis"""
    patterns = analyze_all_compilers()
    categories = categorize_patterns(patterns)

    print("🔍 PATTERN LIBRARY MIGRATION ANALYSIS")
    print("=" * 50)
    print(f"Total compilers found: {len(patterns)}")
    print()

    total_patterns = 0
    for category, category_patterns in categories.items():
        if category_patterns:
            print(f"📁 {category.upper()} ({len(category_patterns)} patterns)")
            for pattern in category_patterns:
                print(f"  • {pattern['step_type']} - {pattern['description']}")
                total_patterns += 1
            print()

    print(f"🎯 TOTAL PATTERNS TO IMPLEMENT: {total_patterns}")
    print()

    # Check what's already implemented
    existing_patterns = ['declare', 'assign', 'if', 'query', 'return']
    remaining = total_patterns - len(existing_patterns)
    print(f"✅ ALREADY IMPLEMENTED: {len(existing_patterns)} patterns")
    print(f"⏳ REMAINING TO IMPLEMENT: {remaining} patterns")


if __name__ == "__main__":
    print_pattern_analysis()