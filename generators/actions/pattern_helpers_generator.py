"""Generate action helper functions from patterns."""

from typing import Any

from jinja2 import Template

from core.ast_models import Entity, Pattern


class PatternHelpersGenerator:
    """Generate helper functions for patterns."""

    def generate(
        self,
        entity: Entity,
        pattern: Pattern,
        pattern_spec: dict[str, Any],
    ) -> list[str]:
        """Generate helper function SQL for pattern."""

        helpers = []

        for helper_spec in pattern_spec.get("action_helpers", []):
            sql = self._generate_helper_function(
                entity,
                pattern,
                helper_spec,
                pattern_spec,
            )
            helpers.append(sql)

        return helpers

    def _generate_helper_function(
        self,
        entity: Entity,
        pattern: Pattern,
        helper_spec: dict[str, Any],
        pattern_spec: dict[str, Any],
    ) -> str:
        """Generate single helper function."""

        # Render function name
        func_name_template = Template(helper_spec["function"])
        func_name = func_name_template.render(
            entity=entity,
            params=pattern.params,
            **pattern.params,
        )

        # Render function logic
        logic_template = Template(helper_spec["logic"])

        # Build template context
        context = {
            "entity": entity,
            "schema": entity.schema,
            "params": pattern.params,
            **pattern.params,
            "natural_key_where_clause": self._build_natural_key_where_clause(
                pattern.params.get("natural_key", [])
            ),
            "field_list": ", ".join(entity.fields.keys()),
            # Add more helper functions as needed
        }

        logic = logic_template.render(context)

        # Build parameter list
        param_list = []
        for param in helper_spec.get("params", []):
            param_def = f"{param['name']} {param['type']}"
            if "default" in param:
                param_def += f" DEFAULT {param['default']}"
            param_list.append(param_def)

        # Generate complete function
        sql = f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    {", ".join(param_list)}
)
RETURNS {helper_spec["returns"]}
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
{logic}
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name} IS '{helper_spec.get("description", "")}';
"""

        return sql

    def _build_natural_key_where_clause(self, natural_key_fields: list[str]) -> str:
        """Build WHERE clause for natural key matching."""
        if not natural_key_fields:
            return "TRUE"

        clauses = []
        for field in natural_key_fields:
            clauses.append(
                f"{field} = (natural_key_values->>'{field}')::{self._get_field_type(field)}"
            )

        return " AND ".join(clauses)

    def _get_field_type(self, field_name: str) -> str:
        """Get PostgreSQL type for field (simplified)."""
        # In real implementation, look up from entity.fields
        return "text"  # Default fallback
