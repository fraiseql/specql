#!/usr/bin/env python3
"""
Categorize implementation plan files based on content and naming
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Category definitions with keywords
CATEGORIES = {
    '00_master_plan': {
        'keywords': ['master', 'phase_[abcdef]', 'executive_overview', 'integration_and_testing', 'deployment_and_community'],
        'dirs': ['MASTER_PLAN'],
        'description': 'Overall project roadmap and phase breakdown'
    },
    '01_architecture': {
        'keywords': ['repository', 'ddd', 'domain_model', 'architecture', 'clean_architecture',
                    'storage', 'consolidation', 'transaction', 'aggregate', 'pattern.*architecture'],
        'description': 'Architectural decisions and patterns'
    },
    '02_infrastructure': {
        'keywords': ['postgresql', 'pgvector', 'docker', 'deployment', 'cicd', 'ci.*cd',
                    'opentofu', 'terraform', 'observability', 'grafana', 'prometheus', 'database.*setup'],
        'dirs': ['team_f_deployment'],
        'description': 'Infrastructure setup and deployment'
    },
    '03_frameworks': {
        'keywords': ['fraiseql', 'confiture', 'graphql', 'apollo', 'framework', 'integration'],
        'description': 'External framework integrations'
    },
    '04_pattern_library': {
        'keywords': ['pattern.*library', 'universal.*pattern', 'domain.*pattern', 'entity.*template',
                    'pattern.*composition', 'three.*tier', 'llm.*enhanced', 'pattern.*hierarchy'],
        'description': 'Pattern library development'
    },
    '05_code_generation': {
        'keywords': ['schema.*generation', 'action.*compilation', 'codegen', 'code.*generation',
                    'frontend.*generation', 'typescript.*types', 'sql.*expression', 'generator'],
        'description': 'Code generation features'
    },
    '06_reverse_engineering': {
        'keywords': ['reverse', 'parser', 'ai.*enhancer', 'grok', 'pattern.*discovery',
                    'algorithmic.*parser', 'sql.*parsing'],
        'description': 'Reverse engineering tools'
    },
    '07_numbering_systems': {
        'keywords': ['numbering', 'six.*digit', 'seven.*digit', 'digit.*unified', 'hierarchical.*file',
                    'identifier.*calculation', 'table.*code', 'sdsex', 'sdsexxf'],
        'description': 'Numbering and organizational systems'
    },
    '08_testing': {
        'keywords': ['test', 'testing', 'unit.*test', 'integration.*test', 'e2e', 'performance.*test',
                    'seed.*data', 'benchmark'],
        'dirs': ['testing-and-seed-generation'],
        'description': 'Testing strategies and tools'
    },
    '09_naming_conventions': {
        'keywords': ['naming.*convention', 'naming.*standard', 'entity.*naming', 'field.*naming',
                    'function.*naming', 'convention'],
        'dirs': ['naming-conventions-registry'],
        'description': 'Naming standards and conventions'
    },
    '10_phases_6_7_8': {
        'keywords': ['phase.*[678]', 'phases.*6.*7.*8', 'self.*schema', 'dual.*interface',
                    'semantic.*search', 'future.*phase'],
        'description': 'Future development phases'
    },
    'archive/completed': {
        'keywords': ['complete', 'implemented', 'done'],
        'match_status': True,
        'description': 'Successfully implemented plans'
    },
    'archive/superseded': {
        'keywords': ['old', 'deprecated', 'superseded', 'obsolete'],
        'description': 'Replaced by newer approaches'
    }
}

def categorize_file(filepath: Path) -> Tuple[str, float]:
    """
    Categorize a file based on its name and path
    Returns (category, confidence_score)
    """
    filename = filepath.name.lower()
    parent_dir = filepath.parent.name

    scores = {}

    for category, config in CATEGORIES.items():
        score = 0

        # Check directory match
        if 'dirs' in config:
            for dir_pattern in config['dirs']:
                if dir_pattern in parent_dir:
                    score += 100

        # Check keyword match
        for keyword in config['keywords']:
            if re.search(keyword, filename):
                score += 10

        scores[category] = score

    # Get best match
    if scores:
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score > 0:
            return best_category, best_score

    return 'uncategorized', 0

def main():
    plans_dir = Path('docs/implementation_plans')
    all_files = list(plans_dir.rglob('*.md'))

    # Categorize all files
    categorized: Dict[str, List[Tuple[Path, float]]] = {}

    for filepath in all_files:
        # Skip files already in subdirectories we're keeping
        relative = filepath.relative_to(plans_dir)
        if len(relative.parts) > 1 and relative.parts[0] in ['archive', 'active']:
            continue

        category, score = categorize_file(filepath)

        if category not in categorized:
            categorized[category] = []
        categorized[category].append((filepath, score))

    # Print categorization results
    print("=" * 80)
    print("CATEGORIZATION RESULTS")
    print("=" * 80)

    for category in sorted(categorized.keys()):
        files = categorized[category]
        print(f"\n{category.upper()} ({len(files)} files)")
        print("-" * 80)

        for filepath, score in sorted(files, key=lambda x: x[1], reverse=True):
            relative = filepath.relative_to(plans_dir)
            print(f"  [{score:3.0f}] {relative}")

    print(f"\n{'=' * 80}")
    print(f"TOTAL: {len(all_files)} files")
    print("=" * 80)

if __name__ == '__main__':
    main()
