"""
Mutation Impacts Generator

Generates JSON metadata describing the impacts of mutations on entities and cache invalidation
requirements for frontend applications. This enables intelligent cache management and UI updates
after mutations.

Output: mutation-impacts.json
"""

import json
from pathlib import Path
from typing import Any

from src.core.ast_models import Action, ActionImpact, Entity


class MutationImpactsGenerator:
    """
    Generates mutation impact metadata for frontend cache management.

    This generator analyzes actions and their impacts to create a comprehensive
    mapping of how mutations affect entities and what cache invalidations are needed.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the mutation-impacts.json file
        """
        self.output_dir = output_dir
        self.impacts: dict[str, Any] = {}

    def generate_impacts(self, entities: list[Entity]) -> None:
        """
        Generate mutation impact metadata for all entities.

        Args:
            entities: List of parsed entity definitions
        """
        self.impacts = {
            "version": "1.0.0",
            "description": "Mutation impact metadata for frontend cache management",
            "mutations": {},
            "entities": {},
            "cacheInvalidationRules": [],
        }

        for entity in entities:
            self._process_entity(entity)

        # Write to file
        output_file = self.output_dir / "mutation-impacts.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.impacts, f, indent=2, ensure_ascii=False)

    def _process_entity(self, entity: Entity) -> None:
        """
        Process a single entity and its actions.

        Args:
            entity: The entity to process
        """
        entity_name = entity.name

        # Add entity metadata
        self.impacts["entities"][entity_name] = {
            "schema": entity.schema,
            "table": entity.table or f"tb_{entity_name.lower()}",
            "hasTableView": entity.table is not None,
            "hierarchical": entity.hierarchical,
        }

        # Process each action
        for action in entity.actions:
            self._process_action(entity, action)

    def _process_action(self, entity: Entity, action: Action) -> None:
        """
        Process a single action and its impacts.

        Args:
            entity: The entity containing the action
            action: The action to process
        """
        mutation_name = f"{entity.name}.{action.name}"
        app_mutation_name = f"app.{action.name}"

        mutation_impact = {
            "entity": entity.name,
            "action": action.name,
            "appFunction": app_mutation_name,
            "coreFunction": f"{entity.schema}.{action.name}",
            "operationType": self._detect_operation_type(action.name),
            "requiresPermission": action.requires is not None,
            "permissionExpression": action.requires,
            "impacts": self._build_impact_metadata(action.impact),
            "cacheInvalidations": self._build_cache_invalidations(action.impact),
            "optimisticUpdates": self._build_optimistic_updates(action.impact),
            "sideEffects": self._build_side_effects(action.impact),
        }

        self.impacts["mutations"][mutation_name] = mutation_impact

        # Add to global cache invalidation rules
        if action.impact and action.impact.cache_invalidations:
            for invalidation in action.impact.cache_invalidations:
                rule = {
                    "mutation": mutation_name,
                    "query": invalidation.query,
                    "filter": invalidation.filter,
                    "strategy": invalidation.strategy,
                    "reason": invalidation.reason,
                }
                self.impacts["cacheInvalidationRules"].append(rule)

    def _detect_operation_type(self, action_name: str) -> str:
        """
        Detect the operation type from action name.

        Args:
            action_name: Name of the action

        Returns:
            Operation type: CREATE, UPDATE, DELETE, or CUSTOM
        """
        if action_name.startswith("create_"):
            return "CREATE"
        elif action_name.startswith("update_"):
            return "UPDATE"
        elif action_name.startswith("delete_"):
            return "DELETE"
        else:
            return "CUSTOM"

    def _build_impact_metadata(self, impact: ActionImpact | None) -> dict[str, Any]:
        """
        Build impact metadata for an action.

        Args:
            impact: The action impact metadata

        Returns:
            Dictionary with impact information
        """
        if not impact:
            return {"hasPrimaryImpact": False, "hasSideEffects": False, "affectedEntities": []}

        affected_entities = [impact.primary.entity] if impact.primary else []
        affected_entities.extend([side.entity for side in impact.side_effects])

        return {
            "hasPrimaryImpact": impact.primary is not None,
            "hasSideEffects": len(impact.side_effects) > 0,
            "affectedEntities": list(set(affected_entities)),  # Remove duplicates
            "primaryEntity": impact.primary.entity if impact.primary else None,
            "primaryOperation": impact.primary.operation if impact.primary else None,
            "primaryFields": impact.primary.fields if impact.primary else [],
        }

    def _build_cache_invalidations(self, impact: ActionImpact | None) -> list[dict[str, Any]]:
        """
        Build cache invalidation specifications.

        Args:
            impact: The action impact metadata

        Returns:
            List of cache invalidation rules
        """
        if not impact or not impact.cache_invalidations:
            return []

        return [
            {
                "query": inv.query,
                "filter": inv.filter or {},
                "strategy": inv.strategy,
                "reason": inv.reason,
            }
            for inv in impact.cache_invalidations
        ]

    def _build_optimistic_updates(self, impact: ActionImpact | None) -> dict[str, Any]:
        """
        Build optimistic update specifications for frontend cache.

        Args:
            impact: The action impact metadata

        Returns:
            Optimistic update configuration
        """
        if not impact or not impact.primary:
            return {"enabled": False}

        primary = impact.primary

        # For simple operations, we can suggest optimistic updates
        if primary.operation in ["CREATE", "UPDATE", "DELETE"]:
            return {
                "enabled": True,
                "entity": primary.entity,
                "operation": primary.operation,
                "fields": primary.fields,
                "requiresRefetch": len(primary.fields) == 0,  # If no fields specified, refetch
            }

        return {"enabled": False}

    def _build_side_effects(self, impact: ActionImpact | None) -> list[dict[str, Any]]:
        """
        Build side effects metadata.

        Args:
            impact: The action impact metadata

        Returns:
            List of side effect specifications
        """
        if not impact or not impact.side_effects:
            return []

        return [
            {
                "entity": side.entity,
                "operation": side.operation,
                "fields": side.fields,
                "collection": side.collection,
            }
            for side in impact.side_effects
        ]
