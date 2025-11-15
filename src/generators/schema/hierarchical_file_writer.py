"""
Hierarchical File Writer

Unified file writer for both write-side and read-side hierarchical generation.
Provides protocol-based path generation and file writing capabilities.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Protocol

logger = logging.getLogger(__name__)


@dataclass
class FileSpec:
    """
    Specification for a file to be written

    Contains all information needed to write a file to the correct location.
    """
    code: str  # Table/view code (6-digit for all layers)
    name: str  # File name without extension (e.g., "tb_contact", "tv_contact")
    content: str  # Complete file content
    layer: str  # Schema layer ("write_side", "read_side")


class PathGenerator(Protocol):
    """
    Protocol for generating file paths from file specifications

    Implementations should provide path generation logic for different schema layers.
    """

    def generate_path(self, file_spec: FileSpec) -> Path:
        """
        Generate hierarchical file path for the given file specification

        Args:
            file_spec: File specification containing code, name, content, layer

        Returns:
            Path object for the file location

        Raises:
            ValueError: If path cannot be generated
        """
        ...


class HierarchicalFileWriter:
    """
    Unified file writer for hierarchical generation

    Handles writing files for both write-side and read-side using protocol-based
    path generation. Supports dry-run mode for previewing file operations.
    """

    def __init__(self, path_generator: PathGenerator, dry_run: bool = False):
        """
        Initialize with path generator

        Args:
            path_generator: Implementation of PathGenerator protocol
            dry_run: If True, only log operations without writing files
        """
        self.path_generator = path_generator
        self.dry_run = dry_run

    def write_files(self, file_specs: List[FileSpec]) -> List[Path]:
        """
        Write multiple files to their hierarchical locations

        Args:
            file_specs: List of file specifications to write

        Returns:
            List of paths where files were written (or would be written in dry-run)

        Raises:
            ValueError: If any file specification is invalid
        """
        if not file_specs:
            logger.debug("No file specs provided, returning empty list")
            return []

        written_paths = []

        for file_spec in file_specs:
            try:
                path = self.write_single_file(file_spec)
                written_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to write file for {file_spec.name}: {e}")
                raise ValueError(f"File writing failed for {file_spec.name}: {e}") from e

        logger.info(f"Successfully processed {len(written_paths)} files")
        return written_paths

    def write_single_file(self, file_spec: FileSpec) -> Path:
        """
        Write a single file to its hierarchical location

        Args:
            file_spec: File specification to write

        Returns:
            Path where file was written (or would be written in dry-run)

        Raises:
            ValueError: If file specification is invalid
        """
        # Validate file spec
        self._validate_file_spec(file_spec)

        # Generate path
        try:
            path = self.path_generator.generate_path(file_spec)
        except Exception as e:
            raise ValueError(f"Path generation failed for {file_spec.name}: {e}") from e

        # Write file (or simulate in dry-run)
        if self.dry_run:
            logger.info(f"DRY RUN: Would write {len(file_spec.content)} chars to {path}")
        else:
            try:
                # Ensure parent directory exists
                path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(file_spec.content)

                logger.debug(f"Written {len(file_spec.content)} chars to {path}")

            except Exception as e:
                raise ValueError(f"File write failed for {path}: {e}") from e

        return path

    def _validate_file_spec(self, file_spec: FileSpec):
        """
        Validate file specification

        Args:
            file_spec: File spec to validate

        Raises:
            ValueError: If validation fails
        """
        if not file_spec.code:
            raise ValueError("File spec must have a code")

        if not file_spec.name:
            raise ValueError("File spec must have a name")

        if file_spec.content is None:
            raise ValueError("File spec must have content (can be empty string)")

        if file_spec.layer not in ["write_side", "read_side", "functions"]:
            raise ValueError(f"Invalid layer '{file_spec.layer}'. Must be 'write_side', 'read_side', or 'functions'")

        # Validate code format based on layer (all layers now use 6-digit codes)
        if len(file_spec.code) != 6:
            raise ValueError(
                f"All codes must be 6 digits, got {len(file_spec.code)} for {file_spec.layer}: {file_spec.code}"
            )
