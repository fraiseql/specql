"""
Rich Type Handler

Handles JSONB composite field manipulation for Tier 2 rich types.

Example SpecQL:
    - update: address.street = '123 Main St'
    - update: address.city = 'Springfield'

Generated PL/pgSQL:
    -- Update JSONB field: address.street
    v_address := jsonb_set(v_address, '{street}', '"123 Main St"');
    UPDATE crm.tb_contact
    SET address = v_address, updated_at = NOW(), updated_by = v_user_id
    WHERE pk_contact = v_pk;
"""

from src.core.ast_models import EntityDefinition


class RichTypeHandler:
    """Handles JSONB composite field operations"""

    def extract_jsonb_value(self, field_path: str, entity: EntityDefinition) -> str:
        """
        Generate PL/pgSQL to extract a value from JSONB field

        Args:
            field_path: Dot-separated path like "address.street"
            entity: Entity definition

        Returns:
            PL/pgSQL expression to extract the value

        Example:
            "address.street" → "v_address->>'street'"
        """
        base_field, json_path = self._parse_field_path(field_path)

        if not self._is_composite_field(base_field, entity):
            raise ValueError(f"Field {base_field} is not a composite (JSONB) field")

        # For simple paths like "address.street"
        if len(json_path) == 1:
            return f"v_{base_field}->>'{json_path[0]}'"
        else:
            # For nested paths like "address.location.city"
            path_str = ",".join(json_path)
            return f"v_{base_field}#>>'{{{path_str}}}'"

    def set_jsonb_value(self, field_path: str, value_expr: str, entity: EntityDefinition) -> str:
        """
        Generate PL/pgSQL to set a value in JSONB field

        Args:
            field_path: Dot-separated path like "address.street"
            value_expr: The value to set (as PL/pgSQL expression)
            entity: Entity definition

        Returns:
            PL/pgSQL statement to update the JSONB field

        Example:
            set_jsonb_value("address.street", "'123 Main St'", entity)
            → "v_address := jsonb_set(v_address, '{street}', '\"123 Main St\"');"
        """
        base_field, json_path = self._parse_field_path(field_path)

        if not self._is_composite_field(base_field, entity):
            raise ValueError(f"Field {base_field} is not a composite (JSONB) field")

        # Build the JSON path string for PostgreSQL jsonb_set
        # Format: '{key1,key2}' for nested paths
        path_str = "{" + ",".join(json_path) + "}"

        # Convert value expression to JSON
        json_value = self._value_to_json(value_expr)

        return f"v_{base_field} := jsonb_set(v_{base_field}, '{path_str}', {json_value});"

    def build_jsonb_object(
        self, field_assignments: dict[str, str], entity: EntityDefinition
    ) -> str:
        """
        Build a complete JSONB object from field assignments

        Args:
            field_assignments: Dict of field paths to values
            entity: Entity definition

        Returns:
            PL/pgSQL expression for the JSONB object

        Example:
            {"address.street": "'123 Main St'", "address.city": "'Springfield'"}
            → "jsonb_build_object('street', '123 Main St', 'city', 'Springfield')"
        """
        if not field_assignments:
            return "jsonb_build_object()"

        # Group by base field
        base_fields = {}
        for field_path, value in field_assignments.items():
            base_field, json_path = self._parse_field_path(field_path)
            if base_field not in base_fields:
                base_fields[base_field] = {}
            # For nested paths, we'd need more complex logic
            # For now, assume single-level paths
            if len(json_path) == 1:
                base_fields[base_field][json_path[0]] = value

        # For single base field, build the object
        if len(base_fields) == 1:
            base_field = list(base_fields.keys())[0]
            assignments = base_fields[base_field]

            args = []
            for key, value in assignments.items():
                args.extend([f"'{key}'", value])

            return f"jsonb_build_object({', '.join(args)})"

        # For multiple base fields, this would be more complex
        # For now, raise an error
        raise NotImplementedError("Multiple base fields not yet supported")

    def _parse_field_path(self, field_path: str) -> tuple[str, list[str]]:
        """
        Parse a field path like "address.street.city" into base field and path

        Returns:
            (base_field, [path_components])
        """
        parts = field_path.split(".")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid field path: {field_path}. Expected format: base_field.property"
            )

        return parts[0], parts[1:]

    def _is_composite_field(self, field_name: str, entity: EntityDefinition) -> bool:
        """
        Check if a field is a composite (JSONB) field
        """
        field_def = entity.fields.get(field_name)
        if not field_def:
            return False

        # Check if it's a composite type (Tier 2)
        return field_def.tier.name == "COMPOSITE"

    def _value_to_json(self, value_expr: str) -> str:
        """
        Convert a PL/pgSQL value expression to JSON format

        Args:
            value_expr: PL/pgSQL expression like "'string'" or "123"

        Returns:
            JSON representation for jsonb_set
        """
        # If it's already a string literal, wrap in quotes for JSON
        if value_expr.startswith("'") and value_expr.endswith("'"):
            # It's a string literal, convert to JSON string
            return f'"{value_expr[1:-1]}"'
        elif value_expr.isdigit() or (value_expr.startswith("-") and value_expr[1:].isdigit()):
            # It's a number
            return value_expr
        elif value_expr.lower() in ("true", "false"):
            # It's a boolean
            return value_expr.lower()
        elif value_expr == "null":
            # It's null
            return value_expr
        else:
            # For variables or complex expressions, assume they're already proper JSON
            return value_expr
