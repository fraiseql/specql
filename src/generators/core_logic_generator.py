"""
Core Logic Generator (Team C)
Generates core.* business logic functions
"""

from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from src.core.ast_models import Entity, FieldDefinition


class CoreLogicGenerator:
    """Generates core layer business logic functions"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_core_create_function(self, entity: Entity) -> str:
        """
        Generate core CREATE function with:
        - Input validation
        - Trinity resolution (UUID → INTEGER)
        - tenant_id population
        - Audit field population
        """
        # Prepare field mappings
        fields = self._prepare_insert_fields(entity)
        validations = self._generate_validations(entity)
        fk_resolutions = self._generate_fk_resolutions(entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": f"tb_{entity.name.lower()}",
                "pk_column": f"pk_{entity.name.lower()}",
            },
            "composite_type": f"app.type_create_{entity.name.lower()}_input",
            "fields": fields,
            "validations": validations,
            "fk_resolutions": fk_resolutions,
        }

        template = self.env.get_template("core_create_function.sql.j2")
        return template.render(**context)

    def generate_core_update_function(self, entity: Entity) -> str:
        """
        Generate core UPDATE function with:
        - Input validation
        - Trinity resolution (UUID → INTEGER)
        - Audit field population (updated_at, updated_by)
        """
        # Prepare field mappings for UPDATE
        update_fields = self._prepare_update_fields(entity)
        validations = self._generate_validations(entity)
        fk_resolutions = self._generate_fk_resolutions(entity)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": f"tb_{entity.name.lower()}",
                "pk_column": f"pk_{entity.name.lower()}",
            },
            "composite_type": f"app.type_update_{entity.name.lower()}_input",
            "update_fields": update_fields,
            "validations": validations,
            "fk_resolutions": fk_resolutions,
        }

        template = self.env.get_template("core_update_function.sql.j2")
        return template.render(**context)

    def generate_core_delete_function(self, entity: Entity) -> str:
        """
        Generate core DELETE function with:
        - Soft delete (deleted_at, deleted_by)
        - Audit trail
        """
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": f"tb_{entity.name.lower()}",
                "pk_column": f"pk_{entity.name.lower()}",
            },
        }

        template = self.env.get_template("core_delete_function.sql.j2")
        return template.render(**context)

    def _prepare_insert_fields(self, entity: Entity) -> Dict:
        """Prepare field list for INSERT statement"""
        insert_fields = []
        insert_values = []

        # Trinity fields
        insert_fields.append("id")
        insert_values.append("v_id")

        # Multi-tenancy
        insert_fields.append("tenant_id")
        insert_values.append("auth_tenant_id")

        # Business fields
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref":
                # Foreign key (INTEGER)
                fk_name = f"fk_{field_name}"
                insert_fields.append(fk_name)
                insert_values.append(f"v_{fk_name}")
            else:
                # Regular field
                insert_fields.append(field_name)
                insert_values.append(f"input_data.{field_name}")

        # Audit fields
        insert_fields.extend(["created_at", "created_by"])
        insert_values.extend(["now()", "auth_user_id"])

        return {
            "columns": insert_fields,
            "insert_values": insert_values,
        }

    def _prepare_update_fields(self, entity: Entity) -> Dict:
        """Prepare field list for UPDATE statement"""
        update_assignments = []

        # Business fields
        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref":
                # Foreign key (INTEGER)
                fk_name = f"fk_{field_name}"
                update_assignments.append(f"{fk_name} = v_{fk_name}")
            else:
                # Regular field
                update_assignments.append(f"{field_name} = input_data.{field_name}")

        # Audit fields
        update_assignments.extend(["updated_at = now()", "updated_by = auth_user_id"])

        return {
            "assignments": update_assignments,
        }

    def _generate_validations(self, entity: Entity) -> List[Dict]:
        """Generate validation checks for required fields"""
        validations = []
        for field_name, field_def in entity.fields.items():
            if not field_def.nullable:
                # Generate validation for required field
                validations.append(
                    {
                        "field": field_name,
                        "check": f"input_data.{field_name} IS NULL",
                        "error": f"failed:missing_{field_name}",
                        "message": f"{field_name.capitalize()} is required",
                    }
                )
        return validations

    def _generate_fk_resolutions(self, entity: Entity) -> List[Dict]:
        """Generate UUID → INTEGER FK resolutions using Trinity helpers"""
        resolutions = []
        is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

        for field_name, field_def in entity.fields.items():
            if field_def.type == "ref" and field_def.target_entity:
                # Check if target entity is in tenant-specific schema
                target_is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

                input_field_ref = f"input_data.{field_name}_id::TEXT"
                helper_function_name = f"{entity.schema}.{field_def.target_entity.lower()}_pk"

                if target_is_tenant_specific:
                    helper_call = f"{helper_function_name}({input_field_ref}, auth_tenant_id)"
                else:
                    helper_call = f"{helper_function_name}({input_field_ref})"

                resolutions.append(
                    {
                        "field": field_name,
                        "target_entity": field_def.target_entity,
                        "variable": f"v_fk_{field_name}",
                        "helper_call": helper_call,
                        "input_field": f"{field_name}_id",  # Composite type uses company_id
                        "target_is_tenant_specific": target_is_tenant_specific,
                    }
                )
        return resolutions

    def _is_tenant_specific_schema(self, schema: str) -> bool:
        """
        Determine if schema is tenant-specific (needs tenant_id filtering)
        """
        TENANT_SCHEMAS = ["tenant", "crm", "management", "operations"]
        return schema in TENANT_SCHEMAS
