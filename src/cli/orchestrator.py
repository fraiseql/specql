"""CLI Orchestrator for unified generation workflows."""

from dataclasses import dataclass
from pathlib import Path

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
        framework: str = "fraiseql",
        enable_performance_monitoring: bool = False,
    ):
        self.parser = SpecQLParser()
        try:
            self.progress = SpecQLProgress(verbose=verbose)
        except Exception:
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

        # Performance monitoring
        self.perf_monitor = None
        if enable_performance_monitoring:
            from src.utils.performance_monitor import get_performance_monitor

            self.perf_monitor = get_performance_monitor()

        # NEW: Registry integration - conditionally create SchemaOrchestrator
        if self.use_registry:
            self.naming = NamingConventions()
            self.schema_orchestrator = SchemaOrchestrator(
                naming_conventions=self.naming,
                enable_performance_monitoring=enable_performance_monitoring,
            )
        else:
            self.naming = None
            self.schema_orchestrator = SchemaOrchestrator(
                naming_conventions=None,
                enable_performance_monitoring=enable_performance_monitoring,
            )

    def get_table_code(self, entity) -> str:
        """
        Derive table code from registry

        Returns:
            6-character hexadecimal table code (e.g., "012311")
        """
        if not self.use_registry or not self.naming:
            raise ValueError(
                "Registry not enabled. Use CLIOrchestrator(use_registry=True)"
            )

        return self.naming.get_table_code(
            entity
        )  # Respects priority: explicit → registry → derive

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
                    entity=entity,
                    table_code=table_code,
                    file_type=file_type,
                    base_dir=base_dir,
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
        confiture_map = {
            "table": "10_tables",
            "function": "30_functions",
            "comment": "40_metadata",
        }

        dir_name = confiture_map.get(file_type, "10_tables")
        filename = f"{entity.name.lower()}.sql"

        return f"db/schema/{dir_name}/{filename}"

    def _generate_tv_file_path(self, tv_file, output_path) -> Path:
        """
        Generate hierarchical path for tv_ table file using HierarchicalFileWriter.

        Args:
            tv_file: TableViewFile object
            output_path: Base output path

        Returns:
            Path to the tv_ file
        """
        from src.generators.schema.hierarchical_file_writer import FileSpec
        from src.generators.schema.read_side_path_generator import ReadSidePathGenerator

        # Create file spec for the tv_ file
        file_spec = FileSpec(
            code=tv_file.code,
            name=tv_file.name,
            content=tv_file.content,
            layer="read_side",
        )

        # Create path generator to get the path
        path_generator = ReadSidePathGenerator(base_dir=str(output_path))

        # Generate path without writing
        try:
            path = path_generator.generate_path(file_spec)
            return path
        except Exception as e:
            # Fallback to legacy path if hierarchical generation fails
            print(
                f"DEBUG: Hierarchical path generation failed for {tv_file.name}: {e}, using legacy path"
            )
            return output_path / f"{tv_file.code}_{tv_file.name}.sql"

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
        dry_run: bool = False,
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

        # Phase 1: Scan entity files
        self.progress.scan_phase(entity_files)

        result = GenerationResult(migrations=[], errors=[], warnings=[])
        output_path = Path(output_dir)
        if not dry_run:
            output_path.mkdir(parents=True, exist_ok=True)
        generated_files = []

        # Foundation only mode
        if foundation_only:
            foundation_sql = self.schema_orchestrator.generate_app_foundation_only(
                with_outbox
            )
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
        # print("DEBUG: Generating foundation")
        foundation_sql = self.schema_orchestrator.generate_app_foundation_only()
        if foundation_sql:
            if self.output_format == "confiture":
                # For Confiture: write to db/schema/00_foundation/
                foundation_dir = Path("db/schema/00_foundation")
                foundation_dir.mkdir(parents=True, exist_ok=True)
                foundation_path = foundation_dir / "000_app_foundation.sql"
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
            # Write the file
            if not dry_run and migration.path:
                migration.path.write_text(migration.content)

        # Parse all entities
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = self.parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                result.errors.append(f"Failed to parse {entity_file}: {e}")

        # Convert entities
        entities = []
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity

                entity = convert_entity_definition_to_entity(entity_def)
                entities.append(entity)
            except Exception as e:
                result.errors.append(f"Failed to convert {entity_def.name}: {e}")

        # Use progress bar for generation
        if not entities:
            # Phase 3: Summary
            stats = self._calculate_generation_stats(result, generated_files)
            self.progress.summary(stats, output_dir, generated_files)
            return result

        for entity, progress_update in self.progress.generation_progress(entities):
            try:
                # Find the corresponding entity_def for this entity
                entity_def = next(ed for ed in entity_defs if ed.name == entity.name)

                # Generate the entity migration (existing logic)
                if self.use_registry:
                    # Registry-based generation
                    table_code = self.get_table_code(entity)

                    # Generate SPLIT schema for Confiture
                    schema_output = self.schema_orchestrator.generate_split_schema(
                        entity, with_audit_cascade
                    )

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
                            self.generate_file_path(
                                entity, table_code, "function", output_dir
                            )
                        ).parent

                        # Ensure directories exist
                        if not dry_run:
                            Path(table_path).parent.mkdir(parents=True, exist_ok=True)
                            Path(helpers_path).parent.mkdir(parents=True, exist_ok=True)
                            functions_dir.mkdir(parents=True, exist_ok=True)
                        schema_base = None  # Not used in hierarchical mode
                    else:
                        # Write to Confiture directory structure
                        schema_base = Path("db/schema")

                        # 1. Table definition (db/schema/10_tables/)
                        table_dir = schema_base / "10_tables"
                        if not dry_run:
                            table_dir.mkdir(parents=True, exist_ok=True)
                        table_path = table_dir / f"{entity.name.lower()}.sql"

                        # 2. Helper functions (db/schema/20_helpers/)
                        helpers_dir = schema_base / "20_helpers"
                        if not dry_run:
                            helpers_dir.mkdir(parents=True, exist_ok=True)
                        helpers_path = (
                            helpers_dir / f"{entity.name.lower()}_helpers.sql"
                        )

                        # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                        functions_dir = schema_base / "30_functions"
                        if not dry_run:
                            functions_dir.mkdir(parents=True, exist_ok=True)

                    # Write table SQL
                    if not dry_run:
                        Path(table_path).write_text(schema_output.table_sql)
                    generated_files.append(table_path)

                    # Write helpers SQL
                    if not dry_run:
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
                            mutation_path = (
                                functions_dir / f"{mutation.action_name}.sql"
                            )

                        mutation_content = f"""-- ============================================================================
-- Mutation: {mutation.action_name}
-- Entity: {entity.name}
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

{mutation.app_wrapper_sql}

{mutation.core_logic_sql}

{mutation.fraiseql_comments_sql}
"""
                        if not dry_run:
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
                            if not dry_run:
                                audit_dir.mkdir(parents=True, exist_ok=True)
                            audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"

                        if not dry_run:
                            Path(audit_path).write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

                    # Register entity if using registry (only for derived codes)
                    if self.naming and not (
                        entity.organization and entity.organization.table_code
                    ):
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
                    schema_output = self.schema_orchestrator.generate_split_schema(
                        entity, with_audit_cascade
                    )

                    # Write to Confiture directory structure
                    schema_base = Path("db/schema")

                    # 1. Table definition (db/schema/10_tables/)
                    table_dir = schema_base / "10_tables"
                    if not dry_run:
                        table_dir.mkdir(parents=True, exist_ok=True)
                    table_path = table_dir / f"{entity.name.lower()}.sql"
                    if not dry_run:
                        table_path.write_text(schema_output.table_sql)
                    generated_files.append(str(table_path))

                    # 2. Helper functions (db/schema/20_helpers/)
                    helpers_dir = schema_base / "20_helpers"
                    if not dry_run:
                        helpers_dir.mkdir(parents=True, exist_ok=True)
                    helpers_path = helpers_dir / f"{entity.name.lower()}_helpers.sql"
                    if not dry_run:
                        helpers_path.write_text(schema_output.helpers_sql)
                    generated_files.append(str(helpers_path))

                    # 3. Mutations - ONE FILE PER MUTATION (db/schema/30_functions/)
                    functions_dir = schema_base / "30_functions"
                    if not dry_run:
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
                        if not dry_run:
                            mutation_path.write_text(mutation_content)
                        generated_files.append(str(mutation_path))

                    # Write audit SQL if generated
                    if schema_output.audit_sql:
                        audit_dir = schema_base / "40_audit"
                        if not dry_run:
                            audit_dir.mkdir(parents=True, exist_ok=True)
                        audit_path = audit_dir / f"{entity.name.lower()}_audit.sql"
                        if not dry_run:
                            audit_path.write_text(schema_output.audit_sql)
                        generated_files.append(str(audit_path))

                    # Use sequential numbering for backward compatibility
                    entity_count = len(
                        [m for m in result.migrations if m.number >= 100]
                    )
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
        if include_tv:
            # Generate table views
            tv_result = self.generate_read_side_hierarchical(
                entity_files, output_dir, dry_run=dry_run
            )
            result.migrations.extend(tv_result.migrations)
            result.errors.extend(tv_result.errors)
            result.warnings.extend(tv_result.warnings)
            generated_files.extend(
                tv_result.generated_files
                if hasattr(tv_result, "generated_files")
                else []
            )

        # Phase 3: Summary
        stats = self._calculate_generation_stats(result, generated_files)
        self.progress.summary(stats, output_dir, generated_files)

        return result

    def generate_hierarchical(
        self,
        entity_files: list[str],
        output_dir: str = "generated",
        dry_run: bool = False,
    ) -> GenerationResult:
        """
        Generate files using hierarchical structure for both write-side and read-side.

        This is the unified entry point for hierarchical generation that uses
        HierarchicalFileWriter for consistent path generation and file writing.

        Args:
            entity_files: List of SpecQL YAML file paths
            output_dir: Base output directory for generated files
            dry_run: If True, only show what would be generated without writing files

        Returns:
            GenerationResult with migration files and any errors/warnings
        """
        print(
            f"DEBUG: generate_hierarchical called with {len(entity_files)} files, dry_run={dry_run}"
        )

        result = GenerationResult(migrations=[], errors=[], warnings=[])
        Path(output_dir)

        # Parse all entities first
        entity_defs = []
        for entity_file in entity_files:
            try:
                content = Path(entity_file).read_text()
                entity_def = self.parser.parse(content)
                entity_defs.append(entity_def)
            except Exception as e:
                result.errors.append(f"Failed to parse {entity_file}: {e}")

        if result.errors:
            return result

        # Convert to Entity objects
        entities = []
        for entity_def in entity_defs:
            try:
                from src.cli.generate import convert_entity_definition_to_entity

                entity = convert_entity_definition_to_entity(entity_def)
                entities.append(entity)
            except Exception as e:
                result.errors.append(f"Failed to convert {entity_def.name}: {e}")

        if result.errors:
            return result

        # Generate write-side files hierarchically
        write_result = self.generate_write_side_hierarchical(
            entities, output_dir, dry_run
        )
        result.migrations.extend(write_result.migrations)
        result.errors.extend(write_result.errors)
        result.warnings.extend(write_result.warnings)

        # Generate read-side files hierarchically
        read_result = self.generate_read_side_hierarchical(
            entity_defs, output_dir, dry_run
        )
        result.migrations.extend(read_result.migrations)
        result.errors.extend(read_result.errors)
        result.warnings.extend(read_result.warnings)

        return result

    def generate_write_side_hierarchical(
        self, entities: list, output_dir: str = "generated", dry_run: bool = False
    ) -> GenerationResult:
        """
        Generate write-side files (tables, functions) using hierarchical structure.

        Args:
            entities: List of Entity objects
            output_dir: Base output directory
            dry_run: If True, only show what would be generated

        Returns:
            GenerationResult with generated files
        """
        from src.generators.schema.hierarchical_file_writer import (
            HierarchicalFileWriter,
            FileSpec,
        )
        from src.generators.schema.write_side_path_generator import (
            WriteSidePathGenerator,
        )

        result = GenerationResult(migrations=[], errors=[], warnings=[])

        if not entities:
            return result

        # Create path generator and writer
        path_generator = WriteSidePathGenerator(base_dir=output_dir)
        writer = HierarchicalFileWriter(path_generator, dry_run=dry_run)

        file_specs = []

        for entity in entities:
            try:
                # Get table code (6 digits with file sequence 1 for main table)
                table_code = self.get_table_code(entity)

                # Extract base code (first 5 digits) for generating additional file codes
                base_code = table_code[:5]  # 6-digit code, base is first 5 digits

                # Generate schema output
                schema_output = self.schema_orchestrator.generate_split_schema(
                    entity, with_audit_cascade=False
                )

                # File sequence tracking for this entity
                file_seq = 1

                # Create file specs for table, helpers, and functions
                # Table file (sequence 1)
                table_spec = FileSpec(
                    code=f"{base_code}{file_seq}",  # e.g., "0123611"
                    name=f"tb_{entity.name.lower()}",
                    content=schema_output.table_sql,
                    layer="write_side",
                )
                file_specs.append(table_spec)
                file_seq += 1

                # Helper functions file (sequence 2)
                if schema_output.helpers_sql:
                    helpers_spec = FileSpec(
                        code=f"{base_code}{file_seq}",  # e.g., "0123612"
                        name=f"tb_{entity.name.lower()}_helpers",
                        content=schema_output.helpers_sql,
                        layer="write_side",
                    )
                    file_specs.append(helpers_spec)
                    file_seq += 1

                # Individual function files (sequences 3, 4, 5, ...)
                for mutation in schema_output.mutations:
                    func_spec = FileSpec(
                        code=f"{base_code}{file_seq}",  # e.g., "0123613", "0123614", ...
                        name=f"fn_{entity.name.lower()}_{mutation.action_name}",
                        content=mutation.app_wrapper_sql
                        + "\n\n"
                        + mutation.core_logic_sql
                        + "\n\n"
                        + mutation.fraiseql_comments_sql,
                        layer="write_side",
                    )
                    file_specs.append(func_spec)
                    file_seq += 1

                # Audit file if present
                if schema_output.audit_sql:
                    audit_spec = FileSpec(
                        code=f"{base_code}{file_seq}",  # e.g., "0123615"
                        name=f"tb_{entity.name.lower()}_audit",
                        content=schema_output.audit_sql,
                        layer="write_side",
                    )
                    file_specs.append(audit_spec)
                    file_seq += 1

            except Exception as e:
                result.errors.append(
                    f"Failed to generate write-side files for {entity.name}: {e}"
                )

        # Write all files
        try:
            written_paths = writer.write_files(file_specs)

            # Create MigrationFile objects for tracking
            for path in written_paths:
                migration = MigrationFile(
                    number=0,  # Not used in hierarchical mode
                    name=path.name,
                    content="",  # Content already written
                    path=path,
                )
                result.migrations.append(migration)

        except Exception as e:
            result.errors.append(f"Failed to write write-side files: {e}")

        return result

    def generate_read_side_hierarchical(
        self, entity_defs: list, output_dir: str = "generated", dry_run: bool = False
    ) -> GenerationResult:
        """
        Generate read-side files (table views) using hierarchical structure.

        Args:
            entity_defs: List of EntityDefinition objects
            output_dir: Base output directory
            dry_run: If True, only show what would be generated

        Returns:
            GenerationResult with generated files
        """
        from src.generators.schema.table_view_file_generator import (
            TableViewFileGenerator,
        )

        result = GenerationResult(migrations=[], errors=[], warnings=[])

        if not entity_defs:
            return result

        try:
            # Use TableViewFileGenerator which already integrates with HierarchicalFileWriter
            generator = TableViewFileGenerator(entity_defs)
            written_paths = generator.write_files_to_disk(
                output_dir=output_dir, dry_run=dry_run
            )

            # Create MigrationFile objects for tracking
            for path_str in written_paths:
                path = Path(path_str)
                migration = MigrationFile(
                    number=0,  # Not used in hierarchical mode
                    name=path.name,
                    content="",  # Content already written
                    path=path,
                )
                result.migrations.append(migration)

        except Exception as e:
            result.errors.append(f"Failed to generate read-side files: {e}")

        return result

    def _calculate_generation_stats(
        self, result: GenerationResult, generated_files: list
    ) -> dict:
        """Calculate statistics for the generation summary"""
        total_lines = 0
        tables = 0
        table_views = 0
        crud_actions = 0
        business_actions = 0

        for migration in result.migrations:
            if migration.content:
                lines = len(migration.content.split("\n"))
                total_lines += lines

                # Count different types of artifacts
                content_lower = migration.content.lower()
                if "create table" in content_lower:
                    tables += 1
                if "create view" in content_lower and "tv_" in content_lower:
                    table_views += 1
                if any(
                    action in content_lower
                    for action in ["create_", "update_", "delete_"]
                ):
                    crud_actions += 1
                if "function" in content_lower and not any(
                    crud in content_lower for crud in ["create_", "update_", "delete_"]
                ):
                    business_actions += 1

        return {
            "total_files": len(generated_files),
            "total_lines": total_lines,
            "tables": tables,
            "table_views": table_views,
            "crud_actions": crud_actions,
            "business_actions": business_actions,
        }
