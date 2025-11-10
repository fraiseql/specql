"""
Action Compiler - Transform SpecQL actions to PL/pgSQL functions
"""

from enum import Enum

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, Entity


class PostgreSQLType(Enum):
    """PostgreSQL type mappings"""

    TEXT = "TEXT"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    DATE = "DATE"
    JSONB = "JSONB"
    UUID = "UUID"


class ParameterGenerator:
    """Generates function parameters from entity fields"""

    def generate(self, entity: Entity, action: Action) -> list[str]:
        """Generate list of parameter declarations"""
        params = []

        if self._requires_entity_id(action):
            params.append(self._entity_id_param(entity))

        params.extend(self._field_params(entity))
        params.append(self._caller_context_param())

        return params

    def _entity_id_param(self, entity: Entity) -> str:
        """Generate entity ID parameter for update/delete"""
        return f"p_{entity.name.lower()}_id UUID"

    def _field_params(self, entity: Entity) -> list[str]:
        """Generate parameters for entity fields"""
        params = []
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref":
                params.append(f"p_{field_name}_id UUID DEFAULT NULL")
            else:
                pg_type = self._map_specql_type(field_def.type_name)
                params.append(f"p_{field_name} {pg_type} DEFAULT NULL")
        return params

    def _caller_context_param(self) -> str:
        """Generate caller context parameter (always added)"""
        return "p_caller_id UUID DEFAULT NULL"

    def _requires_entity_id(self, action: Action) -> bool:
        """Check if action operates on existing entity"""
        return any(step.type in ("update", "delete", "validate") for step in action.steps)

    def _map_specql_type(self, specql_type: str) -> str:
        """Map SpecQL types to PostgreSQL types"""
        mapping = {
            "text": PostgreSQLType.TEXT.value,
            "integer": PostgreSQLType.INTEGER.value,
            "boolean": PostgreSQLType.BOOLEAN.value,
            "timestamp": PostgreSQLType.TIMESTAMPTZ.value,
            "date": PostgreSQLType.DATE.value,
            "jsonb": PostgreSQLType.JSONB.value,
            "uuid": PostgreSQLType.UUID.value,
        }
        return mapping.get(specql_type, PostgreSQLType.TEXT.value)


class ActionCompiler:
    """
    Compiles SpecQL actions to PL/pgSQL functions returning FraiseQL-compatible mutation_result.

    This compiler transforms business logic DSL into production-ready PostgreSQL functions
    with proper type safety, Trinity pattern resolution, and mutation metadata.
    """

    def __init__(self, templates_dir: str = "templates/sql") -> None:
        """Initialize the action compiler with helper components"""
        self.param_generator = ParameterGenerator()
        self.templates_dir = templates_dir

        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )

    def generate_base_types(self) -> str:
        """Generate mutation_result composite type using Jinja2 template"""
        template = self.env.get_template("mutation_result_type.sql.j2")
        return template.render()

    def generate_metadata_types(self) -> str:
        """Generate FraiseQL impact metadata composite types using Jinja2 template"""
        template = self.env.get_template("impact_metadata_types.sql.jinja2")
        return template.render()

    def compile_action(self, action: Action, entity: Entity) -> str:
        """
        Generate PL/pgSQL function from action definition.

        Args:
            action: The SpecQL action to compile
            entity: The entity this action operates on

        Returns:
            Complete PL/pgSQL function definition as string
        """
        schema = entity.schema
        function_name = f"{schema}.{action.name}"

        # Generate parameters
        params = self.param_generator.generate(entity, action)

        # Generate function body
        body = self._generate_basic_body(action, entity)

        return f"""
CREATE OR REPLACE FUNCTION {function_name}(
    {", ".join(params)}
)
RETURNS mutation_result AS $$
DECLARE
    v_result mutation_result;
    {self._generate_declarations(action, entity)}
BEGIN
    {body}
END;
$$ LANGUAGE plpgsql;
"""

    def _generate_declarations(self, action: Action, entity: Entity) -> str:
        """
        Generate DECLARE block variables.

        Args:
            action: Action being compiled
            entity: Entity context

        Returns:
            DECLARE block content
        """
        declarations = []

        if self.param_generator._requires_entity_id(action):
            declarations.append("v_pk INTEGER;")

        return "\n    ".join(declarations)

    def _generate_basic_body(self, action: Action, entity: Entity) -> str:
        """
        Generate minimal function body with basic success response.

        Args:
            action: Action being compiled
            entity: Entity context

        Returns:
            Function body content
        """
        parts = []

        # Trinity resolution if needed
        if self.param_generator._requires_entity_id(action):
            parts.append(
                f"v_pk := {entity.schema}.{entity.name.lower()}_pk(p_{entity.name.lower()}_id);"
            )

        # Basic success response
        parts.append(
            """
    -- Basic success response
    v_result.status := 'success';
    v_result.message := 'Operation completed';
    v_result.object_data := '{}'::jsonb;

    RETURN v_result;
"""
        )

        return "\n    ".join(parts)
