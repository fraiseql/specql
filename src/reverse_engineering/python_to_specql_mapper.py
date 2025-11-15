from typing import List
from src.core.ast_models import Action, ActionStep
from src.reverse_engineering.protocols import ParsedMethod, ParsedEntity
from src.reverse_engineering.python_statement_analyzer import (
    PythonStatementAnalyzer,
    PythonStatement
)

class PythonToSpecQLMapper:
    """
    Map Python methods to SpecQL actions

    Converts Python method body to SpecQL action steps
    """

    def __init__(self):
        self.analyzer = PythonStatementAnalyzer()

    def map_method_to_action(
        self,
        method: ParsedMethod,
        entity: ParsedEntity
    ) -> Action:
        """
        Map Python method to SpecQL action

        Example:
        ```python
        def qualify_lead(self) -> bool:
            if self.status != "lead":
                return False
            self.status = "qualified"
            return True
        ```

        Maps to:
        ```yaml
        - name: qualify_lead
          steps:
            - validate: status = 'lead'
            - update: Contact SET status = 'qualified'
        ```
        """
        # Analyze method body
        statements = self.analyzer.analyze_method_body(method.body_lines)

        # Map statements to SpecQL steps
        steps = []
        for stmt in statements:
            specql_steps = self._map_statement(stmt, entity)
            steps.extend(specql_steps)

        # Create Action
        return Action(
            name=method.method_name,
            steps=steps,
        )

    def _map_statement(
        self,
        stmt: PythonStatement,
        entity: ParsedEntity
    ) -> List[ActionStep]:
        """Map single Python statement to SpecQL steps"""

        if stmt.statement_type == 'if':
            return self._map_if_statement(stmt, entity)

        elif stmt.statement_type == 'assign':
            return self._map_assign_statement(stmt, entity)

        elif stmt.statement_type == 'return':
            return self._map_return_statement(stmt)

        elif stmt.statement_type == 'call':
            return self._map_call_statement(stmt)

        elif stmt.statement_type == 'for':
            return self._map_for_statement(stmt, entity)

        elif stmt.statement_type == 'raise':
            return self._map_raise_statement(stmt)

        return []

    def _map_if_statement(
        self,
        stmt: PythonStatement,
        entity: ParsedEntity
    ) -> List[ActionStep]:
        """
        Map if statement

        Python: if self.status != "lead": return False
        SpecQL: validate: status = 'lead'
        """
        condition = stmt.metadata['condition']

        # Detect validation pattern (if condition: return/raise)
        then_body = stmt.metadata['then_body']
        if then_body and ('return False' in then_body[0] or 'raise' in then_body[0]):
            # This is a validation check
            validation_condition = self._invert_condition(condition)

            return [ActionStep(
                type='validate',
                expression=validation_condition,
            )]

        # Regular if/then/else
        then_steps = []
        for line in then_body:
            # Recursively parse then body
            # (simplified - real implementation would use analyzer)
            pass

        else_steps = []
        for line in stmt.metadata.get('else_body', []):
            # Recursively parse else body
            pass

        return [ActionStep(
            type='if',
            condition=self._normalize_condition(condition, entity),
            then_steps=then_steps,
            else_steps=else_steps if else_steps else [],
        )]

    def _map_assign_statement(
        self,
        stmt: PythonStatement,
        entity: ParsedEntity
    ) -> List[ActionStep]:
        """
        Map assignment statement

        Python: self.status = "qualified"
        SpecQL: update: Contact SET status = 'qualified'
        """
        target = stmt.metadata['targets'][0]
        value = stmt.metadata['value']

        # Detect self.field = value (entity field update)
        if target.startswith('self.'):
            field_name = target[5:]  # Remove 'self.'

            # Check if this is an entity field
            if any(f.field_name == field_name for f in entity.fields):
                return [ActionStep(
                    type='update',
                    entity=entity.entity_name,
                    fields={field_name: value},
                )]

        # Variable assignment (not entity field)
        return [ActionStep(
            type='assign',
            function_name=target,
            arguments={'expression': value},
        )]

    def _map_return_statement(self, stmt: PythonStatement) -> List[ActionStep]:
        """Map return statement"""
        return_value = stmt.metadata['value']

        return [ActionStep(
            type='return',
            arguments={'value': return_value} if return_value else {},
        )]

    def _map_call_statement(self, stmt: PythonStatement) -> List[ActionStep]:
        """
        Map function call

        Python: send_email(self.email, "Welcome")
        SpecQL: call: send_email(email, "Welcome")
        """
        function = stmt.metadata['function']
        args = stmt.metadata['args']

        return [ActionStep(
            type='call',
            function_name=function,
            arguments={f'arg_{i}': arg for i, arg in enumerate(args)},
        )]

    def _map_for_statement(
        self,
        stmt: PythonStatement,
        entity: ParsedEntity
    ) -> List[ActionStep]:
        """
        Map for loop

        Python: for item in items: process(item)
        SpecQL: foreach: item in items DO ...
        """
        target = stmt.metadata['target']
        iter_expr = stmt.metadata['iter']
        stmt.metadata['body']

        # Parse body (simplified)
        body_steps = []

        return [ActionStep(
            type='foreach',
            function_name=target,
            arguments={'collection': iter_expr},
            then_steps=body_steps,
        )]

    def _map_raise_statement(self, stmt: PythonStatement) -> List[ActionStep]:
        """
        Map raise statement

        Python: raise ValueError("Invalid status")
        SpecQL: validate: <opposite condition>
        """
        exception = stmt.metadata['exception']

        return [ActionStep(
            type='raise',
            arguments={'exception': exception},
        )]

    def _invert_condition(self, condition: str) -> str:
        """
        Invert Python condition

        self.status != "lead" → self.status = "lead"
        """
        # Simple inversion (real implementation would use AST)
        if '!=' in condition:
            return condition.replace('!=', '=')
        elif '==' in condition:
            return condition.replace('==', '!=')
        else:
            return f"not ({condition})"

    def _normalize_condition(self, condition: str, entity: ParsedEntity) -> str:
        """
        Normalize Python condition to SpecQL

        self.status == "lead" → status = 'lead'
        """
        # Remove 'self.' prefix
        normalized = condition.replace('self.', '')

        # Replace Python operators with SQL
        normalized = normalized.replace('==', '=')
        normalized = normalized.replace('and', 'AND')
        normalized = normalized.replace('or', 'OR')

        # Replace Python strings (") with SQL strings (')
        normalized = normalized.replace('"', "'")

        return normalized