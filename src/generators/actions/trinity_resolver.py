"""
Trinity Pattern Resolver

Converts UUID (public ID) to INTEGER (internal pk_*) for function logic.
All database operations use INTEGER pk_* for efficiency.
"""


class TrinityResolver:
    """Resolves UUID to INTEGER pk_* using Trinity helper functions"""

    def generate_pk_lookup(self, entity_name: str, schema: str, id_var: str = "p_id") -> str:
        """
        Generate PL/pgSQL code to resolve UUID → INTEGER pk_*

        Args:
            entity_name: Entity name (e.g., "Contact")
            schema: Schema name (e.g., "crm")
            id_var: Variable name containing UUID

        Returns:
            PL/pgSQL code for Trinity resolution

        Example output:
            -- Trinity Pattern: Resolve UUID → INTEGER pk_*
            v_pk := crm.contact_pk(p_contact_id);
            IF v_pk IS NULL THEN
                v_result.status := 'error';
                v_result.message := 'Contact not found';
                RETURN v_result;
            END IF;
        """
        entity_lower = entity_name.lower()
        helper_function = f"{schema}.{entity_lower}_pk"

        return f"""
    -- Trinity Pattern: Resolve UUID → INTEGER pk_*
    v_pk := {helper_function}({id_var});
    IF v_pk IS NULL THEN
        v_result.status := 'error';
        v_result.message := '{entity_name} not found';
        RETURN v_result;
    END IF;
"""

    def generate_id_lookup(self, entity_name: str, schema: str, pk_var: str = "v_pk") -> str:
        """
        Generate PL/pgSQL code to resolve INTEGER pk_* → UUID

        Example output:
            v_id := crm.contact_id(v_pk);
        """
        entity_lower = entity_name.lower()
        helper_function = f"{schema}.{entity_lower}_id"

        return f"    v_id := {helper_function}({pk_var});"
