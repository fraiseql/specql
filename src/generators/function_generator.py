"""
PostgreSQL Function Generator (Team B)
Generates CRUD and action functions from Entity AST
"""

from typing import List

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, ActionStep, Entity
from src.generators.app_wrapper_generator import AppWrapperGenerator
from src.generators.core_logic_generator import CoreLogicGenerator
from src.generators.sql_utils import SQLUtils


class FunctionGenerator:
    """Generates PostgreSQL functions for CRUD operations and SpecQL actions"""

    def __init__(self, templates_dir: str = "templates/sql"):
        """Initialize with Jinja2 templates"""
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )
        self.sql_utils = SQLUtils()
        self.app_gen = AppWrapperGenerator(templates_dir)
        self.core_gen = CoreLogicGenerator(templates_dir)

    def generate_crud_functions(self, entity: Entity) -> str:
        """
        Generate complete set of CRUD functions for entity

        Args:
            entity: Parsed Entity AST

        Returns:
            SQL with all CRUD functions
        """
        functions = []

        # Create function
        if entity.operations and entity.operations.create:
            functions.append(self._generate_create_function(entity))

        # Update function
        if entity.operations and entity.operations.update:
            functions.append(self._generate_update_function(entity))

        # Delete function (soft delete)
        if entity.operations and entity.operations.delete:
            functions.append(self._generate_delete_function(entity))

        return "\n\n".join(functions)

    def generate_action_functions(self, entity: Entity) -> str:
        """
        Generate functions for SpecQL actions using App/Core pattern for CRUD, legacy for custom

        Args:
            entity: Parsed Entity AST

        Returns:
            SQL with action functions
        """
        functions = []

        for action in entity.actions:
            if action.name.startswith(("create", "update", "delete")):
                # Use App/Core pattern for CRUD actions
                app_wrapper = self.app_gen.generate_app_wrapper(entity, action)
                functions.append(app_wrapper)

                # Core layer
                core_logic = None
                if action.name.startswith("create"):
                    core_logic = self.core_gen.generate_core_create_function(entity)
                elif action.name.startswith("update"):
                    core_logic = self.core_gen.generate_core_update_function(entity)
                elif action.name.startswith("delete"):
                    core_logic = self.core_gen.generate_core_delete_function(entity)

                if core_logic:
                    functions.append(core_logic)
            else:
                # Custom actions - use legacy single-layer approach
                functions.append(self._generate_action_function(entity, action))

        return "\n\n".join(functions)

    def _generate_create_function(self, entity: Entity) -> str:
        """Generate INSERT function for entity"""
        schema = entity.schema
        table_name = f"tb_{entity.name.lower()}"
        function_name = f"fn_create_{entity.name.lower()}"

        # Build parameter list
        params = [
            "p_input JSONB",
            "auth_tenant_id TEXT DEFAULT NULL",
            "auth_user_id UUID DEFAULT NULL",
        ]

        # Build INSERT statement
        business_fields = []
        param_assignments = []

        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref" and field_def.target_entity:
                # Foreign key field
                fk_name = f"fk_{field_name}"
                business_fields.append(fk_name)
                param_assignments.append(
                    f"            {fk_name} := core.{field_def.target_entity.lower()}_pk((p_input->>'{field_name}')::TEXT)"
                )
            else:
                # Regular field
                business_fields.append(field_name)
                param_assignments.append(f"            {field_name} := p_input->>'{field_name}'")

        # Build INSERT SQL
        field_list = ", ".join(business_fields)
        value_list = ", ".join([f"v_data.{field}" for field in business_fields])

        insert_sql = f"""
        -- Create record
        INSERT INTO {schema}.{table_name} (
            {field_list},
            created_at,
            created_by,
            updated_at
        )
        VALUES (
            {value_list},
            now(),
            auth_user_id,
            now()
        )
        RETURNING pk_{entity.name.lower()}, id INTO v_pk, v_uuid;"""

        # Build function body
        function_body = f"""
        v_data := jsonb_build_object(
{chr(10).join(param_assignments)}
        );

        -- Validate required fields
        -- TODO: Add validation logic

{insert_sql}

        -- Return success
        RETURN jsonb_build_object(
            'success', true,
            'result', jsonb_build_object(
                'id', v_uuid,
                'pk', v_pk
            ),
            'error', null
        );
"""

        return self.sql_utils.format_create_function(
            schema, function_name, params, "JSONB", function_body.strip(), "plpgsql"
        )

    def _generate_update_function(self, entity: Entity) -> str:
        """Generate UPDATE function for entity"""
        schema = entity.schema
        table_name = f"tb_{entity.name.lower()}"
        function_name = f"fn_update_{entity.name.lower()}"

        # Build parameter list
        params = [
            "p_id TEXT",
            "p_input JSONB",
            "auth_tenant_id TEXT DEFAULT NULL",
            "auth_user_id UUID DEFAULT NULL",
        ]

        # Build UPDATE logic
        update_assignments = []
        fk_lookups = []

        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref" and field_def.target_entity:
                # Foreign key field - need to resolve reference
                fk_name = f"fk_{field_name}"
                fk_lookups.append(
                    f"        v_{fk_name} := core.{field_def.target_entity.lower()}_pk((p_input->>'{field_name}')::TEXT);"
                )
                update_assignments.append(f"            {fk_name} = v_{fk_name}")
            else:
                # Regular field
                update_assignments.append(f"            {field_name} = p_input->>'{field_name}'")

        # Build function body
        function_body = f"""
        -- Resolve primary key
        v_pk := core.{entity.name.lower()}_pk(p_id);

        -- Get current values for comparison
        SELECT * INTO v_current
        FROM {schema}.{table_name}
        WHERE pk_{entity.name.lower()} = v_pk;

        -- Resolve foreign keys
{chr(10).join(fk_lookups)}

        -- Check if any values changed
        v_changed := false;
{chr(10).join([f"        IF p_input ? '{field_name}' AND (p_input->>'{field_name}') IS DISTINCT FROM v_current.{field_name} THEN" for field_name in entity.fields.keys()])}
            v_changed := true;
        END IF;

        IF NOT v_changed THEN
            -- No changes, return current record
            RETURN jsonb_build_object(
                'success', true,
                'result', jsonb_build_object(
                    'id', v_current.id,
                    'pk', v_current.pk_{entity.name.lower()}
                ),
                'error', null
            );
        END IF;

        -- Update record
        UPDATE {schema}.{table_name}
        SET
{chr(10).join(update_assignments)},
            updated_at = now(),
            updated_by = auth_user_id
        WHERE pk_{entity.name.lower()} = v_pk;

        -- Return updated record
        RETURN jsonb_build_object(
            'success', true,
            'result', jsonb_build_object(
                'id', v_current.id,
                'pk', v_pk
            ),
            'error', null
        );
"""

        return self.sql_utils.format_create_function(
            schema, function_name, params, "JSONB", function_body.strip(), "plpgsql"
        )

    def _generate_delete_function(self, entity: Entity) -> str:
        """Generate soft DELETE function for entity"""
        schema = entity.schema
        table_name = f"tb_{entity.name.lower()}"
        function_name = f"fn_delete_{entity.name.lower()}"

        # Build parameter list
        params = ["p_id TEXT", "auth_tenant_id TEXT DEFAULT NULL", "auth_user_id UUID DEFAULT NULL"]

        # Build function body
        function_body = f"""
        -- Resolve primary key
        v_pk := core.{entity.name.lower()}_pk(p_id);

        -- Soft delete
        UPDATE {schema}.{table_name}
        SET
            deleted_at = now(),
            deleted_by = auth_user_id,
            updated_at = now(),
            updated_by = auth_user_id
        WHERE pk_{entity.name.lower()} = v_pk
          AND deleted_at IS NULL;

        -- Check if record was found and updated
        IF FOUND THEN
            RETURN jsonb_build_object(
                'success', true,
                'result', jsonb_build_object('deleted', true),
                'error', null
            );
        ELSE
            RETURN jsonb_build_object(
                'success', false,
                'result', null,
                'error', 'Record not found or already deleted'
            );
        END IF;
"""

        return self.sql_utils.format_create_function(
            schema, function_name, params, "JSONB", function_body.strip(), "plpgsql"
        )

    def _generate_action_function(self, entity: Entity, action: Action) -> str:
        """
        Generate function for SpecQL action

        Args:
            entity: Entity containing the action
            action: Action to generate function for

        Returns:
            SQL function definition
        """
        schema = entity.schema
        function_name = f"fn_{action.name}"

        # Build parameter list (simplified - actions may need input parameters)
        params = [
            "p_input JSONB DEFAULT NULL",
            "auth_tenant_id TEXT DEFAULT NULL",
            "auth_user_id UUID DEFAULT NULL",
        ]

        # Convert action steps to PL/pgSQL
        plpgsql_body = self._convert_action_steps_to_plpgsql(
            entity, action.steps, auth_tenant_id="auth_tenant_id", auth_user_id="auth_user_id"
        )

        # Build function body
        function_body = f"""
        -- {action.name} action implementation
{plpgsql_body}

        -- Return success
        RETURN jsonb_build_object(
            'success', true,
            'result', jsonb_build_object('action', '{action.name}'),
            'error', null
        );
"""

        return self.sql_utils.format_create_function(
            schema, function_name, params, "JSONB", function_body.strip(), "plpgsql"
        )

    def _convert_action_steps_to_plpgsql(
        self,
        entity: Entity,
        steps: List[ActionStep],
        auth_tenant_id: str = "auth_tenant_id",
        auth_user_id: str = "auth_user_id",
    ) -> str:
        """
        Convert SpecQL action steps to PL/pgSQL code

        Args:
            entity: Entity context
            steps: List of action steps
            auth_tenant_id: Variable name for tenant ID
            auth_user_id: Variable name for user ID

        Returns:
            PL/pgSQL code block
        """
        plpgsql_lines = []

        for step in steps:
            if step.type == "validate" and step.expression:
                # Generate validation logic
                plpgsql_lines.append(f"        -- Validate: {step.expression}")
                plpgsql_lines.append("        -- TODO: Implement validation logic")
                plpgsql_lines.append(
                    f"        IF NOT ({self._convert_expression_to_sql(step.expression)}) THEN"
                )
                if step.error:
                    plpgsql_lines.append(
                        f"            RETURN jsonb_build_object('success', false, 'error', '{step.error}');"
                    )
                else:
                    plpgsql_lines.append(
                        "            RETURN jsonb_build_object('success', false, 'error', 'Validation failed');"
                    )
                plpgsql_lines.append("        END IF;")

            elif step.type == "insert":
                # Generate INSERT logic with audit fields
                plpgsql_lines.append(f"        -- Insert into {step.entity}")
                plpgsql_lines.append(f"        -- TODO: Add created_by = {auth_user_id}")

            elif step.type == "update":
                # Generate UPDATE logic with audit fields
                plpgsql_lines.append(f"        -- Update {step.entity}")
                plpgsql_lines.append(f"        -- TODO: Add updated_by = {auth_user_id}")

            elif step.type == "call":
                # Generate function call
                plpgsql_lines.append(f"        -- Call {step.function_name}")
                plpgsql_lines.append("        -- TODO: Implement function call logic")

            elif step.type == "notify":
                # Generate notification logic
                plpgsql_lines.append(f"        -- Notify {step.function_name}")
                plpgsql_lines.append("        -- TODO: Implement notification logic")

            elif step.type == "if" and step.condition:
                # Generate conditional logic
                plpgsql_lines.append(f"        -- Conditional: {step.condition}")
                plpgsql_lines.append(
                    f"        IF {self._convert_expression_to_sql(step.condition)} THEN"
                )
                if step.then_steps:
                    plpgsql_lines.extend(
                        self._convert_action_steps_to_plpgsql(entity, step.then_steps)
                    )
                plpgsql_lines.append("        ELSE")
                if step.else_steps:
                    plpgsql_lines.extend(
                        self._convert_action_steps_to_plpgsql(entity, step.else_steps)
                    )
                plpgsql_lines.append("        END IF;")

        return "\n".join(plpgsql_lines)

    def _convert_expression_to_sql(self, expression: str) -> str:
        """
        Convert SpecQL expression to SQL condition

        Args:
            expression: SpecQL expression (e.g., "status = 'lead'")

        Returns:
            SQL condition
        """
        if not expression:
            return "true"  # Default to true if no expression

        # Simple conversion - this would need to be more sophisticated
        # For now, just pass through with basic quote handling
        return expression.replace(" = ", " = ")
