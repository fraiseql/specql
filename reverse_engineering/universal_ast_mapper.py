import importlib.metadata
from datetime import datetime

import yaml

from core.ast_models import Action
from reverse_engineering.protocols import ParsedEntity, ParsedMethod, SourceLanguage


class UniversalASTMapper:
    """
    Universal mapper: Language-agnostic AST → SpecQL

    Works with any language that implements ParsedEntity/ParsedMethod protocols
    """

    def __init__(self):
        # Language-specific mappers
        from reverse_engineering.ast_to_specql_mapper import ASTToSpecQLMapper
        from reverse_engineering.python_to_specql_mapper import PythonToSpecQLMapper

        self.mappers = {
            SourceLanguage.PYTHON: PythonToSpecQLMapper(),
            SourceLanguage.SQL: ASTToSpecQLMapper(),
        }

    def map_entity_to_specql(self, entity: ParsedEntity) -> dict:
        """
        Map ParsedEntity to SpecQL YAML dict

        Works regardless of source language
        """
        return {
            "entity": entity.entity_name,
            "schema": entity.namespace,
            "description": entity.docstring,
            "fields": self._map_fields_to_dict(entity.fields),
            "actions": [
                self._action_to_dict(self.map_method_to_action(m, entity)) for m in entity.methods
            ],
            "_metadata": {
                "source_language": entity.source_language.value,
                "source_file": entity.metadata.get("file_path"),
                "generated_at": self._get_current_timestamp(),
                "specql_version": self._get_specql_version(),
                "patterns_detected": self._detect_patterns(entity),
                "fields_extracted": len(entity.fields),
                "actions_extracted": len(entity.methods),
            },
        }

    def map_to_specql(self, entity: ParsedEntity) -> str:
        """
        Map ParsedEntity to SpecQL YAML string

        This method implements the MapperProtocol interface
        """
        specql_dict = self.map_entity_to_specql(entity)
        return yaml.dump(specql_dict, default_flow_style=False, sort_keys=False)

    def map_method_to_action(self, method: ParsedMethod, entity: ParsedEntity) -> Action:
        """
        Map ParsedMethod to Action

        Delegates to language-specific mapper
        """
        mapper = self.mappers.get(entity.source_language)

        if not mapper:
            raise ValueError(f"No mapper for language: {entity.source_language}")

        return mapper.map_method_to_action(method, entity)

    def _map_fields_to_dict(self, fields) -> dict:
        """Map list of ParsedField to SpecQL fields dict"""
        fields_dict = {}

        for field in fields:
            # Build type string: type[!] for required fields
            type_str = field.field_type
            if field.required:
                type_str += "!"

            # Handle foreign keys
            if field.is_foreign_key:
                type_str = f"ref({field.foreign_key_target})"

            fields_dict[field.field_name] = type_str

        return fields_dict

    def _map_field(self, field) -> dict:
        """Map ParsedField to SpecQL field dict"""
        field_dict = {
            "name": field.field_name,
            "type": field.field_type,
            "required": field.required,
        }

        if field.default is not None:
            field_dict["default"] = field.default

        if field.is_foreign_key:
            field_dict["ref"] = field.foreign_key_target

        return field_dict

    def _detect_patterns(self, entity: ParsedEntity) -> list[str]:
        """Detect cross-language patterns"""
        patterns = []

        # Entity patterns (work across languages)
        field_names = {f.field_name for f in entity.fields}

        # Audit trail pattern
        if {"created_at", "updated_at", "created_by", "updated_by"} <= field_names:
            patterns.append("audit_trail")

        # Soft delete pattern
        if "deleted_at" in field_names:
            patterns.append("soft_delete")

        # Status/state pattern
        if "status" in field_names or "state" in field_names:
            patterns.append("state_machine")

        # Tenant pattern
        if "tenant_id" in field_names:
            patterns.append("multi_tenant")

        return patterns

    def _action_to_dict(self, action: Action) -> dict:
        """Convert Action to dict for YAML serialization"""
        action_dict = {
            "name": action.name,
            "steps": [self._step_to_dict(step) for step in action.steps],
        }

        if action.requires:
            action_dict["requires"] = action.requires

        return action_dict

    def _step_to_dict(self, step) -> dict:
        """Convert ActionStep to dict for YAML serialization"""
        # Generate step as string in the format expected by the parser
        if step.type == "update":
            # Format: "Entity SET field1 = value1, field2 = value2"
            entity = getattr(step, "entity", "")
            fields = getattr(step, "fields", {})
            if isinstance(fields, dict):
                set_parts = [f"{k} = {repr(v)}" for k, v in fields.items()]
                set_clause = ", ".join(set_parts)
                step_value = f"{entity} SET {set_clause}"
            else:
                step_value = str(fields)
        elif step.type == "call":
            # Format: function_name() or function_name(arg1 = value1, ...)
            function_name = getattr(step, "function_name", "")
            arguments = getattr(step, "arguments", {})
            if arguments:
                args_str = ", ".join(f"{k} = {repr(v)}" for k, v in arguments.items())
                step_value = f"{function_name}({args_str})"
            else:
                step_value = f"{function_name}()"
        elif step.type == "validate":
            # Format: expression
            step_value = getattr(step, "expression", "")
        else:
            # For other types, use a simple string representation
            step_value = str(getattr(step, "expression", ""))

        return {step.type: step_value}

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def _get_specql_version(self) -> str:
        """Get SpecQL version from package metadata"""
        try:
            return importlib.metadata.version("specql")
        except importlib.metadata.PackageNotFoundError:
            return "unknown"
