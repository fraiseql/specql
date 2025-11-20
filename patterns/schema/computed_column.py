"""Computed column pattern implementation."""

from dataclasses import dataclass

from core.ast_models import Entity


@dataclass
class ComputedColumnConfig:
    """Configuration for computed column."""

    column_name: str
    expression: str
    type: str
    nullable: bool = False
    stored: bool = True  # STORED vs VIRTUAL


class ComputedColumnPattern:
    """Generate computed columns for entities."""

    @classmethod
    def apply(cls, entity: Entity, params: dict) -> tuple[Entity, str]:
        """
        Apply computed column pattern.

        Adds a generated column to the entity that is computed from an expression.

        Args:
            entity: Entity to add computed column to
            params:
                - column_name: Name of the computed column
                - expression: SQL expression for computation
                - type: Column type (decimal, integer, text, etc.)
                - nullable: Whether column allows NULL (default: false)
                - stored: Whether to store the computed value (default: true)

        Returns:
            Tuple of (modified_entity, additional_sql)
        """
        config = cls._parse_config(params)

        # Add computed column to entity
        computed_field = cls._create_computed_field(config)

        # Add to entity.computed_columns (accessed by table generator)
        if not hasattr(entity, 'computed_columns'):
            entity.computed_columns = []
        entity.computed_columns.append(computed_field)

        # No additional SQL needed - the table generator will handle this
        return entity, ""

    @classmethod
    def _parse_config(cls, params: dict) -> ComputedColumnConfig:
        """Parse pattern parameters."""
        column_name = params.get("column_name")
        expression = params.get("expression")
        col_type = params.get("type")

        if not column_name:
            raise ValueError("Computed column pattern requires 'column_name'")
        if not expression:
            raise ValueError("Computed column pattern requires 'expression'")
        if not col_type:
            raise ValueError("Computed column pattern requires 'type'")

        return ComputedColumnConfig(
            column_name=column_name,
            expression=expression,
            type=col_type,
            nullable=params.get("nullable", False),
            stored=params.get("stored", True),
        )

    @classmethod
    def _create_computed_field(cls, config: ComputedColumnConfig) -> dict:
        """Create a computed field definition."""
        return {
            'name': config.column_name,
            'type': config.type,
            'nullable': config.nullable,
            'computed': True,
            'expression': config.expression,
            'stored': config.stored,
        }
