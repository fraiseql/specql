"""
YAML utilities for SpecQL entities
"""

import yaml
from typing import List
from src.core.universal_ast import UniversalEntity


def entities_to_yaml_string(entities: List[UniversalEntity]) -> str:
    """
    Convert list of UniversalEntity objects to YAML string

    Args:
        entities: List of entities to convert

    Returns:
        YAML string representation
    """
    # Convert entities to dict format
    entities_dict = []
    for entity in entities:
        entity_dict = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "fields": [
                    {
                        "name": field.name,
                        "type": field.type.value,
                        "required": field.required,
                        "default": field.default,
                        "references": field.references,
                    }
                    for field in entity.fields
                ],
                "actions": [
                    {
                        "name": action.name,
                        "parameters": [
                            {"name": param.name, "type": param.type.value}
                            for param in (action.parameters or [])
                        ],
                        "steps": [
                            {"type": step.type.value, "expression": step.expression}
                            for step in action.steps
                        ],
                    }
                    for action in entity.actions
                ],
            }
        }
        entities_dict.append(entity_dict)

    return yaml.dump(entities_dict, default_flow_style=False, sort_keys=False)


def yaml_string_to_entities(yaml_str: str) -> List[UniversalEntity]:
    """
    Convert YAML string to list of UniversalEntity objects

    Args:
        yaml_str: YAML string to parse

    Returns:
        List of UniversalEntity objects
    """
    from src.core.universal_ast import UniversalField, UniversalAction, FieldType

    data = yaml.safe_load(yaml_str)
    entities = []

    for item in data:
        entity_data = item["entity"]
        fields = []
        for field_data in entity_data.get("fields", []):
            field = UniversalField(
                name=field_data["name"],
                type=FieldType(field_data["type"]),
                required=field_data.get("required", True),
                default=field_data.get("default"),
                references=field_data.get("references"),
            )
            fields.append(field)

        actions = []
        for action_data in entity_data.get("actions", []):
            # Simplified action creation for round-trip testing
            action = UniversalAction(
                name=action_data["name"],
                entity=entity_data["name"],  # Required field
                steps=[],  # Required field
                impacts=[],  # Required field
            )
            actions.append(action)

        entity = UniversalEntity(
            name=entity_data["name"],
            schema=entity_data["schema"],
            fields=fields,
            actions=actions,
        )
        entities.append(entity)

    return entities
