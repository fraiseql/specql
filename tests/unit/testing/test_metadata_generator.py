"""Tests for TestMetadataGenerator - AST to SQL conversion"""

from src.core.ast_models import Entity, FieldDefinition


def test_generate_entity_config():
    """Should generate entity test config SQL"""
    entity = Entity(name="Contact", schema="crm", fields={})

    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()
    sql = generator.generate_entity_config(entity, table_code=123210)

    assert "INSERT INTO test_metadata.tb_entity_test_config" in sql
    assert "'Contact'" in sql
    assert "'crm'" in sql
    assert "123210" in sql


def test_generate_field_mapping_for_email():
    """Should generate field mapping for email field"""
    field = FieldDefinition(name="email", type_name="email", nullable=False)

    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()
    sql = generator.generate_field_mapping(entity_config_id=1, field=field)

    assert "INSERT INTO test_metadata.tb_field_generator_mapping" in sql
    assert "'email'" in sql
    assert "'random'" in sql  # email fields use random generator


def test_generate_field_mapping_for_fk():
    """Should generate field mapping for foreign key field"""
    field = FieldDefinition(name="fk_company", type_name="ref(Company)", nullable=True)

    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()
    sql = generator.generate_field_mapping(entity_config_id=1, field=field)

    assert "INSERT INTO test_metadata.tb_field_generator_mapping" in sql
    assert "'fk_company'" in sql
    assert "'fk_resolve'" in sql  # FK fields use fk_resolve generator


def test_derive_entity_code():
    """Should derive 3-char entity code from name"""
    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    assert generator._derive_entity_code("Contact") == "CON"
    assert generator._derive_entity_code("Company") == "COM"
    assert generator._derive_entity_code("Task") == "TAS"


def test_infer_generator_type():
    """Should infer generator type from field type"""
    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    email_field = FieldDefinition(name="email", type_name="email")
    fk_field = FieldDefinition(name="fk_company", type_name="ref(Company)")
    text_field = FieldDefinition(name="name", type_name="text")

    assert generator._infer_generator_type(email_field) == "random"
    assert generator._infer_generator_type(fk_field) == "fk_resolve"
    assert generator._infer_generator_type(text_field) == "random"


def test_get_generator_function():
    """Should get SQL function name for field types"""
    # This will fail until we implement the generator
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    email_field = FieldDefinition(name="email", type_name="email")
    phone_field = FieldDefinition(name="phone", type_name="phoneNumber")
    url_field = FieldDefinition(name="website", type_name="url")
    enum_field = FieldDefinition(name="status", type_name="enum(lead,qualified)")
    unknown_field = FieldDefinition(name="custom", type_name="custom_type")

    assert generator._get_generator_function(email_field) == "test_random_email"
    assert generator._get_generator_function(phone_field) == "test_random_phone"
    assert generator._get_generator_function(url_field) == "test_random_url"
    assert generator._get_generator_function(enum_field) == "test_random_enum"
    assert generator._get_generator_function(unknown_field) == "test_random_value"


def test_parse_fk_target():
    """Should parse FK target information from ref() type"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    fk_field = FieldDefinition(name="fk_company", type_name="ref(Company)")
    non_fk_field = FieldDefinition(name="name", type_name="text")

    entity, schema, table, pk_field = generator._parse_fk_target(fk_field)
    assert entity == "Company"
    assert schema == "crm"
    assert table == "tb_company"
    assert pk_field == "pk_company"

    none_result = generator._parse_fk_target(non_fk_field)
    assert none_result == (None, None, None, None)


def test_get_priority_order():
    """Should assign correct priority orders"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    basic_field = FieldDefinition(name="name", type_name="text")
    fk_field = FieldDefinition(name="fk_company", type_name="ref(Company)")

    assert generator._get_priority_order(basic_field) == 10
    assert generator._get_priority_order(fk_field) == 20


def test_has_unique_constraints():
    """Should detect entities with unique constraints"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    # Entity with email field (should have unique constraints)
    entity_with_email = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email"),
            "name": FieldDefinition(name="name", type_name="text"),
        },
    )

    # Entity without unique indicators
    entity_without_unique = Entity(
        name="Task",
        schema="crm",
        fields={
            "title": FieldDefinition(name="title", type_name="text"),
            "description": FieldDefinition(name="description", type_name="text"),
        },
    )

    assert generator._has_unique_constraints(entity_with_email) == True
    assert generator._has_unique_constraints(entity_without_unique) == False


def test_generate_default_scenarios():
    """Should generate default test scenarios"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type_name="email")},
    )

    scenarios_sql = generator.generate_default_scenarios(entity, entity_config_id=1)

    assert "happy_path_create" in scenarios_sql
    assert "duplicate_constraint" in scenarios_sql  # Because entity has email field
    assert "INSERT INTO test_metadata.tb_test_scenarios" in scenarios_sql


def test_generate_entity_config_with_all_fields():
    """Should generate entity config with all required fields"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    entity = Entity(name="Contact", schema="crm", fields={})

    sql = generator.generate_entity_config(entity, table_code=123210)

    # Check all the new fields are included
    assert "is_tenant_scoped" in sql
    assert "enable_crud_tests" in sql
    assert "enable_action_tests" in sql
    assert "enable_constraint_tests" in sql
    assert "enable_dedup_tests" in sql
    assert "enable_fk_tests" in sql
    assert "TRUE" in sql  # All flags should be TRUE


def test_generate_field_mapping_with_fk_details():
    """Should generate field mapping with FK details"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    fk_field = FieldDefinition(
        name="fk_company", type_name="ref(Company)", postgres_type="INTEGER", nullable=True
    )

    sql = generator.generate_field_mapping(entity_config_id=1, field=fk_field)

    assert "fk_target_entity" in sql
    assert "'Company'" in sql
    assert "'crm'" in sql
    assert "'tb_company'" in sql
    assert "'pk_company'" in sql
    assert "ARRAY['tenant_id']" in sql
    assert "20" in sql  # FK priority


def test_full_contact_entity_conversion():
    """Should generate complete metadata for Contact entity"""
    from src.testing.metadata.metadata_generator import TestMetadataGenerator

    generator = TestMetadataGenerator()

    # Create a realistic Contact entity
    contact_entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(
                name="email", type_name="email", postgres_type="TEXT", nullable=False
            ),
            "first_name": FieldDefinition(
                name="first_name", type_name="text", postgres_type="TEXT", nullable=True
            ),
            "last_name": FieldDefinition(
                name="last_name", type_name="text", postgres_type="TEXT", nullable=True
            ),
            "phone": FieldDefinition(
                name="phone", type_name="phoneNumber", postgres_type="TEXT", nullable=True
            ),
            "status": FieldDefinition(
                name="status",
                type_name="enum(lead,qualified,customer)",
                postgres_type="TEXT",
                nullable=False,
            ),
            "fk_company": FieldDefinition(
                name="fk_company", type_name="ref(Company)", postgres_type="INTEGER", nullable=True
            ),
            "country_code": FieldDefinition(
                name="country_code", type_name="text", postgres_type="TEXT", nullable=True
            ),
            "postal_code": FieldDefinition(
                name="postal_code", type_name="text", postgres_type="TEXT", nullable=True
            ),
            "city_code": FieldDefinition(
                name="city_code", type_name="text", postgres_type="TEXT", nullable=True
            ),
        },
    )

    # Generate entity config
    entity_sql = generator.generate_entity_config(contact_entity, table_code=123210)
    assert "INSERT INTO test_metadata.tb_entity_test_config" in entity_sql
    assert "'Contact'" in entity_sql
    assert "'crm'" in entity_sql
    assert "'CON'" in entity_sql  # Entity code
    assert "'123210'" in entity_sql  # Base UUID prefix (table_code zero-padded)

    # Generate field mappings
    field_sqls = []
    for i, (field_name, field) in enumerate(contact_entity.fields.items(), 1):
        field_sql = generator.generate_field_mapping(entity_config_id=1, field=field)
        field_sqls.append(field_sql)

        assert f"'{field_name}'" in field_sql
        assert f"'{field.type_name}'" in field_sql

    # Check specific field types
    email_sql = next(sql for sql in field_sqls if "'email'" in sql)
    assert "'test_random_email'" in email_sql
    assert "10" in email_sql  # Priority

    enum_sql = next(sql for sql in field_sqls if "'status'" in sql)
    assert "'test_random_enum'" in enum_sql

    fk_sql = next(sql for sql in field_sqls if "'fk_company'" in sql)
    assert "'fk_resolve'" in fk_sql
    assert "'Company'" in fk_sql
    assert "20" in fk_sql  # FK priority

    # Generate scenarios
    scenarios_sql = generator.generate_default_scenarios(contact_entity, entity_config_id=1)
    assert "happy_path_create" in scenarios_sql
    assert "duplicate_constraint" in scenarios_sql  # Because entity has email

    # Verify we can generate all SQL without errors
    all_sql = entity_sql + "\n".join(field_sqls) + "\n" + scenarios_sql
    assert len(all_sql) > 1000  # Should be substantial SQL output
    assert "INSERT INTO" in all_sql
    assert "test_metadata" in all_sql
