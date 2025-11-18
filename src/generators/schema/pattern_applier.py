"""Apply patterns to entity schema."""

from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
import yaml
from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Entity, FieldDefinition, Index


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

    def __init__(self, pattern_dir: Path = Path("stdlib/schema")):
        self.pattern_dir = pattern_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(pattern_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def apply_pattern(
        self,
        entity: Entity,
        pattern_type: str,
        params: Dict[str, Any],
    ) -> Entity:
        """Apply pattern to entity, returning modified entity."""

        # Load pattern specification
        pattern_spec = self._load_pattern_spec(pattern_type)

        # Validate parameters
        self._validate_params(pattern_spec, params)

        # Apply schema extensions
        entity = self._apply_schema_extensions(entity, pattern_spec, params)

        # Generate helper functions (handled by action compiler)
        # Metadata for FraiseQL
        entity.metadata["patterns"] = entity.metadata.get("patterns", [])
        entity.metadata["patterns"].append(
            {
                "type": pattern_type,
                "params": params,
            }
        )

        return entity

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
    ) -> None:
        """Validate pattern parameters against specification."""
        spec_params = {p["name"]: p for p in pattern_spec.get("parameters", [])}

        # Check required parameters
        for param_name, param_spec in spec_params.items():
            if param_spec.get("required", False) and param_name not in params:
                raise ValueError(
                    f"Required parameter '{param_name}' missing for pattern "
                    f"'{pattern_spec['pattern']}'"
                )

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

        # Add constraints - Note: Entity doesn't have constraints field, so we'll store in metadata
        if "constraints" in extensions:
            for constraint_template in extensions["constraints"]:
                constraint = self._render_constraint(
                    constraint_template,
                    template_context,
                    entity,
                )
                if "constraints" not in entity.metadata:
                    entity.metadata["constraints"] = []
                entity.metadata["constraints"].append(constraint)

        # Add indexes
        if "indexes" in extensions:
            for index_template in extensions["indexes"]:
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
