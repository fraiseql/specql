"""CLI Orchestrator for unified generation workflows."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.cli.progress import SpecQLProgress
from src.cli.framework_registry import get_framework_registry
from src.core.specql_parser import SpecQLParser
from src.generators.schema.naming_conventions import NamingConventions  # NEW
from src.generators.schema_orchestrator import SchemaOrchestrator


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

    def __init__(
        self,
        use_registry: bool = True,  # CHANGED: Default to True for production-ready
        output_format: str = "hierarchical",
        verbose: bool = False,
        framework: str = "fraiseql"
    ):
        self.parser = SpecQLParser()
        try:
            self.progress = SpecQLProgress(verbose=verbose)
        except Exception as e:
            print(f"DEBUG: Failed to initialize progress: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Framework-aware defaults
        self.framework = framework
        registry = get_framework_registry()
        self.framework_defaults = registry.get_effective_defaults(framework)

        # Apply framework defaults to generation settings
        # use_registry parameter takes precedence over framework defaults
        self.use_registry = use_registry
        self.output_format = output_format

        # NEW: Registry integration - conditionally create SchemaOrchestrator
        if self.use_registry:
            self.naming = NamingConventions()
            self.schema_orchestrator = SchemaOrchestrator(naming_conventions=self.naming)
        else:
            self.naming = None
            self.schema_orchestrator = SchemaOrchestrator(naming_conventions=None)

    def get_table_code(self, entity) -> str:
        """
        Derive table code from registry

        Returns:
            6-character hexadecimal table code (e.g., "012311")
        """
        if not self.use_registry or not self.naming:
            raise ValueError("Registry not enabled. Use CLIOrchestrator(use_registry=True)")

        return self.naming.get_table_code(entity)  # Respects priority: explicit → registry → derive

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
        with_query_patterns: bool = False,
        with_audit_cascade: bool = False,
        with_outbox: bool = False,
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

        print(f"DEBUG: generate_from_files called with {len(entity_files)} files")

        # Phase 1: Scan entity files
        schema_stats = self.progress.scan_phase(entity_files)
        print(f"DEBUG: scan_phase completed")

        result = GenerationResult(migrations=[], errors=[], warnings=[])
        print(f"DEBUG: GenerationResult created")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Foundation only mode
        if foundation_only:
            foundation_sql = self.schema_orchestrator.generate_app_foundation_only(with_outbox)
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

        # Generate foundation first (always, unless foundation_only)
        print(f"DEBUG: Generating foundation")
        foundation_sql = self.schema_orchestrator.generate_app_foundation_only()
        print(f"DEBUG: Foundation SQL generated, length: {len(foundation_sql) if foundation_sql else 0}")
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

        print(f"DEBUG: Parsed {len(entity_defs)} entity definitions")

        # Convert entities
        entities = []
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity
                entity = convert_entity_definition_to_entity(entity_def)
                entities.append(entity)
            except Exception as e:
                result.errors.append(f"Failed to convert {entity_def.name}: {e}")

        print(f"DEBUG: Converted to {len(entities)} entities")

        # Use progress bar for generation
        generated_files = []
        print(f"DEBUG: Starting progress generation with {len(entities)} entities")
        if not entities:
            print("DEBUG: No entities to process")
            return result

        for entity, progress_update in self.progress.generation_progress(entities):
            print(f"DEBUG: Processing entity {entity.name}")
            try:
                # Find the corresponding entity_def for this entity
                entity_def = next(ed for ed in entity_defs if ed.name == entity.name)

                # Generate the entity migration (existing logic)
                if self.use_registry:
                    # Registry-based generation
                    table_code = self.get_table_code(entity)

                    # Generate SPLIT schema for Confiture
                    schema_output = self.schema_orchestrator.generate_split_schema(entity, with_audit_cascade)

                    # Determine output structure
                    if self.output_format == "hierarchical":

                        # Write to hierarchical directory structure
                        table_path = self.generate_file_path(
                            entity, table_code, "table", output_dir
                        )
                        helpers_path = self.generate_file_path(
                            entity, table_code, "function", output_dir
                        )
                        functions_dir = Path(
                            self.generate_file_path(entity, table_code, "function", output_dir)
                        ).parent

                        # Ensure directories exist
                        Path(table_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(helpers_path).parent.mkdir(parents=True, exist_ok=True)
                        functions_dir.mkdir(parents=True, exist_ok=True)
                        schema_base = None  # Not used in hierarchical mode
                    else:
                        # Write to Confiture directory structure
                        schema_base = Path("db/schema")

                        # 1. Table definition (db/schema/10_tables/)
                        table_dir = schema_base / "10_tables"
                        table_dir.mkdir(parents=True, exist_ok=True)
                        table_path = table_dir / f"{entity.name.lower()}.sql"

                        # 2. Helper functions (db/schema/20_helpers/)
                        helpers_dir = schema_base / "20_helpers"
                        helpers_dir.mkdir(parents=True, exist_ok=True)
                        helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"

                        # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                        functions_dir = schema_base / "30_functions"
                        functions_dir.mkdir(parents=True, exist_ok=True)

                    # Write table SQL
                    Path(table_path).write_text(schema_output.table_sql)
                    generated_files.append(table_path)

                    # Write helpers SQL
                    Path(helpers_path).write_text(schema_output.helpers_sql)
                    generated_files.append(helpers_path)

                    # Write mutations
                    for mutation in schema_output.mutations:
                        if self.output_format == "hierarchical":
                            from src.generators.naming_utils import camel_to_snake

                            entity_snake = camel_to_snake(entity.name)
                            mutation_path = (
                                functions_dir
                                / f"{table_code}_fn_{entity_snake}_{mutation.action_name}.sql"
                            )
                        else:
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
                        generated_files.append(str(mutation_path))

                    # Write audit SQL if generated
                    if schema_output.audit_sql:
                        if self.output_format == "hierarchical":
                            audit_path = self.generate_file_path(
                                entity, table_code, "audit", output_dir
                            )
                        else:
                            # Confiture: db/schema/40_audit/
                            audit_dir = Path("db/schema") / "40_audit"
                            audit_dir.mkdir(parents=True, exist_ok=True)
                            audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"

                        Path(audit_path).write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

                    # Register entity if using registry (only for derived codes)
                    if self.naming and not (entity.organization and entity.organization.table_code):
                        # Only auto-register entities with derived codes
                        # Explicit codes from external systems should not be registered
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
                    schema_output = self.schema_orchestrator.generate_split_schema(entity, with_audit_cascade)

                    # Write to Confiture directory structure
                    schema_base = Path("db/schema")

                    # 1. Table definition (db/schema/10_tables/)
                    table_dir = schema_base / "10_tables"
                    table_dir.mkdir(parents=True, exist_ok=True)
                    table_path = table_dir / f"{entity.name.lower()}.sql"
                    table_path.write_text(schema_output.table_sql)
                    generated_files.append(str(table_path))

                    # 2. Helper functions (db/schema/20_helpers/)
                    helpers_dir = schema_base / "20_helpers"
                    helpers_dir.mkdir(parents=True, exist_ok=True)
                    helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"
                    helpers_path.write_text(schema_output.helpers_sql)
                    generated_files.append(str(helpers_path))

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
                        generated_files.append(str(mutation_path))

                    # Write audit SQL if generated
                    if schema_output.audit_sql:
                        audit_dir = schema_base / "40_audit"
                        audit_dir.mkdir(parents=True, exist_ok=True)
                        audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"
                        audit_path.write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

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
                progress_update()  # Update progress bar

            except Exception as e:
                result.errors.append(f"Failed to generate {entity.name}: {e}")
                progress_update()  # Update progress even on error

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

        # Generate query patterns if requested
        if with_query_patterns:
            try:
                import yaml
                from src.generators.query_pattern_generator import QueryPatternGenerator
                from src.patterns.pattern_registry import PatternRegistry

                registry = PatternRegistry()
                pattern_generator = QueryPatternGenerator(registry)

                # Collect all query patterns from all entities
                all_patterns = []
                entity_pattern_map = {}  # pattern_name -> entity_data

                for entity_file in entity_files:
                    content = Path(entity_file).read_text()
                    entity_data = yaml.safe_load(content)

                    if "query_patterns" in entity_data and entity_data["query_patterns"]:
                        for pattern_config in entity_data["query_patterns"]:
                            all_patterns.append(pattern_config)
                            entity_pattern_map[pattern_config["name"]] = entity_data

                # Resolve dependencies and sort patterns
                if all_patterns:
                    from src.generators.schema.view_dependency import ViewDependencyResolver

                    resolver = ViewDependencyResolver()
                    sorted_pattern_names = resolver.sort(all_patterns)

                    # Generate SQL files in dependency order
                    for pattern_name in sorted_pattern_names:
                        # Find the pattern config and entity
                        pattern_config = next(p for p in all_patterns if p["name"] == pattern_name)
                        entity_data = entity_pattern_map[pattern_name]

                        # Generate SQL for this single pattern
                        sql_files = pattern_generator.generate_single(entity_data, pattern_config)

                        for sql_file in sql_files:
                            # Write to db/schema/02_query_side/{schema}/ directory
                            schema = entity_data.get("schema", "tenant")
                            schema_dir = Path("db/schema/02_query_side") / schema
                            schema_dir.mkdir(parents=True, exist_ok=True)
                            file_path = schema_dir / sql_file.name

                            migration = MigrationFile(
                                number=300,  # After table views
                                name=f"query_pattern_{sql_file.name}",
                                content=sql_file.content,
                                path=file_path,
                            )
                            result.migrations.append(migration)
            except Exception as e:
                result.errors.append(f"Failed to generate query patterns: {e}")

        # Write migrations to disk
        for migration in result.migrations:
            if migration.path:
                migration.path.write_text(migration.content)

        # Phase 3: Summary
        stats = self._calculate_generation_stats(result, generated_files)
        self.progress.summary(stats, output_dir, generated_files)

        return result

    def _calculate_generation_stats(self, result: GenerationResult, generated_files: list) -> dict:
        """Calculate statistics for the generation summary"""
        total_lines = 0
        tables = 0
        table_views = 0
        crud_actions = 0
        business_actions = 0

        for migration in result.migrations:
            if migration.content:
                lines = len(migration.content.split('\n'))
                total_lines += lines

                # Count different types of artifacts
                content_lower = migration.content.lower()
                if 'create table' in content_lower:
                    tables += 1
                if 'create view' in content_lower and 'tv_' in content_lower:
                    table_views += 1
                if any(action in content_lower for action in ['create_', 'update_', 'delete_']):
                    crud_actions += 1
                if 'function' in content_lower and not any(crud in content_lower for crud in ['create_', 'update_', 'delete_']):
                    business_actions += 1

        return {
            'total_files': len(generated_files),
            'total_lines': total_lines,
            'tables': tables,
            'table_views': table_views,
            'crud_actions': crud_actions,
            'business_actions': business_actions,
        }

        # Generate foundation first
        print(f"DEBUG: Generating foundation")
        foundation_sql = self.schema_orchestrator.generate_app_foundation_only()
        print(f"DEBUG: Foundation SQL generated, length: {len(foundation_sql) if foundation_sql else 0}")
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

        print(f"DEBUG: Parsed {len(entity_defs)} entity definitions")

        # Phase 2: Generate entity migrations with progress tracking
        entities = []
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity
                entity = convert_entity_definition_to_entity(entity_def)
                entities.append(entity)
            except Exception as e:
                result.errors.append(f"Failed to convert {entity_def.name}: {e}")

        print(f"DEBUG: Converted to {len(entities)} entities")

        # Use progress bar for generation
        generated_files = []
        print(f"DEBUG: Starting progress generation with {len(entities)} entities")
        if not entities:
            print("DEBUG: No entities to process")
            return result

        for entity, progress_update in self.progress.generation_progress(entities):
            print(f"DEBUG: Processing entity {entity.name}")
            try:
                # Find the corresponding entity_def for this entity
                entity_def = next(ed for ed in entity_defs if ed.name == entity.name)

                # Generate the entity migration (existing logic)
                if self.use_registry:
                    # Registry-based generation
                    table_code = self.get_table_code(entity)

                    # Generate SPLIT schema for Confiture
                    schema_output = self.schema_orchestrator.generate_split_schema(entity, with_audit_cascade)

                    # Determine output structure
                    if self.output_format == "hierarchical":

                        # Write to hierarchical directory structure
                        table_path = self.generate_file_path(
                            entity, table_code, "table", output_dir
                        )
                        helpers_path = self.generate_file_path(
                            entity, table_code, "function", output_dir
                        )
                        functions_dir = Path(
                            self.generate_file_path(entity, table_code, "function", output_dir)
                        ).parent

                        # Ensure directories exist
                        Path(table_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(helpers_path).parent.mkdir(parents=True, exist_ok=True)
                        functions_dir.mkdir(parents=True, exist_ok=True)
                        schema_base = None  # Not used in hierarchical mode
                    else:
                        # Write to Confiture directory structure
                        schema_base = Path("db/schema")

                        # 1. Table definition (db/schema/10_tables/)
                        table_dir = schema_base / "10_tables"
                        table_dir.mkdir(parents=True, exist_ok=True)
                        table_path = table_dir / f"{entity.name.lower()}.sql"

                        # 2. Helper functions (db/schema/20_helpers/)
                        helpers_dir = schema_base / "20_helpers"
                        helpers_dir.mkdir(parents=True, exist_ok=True)
                        helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"

                        # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                        functions_dir = schema_base / "30_functions"
                        functions_dir.mkdir(parents=True, exist_ok=True)

                    # Write table SQL
                    Path(table_path).write_text(schema_output.table_sql)
                    generated_files.append(table_path)

                    # Write helpers SQL
                    Path(helpers_path).write_text(schema_output.helpers_sql)
                    generated_files.append(helpers_path)

                    # Write mutations
                    for mutation in schema_output.mutations:
                        if self.output_format == "hierarchical":
                            from src.generators.naming_utils import camel_to_snake

                            entity_snake = camel_to_snake(entity.name)
                            mutation_path = (
                                functions_dir
                                / f"{table_code}_fn_{entity_snake}_{mutation.action_name}.sql"
                            )
                        else:
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
                        generated_files.append(str(mutation_path))

                    # Write audit SQL if generated
                    if schema_output.audit_sql:
                        if self.output_format == "hierarchical":
                            audit_path = self.generate_file_path(
                                entity, table_code, "audit", output_dir
                            )
                        else:
                            # Confiture: db/schema/40_audit/
                            audit_dir = Path("db/schema") / "40_audit"
                            audit_dir.mkdir(parents=True, exist_ok=True)
                            audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"

                        Path(audit_path).write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

                    # Register entity if using registry (only for derived codes)
                    if self.naming and not (entity.organization and entity.organization.table_code):
                        # Only auto-register entities with derived codes
                        # Explicit codes from external systems should not be registered
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
                    schema_output = self.schema_orchestrator.generate_split_schema(entity, with_audit_cascade)

                    # Write to Confiture directory structure
                    schema_base = Path("db/schema")

                    # 1. Table definition (db/schema/10_tables/)
                    table_dir = schema_base / "10_tables"
                    table_dir.mkdir(parents=True, exist_ok=True)
                    table_path = table_dir / f"{entity.name.lower()}.sql"
                    table_path.write_text(schema_output.table_sql)
                    generated_files.append(str(table_path))

                    # 2. Helper functions (db/schema/20_helpers/)
                    helpers_dir = schema_base / "20_helpers"
                    helpers_dir.mkdir(parents=True, exist_ok=True)
                    helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"
                    helpers_path.write_text(schema_output.helpers_sql)
                    generated_files.append(str(helpers_path))

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
                        generated_files.append(str(mutation_path))

                    # Write audit SQL if generated
                    if schema_output.audit_sql:
                        audit_dir = schema_base / "40_audit"
                        audit_dir.mkdir(parents=True, exist_ok=True)
                        audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"
                        audit_path.write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

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
                progress_update()  # Update progress bar

            except Exception as e:
                result.errors.append(f"Failed to generate {entity.name}: {e}")
                progress_update()  # Update progress even on error

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

        # Generate query patterns if requested
        if with_query_patterns:
            try:
                import yaml
                from src.generators.query_pattern_generator import QueryPatternGenerator
                from src.patterns.pattern_registry import PatternRegistry

                registry = PatternRegistry()
                pattern_generator = QueryPatternGenerator(registry)

                # Collect all query patterns from all entities
                all_patterns = []
                entity_pattern_map = {}  # pattern_name -> entity_data

                for entity_file in entity_files:
                    content = Path(entity_file).read_text()
                    entity_data = yaml.safe_load(content)

                    if "query_patterns" in entity_data and entity_data["query_patterns"]:
                        for pattern_config in entity_data["query_patterns"]:
                            all_patterns.append(pattern_config)
                            entity_pattern_map[pattern_config["name"]] = entity_data

                # Resolve dependencies and sort patterns
                if all_patterns:
                    from src.generators.schema.view_dependency import ViewDependencyResolver

                    resolver = ViewDependencyResolver()
                    sorted_pattern_names = resolver.sort(all_patterns)

                    # Generate SQL files in dependency order
                    for pattern_name in sorted_pattern_names:
                        # Find the pattern config and entity
                        pattern_config = next(p for p in all_patterns if p["name"] == pattern_name)
                        entity_data = entity_pattern_map[pattern_name]

                        # Generate SQL for this single pattern
                        sql_files = pattern_generator.generate_single(entity_data, pattern_config)

                        for sql_file in sql_files:
                            # Write to db/schema/02_query_side/{schema}/ directory
                            schema = entity_data.get("schema", "tenant")
                            schema_dir = Path("db/schema/02_query_side") / schema
                            schema_dir.mkdir(parents=True, exist_ok=True)
                            file_path = schema_dir / sql_file.name

                            migration = MigrationFile(
                                number=300,  # After table views
                                name=f"query_pattern_{sql_file.name}",
                                content=sql_file.content,
                                path=file_path,
                            )
                            result.migrations.append(migration)
            except Exception as e:
                result.errors.append(f"Failed to generate query patterns: {e}")

        # Write migrations to disk
        for migration in result.migrations:
            if migration.path:
                migration.path.write_text(migration.content)

        # Phase 3: Summary
        stats = self._calculate_generation_stats(result, generated_files)
        self.progress.summary(stats, output_dir, generated_files)

        return result
