"""
Duplicate Check Step Compiler

Compiles 'duplicate_check' steps to PL/pgSQL SELECT statements that check
for existing records before INSERT operations. Returns structured NOOP responses
with conflict details when duplicates are found.

Example SpecQL:
    - duplicate_check:
        entity: Contract
        fields: [customer_org, provider_org, customer_contract_id]
        error_message: "Contract already exists for this customer/provider/contract_id"

Generated PL/pgSQL:
    -- Check for duplicate Contract
    SELECT id INTO v_existing_id
    FROM tenant.tb_contract
    WHERE customer_org = input_data.customer_org
      AND provider_org = input_data.provider_org
      AND customer_contract_id = input_data.customer_contract_id
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        -- Load existing object for conflict response
        SELECT data INTO v_existing_object
        FROM tenant.v_contract_projection
        WHERE id = v_existing_id;

        -- Return NOOP with conflict details
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contract',
            v_existing_id,
            'NOOP',
            'noop:already_exists',
            ARRAY[]::TEXT[],
            'Contract already exists for this customer/provider/contract_id',
            v_existing_object,
            v_existing_object,
            jsonb_build_object(
                'trigger', 'api_create',
                'status', 'noop:already_exists',
                'reason', 'unique_constraint_violation',
                'conflict', jsonb_build_object(
                    'customer_org', input_data.customer_org,
                    'provider_org', input_data.provider_org,
                    'customer_contract_id', input_data.customer_contract_id,
                    'conflict_object', v_existing_object
                )
            )
        );
    END IF;
"""

from src.core.ast_models import ActionStep, EntityDefinition


class DuplicateCheckCompiler:
    """Compiles duplicate check steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile duplicate check step to PL/pgSQL

        Args:
            step: ActionStep with type='duplicate_check'
            entity: EntityDefinition
            context: Compilation context

        Returns:
            PL/pgSQL code for duplicate detection
        """
        if step.type != "duplicate_check":
            raise ValueError(f"Expected duplicate_check step, got {step.type}")

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
