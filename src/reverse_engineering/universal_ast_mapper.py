from typing import List
from src.core.ast_models import Action
from src.reverse_engineering.protocols import ParsedEntity, ParsedMethod, SourceLanguage

class UniversalASTMapper:
    """
    Universal mapper: Language-agnostic AST → SpecQL

    Works with any language that implements ParsedEntity/ParsedMethod protocols
    """

    def __init__(self):
        # Language-specific mappers
        from src.reverse_engineering.python_to_specql_mapper import PythonToSpecQLMapper
        from src.reverse_engineering.ast_to_specql_mapper import ASTToSpecQLMapper

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
            'entity': entity.entity_name,
            'schema': entity.namespace,
            'description': entity.docstring,
            'fields': [self._map_field(f) for f in entity.fields],
            'actions': [
                self._action_to_dict(self.map_method_to_action(m, entity))
                for m in entity.methods
            ],
            '_metadata': {
                'source_language': entity.source_language.value,
                'patterns': self._detect_patterns(entity),
            }
        }

    def map_method_to_action(self, method: ParsedMethod, entity: ParsedEntity) -> Action:
        """
        Map ParsedMethod to Action

        Delegates to language-specific mapper
        """
        mapper = self.mappers.get(entity.source_language)

        if not mapper:
            raise ValueError(f"No mapper for language: {entity.source_language}")

        return mapper.map_method_to_action(method, entity)

    def _map_field(self, field) -> dict:
        """Map ParsedField to SpecQL field dict"""
        field_dict = {
            'name': field.field_name,
            'type': field.field_type,
            'required': field.required,
        }

        if field.default is not None:
            field_dict['default'] = field.default

        if field.is_foreign_key:
            field_dict['ref'] = field.foreign_key_target

        return field_dict

    def _detect_patterns(self, entity: ParsedEntity) -> List[str]:
        """Detect cross-language patterns"""
        patterns = []

        # Entity patterns (work across languages)
        field_names = {f.field_name for f in entity.fields}

        # Audit trail pattern
        if {'created_at', 'updated_at', 'created_by', 'updated_by'} <= field_names:
            patterns.append('audit_trail')

        # Soft delete pattern
        if 'deleted_at' in field_names:
            patterns.append('soft_delete')

        # Status/state pattern
        if 'status' in field_names or 'state' in field_names:
            patterns.append('state_machine')

        # Tenant pattern
        if 'tenant_id' in field_names:
            patterns.append('multi_tenant')

        return patterns

    def _action_to_dict(self, action: Action) -> dict:
        """Convert Action to dict for YAML serialization"""
        action_dict = {
            'name': action.name,
            'steps': [self._step_to_dict(step) for step in action.steps]
        }

        if action.requires:
            action_dict['requires'] = action.requires

        return action_dict

    def _step_to_dict(self, step) -> dict:
        """Convert ActionStep to dict for YAML serialization"""
        step_dict = {'type': step.type}

        # Add relevant fields based on step type
        if hasattr(step, 'expression') and step.expression:
            step_dict['expression' if step.type == 'validate' else 'condition'] = step.expression

        if hasattr(step, 'entity') and step.entity:
            step_dict['entity'] = step.entity

        if hasattr(step, 'fields') and step.fields:
            step_dict['fields'] = step.fields

        if hasattr(step, 'function_name') and step.function_name:
            step_dict['function'] = step.function_name

        if hasattr(step, 'arguments') and step.arguments:
            step_dict['arguments'] = step.arguments

        if hasattr(step, 'then_steps') and step.then_steps:
            step_dict['then'] = [self._step_to_dict(s) for s in step.then_steps]

        if hasattr(step, 'else_steps') and step.else_steps:
            step_dict['else'] = [self._step_to_dict(s) for s in step.else_steps]

        return step_dict