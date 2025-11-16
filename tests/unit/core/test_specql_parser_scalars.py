from src.core.ast_models import FieldTier
from src.core.specql_parser import SpecQLParser


def test_parse_entity_with_scalar_types():
    """Test parsing entity with rich scalar types"""
    yaml_content = """
    entity: Contact
    schema: crm
    description: "Customer contact information"

    fields:
      email: email!
      phone: phoneNumber
      website: url
      discount: percentage
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert entity.name == "Contact"
    assert entity.schema == "crm"
    assert len(entity.fields) == 4

    # Check email field
    email_field = entity.fields["email"]
    assert email_field.is_rich_scalar()
    assert email_field.nullable is False
    assert email_field.postgres_type == "TEXT"
    assert email_field.fraiseql_type == "Email"
    assert email_field.validation_pattern is not None

    # Check phone field
    phone_field = entity.fields["phone"]
    assert phone_field.is_rich_scalar()
    assert phone_field.nullable is True
    assert phone_field.fraiseql_type == "PhoneNumber"

    # Check percentage field
    pct_field = entity.fields["discount"]
    assert pct_field.postgres_type == "NUMERIC(5,2)"
    assert pct_field.min_value == 0.0
    assert pct_field.max_value == 100.0


def test_parse_mixed_basic_and_scalar_types():
    """Test parsing entity with mix of basic and scalar types"""
    yaml_content = """
    entity: Product
    fields:
      name: text!
      price: money!
      stock: integer
      website: url
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Basic type
    assert entity.fields["name"].tier == FieldTier.BASIC
    assert entity.fields["name"].postgres_type == "TEXT"

    # Rich scalar type
    assert entity.fields["price"].tier == FieldTier.SCALAR
    assert entity.fields["price"].postgres_type == "NUMERIC(19,4)"

    # Basic integer
    assert entity.fields["stock"].tier == FieldTier.BASIC
    assert entity.fields["stock"].postgres_type == "INTEGER"


def test_parse_entity_with_actions():
    """Test parsing entity with actions (stub implementation)"""
    yaml_content = """
    entity: User
    fields:
      name: text!
    actions:
      - name: create_user
        description: "Create a new user"
        steps: []
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.actions) == 1
    assert entity.actions[0].name == "create_user"
    assert entity.actions[0].description == "Create a new user"


def test_parse_boolean_field():
    """Test parsing boolean basic type"""
    yaml_content = """
    entity: Task
    fields:
      completed: boolean!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    field = entity.fields["completed"]
    from src.core.ast_models import FieldTier

    # Boolean is a BASIC type, not a scalar type
    assert field.tier == FieldTier.BASIC
    assert field.nullable is False
    assert field.postgres_type == "BOOLEAN"
    assert field.fraiseql_type == "Boolean"


def test_parse_datetime_fields():
    """Test parsing date/time scalar types"""
    yaml_content = """
    entity: Event
    fields:
      start_date: date
      event_timestamp: datetime!
      duration: duration
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Date field
    date_field = entity.fields["start_date"]
    assert date_field.postgres_type == "DATE"
    assert date_field.fraiseql_type == "Date"

    # Datetime field
    datetime_field = entity.fields["event_timestamp"]
    assert datetime_field.postgres_type == "TIMESTAMPTZ"
    assert datetime_field.fraiseql_type == "DateTime"
    assert datetime_field.nullable is False

    # Duration field
    duration_field = entity.fields["duration"]
    assert duration_field.postgres_type == "INTERVAL"
    assert duration_field.fraiseql_type == "Duration"


def test_parse_geographic_fields():
    """Test parsing geographic scalar types"""
    yaml_content = """
    entity: Location
    fields:
      coords: coordinates
      lat: latitude
      lng: longitude
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Coordinates
    coords_field = entity.fields["coords"]
    assert coords_field.postgres_type == "POINT"
    assert coords_field.fraiseql_type == "Coordinates"

    # Latitude
    lat_field = entity.fields["lat"]
    assert lat_field.postgres_type == "NUMERIC(10,8)"
    assert lat_field.min_value == -90.0
    assert lat_field.max_value == 90.0

    # Longitude
    lng_field = entity.fields["lng"]
    assert lng_field.postgres_type == "NUMERIC(11,8)"
    assert lng_field.min_value == -180.0
    assert lng_field.max_value == 180.0


def test_parse_composite_types():
    """Test parsing composite type fields"""
    yaml_content = """
    entity: Company
    fields:
      address: SimpleAddress!
      contact: ContactInfo
      money_amount: MoneyAmount
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 3

    # SimpleAddress (non-nullable)
    address_field = entity.fields["address"]
    assert address_field.is_composite()
    assert address_field.nullable is False
    assert address_field.postgres_type == "JSONB"
    assert address_field.fraiseql_type == "SimpleAddress"
    assert address_field.composite_def is not None
    assert address_field.composite_def.name == "SimpleAddress"

    # ContactInfo (nullable)
    contact_field = entity.fields["contact"]
    assert contact_field.is_composite()
    assert contact_field.nullable is True
    assert contact_field.fraiseql_type == "ContactInfo"

    # MoneyAmount
    money_field = entity.fields["money_amount"]
    assert money_field.is_composite()
    assert money_field.composite_def.name == "MoneyAmount"


def test_parse_nested_composite_types():
    """Test parsing composite types that reference other composites"""
    yaml_content = """
    entity: Business
    fields:
      hours: BusinessHours
      address: SimpleAddress
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # BusinessHours contains TimeRange composites
    hours_field = entity.fields["hours"]
    assert hours_field.is_composite()
    assert hours_field.composite_def.name == "BusinessHours"

    # Check that the composite definition has the expected fields
    hours_def = hours_field.composite_def
    assert "monday" in hours_def.fields
    assert "sunday" in hours_def.fields


def test_composite_type_jsonb_schema():
    """Test that composite types generate correct JSONB schema"""
    from src.core.scalar_types import get_composite_type

    address_def = get_composite_type("SimpleAddress")
    assert address_def is not None

    schema = address_def.get_jsonb_schema()
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema

    # Check required fields
    assert "street" in schema["required"]
    assert "city" in schema["required"]
    assert "state" in schema["required"]
    assert "zipCode" in schema["required"]

    # Check optional fields
    assert "country" not in schema["required"]


def test_parse_reference_fields():
    """Test parsing entity reference fields"""
    yaml_content = """
    entity: Employee
    fields:
      manager: ref(Employee)
      department: ref(Department)!
      company: ref(Company)
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 3

    # Manager reference (nullable)
    manager_field = entity.fields["manager"]
    assert manager_field.is_reference()
    assert manager_field.nullable is True
    assert (
        manager_field.postgres_type == "INTEGER"
    )  # ✅ FIXED: Trinity Pattern uses INTEGER FKs
    assert manager_field.fraiseql_type == "ID"
    assert manager_field.reference_entity == "Employee"

    # Department reference (non-nullable)
    dept_field = entity.fields["department"]
    assert dept_field.is_reference()
    assert dept_field.nullable is False
    assert dept_field.postgres_type == "INTEGER"  # ✅ FIXED: All FKs are INTEGER
    assert dept_field.reference_entity == "Department"

    # Company reference
    company_field = entity.fields["company"]
    assert company_field.is_reference()
    assert company_field.postgres_type == "INTEGER"  # ✅ FIXED: All FKs are INTEGER
    assert company_field.reference_entity == "Company"


def test_parse_polymorphic_reference_fields():
    """Test parsing polymorphic reference fields (ref(Entity1|Entity2))"""
    yaml_content = """
    entity: Comment
    fields:
      author: ref(User|Admin)
      parent: ref(Post|Comment)
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Author polymorphic reference
    author_field = entity.fields["author"]
    assert author_field.is_reference()
    assert author_field.reference_entity == "User"  # First entity in the union
    assert author_field.type_name == "ref"

    # Parent polymorphic reference
    parent_field = entity.fields["parent"]
    assert parent_field.is_reference()
    assert parent_field.reference_entity == "Post"
    assert parent_field.type_name == "ref"


def test_parse_mixed_field_types():
    """Test parsing entity with all three tiers of field types"""
    yaml_content = """
    entity: Invoice
    fields:
      # Basic types
      number: text!
      total: money!

      # Scalar rich types
      email: email
      phone: phoneNumber

      # Composite types
      billing_address: SimpleAddress
      shipping_address: SimpleAddress

      # Reference types
      customer: ref(Customer)!
      salesperson: ref(Employee)
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 8

    # Check tier classification
    assert entity.fields["number"].tier.value == "basic"
    assert entity.fields["email"].tier.value == "scalar"
    assert entity.fields["billing_address"].tier.value == "composite"
    assert entity.fields["customer"].tier.value == "reference"

    # Check specific field properties
    assert entity.fields["customer"].reference_entity == "Customer"
    assert entity.fields["billing_address"].composite_def.name == "SimpleAddress"
    assert entity.fields["email"].scalar_def.name == "email"
