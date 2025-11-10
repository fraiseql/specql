"""
Core Logic Generator (Team C)
Generates core.* business logic functions
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, Entity, FieldTier
from src.generators.schema.schema_registry import SchemaRegistry
from src.utils.safe_slug import safe_slug, safe_table_name


class CoreLogicGenerator:
    """Generates core layer business logic functions"""

    def __init__(self, schema_registry: SchemaRegistry, templates_dir: str = "templates/sql"):
        self.schema_registry = schema_registry
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_core_create_function(self, entity: Entity) -> str:
        """
        Generate core CREATE function with:
        - Input validation
        - Trinity resolution (UUID → INTEGER)
        - tenant_id population
        - Audit field population
        """
        # Prepare field mappings
        fields = self._prepare_insert_fields(entity)
        validations = self._generate_validations(entity)
        fk_resolutions = self._generate_fk_resolutions(entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
                "pk_column": f"pk_{safe_slug(entity.name)}",
            },
            "composite_type": f"app.type_create_{entity.name.lower()}_input",
            "fields": fields,
            "validations": validations,
            "fk_resolutions": fk_resolutions,
        }

        template = self.env.get_template("core_create_function.sql.j2")
        return template.render(**context)

    def generate_core_update_function(self, entity: Entity) -> str:
        """
        Generate core UPDATE function with:
        - Input validation
        - Trinity resolution (UUID → INTEGER)
        - Audit field population (updated_at, updated_by)
        """
        # Prepare field mappings for UPDATE
        update_fields = self._prepare_update_fields(entity)
        validations = self._generate_validations(entity)
        fk_resolutions = self._generate_fk_resolutions(entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
                "pk_column": f"pk_{safe_slug(entity.name)}",
            },
            "composite_type": f"app.type_update_{entity.name.lower()}_input",
            "update_fields": update_fields,
            "validations": validations,
            "fk_resolutions": fk_resolutions,
        }

        template = self.env.get_template("core_update_function.sql.j2")
        return template.render(**context)

    def generate_core_delete_function(self, entity: Entity) -> str:
        """
        Generate core DELETE function with:
        - Soft delete (deleted_at, deleted_by)
        - Audit trail
        """
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
                "pk_column": f"pk_{safe_slug(entity.name)}",
            },
        }

        template = self.env.get_template("core_delete_function.sql.j2")
        return template.render(**context)

    def _prepare_insert_fields(self, entity: Entity) -> dict[str, list[str]]:
        """Prepare field list for INSERT statement"""
        insert_fields = []
        insert_values = []

        # Trinity fields
        insert_fields.append("id")
        insert_values.append(f"v_{entity.name.lower()}_id")

        # Multi-tenancy
        insert_fields.append("tenant_id")
        insert_values.append("auth_tenant_id")

        # Business fields
        for field_name, field_def in entity.fields.items():
            if field_def.tier == FieldTier.REFERENCE:
                # Foreign key (INTEGER)
                fk_name = f"fk_{field_name}"
                insert_fields.append(fk_name)
                insert_values.append(f"v_{fk_name}")
            else:
                # Regular field
                insert_fields.append(field_name)
                insert_values.append(f"input_data.{field_name}")

        # Audit fields
        insert_fields.extend(["created_at", "created_by"])
        insert_values.extend(["now()", "auth_user_id"])

        return {
            "columns": insert_fields,
            "insert_values": insert_values,
        }

    def _prepare_update_fields(self, entity: Entity) -> dict[str, list[str]]:
        """Prepare field list for UPDATE statement"""
        update_assignments = []

        # Business fields
        for field_name, field_def in entity.fields.items():
            if field_def.tier == FieldTier.REFERENCE:
                # Foreign key (INTEGER)
                fk_name = f"fk_{field_name}"
                update_assignments.append(f"{fk_name} = v_{fk_name}")
            else:
                # Regular field
                update_assignments.append(f"{field_name} = input_data.{field_name}")

        # Audit fields
        update_assignments.extend(["updated_at = now()", "updated_by = auth_user_id"])

        return {
            "assignments": update_assignments,
        }

    def _generate_validations(self, entity: Entity) -> list[dict[str, str]]:
        """Generate validation checks for required fields"""
        validations = []
        for field_name, field_def in entity.fields.items():
            if not field_def.nullable:
                # Generate validation for required field using structured error codes
                error_code = "validation:required_field"
                error_message = f"{field_name.capitalize()} is required"
                validations.append(
                    {
                        "field": field_name,
                        "check": f"input_data.{field_name} IS NULL",
                        "error": error_code,
                        "message": error_message,
                    }
                )
        return validations

    def _generate_fk_resolutions(self, entity: Entity) -> list[dict[str, Any]]:
        """Generate UUID → INTEGER FK resolutions using Trinity helpers"""
        resolutions = []
        is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                # Check if target entity is in tenant-specific schema
                target_is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

                input_field_ref = f"input_data.{field_name}_id::TEXT"
                helper_function_name = f"{entity.schema}.{field_def.reference_entity.lower()}_pk"

                if target_is_tenant_specific:
                    helper_call = f"{helper_function_name}({input_field_ref}, auth_tenant_id)"
                else:
                    helper_call = f"{helper_function_name}({input_field_ref})"

                resolutions.append(
                    {
                        "field": field_name,
                        "target_entity": field_def.reference_entity,
                        "variable": f"v_fk_{field_name}",
                        "helper_call": helper_call,
                        "input_field": f"{field_name}_id",  # Composite type uses company_id
                        "target_is_tenant_specific": target_is_tenant_specific,
                    }
                )
        return resolutions

    def _is_tenant_specific_schema(self, schema: str) -> bool:
        """
        Determine if schema is tenant-specific (needs tenant_id filtering)

        Uses schema registry to check multi_tenant flag
        """
        return self.schema_registry.is_multi_tenant(schema)

    def detect_action_pattern(self, action_name: str) -> str:
        """
        Detect action pattern from name or explicit type

        Returns: 'create', 'update', 'delete', 'custom'
        """
        name_lower = action_name.lower()
        if name_lower.startswith("create"):
            return "create"
        elif name_lower.startswith("update"):
            return "update"
        elif name_lower.startswith("delete"):
            return "delete"
        else:
            return "custom"

    def generate_core_custom_action(self, entity: Entity, action) -> str:
        """
        Generate core function for custom business action with step compilation
        """
        # Compile action steps
        compiled_steps = self._compile_action_steps(action, entity)

        # Extract variable declarations
        declarations = self._extract_declarations(action, entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": f"tb_{entity.name.lower()}",
            },
            "action": action,
            "composite_type": f"app.type_{action.name}_input",
            "declarations": declarations,
            "compiled_steps": compiled_steps,
            "camel_name": self._to_camel_case(action.name),
        }

        template = self.env.get_template("core_custom_action.sql.j2")
        return template.render(**context)

    def generate_custom_action(self, entity: Entity, action: Action) -> str:
        """
        Generate custom business action with step compilation
        """
        # Compile action steps
        compiled_steps = self._compile_action_steps(action, entity)
        print(f"DEBUG: compiled_steps for {action.name}: {compiled_steps}")

        # Extract variable declarations
        declarations = self._extract_declarations(action, entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
            },
            "action": action,
            "composite_type": f"app.type_{action.name}_input",
            "declarations": declarations,
            "compiled_steps": compiled_steps,
            "camel_name": self._to_camel_case(action.name),
        }

        template = self.env.get_template("core_custom_action.sql.j2")
        return template.render(**context)

    def _compile_action_steps(self, action: Action, entity: Entity) -> list[str]:
        """
        Compile action steps into SQL statements
        """
        compiled = []

        for step in action.steps:
            if step.type == "validate" and step.expression:
                # Extract fields used in validation
                fields_in_validation = self._extract_fields_from_expression(step.expression, entity)

                # Fetch current values for validation
                if fields_in_validation:
                    table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
                    select_fields = ", ".join(fields_in_validation)
                    select_into = ", ".join(f"v_current_{field}" for field in fields_in_validation)

                    compiled.append(f"-- Fetch current values for validation: {step.expression}")
                    compiled.append(
                        f"RAISE NOTICE 'Before SELECT: v_{entity.name.lower()}_id=%, auth_tenant_id=%', v_{entity.name.lower()}_id, auth_tenant_id;"
                    )
                    compiled.append(f"SELECT {select_fields} INTO {select_into}")
                    compiled.append(
                        f"FROM {table_name} WHERE id = v_{entity.name.lower()}_id AND tenant_id = auth_tenant_id;"
                    )
                    compiled.append(
                        f"RAISE NOTICE 'After SELECT: v_current_{fields_in_validation[0]}=%', v_current_{fields_in_validation[0]};"
                    )

                # Replace field references with v_current_* variables
                expression = step.expression
                for field_name in fields_in_validation:
                    expression = expression.replace(field_name, f"v_current_{field_name}")

                # Use custom error message if provided, otherwise default
                error_message = (
                    step.error
                    or f"{step.expression.replace(chr(39), chr(39) * 2)} validation failed"
                )

                compiled.append(f"-- Validate: {step.expression}")
                if fields_in_validation:
                    compiled.append(
                        f"RAISE NOTICE 'Before validation: v_current_{fields_in_validation[0]}=%', v_current_{fields_in_validation[0]};"
                    )
                compiled.append(f"IF NOT ({expression}) THEN")
                compiled.append("    RETURN app.log_and_return_mutation(")
                compiled.append(
                    "        auth_tenant_id, auth_user_id, "
                    + f"'{entity.name.lower()}', v_{entity.name.lower()}_id,"
                )
                compiled.append("        'CUSTOM', 'failed:validation_error',")
                compiled.append(f"        ARRAY[]::TEXT[], '{error_message}', NULL, NULL")
                compiled.append("    );")
                compiled.append("END IF;")

            elif step.type == "update":
                entity_name = step.entity or entity.name
                compiled.append(f"-- Update {entity_name}")
                table_name = f"{entity.schema}.tb_{entity_name.lower()}"
                assignments = []
                if step.fields:
                    for field, value in step.fields.items():
                        if field == "raw_set":
                            # Raw SQL SET clause
                            assignments.append(value)
                        else:
                            assignments.append(f"{field} = {repr(value)}")

                    # Add audit fields
                    assignments.extend(["updated_at = now()", "updated_by = auth_user_id"])

                compiled.append(f"UPDATE {table_name} SET {', '.join(assignments)}")
                compiled.append(f"WHERE id = v_{entity.name.lower()}_id;")

            elif step.type == "call":
                compiled.append(f"-- Call: {step.expression}")
                # TODO: Implement proper call compilation when emit_event is available
                compiled.append(
                    f"-- PERFORM {step.expression};"
                )  # Commented out until emit_event exists

            elif step.type == "refresh_table_view":
                # Handle refresh_table_view step
                compiled.extend(self._compile_refresh_table_view_step(step, entity))

        return compiled

    def _compile_refresh_table_view_step(self, step, entity: Entity) -> list[str]:
        """
        Compile refresh_table_view step to PL/pgSQL PERFORM calls
        """
        compiled = []
        entity_lower = entity.name.lower()
        pk_var = f"v_pk_{entity_lower}"

        if hasattr(step, "refresh_scope") and step.refresh_scope.value == "self":
            # Refresh only this entity's tv_ row
            compiled.append("-- Refresh table view (self)")
            compiled.append(f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});")

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "propagate":
            # Refresh this entity + specific related entities
            compiled.append("-- Refresh table view (self + propagate)")
            compiled.append(f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});")

            # Refresh specified related entities
            if hasattr(step, "propagate_entities") and step.propagate_entities:
                for rel_entity_name in step.propagate_entities:
                    # For simplicity, assume same schema and basic FK naming
                    rel_lower = rel_entity_name.lower()
                    fk_var = f"v_fk_{rel_entity_name.lower()}"
                    compiled.append(f"PERFORM {entity.schema}.refresh_tv_{rel_lower}({fk_var});")

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "related":
            # Refresh this entity + all entities that reference it
            compiled.append("-- Refresh table view (self + all related)")
            compiled.append(f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});")
            # TODO: Implement finding dependent entities

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "batch":
            # Deferred refresh (collect PKs, refresh at end)
            compiled.append("-- Queue for batch refresh (deferred)")
            compiled.append(
                f"INSERT INTO pg_temp.tv_refresh_queue VALUES ('{entity.name}', {pk_var});"
            )

        return compiled

    def _extract_fields_from_expression(self, expression: str, entity: Entity) -> list[str]:
        """
        Extract field names referenced in a validation expression
        """
        import re

        field_names = list(entity.fields.keys())
        fields_in_expr = []

        for field_name in field_names:
            if re.search(rf"\b{re.escape(field_name)}\b", expression):
                fields_in_expr.append(field_name)

        return fields_in_expr

    def _map_field_type_to_pg_type(self, specql_type: str) -> str:
        """
        Map SpecQL field types to PostgreSQL types for variable declarations
        """
        mapping = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "timestamp": "TIMESTAMPTZ",
            "date": "DATE",
            "jsonb": "JSONB",
            "uuid": "UUID",
        }
        return mapping.get(specql_type, "TEXT")

    def _extract_declarations(self, action, entity) -> list[str]:
        """
        Extract variable declarations needed for the action
        """
        declarations = [
            f"v_{entity.name.lower()}_pk INTEGER",
            # v_{entity.name.lower()}_id is declared in the template
        ]

        # Add declarations for current field values used in validation
        fields_in_validation = set()
        for step in action.steps:
            if step.type == "validate" and step.expression:
                fields_in_validation.update(
                    self._extract_fields_from_expression(step.expression, entity)
                )

        for field_name in fields_in_validation:
            field_def = entity.fields.get(field_name)
            if field_def:
                # Map field type to PostgreSQL type
                pg_type = self._map_field_type_to_pg_type(field_def.type_name)
                declarations.append(f"v_current_{field_name} {pg_type}")

        # Add declarations for FK resolutions
        for field_name, field_def in entity.fields.items():
            if field_def.tier == FieldTier.REFERENCE:
                declarations.append(f"v_fk_{field_name} INTEGER")

        return declarations

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])
