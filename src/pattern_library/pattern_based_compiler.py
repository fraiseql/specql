"""
Pattern-based PostgreSQL compiler that uses the pattern library instead of hard-coded compilers.

This demonstrates Phase B2 completion: PostgreSQL generation via pattern library templates.
"""

from typing import Any, Dict, List, Optional
from src.pattern_library.api import PatternLibrary


class PatternBasedCompiler:
    """
    PostgreSQL compiler that uses pattern library templates instead of hard-coded logic.

    This replaces the individual step compiler classes with a unified pattern-based approach.
    """

    def __init__(self, db_path: str = "pattern_library.db"):
        """
        Initialize with pattern library

        Args:
            db_path: Path to pattern library database
        """
        self.library = PatternLibrary(db_path)

    def compile_action_step(
        self,
        step_type: str,
        context: Dict[str, Any],
        entity: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compile an action step using pattern library

        Args:
            step_type: Type of step (declare, if, insert, etc.)
            context: Variables and context for template rendering
            entity: Entity information for table operations

        Returns:
            Compiled PostgreSQL code
        """
        try:
            return self.library.compile_pattern(
                pattern_name=step_type,
                language_name="postgresql",
                context=context
            )
        except ValueError as e:
            raise ValueError(f"Failed to compile step '{step_type}': {e}")

    def compile_action_steps(
        self,
        steps: List[Dict[str, Any]],
        entity: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compile multiple action steps

        Args:
            steps: List of step dictionaries with 'type' and other fields
            entity: Entity information

        Returns:
            Combined PostgreSQL code for all steps
        """
        compiled_steps = []

        for step in steps:
            step_type = step.get('type')
            if not step_type:
                continue

            # Prepare context from step fields
            context = dict(step)
            context.pop('type', None)  # Remove type from context

            # Add entity info if available
            if entity:
                context.update({
                    'table_name': f"{entity.get('schema', 'public')}.tb_{entity.get('name', '').lower()}",
                    'pk_column': f"pk_{entity.get('name', '').lower()}",
                    'entity_name': entity.get('name', '')
                })

            try:
                compiled = self.compile_action_step(step_type, context, entity)
                compiled_steps.append(compiled)
            except ValueError as e:
                # For now, skip steps we can't compile
                print(f"Warning: Skipping step {step_type}: {e}")
                continue

        return "\n\n".join(compiled_steps)

    # ===== Convenience methods for common patterns =====

    def compile_declare(
        self,
        variable_name: str,
        variable_type: str,
        default_value: Optional[str] = None
    ) -> str:
        """Compile a declare statement"""
        return self.compile_action_step("declare", {
            "variable_name": variable_name,
            "variable_type": variable_type,
            "default_value": default_value
        })

    def compile_assign(
        self,
        variable_name: str,
        expression: str
    ) -> str:
        """Compile an assignment"""
        return self.compile_action_step("assign", {
            "variable_name": variable_name,
            "expression": expression
        })

    def compile_if(
        self,
        condition: str,
        then_steps: List[Dict[str, Any]],
        else_steps: Optional[List[Dict[str, Any]]] = None,
        entity: Optional[Dict[str, Any]] = None
    ) -> str:
        """Compile an if statement"""
        # Compile nested steps
        then_body = self.compile_action_steps(then_steps, entity)
        else_body = ""
        if else_steps:
            else_body = self.compile_action_steps(else_steps, entity)

        return self.compile_action_step("if", {
            "condition": condition,
            "then_steps": then_body,
            "else_steps": else_body,
            "fields_to_fetch": [],  # Would need to be determined from condition
            "variables": [],  # Would need to be determined
            "table_name": entity.get('table_name') if entity else "",
            "pk_column": entity.get('pk_column') if entity else ""
        }, entity)

    def compile_insert(
        self,
        entity: Dict[str, Any],
        fields: Dict[str, Any],
        result_variable: Optional[str] = None
    ) -> str:
        """Compile an insert statement"""
        return self.compile_action_step("insert", {
            "entity": entity.get('name', ''),
            "columns": list(fields.keys()),
            "values": list(fields.values()),
            "table_name": f"{entity.get('schema', 'public')}.tb_{entity.get('name', '').lower()}",
            "pk_column": f"pk_{entity.get('name', '').lower()}",
            "result_variable": result_variable or f"v_{entity.get('name', '').lower()}_id"
        }, entity)

    def compile_update(
        self,
        entity: Dict[str, Any],
        set_clause: str,
        where_clause: Optional[str] = None
    ) -> str:
        """Compile an update statement"""
        return self.compile_action_step("update", {
            "entity": entity.get('name', ''),
            "set_clause": set_clause,
            "where_clause": where_clause,
            "table_name": f"{entity.get('schema', 'public')}.tb_{entity.get('name', '').lower()}"
        }, entity)

    def compile_query(
        self,
        sql: str,
        into_variable: str
    ) -> str:
        """Compile a query statement"""
        return self.compile_action_step("query", {
            "sql": sql,
            "into_variable": into_variable
        })

    def compile_return(
        self,
        expression: str
    ) -> str:
        """Compile a return statement"""
        return self.compile_action_step("return", {
            "expression": expression
        })

    def close(self):
        """Close pattern library connection"""
        self.library.close()


# ===== Example usage and testing =====

def test_pattern_based_compiler():
    """Test the pattern-based compiler with sample actions"""

    compiler = PatternBasedCompiler()

    # Test declare
    declare_sql = compiler.compile_declare("total", "NUMERIC", "0")
    print("DECLARE:", declare_sql)

    # Test assign
    assign_sql = compiler.compile_assign("total", "total + 100")
    print("ASSIGN:", assign_sql)

    # Test query
    query_sql = compiler.compile_query("SELECT COUNT(*) FROM users", "user_count")
    print("QUERY:", query_sql)

    # Test return
    return_sql = compiler.compile_return("user_count")
    print("RETURN:", return_sql)

    # Test insert
    entity = {"name": "User", "schema": "public"}
    insert_sql = compiler.compile_insert(entity, {"name": "'John'", "email": "'john@example.com'"})
    print("INSERT:", insert_sql)

    # Test update
    update_sql = compiler.compile_update(entity, "name = 'Jane'", "pk_user = v_user_id")
    print("UPDATE:", update_sql)

    compiler.close()


if __name__ == "__main__":
    test_pattern_based_compiler()