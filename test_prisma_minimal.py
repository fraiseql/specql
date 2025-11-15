#!/usr/bin/env python3
"""
Minimal test of Prisma parser
"""

import re
import sys

sys.path.append("src")

from core.universal_ast import UniversalEntity, UniversalField, FieldType


class MinimalPrismaParser:
    """Minimal Prisma parser for testing"""

    def __init__(self):
        self.type_mapping = {
            "String": FieldType.TEXT,
            "Int": FieldType.INTEGER,
            "Boolean": FieldType.BOOLEAN,
            "DateTime": FieldType.DATETIME,
        }

    def parse_schema_content(self, content: str):
        entities = []
        model_pattern = r"model\s+(\w+)\s*\{([^}]+)\}"
        matches = re.findall(model_pattern, content, re.DOTALL)

        for model_name, model_content in matches:
            fields = []
            lines = [line.strip() for line in model_content.split("\n") if line.strip()]

            for line in lines:
                if (
                    line.startswith("//")
                    or line.startswith("@@")
                    or "@relation" in line
                ):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    field_name = parts[0]
                    field_type = parts[1].rstrip("?")
                    is_optional = parts[1].endswith("?")

                    specql_type = self.type_mapping.get(field_type, FieldType.TEXT)

                    field = UniversalField(
                        name=field_name, type=specql_type, required=not is_optional
                    )
                    fields.append(field)

            if fields:
                entity = UniversalEntity(
                    name=model_name,
                    schema="public",
                    fields=fields,
                    actions=[],
                    description=f"Prisma model {model_name}",
                )
                entities.append(entity)

        return entities


if __name__ == "__main__":
    parser = MinimalPrismaParser()
    content = open("test_prisma_schema.prisma").read()
    entities = parser.parse_schema_content(content)

    print(f"Parsed {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity.name}: {len(entity.fields)} fields")
        for field in entity.fields[:2]:  # Show first 2 fields
            print(f"    {field.name}: {field.type.value} (required: {field.required})")
