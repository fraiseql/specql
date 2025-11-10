"""
Refresh Table View Step Compiler

Compiles 'refresh_table_view' steps to PL/pgSQL PERFORM calls for tv_ refresh functions.

Example SpecQL:
    - refresh_table_view:
        scope: self
        propagate: [author, book]

Generated PL/pgSQL:
    -- Refresh table view (self + propagate)
    PERFORM library.refresh_tv_review(v_pk_review);

    -- Refresh author (recalculate average_rating)
    PERFORM crm.refresh_tv_user(v_fk_author);

    -- Refresh book (recalculate review_count)
    PERFORM library.refresh_tv_book(v_fk_book);
"""

from src.core.ast_models import ActionStep, EntityDefinition, RefreshScope


class RefreshTableViewStepCompiler:
    """Compiles refresh_table_view steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile refresh_table_view step to PL/pgSQL

        Args:
            step: ActionStep with type='refresh_table_view'
            entity: EntityDefinition
            context: Compilation context with entity registry, FK mappings, etc.

        Returns:
            PL/pgSQL PERFORM calls for tv_ refresh functions
        """
        if step.type != "refresh_table_view":
            raise ValueError(f"Expected refresh_table_view step, got {step.type}")

        entity_lower = entity.name.lower()
        pk_var = f"v_pk_{entity_lower}"

        if step.refresh_scope == RefreshScope.SELF:
            # Refresh only this entity's tv_ row
            return f"""
    -- Refresh table view (self)
    PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});
""".strip()

        elif step.refresh_scope == RefreshScope.PROPAGATE:
            # Refresh this entity + specific related entities
            lines = [
                "-- Refresh table view (self + propagate)",
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});",
            ]

            # Refresh specified related entities
            if step.propagate_entities:
                fk_vars = context.get("fk_vars", {})
                for rel_entity_name in step.propagate_entities:
                    # Get FK for this relation - try context first, then derive
                    fk_var = fk_vars.get(rel_entity_name.lower()) or self._get_fk_var_for_entity(
                        entity, rel_entity_name, context
                    )

                    if fk_var:
                        # Get the actual entity name that this field references
                        field_def = entity.fields.get(rel_entity_name)
                        if field_def and field_def.is_reference() and field_def.reference_entity:
                            actual_entity_name = field_def.reference_entity
                            if actual_entity_name:  # Additional check for type safety
                                rel_schema = self._get_entity_schema(actual_entity_name, context)  # type: ignore
                                entity_name_lower = actual_entity_name.lower()  # type: ignore
                                lines.append(
                                    f"PERFORM {rel_schema}.refresh_tv_{entity_name_lower}({fk_var});"
                                )

            return "\n    ".join(lines)

        elif step.refresh_scope == RefreshScope.RELATED:
            # Refresh this entity + all entities that reference it
            lines = [
                "-- Refresh table view (self + all related)",
                f"PERFORM {entity.schema}.refresh_tv_{entity_lower}({pk_var});",
            ]

            # Find all entities that reference this one
            dependent_entities = self._find_dependent_entities(entity, context)
            for rel_entity in dependent_entities:
                rel_lower = rel_entity.name.lower()
                rel_schema = rel_entity.schema

                # Refresh all rows that reference this entity
                lines.append(
                    f"-- Refresh {rel_entity.name} entities that reference this {entity.name}"
                )
                lines.append(
                    f"PERFORM {rel_schema}.refresh_tv_{rel_lower}_by_{entity_lower}({pk_var});"
                )

            return "\n    ".join(lines)

        elif step.refresh_scope == RefreshScope.BATCH:
            # Deferred refresh (collect PKs, refresh at end)
            return f"""
    -- Queue for batch refresh (deferred)
    INSERT INTO pg_temp.tv_refresh_queue VALUES ('{entity.name}', {pk_var});
""".strip()

        else:
            raise ValueError(f"Unknown refresh scope: {step.refresh_scope}")

    def _get_fk_var_for_entity(
        self, entity: EntityDefinition, ref_entity_name: str, context: dict
    ) -> str | None:
        """
        Get FK variable name for referenced entity.

        Args:
            entity: The current entity
            ref_entity_name: Name of the referenced entity
            context: Compilation context

        Returns:
            FK variable name (e.g., 'v_fk_author') or None if not found
        """
        # Look for fields that reference this entity
        for field_name, field_def in entity.fields.items():
            if field_def.is_reference() and field_def.reference_entity == ref_entity_name:
                return f"v_fk_{field_name.lower()}"

        return None

    def _get_entity_schema(self, entity_name: str | None, context: dict) -> str:
        """
        Get schema for an entity name.

        Args:
            entity_name: Name of the entity
            context: Compilation context with entity registry

        Returns:
            Schema name (e.g., 'crm', 'library')
        """
        if not entity_name:
            # Fallback: assume same schema as current entity
            current_entity = context.get("current_entity")
            if current_entity:
                return current_entity.schema
            return "public"

        # Try to get from context entity registry
        entity_registry = context.get("entity_registry", {})
        if entity_name in entity_registry:
            return entity_registry[entity_name].schema

        # Fallback: assume same schema as current entity
        current_entity = context.get("current_entity")
        if current_entity:
            return current_entity.schema

        # Last resort: assume 'public'
        return "public"

    def _find_dependent_entities(
        self, entity: EntityDefinition, context: dict
    ) -> list[EntityDefinition]:
        """
        Find entities that have foreign keys to this entity.

        Args:
            entity: The entity to find dependents for
            context: Compilation context with entity registry

        Returns:
            List of EntityDefinition that reference this entity
        """
        dependent_entities = []
        entity_registry = context.get("entity_registry", {})

        for other_entity in entity_registry.values():
            if other_entity.name == entity.name:
                continue  # Skip self

            # Check if this entity has FKs to our entity
            for field_name, field_def in other_entity.fields.items():
                if field_def.is_reference() and field_def.reference_entity == entity.name:
                    dependent_entities.append(other_entity)
                    break

        return dependent_entities
