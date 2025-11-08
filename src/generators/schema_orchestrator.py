"""
Schema Orchestrator (Team B)
Coordinates table + type generation for complete schema
"""

from typing import Dict, List, Union
from src.generators.table_generator import TableGenerator
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.core.ast_models import Entity
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.table_generator import TableGenerator


class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(self) -> None:
        self.table_gen = TableGenerator()
        self.type_gen = CompositeTypeGenerator()
        self.helper_gen = TrinityHelperGenerator()

    def generate_complete_schema(self, entity: Entity) -> str:
        """
        Generate complete schema for entity: tables + types + indexes + constraints

        Args:
            entity: Entity to generate schema for

        Returns:
            Complete SQL schema as string
        """
        parts = []

        # 1. Common types (mutation_result, deletion_input, etc.)
        common_types = self.type_gen.generate_common_types()
        if common_types:
            parts.append("-- Common Types\n" + common_types)

        # 2. Entity table (Trinity pattern)
        table_sql = self.table_gen.generate_table_ddl(entity)
        parts.append("-- Entity Table\n" + table_sql)

        # 3. Input types for actions
        for action in entity.actions:
            input_type = self.type_gen.generate_input_type(entity, action)
            if input_type:
                parts.append(f"-- Input Type: {action.name}\n" + input_type)

        # 4. Indexes
        indexes = self.table_gen.generate_indexes_ddl(entity)
        if indexes:
            parts.append("-- Indexes\n" + indexes)

        # 5. Foreign keys
        fks = self.table_gen.generate_foreign_keys_ddl(entity)
        if fks:
            parts.append("-- Foreign Keys\n" + fks)

        # 6. Trinity helper functions
        helpers = self.helper_gen.generate_all_helpers(entity)
        parts.append("-- Trinity Helper Functions\n" + helpers)

        return "\n\n".join(parts)

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
