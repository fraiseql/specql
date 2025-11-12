#!/usr/bin/env python3
"""
SpecQL Check Codes CLI
Check uniqueness of table codes across entity files
"""

from pathlib import Path
from typing import Dict, List

from src.core.specql_parser import SpecQLParser


def check_table_code_uniqueness(entity_files: List[Path]) -> Dict[str, List[str]]:
    """
    Check for duplicate table codes across entity files.

    Args:
        entity_files: List of paths to YAML entity files

    Returns:
        Dict mapping table codes to list of entity names that use them
        Only includes codes that appear more than once
    """
    parser = SpecQLParser()
    code_to_entities = {}

    for entity_file in entity_files:
        try:
            content = entity_file.read_text()
            entity_def = parser.parse(content)

            # Extract table code from organization
            if entity_def.organization and entity_def.organization.table_code:
                table_code = entity_def.organization.table_code
                entity_name = entity_def.name

                if table_code not in code_to_entities:
                    code_to_entities[table_code] = []
                code_to_entities[table_code].append(entity_name)

        except Exception:
            # Skip files that can't be parsed - they'll be reported as errors
            # when we add proper error handling
            continue

    # Return only codes that have duplicates
    return {code: entities for code, entities in code_to_entities.items() if len(entities) > 1}


def main():
    """Entry point for specql check-codes command"""
    # TODO: Implement CLI command
    pass


if __name__ == "__main__":
    main()
