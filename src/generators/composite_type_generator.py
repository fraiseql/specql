"""
Composite Type Generator (Team B)
Generates PostgreSQL composite types for action inputs
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, Entity, FieldDefinition


class CompositeTypeGenerator:
    """Generates app.type_*_input composite types from actions"""

    # Field type mappings: SpecQL → PostgreSQL composite type fields
    TYPE_MAPPINGS = {
        "text": "TEXT",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMPTZ",
        "uuid": "UUID",
        "json": "JSONB",
        "decimal": "DECIMAL",
    }

    def generate_input_type(self, entity: Entity, action: Action) -> str:
        """
        Generate composite type for action input

        Args:
            entity: Entity containing the action
            action: Action to generate input type for

        Returns:
            SQL for composite type creation
        """
        # Determine fields needed for this action
        fields = self._determine_action_fields(entity, action)

        if not fields:
            return ""  # No input type needed

        type_name = f"type_{action.name}_input"
        graphql_name = self._to_pascal_case(action.name) + "Input"

        # Prepare fields for template
        prepared_fields = self._prepare_fields(fields, type_name)

        # Generate field comments
        field_comments = self._generate_field_comments(type_name, fields)

        context = {
            "type_name": type_name,
            "action_name": action.name,
            "graphql_name": graphql_name,
            "fields": prepared_fields,
            "field_comments": field_comments,
        }

        template = self.env.get_template("composite_type.sql.j2")
        return template.render(**context)

    def _determine_action_fields(
        self, entity: Entity, action: Action
    ) -> dict[str, FieldDefinition]:
        """
        Determine which fields are needed for action input

        Strategy:
        - For create actions: all entity fields
        - For update actions: all mutable fields
        - For custom actions: parse action steps to identify referenced fields

        Returns:
            Dict mapping API field name → field definition
            ⚠️ Field names are transformed for external API:
              - "company" (ref) → "company_id" (UUID in composite type)
              - Regular fields keep their names
        """
        # Get base fields
        if action.name.startswith("create"):
            base_fields = entity.fields
        elif action.name.startswith("update"):
            # Exclude audit fields but include id for record identification
            base_fields = {
                k: v
                for k, v in entity.fields.items()
                if k not in ["created_at", "created_by", "updated_at", "updated_by"]
            }
            # Add id field for update operations
            base_fields["id"] = FieldDefinition(name="id", type_name="uuid", nullable=False)
        elif action.name.startswith("delete"):
            # Delete actions typically don't need input types (just ID)
            return {}
        else:
            # Custom action - analyze steps to determine required fields
            base_fields = self._analyze_custom_action_fields(action, entity)

        # Transform field names for external API
        api_fields = {}
        for field_name, field_def in base_fields.items():
            if field_def.type_name == "ref":
                # ref fields: append "_id" for external API
                # "company" → "company_id"
                api_field_name = f"{field_name}_id"
            else:
                # Regular fields: keep name as-is
                api_field_name = field_name

            api_fields[api_field_name] = field_def

        return api_fields

    def _prepare_fields(
        self, fields: dict[str, FieldDefinition], type_name: str
    ) -> dict[str, dict[str, Any]]:
        """Prepare fields for template rendering"""
        prepared = {}
        for field_name, field_def in fields.items():
            prepared[field_name] = {
                "pg_type": self._map_field_type(field_def),
                "nullable": field_def.nullable,
            }
        return prepared

    def _generate_field_comments(
        self, type_name: str, fields: dict[str, FieldDefinition]
    ) -> list[str]:
        """Generate FraiseQL field-level comments with YAML metadata"""
        comments = []
        for field_name, field_def in fields.items():
            # Generate GraphQL type for FraiseQL
            graphql_type = self._map_to_graphql_type(field_def)

            # Build description
            description = self._generate_field_description(field_name, field_def)

            # Build YAML annotation
            yaml_parts = [
                f"name: {field_name}",
                f"type: {graphql_type}{'' if field_def.nullable else '!'}",
                f"required: {str(not field_def.nullable).lower()}",
            ]

            if field_def.type_name == "ref":
                yaml_parts.append(f"references: {field_def.reference_entity}")

            if field_def.type_name == "enum" and field_def.values:
                values_str = ", ".join(field_def.values)
                yaml_parts.append(f"enumValues: {values_str}")

            yaml_content = "\n".join(yaml_parts)

            comment = f"""COMMENT ON COLUMN app.{type_name}.{field_name} IS
'{description}

@fraiseql:field
{yaml_content}';"""

            comments.append(comment)
        return comments

    def _generate_field_description(self, field_name: str, field_def: FieldDefinition) -> str:
        """Generate human-readable description for field"""
        base_name = field_name.replace("_id", "") if field_name.endswith("_id") else field_name

        if field_def.type_name == "ref":
            return f"{base_name.title()} reference ({'required' if not field_def.nullable else 'optional'})."
        elif field_def.type_name == "email":
            return f"Email address ({'required' if not field_def.nullable else 'optional'})."
        elif field_def.type_name == "enum":
            values = ", ".join(field_def.values) if field_def.values else "values"
            return f"{base_name.title()} ({values})."
        else:
            return f"{base_name.title()} ({'required' if not field_def.nullable else 'optional'})."

    def _map_to_graphql_type(self, field_def: FieldDefinition) -> str:
        """Map SpecQL field type to GraphQL type for FraiseQL"""
        if field_def.type_name == "ref":
            # References become UUID in GraphQL (external API contract)
            return "UUID"
        elif field_def.type_name == "enum":
            return "String"  # Enums are strings in GraphQL
        elif field_def.type_name == "list":
            base_type = self.TYPE_MAPPINGS.get(field_def.item_type or "text", "String")
            return f"[{base_type}]"
        else:
            # Map PostgreSQL types to GraphQL types
            pg_type = self.TYPE_MAPPINGS.get(field_def.type_name, "String")
            graphql_mappings = {
                "TEXT": "String",
                "INTEGER": "Int",
                "BOOLEAN": "Boolean",
                "DATE": "String",  # ISO date string
                "TIMESTAMPTZ": "String",  # ISO datetime string
                "UUID": "UUID",
                "JSONB": "JSON",
                "DECIMAL": "Float",
            }
            return graphql_mappings.get(pg_type, "String")

    def _map_field_type(self, field_def: FieldDefinition) -> str:
        """
        Map SpecQL field type to PostgreSQL composite type field

        ⚠️ CRITICAL: Composite types represent EXTERNAL API contract
        - Foreign keys: UUID (not INTEGER - GraphQL uses UUIDs)
        - Core layer handles UUID → INTEGER resolution
        """
        if field_def.type_name == "ref":
            # ✅ Foreign keys are UUIDs in API input (not INTEGER!)
            # Core layer will resolve UUID → INTEGER when inserting
            return "UUID"
        elif field_def.type_name == "enum":
            return "TEXT"
        elif field_def.type_name == "list":
            base_type = self.TYPE_MAPPINGS.get(field_def.item_type or "text", "TEXT")
            return f"{base_type}[]"
        else:
            return self.TYPE_MAPPINGS.get(field_def.type_name, "TEXT")

    def _analyze_custom_action_fields(
        self, action: Action, entity: Entity
    ) -> dict[str, FieldDefinition]:
        """
        Analyze custom action steps to determine required input fields

        For custom actions, we typically only need:
        - 'id' field for record identification
        - Any fields that are parameters to the action (not validated against database state)

        Validation expressions check database state, not input parameters.
        Update fields are set to literal values, not taken from input.
        """
        # For now, custom actions only need the id field to identify the record
        # Future: analyze for action parameters beyond just record identification
        return {"id": FieldDefinition(name="id", type_name="uuid", nullable=False)}

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in snake_str.split("_"))

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self._mutation_result_generated = False

    def generate_mutation_result_type(self) -> str:
        """Generate standard mutation_result composite type (once)"""
        if self._mutation_result_generated:
            return ""

        self._mutation_result_generated = True

        return """
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';

COMMENT ON COLUMN app.mutation_result.id IS
'Unique identifier of the affected entity.

@fraiseql:field
name: id
type: UUID!
required: true';

COMMENT ON COLUMN app.mutation_result.updated_fields IS
'Fields that were modified in this mutation.

@fraiseql:field
name: updatedFields
type: [String]
required: false';

COMMENT ON COLUMN app.mutation_result.status IS
  'Status: success, failed:*, warning:*';

COMMENT ON COLUMN app.mutation_result.message IS
'Human-readable success or error message.

@fraiseql:field
name: message
type: String
required: false';

COMMENT ON COLUMN app.mutation_result.object_data IS
'Complete entity data after mutation.

@fraiseql:field
name: object
type: JSON
required: false';

COMMENT ON COLUMN app.mutation_result.extra_metadata IS
'Additional metadata including side effects and impact information.

@fraiseql:field
name: extra
type: JSON
required: false';
"""

    def generate_common_types(self) -> str:
        """Generate all common types needed across schema"""
        types = []

        # Mutation result
        result_type = self.generate_mutation_result_type()
        if result_type:
            types.append(result_type)

        # Standard deletion input (if needed)
        types.append(self._generate_deletion_input_type())

        return "\n\n".join(types)

    def _generate_deletion_input_type(self) -> str:
        """Generate standard deletion input type"""
        return """
CREATE TYPE app.type_deletion_input AS (
    id UUID
);

COMMENT ON TYPE app.type_deletion_input IS
'Input type for deletion operations.

@fraiseql:input
name: DeletionInput';
"""
