"""Pattern registry for loading and managing schema patterns."""

from pathlib import Path
from typing import Any

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)


class PatternRegistry:
    """Registry for loading and managing schema patterns."""

    def __init__(self, pattern_dir: Path = Path("stdlib/schema")):
        self.pattern_dir = pattern_dir
        self.patterns: dict[str, dict[str, Any]] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load all pattern specifications from stdlib/schema/."""
        if not self.pattern_dir.exists():
            raise RuntimeError(f"Pattern directory not found: {self.pattern_dir}")

        # Load patterns from root directory
        for pattern_file in self.pattern_dir.glob("*.yaml"):
            self._load_pattern_file(pattern_file)

        # Load patterns from subdirectories
        for subdir in self.pattern_dir.iterdir():
            if subdir.is_dir():
                for pattern_file in subdir.glob("*.yaml"):
                    self._load_pattern_file(pattern_file)

    def _load_pattern_file(self, pattern_file: Path) -> None:
        """Load a single pattern file."""
        try:
            with open(pattern_file) as f:
                spec = yaml.safe_load(f)

            if not spec or "pattern" not in spec:
                return  # Skip invalid files

            pattern_name = spec["pattern"]
            self.patterns[pattern_name] = spec

        except Exception as e:
            # Log but don't fail - allow partial loading
            logger.warning(f"Failed to load pattern {pattern_file}: {e}")

    def get_pattern(self, pattern_type: str) -> dict[str, Any]:
        """Get pattern specification by type."""
        if pattern_type not in self.patterns:
            available = list(self.patterns.keys())
            raise ValueError(f"Unknown pattern: {pattern_type}. Available: {available}")
        return self.patterns[pattern_type]

    def list_patterns(self) -> list[str]:
        """List all available pattern types."""
        return list(self.patterns.keys())
