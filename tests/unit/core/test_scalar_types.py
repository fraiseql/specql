import pytest
from src.core.scalar_types import SCALAR_TYPES, get_scalar_type, is_scalar_type


def test_scalar_types_registry_complete():
    """Ensure all 22 scalar types are registered"""
    assert len(SCALAR_TYPES) >= 22

    required_types = [
        "email",
        "phoneNumber",
        "url",
        "slug",
        "markdown",
        "html",
        "ipAddress",
        "macAddress",
        "money",
        "percentage",
        "date",
        "datetime",
        "time",
        "duration",
        "coordinates",
        "latitude",
        "longitude",
        "image",
        "file",
        "color",
        "uuid",
        "json",
        "boolean",
    ]

    for type_name in required_types:
        assert type_name in SCALAR_TYPES, f"Missing scalar type: {type_name}"


def test_email_scalar_definition():
    """Test email scalar type definition"""
    email = get_scalar_type("email")

    assert email is not None
    assert email.name == "email"
    assert email.postgres_type.value == "TEXT"
    assert email.fraiseql_scalar_name == "Email"
    assert email.validation_pattern is not None
    assert "@" in email.validation_pattern
    assert email.input_type == "email"


def test_money_scalar_with_precision():
    """Test money scalar type with NUMERIC precision"""
    money = get_scalar_type("money")

    assert money is not None
    assert money.postgres_type.value == "NUMERIC"
    assert money.postgres_precision == (19, 4)
    assert money.get_postgres_type_with_precision() == "NUMERIC(19,4)"
    assert money.min_value == 0.0


def test_latitude_range_validation():
    """Test latitude has min/max range"""
    lat = get_scalar_type("latitude")

    assert lat is not None
    assert lat.min_value == -90.0
    assert lat.max_value == 90.0


def test_is_scalar_type_helper():
    """Test is_scalar_type helper function"""
    assert is_scalar_type("email") is True
    assert is_scalar_type("money") is True
    assert is_scalar_type("not_a_type") is False


def test_phone_number_validation_pattern():
    """Test phone number has E.164 validation pattern"""
    phone = get_scalar_type("phoneNumber")

    assert phone is not None
    assert phone.validation_pattern is not None
    assert phone.validation_pattern.startswith("^")
    assert phone.validation_pattern.endswith("$")
    assert "+" in phone.validation_pattern


def test_color_hex_validation():
    """Test color type has hex validation pattern"""
    color = get_scalar_type("color")

    assert color is not None
    assert color.validation_pattern is not None
    assert "#[0-9A-Fa-f]{6}" in color.validation_pattern


def test_uuid_type_mapping():
    """Test UUID type maps to PostgreSQL UUID"""
    uuid_type = get_scalar_type("uuid")

    assert uuid_type is not None
    assert uuid_type.postgres_type.value == "UUID"
    assert uuid_type.fraiseql_scalar_name == "UUID"


def test_json_type_mapping():
    """Test JSON type maps to PostgreSQL JSONB"""
    json_type = get_scalar_type("json")

    assert json_type is not None
    assert json_type.postgres_type.value == "JSONB"
    assert json_type.fraiseql_scalar_name == "JSON"


def test_geographic_types_precision():
    """Test geographic types have appropriate precision"""
    lat = get_scalar_type("latitude")
    lng = get_scalar_type("longitude")

    assert lat.postgres_precision == (10, 8)
    assert lng.postgres_precision == (11, 8)

    assert lat.get_postgres_type_with_precision() == "NUMERIC(10,8)"
    assert lng.get_postgres_type_with_precision() == "NUMERIC(11,8)"


def test_percentage_range():
    """Test percentage has 0-100 range"""
    pct = get_scalar_type("percentage")

    assert pct is not None
    assert pct.min_value == 0.0
    assert pct.max_value == 100.0
    assert pct.postgres_precision == (5, 2)


def test_network_types():
    """Test network types map correctly"""
    ip = get_scalar_type("ipAddress")
    mac = get_scalar_type("macAddress")

    assert ip.postgres_type.value == "INET"
    assert mac.postgres_type.value == "MACADDR"


def test_datetime_types():
    """Test date/time types map correctly"""
    date = get_scalar_type("date")
    datetime = get_scalar_type("datetime")
    time = get_scalar_type("time")
    duration = get_scalar_type("duration")

    assert date.postgres_type.value == "DATE"
    assert datetime.postgres_type.value == "TIMESTAMPTZ"
    assert time.postgres_type.value == "TIME"
    assert duration.postgres_type.value == "INTERVAL"
