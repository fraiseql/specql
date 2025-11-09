"""
Foreign Key Resolver

Handles Tier 3 entity reference resolution for foreign key lookups using Trinity helper functions.

Example SpecQL:
    - update: contact_id = ref(Contact).uuid
    - insert: contact_id = ref(Contact).uuid

Generated PL/pgSQL:
    -- Resolve FK: ref(Contact).uuid → pk_contact
    v_contact_id := crm.contact_pk(v_uuid_param, auth_tenant_id);
    IF v_contact_id IS NULL THEN
        v_result.status := 'error';
        v_result.message := 'Contact not found';
        RETURN v_result;
    END IF;

    UPDATE crm.tb_task
    SET contact_id = v_contact_id, updated_at = NOW(), updated_by = v_user_id
    WHERE pk_task = v_pk;
"""

from src.core.ast_models import EntityDefinition
from src.generators.schema.naming_conventions import NamingConventions


class ForeignKeyResolver:
    """Resolves foreign key references for Tier 3 entity relationships using Trinity helpers"""

    def __init__(self, naming_conventions: NamingConventions, tenant_var: str = "auth_tenant_id"):
        """
        Initialize with naming conventions and tenant variable name

        Args:
            naming_conventions: Naming conventions with domain registry
            tenant_var: Variable name containing tenant_id (default: auth_tenant_id)
        """
        self.naming_conventions = naming_conventions
        self.tenant_var = tenant_var

    def resolve_fk_reference(
        self, reference_expr: str, entity: EntityDefinition, uuid_var: str = "v_uuid_param"
    ) -> str:
        """
        Resolve a foreign key reference expression using Trinity helper

        Args:
            reference_expr: Expression like "ref(Contact).uuid"
            entity: Current entity definition
            uuid_var: Variable containing the UUID to resolve

        Returns:
            PL/pgSQL code to resolve the FK using Trinity helper

        Example:
            resolve_fk_reference("ref(Contact).uuid", task_entity)
            → Trinity helper call with tenant_id
        """
        # Parse the reference expression
        target_entity, lookup_field = self._parse_reference_expr(reference_expr)

        if not target_entity or not lookup_field:
            raise ValueError(f"Invalid reference expression: {reference_expr}")

        # Generate the FK resolution using Trinity helper
        return self._generate_trinity_fk_resolution(target_entity, lookup_field, uuid_var)

    def _parse_reference_expr(self, expr: str) -> tuple[str, str]:
        """
        Parse reference expression like "ref(Contact).uuid"

        Returns:
            (target_entity_name, lookup_field)
        """
        # Expected format: ref(EntityName).field
        if not expr.startswith("ref(") or ")." not in expr:
            raise ValueError(f"Invalid reference format: {expr}. Expected: ref(EntityName).field")

        try:
            # Extract entity name from ref(EntityName)
            ref_part, field_part = expr.split(").", 1)
            entity_name = ref_part[4:]  # Remove "ref("

            return entity_name, field_part
        except ValueError:
            raise ValueError(f"Invalid reference format: {expr}")

    def _generate_trinity_fk_resolution(
        self, target_entity: str, lookup_field: str, uuid_var: str
    ) -> str:
        """
        Generate PL/pgSQL to resolve FK using Trinity helper function

        Args:
            target_entity: Name of the referenced entity (e.g., "Contact")
            lookup_field: Field to lookup by (e.g., "uuid")
            uuid_var: Variable containing the UUID

        Returns:
            PL/pgSQL Trinity helper call for FK resolution
        """
        # Target entity details
        target_lower = target_entity.lower()
        target_schema = self._resolve_entity_schema(target_entity)
        target_pk = f"pk_{target_lower}"

        # Variable to store the resolved FK
        fk_var = f"v_{target_lower}_id"

        # Trinity helper function
        helper_function = f"{target_schema}.{target_lower}_pk"

        return f"""    -- Resolve FK: ref({target_entity}).{lookup_field} → {target_pk}
    {fk_var} := {helper_function}({uuid_var}, {self.tenant_var});
    IF {fk_var} IS NULL THEN
        v_result.status := 'error';
        v_result.message := '{target_entity} not found';
        RETURN v_result;
    END IF;"""

    def _resolve_entity_schema(self, entity_name: str) -> str:
        """
        Resolve entity name to schema name using registry

        Checks:
        1. Domain registry for registered entities
        2. Inference heuristics if not registered

        Returns canonical schema name (resolves aliases)
        """
        # Check if entity is registered
        entry = self.naming_conventions.registry.get_entity(entity_name)
        if entry:
            # Get domain from registry entry
            domain_code = entry.domain
            domain = self.naming_conventions.registry.get_domain(domain_code)
            return (
                domain.domain_name if domain else "public"
            )  # Use canonical domain name (not alias)

        # Fallback to inference (for backward compatibility)
        return self._infer_schema_from_entity_name(entity_name)

    def _infer_schema_from_entity_name(self, entity_name: str) -> str:
        """
        Infer schema from entity name using common patterns

        This is a fallback for entities not yet registered
        """
        name_lower = entity_name.lower()

        # CRM/Management entities
        if any(x in name_lower for x in ["contact", "company", "person", "account", "customer"]):
            return "crm"

        # Catalog entities
        if any(x in name_lower for x in ["manufacturer", "product", "brand", "model"]):
            return "catalog"

        # Project entities
        if any(x in name_lower for x in ["project", "task", "milestone"]):
            return "projects"

        # Default to entity's own schema (will be validated elsewhere)
        return name_lower

    def generate_fk_assignment(
        self,
        field_name: str,
        reference_expr: str,
        entity: EntityDefinition,
        uuid_var: str = "v_uuid_param",
    ) -> str:
        """
        Generate FK assignment with Trinity resolution

        Args:
            field_name: The FK field name (e.g., "contact_id")
            reference_expr: The reference expression (e.g., "ref(Contact).uuid")
            entity: Current entity
            uuid_var: Variable containing the UUID to resolve

        Returns:
            Complete PL/pgSQL for FK resolution and assignment
        """
        resolution_sql = self.resolve_fk_reference(reference_expr, entity, uuid_var)

        # Extract the target entity to get the FK variable name
        target_entity, _ = self._parse_reference_expr(reference_expr)
        fk_var = f"v_{target_entity.lower()}_id"

        return f"""    -- Resolve and assign FK: {field_name} = {reference_expr}
{resolution_sql}

    v_{field_name} := {fk_var};"""
