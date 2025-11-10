"""
Conditional Compiler - Transform conditional logic to PL/pgSQL control flow
"""

import re
from dataclasses import dataclass

from src.core.ast_models import ActionStep, Entity
from src.utils.safe_slug import safe_slug, safe_table_name


@dataclass
class ConditionalCompiler:
    """Compiles conditional logic (if/then/else, switch) to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: Entity) -> str:
        """Compile conditional step"""
        if step.type == "if":
            return self._compile_if(step, entity)
        elif step.type == "switch":
            return self._compile_switch(step, entity)
        return ""

    def _compile_if(self, step: ActionStep, entity: Entity) -> str:
        """Compile if/then/else"""
        condition = step.condition or ""

        # Extract fields from condition and generate SELECT
        fields_to_fetch = self._extract_fields(condition, entity)
        select_sql = self._generate_select(fields_to_fetch, entity)

        # Replace field names with variables in condition
        condition_vars = self._replace_fields_with_vars(condition, entity)

        then_body = self._compile_steps(step.then_steps or [], entity)
        else_body = self._compile_steps(step.else_steps or [], entity) if step.else_steps else ""

        sql = f"""
    -- If: {condition}
{select_sql}

    IF ({condition_vars}) THEN
        {then_body}
"""
        if else_body:
            sql += f"""
    ELSE
        {else_body}
"""
        sql += """
    END IF;
"""
        return sql

    def _compile_switch(self, step: ActionStep, entity: Entity) -> str:
        """Compile switch/case"""
        expression = step.expression or ""
        cases = step.cases or {}

        case_clauses = []
        for value, case_steps in cases.items():
            body = self._compile_steps(case_steps, entity)
            case_clauses.append(
                f"""
        WHEN '{value}' THEN
            {body}
"""
            )

        return f"""
    CASE {expression}
        {"".join(case_clauses)}
    END CASE;
"""

    def _extract_fields(self, condition: str, entity: Entity) -> list[str]:
        """
        Extract field names from condition expression

        Example:
            "status = 'lead' AND lead_score >= 70"
            → ["status", "lead_score"]
        """
        field_names = list(entity.fields.keys())
        fields_in_condition = []

        for field_name in field_names:
            # Match whole word only (avoid partial matches)
            if re.search(rf"\b{field_name}\b", condition):
                fields_in_condition.append(field_name)

        return fields_in_condition

    def _generate_select(self, fields: list[str], entity: Entity) -> str:
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

    def _replace_fields_with_vars(self, condition: str, entity: Entity) -> str:
        """
        Replace field names with v_field variables

        Example:
            "status = 'lead'" → "v_status = 'lead'"
        """
        field_names = set(entity.fields.keys())

        for field_name in field_names:
            # Replace whole word matches only
            condition = re.sub(rf"\b{re.escape(field_name)}\b", f"v_{field_name}", condition)

        return condition

    def _compile_steps(self, steps: list[ActionStep], entity: Entity) -> str:
        """Compile list of steps (recursive)"""
        # For now, return a simple placeholder - will be enhanced when integrated
        if not steps:
            return "-- No steps"

        compiled = []
        for step in steps:
            if step.type == "update":
                # Simple update compilation for testing
                table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
                pk_column = f"pk_{safe_slug(entity.name)}"
                fields_sql = ", ".join(f"{k} = '{v}'" for k, v in (step.fields or {}).items())
                compiled.append(f"UPDATE {table_name} SET {fields_sql} WHERE {pk_column} = v_pk;")
            elif step.type == "insert":
                # Simple insert compilation for testing
                target_entity = step.entity or entity.name
                table_name = f"{entity.schema}.tb_{safe_slug(target_entity)}_lightweight"
                fields_sql = ", ".join(f"{k} = '{v}'" for k, v in (step.fields or {}).items())
                compiled.append(f"INSERT INTO {table_name} ({fields_sql});")
            else:
                compiled.append(f"-- Unknown step type: {step.type}")

        return "\n        ".join(compiled)
