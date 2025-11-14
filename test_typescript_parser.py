#!/usr/bin/env python3
"""
Test the TypeScript parser
"""

import sys

sys.path.append("src")

from parsers.typescript.typescript_parser import TypeScriptParser


def test_typescript_parser():
    parser = TypeScriptParser()
    content = open("test_typescript_interfaces.ts").read()
    entities = parser.parse_content(content, "test_typescript_interfaces.ts")

    print(f"Parsed {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity.name}: {len(entity.fields)} fields")
        for field in entity.fields[:3]:  # Show first 3 fields
            print(f"    {field.name}: {field.type.value} (required: {field.required})")
            if field.references:
                print(f"      -> references {field.references}")


if __name__ == "__main__":
    test_typescript_parser()
