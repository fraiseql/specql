"""Tests for GroupLeaderDetector - field group detection logic"""

from core.ast_models import Entity, FieldDefinition


def test_detect_address_group_leader():
    """Should detect address fields as group leader"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "country_code": FieldDefinition(name="country_code", type_name="text"),
            "postal_code": FieldDefinition(name="postal_code", type_name="text"),
            "city_code": FieldDefinition(name="city_code", type_name="text"),
        },
    )

    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    groups = detector.detect_groups(entity)

    assert "address_group" in groups
    assert groups["address_group"]["leader"] == "country_code"
    assert set(groups["address_group"]["dependents"]) == {"postal_code", "city_code"}


def test_detect_location_group_leader():
    """Should detect location fields as group leader"""
    entity = Entity(
        name="Store",
        schema="inventory",
        fields={
            "latitude": FieldDefinition(name="latitude", type_name="numeric"),
            "longitude": FieldDefinition(name="longitude", type_name="numeric"),
            "elevation": FieldDefinition(name="elevation", type_name="numeric"),
        },
    )

    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    groups = detector.detect_groups(entity)

    assert "location_group" in groups
    assert groups["location_group"]["leader"] == "latitude"
    assert set(groups["location_group"]["dependents"]) == {"longitude", "elevation"}


def test_no_group_detected_for_single_field():
    """Should not detect groups when only one field matches"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "country_code": FieldDefinition(name="country_code", type_name="text"),
            "email": FieldDefinition(name="email", type_name="email"),
        },
    )

    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    groups = detector.detect_groups(entity)

    assert len(groups) == 0


def test_multiple_groups_in_same_entity():
    """Should detect multiple groups in the same entity"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            # Address group
            "country_code": FieldDefinition(name="country_code", type_name="text"),
            "postal_code": FieldDefinition(name="postal_code", type_name="text"),
            "city_code": FieldDefinition(name="city_code", type_name="text"),
            # Location group
            "latitude": FieldDefinition(name="latitude", type_name="numeric"),
            "longitude": FieldDefinition(name="longitude", type_name="numeric"),
            # Other fields
            "email": FieldDefinition(name="email", type_name="email"),
        },
    )

    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    groups = detector.detect_groups(entity)

    assert "address_group" in groups
    assert "location_group" in groups
    assert len(groups) == 2


def test_pick_leader_with_priority():
    """Should pick leader based on priority order"""
    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()

    # Test with country_code available (highest priority)
    fields = {"country_code", "postal_code", "city_code"}
    leader = detector._pick_leader(fields, ["country_code", "country"])
    assert leader == "country_code"

    # Test with country available (fallback priority)
    fields = {"country", "postal_code", "city_code"}
    leader = detector._pick_leader(fields, ["country_code", "country"])
    assert leader == "country"

    # Test with no priority matches (pick first alphabetically)
    fields = {"postal_code", "city_code"}
    leader = detector._pick_leader(fields, ["country_code", "country"])
    assert leader == "city_code"  # First alphabetically


def test_get_address_query_template():
    """Should return correct address query template"""
    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    template = detector._get_address_query_template()

    # Check that all expected fields are present (order may vary)
    assert "country_code" in template
    assert "postal_code" in template
    assert "city_code" in template
    assert "FROM dim.tb_address" in template
    assert "ORDER BY RANDOM() LIMIT 1" in template


def test_get_location_query_template():
    """Should return correct location query template"""
    # This will fail until we implement the detector
    from testing.metadata.group_leader_detector import GroupLeaderDetector

    detector = GroupLeaderDetector()
    template = detector._get_location_query_template()

    # Check that all expected fields are present (order may vary)
    assert "latitude" in template
    assert "longitude" in template
    assert "elevation" in template
    assert "FROM dim.tb_location" in template
    assert "ORDER BY RANDOM() LIMIT 1" in template
