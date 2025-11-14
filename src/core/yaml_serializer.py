"""Serialize UniversalEntity to SpecQL YAML format"""

from typing import Dict, Any, List
import yaml
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class YAMLSerializer:
    """Serializes UniversalEntity to SpecQL YAML"""

    def serialize(self, entity: UniversalEntity) -> str:
        """Convert UniversalEntity to YAML string"""
        data = self._entity_to_dict(entity)
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def _entity_to_dict(self, entity: UniversalEntity) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        result: Dict[str, Any] = {
            "entity": entity.name,
            "schema": entity.schema,
        }

        # Add fields
        if entity.fields:
            result["fields"] = self._serialize_fields(entity.fields)

        # Add actions if present
        if entity.actions:
            result["actions"] = self._serialize_actions(entity.actions)

        return result

    def _serialize_fields(self, fields: List[UniversalField]) -> Dict[str, Any]:
        """Serialize fields to dictionary"""
        result = {}

        for field in fields:
            # Skip audit fields (auto-generated)
            if field.name in ["id", "createdAt", "updatedAt", "deletedAt"]:
                continue

            field_spec = self._serialize_field(field)
            result[field.name] = field_spec

        return result

    def _serialize_field(self, field: UniversalField) -> Any:
        """Serialize single field"""
        # Simple field: just type
        if field.type in [
            FieldType.TEXT,
            FieldType.INTEGER,
            FieldType.BOOLEAN,
            FieldType.DATETIME,
        ]:
            type_str = field.type.value

            # Add required marker
            if field.required:
                type_str += "!"

            # Add default value
            if field.default is not None:
                type_str += f" = {field.default}"

            return type_str

        # Enum field
        elif field.type == FieldType.ENUM:
            enum_spec = {"type": "enum", "values": field.enum_values}
            if field.default:
                enum_spec["default"] = field.default
            return enum_spec

        # Reference field
        elif field.type == FieldType.REFERENCE:
            ref_spec = {"type": "reference", "references": field.references}
            if field.required:
                ref_spec["required"] = True
            return ref_spec

        # List field
        elif field.type == FieldType.LIST:
            return {"type": "list", "items": field.list_item_type}

        else:
            return field.type.value

    def _serialize_actions(self, actions: List) -> List[Dict[str, Any]]:
        """Serialize actions"""
        return [self._serialize_action(action) for action in actions]

    def _serialize_action(self, action) -> Dict[str, Any]:
        """Serialize single action"""
        result = {
            "name": action.name,
            "steps": [self._serialize_step(step) for step in action.steps],
        }
        return result

    def _serialize_step(self, step) -> Dict[str, str]:
        """Serialize action step"""
        return {step.type.value: step.expression or str(step.fields)}
