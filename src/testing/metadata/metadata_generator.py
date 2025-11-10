"""Generate test metadata SQL from SpecQL AST"""

from src.core.ast_models import Entity, FieldDefinition


class TestMetadataGenerator:
    """Generate test metadata SQL from SpecQL AST"""

    def generate_entity_config(self, entity: Entity, table_code: int) -> str:
        """Generate entity test config INSERT statement"""

        entity_code = self._derive_entity_code(entity.name)
        # For UUID encoding, we need the table code as a 6-digit string
        base_uuid_prefix = str(table_code).zfill(6)

        # Escape single quotes in strings
        entity_name_safe = entity.name or ""
        schema_safe = entity.schema or ""
        entity_name_escaped = entity_name_safe.replace("'", "''")
        schema_escaped = schema_safe.replace("'", "''")
        table_name = f"tb_{entity_name_safe.lower()}"

        return f"""
INSERT INTO test_metadata.tb_entity_test_config
(entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix, is_tenant_scoped, enable_crud_tests, enable_action_tests, enable_constraint_tests, enable_dedup_tests, enable_fk_tests)
VALUES
('{entity_name_escaped}', '{schema_escaped}', '{table_name}', {table_code}, '{entity_code}', '{base_uuid_prefix}', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE);
"""

    def generate_field_mapping(self, entity_config_id: int, field: FieldDefinition) -> str:
        """Generate field generator mapping INSERT statement"""

        generator_type = self._infer_generator_type(field)
        generator_function = self._get_generator_function(field)
        priority_order = self._get_priority_order(field)

        # Escape single quotes
        field_name_safe = field.name or ""
        field_type_safe = field.type_name or ""
        postgres_type_safe = field.postgres_type or ""
        field_name_escaped = field_name_safe.replace("'", "''")
        field_type_escaped = field_type_safe.replace("'", "''")
        postgres_type_escaped = postgres_type_safe.replace("'", "''")

        # Handle FK fields
        fk_target_entity = None
        fk_target_schema = None
        fk_target_table = None
        fk_target_pk_field = None
        fk_dependencies = None

        if generator_type == "fk_resolve":
            fk_target_entity, fk_target_schema, fk_target_table, fk_target_pk_field = (
                self._parse_fk_target(field)
            )
            fk_dependencies = ["tenant_id"] if field.type_name.startswith("ref(") else None

        return f"""
INSERT INTO test_metadata.tb_field_generator_mapping
(fk_entity_test_config, field_name, field_type, postgres_type, generator_type, generator_function, fk_target_entity, fk_target_schema, fk_target_table, fk_target_pk_field, fk_dependencies, nullable, priority_order)
VALUES
({entity_config_id}, '{field_name_escaped}', '{field_type_escaped}', '{postgres_type_escaped}', '{generator_type}', '{generator_function}', {f"'{fk_target_entity}'" if fk_target_entity else "NULL"}, {f"'{fk_target_schema}'" if fk_target_schema else "NULL"}, {f"'{fk_target_table}'" if fk_target_table else "NULL"}, {f"'{fk_target_pk_field}'" if fk_target_pk_field else "NULL"}, {f"ARRAY{list(fk_dependencies)}" if fk_dependencies else "NULL"}, {str(field.nullable).upper()}, {priority_order});
"""

    def generate_default_scenarios(self, entity: Entity, entity_config_id: int) -> str:
        """Generate default test scenarios for entity"""
        scenarios = []

        # Happy path create scenario
        scenarios.append(
            f"""
INSERT INTO test_metadata.tb_test_scenarios
(fk_entity_test_config, scenario_code, scenario_name, scenario_type, expected_result, description, test_category, enabled)
VALUES
({entity_config_id}, 0, 'happy_path_create', 'happy_path', 'success', 'Standard {entity.name} creation', 'crud', TRUE);
"""
        )

        # Constraint violation scenario (if entity has unique constraints)
        if self._has_unique_constraints(entity):
            scenarios.append(
                f"""
INSERT INTO test_metadata.tb_test_scenarios
(fk_entity_test_config, scenario_code, scenario_name, scenario_type, expected_result, expected_error_code, description, test_category, enabled, seed_count)
VALUES
({entity_config_id}, 1000, 'duplicate_constraint', 'constraint_violation', 'error', 'duplicate_key_violation', 'Duplicate constraint violation test', 'constraint', TRUE, 2);
"""
            )

        return "\n".join(scenarios)

    def _derive_entity_code(self, entity_name: str) -> str:
        """Derive 3-char entity code from name"""
        # Take first 3 uppercase letters, or first 3 chars uppercase
        code = "".join([c for c in entity_name if c.isupper()])[:3]
        if len(code) < 3:
            code = entity_name[:3].upper()
        return code

    def _infer_generator_type(self, field: FieldDefinition) -> str:
        """Infer generator type from field type"""
        if field.type_name.startswith("ref("):
            return "fk_resolve"
        elif field.type_name.startswith("enum("):
            return "random"  # Enums use random selection
        elif field.type_name in [
            "text",
            "email",
            "phoneNumber",
            "url",
            "integer",
            "boolean",
            "date",
            "timestamptz",
        ]:
            return "random"
        else:
            return "random"  # Default fallback

    def _get_generator_function(self, field: FieldDefinition) -> str:
        """Get SQL function name for random generation"""
        # Map field types to generator functions
        GENERATOR_MAP = {
            "email": "test_random_email",
            "phoneNumber": "test_random_phone",
            "url": "test_random_url",
            "text": "test_random_text",
            "integer": "test_random_integer",
            "boolean": "test_random_boolean",
            "date": "test_random_date",
            "timestamptz": "test_random_timestamptz",
        }

        # Handle enum types
        if field.type_name.startswith("enum("):
            return "test_random_enum"

        return GENERATOR_MAP.get(field.type_name, "test_random_value")

    def _get_priority_order(self, field: FieldDefinition) -> int:
        """Get generation priority order (lower = earlier)"""
        # FK fields should be generated after their dependencies
        if field.type_name.startswith("ref("):
            return 20
        # Basic fields first
        return 10

    def _parse_fk_target(
        self, field: FieldDefinition
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """Parse FK target from ref(Target) type"""
        if not field.type_name.startswith("ref("):
            return None, None, None, None

        target_entity = field.type_name[4:-1]  # Remove 'ref(' and ')'
        target_schema = "crm"  # Default assumption, could be enhanced
        target_table = f"tb_{target_entity.lower()}"
        target_pk_field = f"pk_{target_entity.lower()}"

        return target_entity, target_schema, target_table, target_pk_field

    def _has_unique_constraints(self, entity: Entity) -> bool:
        """Check if entity has unique constraints"""
        # Simple check: look for fields that might be unique
        # In a real implementation, this would check the actual schema constraints
        unique_indicators = ["email", "username", "code", "identifier"]
        return any(field.name.lower() in unique_indicators for field in entity.fields.values())
