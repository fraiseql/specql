#!/usr/bin/env python3

from pathlib import Path

from reverse_engineering.python_ast_parser import PythonASTParser

# Read from file
source_code = Path("test_multi_models.py").read_text()

parser = PythonASTParser()
entities = parser.parse(source_code, "test_multi_models.py")

print(f"Found {len(entities)} entities:")
for entity in entities:
    print(f"  - {entity.entity_name}: {len(entity.fields)} fields")
