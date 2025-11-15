"""Base class for step compilers"""

from abc import ABC, abstractmethod

from src.core.ast_models import ActionStep, EntityDefinition


class StepCompiler(ABC):
    """Base class for all step compilers"""

    @abstractmethod
    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile a step to PL/pgSQL

        Args:
            step: The action step to compile
            entity: The entity definition
            context: Compilation context (variables, CTEs, etc.)

        Returns:
            PL/pgSQL code for this step
        """
        pass