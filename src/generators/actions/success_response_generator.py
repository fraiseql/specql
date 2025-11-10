"""
Success Response Generator

Generates complete mutation_result success responses with object data and relationships.
"""


from src.generators.actions.action_context import ActionContext


class SuccessResponseGenerator:
    """Generates success responses for mutation_result"""

    def generate_object_data(self, context: ActionContext) -> str:
        """
        Generate object_data JSONB construction with relationships

        Args:
            context: ActionContext with entity and impact information

        Returns:
            PL/pgSQL code to build object_data
        """
        entity_name = context.entity_name
        schema = context.entity_schema
        entity_lower = entity_name.lower()

        # Check if entity should use table view (denormalized data)
        if (
            hasattr(context.entity, "should_generate_table_view")
            and context.entity.should_generate_table_view
        ):
            # Return from tv_ (denormalized data)
            table_name = f"{schema}.tv_{entity_lower}"
            object_sql = f"""
    -- Build result from table view (denormalized)
    SELECT data  -- JSONB from tv_
    FROM {table_name}
    WHERE pk_{entity_lower} = v_pk
    INTO v_result.object_data;
"""
        else:
            # Return from tb_ (normalized, build JSONB)
            table_name = f"{schema}.tb_{entity_lower}"

            # Build basic object structure
            object_parts = [f"'__typename', '{entity_name}'", "'id', c.id"]

            # Add fields from impact declaration
            if context.impact and "primary" in context.impact:
                primary = context.impact["primary"]
                if "fields" in primary:
                    for field in primary["fields"]:
                        object_parts.append(f"'{field}', c.{field}")

            # Handle relationships if specified
            if context.impact and "primary" in context.impact:
                primary = context.impact["primary"]
                if "include_relations" in primary:
                    for relation in primary["include_relations"]:
                        # For now, add placeholder - real implementation would need FK resolution
                        object_parts.append(
                            f"'{relation}', null  -- TODO: Implement {relation} relationship"
                        )

            # Build the JSONB construction
            separator = ",\n        "
            object_sql = f"""
    -- Build complete object data with relationships
    SELECT jsonb_build_object(
        {separator.join(object_parts)}
    )
    FROM {table_name} c
    WHERE c.pk_{entity_name.lower()} = v_pk
    INTO v_result.object_data;
"""

        return object_sql

    def generate_success_response(self, context: ActionContext) -> str:
        """
        Generate complete success response construction

        Args:
            context: ActionContext with function details

        Returns:
            PL/pgSQL code for complete success response
        """
        parts = []

        # Status and message
        parts.append("""
    -- Set success status
    v_result.status := 'success';
    v_result.message := 'Operation completed successfully';
""")

        # Object data
        parts.append(self.generate_object_data(context))

        # Updated fields (from impact)
        if context.impact and "primary" in context.impact:
            primary = context.impact["primary"]
            if "fields" in primary:
                fields_array = ", ".join(f"'{field}'" for field in primary["fields"])
                parts.append(f"""
    -- Set updated fields
    v_result.updated_fields := ARRAY[{fields_array}];
""")

        # Extra metadata (impact + side effects)
        if context.has_impact_metadata:
            parts.append("""
    -- Build extra metadata with impact information
    v_result.extra_metadata := jsonb_build_object(
        '_meta', to_jsonb(v_meta)
    );
""")
        else:
            parts.append("""
    -- No extra metadata
    v_result.extra_metadata := '{}'::jsonb;
""")

        return "\n".join(parts)
