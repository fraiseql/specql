"""
Schema Orchestrator (Team B)
Coordinates table + type generation for complete schema
"""

from dataclasses import dataclass

from src.core.ast_models import Entity, EntityDefinition
from src.utils.logger import LogContext, get_team_logger
from src.utils.performance_monitor import get_performance_monitor
from src.generators.app_schema_generator import AppSchemaGenerator
from src.generators.app_wrapper_generator import AppWrapperGenerator
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.core_logic_generator import CoreLogicGenerator
from src.generators.fraiseql.mutation_annotator import MutationAnnotator
from src.generators.fraiseql.table_view_annotator import TableViewAnnotator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.schema.table_view_dependency import TableViewDependencyResolver
from src.generators.schema.table_view_generator import TableViewGenerator
from src.generators.table_generator import TableGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.utils.safe_slug import safe_table_name


@dataclass
class MutationFunctionPair:
    """One mutation = 2 functions + FraiseQL comments (ALL IN ONE FILE)"""

    action_name: str
    app_wrapper_sql: str  # app.{action_name}()
    core_logic_sql: str  # core.{action_name}()
    fraiseql_comments_sql: str  # COMMENT ON FUNCTION statements (Team D)


@dataclass
class SchemaOutput:
    """Split output for Confiture directory structure"""

    table_sql: str  # → db/schema/10_tables/{entity}.sql (includes FraiseQL COMMENT)
    helpers_sql: str  # → db/schema/20_helpers/{entity}_helpers.sql
    mutations: list[
        MutationFunctionPair
    ]  # → db/schema/30_functions/{action_name}.sql (ONE FILE EACH!)


class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(self, naming_conventions: NamingConventions | None = None, enable_performance_monitoring: bool = False) -> None:
        self.logger = get_team_logger("Team B", __name__)
        self.logger.debug("Initializing SchemaOrchestrator")

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

        # Performance monitoring
        self.enable_performance_monitoring = enable_performance_monitoring
        self.perf_monitor = get_performance_monitor() if enable_performance_monitoring else None

        self.logger.debug("SchemaOrchestrator initialized successfully")

    def generate_complete_schema(self, entity: Entity) -> str:
        """
        Generate complete schema for entity: app foundation + tables + types + indexes + constraints

        Args:
            entity: Entity to generate schema for

        Returns:
            Complete SQL schema as string
        """
        context = LogContext(
            entity_name=entity.name,
            schema=entity.schema,
            operation="generate_schema"
        )
        logger = get_team_logger("Team B", __name__, context)
        logger.info(f"Generating complete schema for entity '{entity.name}' in schema '{entity.schema}'")

        parts = []

        # 1. App schema foundation (mutation_result type + shared utilities)
        logger.debug("Generating app schema foundation")
        app_foundation = self.app_gen.generate_app_foundation()
        if app_foundation:
            parts.append("-- App Schema Foundation\n" + app_foundation)
            logger.debug("App schema foundation generated")

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
        logger.debug("Generating entity table DDL")
        table_sql = self.table_gen.generate_table_ddl(entity)
        parts.append("-- Entity Table\n" + table_sql)

        # 4.5. Field comments for FraiseQL metadata
        field_comments = self.table_gen.generate_field_comments(entity)
        if field_comments:
            logger.debug(f"Generated {len(field_comments)} field comments")
            parts.append("-- Field Comments for FraiseQL\n" + "\n\n".join(field_comments))

        # 4. Input types for actions
        if entity.actions:
            logger.debug(f"Generating input types for {len(entity.actions)} actions")
        for action in entity.actions:
            input_type = self.type_gen.generate_input_type(entity, action)
            if input_type:
                parts.append(f"-- Input Type: {action.name}\n" + input_type)

        # 5. Indexes
        logger.debug("Generating indexes")
        indexes = self.table_gen.generate_indexes_ddl(entity)
        if indexes:
            parts.append("-- Indexes\n" + indexes)

        # 6. Foreign keys
        logger.debug("Generating foreign keys")
        fks = self.table_gen.generate_foreign_keys_ddl(entity)
        if fks:
            parts.append("-- Foreign Keys\n" + fks)

        # 7. Core logic functions
        core_functions = []
        if entity.actions:
            logger.debug(f"Generating core logic functions for {len(entity.actions)} actions")
            # Generate core functions for each action based on detected pattern
            for action in entity.actions:
                action_pattern = self.core_gen.detect_action_pattern(action.name)
                logger.debug(f"Generating {action_pattern} function for action '{action.name}'")
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
            logger.debug(f"Generating FraiseQL mutation annotations for {len(entity.actions)} actions")
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
        logger.debug("Generating Trinity helper functions")
        helpers = self.helper_gen.generate_all_helpers(entity)
        parts.append("-- Trinity Helper Functions\n" + helpers)

        logger.info(f"Successfully generated complete schema for '{entity.name}' ({len(parts)} components)")
        return "\n\n".join(parts)

    def generate_split_schema(self, entity: Entity) -> SchemaOutput:
        """
        Generate schema split by component

        CRITICAL: Each action generates a SEPARATE file with 2 functions + comments
        """
        # Track schema generation time if performance monitoring is enabled
        if self.perf_monitor:
            ctx = self.perf_monitor.track("generate_schema", category="generation")
            ctx.__enter__()
        else:
            ctx = None

        try:
            context = LogContext(
                entity_name=entity.name,
                schema=entity.schema,
                operation="generate_split_schema"
            )
            logger = get_team_logger("Team B", __name__, context)
            logger.info(f"Generating split schema for entity '{entity.name}'")

            # Team B: Table definition
            logger.debug("Generating table DDL")
            if self.perf_monitor:
                with self.perf_monitor.track("table_ddl", category="template_rendering"):
                    table_ddl = self.table_gen.generate_table_ddl(entity)
            else:
                table_ddl = self.table_gen.generate_table_ddl(entity)
            table_sql = table_ddl  # For now, no table comments

            # Team B: Helper functions (Trinity pattern utilities)
            logger.debug("Generating helper functions")
            if self.perf_monitor:
                with self.perf_monitor.track("helpers", category="template_rendering"):
                    helpers_sql = self.helper_gen.generate_all_helpers(entity)
            else:
                helpers_sql = self.helper_gen.generate_all_helpers(entity)

            # Team C + Team D: ONE FILE PER MUTATION (app + core + comments)
            mutations = []
            app_wrapper_gen = AppWrapperGenerator()

            if entity.actions:
                logger.debug(f"Generating {len(entity.actions)} mutation files")

            for action in entity.actions:
                # Detect action pattern for core function generation
                action_pattern = self.core_gen.detect_action_pattern(action.name)
                logger.debug(f"Generating mutation '{action.name}' (pattern: {action_pattern})")

                # Generate core function based on pattern
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

            logger.info(f"Successfully generated split schema for '{entity.name}' ({len(mutations)} mutations)")
            return SchemaOutput(table_sql=table_sql, helpers_sql=helpers_sql, mutations=mutations)
        finally:
            # Exit performance tracking context
            if ctx:
                ctx.__exit__(None, None, None)

    def generate_table_views(self, entities: list[EntityDefinition]) -> str:
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
