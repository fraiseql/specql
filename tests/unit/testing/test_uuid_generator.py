"""Tests for UUID generator component"""

from uuid import UUID

from testing.seed.uuid_generator import SpecQLUUIDGenerator, UUIDComponents


def test_generate_basic_uuid():
    """Test basic UUID generation with default scenario"""
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuid = gen.generate(scenario=0, instance=1)

    assert str(uuid) == "01232121-0000-4000-8000-000000000001"


def test_generate_scenario_1000():
    """Test UUID generation with scenario 1000"""
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuid = gen.generate(scenario=1000, instance=1)

    # Scenario 1000 → 4100-8000
    assert str(uuid) == "01232121-0000-4100-8000-000000000001"


def test_generate_with_test_case():
    """Test UUID generation with test case"""
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuid = gen.generate(scenario=1000, instance=5, test_case=3)

    # Scenario 1000, test case 3 → 0001-0003
    assert str(uuid) == "01232121-0000-4100-8003-000000000005"


def test_generate_mutation_test_type():
    """Test UUID generation for mutation tests"""
    gen = SpecQLUUIDGenerator("Contact", "012321", test_type="mutation_test")
    uuid = gen.generate(scenario=0, instance=1)

    assert str(uuid) == "01232122-0000-4000-8000-000000000001"


def test_generate_with_function_num():
    """Test UUID generation with function number"""
    gen = SpecQLUUIDGenerator("Contact", "012321", function_num=42)
    uuid = gen.generate(scenario=0, instance=1)

    assert str(uuid) == "01232121-0042-4000-8000-000000000001"


def test_decode_uuid():
    """Test UUID decoding"""
    uuid = UUID("01232122-3201-4100-8005-000000000042")
    components = SpecQLUUIDGenerator.decode(uuid)

    assert components.entity_code == "012321"
    assert components.test_type == "22"
    assert components.function_num == "3201"
    assert components.scenario == 1000
    assert components.test_case == 5
    assert components.instance == 42


def test_decode_basic_uuid():
    """Test decoding of basic seed UUID"""
    uuid = UUID("01232121-0000-0000-0000-000000000001")
    components = SpecQLUUIDGenerator.decode(uuid)

    assert components.entity_code == "012321"
    assert components.test_type == "21"
    assert components.function_num == "0000"
    assert components.scenario == 0
    assert components.test_case == 0
    assert components.instance == 1


def test_generate_batch():
    """Test batch UUID generation"""
    gen = SpecQLUUIDGenerator("Contact", "012321")
    uuids = gen.generate_batch(count=3, scenario=2000)

    assert len(uuids) == 3
    assert uuids[0] == UUID("01232121-0000-4200-8000-000000000001")
    assert uuids[1] == UUID("01232121-0000-4200-8000-000000000002")
    assert uuids[2] == UUID("01232121-0000-4200-8000-000000000003")


def test_from_metadata():
    """Test creating generator from metadata config"""
    entity_config = {"entity_name": "Contact", "base_uuid_prefix": "012321"}

    gen = SpecQLUUIDGenerator.from_metadata(entity_config)
    uuid = gen.generate(scenario=0, instance=1)

    assert str(uuid) == "01232121-0000-4000-8000-000000000001"


def test_uuid_components_str():
    """Test UUIDComponents string representation"""
    components = UUIDComponents(
        entity_code="012321",
        test_type="21",
        function_num="0000",
        scenario=1000,
        test_case=5,
        instance=42,
    )

    expected = "Entity: 012321, Type: 21, Function: 0000, Scenario: 1000, Test: 5, Instance: 42"
    assert str(components) == expected
