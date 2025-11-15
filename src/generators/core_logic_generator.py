"""
Core Logic Generator (Team C)
Generates core.* business logic functions
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, ActionStep, Entity, FieldTier
from src.generators.actions.compilation_context import CompilationContext
from src.generators.schema.schema_registry import SchemaRegistry
from src.utils.safe_slug import safe_slug, safe_table_name


class CoreLogicGenerator:
    """Generates core layer business logic functions"""

    def __init__(
        self, schema_registry: SchemaRegistry, templates_dir: str = "templates/sql"
    ):
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
        self._is_tenant_specific_schema(entity.schema)

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                # Check if target entity is in tenant-specific schema
                target_is_tenant_specific = self._is_tenant_specific_schema(
                    entity.schema
                )

                input_field_ref = f"input_data.{field_name}_id::TEXT"
                helper_function_name = (
                    f"{entity.schema}.{field_def.reference_entity.lower()}_pk"
                )

                if target_is_tenant_specific:
                    helper_call = (
                        f"{helper_function_name}({input_field_ref}, auth_tenant_id)"
                    )
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
        context = CompilationContext()  # Collect CTEs and variables for use in queries

        for step in action.steps:
            if step.type == "validate" and step.expression:
                # Extract fields used in validation
                fields_in_validation = self._extract_fields_from_expression(
                    step.expression, entity
                )

                # Fetch current values for validation
                if fields_in_validation:
                    table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
                    select_fields = ", ".join(fields_in_validation)
                    select_into = ", ".join(
                        f"v_current_{field}" for field in fields_in_validation
                    )

                    compiled.append(
                        f"-- Fetch current values for validation: {step.expression}"
                    )
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
                    expression = expression.replace(
                        field_name, f"v_current_{field_name}"
                    )

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
                compiled.append(
                    f"        ARRAY[]::TEXT[], '{error_message}', NULL, NULL"
                )
                compiled.append("    );")
                compiled.append("END IF;")

            elif step.type == "duplicate_check":
                compiled.append(self._compile_duplicate_check_step(step, entity))

            elif step.type == "delete":
                compiled.append(self._compile_delete_step(step, entity))

            elif step.type == "update":
                entity_name = step.entity or entity.name
                compiled.append(f"-- Update {entity_name}")
                table_name = f"{entity.schema}.tb_{entity_name.lower()}"

                # Check if partial updates are requested
                partial_updates = (
                    step.fields.get("partial_updates", False) if step.fields else False
                )
                track_updated_fields = (
                    step.fields.get("track_updated_fields", False)
                    if step.fields
                    else False
                )
                recalculate_identifier = (
                    step.fields.get("recalculate_identifier", False)
                    if step.fields
                    else False
                )
                refresh_projection = (
                    step.fields.get("refresh_projection", None) if step.fields else None
                )

                assignments = []
                tracking_code = []

                if step.fields:
                    if partial_updates:
                        # Generate CASE expressions for partial updates
                        assignments = self._generate_partial_update_assignments(
                            entity, step.fields
                        )
                        if track_updated_fields:
                            tracking_code = self._generate_field_tracking(
                                entity, step.fields
                            )
                    else:
                        # Full update (existing logic)
                        for field, value in step.fields.items():
                            if field in [
                                "partial_updates",
                                "track_updated_fields",
                                "recalculate_identifier",
                            ]:
                                continue  # Skip control fields
                            elif field == "raw_set":
                                # Raw SQL SET clause
                                assignments.append(value)
                            else:
                                assignments.append(f"{field} = {repr(value)}")

                        # Add audit fields
                        assignments.extend(
                            ["updated_at = now()", "updated_by = auth_user_id"]
                        )

                if partial_updates:
                    compiled.append(f"UPDATE {table_name}")
                    compiled.append(f"SET {', '.join(assignments)}")
                    compiled.append(
                        f"WHERE id = v_{entity.name.lower()}_id AND tenant_id = auth_tenant_id;"
                    )
                    if tracking_code:
                        compiled.extend(tracking_code)
                else:
                    compiled.append(f"UPDATE {table_name} SET {', '.join(assignments)}")
                    compiled.append(f"WHERE id = v_{entity.name.lower()}_id;")

                # Add identifier recalculation if requested
                if recalculate_identifier:
                    compiled.append(self._generate_identifier_recalc_call(entity))

                # Add projection refresh if requested
                if refresh_projection:
                    compiled.append(
                        self._generate_projection_refresh_call(
                            entity, refresh_projection
                        )
                    )

            elif step.type == "call":
                compiled.append(f"-- Call: {step.expression}")
                # TODO: Implement proper call compilation when emit_event is available
                compiled.append(
                    f"-- PERFORM {step.expression};"
                )  # Commented out until emit_event exists

            elif step.type == "refresh_table_view":
                # Handle refresh_table_view step
                compiled.extend(self._compile_refresh_table_view_step(step, entity))

            elif step.type == "cte":
                # Handle CTE step - collect CTE for use in subsequent queries
                if step.cte_name:
                    context.add_cte(
                        step.cte_name, step.cte_query or "", step.cte_materialized
                    )

            elif step.type == "query":
                # Handle query step with potential CTEs
                compiled.append(self._compile_query_step(step, context))

            elif step.type == "switch":
                # Handle switch step
                compiled.append(self._compile_switch_step(step, context))

            elif step.type == "return_early":
                # Handle return_early step
                compiled.append(self._compile_return_early_step(step, context))

        return compiled

    def _compile_query_step(self, step: ActionStep, context: CompilationContext) -> str:
        """
        Compile a query step with CTE support
        """
        query_sql = step.expression or ""

        # Add WITH clause if CTEs exist
        if context.has_ctes():
            with_clause = context.get_with_clause()
            query_sql = f"{with_clause}\n{query_sql}"

        return f"-- Query: {query_sql}"

    def _compile_duplicate_check_step(self, step, entity: Entity) -> str:
        """
        Compile duplicate check step to PL/pgSQL

        Args:
            step: Duplicate check step
            entity: Entity being checked

        Returns:
            PL/pgSQL code for duplicate detection
        """
        # Get configuration from step fields
        check_fields = step.fields.get("fields", []) if step.fields else []
        error_message = (
            step.fields.get("error_message", "Record already exists")
            if step.fields
            else "Record already exists"
        )
        return_conflict_object = (
            step.fields.get("return_conflict_object", True) if step.fields else True
        )

        if not check_fields:
            raise ValueError("duplicate_check step must specify 'fields' to check")

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        projection_name = f"{entity.schema}.v_{entity_lower}_projection"

        # Build WHERE conditions
        where_conditions = []
        for field in check_fields:
            where_conditions.append(f"{field} = input_data.{field}")

        where_clause = " AND ".join(where_conditions)

        # Build conflict object for response
        conflict_fields = []
        for field in check_fields:
            conflict_fields.append(f"'{field}', input_data.{field}")

        conflict_object = ", ".join(conflict_fields)

        sql_parts = []

        # Check for existing record
        sql_parts.append(f"""
    -- Check for duplicate {entity.name}
    SELECT id INTO v_existing_id
    FROM {table_name}
    WHERE {where_clause}
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL
    LIMIT 1;""")

        # Handle duplicate found
        sql_parts.append("""
    IF v_existing_id IS NOT NULL THEN""")

        if return_conflict_object:
            sql_parts.append(f"""
        -- Load existing object for conflict response
        SELECT data INTO v_existing_object
        FROM {projection_name}
        WHERE id = v_existing_id;""")

        # Return NOOP response
        sql_parts.append(f"""
        -- Return NOOP with conflict details
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            '{entity_lower}',
            v_existing_id,
            'NOOP',
            'noop:already_exists',
            ARRAY[]::TEXT[],
            '{error_message}',
            {"v_existing_object" if return_conflict_object else "NULL"},
            {"v_existing_object" if return_conflict_object else "NULL"},
            jsonb_build_object(
                'trigger', 'api_create',
                'status', 'noop:already_exists',
                'reason', 'unique_constraint_violation',
                'conflict', jsonb_build_object(
                    {conflict_object}{", 'conflict_object', v_existing_object" if return_conflict_object else ""}
                )
            )
        );
    END IF;""")

        return "\n".join(sql_parts)

    def _compile_delete_step(self, step, entity: Entity) -> str:
        """
        Compile delete step to PL/pgSQL with hard/soft delete support

        Args:
            step: Delete step
            entity: Entity being deleted

        Returns:
            PL/pgSQL code for delete operation
        """
        # Get configuration from step fields
        supports_hard_delete = (
            step.fields.get("supports_hard_delete", False) if step.fields else False
        )
        check_dependencies = (
            step.fields.get("check_dependencies", []) if step.fields else []
        )

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"

        sql_parts = []

        if supports_hard_delete and check_dependencies:
            # Generate dependency checking code
            sql_parts.append(
                self._generate_dependency_check(entity, check_dependencies)
            )

        sql_parts.append(f"""
    -- Delete {entity.name}
    DECLARE
        v_hard_delete BOOLEAN := COALESCE(
            (input_payload->>'hard_delete')::BOOLEAN,
            FALSE
        );
    BEGIN""")

        if supports_hard_delete and check_dependencies:
            sql_parts.append("""
        -- Check if hard delete is blocked by dependencies
        IF v_hard_delete AND v_has_dependencies THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                '{entity_lower}', v_{entity_lower}_id,
                'NOOP', 'noop:cannot_delete_with_dependencies',
                ARRAY[]::TEXT[],
                'Cannot hard delete record with dependencies',
                NULL, NULL,
                jsonb_build_object(
                    'reason', 'has_dependencies',
                    'dependencies', v_dependency_details,
                    'suggestion', 'Use soft delete or remove dependencies first'
                )
            );
        END IF;""")

        # Perform delete
        delete_sql = f"""
        -- Perform delete
        IF v_hard_delete THEN
            -- Hard delete
            DELETE FROM {table_name}
            WHERE id = v_{entity_lower}_id
              AND tenant_id = auth_tenant_id;

            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                '{entity_lower}', v_{entity_lower}_id,
                'DELETE', 'deleted',
                ARRAY[]::TEXT[],
                'Record deleted permanently',
                NULL, NULL
            );
        ELSE
            -- Soft delete
            UPDATE {table_name}
            SET deleted_at = NOW(),
                deleted_by = auth_user_id
            WHERE id = v_{entity_lower}_id
              AND tenant_id = auth_tenant_id;

            RETURN app.log_and_return_mutation(
                auth_tenant_id, auth_user_id,
                '{entity_lower}', v_{entity_lower}_id,
                'UPDATE', 'soft_deleted',
                ARRAY[]::TEXT[],
                'Record soft deleted',
                NULL, NULL
            );
        END IF;
    END;"""

        sql_parts.append(delete_sql)

        return "\n".join(sql_parts)

    def _generate_dependency_check(self, entity: Entity, dependencies: list) -> str:
        """
        Generate dependency checking code for hard delete

        Args:
            entity: Entity being deleted
            dependencies: List of dependency checks

        Returns:
            PL/pgSQL code for dependency checking
        """
        entity_lower = entity.name.lower()

        check_parts = [
            """
    -- Check dependencies before hard delete
    DECLARE
        v_has_dependencies BOOLEAN := FALSE;
        v_dependency_details JSONB := '{}'::JSONB;
    BEGIN"""
        ]

        for dep in dependencies:
            dep_entity = dep.get("entity")
            dep_field = dep.get("field", f"{entity_lower}_id")
            block_hard_delete = dep.get("block_hard_delete", True)

            if block_hard_delete:
                check_parts.append(f"""
        -- Check {dep_entity} dependency
        IF EXISTS (
            SELECT 1 FROM {entity.schema}.tb_{dep_entity.lower()}
            WHERE {dep_field} = v_{entity_lower}_id
              AND tenant_id = auth_tenant_id
              AND deleted_at IS NULL
        ) THEN
            v_has_dependencies := TRUE;
            v_dependency_details := jsonb_set(
                COALESCE(v_dependency_details, '{{}}'::JSONB),
                '{{{dep_entity}}}',
                (SELECT COUNT(*)::TEXT::JSONB
                 FROM {entity.schema}.tb_{dep_entity.lower()}
                 WHERE {dep_field} = v_{entity_lower}_id
                   AND tenant_id = auth_tenant_id
                   AND deleted_at IS NULL)
            );
        END IF;""")

        check_parts.append("    END;")
        return "\n".join(check_parts)

    def _generate_identifier_recalc_call(self, entity: Entity) -> str:
        """
        Generate call to identifier recalculation function

        Args:
            entity: Entity to recalculate identifier for

        Returns:
            PL/pgSQL PERFORM statement for identifier recalculation
        """
        entity_lower = entity.name.lower()
        schema = entity.schema

        return f"""
    -- Recalculate identifier
    PERFORM {schema}.recalcid_{entity_lower}(
        v_{entity_lower}_id,
        auth_tenant_id,
        auth_user_id
    );"""

    def _generate_projection_refresh_call(
        self, entity: Entity, projection_name: str
    ) -> str:
        """
        Generate call to projection refresh function

        Args:
            entity: Entity whose projection to refresh
            projection_name: Name of the projection to refresh

        Returns:
            PL/pgSQL PERFORM statement for projection refresh
        """
        entity_lower = entity.name.lower()
        schema = entity.schema

        return f"""
    -- Refresh projection
    PERFORM {schema}.refresh_{projection_name}(
        v_{entity_lower}_id,
        auth_tenant_id
    );"""

    def _generate_partial_update_assignments(
        self, entity: Entity, step_fields: dict
    ) -> list[str]:
        """
        Generate CASE expressions for partial updates

        Args:
            entity: The entity being updated
            step_fields: Fields from the update step

        Returns:
            List of SET assignments with CASE expressions
        """
        assignments = []

        # Generate CASE expressions for each field in the entity
        for field_name, field_def in entity.fields.items():
            # Skip system fields that shouldn't be updated directly
            if field_name in ["id", "tenant_id", "created_at", "created_by"]:
                continue

            # Audit fields are always set, not conditionally updated
            if field_name in ["updated_at", "updated_by"]:
                if field_name == "updated_at":
                    assignments.append("updated_at = NOW()")
                elif field_name == "updated_by":
                    assignments.append("updated_by = auth_user_id")
            else:
                case_expr = f"""{field_name} = CASE WHEN input_payload ? '{field_name}'
                         THEN input_data.{field_name}
                         ELSE {field_name} END"""
                assignments.append(case_expr)

        return assignments

    def _generate_field_tracking(self, entity: Entity, step_fields: dict) -> list[str]:
        """
        Generate code to track which fields were updated

        Args:
            entity: The entity being updated
            step_fields: Fields from the update step

        Returns:
            List of PL/pgSQL statements for field tracking
        """
        tracking_code = []

        # Initialize updated fields array if not already done
        tracking_code.append("v_updated_fields := ARRAY[]::TEXT[];")

        # Track each field that could be updated (excluding system and audit fields)
        for field_name, field_def in entity.fields.items():
            # Skip system fields and audit fields (they're always updated)
            if field_name in [
                "id",
                "tenant_id",
                "created_at",
                "created_by",
                "updated_at",
                "updated_by",
            ]:
                continue

            tracking_code.append(f"""
    IF input_payload ? '{field_name}' THEN
        v_updated_fields := v_updated_fields || ARRAY['{field_name}'];
    END IF;""")

        return tracking_code

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
            compiled.append(
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});"
            )

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "propagate":
            # Refresh this entity + specific related entities
            compiled.append("-- Refresh table view (self + propagate)")
            compiled.append(
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});"
            )

            # Refresh specified related entities
            if hasattr(step, "propagate_entities") and step.propagate_entities:
                for rel_entity_name in step.propagate_entities:
                    # For simplicity, assume same schema and basic FK naming
                    rel_lower = rel_entity_name.lower()
                    fk_var = f"v_fk_{rel_entity_name.lower()}"
                    compiled.append(
                        f"PERFORM {entity.schema}.refresh_tv_{rel_lower}({fk_var});"
                    )

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "related":
            # Refresh this entity + all entities that reference it
            compiled.append("-- Refresh table view (self + all related)")
            compiled.append(
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});"
            )
            # TODO: Implement finding dependent entities

        elif hasattr(step, "refresh_scope") and step.refresh_scope.value == "batch":
            # Deferred refresh (collect PKs, refresh at end)
            compiled.append("-- Queue for batch refresh (deferred)")
            compiled.append(
                f"INSERT INTO pg_temp.tv_refresh_queue VALUES ('{entity.name}', {pk_var});"
            )

        return compiled

    def _extract_fields_from_expression(
        self, expression: str, entity: Entity
    ) -> list[str]:
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

    def _format_value_for_sql(self, value: Any) -> str:
        """Format a value for SQL DEFAULT clause"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        else:
            return str(value)

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

        # Add declarations from declare steps
        for step in action.steps:
            if step.type == "declare":
                if step.variable_name:
                    # Single declaration
                    pg_type = self._map_field_type_to_pg_type(
                        step.variable_type or "text"
                    )
                    default = ""
                    if step.default_value is not None:
                        default = (
                            f" := {self._format_value_for_sql(step.default_value)}"
                        )
                    declarations.append(f"{step.variable_name} {pg_type}{default}")
                elif step.declarations:
                    # Multiple declarations
                    for decl in step.declarations:
                        pg_type = self._map_field_type_to_pg_type(decl.type)
                        default = ""
                        if decl.default_value is not None:
                            default = (
                                f" := {self._format_value_for_sql(decl.default_value)}"
                            )
                        declarations.append(f"{decl.name} {pg_type}{default}")

        return declarations

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    def _compile_switch_step(
        self, step: ActionStep, context: CompilationContext
    ) -> str:
        """
        Compile switch step to PL/pgSQL CASE WHEN or IF/ELSIF
        """
        # For now, use a simplified implementation
        # In practice, this would use the SwitchStepCompiler
        switch_expr = step.switch_expression or ""

        lines = []
        if self._is_simple_switch(step):
            lines.append(f"CASE {switch_expr}")
            for case in step.cases:
                when_value = case.when_value
                lines.append(f"  WHEN {when_value} THEN")
                # Simplified: just add a comment for now
                lines.append("    -- Case logic here")
            if step.default_steps:
                lines.append("  ELSE")
                lines.append("    -- Default logic here")
            lines.append("END CASE;")
        else:
            # IF/ELSIF chain
            for i, case in enumerate(step.cases):
                keyword = "IF" if i == 0 else "ELSIF"
                condition = case.when_condition or case.when_value
                lines.append(f"{keyword} {condition} THEN")
                lines.append("  -- Case logic here")
            if step.default_steps:
                lines.append("ELSE")
                lines.append("  -- Default logic here")
            lines.append("END IF;")

        return "\n".join(lines)

    def _compile_return_early_step(
        self, step: ActionStep, context: CompilationContext
    ) -> str:
        """
        Compile return_early step to PL/pgSQL RETURN
        """
        return_value = step.return_value

        if return_value is None:
            return "RETURN;"
        elif isinstance(return_value, dict):
            # Complex return value (mutation result)
            success = return_value.get("success", "false")
            message = return_value.get("message", "''")
            return f"""RETURN ROW(
    {success}::BOOLEAN,
    {message}::TEXT,
    '{{}}'::JSONB,
    '{{}}'::JSONB
)::app.mutation_result;"""
        else:
            # Simple return value
            return f"RETURN {return_value};"

    def _is_simple_switch(self, step: ActionStep) -> bool:
        """Check if switch can use simple CASE WHEN syntax"""
        from src.generators.actions.switch_optimizer import SwitchOptimizer

        return SwitchOptimizer.detect_simple_switch(step.cases, step.switch_expression)
