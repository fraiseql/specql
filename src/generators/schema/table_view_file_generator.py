"""
Table View File Generator

Splits monolithic tv_ generation into individual entity files.
Maintains dependency order and generates complete SQL with FraiseQL annotations.
"""

import logging
from typing import Dict, List, Optional

from src.core.ast_models import EntityDefinition
from src.generators.schema.table_view_file import TableViewFile
from src.generators.schema.table_view_generator import TableViewGenerator
from src.generators.fraiseql.table_view_annotator import TableViewAnnotator
from src.generators.schema.table_view_dependency import TableViewDependencyResolver

logger = logging.getLogger(__name__)


class TableViewFileGenerator:
    """
    Generates individual tv_ table files instead of monolithic output.

    This class splits the generation of table views into separate files per entity,
    maintaining proper dependency order and including all necessary SQL components
    and FraiseQL annotations.

    Example:
        generator = TableViewFileGenerator([company_entity, contact_entity])
        files = generator.generate_files()
        # Returns [TableViewFile for tv_company, TableViewFile for tv_contact]
    """



    def __init__(self, entities: List[EntityDefinition]):
        """
        Initialize with entities to generate tv_ files for.

        Args:
            entities: List of entity definitions to generate tv_ files for.
                    Must not be None and should contain valid EntityDefinition objects.

        Raises:
            ValueError: If entities is None or contains invalid entities.
        """
        if entities is None:
            raise ValueError("entities cannot be None")

        self.entities = entities
        self.entity_map: Dict[str, EntityDefinition] = {e.name: e for e in entities}

        logger.debug(f"Initialized TableViewFileGenerator with {len(entities)} entities")

    def generate_files(self) -> List[TableViewFile]:
        """
        Generate individual tv_ files for all entities.

        Processes entities in dependency order to ensure proper creation sequence.
        Only generates files for entities that should have table views.

        Returns:
            List of TableViewFile objects, one per tv_ entity in dependency order.
            Empty list if no entities require table view generation.

        Raises:
            ValueError: If dependency resolution fails due to circular references.
        """
        if not self.entities:
            logger.debug("No entities provided, returning empty list")
            return []

        # Resolve dependency order for generation
        resolver = TableViewDependencyResolver(self.entities)
        generation_order = resolver.get_generation_order()

        logger.debug(f"Generation order: {generation_order}")

        files = []

        # Generate tv_ files in dependency order
        for entity_name in generation_order:
            entity = self.entity_map[entity_name]

            if not entity.should_generate_table_view:
                logger.debug(f"Skipping {entity_name} - should not generate table view")
                continue

            file = self._generate_single_file(entity)
            if file:
                files.append(file)
                logger.debug(f"Generated file for {entity_name}: {file.name}")
            else:
                logger.warning(f"Failed to generate file for {entity_name}")

        logger.info(f"Generated {len(files)} table view files")
        return files

    def _generate_single_file(self, entity: EntityDefinition) -> Optional[TableViewFile]:
        """
        Generate a single tv_ file for one entity.

        Args:
            entity: Entity to generate tv_ file for. Must be a valid EntityDefinition.

        Returns:
            TableViewFile if generation successful, None if schema generation fails.
        """
        logger.debug(f"Generating file for entity: {entity.name}")

        # Generate table view schema
        tv_schema = self._generate_table_view_schema(entity)
        if not tv_schema:
            logger.warning(f"Failed to generate schema for {entity.name}")
            return None

        # Generate FraiseQL annotations
        annotations = self._generate_fraiseql_annotations(entity)

        # Combine all content parts
        content = self._combine_content_parts(entity, tv_schema, annotations)

        # Generate read-side code
        code = self._generate_code_for_entity(entity)

        # Determine dependencies
        dependencies = self._get_dependencies(entity)

        file = TableViewFile(
            code=code,
            name=f"tv_{entity.name.lower()}",
            content=content,
            dependencies=dependencies
        )

        logger.debug(f"Successfully generated file: {file.name}")
        return file

    def _generate_table_view_schema(self, entity: EntityDefinition) -> Optional[str]:
        """
        Generate the table view schema for an entity.

        Args:
            entity: Entity to generate schema for.

        Returns:
            SQL schema string, or None if generation fails.
        """
        try:
            generator = TableViewGenerator(entity, self.entity_map)
            return generator.generate_schema()
        except Exception as e:
            logger.error(f"Error generating schema for {entity.name}: {e}")
            return None

    def _generate_fraiseql_annotations(self, entity: EntityDefinition) -> str:
        """
        Generate FraiseQL annotations for an entity.

        Args:
            entity: Entity to generate annotations for.

        Returns:
            Annotations string, empty if no table_views config or generation fails.
        """
        if not entity.table_views:
            return ""

        try:
            annotator = TableViewAnnotator(entity)
            return annotator.generate_annotations()
        except Exception as e:
            logger.warning(f"Error generating annotations for {entity.name}: {e}")
            return ""

    def _combine_content_parts(self, entity: EntityDefinition, tv_schema: str, annotations: str) -> str:
        """
        Combine all content parts into final file content.

        Args:
            entity: Entity being processed.
            tv_schema: Table view schema SQL.
            annotations: FraiseQL annotations.

        Returns:
            Combined content string.
        """
        parts = []

        # Table view schema with header
        table_name = f"{entity.schema}.tv_{entity.name.lower()}"
        parts.append(f"-- Table View: {table_name}\n{tv_schema}")

        # FraiseQL annotations
        if annotations:
            parts.append(f"-- FraiseQL Annotations: {table_name}\n{annotations}")

        return "\n\n".join(parts)

    def _generate_code_for_entity(self, entity: EntityDefinition) -> str:
        """
        Generate read-side code for entity.

        Args:
            entity: Entity to generate code for.

        Returns:
            7-digit read-side code string.
        """
        from src.application.services.domain_service_factory import get_domain_service

        # Determine domain and subdomain
        domain_name = entity.schema
        subdomain_name = entity.subdomain

        # If subdomain not specified, try to infer it
        if not subdomain_name:
            try:
                service = get_domain_service()
                domain = service.repository.find_by_name(domain_name)
                if domain and domain.subdomains:
                    # Use first subdomain as default
                    subdomain_name = list(domain.subdomains.values())[0].subdomain_name
                else:
                    subdomain_name = "core"
            except Exception as e:
                logger.warning(f"Could not infer subdomain for {entity.name}: {e}, using 'core'")
                subdomain_name = "core"

        # Generate read-side code (simplified - not stored in registry)
        try:
            # Get domain number
            service = get_domain_service()
            domain = service.repository.find_by_name(domain_name)
            domain_num = domain.domain_number.value if domain else "0"

            # Get subdomain number (simplified mapping)
            subdomain_num = "00"  # Default
            if domain:
                for sd in domain.subdomains.values():
                    if sd.subdomain_name == subdomain_name:
                        subdomain_num = sd.subdomain_number
                        break

            # Generate simple read-side code: 02 + domain + subdomain + entity_sequence + file
            # For now, use a simple incrementing pattern
            entity_hash = hash(entity.name.lower()) % 100
            code = f"02{domain_num}{subdomain_num}{entity_hash:02d}0"

            logger.debug(f"Generated code for {entity.name}: {code}")
            return code
        except Exception as e:
            logger.error(f"Failed to generate code for {entity.name}: {e}")
            # Fallback to a default pattern
            return f"02{domain_name[:1].upper()}{subdomain_name[:2].upper()}000"

    def _get_dependencies(self, entity: EntityDefinition) -> List[str]:
        """
        Get list of tv_ dependencies for this entity.

        Dependencies are determined by foreign key references to other entities
        that also generate table views.

        Args:
            entity: Entity to check dependencies for.

        Returns:
            List of tv_ view names this entity depends on, in alphabetical order.
        """
        dependencies = set()

        # Check foreign key references
        for field in entity.fields.values():
            if field.is_reference() and field.reference_entity:
                ref_entity_name = field.reference_entity
                if ref_entity_name in self.entity_map:
                    ref_entity = self.entity_map[ref_entity_name]
                    if ref_entity.should_generate_table_view:
                        dependencies.add(f"tv_{ref_entity_name.lower()}")

        # Return sorted for consistency
        sorted_deps = sorted(dependencies)
        logger.debug(f"Dependencies for {entity.name}: {sorted_deps}")
        return sorted_deps

    def write_files_to_disk(self, output_dir: str = "generated", dry_run: bool = False) -> List[str]:
        """
        Write generated tv_ files to disk using hierarchical structure.

        Args:
            output_dir: Base output directory for generated files
            dry_run: If True, only log operations without writing files

        Returns:
            List of file paths that were written (or would be written in dry-run)

        Raises:
            ValueError: If file generation fails
        """
        from src.generators.schema.hierarchical_file_writer import HierarchicalFileWriter, FileSpec
        from src.generators.schema.read_side_path_generator import ReadSidePathGenerator

        # Generate the files
        files = self.generate_files()
        if not files:
            logger.info("No files to write")
            return []

        # Create file specs for HierarchicalFileWriter
        file_specs = []
        for file in files:
            spec = FileSpec(
                code=file.code,
                name=file.name,
                content=file.content,
                layer="read_side"
            )
            file_specs.append(spec)

        # Create path generator and writer
        path_generator = ReadSidePathGenerator(base_dir=output_dir)
        writer = HierarchicalFileWriter(path_generator, dry_run=dry_run)

        # Write files
        try:
            written_paths = writer.write_files(file_specs)
            logger.info(f"Successfully wrote {len(written_paths)} files to {output_dir}")
            return [str(path) for path in written_paths]
        except Exception as e:
            logger.error(f"Failed to write files: {e}")
            raise ValueError(f"File writing failed: {e}") from e