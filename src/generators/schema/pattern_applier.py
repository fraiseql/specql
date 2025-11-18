"""Apply patterns to entity schema."""

from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
import yaml
from jinja2 import Environment, FileSystemLoader, Template

from src.core.ast_models import Entity, FieldDefinition, Index, Pattern


@dataclass
class Constraint:
    """Database constraint definition for patterns."""

    type: str
    name: str | None = None
    fields: List[str] | None = None
    where: str | None = None
    comment: str | None = None


class PatternApplier:
    """Apply pattern transformations to entities."""

    def __init__(self):
        # Set up Jinja environment for template rendering
        from pathlib import Path

        self.pattern_dir = Path("stdlib/schema")
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.pattern_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def apply_patterns(self, entity: Entity) -> tuple[Entity, str]:
        """Apply all patterns defined in entity. Returns (entity, additional_sql)."""
        if not entity.patterns:
            return entity, ""

        additional_sql_parts = []

        for pattern in entity.patterns:
            entity, pattern_sql = self.apply_single_pattern(entity, pattern)
            if pattern_sql:
                additional_sql_parts.append(pattern_sql)

        return entity, "\n\n".join(additional_sql_parts)

    def apply_single_pattern(self, entity: Entity, pattern: "Pattern") -> tuple[Entity, str]:
        """Apply a single pattern to entity. Returns (entity, additional_sql)."""

        # Load pattern specification
        pattern_spec = self._load_pattern_spec(pattern.type)

        # Validate parameters and add defaults
        validated_params = self._validate_params(pattern_spec, pattern.params, entity)

        # Apply schema extensions
        entity = self._apply_schema_extensions(entity, pattern_spec, validated_params)

        # Generate additional SQL if pattern has schema_template
        additional_sql = ""
        if "schema_template" in pattern_spec:
            additional_sql = self._render_schema_template(pattern_spec, entity, validated_params)

        # Store pattern metadata in notes
        pattern_info = f"Applied pattern: {pattern.type}"
        if hasattr(entity, "notes") and entity.notes:
            entity.notes += f"\n{pattern_info}"
        else:
            entity.notes = pattern_info

        return entity, additional_sql

    def _load_pattern_spec(self, pattern_type: str) -> Dict[str, Any]:
        """Load pattern YAML specification."""
        pattern_path = self.pattern_dir / f"{pattern_type}.yaml"

        if not pattern_path.exists():
            # Try subdirectories (temporal/, validation/, schema/)
            for subdir in ["temporal", "validation", "schema"]:
                pattern_path = self.pattern_dir / subdir / f"{pattern_type}.yaml"
                if pattern_path.exists():
                    break

        if not pattern_path.exists():
            raise ValueError(f"Pattern '{pattern_type}' not found in {self.pattern_dir}")

        with open(pattern_path) as f:
            return yaml.safe_load(f)

    def _validate_params(
        self,
        pattern_spec: Dict[str, Any],
        params: Dict[str, Any],
        entity: Entity,
    ) -> Dict[str, Any]:
        """Validate pattern parameters and add defaults."""
        spec_params = {p["name"]: p for p in pattern_spec.get("parameters", [])}
        validated_params = params.copy()

        # Handle aliases (group_by -> group_by_fields, alias -> name)
        if "group_by" in params and "group_by_fields" not in params:
            validated_params["group_by_fields"] = params["group_by"]
        if "aggregates" in params:
            for agg in validated_params["aggregates"]:
                if "alias" in agg and "name" not in agg:
                    agg["name"] = agg["alias"]
                elif "name" not in agg:
                    # Generate default name
                    func = agg.get("function", "").lower()
                    field = agg.get("field", "")
                    if func and field:
                        agg["name"] = f"{func}_{field}"
                    elif func:
                        agg["name"] = func
                    else:
                        agg["name"] = "aggregate"

        # Check required parameters and add defaults
        for param_name, param_spec in spec_params.items():
            if param_name not in params and param_name not in validated_params:
                if param_spec.get("required", False):
                    # Special case: source_entity defaults to current entity
                    if param_name == "source_entity":
                        validated_params[param_name] = {
                            "schema": entity.schema,
                            "name": entity.name,
                        }
                    else:
                        raise ValueError(
                            f"Required parameter '{param_name}' missing for pattern "
                            f"'{pattern_spec['pattern']}'"
                        )
                elif "default" in param_spec:
                    validated_params[param_name] = param_spec["default"]

        return validated_params

        # Check unknown parameters
        for param_name in params:
            if param_name not in spec_params:
                raise ValueError(
                    f"Unknown parameter '{param_name}' for pattern '{pattern_spec['pattern']}'"
                )

        # Type validation
        for param_name, param_value in params.items():
            param_spec = spec_params[param_name]
            self._validate_param_type(param_name, param_value, param_spec)

    def _validate_param_type(
        self,
        param_name: str,
        param_value: Any,
        param_spec: Dict[str, Any],
    ) -> None:
        """Validate parameter type."""
        param_type = param_spec.get("type", "string")

        if param_type == "string" and not isinstance(param_value, str):
            raise TypeError(f"Parameter '{param_name}' must be string")

        elif param_type == "boolean" and not isinstance(param_value, bool):
            raise TypeError(f"Parameter '{param_name}' must be boolean")

        elif param_type == "integer" and not isinstance(param_value, int):
            raise TypeError(f"Parameter '{param_name}' must be integer")

        elif param_type.startswith("array<"):
            if not isinstance(param_value, list):
                raise TypeError(f"Parameter '{param_name}' must be array")

        # Validation regex if specified
        if "validation" in param_spec and isinstance(param_value, str):
            import re

            if not re.match(param_spec["validation"], param_value):
                raise ValueError(
                    f"Parameter '{param_name}' value '{param_value}' "
                    f"does not match pattern '{param_spec['validation']}'"
                )

    def _apply_schema_extensions(
        self,
        entity: Entity,
        pattern_spec: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Entity:
        """Apply schema extensions from pattern."""
        extensions = pattern_spec.get("schema_extensions", {})

        # Render templates with Jinja2
        template_context = {
            "entity": entity,
            "params": params,
            **params,  # Params available directly
        }

        # Add fields
        if "fields" in extensions:
            for field_template in extensions["fields"]:
                field = self._render_field(field_template, template_context, entity)
                entity.fields[field.name] = field

        # Add computed columns
        if "computed_columns" in extensions:
            for computed_template in extensions["computed_columns"]:
                computed_col = self._render_computed_column(
                    computed_template, template_context, entity
                )
                # Store computed columns in entity for template access
                if not hasattr(entity, "computed_columns"):
                    entity.computed_columns = []
                entity.computed_columns.append(computed_col)

        # Add constraints - Note: Entity doesn't have constraints field, so we'll skip for now
        # Constraints will be handled by the table generator based on pattern metadata
        if "constraints" in extensions:
            # Store constraint info in notes for debugging
            constraint_info = f"Pattern {pattern_spec['pattern']} adds {len(extensions['constraints'])} constraints"
            if entity.notes:
                entity.notes += f"\n{constraint_info}"
            else:
                entity.notes = constraint_info

        # Add indexes
        if "indexes" in extensions:
            for index_template in extensions["indexes"]:
                # Check 'when' condition if present
                when_condition = index_template.get("when")
                if when_condition is not None:
                    # Render the condition
                    when_template = Template(str(when_condition))
                    when_value = when_template.render(template_context)
                    # Evaluate as boolean (handle string "true"/"false" or actual boolean)
                    if when_value.lower() in ("false", "0", "", "none", "null"):
                        continue  # Skip this index

                index = self._render_index(index_template, template_context, entity)
                entity.indexes.append(index)

        return entity

    def _render_field(
        self,
        field_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> FieldDefinition:
        """Render field template with Jinja2."""
        from jinja2 import Template

        # Render field name
        name_template = Template(field_template["name"])
        name = name_template.render(context)

        # Create field
        field = FieldDefinition(
            name=name,
            type_name=field_template["type"],
            nullable=field_template.get("nullable", False),
            default=field_template.get("default"),
            description=field_template.get("comment", ""),
        )

        return field

    def _render_constraint(
        self,
        constraint_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Constraint:
        """Render constraint template."""
        from jinja2 import Template

        # Render constraint fields
        fields_template = Template(str(constraint_template["fields"]))
        fields_str = fields_template.render(context)

        # Parse fields (could be Python expression from template)
        import ast

        try:
            fields = ast.literal_eval(fields_str)
            if not isinstance(fields, list):
                fields = [fields]
        except (ValueError, SyntaxError):
            # Not a Python literal, treat as single field name
            fields = [fields_str]

        # Render name
        name = constraint_template.get("name", "")
        if name:
            name_template = Template(name)
            name = name_template.render(context)

        # Render where clause if present
        where = constraint_template.get("where")
        if where:
            where_template = Template(where)
            where = where_template.render(context)

        constraint = Constraint(
            type=constraint_template["type"],
            name=name,
            fields=fields,
            where=where,
            comment=constraint_template.get("comment", ""),
        )

        return constraint

    def _render_schema_template(
        self,
        pattern_spec: Dict[str, Any],
        entity: Entity,
        params: Dict[str, Any],
    ) -> str:
        """Render schema template with Jinja2."""
        template_str = pattern_spec["schema_template"]
        template = self.jinja_env.from_string(template_str)

        # Prepare context
        context = {
            "entity": entity,
            "params": params,
            **params,  # Params available directly
        }

        return template.render(context)

    def _render_index(
        self,
        index_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Index:
        """Render index template."""
        from jinja2 import Template

        # Render fields
        fields_template = Template(str(index_template["fields"]))
        fields_str = fields_template.render(context)

        # Parse fields
        import ast

        try:
            fields = ast.literal_eval(fields_str)
            if not isinstance(fields, list):
                fields = [fields]
        except (ValueError, SyntaxError):
            fields = [fields_str]

        # Render name if present
        name = index_template.get("name", "")
        if name:
            name_template = Template(name)
            name = name_template.render(context)

        # Render where clause if present
        where = index_template.get("where")
        if where:
            where_template = Template(where)
            where = where_template.render(context)

        index = Index(
            name=name,
            columns=fields,
            type=index_template.get("using", "btree"),
        )

        return index

    def _render_computed_column(
        self,
        computed_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Dict[str, Any]:
        """Render computed column template."""
        from jinja2 import Template

        # Render name
        name_template = Template(computed_template["name"])
        name = name_template.render(context)

        # Render type
        type_template = Template(computed_template["type"])
        col_type = type_template.render(context)

        # Render expression
        expression_template = Template(computed_template["expression"])
        expression = expression_template.render(context)

        # Get stored flag
        stored = computed_template.get("stored", True)

        # Render comment if present
        comment = computed_template.get("comment", "")
        if comment:
            comment_template = Template(comment)
            comment = comment_template.render(context)

        return {
            "name": name,
            "type": col_type,
            "expression": expression,
            "stored": stored,
            "comment": comment,
        }
