"""CLI Orchestrator for unified generation workflows."""

from dataclasses import dataclass
from pathlib import Path

from src.core.specql_parser import SpecQLParser
from src.generators.schema.naming_conventions import NamingConventions  # NEW
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.utils.performance_monitor import get_performance_monitor


@dataclass
class MigrationFile:
    """Represents a generated migration file"""

    number: int  # Kept for backward compatibility
    name: str
    content: str
    path: Path | None = None
    table_code: str | None = None  # NEW: Hexadecimal table code


@dataclass
class GenerationResult:
    """Result of generation process"""

    migrations: list[MigrationFile]
    errors: list[str]
    warnings: list[str]


class CLIOrchestrator:
    """Orchestrate all Teams for CLI commands"""

    def __init__(self, use_registry: bool = False, output_format: str = "hierarchical", enable_performance_monitoring: bool = False):
        self.enable_performance_monitoring = enable_performance_monitoring
        self.perf_monitor = get_performance_monitor() if enable_performance_monitoring else None

        self.parser = SpecQLParser(enable_performance_monitoring=enable_performance_monitoring)
        self.schema_orchestrator = SchemaOrchestrator(enable_performance_monitoring=enable_performance_monitoring)

        # NEW: Registry integration
        self.use_registry = use_registry
        self.output_format = output_format
        if use_registry:
            self.naming = NamingConventions()
        else:
            self.naming = None

    def get_table_code(self, entity) -> str:
        """
        Derive table code from registry

        Returns:
            6-character hexadecimal table code (e.g., "012311")
        """
        if not self.use_registry or not self.naming:
            raise ValueError("Registry not enabled. Use CLIOrchestrator(use_registry=True)")

        return self.naming.derive_table_code(entity)

    def generate_file_path(
        self,
        entity,
        table_code: str,
        file_type: str = "table",
        base_dir: str = "generated/migrations",
    ) -> str:
        """
        Generate file path (registry-aware or legacy flat)

        Args:
            entity: Entity AST model
            table_code: 6-digit hexadecimal table code
            file_type: Type of file ('table', 'function', 'comment')
            base_dir: Base directory for output

        Returns:
            File path (hierarchical if registry enabled, flat otherwise)
        """
        if self.use_registry and self.naming:
            if self.output_format == "confiture":
                # Use Confiture-compatible flat paths
                return self.generate_file_path_confiture(entity, file_type)
            else:
                # Use registry's hierarchical path
                return self.naming.generate_file_path(
                    entity=entity, table_code=table_code, file_type=file_type, base_dir=base_dir
                )
        else:
            # Legacy flat path
            return str(Path(base_dir) / f"{table_code}_{entity.name.lower()}.sql")

    def generate_file_path_confiture(self, entity, file_type: str) -> str:
        """
        Generate Confiture-compatible flat paths

        Maps registry layers to Confiture directories:
        - 01_write_side → db/schema/10_tables
        - 03_functions → db/schema/30_functions
        - metadata → db/schema/40_metadata
        """
        confiture_map = {"table": "10_tables", "function": "30_functions", "comment": "40_metadata"}

        dir_name = confiture_map.get(file_type, "10_tables")
        filename = f"{entity.name.lower()}.sql"

        return f"db/schema/{dir_name}/{filename}"

    def generate_from_files(
        self,
        entity_files: list[str],
        output_dir: str = "migrations",
        with_impacts: bool = False,
        include_tv: bool = False,
        foundation_only: bool = False,
    ) -> GenerationResult:
        """
        Generate migrations from SpecQL files (registry-aware)

        When use_registry=True:
        - Derives hexadecimal table codes
        - Creates hierarchical directory structure
        - Registers entities in domain_registry.yaml

        When use_registry=False:
        - Uses legacy flat numbering (000, 100, 200)
        - Single directory output
        """

        result = GenerationResult(migrations=[], errors=[], warnings=[])
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Foundation only mode
        if foundation_only:
            foundation_sql = self.schema_orchestrator.generate_app_foundation_only()
            migration = MigrationFile(
                number=0,
                name="app_foundation",
                content=foundation_sql,
                path=output_path / "000_app_foundation.sql",
            )
            result.migrations.append(migration)
            # Write the file
            if migration.path:
                migration.path.write_text(migration.content)
            return result

        # Generate foundation first
        foundation_sql = self.schema_orchestrator.generate_app_foundation_only()
        if foundation_sql:
            if self.output_format == "confiture":
                # For Confiture: write to db/schema/00_foundation/
                foundation_dir = Path("db/schema/00_foundation")
                foundation_dir.mkdir(parents=True, exist_ok=True)
                foundation_path = foundation_dir / "000_app_foundation.sql"
                foundation_path.write_text(foundation_sql)
                migration = MigrationFile(
                    number=0,
                    name="app_foundation",
                    content=foundation_sql,
                    path=foundation_path,
                )
            else:
                # Legacy format: write to output_dir
                migration = MigrationFile(
                    number=0,
                    name="app_foundation",
                    content=foundation_sql,
                    path=output_path / "000_app_foundation.sql",
                )
            result.migrations.append(migration)

        # Parse all entities
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = self.parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                result.errors.append(f"Failed to parse {entity_file}: {e}")

        # Generate entity migrations
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity

                entity = convert_entity_definition_to_entity(entity_def)

                if self.use_registry:
                    # Registry-based generation
                    table_code = self.get_table_code(entity)

                    # Generate SPLIT schema for Confiture
                    schema_output = self.schema_orchestrator.generate_split_schema(entity)

                    # Write to Confiture directory structure
                    schema_base = Path("db/schema")

                    # 1. Table definition (db/schema/10_tables/)
                    table_dir = schema_base / "10_tables"
                    table_dir.mkdir(parents=True, exist_ok=True)
                    table_path = table_dir / f"{entity.name.lower()}.sql"
                    table_path.write_text(schema_output.table_sql)

                    # 2. Helper functions (db/schema/20_helpers/)
                    helpers_dir = schema_base / "20_helpers"
                    helpers_dir.mkdir(parents=True, exist_ok=True)
                    helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"
                    helpers_path.write_text(schema_output.helpers_sql)

                    # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                    functions_dir = schema_base / "30_functions"
                    functions_dir.mkdir(parents=True, exist_ok=True)

                    for mutation in schema_output.mutations:
                        mutation_path = functions_dir / f"{mutation.action_name}.sql"
                        mutation_content = f"""-- ============================================================================
-- Mutation: {mutation.action_name}
-- Entity: {entity.name}
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

{mutation.app_wrapper_sql}

{mutation.core_logic_sql}

{mutation.fraiseql_comments_sql}
"""
                        mutation_path.write_text(mutation_content)

                    # Register entity if using registry
                    if self.naming:
                        self.naming.register_entity_auto(entity, table_code)

                        # Register entity in domain registry
                        self.naming.register_entity_auto(entity, table_code)

                    # Track all files
                    migration = MigrationFile(
                        number=int(table_code, 16),
                        name=entity.name.lower(),
                        content=schema_output.table_sql,  # Primary content
                        path=Path(table_path) if table_path else None,
                        table_code=table_code,
                    )

                else:
                    # Confiture-compatible generation (default behavior)
                    schema_output = self.schema_orchestrator.generate_split_schema(entity)

                    # Write to Confiture directory structure
                    schema_base = Path("db/schema")

                    # 1. Table definition (db/schema/10_tables/)
                    table_dir = schema_base / "10_tables"
                    table_dir.mkdir(parents=True, exist_ok=True)
                    table_path = table_dir / f"{entity.name.lower()}.sql"
                    table_path.write_text(schema_output.table_sql)

                    # 2. Helper functions (db/schema/20_helpers/)
                    helpers_dir = schema_base / "20_helpers"
                    helpers_dir.mkdir(parents=True, exist_ok=True)
                    helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"
                    helpers_path.write_text(schema_output.helpers_sql)

                    # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                    functions_dir = schema_base / "30_functions"
                    functions_dir.mkdir(parents=True, exist_ok=True)

                    for mutation in schema_output.mutations:
                        mutation_path = functions_dir / f"{mutation.action_name}.sql"
                        mutation_content = f"""-- ============================================================================
-- Mutation: {mutation.action_name}
-- Entity: {entity.name}
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

{mutation.app_wrapper_sql}

{mutation.core_logic_sql}

{mutation.fraiseql_comments_sql}
"""
                        mutation_path.write_text(mutation_content)

                    # Use sequential numbering for backward compatibility
                    entity_count = len([m for m in result.migrations if m.number >= 100])
                    entity_number = 100 + entity_count

                    migration = MigrationFile(
                        number=entity_number,
                        name=entity.name.lower(),
                        content=schema_output.table_sql,  # Primary content
                        path=table_path,
                    )

                result.migrations.append(migration)

            except Exception as e:
                result.errors.append(f"Failed to generate {entity_def.name}: {e}")

        # Generate tv_ tables if requested
        if include_tv and entity_defs:
            try:
                tv_sql = self.schema_orchestrator.generate_table_views(entity_defs)
                if tv_sql:
                    migration = MigrationFile(
                        number=200,
                        name="table_views",
                        content=tv_sql,
                        path=output_path / "200_table_views.sql",
                    )
                    result.migrations.append(migration)
            except Exception as e:
                result.errors.append(f"Failed to generate tv_ tables: {e}")

        # Write migrations to disk
        for migration in result.migrations:
            if migration.path:
                migration.path.write_text(migration.content)

        return result
