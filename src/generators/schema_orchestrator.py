"""
Schema Orchestrator (Team B)
Coordinates table + type generation for complete schema
"""

from dataclasses import dataclass

from src.core.ast_models import Entity, EntityDefinition
from src.generators.app_schema_generator import AppSchemaGenerator
from src.generators.app_wrapper_generator import AppWrapperGenerator
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.core_logic_generator import CoreLogicGenerator
from src.generators.enterprise.audit_generator import AuditGenerator
from src.generators.fraiseql.mutation_annotator import MutationAnnotator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.schema.table_view_file import TableViewFile
from src.generators.schema.table_view_file_generator import TableViewFileGenerator
from src.generators.table_generator import TableGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.utils.safe_slug import safe_table_name


@dataclass
class MutationFunctionPair:
    """One mutation = 2 functions + FraiseQL comments (ALL IN ONE FILE)"""

    action_name: str
    app_wrapper_sql: str  # app.{action_name}()
    core_logic_sql: str  # core.{action_name}()
    fraiseql_comments_sql: str  # COMMENT ON FUNCTION statements


@dataclass
class SchemaOutput:
    """Split output for Confiture directory structure"""

    table_sql: str  # → db/schema/10_tables/{entity}.sql (includes FraiseQL COMMENT)
    helpers_sql: str  # → db/schema/20_helpers/{entity}_helpers.sql
    mutations: list[
        MutationFunctionPair
    ]  # → db/schema/30_functions/{action_name}.sql (ONE FILE EACH!)
    audit_sql: str | None = None  # → db/schema/40_audit/{entity}_audit.sql (optional)


class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(
        self,
        entities: list | None = None,
        actions: list | None = None,
        naming_conventions: NamingConventions | None = None,
        enable_performance_monitoring: bool = False,
    ) -> None:
        # Create naming conventions if not provided and registry is needed
        if naming_conventions is None:
            # Only create naming conventions if we actually need registry functionality
            # For now, always create it but this could be optimized later
            naming_conventions = NamingConventions()

        # Create schema registry
        schema_registry = SchemaRegistry()

        # Store entities and actions for future use
        self.entities = entities or []
        self.actions = actions or []

        # Performance monitoring
        self.perf_monitor = None
        if enable_performance_monitoring:
            from src.utils.performance_monitor import get_performance_monitor
            self.perf_monitor = get_performance_monitor()

        self.app_gen = AppSchemaGenerator(templates_dir="../specql/templates/sql")
        self.table_gen = TableGenerator(schema_registry, templates_dir="../specql/templates/sql")
        self.type_gen = CompositeTypeGenerator(templates_dir="../specql/templates/sql")
        self.helper_gen = TrinityHelperGenerator(schema_registry, templates_dir="../specql/templates/sql")
        self.core_gen = CoreLogicGenerator(schema_registry, templates_dir="../specql/templates/sql")

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

        # 4.5. Field comments for FraiseQL metadata
        field_comments = self.table_gen.generate_field_comments(entity)
        if field_comments:
            parts.append("-- Field Comments for FraiseQL\n" + "\n\n".join(field_comments))

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

        # 8. FraiseQL mutation annotations
        mutation_annotations = []
        if entity.actions:
            for action in entity.actions:
                annotator = MutationAnnotator(entity.schema, entity.name)
                annotation = annotator.generate_mutation_annotation(action)
                if annotation:
                    mutation_annotations.append(annotation)

        if mutation_annotations:
            parts.append("-- FraiseQL Mutation Annotations\n" + "\n\n".join(mutation_annotations))

        # 9. Trinity helper functions
        helpers = self.helper_gen.generate_all_helpers(entity)
        parts.append("-- Trinity Helper Functions\n" + helpers)

        return "\n\n".join(parts)

    def generate_split_schema(self, entity: Entity, with_audit_cascade: bool = False) -> SchemaOutput:
        """
        Generate schema split by component

        CRITICAL: Each action generates a SEPARATE file with 2 functions + comments
        """
        # Generate table DDL with performance tracking
        if self.perf_monitor:
            with self.perf_monitor.track("table_ddl", category="template_rendering"):
                table_ddl = self.table_gen.generate_table_ddl(entity)
        else:
            table_ddl = self.table_gen.generate_table_ddl(entity)
        table_sql = table_ddl  # For now, no table comments

        # Generate helper functions with performance tracking
        if self.perf_monitor:
            with self.perf_monitor.track("helpers", category="template_rendering"):
                helpers_sql = self.helper_gen.generate_all_helpers(entity)
        else:
            helpers_sql = self.helper_gen.generate_all_helpers(entity)

        mutations = []
        app_wrapper_gen = AppWrapperGenerator(templates_dir="../specql/templates/sql")

        for action in entity.actions:
            # Detect action pattern for core function generation
            action_pattern = self.core_gen.detect_action_pattern(action.name)

            # Generate core function based on pattern with performance tracking
            if self.perf_monitor:
                with self.perf_monitor.track(f"mutation_{action.name}", category="template_rendering"):
                    if action_pattern == "create":
                        core_sql = self.core_gen.generate_core_create_function(entity)
                    elif action_pattern == "update":
                        core_sql = self.core_gen.generate_core_update_function(entity)
                    elif action_pattern == "delete":
                        core_sql = self.core_gen.generate_core_delete_function(entity)
                    else:  # custom
                        core_sql = self.core_gen.generate_core_custom_action(entity, action)
            else:
                if action_pattern == "create":
                    core_sql = self.core_gen.generate_core_create_function(entity)
                elif action_pattern == "update":
                    core_sql = self.core_gen.generate_core_update_function(entity)
                elif action_pattern == "delete":
                    core_sql = self.core_gen.generate_core_delete_function(entity)
                else:  # custom
                    core_sql = self.core_gen.generate_core_custom_action(entity, action)

            # Generate app wrapper
            app_sql = app_wrapper_gen.generate_app_wrapper(entity, action)

            # Generate FraiseQL comments
            annotator = MutationAnnotator(entity.schema, entity.name)
            comments_sql = annotator.generate_mutation_annotation(action)

            mutations.append(
                MutationFunctionPair(
                    action_name=action.name,
                    app_wrapper_sql=app_sql,
                    core_logic_sql=core_sql,
                    fraiseql_comments_sql=comments_sql,
                )
            )

        # Generate audit SQL if requested
        audit_sql = None
        if with_audit_cascade:
            audit_gen = AuditGenerator()
            # Get entity fields for audit generation
            entity_fields = [field.name for field in entity.fields]
            audit_config = {"enabled": True, "include_cascade": True}
            audit_sql = audit_gen.generate_audit_trail(entity.name, entity_fields, audit_config)

        return SchemaOutput(table_sql=table_sql, helpers_sql=helpers_sql, mutations=mutations, audit_sql=audit_sql)

    def generate_table_views(self, entities: list[EntityDefinition]) -> list[TableViewFile]:
        """
        Generate tv_ table files for all entities in dependency order.

        Args:
            entities: All entities to generate tv_ table files for

        Returns:
            List of TableViewFile objects, one per tv_ entity in dependency order
        """
        if not entities:
            return []

        # Use TableViewFileGenerator to create individual files
        file_generator = TableViewFileGenerator(entities)
        return file_generator.generate_files()

    def generate_app_foundation_only(self, include_outbox: bool = False) -> str:
        """
        Generate only the app schema foundation (for base migrations)

        Returns:
            SQL for app schema foundation
        """
        return self.app_gen.generate_app_foundation(include_outbox)

    def generate_schema_summary(self, entity: Entity) -> dict[str, str | list[str]]:
        """
        Generate summary of what will be created for this entity

        Returns:
            Dict with counts and names of generated objects
        """
        types_list: list[str] = []
        summary: dict[str, str | list[str]] = {
            "entity": entity.name,
            "table": f"{entity.schema}.{safe_table_name(entity.name)}",
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

    def generate_full_schema(self) -> str:
        """
        Generate complete schema including jobs schema for external services

        Returns:
            Complete SQL schema as string
        """
        from src.generators.schema.jobs_schema_generator import JobsSchemaGenerator

        parts = []

        # 1. App schema foundation
        app_foundation = self.app_gen.generate_app_foundation()
        if app_foundation:
            parts.append("-- App Schema Foundation\n" + app_foundation)

        # 2. Jobs schema for external services
        jobs_gen = JobsSchemaGenerator()
        jobs_schema = jobs_gen.generate()
        parts.append("-- Jobs Schema for External Services\n" + jobs_schema)

        return "\n\n".join(parts)
