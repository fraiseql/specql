"""Pattern import functionality"""
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

from src.application.services.pattern_service import PatternService


class PatternImporter:
    """Imports patterns from various formats"""

    def __init__(self, service: PatternService):
        self.service = service

    def import_from_yaml(
        self,
        input_path: Path,
        skip_existing: bool = True,
        generate_embeddings: bool = True
    ) -> int:
        """
        Import patterns from YAML file

        Args:
            input_path: Input file path
            skip_existing: Skip patterns that already exist
            generate_embeddings: Generate embeddings for imported patterns

        Returns:
            Number of patterns imported
        """
        with open(input_path) as f:
            data = yaml.safe_load(f)

        return self._import_patterns(
            data["patterns"],
            skip_existing=skip_existing,
            generate_embeddings=generate_embeddings
        )

    def import_from_json(
        self,
        input_path: Path,
        skip_existing: bool = True,
        generate_embeddings: bool = True
    ) -> int:
        """Import patterns from JSON file"""
        with open(input_path) as f:
            data = json.load(f)

        return self._import_patterns(
            data["patterns"],
            skip_existing=skip_existing,
            generate_embeddings=generate_embeddings
        )

    def _import_patterns(
        self,
        patterns_data: List[Dict[str, Any]],
        skip_existing: bool,
        generate_embeddings: bool
    ) -> int:
        """Import list of patterns"""
        imported_count = 0

        for pattern_data in patterns_data:
            # Validate required fields
            self._validate_pattern_data(pattern_data)

            # Check if exists
            try:
                existing = self.service.get_pattern_by_name(pattern_data["name"])
                if existing and skip_existing:
                    continue
            except ValueError:
                # Pattern doesn't exist, proceed with import
                existing = None

            # Create or update pattern
            self.service.create_pattern(
                name=pattern_data["name"],
                category=pattern_data["category"],
                description=pattern_data["description"],
                parameters=pattern_data.get("parameters", {}),
                implementation=pattern_data.get("implementation", {}),
                complexity_score=pattern_data.get("complexity_score", 1),
                source_type="migrated",
                generate_embedding=generate_embeddings
            )

            imported_count += 1

        return imported_count

    def _validate_pattern_data(self, pattern_data: Dict[str, Any]) -> None:
        """Validate pattern data structure"""
        required_fields = ["name", "category", "description"]

        for field in required_fields:
            if field not in pattern_data:
                raise ValueError(f"Invalid pattern: missing required field '{field}'")

        # Validate types
        if not isinstance(pattern_data["name"], str):
            raise ValueError("Pattern name must be a string")

        if not isinstance(pattern_data["category"], str):
            raise ValueError("Pattern category must be a string")