"""Tests for InfoInstanceDetector."""

from reverse_engineering.info_instance_detector import (
    InfoInstanceDetector,
)


class TestInfoTableDetection:
    """Tests for detecting _info tables."""

    def test_detect_info_table_by_name_suffix(self):
        """Tables ending with _info should be detected as info tables."""
        detector = InfoInstanceDetector()

        result = detector.detect(
            table_name="tb_administrative_unit_info",
            columns=["pk_administrative_unit_info", "identifier", "name"],
        )

        assert result.is_info_table is True
        assert result.is_instance_table is False
        assert result.base_entity_name == "administrative_unit"

    def test_regular_table_not_detected_as_info(self):
        """Tables without _info suffix should not be detected as info tables."""
        detector = InfoInstanceDetector()

        result = detector.detect(table_name="tb_contact", columns=["pk_contact", "email", "name"])

        assert result.is_info_table is False


class TestInstanceTableDetection:
    """Tests for detecting instance tables."""

    def test_detect_instance_table_with_info_fk(self):
        """Tables with fk_{entity}_info should be detected as instance tables."""
        detector = InfoInstanceDetector()

        result = detector.detect(
            table_name="tb_administrative_unit",
            columns=[
                "pk_administrative_unit",
                "fk_administrative_unit_info",  # FK to info table
                "fk_parent_administrative_unit",  # Self-ref for hierarchy
                "path",
                "identifier",
            ],
        )

        assert result.is_instance_table is True
        assert result.is_info_table is False
        assert result.base_entity_name == "administrative_unit"
        assert result.info_fk_column == "fk_administrative_unit_info"
        assert result.parent_fk_column == "fk_parent_administrative_unit"

    def test_regular_table_not_detected_as_instance(self):
        """Tables without info FK should not be detected as instance tables."""
        detector = InfoInstanceDetector()

        result = detector.detect(
            table_name="tb_contact", columns=["pk_contact", "fk_company", "email"]
        )

        assert result.is_instance_table is False


class TestPairDetection:
    """Tests for detecting info/instance pairs."""

    def test_detect_pair_from_table_list(self):
        """Should match _info table with corresponding instance table."""
        detector = InfoInstanceDetector()

        tables = [
            {
                "name": "tb_administrative_unit_info",
                "columns": ["pk_administrative_unit_info", "identifier", "name"],
            },
            {
                "name": "tb_administrative_unit",
                "columns": [
                    "pk_administrative_unit",
                    "fk_administrative_unit_info",
                    "fk_parent_administrative_unit",
                    "path",
                ],
            },
            {"name": "tb_contact", "columns": ["pk_contact", "email"]},  # Standalone
        ]

        pairs = detector.detect_pairs(tables)

        assert len(pairs) == 1
        assert pairs[0].info_table == "tb_administrative_unit_info"
        assert pairs[0].instance_table == "tb_administrative_unit"
        assert pairs[0].base_entity_name == "administrative_unit"

    def test_info_without_instance_not_paired(self):
        """Info table without matching instance should not create pair."""
        detector = InfoInstanceDetector()

        tables = [
            {"name": "tb_currency_info", "columns": ["pk_currency_info", "code", "name"]},
            # No tb_currency instance table
        ]

        pairs = detector.detect_pairs(tables)

        assert len(pairs) == 0
