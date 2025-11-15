"""Unit tests for PatternDetector"""

import pytest
from src.parsers.plpgsql.pattern_detector import PatternDetector
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class TestPatternDetector:
    """Test PatternDetector"""

    @pytest.fixture
    def detector(self):
        return PatternDetector()

    def test_detect_trinity_pattern_complete(self, detector):
        """Test detecting complete Trinity pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.TEXT),
                UniversalField(name="identifier", type=FieldType.TEXT),
            ],
            actions=[],
        )

        result = detector._detect_trinity_pattern(entity)

        assert result["detected"] == True
        assert result["has_pk"] == True
        assert result["has_id"] == True
        assert result["has_identifier"] == True
        assert result["confidence"] == 1.0

    def test_detect_trinity_pattern_partial(self, detector):
        """Test detecting partial Trinity pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.TEXT),
                # Missing identifier
            ],
            actions=[],
        )

        result = detector._detect_trinity_pattern(entity)

        assert result["detected"] == False
        assert result["confidence"] == 2 / 3  # 2 out of 3

    def test_detect_audit_fields_complete(self, detector):
        """Test detecting complete audit fields"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="created_at", type=FieldType.DATETIME),
                UniversalField(name="updated_at", type=FieldType.DATETIME),
                UniversalField(name="deleted_at", type=FieldType.DATETIME),
            ],
            actions=[],
        )

        result = detector._detect_audit_fields(entity)

        assert result["detected"] == True
        assert result["has_created_at"] == True
        assert result["has_updated_at"] == True
        assert result["has_deleted_at"] == True

    def test_detect_deduplication_pattern(self, detector):
        """Test detecting deduplication pattern"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                UniversalField(name="dedup_key", type=FieldType.TEXT),
                UniversalField(name="dedup_hash", type=FieldType.TEXT),
                UniversalField(name="is_unique", type=FieldType.BOOLEAN),
            ],
            actions=[],
        )

        result = detector._detect_deduplication(entity)

        assert result["detected"] == True
        assert result["confidence"] == 1.0

    def test_detect_hierarchical_entity(self, detector):
        """Test detecting hierarchical entity"""
        entity = UniversalEntity(
            name="Category",
            schema="catalog",
            fields=[
                UniversalField(name="fk_parent", type=FieldType.REFERENCE),
            ],
            actions=[],
        )

        result = detector._detect_hierarchical(entity)

        assert result["detected"] == True
        assert result["parent_field"] == "fk_parent"

    def test_calculate_overall_confidence(self, detector):
        """Test calculating overall confidence score"""
        entity = UniversalEntity(
            name="Contact",
            schema="crm",
            fields=[
                # Complete Trinity
                UniversalField(name="pk_contact", type=FieldType.INTEGER),
                UniversalField(name="id", type=FieldType.TEXT),
                UniversalField(name="identifier", type=FieldType.TEXT),
                # Complete Audit
                UniversalField(name="created_at", type=FieldType.DATETIME),
                UniversalField(name="updated_at", type=FieldType.DATETIME),
                UniversalField(name="deleted_at", type=FieldType.DATETIME),
                # Business fields
                UniversalField(name="email", type=FieldType.TEXT),
            ],
            actions=[],
        )

        patterns = detector.detect_patterns(entity)

        # Trinity (40%) + Audit (30%) = 70% minimum
        assert patterns["confidence"] >= 0.70
