"""
Generate identifier recalculation functions for composite identifiers

When a referenced entity's identifier changes, composite identifiers
that include it must be recalculated.
"""


class CompositeIdentifierGenerator:
    """Generate recalculation functions for composite identifiers"""

    def generate_recalc_function(self, entity) -> str:
        """
        Generate function to recalculate composite identifier

        Example for Allocation:
        - tenant_identifier
        - machine.path_identifier
        - location.path_identifier
        - daterange

        When machine or location changes, recalculate allocation identifier

        Args:
            entity: Entity with composite identifier

        Returns:
            SQL function as string
        """
        # Check if entity has composite identifier
        if not hasattr(entity, "identifier") or not entity.identifier:
            return ""

        # Check for composite field (this might be stored differently)
        composite_parts = None
        if hasattr(entity.identifier, "composite") and entity.identifier.composite:
            composite_parts = entity.identifier.composite
        elif hasattr(entity.identifier, "get") and entity.identifier.get("composite"):
            composite_parts = entity.identifier.get("composite")

        if not composite_parts:
            return ""

        func_name = f"recalculate_{entity.name.lower()}_identifier"

        # Generate SQL function
        return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(p_id UUID)
RETURNS VOID AS $$
DECLARE
    v_new_identifier TEXT;
BEGIN
    -- Recalculate composite identifier
    SELECT {self._generate_identifier_calculation(composite_parts, entity)}
    INTO v_new_identifier
    FROM {entity.schema}.tb_{entity.name.lower()}
    WHERE id = p_id;

    -- Update identifier
    UPDATE {entity.schema}.tb_{entity.name.lower()}
    SET identifier = v_new_identifier
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""
        if not entity.identifier or not entity.identifier.get("composite"):
            return ""

        func_name = f"recalculate_{entity.name.lower()}_identifier"

        # Generate SQL function
        return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(p_id UUID)
RETURNS VOID AS $$
DECLARE
    v_new_identifier TEXT;
BEGIN
    -- Recalculate composite identifier
    SELECT {self._generate_identifier_calculation(entity)}
    INTO v_new_identifier
    FROM {entity.schema}.tb_{entity.name.lower()}
    WHERE id = p_id;

    -- Update identifier
    UPDATE {entity.schema}.tb_{entity.name.lower()}
    SET identifier = v_new_identifier
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""

    def _generate_identifier_calculation(self, composite_parts, entity) -> str:
        """
        Generate SQL to calculate composite identifier

        Parts separated by '|'

        Args:
            composite_parts: List of composite identifier parts
            entity: Entity with composite identifier

        Returns:
            SQL expression for identifier calculation
        """
        # Generate SQL fragments
        fragments = []
        for part in composite_parts:
            if "." in part:
                # Referenced entity's identifier
                ref_entity, field = part.split(".")
                fragments.append(f"{ref_entity}_{field}")
            else:
                # Own field
                fragments.append(part)

        # Join with ||'|'||
        sql = " || '|' || ".join(fragments)

        return sql
