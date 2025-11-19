"""
Universal Audit Trail Pattern Detection Tests
"""

import pytest

from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestAuditTrailPattern:
    """Test audit trail detection across languages"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_sql_full_audit_trail(self, detector):
        """Test SQL table with full audit fields"""
        sql_code = """
CREATE TABLE tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL
);

CREATE FUNCTION update_contact_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_contact_updated
BEFORE UPDATE ON tb_contact
FOR EACH ROW
EXECUTE FUNCTION update_contact_timestamp();
        """

        # EXPECTED TO FAIL
        patterns = detector.detect(sql_code, language="sql")

        assert any(p.name == "audit_trail" for p in patterns)
        audit = next(p for p in patterns if p.name == "audit_trail")

        assert audit.confidence >= 0.89
        assert "created_at" in " ".join(audit.evidence).lower()
        assert "updated_at" in " ".join(audit.evidence).lower()

    def test_rust_audit_fields(self, detector):
        """Test Rust struct with audit fields"""
        rust_code = """
use chrono::{DateTime, Utc};
use uuid::Uuid;

pub struct Contact {
    pub email: String,
    pub created_at: DateTime<Utc>,
    pub created_by: Uuid,
    pub updated_at: DateTime<Utc>,
    pub updated_by: Uuid,
}

impl Contact {
    pub fn new(email: String, user_id: Uuid) -> Self {
        let now = Utc::now();
        Contact {
            email,
            created_at: now,
            created_by: user_id,
            updated_at: now,
            updated_by: user_id,
        }
    }

    pub fn update(&mut self, user_id: Uuid) {
        self.updated_at = Utc::now();
        self.updated_by = user_id;
    }
}
        """

        patterns = detector.detect(rust_code, language="rust")

        # EXPECTED TO FAIL
        assert any(p.name == "audit_trail" for p in patterns)

    def test_python_audit_mixin(self, detector):
        """Test Python with audit mixin"""
        python_code = """
from datetime import datetime
from uuid import UUID

class AuditMixin:
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID

class Contact(AuditMixin):
    email: str

    def __init__(self, email: str, user_id: UUID):
        self.email = email
        self.created_at = datetime.now()
        self.created_by = user_id
        self.updated_at = datetime.now()
        self.updated_by = user_id

    def update(self, user_id: UUID):
        self.updated_at = datetime.now()
        self.updated_by = user_id
        """

        patterns = detector.detect(python_code, language="python")

        # EXPECTED TO FAIL
        assert any(p.name == "audit_trail" for p in patterns)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
