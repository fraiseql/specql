"""
If Step Compiler

Compiles 'if' steps to PL/pgSQL conditional logic.

Example SpecQL:
    - if: status = 'lead'
      then:
        - update: status = 'qualified'
      else:
        - update: status = 'nurture'

Generated PL/pgSQL:
    -- If: status = 'lead'
    SELECT status INTO v_status
    FROM crm.tb_contact
    WHERE pk_contact = v_pk;

    IF (v_status = 'lead') THEN
        -- Update: status = 'qualified'
        UPDATE crm.tb_contact
        SET status = 'qualified', updated_at = NOW(), updated_by = v_user_id
        WHERE pk_contact = v_pk;
    ELSE
        -- Update: status = 'nurture'
        UPDATE crm.tb_contact
        SET status = 'nurture', updated_at = NOW(), updated_by = v_user_id
        WHERE pk_contact = v_pk;
    END IF;
"""

from src.core.ast_models import ActionStep, EntityDefinition


class IfStepCompiler:
    """Compiles if/then/else steps to PL/pgSQL"""

    def __init__(self, step_compiler_registry=None):
        """
        Initialize with step compiler registry for compiling nested steps

        Args:
            step_compiler_registry: Dict mapping step types to compilers
        """
        self.step_compiler_registry = step_compiler_registry or {}

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile if step to PL/pgSQL

        Args:
            step: ActionStep with type='if'
            entity: EntityDefinition for table/schema context
            context: Compilation context (variables, etc.)

        Returns:
            PL/pgSQL code for conditional logic
        """
        if step.type != "if":
            raise ValueError(f"Expected if step, got {step.type}")

        condition = step.condition
        if not condition:
            raise ValueError("If step must have a condition")

        # Parse condition to extract field references
        fields_to_fetch = self._extract_fields(condition, entity)

        # Generate SELECT to fetch field values
        select_sql = self._generate_select(fields_to_fetch, entity)

        # Generate IF block with then/else
        if_block_sql = self._generate_if_block(
            condition, step.then_steps, step.else_steps, entity, context
        )

        return f"""
    -- If: {condition}
{select_sql}

{if_block_sql}
"""

    def _extract_fields(self, condition: str, entity: EntityDefinition) -> list[str]:
        """
        Extract field names from condition expression

        Example:
            "status = 'lead' AND lead_score >= 70"
            → ["status", "lead_score"]
        """
        import re

        # Get all field names from entity
        field_names = list(entity.fields.keys())

        # Find which fields are referenced in condition
        fields_in_condition = []
        for field_name in field_names:
            # Match whole word only (avoid partial matches)
            if re.search(rf"\b{field_name}\b", condition):
                fields_in_condition.append(field_name)

        return fields_in_condition

    def _generate_select(self, fields: list[str], entity: EntityDefinition) -> str:
        """
        Generate SELECT statement to fetch field values

        Example:
            SELECT status, lead_score INTO v_status, v_lead_score
            FROM crm.tb_contact
            WHERE pk_contact = v_pk;
        """
        if not fields:
            return ""

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        pk_column = f"pk_{entity_lower}"

        # Build SELECT list with INTO clause
        select_list = ", ".join(fields)
        into_list = ", ".join(f"v_{field}" for field in fields)

        return f"""    SELECT {select_list} INTO {into_list}
    FROM {table_name}
    WHERE {pk_column} = v_pk;"""

    def _generate_if_block(
        self,
        condition: str,
        then_steps: list[ActionStep],
        else_steps: list[ActionStep],
        entity: EntityDefinition,
        context: dict,
    ) -> str:
        """
        Generate IF/THEN/ELSE block

        Args:
            condition: The condition expression
            then_steps: Steps to execute if condition is true
            else_steps: Steps to execute if condition is false
            entity: Entity definition
            context: Compilation context

        Returns:
            PL/pgSQL IF block
        """
        # Replace field names with v_field variables
        check_condition = self._replace_fields_with_vars(condition, entity)

        # Compile then steps
        then_sql = self._compile_steps(then_steps, entity, context)

        # Compile else steps
        else_sql = ""
        if else_steps:
            else_compiled = self._compile_steps(else_steps, entity, context)
            else_sql = f"""
    ELSE{else_compiled}"""

        return f"""    IF ({check_condition}) THEN{then_sql}{else_sql}
    END IF;"""

    def _compile_steps(
        self, steps: list[ActionStep], entity: EntityDefinition, context: dict
    ) -> str:
        """
        Compile a list of steps using the step compiler registry

        Args:
            steps: List of ActionStep to compile
            entity: Entity definition
            context: Compilation context

        Returns:
            Compiled PL/pgSQL for all steps
        """
        if not steps:
            return ""

        compiled_steps = []
        for step in steps:
            compiler = self.step_compiler_registry.get(step.type)
            if not compiler:
                raise ValueError(f"No compiler registered for step type: {step.type}")

            compiled_step = compiler.compile(step, entity, context)
            compiled_steps.append(compiled_step)

        return "\n\n".join(compiled_steps)

    def _replace_fields_with_vars(self, condition: str, entity: EntityDefinition) -> str:
        """
        Replace field names with v_field variables

        Example:
            "status = 'lead'" → "v_status = 'lead'"
        """
        # Replace field names with v_ prefix
        field_names = set(entity.fields.keys())

        for field_name in field_names:
            # Replace whole word matches only
            import re

            condition = re.sub(rf"\b{re.escape(field_name)}\b", f"v_{field_name}", condition)

        return condition
