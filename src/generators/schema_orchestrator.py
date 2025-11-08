"""
Schema Orchestrator (Team B)
Coordinates table + type generation for complete schema
"""

from typing import Dict, List, Union
from src.generators.table_generator import TableGenerator
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.generators.app_schema_generator import AppSchemaGenerator
from src.generators.core_logic_generator import CoreLogicGenerator
from src.core.ast_models import Entity


class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(self) -> None:
        self.app_gen = AppSchemaGenerator()
        self.table_gen = TableGenerator()
        self.type_gen = CompositeTypeGenerator()
        self.helper_gen = TrinityHelperGenerator()
        self.core_gen = CoreLogicGenerator()

    def generate_complete_schema(self, entity: Entity) -> str:
        """
        Generate complete schema for entity: app foundation + tables + types + indexes + constraints

        Args:
            entity: Entity to generate schema for

        Returns:
            Complete SQL schema as string
        """
        parts = []

        # 1. App schema foundation (mutation_result type + shared utilities)
        app_foundation = self.app_gen.generate_app_foundation()
        if app_foundation:
            parts.append("-- App Schema Foundation\n" + app_foundation)

        # 2. Common types (mutation_result, etc.) - now handled by app foundation
        # Note: generate_common_types() is still called for backward compatibility
        # but app foundation takes precedence
        common_types = self.type_gen.generate_common_types()
        if common_types and not app_foundation:
            parts.append("-- Common Types\n" + common_types)

        # 3. Entity table (Trinity pattern)
        table_sql = self.table_gen.generate_table_ddl(entity)
        parts.append("-- Entity Table\n" + table_sql)

        # 4. Input types for actions
        for action in entity.actions:
            input_type = self.type_gen.generate_input_type(entity, action)
            if input_type:
                parts.append(f"-- Input Type: {action.name}\n" + input_type)

        # 5. Indexes
        indexes = self.table_gen.generate_indexes_ddl(entity)
        if indexes:
            parts.append("-- Indexes\n" + indexes)

        # 6. Foreign keys
        fks = self.table_gen.generate_foreign_keys_ddl(entity)
        if fks:
            parts.append("-- Foreign Keys\n" + fks)

        # 7. Core logic functions
        core_functions = []
        if entity.actions:
            # Generate core functions for each action
            # TODO: For now, generate a generic action function for each action
            # This will be refined to generate specific function types based on action analysis
            for action in entity.actions:
                # For now, generate update-style functions for all actions
                # This is a temporary implementation until action analysis is complete
                core_functions.append(self.core_gen.generate_core_update_function(entity))

        if core_functions:
            parts.append("-- Core Logic Functions\n" + "\n\n".join(core_functions))

        # 8. Trinity helper functions
        helpers = self.helper_gen.generate_all_helpers(entity)
        parts.append("-- Trinity Helper Functions\n" + helpers)

        return "\n\n".join(parts)

    def generate_app_foundation_only(self) -> str:
        """
        Generate only the app schema foundation (for base migrations)

        Returns:
            SQL for app schema foundation
        """
        return self.app_gen.generate_app_foundation()

    def generate_schema_summary(self, entity: Entity) -> Dict[str, Union[str, List[str]]]:
        """
        Generate summary of what will be created for this entity

        Returns:
            Dict with counts and names of generated objects
        """
        types_list: List[str] = []
        summary: Dict[str, Union[str, List[str]]] = {
            "entity": entity.name,
            "table": f"{entity.schema}.tb_{entity.name.lower()}",
            "types": types_list,
            "indexes": [],
            "constraints": [],
        }

        # Count types that will be generated
        for action in entity.actions:
            if self.type_gen.generate_input_type(entity, action):
                types_list.append(f"app.type_{action.name}_input")

        # Add common types
        if self.type_gen.generate_common_types():
            types_list.extend(["app.mutation_result", "app.type_deletion_input"])

        # Indexes and constraints would be counted here
        # (simplified for now)

        return summary
