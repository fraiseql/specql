"""
Input Validation Limits

These limits prevent DoS attacks and excessive resource consumption.
They can be configured via environment variables or defaults.
"""

import os


class ValidationLimits:
    """Configuration for input validation limits"""

    # Maximum YAML file size (1MB default) - prevents DoS
    MAX_YAML_FILE_SIZE: int = int(os.getenv("SPECQL_MAX_YAML_SIZE", 1_048_576))  # 1MB

    # Maximum YAML nesting depth (50 default) - prevents stack overflow
    MAX_NESTING_DEPTH: int = int(os.getenv("SPECQL_MAX_NESTING_DEPTH", 50))

    # Maximum fields per entity (1000 default) - prevents excessive complexity
    MAX_FIELDS_PER_ENTITY: int = int(os.getenv("SPECQL_MAX_FIELDS", 1000))

    # Maximum actions per entity (100 default) - prevents excessive complexity
    MAX_ACTIONS_PER_ENTITY: int = int(os.getenv("SPECQL_MAX_ACTIONS", 100))

    # Maximum steps per action (500 default) - prevents excessive complexity
    MAX_STEPS_PER_ACTION: int = int(os.getenv("SPECQL_MAX_STEPS", 500))

    @classmethod
    def validate_yaml_size(cls, yaml_content: str) -> None:
        """Validate YAML file size"""
        size = len(yaml_content.encode("utf-8"))
        if size > cls.MAX_YAML_FILE_SIZE:
            from src.core.specql_parser import ParseError

            raise ParseError(
                f"YAML file size ({size:,} bytes) exceeds maximum allowed "
                f"({cls.MAX_YAML_FILE_SIZE:,} bytes)"
            )

    @classmethod
    def validate_nesting_depth(cls, data: dict, current_depth: int = 0) -> None:
        """Validate YAML nesting depth recursively"""
        if current_depth > cls.MAX_NESTING_DEPTH:
            from src.core.specql_parser import ParseError

            raise ParseError(
                f"YAML nesting depth ({current_depth}) exceeds maximum allowed "
                f"({cls.MAX_NESTING_DEPTH})"
            )

        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, (dict, list)):
                    cls.validate_nesting_depth(value, current_depth + 1)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    cls.validate_nesting_depth(item, current_depth + 1)

    @classmethod
    def validate_field_count(cls, entity_name: str, field_count: int) -> None:
        """Validate field count per entity"""
        if field_count > cls.MAX_FIELDS_PER_ENTITY:
            from src.core.exceptions import SpecQLValidationError

            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Field count ({field_count}) exceeds maximum allowed "
                f"({cls.MAX_FIELDS_PER_ENTITY})",
            )

    @classmethod
    def validate_action_count(cls, entity_name: str, action_count: int) -> None:
        """Validate action count per entity"""
        if action_count > cls.MAX_ACTIONS_PER_ENTITY:
            from src.core.exceptions import SpecQLValidationError

            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Action count ({action_count}) exceeds maximum allowed "
                f"({cls.MAX_ACTIONS_PER_ENTITY})",
            )

    @classmethod
    def validate_steps_count(cls, entity_name: str, action_name: str, steps_count: int) -> None:
        """Validate steps count per action"""
        if steps_count > cls.MAX_STEPS_PER_ACTION:
            from src.core.exceptions import SpecQLValidationError

            raise SpecQLValidationError(
                entity=entity_name,
                message=f"Steps count ({steps_count}) in action '{action_name}' exceeds maximum allowed "
                f"({cls.MAX_STEPS_PER_ACTION})",
            )
