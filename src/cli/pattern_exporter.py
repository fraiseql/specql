"""Pattern export functionality"""
import yaml
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.application.services.pattern_service import PatternService
from src.domain.entities.pattern import Pattern


class PatternExporter:
    """Exports patterns to various formats"""

    def __init__(self, service: PatternService):
        self.service = service

    def export_to_yaml(
        self,
        output_path: Path,
        category: Optional[str] = None,
        include_embeddings: bool = False
    ) -> None:
        """
        Export patterns to YAML format

        Args:
            output_path: Output file path
            category: Optional category filter
            include_embeddings: Whether to include embeddings (default: False)
        """
        patterns = self._get_patterns(category)
        export_data = self._prepare_export_data(patterns, include_embeddings)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    def export_to_json(
        self,
        output_path: Path,
        category: Optional[str] = None,
        include_embeddings: bool = False
    ) -> None:
        """
        Export patterns to JSON format

        Args:
            output_path: Output file path
            category: Optional category filter
            include_embeddings: Whether to include embeddings
        """
        patterns = self._get_patterns(category)
        export_data = self._prepare_export_data(patterns, include_embeddings)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

    def _get_patterns(self, category: Optional[str] = None) -> List[Pattern]:
        """Get patterns to export"""
        if category:
            return self.service.find_patterns_by_category(category)
        else:
            return self.service.list_all_patterns()

    def _prepare_export_data(
        self,
        patterns: List[Pattern],
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """
        Prepare export data structure

        Returns:
            {
                "metadata": {...},
                "patterns": [...]
            }
        """
        return {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "total_patterns": len(patterns),
                "format_version": "1.0.0",
                "source": "SpecQL Pattern Library"
            },
            "patterns": [
                self._pattern_to_dict(pattern, include_embeddings)
                for pattern in patterns
            ]
        }

    def _pattern_to_dict(
        self,
        pattern: Pattern,
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """Convert pattern to dictionary for export"""
        data = {
            "name": pattern.name,
            "category": pattern.category.value,
            "description": pattern.description,
            "parameters": pattern.parameters,
            "implementation": pattern.implementation,
            "complexity_score": pattern.complexity_score,
            "source_type": pattern.source_type.value,
        }

        # Optionally include embeddings
        if include_embeddings and pattern.embedding:
            data["embedding"] = pattern.embedding

        # Include deprecation info if deprecated
        if pattern.deprecated:
            data["deprecated"] = True
            data["deprecated_reason"] = pattern.deprecated_reason
            data["replacement_pattern_id"] = pattern.replacement_pattern_id

        return data