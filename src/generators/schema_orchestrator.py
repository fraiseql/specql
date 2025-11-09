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
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.schema.table_view_generator import TableViewGenerator
from src.generators.schema.table_view_dependency import TableViewDependencyResolver
from src.generators.fraiseql.table_view_annotator import TableViewAnnotator
from src.generators.fraiseql.mutation_annotator import MutationAnnotator
from src.core.ast_models import Entity, EntityDefinition


class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(self, naming_conventions: NamingConventions = None) -> None:
        # Create naming conventions if not provided
        if naming_conventions is None:
            naming_conventions = NamingConventions()

        # Create schema registry
        schema_registry = SchemaRegistry(naming_conventions.registry)

        self.app_gen = AppSchemaGenerator()
        self.table_gen = TableGenerator(schema_registry)
        self.type_gen = CompositeTypeGenerator()
        self.helper_gen = TrinityHelperGenerator(schema_registry)
        self.core_gen = CoreLogicGenerator(schema_registry)

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

        # 2. Create schema if needed
        schema_creation = f"CREATE SCHEMA IF NOT EXISTS {entity.schema};"
        parts.append(f"-- Create schema\n{schema_creation}")

        # 3. Common types (mutation_result, etc.) - now handled by app foundation
        # Note: generate_common_types() is still called for backward compatibility
        # but app foundation takes precedence
        common_types = self.type_gen.generate_common_types()
        if common_types and not app_foundation:
            parts.append("-- Common Types\n" + common_types)

        # 4. Entity table (Trinity pattern)
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
            # Generate core functions for each action based on detected pattern
            for action in entity.actions:
                action_pattern = self.core_gen.detect_action_pattern(action.name)
                if action_pattern == "create":
                    core_functions.append(self.core_gen.generate_core_create_function(entity))
                elif action_pattern == "update":
                    core_functions.append(self.core_gen.generate_core_update_function(entity))
                elif action_pattern == "delete":
                    core_functions.append(self.core_gen.generate_core_delete_function(entity))
                else:  # custom
                    core_functions.append(self.core_gen.generate_core_custom_action(entity, action))

        if core_functions:
            parts.append("-- Core Logic Functions\n" + "\n\n".join(core_functions))

        # 8. FraiseQL mutation annotations (Team D)
        mutation_annotations = []
        if entity.actions:
            for action in entity.actions:
                annotator = MutationAnnotator(entity.schema, entity.name)
                annotation = annotator.generate_mutation_annotation(action)
                if annotation:
                    mutation_annotations.append(annotation)

        if mutation_annotations:
            parts.append(
                "-- FraiseQL Mutation Annotations (Team D)\n" + "\n\n".join(mutation_annotations)
            )

        # 9. Trinity helper functions
        helpers = self.helper_gen.generate_all_helpers(entity)
        parts.append("-- Trinity Helper Functions\n" + helpers)

        return "\n\n".join(parts)

    def generate_table_views(self, entities: List[EntityDefinition]) -> str:
        """
        Generate tv_ tables for all entities in dependency order.

        Args:
            entities: All entities to generate tv_ tables for

        Returns:
            Complete SQL for all tv_ tables and refresh functions
        """
        if not entities:
            return ""

        # Resolve dependency order for generation
        resolver = TableViewDependencyResolver(entities)
        generation_order = resolver.get_generation_order()

        parts = []

        # Generate tv_ tables in dependency order
        for entity_name in generation_order:
            entity = next(e for e in entities if e.name == entity_name)
            generator = TableViewGenerator(entity, {e.name: e for e in entities})
            tv_schema = generator.generate_schema()
            if tv_schema:
                parts.append(
                    f"-- Table View: {entity.schema}.tv_{entity.name.lower()}\n" + tv_schema
                )

            # Generate FraiseQL annotations for tv_ table
            if entity.table_views:
                annotator = TableViewAnnotator(entity)
                annotations = annotator.generate_annotations()
                if annotations:
                    parts.append(
                        f"-- FraiseQL Annotations: {entity.schema}.tv_{entity.name.lower()}\n"
                        + annotations
                    )

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
