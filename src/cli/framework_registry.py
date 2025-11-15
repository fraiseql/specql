"""
Framework registry and detection logic for SpecQL CLI

This module provides utilities for framework detection, validation,
and selection based on project context and user preferences.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from src.cli.framework_defaults import (
    get_framework_defaults,
    get_available_frameworks,
    apply_dev_mode_overrides,
    validate_framework_option,
    get_output_dir_for_framework,
)


class FrameworkRegistry:
    """Registry for managing framework-specific configurations and detection"""

    def __init__(self):
        self._frameworks = get_available_frameworks()

    def list_frameworks(self) -> Dict[str, str]:
        """List all available frameworks with descriptions"""
        return self._frameworks.copy()

    def is_valid_framework(self, framework: str) -> bool:
        """Check if a framework name is valid"""
        return framework.lower() in self._frameworks

    def get_framework_description(self, framework: str) -> Optional[str]:
        """Get description for a framework"""
        return self._frameworks.get(framework.lower())

    def detect_framework_from_project(self) -> Optional[str]:
        """
        Attempt to detect the target framework from project structure.

        Detection logic:
        1. Check for framework-specific files/directories
        2. Check for dependency files (requirements.txt, pyproject.toml, etc.)
        3. Default to fraiseql if no clear indicators

        Returns:
            Detected framework name or None if no clear detection
        """
        # Check current directory for framework indicators
        cwd = Path.cwd()

        # Django indicators
        if (cwd / "manage.py").exists() or (cwd / "settings.py").exists():
            return "django"

        # Rails indicators
        if (cwd / "Gemfile").exists() and (cwd / "app").exists() and (cwd / "config").exists():
            gemfile = cwd / "Gemfile"
            try:
                content = gemfile.read_text().lower()
                if "rails" in content:
                    return "rails"
            except Exception:
                pass

        # Prisma indicators
        if (cwd / "prisma").exists() or (cwd / "schema.prisma").exists():
            return "prisma"

        # FraiseQL indicators (check for GraphQL schema, etc.)
        if (cwd / "graphql").exists() or any(f.suffix == ".graphql" for f in cwd.glob("*")):
            return "fraiseql"

        # Check for SpecQL-specific indicators
        if (cwd / "entities").exists() and any(f.suffix == ".yaml" for f in (cwd / "entities").glob("*")):
            # SpecQL project - could be any framework, default to fraiseql
            return "fraiseql"

        return None

    def resolve_framework(
        self,
        explicit_framework: Optional[str] = None,
        dev_mode: bool = False,
        auto_detect: bool = True
    ) -> str:
        """
        Resolve the target framework based on user input and project context.

        Priority order:
        1. Explicit --framework flag
        2. Auto-detection from project structure (if enabled)
        3. Default to fraiseql

        Args:
            explicit_framework: Framework specified via --framework flag
            dev_mode: Whether --dev flag was used
            auto_detect: Whether to attempt auto-detection

        Returns:
            Resolved framework name
        """
        # Explicit framework takes highest priority
        if explicit_framework:
            return validate_framework_option(explicit_framework)

        # Auto-detect from project (unless disabled)
        if auto_detect:
            detected = self.detect_framework_from_project()
            if detected:
                return detected

        # Default to fraiseql
        return "fraiseql"

    def get_effective_defaults(
        self,
        framework: str,
        dev_mode: bool = False,
        no_tv: bool = False,
        custom_output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get effective defaults for a framework, applying user overrides.

        Args:
            framework: Target framework
            dev_mode: Whether development mode is enabled
            no_tv: Whether to disable table views
            custom_output_dir: User-specified output directory

        Returns:
            Dictionary of effective configuration
        """
        # Get base framework defaults
        defaults = get_framework_defaults(framework)

        # Apply development mode overrides
        if dev_mode:
            defaults = apply_dev_mode_overrides(defaults)

        # Apply user overrides
        if no_tv:
            defaults["include_tv"] = False

        if custom_output_dir:
            defaults["output_dir"] = custom_output_dir
        else:
            defaults["output_dir"] = get_output_dir_for_framework(framework, dev_mode)

        return defaults

    def validate_framework_compatibility(
        self,
        framework: str,
        requested_features: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Validate that requested features are compatible with the framework.

        Args:
            framework: Target framework
            requested_features: Dictionary of requested features

        Returns:
            Dictionary of warnings for incompatible features
        """
        warnings = {}
        get_framework_defaults(framework)

        # Check for framework-incompatible features
        if framework == "django" and requested_features.get("include_tv", False):
            warnings["include_tv"] = (
                "Table views (tv_*) are not typically needed for Django ORM. "
                "Consider using --no-tv for Django projects."
            )

        if framework == "rails" and requested_features.get("include_tv", False):
            warnings["include_tv"] = (
                "Table views (tv_*) are not typically needed for Rails ActiveRecord. "
                "Consider using --no-tv for Rails projects."
            )

        if framework == "fraiseql" and not requested_features.get("include_tv", True):
            warnings["no_tv"] = (
                "Disabling table views (tv_*) may limit GraphQL functionality. "
                "FraiseQL typically requires tv_* views for full GraphQL support."
            )

        return warnings


# Global registry instance
_registry = None

def get_framework_registry() -> FrameworkRegistry:
    """Get the global framework registry instance"""
    global _registry
    if _registry is None:
        _registry = FrameworkRegistry()
    return _registry