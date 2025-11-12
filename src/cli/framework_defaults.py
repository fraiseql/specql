"""
Framework-specific default configurations for SpecQL CLI

This module defines the default behavior for different target frameworks,
ensuring that SpecQL generates appropriate artifacts for each framework's
production requirements.
"""

from typing import Dict, Any, Optional


# Framework-specific default configurations
FRAMEWORK_DEFAULTS = {
    "fraiseql": {
        "include_tv": True,           # GraphQL requires tv_* views
        "trinity_pattern": True,     # pk_*, id, identifier pattern
        "audit_fields": True,        # created_at, updated_at, etc.
        "fraiseql_annotations": True, # GraphQL metadata comments
        "helper_functions": True,    # Type-safe access functions
        "use_registry": True,        # Hierarchical output structure
        "output_format": "hierarchical", # Organized directory structure
        "description": "PostgreSQL + FraiseQL GraphQL (full-stack)",
    },
    "django": {
        "include_tv": False,          # Django ORM doesn't need tv_*
        "trinity_pattern": False,     # Django uses single PK
        "audit_fields": True,         # Django has auto timestamps
        "fraiseql_annotations": False, # Not applicable
        "helper_functions": False,    # Django ORM provides access
        "use_registry": False,        # Flat structure for Django
        "output_format": "confiture", # db/schema/ structure
        "description": "Django ORM models and admin",
        # Future: include_models, include_admin, etc.
    },
    "rails": {
        "include_tv": False,          # ActiveRecord doesn't need tv_*
        "trinity_pattern": False,     # Rails uses single PK
        "audit_fields": True,         # Rails has timestamps
        "fraiseql_annotations": False, # Not applicable
        "helper_functions": False,    # ActiveRecord provides access
        "use_registry": False,        # Flat structure for Rails
        "output_format": "confiture", # db/schema/ structure
        "description": "Rails ActiveRecord models",
        # Future: include_models, include_migrations, etc.
    },
    "prisma": {
        "include_tv": False,          # Prisma doesn't need tv_*
        "trinity_pattern": False,     # Prisma handles PK patterns
        "audit_fields": True,         # Prisma supports timestamps
        "fraiseql_annotations": False, # Not applicable
        "helper_functions": False,    # Prisma client provides access
        "use_registry": False,        # Flat structure for Prisma
        "output_format": "confiture", # db/schema/ structure
        "description": "Prisma ORM schema",
        # Future: include_prisma_schema, etc.
    },
}


def get_framework_defaults(framework: str) -> Dict[str, Any]:
    """
    Get default configuration for a specific framework.

    Args:
        framework: Framework name (e.g., 'fraiseql', 'django')

    Returns:
        Dictionary of default settings for the framework

    Raises:
        ValueError: If framework is not supported
    """
    if framework not in FRAMEWORK_DEFAULTS:
        available = list(FRAMEWORK_DEFAULTS.keys())
        raise ValueError(f"Unknown framework '{framework}'. Available: {available}")

    return FRAMEWORK_DEFAULTS[framework].copy()


def get_available_frameworks() -> Dict[str, str]:
    """
    Get all available frameworks with their descriptions.

    Returns:
        Dictionary mapping framework names to descriptions
    """
    return {
        name: config["description"]
        for name, config in FRAMEWORK_DEFAULTS.items()
    }


def apply_dev_mode_overrides(defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply development mode overrides to framework defaults.

    Development mode prioritizes speed over production readiness:
    - Flat structure for quick iteration
    - No registry for faster generation
    - No table views to reduce output
    - Confiture-compatible output

    Args:
        defaults: Framework defaults to override

    Returns:
        Modified defaults for development mode
    """
    dev_overrides = {
        "use_registry": False,
        "output_format": "confiture",
        "include_tv": False,
        "output_dir": "db/schema",
    }

    # Apply overrides
    result = defaults.copy()
    result.update(dev_overrides)
    return result


def validate_framework_option(framework: Optional[str]) -> str:
    """
    Validate and normalize framework option.

    Args:
        framework: Framework name or None

    Returns:
        Validated framework name (defaults to 'fraiseql')
    """
    if framework is None:
        return "fraiseql"

    framework = framework.lower().strip()
    if framework not in FRAMEWORK_DEFAULTS:
        available = list(FRAMEWORK_DEFAULTS.keys())
        raise ValueError(f"Unknown framework '{framework}'. Available: {available}")

    return framework


def get_output_dir_for_framework(framework: str, dev_mode: bool = False, custom_dir: Optional[str] = None) -> str:
    """
    Get appropriate output directory for a framework.

    Args:
        framework: Target framework
        dev_mode: Whether development mode is enabled
        custom_dir: User-specified output directory

    Returns:
        Output directory path
    """
    if custom_dir:
        return custom_dir

    if dev_mode:
        return "db/schema"

    defaults = get_framework_defaults(framework)
    return "migrations" if defaults.get("use_registry", False) else "db/schema"