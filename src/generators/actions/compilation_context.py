"""Compilation context for tracking state across step compilation"""

from dataclasses import dataclass, field


@dataclass
class CompilationContext:
    """Shared context for step compilation"""

    # CTE tracking
    ctes: list[dict] = field(default_factory=list)

    # Variable tracking
    declared_variables: dict[str, str] = field(default_factory=dict)  # name -> type

    # Function context
    schema: str = ""
    function_name: str = ""
    parameters: dict[str, str] = field(default_factory=dict)

    # Loop tracking
    loop_stack: list[dict] = field(default_factory=list)  # Track nested loops

    # Exception context
    exception_context: bool = False  # Track if inside exception handler

    def add_cte(self, name: str, query: str, materialized: bool = False):
        """Register a CTE"""
        self.ctes.append({
            "name": name,
            "query": query.strip(),
            "materialized": materialized
        })

    def add_variable(self, name: str, var_type: str):
        """Register a declared variable"""
        self.declared_variables[name] = var_type

    def has_ctes(self) -> bool:
        """Check if any CTEs are registered"""
        return len(self.ctes) > 0

    def get_with_clause(self) -> str:
        """Build WITH clause from CTEs"""
        if not self.has_ctes():
            return ""

        cte_defs = []
        for cte in self.ctes:
            mat = " MATERIALIZED" if cte["materialized"] else ""
            cte_defs.append(f"{cte['name']} AS{mat} (\n{cte['query']}\n)")

        return "WITH " + ",\n".join(cte_defs) + "\n"

    def enter_loop(self, loop_type: str, variables: list[str]):
        """Enter a loop context"""
        self.loop_stack.append({
            "type": loop_type,
            "variables": variables,
            "depth": len(self.loop_stack)
        })

    def exit_loop(self):
        """Exit loop context"""
        if self.loop_stack:
            self.loop_stack.pop()

    def get_current_loop_depth(self) -> int:
        """Get current loop nesting depth"""
        return len(self.loop_stack)

    def is_in_exception_handler(self) -> bool:
        """Check if currently inside an exception handler"""
        return self.exception_context

    def enter_exception_handler(self):
        """Enter exception handling context"""
        self.exception_context = True

    def exit_exception_handler(self):
        """Exit exception handling context"""
        self.exception_context = False