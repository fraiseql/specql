"""Tests for audit trail detection functionality."""

from reverse_engineering.audit_detector import AuditTrailDetector
from reverse_engineering.pattern_orchestrator import PatternDetectionOrchestrator
from reverse_engineering.table_parser import SQLTableParser


class TestAuditTrailDetector:
    """Test cases for audit trail detection."""

    def test_detect_audit_trail(self):
        """Test detection of audit trail patterns."""
        sql = """
        CREATE TABLE catalog.tb_manufacturer (
            pk_manufacturer UUID PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_by UUID,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_by UUID,
            deleted_at TIMESTAMPTZ,
            deleted_by UUID
        );
        """

        parser = SQLTableParser()
        parsed_table = parser.parse_table(sql)

        detector = AuditTrailDetector()
        result = detector.detect(parsed_table)

        assert result.has_audit_trail is True
        assert result.has_soft_delete is True
        assert result.audit_fields == [
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ]
        assert result.confidence == 1.0  # All 6 fields present

    def test_detect_all_patterns(self):
        """Test multi-pattern detection integration."""
        sql = """
        CREATE TABLE catalog.tb_manufacturer (
            id INTEGER PRIMARY KEY,
            pk_manufacturer UUID UNIQUE,
            identifier TEXT UNIQUE,
            name TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
        """

        parser = SQLTableParser()
        parsed_table = parser.parse_table(sql)

        orchestrator = PatternDetectionOrchestrator()
        result = orchestrator.detect_all(parsed_table)

        assert "trinity" in result.patterns
        assert "audit_trail" in result.patterns
        assert "soft_delete" in result.patterns
        assert result.confidence >= 0.7
