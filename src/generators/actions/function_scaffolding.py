"""
PL/pgSQL Function Scaffolding Generator

Generates the outer structure of action functions:
- Function signature
- Parameter declarations
- Variable declarations
- Transaction management
- Error handling
- Return type (mutation_result)
"""

from dataclasses import dataclass

from src.core.ast_models import ActionDefinition, EntityDefinition


@dataclass
class FunctionSignature:
    """Function signature definition"""

    function_name: str
    schema: str
    parameters: list[dict[str, str]]  # [{"name": "p_id", "type": "UUID"}]
    returns: str = "mutation_result"


@dataclass
class FunctionScaffolding:
    """Complete function scaffolding"""

    signature: FunctionSignature
    variables: list[str]  # Variable declarations
    body: str  # Function body (will be filled by step compilers)
    error_handling: bool = True


class FunctionScaffoldingGenerator:
    """Generates PL/pgSQL function scaffolding"""

    def generate(self, action: ActionDefinition, entity: EntityDefinition) -> FunctionScaffolding:
        """
        Generate function scaffolding from action definition

        Args:
            action: ActionDefinition from Team A
            entity: EntityDefinition (for context)

        Returns:
            FunctionScaffolding ready for step compilation
        """
        # Generate function signature
        signature = self._generate_signature(action, entity)

        # Generate variable declarations
        variables = self._generate_variables(action, entity)

        return FunctionScaffolding(
            signature=signature,
            variables=variables,
            body="",  # Will be filled by step compilers
            error_handling=True,
        )

    def _generate_signature(
        self, action: ActionDefinition, entity: EntityDefinition
    ) -> FunctionSignature:
        """
        Generate function signature

        Example:
            crm.qualify_lead(p_contact_id UUID, p_caller_id UUID DEFAULT NULL)
        """
        function_name = f"{entity.schema}.{action.name}"

        # Primary parameter: entity ID (UUID)
        entity_lower = entity.name.lower()
        parameters = [{"name": f"p_{entity_lower}_id", "type": "UUID", "required": True}]

        # Caller ID for audit trail (optional)
        parameters.append({"name": "p_caller_id", "type": "UUID", "default": "NULL"})

        # Additional parameters from action metadata
        # TODO: Add support for action parameters when ActionDefinition is extended

        return FunctionSignature(
            function_name=function_name,
            schema=entity.schema,
            parameters=parameters,
            returns="mutation_result",
        )

    def _generate_variables(self, action: ActionDefinition, entity: EntityDefinition) -> list[str]:
        """
        Generate DECLARE block variables

        Standard variables:
        - v_pk: INTEGER (Trinity Pattern pk_*)
        - v_result: mutation_result (return value)
        - v_old_status, v_new_status, etc. (step-specific)
        """
        entity_lower = entity.name.lower()

        variables = [
            f"v_pk INTEGER;  -- Trinity Pattern: pk_{entity_lower}",
            "v_result mutation_result;  -- Return value",
        ]

        # Add entity-specific variables based on fields
        for field_name, field_def in entity.fields.items():
            if self._field_used_in_action(field_name, action):
                pg_type = field_def.postgres_type or "TEXT"
                variables.append(f"v_{field_name} {pg_type};")

        return variables

    def _field_used_in_action(self, field_name: str, action: ActionDefinition) -> bool:
        """Check if field is referenced in action steps"""
        # Simple heuristic: check if field name appears in step expressions
        action_text = str(action.steps)
        return field_name in action_text

    def _map_type_to_postgres(self, specql_type: str) -> str:
        """Map SpecQL type to PostgreSQL type"""
        type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "uuid": "UUID",
            "date": "DATE",
            "datetime": "TIMESTAMPTZ",
        }
        return type_map.get(specql_type, "TEXT")

    def render(self, scaffolding: FunctionScaffolding) -> str:
        """
        Render complete function DDL

        Example output:
            CREATE OR REPLACE FUNCTION crm.qualify_lead(
                p_contact_id UUID,
                p_caller_id UUID DEFAULT NULL
            )
            RETURNS mutation_result AS $$
            DECLARE
                v_pk INTEGER;
                v_result mutation_result;
                v_status TEXT;
            BEGIN
                -- Function body goes here
                {scaffolding.body}

                RETURN v_result;
            EXCEPTION
                WHEN OTHERS THEN
                    v_result.status := 'error';
                    v_result.message := SQLERRM;
                    RETURN v_result;
            END;
            $$ LANGUAGE plpgsql;
        """
        sig = scaffolding.signature

        # Build parameter list
        params = []
        for param in sig.parameters:
            param_def = f"{param['name']} {param['type']}"
            if "default" in param:
                param_def += f" DEFAULT {param['default']}"
            params.append(param_def)

        params_str = ",\n    ".join(params)

        # Build variable declarations
        vars_str = "\n    ".join(scaffolding.variables)

        # Build function
        function_ddl = f"""
CREATE OR REPLACE FUNCTION {sig.function_name}(
    {params_str}
)
RETURNS {sig.returns} AS $$
DECLARE
    {vars_str}
BEGIN
{scaffolding.body}

    RETURN v_result;
"""

        # Add error handling if enabled
        if scaffolding.error_handling:
            function_ddl += """
EXCEPTION
    WHEN OTHERS THEN
        v_result.status := 'error';
        v_result.message := SQLERRM;
        RETURN v_result;
"""

        function_ddl += """
END;
$$ LANGUAGE plpgsql;
"""

        return function_ddl
