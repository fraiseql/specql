"""
Schema Registry
Central registry for schema properties and multi-tenancy classification

Replaces hardcoded TENANT_SCHEMAS lists with registry-driven lookups
"""

from src.application.services.domain_service_factory import get_domain_service


class SchemaRegistry:
    """
    Central registry for schema properties

    Replaces hardcoded TENANT_SCHEMAS lists with registry-driven lookups
    """

    def __init__(self):
        self.domain_service = get_domain_service()

    def is_multi_tenant(self, schema_name: str) -> bool:
        """
        Check if schema requires tenant_id column

        Checks:
        1. Domain registry (including aliases)
        2. multi_tenant flag in domain metadata
        3. Falls back to False (safe default)

        Example:
            registry.is_multi_tenant("crm")         # True
            registry.is_multi_tenant("management")  # True (alias of crm)
            registry.is_multi_tenant("catalog")     # False
            registry.is_multi_tenant("common")      # False
        """
        domain = self.domain_service.repository.find_by_name(schema_name)
        if domain:
            return domain.multi_tenant

        # Framework schemas (hardcoded, safe)
        framework_multi_tenant = {
            # None currently - core has mixed behavior
        }
        return schema_name in framework_multi_tenant

    def get_canonical_schema_name(self, schema_name: str) -> str:
        """
        Resolve alias to canonical schema name

        Example:
            registry.get_canonical_schema_name("management")  # "crm"
            registry.get_canonical_schema_name("tenant")      # "projects"
            registry.get_canonical_schema_name("catalog")     # "catalog"
        """
        domain = self.domain_service.repository.find_by_name(schema_name)
        return domain.domain_name if domain else schema_name

    def is_framework_schema(self, schema_name: str) -> bool:
        """Check if schema is framework-level (common, app, core)"""
        return schema_name in ["common", "app", "core"]

    def is_shared_reference_schema(self, schema_name: str) -> bool:
        """
        Check if schema is shared reference data (no tenant_id)

        Includes:
        - Framework schemas: common, app
        - User-defined domains with multi_tenant=false
        """
        if schema_name in ["common", "app"]:
            return True

        domain = self.domain_service.repository.find_by_name(schema_name)
        if domain:
            return not domain.multi_tenant

        return False

    def get_domain_by_name_or_alias(self, schema_name: str):
        """
        Get domain info by name or alias

        This is a convenience method that delegates to domain service
        """
        return self.domain_service.repository.find_by_name(schema_name)
